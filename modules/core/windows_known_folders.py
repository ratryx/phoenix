import os
import ctypes
from ctypes import wintypes

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_byte * 8)
    ]

FOLDERID_LocalAppData = GUID(
    0xF1B32785, 0x6FBA, 0x4FCF,
    (0x9D, 0x55, 0x7B, 0x8E, 0x7F, 0x15, 0x70, 0x91)
)

def obter_local_appdata() -> str:
    if os.name != 'nt':
        return os.environ.get("LOCALAPPDATA", "")
        
    # Em testes, podemos precisar do fallback se injetarmos via monkeypatch
    # Mas no Windows real, a API é a fonte.
    try:
        shell32 = ctypes.windll.shell32
        path_ptr = ctypes.c_wchar_p()
        # SHGetKnownFolderPath(rfid, dwFlags, hToken, ppszPath)
        hr = shell32.SHGetKnownFolderPath(ctypes.byref(FOLDERID_LocalAppData), 0, None, ctypes.byref(path_ptr))
        if hr == 0 and path_ptr.value:
            res = path_ptr.value
            ctypes.windll.ole32.CoTaskMemFree(path_ptr)
            return res
    except Exception:
        pass
        
    return os.environ.get("LOCALAPPDATA", "")

def obter_windows_directory() -> str:
    if os.name != 'nt':
        return os.environ.get("SystemRoot", r"C:\Windows")
        
    try:
        kernel32 = ctypes.windll.kernel32
        buf = ctypes.create_unicode_buffer(260)
        length = kernel32.GetWindowsDirectoryW(buf, 260)
        if length > 0:
            return buf.value
    except Exception:
        pass
        
    return os.environ.get("SystemRoot", r"C:\Windows")
