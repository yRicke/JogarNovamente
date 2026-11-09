"""Integração Windows: processo em foco, atalhos globais e Xbox virtual."""

import ctypes
import ntpath
import threading
from ctypes import wintypes


def _libraries():
    user = ctypes.WinDLL("user32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    user.GetForegroundWindow.argtypes = []
    user.GetForegroundWindow.restype = wintypes.HWND
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowThreadProcessId.restype = wintypes.DWORD
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    return user, kernel


class FortniteFocus:
    def __init__(self):
        self.user, self.kernel = _libraries()

    def __call__(self):
        pid = wintypes.DWORD()
        window = self.user.GetForegroundWindow()
        if not window or not self.user.GetWindowThreadProcessId(window, ctypes.byref(pid)):
            return False
        handle = self.kernel.OpenProcess(0x1000, False, pid.value)
        if not handle:
            return False
        try:
            size = wintypes.DWORD(32768)
            path = ctypes.create_unicode_buffer(size.value)
            if not self.kernel.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)):
                return False
            return ntpath.basename(path.value).lower() in {
                "fortniteclient-win64-shipping.exe",
                "fortniteclient-win64-shipping_eac.exe",
                "fortniteclient-win64-shipping_be.exe",
            }
        finally:
            self.kernel.CloseHandle(handle)


class XboxPad:
    def __init__(self):
        try:
            import vgamepad as vg
        except ImportError as exc:
            raise RuntimeError("Dependência ausente. Execute instalar.bat primeiro.") from exc
        self._button = vg.XUSB_BUTTON.XUSB_GAMEPAD_Y
        try:
            self._pad = vg.VX360Gamepad()
        except Exception as exc:
            raise RuntimeError(
                "Não foi possível conectar o Xbox virtual. Verifique o driver "
                "ViGEmBus e reinicie o Windows. Consulte README.md."
            ) from exc

    def tap_y(self, stop):
        if stop.is_set():
            return False
        try:
            self._pad.press_button(button=self._button)
            self._pad.update()
            stop.wait(0.12)
        finally:
            self._pad.release_button(button=self._button)
            self._pad.update()
        return True

    def close(self):
        try:
            self._pad.reset()
            self._pad.update()
        finally:
            self._pad = None  # Desconecta o dispositivo virtual.


class Hotkeys(threading.Thread):
    """Fila de mensagens própria, sem disputar eventos com o Tkinter."""

    def __init__(self, emit):
        super().__init__(name="atalhos-globais", daemon=True)
        self.emit = emit
        self.stop = threading.Event()

    def run(self):
        user = ctypes.WinDLL("user32", use_last_error=True)
        user.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        user.RegisterHotKey.restype = wintypes.BOOL
        user.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        user.UnregisterHotKey.restype = wintypes.BOOL
        user.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND,
                                      wintypes.UINT, wintypes.UINT, wintypes.UINT]
        user.PeekMessageW.restype = wintypes.BOOL
        registered = []
        try:
            for key_id, vk, label in [(1, 0x77, "F8"), (2, 0x78, "F9")]:
                if user.RegisterHotKey(None, key_id, 0x4000, vk):
                    registered.append(key_id)
                else:
                    self.emit("hotkey_warning", f"{label} indisponível; use os botões da janela.")
            msg = wintypes.MSG()
            while not self.stop.is_set():
                while user.PeekMessageW(ctypes.byref(msg), None, 0x0312, 0x0312, 1):
                    self.emit("toggle" if msg.wParam == 1 else "stop", None)
                self.stop.wait(0.03)
        finally:
            for key_id in registered:
                user.UnregisterHotKey(None, key_id)
