import flet as ft
import ctypes
import threading
import time

# Função para fazer a janela piscar
def flash_window(hwnd):
    class FLASHWINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.wintypes.DWORD),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("uCount", ctypes.wintypes.UINT),
            ("dwTimeout", ctypes.wintypes.DWORD)
        ]

    FLASHWINFO.cbSize = ctypes.sizeof(FLASHWINFO)
    FLASHWINFO.dwFlags = 0x00000003  # FLASHW_ALL
    FLASHWINFO.uCount = 3
    FLASHWINFO.dwTimeout = 0

    flash_info = FLASHWINFO()
    ctypes.windll.user32.FlashWindowEx(ctypes.byref(flash_info))

# Função para obter o identificador da janela Flet
def get_window_handle():
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    return hwnd

# Função para iniciar o alerta de piscar a janela
def simulate_flash():
    hwnd = get_window_handle()
    if hwnd:
        while True:
            time.sleep(5)  # Espera 5 segundos
            flash_window(hwnd)  # Faz a janela piscar
            time.sleep(5)  # Espera antes de piscar novamente

def main(page: ft.Page):
    # Adiciona um texto à página principal
    page.add(ft.Text("Minha Aplicação", size=30))

    # Inicia uma thread para simular o piscar da janela
    threading.Thread(target=simulate_flash, daemon=True).start()

ft.app(target=main)
