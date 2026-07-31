import os
import subprocess
import time
import threading
import logging
from dataclasses import dataclass
from typing import Sequence, Collection, Optional, Any, Dict

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
        
        # Hide taskkill console window on Windows
        startupinfo = None
        if hasattr(subprocess, "STARTUPINFO"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        taskkill_proc = subprocess.Popen(
            taskkill_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            startupinfo=startupinfo
        )
        taskkill_proc.communicate(timeout=10.0)
    except Exception as e:
        logger.debug(f"Failed to invoke taskkill for PID {process.pid}: {e}")

    try:
        process.wait(timeout=2.0)
        return True
    except subprocess.TimeoutExpired:
        try:
            process.kill()
            process.wait(timeout=2.0)
            return True
        except Exception as e:
            logger.debug(f"Failed to kill process {process.pid} as fallback: {e}")
            return False

def _decode_output(data: bytes, max_chars: int) -> str:
    """Decodes output bytes defensively and truncates."""
    if not data:
        return ""
        
    text = ""
    encodings_to_try = [
        "utf-8-sig",  # UTF-8 with BOM
        "utf-8",
        "utf-16",     # LE/BE depending on BOM
        "cp1252",
        "oem",
        "ascii"
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
        # Fallback with replacement
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
    if not args or isinstance(args, str):
        return _create_result(COMMAND_INVALID, False, None)
    
    if not args[0].strip():
        return _create_result(COMMAND_INVALID, False, None)
        
    for arg in args:
        if "\x00" in arg:
            return _create_result(COMMAND_INVALID, False, None)
            
    if timeout_seconds <= 0:
        return _create_result(COMMAND_INVALID, False, None)

    # 2. Setup Windows flags
    startupinfo = None
    creationflags = 0
    
    if hasattr(subprocess, "STARTUPINFO"):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP

    # 3. Start process
    try:
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            shell=False,
            startupinfo=startupinfo,
            creationflags=creationflags
        )
    except FileNotFoundError:
        return _create_result(COMMAND_NOT_FOUND, False, None)
    except PermissionError:
        return _create_result(COMMAND_ACCESS_DENIED, False, None)
    except OSError as e:
        logger.error(f"Failed to start process {args[0]} ({operation_name}): {e}")
        return _create_result(COMMAND_INTERNAL_ERROR, False, None)
    except Exception as e:
        logger.exception(f"Unexpected error starting {args[0]} ({operation_name})")
        return _create_result(COMMAND_INTERNAL_ERROR, False, None)

    # 4. Wait loop
    poll_interval = 0.1
    stdout_chunks = []
    stderr_chunks = []
    
    try:
        while True:
            if cancel_event and cancel_event.is_set():
                term_ok = _terminate_process_tree(process)
                out, err = process.communicate()
                if out: stdout_chunks.append(out)
                if err: stderr_chunks.append(err)
                return _create_result(
                    COMMAND_CANCELLED, False, process.returncode,
                    _decode_output(b"".join(stdout_chunks), max_output_chars),
                    _decode_output(b"".join(stderr_chunks), max_output_chars),
                    cancelled=True, termination_ok=term_ok
                )

            if time.monotonic() - start_time > timeout_seconds:
                term_ok = _terminate_process_tree(process)
                out, err = process.communicate()
                if out: stdout_chunks.append(out)
                if err: stderr_chunks.append(err)
                return _create_result(
                    COMMAND_TIMEOUT, False, process.returncode,
                    _decode_output(b"".join(stdout_chunks), max_output_chars),
                    _decode_output(b"".join(stderr_chunks), max_output_chars),
                    timed_out=True, termination_ok=term_ok
                )

            try:
                # Polling approach with communicate
                out, err = process.communicate(timeout=poll_interval)
                if out: stdout_chunks.append(out)
                if err: stderr_chunks.append(err)
                break  # Process finished
            except subprocess.TimeoutExpired:
                # Not finished yet
                pass

    except Exception as e:
        logger.exception(f"Unexpected error while waiting for {args[0]} ({operation_name})")
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
    """
    Maps a CommandResult to a bridge-safe payload.
    """
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
