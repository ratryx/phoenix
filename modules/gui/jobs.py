import uuid
import threading
import time
import traceback
import logging
import json

logger = logging.getLogger(__name__)

class JobManager:
    """
    Gerenciador thread-safe de tarefas em background para a GUI.
    Mantém o contrato exato consumido pelo app.js (pywebview).
    """
    def __init__(self, ttl_seconds=900):
        self._jobs = {}
        self._lock = threading.RLock()
        self.ttl_seconds = ttl_seconds
        self._exclusive_groups = {}  # group_name -> active_job_id

    def submit(self, target_fn, *args, job_id=None, operation_name="unknown", exclusive_group=None, **kwargs):
        """Inicia uma função em thread isolada, retornando o job_id."""
        with self._lock:
            self._cleanup_expired()
            
            job_id = job_id or str(uuid.uuid4())
            
            # Controle de exclusividade
            if exclusive_group:
                active_job = self._exclusive_groups.get(exclusive_group)
                if active_job and active_job in self._jobs and self._jobs[active_job]["status"] == "running":
                    # Cria job rejeitado imediatamente
                    self._jobs[job_id] = {
                        "status": "done",
                        "resultado": {
                            "ok": False,
                            "erro": "Outra operação do sistema já está em execução.",
                            "detalhe": f"Conflito no grupo exclusivo: {exclusive_group}"
                        },
                        "created_at": time.time(),
                        "started_at": time.time(),
                        "completed_at": time.time(),
                        "operation_name": operation_name,
                        "exclusive_group": exclusive_group
                    }
                    return job_id

                # Registra o novo dono do grupo
                self._exclusive_groups[exclusive_group] = job_id

            self._jobs[job_id] = {
                "status": "running",
                "resultado": None,
                "created_at": time.time(),
                "started_at": None,
                "completed_at": None,
                "operation_name": operation_name,
                "exclusive_group": exclusive_group
            }

        def worker():
            with self._lock:
                if job_id in self._jobs:
                    self._jobs[job_id]["started_at"] = time.time()
            
            try:
                res = target_fn(*args, **kwargs)
                
                # Validação de serialização JSON (Bridge Contract)
                try:
                    json.dumps(res)
                except Exception as serial_err:
                    logger.error(f"Erro de serialização no job {job_id} ({operation_name}): {serial_err}")
                    res = {
                        "ok": False, 
                        "erro": "Erro interno: Resultado não serializável", 
                        "detalhe": str(serial_err)
                    }
            except Exception as e:
                logger.exception(f"Erro na execução do job {job_id} ({operation_name})")
                res = {
                    "ok": False, 
                    "erro": str(e), 
                    "detalhe": traceback.format_exc()
                }
            finally:
                with self._lock:
                    job = self._jobs.get(job_id)
                    if job:
                        job["status"] = "done"
                        job["resultado"] = res
                        job["completed_at"] = time.time()
                    
                    # Libera grupo exclusivo se formos o dono
                    if exclusive_group and self._exclusive_groups.get(exclusive_group) == job_id:
                        del self._exclusive_groups[exclusive_group]

        threading.Thread(target=worker, daemon=True, name=f"PhoenixJob-{job_id}").start()
        return job_id

    def update_progress(self, job_id, pct, msg):
        """Atualiza estado de progresso de forma segura."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job["status"] == "running":
                job["progresso"] = pct
                job["mensagem"] = msg

    def get_progress(self, job_id):
        """Lê o progresso de forma segura."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                return job.get("progresso", 0)
            return 0

    def consultar(self, job_id: str) -> dict:
        """
        Consulta o status atual para o frontend. 
        Mantém o contrato de retorno exato esperado pelo pywebview/app.js.
        """
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
        """Limpa jobs finalizados além do TTL."""
        now = time.time()
        expired_ids = []
        for j_id, job in self._jobs.items():
            if job["status"] == "done":
                completed_at = job.get("completed_at") or 0
                if now - completed_at > self.ttl_seconds:
                    expired_ids.append(j_id)
                    
        for j_id in expired_ids:
            del self._jobs[j_id]
