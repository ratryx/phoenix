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

if os.name == 'nt':
    shell32 = ctypes.windll.shell32
    shell32.SHGetKnownFolderPath.argtypes = [
        ctypes.POINTER(GUID),
        wintypes.DWORD,
        wintypes.HANDLE,
        ctypes.POINTER(ctypes.c_wchar_p)
    ]
    shell32.SHGetKnownFolderPath.restype = ctypes.c_long

    ole32 = ctypes.windll.ole32
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    ole32.CoTaskMemFree.restype = None

    kernel32 = ctypes.windll.kernel32
    kernel32.GetWindowsDirectoryW.argtypes = [wintypes.LPWSTR, wintypes.UINT]
    kernel32.GetWindowsDirectoryW.restype = wintypes.UINT

def obter_local_appdata() -> str:
    if os.name != 'nt':
        return os.environ.get("LOCALAPPDATA", "")
        
    try:
        path_ptr = ctypes.c_wchar_p()
        hr = shell32.SHGetKnownFolderPath(ctypes.byref(FOLDERID_LocalAppData), 0, None, ctypes.byref(path_ptr))
        if hr == 0 and path_ptr.value:
            res = path_ptr.value
            ole32.CoTaskMemFree(path_ptr)
            return res
    except Exception:
        pass
        
    return ""

def obter_windows_directory() -> str:
    if os.name != 'nt':
        return os.environ.get("SystemRoot", r"C:\Windows")
        
    try:
        buf_size = 260
        buf = ctypes.create_unicode_buffer(buf_size)
        length = kernel32.GetWindowsDirectoryW(buf, buf_size)
        
        if length > buf_size:
            # Buffer was too small, allocate with returned size
            buf = ctypes.create_unicode_buffer(length)
            length = kernel32.GetWindowsDirectoryW(buf, length)
            
        if 0 < length <= len(buf):
            return buf.value
    except Exception:
        pass
        
    return ""
