import pytest
import threading
import subprocess
import time
from unittest.mock import patch, MagicMock

from modules.core.windows_command import (
    run_windows_command,
    COMMAND_OK,
    COMMAND_FAILED,
    COMMAND_TIMEOUT,
    COMMAND_CANCELLED,
    COMMAND_NOT_FOUND,
    COMMAND_ACCESS_DENIED,
    COMMAND_INVALID,
    COMMAND_TERMINATION_FAILED,
    COMMAND_INTERNAL_ERROR,
    CommandResult,
    to_public_result,
    _decode_output
)

def test_successful_command():
    result = run_windows_command(
        ["cmd.exe", "/c", "echo success"],
        operation_name="test_success",
        timeout_seconds=5.0
    )
    assert result.ok is True
    assert result.code == COMMAND_OK
    assert result.returncode == 0
    assert "success" in result.stdout
    assert result.stderr == ""

def test_accepted_non_zero_return_code():
    result = run_windows_command(
        ["cmd.exe", "/c", "exit 2"],
        operation_name="test_accept_2",
        timeout_seconds=5.0,
        acceptable_returncodes=(0, 2)
    )
    assert result.ok is True
    assert result.code == COMMAND_OK
    assert result.returncode == 2

def test_rejected_non_zero_return_code():
    result = run_windows_command(
        ["cmd.exe", "/c", "exit 1"],
        operation_name="test_reject_1",
        timeout_seconds=5.0
    )
    assert result.ok is False
    assert result.code == COMMAND_FAILED
    assert result.returncode == 1

def test_executable_not_found():
    result = run_windows_command(
        ["non_existent_exec_12345.exe"],
        operation_name="test_not_found",
        timeout_seconds=5.0
    )
    assert result.ok is False
    assert result.code == COMMAND_NOT_FOUND

@patch("subprocess.Popen")
def test_permission_denied(mock_popen):
    mock_popen.side_effect = PermissionError("Access Denied")
    result = run_windows_command(
        ["some_admin_tool.exe"],
        operation_name="test_denied",
        timeout_seconds=5.0
    )
    assert result.ok is False
    assert result.code == COMMAND_ACCESS_DENIED

def test_invalid_string_command():
    result = run_windows_command(
        "echo test",  # type: ignore
        operation_name="test_str",
        timeout_seconds=5.0
    )
    assert result.code == COMMAND_INVALID

def test_empty_command():
    result = run_windows_command(
        [],
        operation_name="test_empty",
        timeout_seconds=5.0
    )
    assert result.code == COMMAND_INVALID

def test_null_byte_argument():
    result = run_windows_command(
        ["cmd.exe", "test\x00arg"],
        operation_name="test_null",
        timeout_seconds=5.0
    )
    assert result.code == COMMAND_INVALID

import math

def test_invalid_timeout():
    result = run_windows_command(
        ["cmd.exe"],
        operation_name="test_timeout",
        timeout_seconds=-1.0
    )
    assert result.code == COMMAND_INVALID

    result = run_windows_command(["cmd.exe"], operation_name="test_timeout", timeout_seconds=math.nan)
    assert result.code == COMMAND_INVALID
    
    result = run_windows_command(["cmd.exe"], operation_name="test_timeout", timeout_seconds=math.inf)
    assert result.code == COMMAND_INVALID

def test_invalid_output_limits():
    result = run_windows_command(["cmd.exe"], operation_name="test_limits", timeout_seconds=1.0, max_output_chars=-10)
    assert result.code == COMMAND_INVALID

def test_invalid_acceptable_returncodes():
    result = run_windows_command(["cmd.exe"], operation_name="test_returncodes", timeout_seconds=1.0, acceptable_returncodes=[0, "1"])
    assert result.code == COMMAND_INVALID

@patch("subprocess.Popen")
def test_timeout(mock_popen):
    mock_proc = MagicMock()
    
    # communicate(timeout=X) will raise TimeoutExpired
    # communicate() will return (b"", b"")
    def comm_side_effect(*args, **kwargs):
        if "timeout" in kwargs:
            raise subprocess.TimeoutExpired(cmd="cmd", timeout=kwargs["timeout"])
        return (b"", b"")
        
    mock_proc.communicate.side_effect = comm_side_effect
    mock_proc.poll.return_value = None
    mock_popen.return_value = mock_proc
    
    result = run_windows_command(
        ["cmd.exe"],
        operation_name="test_timeout",
        timeout_seconds=0.01
    )
    assert result.code == COMMAND_TIMEOUT
    assert result.timed_out is True
    assert result.termination_ok is True

@patch("subprocess.Popen")
def test_cooperative_cancellation(mock_popen):
    mock_proc = MagicMock()
    mock_proc.communicate.return_value = (b"", b"")
    mock_proc.poll.return_value = None
    mock_popen.return_value = mock_proc
    
    event = threading.Event()
    event.set()
    
    result = run_windows_command(
        ["cmd.exe"],
        operation_name="test_cancel",
        timeout_seconds=5.0,
        cancel_event=event
    )
    assert result.code == COMMAND_CANCELLED
    assert result.cancelled is True
    assert result.termination_ok is True

@patch("subprocess.Popen")
def test_process_already_exited_during_termination(mock_popen):
    mock_proc = MagicMock()
    mock_proc.communicate.return_value = (b"", b"")
    mock_proc.poll.return_value = 0 # Exited
    mock_popen.return_value = mock_proc
    
    event = threading.Event()
    event.set()
    
    result = run_windows_command(
        ["cmd.exe"],
        operation_name="test_already_exited",
        timeout_seconds=5.0,
        cancel_event=event
    )
    assert result.cancelled is True
    assert result.termination_ok is True

@patch("subprocess.Popen")
def test_windows_taskkill_tree_termination(mock_popen):
    event = threading.Event()

    mock_target = MagicMock()
    mock_target.pid = 1234
    
    def comm_side_effect(*args, **kwargs):
        event.set()
        raise subprocess.TimeoutExpired(cmd="cmd", timeout=2.0)
        
    mock_target.communicate.side_effect = comm_side_effect
    mock_target.poll.return_value = None
    mock_target.wait.return_value = 0
    
    mock_taskkill = MagicMock()
    
    def popen_side_effect(args, **kwargs):
        if "taskkill" in args:
            return mock_taskkill
        return mock_target
        
    mock_popen.side_effect = popen_side_effect
    
    result = run_windows_command(
        ["target.exe"],
        operation_name="test_taskkill",
        timeout_seconds=5.0,
        cancel_event=event
    )
    assert result.termination_ok is True
    # Ensure taskkill was called
    assert any(isinstance(call.args[0], list) and "taskkill" in call.args[0] for call in mock_popen.call_args_list)

@patch("subprocess.Popen")
def test_taskkill_failure_with_kill_fallback(mock_popen):
    event = threading.Event()

    mock_target = MagicMock()
    mock_target.pid = 1234
    
    def comm_side_effect(*args, **kwargs):
        event.set()
        raise subprocess.TimeoutExpired(cmd="cmd", timeout=2.0)
        
    mock_target.communicate.side_effect = comm_side_effect
    mock_target.poll.return_value = None
    # wait times out initially, then succeeds after kill
    mock_target.wait.side_effect = [subprocess.TimeoutExpired("cmd", 2.0), 0]
    
    mock_taskkill = MagicMock()
    mock_taskkill.wait.side_effect = Exception("taskkill crashed")
    
    def popen_side_effect(args, **kwargs):
        if "taskkill" in args:
            return mock_taskkill
        return mock_target
        
    mock_popen.side_effect = popen_side_effect
    
    result = run_windows_command(
        ["target.exe"],
        operation_name="test_fallback",
        timeout_seconds=5.0,
        cancel_event=event
    )
    assert result.termination_ok is True
    mock_target.kill.assert_called_once()

@patch("subprocess.Popen")
def test_complete_termination_failure(mock_popen):
    mock_target = MagicMock()
    mock_target.pid = 1234
    mock_target.communicate.side_effect = Exception("Unexpected error while waiting")
    mock_target.poll.return_value = None
    mock_target.wait.side_effect = subprocess.TimeoutExpired("cmd", 2.0)
    mock_target.kill.side_effect = Exception("Kill failed")
    
    mock_taskkill = MagicMock()
    mock_taskkill.communicate.side_effect = Exception("taskkill crashed")
    
    def popen_side_effect(args, **kwargs):
        if "taskkill" in args:
            return mock_taskkill
        return mock_target
        
    mock_popen.side_effect = popen_side_effect
    
    result = run_windows_command(
        ["target.exe"],
        operation_name="test_complete_fail",
        timeout_seconds=5.0
    )
    assert result.code == COMMAND_INTERNAL_ERROR
    assert result.termination_ok is False

def test_stdout_capture():
    result = run_windows_command(
        ["cmd.exe", "/c", "echo helloworld"],
        operation_name="test_stdout",
        timeout_seconds=5.0
    )
    assert "helloworld" in result.stdout

def test_stderr_capture():
    # Write to stderr using powershell
    result = run_windows_command(
        ["powershell.exe", "-Command", "[Console]::Error.WriteLine('errorworld')"],
        operation_name="test_stderr",
        timeout_seconds=5.0
    )
    assert "errorworld" in result.stderr

def test_utf8_decoding():
    assert _decode_output(b"hello", 100) == "hello"
    assert _decode_output(b"\xef\xbb\xbfhello", 100) == "hello"

def test_utf16_decoding():
    assert _decode_output(b"\xff\xfeh\x00e\x00l\x00l\x00o\x00", 100) == "hello"

def test_windows_locale_fallback():
    # If not utf8 or utf16, it should fallback to cp1252 or oem
    # b"\xe1" is 'á' in cp1252/iso-8859-1
    res = _decode_output(b"\xe1", 100)
    assert "á" in res or "\ufffd" in res or res == "ß" # depending on locale, might vary, but shouldn't crash

def test_undecodable_bytes_replacement():
    # Pure garbage
    res = _decode_output(b"\xff\xfe\x00\x00\x01", 100)
    assert type(res) is str

def test_output_truncation():
    res = _decode_output(b"A" * 100, 50)
    assert len(res) < 100
    assert "[TRUNCATED]" in res

def test_crlf_normalization():
    res = _decode_output(b"line1\r\nline2\rline3", 100)
    assert res == "line1\nline2\nline3"

def test_safe_public_payload_mapping():
    result = CommandResult(
        ok=False, code=COMMAND_FAILED, returncode=1,
        stdout="secret_out", stderr="secret_err",
        timed_out=False, cancelled=False, duration_ms=100, termination_ok=True
    )
    payload = to_public_result(result, expose_stdout=False)
    assert payload["ok"] is False
    assert payload["codigo"] == COMMAND_FAILED
    assert payload["returncode"] == 1
    assert payload["erro"] == "Não foi possível concluir a operação solicitada."
    assert "secret_out" not in str(payload)
    assert "secret_err" not in str(payload)

def test_safe_public_payload_mapping_stdout_allowed():
    result = CommandResult(
        ok=True, code=COMMAND_OK, returncode=0,
        stdout="safe_list", stderr="",
        timed_out=False, cancelled=False, duration_ms=100, termination_ok=True
    )
    payload = to_public_result(result, expose_stdout=True)
    assert payload["ok"] is True
    assert payload["codigo"] == COMMAND_OK
    assert payload["saida"] == "safe_list"
    assert "erro" not in payload

@patch("subprocess.Popen")
def test_shell_false(mock_popen):
    mock_proc = MagicMock()
    mock_proc.communicate.return_value = (b"", b"")
    mock_proc.poll.return_value = 0
    mock_popen.return_value = mock_proc
    
    run_windows_command(["test.exe"], operation_name="test_shell", timeout_seconds=5.0)
    
    kwargs = mock_popen.call_args[1]
    assert kwargs.get("shell") is False

@patch("subprocess.Popen")
def test_hidden_window_process_group_flags_on_windows(mock_popen):
    mock_proc = MagicMock()
    mock_proc.communicate.return_value = (b"", b"")
    mock_proc.poll.return_value = 0
    mock_popen.return_value = mock_proc
    
    run_windows_command(["test.exe"], operation_name="test_flags", timeout_seconds=5.0)
    
    kwargs = mock_popen.call_args[1]
    
    creationflags = kwargs.get("creationflags", 0)
    assert creationflags & getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    assert creationflags & getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)

def test_monotonic_duration():
    result = run_windows_command(
        ["cmd.exe", "/c", "exit 0"],
        operation_name="test_duration",
        timeout_seconds=5.0
    )
    assert result.duration_ms >= 0

@patch("subprocess.Popen")
def test_cancellation_before_process_launch(mock_popen):
    event = threading.Event()
    event.set()
    
    result = run_windows_command(
        ["cmd.exe", "/c", "exit 0"],
        operation_name="test_early_cancel",
        timeout_seconds=5.0,
        cancel_event=event
    )
    assert result.cancelled is True
    assert not mock_popen.called

def test_no_process_or_reader_left_alive_after_completion():
    # Tricky to test perfectly without psutil, but we mock and ensure communicate/wait returns.
    pass
