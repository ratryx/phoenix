import os
import subprocess
import time
import threading
import logging
from dataclasses import dataclass
from typing import Sequence, Collection, Optional, Any, Dict
import math

logger = logging.getLogger(__name__)

COMMAND_OK = "COMMAND_OK"
COMMAND_FAILED = "COMMAND_FAILED"
COMMAND_TIMEOUT = "COMMAND_TIMEOUT"
COMMAND_CANCELLED = "COMMAND_CANCELLED"
COMMAND_NOT_FOUND = "COMMAND_NOT_FOUND"
COMMAND_ACCESS_DENIED = "COMMAND_ACCESS_DENIED"
COMMAND_INVALID = "COMMAND_INVALID"
COMMAND_TERMINATION_FAILED = "COMMAND_TERMINATION_FAILED"
COMMAND_INTERNAL_ERROR = "COMMAND_INTERNAL_ERROR"

@dataclass(frozen=True)
class CommandResult:
    ok: bool
    code: str
    returncode: Optional[int]
    stdout: str
    stderr: str
    timed_out: bool
    cancelled: bool
    duration_ms: int
    termination_ok: bool

def _terminate_process_tree(process: subprocess.Popen) -> bool:
    """
    Terminates the complete process tree on Windows using taskkill.
    Falls back to process.kill() if taskkill fails.
    """
    if process.poll() is not None:
        return True

    try:
        pid = process.pid
        taskkill_args = ["taskkill", "/PID", str(pid), "/T", "/F"]
        
        CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        
        taskkill_proc = subprocess.Popen(
            taskkill_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            creationflags=CREATE_NO_WINDOW
        )
        taskkill_proc.wait(timeout=10.0)
    except Exception as e:
        logger.debug(f"Failed to invoke taskkill for PID {process.pid}")

    try:
        process.wait(timeout=3.0)
        return True
    except subprocess.TimeoutExpired:
        try:
            process.kill()
            process.wait(timeout=2.0)
            return True
        except Exception as e:
            logger.debug(f"Failed to kill process {process.pid} as fallback")
            return False

def _decode_output(data: bytes, max_chars: int) -> str:
    if not data:
        return ""
        
    text = ""
    encodings_to_try = [
        "utf-8-sig", "utf-8", "utf-16", "cp1252", "oem", "ascii"
    ]
    
    for enc in encodings_to_try:
        try:
            if enc == "oem":
                try:
                    import locale
                    enc = locale.getpreferredencoding(False) or "cp1252"
                except Exception:
                    enc = "cp1252"
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = data.decode("utf-8", errors="replace")
        
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[TRUNCATED]"
    return text

def run_windows_command(
    args: Sequence[str],
    *,
    operation_name: str,
    timeout_seconds: float,
    cancel_event: Optional[threading.Event] = None,
    acceptable_returncodes: Collection[int] = (0,),
    max_output_chars: int = 32768,
) -> CommandResult:
    start_time = time.monotonic()
    
    def _create_result(code: str, ok: bool, returncode: Optional[int], 
                       stdout: str = "", stderr: str = "",
                       timed_out: bool = False, cancelled: bool = False,
                       termination_ok: bool = True) -> CommandResult:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        return CommandResult(
            ok=ok,
            code=code,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            timed_out=timed_out,
            cancelled=cancelled,
            duration_ms=duration_ms,
            termination_ok=termination_ok
        )

    # 1. Validation
    if not isinstance(args, (list, tuple)) or not args:
        return _create_result(COMMAND_INVALID, False, None)
    
    for arg in args:
        if not isinstance(arg, str):
            return _create_result(COMMAND_INVALID, False, None)
        if "\x00" in arg:
            return _create_result(COMMAND_INVALID, False, None)
            
    if not args[0].strip():
        return _create_result(COMMAND_INVALID, False, None)
        
    if not isinstance(timeout_seconds, (int, float)) or math.isnan(timeout_seconds) or math.isinf(timeout_seconds) or timeout_seconds <= 0:
        return _create_result(COMMAND_INVALID, False, None)
        
    if not isinstance(max_output_chars, int) or max_output_chars <= 0:
        return _create_result(COMMAND_INVALID, False, None)
        
    for code in acceptable_returncodes:
        if not isinstance(code, int):
            return _create_result(COMMAND_INVALID, False, None)

    # 2. Cancellation before launch
    if cancel_event is not None and cancel_event.is_set():
        return _create_result(COMMAND_CANCELLED, False, None, cancelled=True, termination_ok=True)

    # 3. Setup Windows flags
    CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
    creationflags = CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP

    # 4. Start process
    try:
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            shell=False,
            creationflags=creationflags
        )
    except FileNotFoundError:
        return _create_result(COMMAND_NOT_FOUND, False, None)
    except PermissionError:
        return _create_result(COMMAND_ACCESS_DENIED, False, None)
    except OSError as e:
        logger.error(f"Failed to start process ({operation_name})")
        return _create_result(COMMAND_INTERNAL_ERROR, False, None)
    except Exception as e:
        logger.error(f"Unexpected error starting ({operation_name})")
        return _create_result(COMMAND_INTERNAL_ERROR, False, None)

    # 5. Wait loop
    poll_interval = 0.1
    stdout_chunks = []
    stderr_chunks = []
    
    try:
        while True:
            if cancel_event and cancel_event.is_set():
                term_ok = _terminate_process_tree(process)
                try:
                    out, err = process.communicate(timeout=2.0)
                    if out: stdout_chunks.append(out)
                    if err: stderr_chunks.append(err)
                except subprocess.TimeoutExpired:
                    pass
                final_code = COMMAND_CANCELLED if term_ok else COMMAND_TERMINATION_FAILED
                return _create_result(
                    final_code, False, process.returncode,
                    _decode_output(b"".join(stdout_chunks), max_output_chars),
                    _decode_output(b"".join(stderr_chunks), max_output_chars),
                    cancelled=True, termination_ok=term_ok
                )

            if time.monotonic() - start_time > timeout_seconds:
                term_ok = _terminate_process_tree(process)
                try:
                    out, err = process.communicate(timeout=2.0)
                    if out: stdout_chunks.append(out)
                    if err: stderr_chunks.append(err)
                except subprocess.TimeoutExpired:
                    pass
                final_code = COMMAND_TIMEOUT if term_ok else COMMAND_TERMINATION_FAILED
                return _create_result(
                    final_code, False, process.returncode,
                    _decode_output(b"".join(stdout_chunks), max_output_chars),
                    _decode_output(b"".join(stderr_chunks), max_output_chars),
                    timed_out=True, termination_ok=term_ok
                )

            try:
                out, err = process.communicate(timeout=poll_interval)
                if out: stdout_chunks.append(out)
                if err: stderr_chunks.append(err)
                break  # Process finished
            except subprocess.TimeoutExpired:
                pass

    except Exception as e:
        logger.error(f"Unexpected error while waiting for ({operation_name})")
        term_ok = _terminate_process_tree(process)
        return _create_result(COMMAND_INTERNAL_ERROR, False, None, termination_ok=term_ok)

    returncode = process.returncode
    stdout = _decode_output(b"".join(stdout_chunks), max_output_chars)
    stderr = _decode_output(b"".join(stderr_chunks), max_output_chars)
    
    ok = returncode in acceptable_returncodes
    code = COMMAND_OK if ok else COMMAND_FAILED

    return _create_result(
        code, ok, returncode,
        stdout, stderr
    )

def to_public_result(
    result: CommandResult,
    *,
    expose_stdout: bool = False,
    error_message: str = "Não foi possível concluir a operação solicitada."
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "ok": result.ok,
        "codigo": result.code,
    }
    
    if result.returncode is not None:
        payload["returncode"] = result.returncode

    if result.ok:
        if expose_stdout and result.stdout:
            payload["saida"] = result.stdout
    else:
        payload["erro"] = error_message
        
    return payload
