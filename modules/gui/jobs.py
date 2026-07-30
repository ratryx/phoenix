import uuid
import threading
import time
import logging
import json
from modules.core.exceptions import JobCancelledError

logger = logging.getLogger(__name__)

class JobContext:
    def __init__(self, job_id: str, cancel_event: threading.Event, update_progress_fn):
        self.job_id = job_id
        self.cancel_event = cancel_event
        self._update_progress_fn = update_progress_fn

    def is_cancel_requested(self) -> bool:
        return self.cancel_event.is_set()

    def raise_if_cancelled(self):
        if self.is_cancel_requested():
            raise JobCancelledError("Job cancelled cooperatively")

    def update_progress(self, pct: int, msg: str):
        self._update_progress_fn(self.job_id, pct, msg)

class JobManager:
    """
    Gerenciador thread-safe de tarefas em background para a GUI.
    Mantém o contrato exato consumido pelo app.js (pywebview).
    Estados válidos: running, cancel_requested, done, failed, cancelled, timed_out, not_found
    """
    def __init__(self, ttl_seconds=900, max_retained_jobs=100, watchdog_interval=1.0):
        self._jobs = {}
        self._lock = threading.RLock()
        self.ttl_seconds = ttl_seconds
        self.max_retained_jobs = max_retained_jobs
        self._exclusive_groups = {}  # group_name -> active_job_id

        self._shutdown_event = threading.Event()
        self._watchdog_interval = watchdog_interval

        self._watchdog = threading.Thread(target=self._watchdog_loop, daemon=True, name="PhoenixJobWatchdog")
        self._watchdog.start()

    def _watchdog_loop(self):
        while not self._shutdown_event.wait(self._watchdog_interval):
            self._check_timeouts()
            self._cleanup_expired()

        # Garante a limpeza uma última vez após o shutdown
        self._check_timeouts()
        self._cleanup_expired()

    def _generate_unique_job_id(self):
        while True:
            new_id = str(uuid.uuid4())
            if new_id not in self._jobs:
                return new_id

    def submit(self, target_fn, *args, job_id=None, operation_name="unknown", exclusive_group=None, timeout=None, pass_job_context=False, **kwargs):
        """Inicia uma função em thread isolada, retornando o job_id."""
        with self._lock:
            if not isinstance(job_id, str) or not job_id.strip():
                job_id = self._generate_unique_job_id()

            if self._shutdown_event.is_set():
                return self._create_rejected_job(
                    self._generate_unique_job_id(), operation_name, exclusive_group,
                    "JOB_MANAGER_SHUTDOWN", "O sistema está sendo encerrado."
                )

            self._cleanup_expired()

            if job_id in self._jobs:
                return self._create_rejected_job(
                    self._generate_unique_job_id(), operation_name, exclusive_group,
                    "JOB_DUPLICATE_ID", "ID de tarefa duplicado fornecido."
                )

            # Controle de exclusividade
            if exclusive_group:
                active_job_id = self._exclusive_groups.get(exclusive_group)
                if active_job_id and active_job_id in self._jobs and self._jobs[active_job_id]["worker_alive"]:
                    return self._create_rejected_job(
                        self._generate_unique_job_id(), operation_name, exclusive_group,
                        "JOB_CONFLICT", "Outra operação do sistema já está em execução.",
                        detalhe="Por favor, aguarde a conclusão da tarefa atual."
                    )

                self._exclusive_groups[exclusive_group] = job_id

            now = time.monotonic()
            self._jobs[job_id] = {
                "status": "running",
                "resultado": None,
                "created_at": time.time(),
                "started_at": None,
                "completed_at": None,
                "worker_exited_at": None,
                "operation_name": operation_name,
                "exclusive_group": exclusive_group,
                "worker_alive": True,
                "cancel_event": threading.Event(),
                "deadline": now + timeout if timeout else None
            }

        def worker():
            with self._lock:
                if job_id in self._jobs:
                    self._jobs[job_id]["started_at"] = time.time()

            job_ctx = JobContext(job_id, self._jobs[job_id]["cancel_event"], self.update_progress)
            if pass_job_context:
                kwargs["job_context"] = job_ctx

            res = None
            exception_type = None

            try:
                res = target_fn(*args, **kwargs)

                # Validação de serialização JSON (Bridge Contract)
                try:
                    json.dumps(res)
                except Exception as serial_err:
                    logger.exception(f"Erro de serialização no job {job_id} ({operation_name}): {serial_err}")
                    res = {
                        "ok": False,
                        "codigo": "JOB_RESULT_INVALID",
                        "erro": "Erro interno do aplicativo. O resultado gerado é inválido.",
                        "detalhe": "Não foi possível exibir o resultado."
                    }
                    exception_type = "invalid"

            except JobCancelledError:
                res = {
                    "ok": False,
                    "codigo": "JOB_CANCELLED",
                    "erro": "A operação foi cancelada pelo usuário."
                }
                exception_type = "cancelled"
            except Exception as e:
                logger.exception(f"Falha durante execução do job {job_id} ({operation_name})")
                res = {
                    "ok": False,
                    "codigo": "JOB_INTERNAL_ERROR",
                    "erro": "Não foi possível concluir a operação.",
                    "detalhe": "Um erro inesperado ocorreu. Os detalhes foram registrados nos logs."
                }
                exception_type = "failed"
            finally:
                with self._lock:
                    job = self._jobs.get(job_id)
                    if job:
                        job["worker_alive"] = False
                        job["worker_exited_at"] = time.time()

                        if job["status"] not in ("timed_out", "cancelled"):
                            if exception_type == "cancelled":
                                job["status"] = "cancelled"
                                if not res:
                                    res = {"ok": False, "codigo": "JOB_CANCELLED", "erro": "A operação foi cancelada."}
                            elif exception_type:
                                job["status"] = "failed"
                            else:
                                job["status"] = "done"

                            job["resultado"] = res
                            job["completed_at"] = time.time()
                        elif not job.get("completed_at"):
                            job["completed_at"] = time.time()

                    if exclusive_group and self._exclusive_groups.get(exclusive_group) == job_id:
                        del self._exclusive_groups[exclusive_group]

        threading.Thread(target=worker, daemon=True, name=f"PhoenixJob-{job_id}").start()
        return job_id

    def _create_rejected_job(self, job_id, operation_name, exclusive_group, codigo, erro, detalhe=""):
        self._jobs[job_id] = {
            "status": "failed",
            "resultado": {
                "ok": False,
                "codigo": codigo,
                "erro": erro,
                "detalhe": detalhe
            },
            "created_at": time.time(),
            "started_at": time.time(),
            "completed_at": time.time(),
            "worker_exited_at": time.time(),
            "operation_name": operation_name,
            "exclusive_group": exclusive_group,
            "worker_alive": False,
            "cancel_event": threading.Event(),
            "deadline": None
        }
        self._cleanup_expired()
        return job_id

    def update_progress(self, job_id, pct, msg):
        """Atualiza estado de progresso de forma segura."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job["status"] in ("running", "cancel_requested"):
                try:
                    pct = max(0, min(100, int(float(pct))))
                except (ValueError, TypeError):
                    pct = 0

                # Sanitização rigorosa da mensagem
                if msg is None:
                    safe_msg = ""
                elif isinstance(msg, (int, float, bool)):
                    safe_msg = str(msg)
                elif isinstance(msg, str):
                    safe_msg = msg
                else:
                    safe_msg = "[Objeto Complexo Omitido]"

                safe_msg = safe_msg[:200]

                job["progresso"] = pct
                job["mensagem"] = safe_msg

    def get_progress(self, job_id):
        """Lê o progresso de forma segura."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                return job.get("progresso", 0)
            return 0

    def cancelar(self, job_id: str) -> dict:
        """Solicita cancelamento cooperativo de uma tarefa."""
        if not isinstance(job_id, str) or not job_id.strip():
            return {"ok": False, "codigo": "JOB_INVALID_ID", "erro": "ID inválido."}

        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return {"ok": False, "codigo": "JOB_NOT_FOUND", "erro": "A tarefa não foi encontrada."}

            if not job["worker_alive"]:
                return {"ok": True, "status": job["status"]}

            job["cancel_event"].set()
            if job["status"] == "running":
                job["status"] = "cancel_requested"

            return {"ok": True, "status": job["status"]}

    def _check_timeouts(self):
        """Verifica timeouts pendentes."""
        now = time.monotonic()
        with self._lock:
            for j_id, job in self._jobs.items():
                if job["worker_alive"] and job["status"] in ("running", "cancel_requested") and job["deadline"] and now > job["deadline"]:
                    job["cancel_event"].set()
                    job["status"] = "timed_out"
                    job["resultado"] = {
                        "ok": False,
                        "codigo": "JOB_TIMEOUT",
                        "erro": "A operação excedeu o tempo máximo permitido."
                    }
                    job["completed_at"] = time.time()
                    # Não limpa o exclusive_group e worker_alive aqui; quem faz isso é o worker no finally

    def consultar(self, job_id: str) -> dict:
        """Consulta o status atual para o frontend."""
        if not isinstance(job_id, str) or not job_id.strip():
            return {"status": "not_found"}

        with self._lock:
            self._cleanup_expired()
            job = self._jobs.get(job_id)

            if not job:
                return {"status": "not_found"}

            payload = {
                "status": job["status"],
                "resultado": job.get("resultado")
            }
            if "progresso" in job:
                payload["progresso"] = job["progresso"]
            if "mensagem" in job:
                payload["mensagem"] = job["mensagem"]

            return payload

    def _cleanup_expired(self):
        """Limpa jobs finalizados além do TTL ou da capacidade máxima."""
        now = time.time()
        terminal_jobs = []
        for j_id, job in self._jobs.items():
            if not job["worker_alive"]:
                exit_time = job.get("worker_exited_at") or job.get("completed_at") or 0
                terminal_jobs.append((j_id, exit_time))

        expired_ids = [j_id for j_id, comp_time in terminal_jobs if now - comp_time > self.ttl_seconds]
        for j_id in expired_ids:
            del self._jobs[j_id]

        terminal_jobs = [item for item in terminal_jobs if item[0] not in expired_ids]
        if len(self._jobs) > self.max_retained_jobs:
            terminal_jobs.sort(key=lambda x: x[1])
            excess = len(self._jobs) - self.max_retained_jobs
            for i in range(min(excess, len(terminal_jobs))):
                del self._jobs[terminal_jobs[i][0]]

    def shutdown(self):
        """Inicia encerramento seguro do gerenciador de jobs."""
        with self._lock:
            self._shutdown_event.set()
            for job in self._jobs.values():
                if job["worker_alive"]:
                    job["cancel_event"].set()
                    if job["status"] == "running":
                        job["status"] = "cancel_requested"

        if threading.current_thread() != self._watchdog:
            self._watchdog.join(timeout=2.0)
