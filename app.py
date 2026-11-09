"""Interface para repetição periódica do botão Y no Windows."""

import argparse
import os
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from engine import Settings, run
from windows_io import FortniteFocus, Hotkeys, XboxPad


class App:
    def __init__(self, root, simulate=False):
        self.root = root
        self.events = queue.Queue()
        self.worker = None
        self.stop_event = threading.Event()
        self.closing = False
        self.focus = FortniteFocus()
        root.title("Jogar novamente")
        root.geometry("540x640")
        root.minsize(540, 640)
        root.configure(bg="#10151e")
        root.protocol("WM_DELETE_WINDOW", self.close)

        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background="#10151e")
        style.configure("TLabel", background="#10151e", foreground="#e6edf7", font=("Segoe UI", 11))
        style.configure("Title.TLabel", font=("Segoe UI", 25, "bold"))
        style.configure("Muted.TLabel", foreground="#a6b5cb", font=("Segoe UI", 10))
        style.configure("State.TLabel", foreground="#b9ff68", font=("Segoe UI", 11, "bold"))
        style.configure("TCheckbutton", background="#10151e", foreground="#e6edf7", font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", "#10151e")])
        style.configure("TButton", font=("Segoe UI", 12, "bold"), padding=12)

        frame = ttk.Frame(root, padding=28)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Jogar novamente", style="Title.TLabel").pack(anchor="w")
        ttk.Label(frame, text="Botão Y e analógicos · controle Xbox virtual", style="Muted.TLabel").pack(anchor="w", pady=(4, 24))
        self.status = tk.StringVar(value="Desligado")
        ttk.Label(frame, textvariable=self.status, style="State.TLabel", wraplength=475).pack(anchor="w")
        self.count = tk.StringVar(value="Comandos nesta sessão: 0")
        ttk.Label(frame, textvariable=self.count, style="Muted.TLabel").pack(anchor="w", pady=(8, 22))
        self.movements = tk.StringVar(value="Movimentos dos analógicos: 0")
        ttk.Label(frame, textvariable=self.movements, style="Muted.TLabel").pack(anchor="w", pady=(0, 12))

        ttk.Label(frame, text="Intervalo aleatório entre comandos (segundos)").pack(anchor="w")
        fields = ttk.Frame(frame)
        fields.pack(fill="x", pady=(10, 18))
        self.minimum = tk.StringVar(value="3")
        self.maximum = tk.StringVar(value="10")
        ttk.Label(fields, text="Mínimo").grid(row=0, column=0, sticky="w")
        ttk.Label(fields, text="Máximo").grid(row=0, column=1, sticky="w", padx=(22, 0))
        self.min_entry = ttk.Entry(fields, textvariable=self.minimum, width=17, font=("Segoe UI", 12))
        self.max_entry = ttk.Entry(fields, textvariable=self.maximum, width=17, font=("Segoe UI", 12))
        self.min_entry.grid(row=1, column=0, pady=(6, 0))
        self.max_entry.grid(row=1, column=1, padx=(22, 0), pady=(6, 0))
        self.simulate = tk.BooleanVar(value=simulate)
        self.sim_check = ttk.Checkbutton(frame, text="Simular sem enviar comandos (dispensa o jogo)", variable=self.simulate)
        self.sim_check.pack(anchor="w", pady=(0, 16))
        self.move_sticks = tk.BooleanVar(value=True)
        self.sticks_check = ttk.Checkbutton(
            frame, text="Mover os dois analógicos ocasionalmente (20–45 s)",
            variable=self.move_sticks)
        self.sticks_check.pack(anchor="w", pady=(0, 16))

        self.button = ttk.Button(frame, text="Ligar", command=self.toggle)
        self.button.pack(fill="x")
        ttk.Label(frame, text="F8  ligar / desligar       F9  parar", style="Muted.TLabel").pack(anchor="w", pady=(12, 18))
        ttk.Label(frame, text="O envio pausa quando você sai do Fortnite.\nNão há captura nem armazenamento de imagens.",
                  style="Muted.TLabel", wraplength=475).pack(anchor="w")
        ttk.Label(frame, text="Y e analógicos também atuam durante a partida.\nIntervalos aleatórios não eliminam o risco de banimento.",
                  style="Muted.TLabel", wraplength=475).pack(anchor="w", pady=(12, 0))
        self.hotkey_note = tk.StringVar()
        ttk.Label(frame, textvariable=self.hotkey_note, style="Muted.TLabel", wraplength=475).pack(anchor="w", pady=(8, 0))

        self.hotkeys = Hotkeys(self.emit)
        self.hotkeys.start()
        root.after(50, self.poll)

    def emit(self, kind, value):
        self.events.put((kind, value))

    def toggle(self):
        if self.closing:
            return
        if self.worker is not None:
            self.stop()
            return
        try:
            settings = Settings(float(self.minimum.get().replace(",", ".")),
                                float(self.maximum.get().replace(",", ".")), self.simulate.get(),
                                self.move_sticks.get())
        except ValueError as exc:
            messagebox.showerror("Confira os intervalos", str(exc), parent=self.root)
            return
        self.stop_event = threading.Event()
        self.count.set("Comandos nesta sessão: 0")
        self.movements.set("Movimentos dos analógicos: 0")
        self.status.set("Conectando o controle…" if not settings.simulate else "Iniciando simulação…")
        for widget in (self.min_entry, self.max_entry, self.sim_check, self.sticks_check):
            widget.configure(state="disabled")
        self.button.configure(text="Desligar")
        self.worker = threading.Thread(target=run, args=(
            settings, self.stop_event, self.focus, XboxPad, self.emit), name="repetidor-y")
        self.worker.start()

    def stop(self):
        if self.worker is not None:
            self.stop_event.set()
            self.button.configure(text="Parando…", state="disabled")
            self.status.set("Parando e liberando o controle…")

    def poll(self):
        while True:
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "status" and not self.stop_event.is_set():
                self.status.set(value)
            elif kind == "count":
                label = "Simulações" if self.simulate.get() else "Comandos"
                self.count.set(f"{label} nesta sessão: {value}")
            elif kind == "movements":
                label = "Movimentos simulados" if self.simulate.get() else "Movimentos dos analógicos"
                self.movements.set(f"{label}: {value}")
            elif kind == "error":
                if not self.closing:
                    messagebox.showerror("Falha no controle", value, parent=self.root)
            elif kind == "toggle":
                self.toggle()
            elif kind == "stop":
                self.stop()
            elif kind == "hotkey_warning":
                self.hotkey_note.set(value)

        # Aguarda a saída real do worker antes de permitir uma nova sessão.
        if self.worker is not None and not self.worker.is_alive():
            self.worker.join()
            self.worker = None
            self.status.set("Desligado")
            self.button.configure(text="Ligar", state="normal")
            for widget in (self.min_entry, self.max_entry, self.sim_check, self.sticks_check):
                widget.configure(state="normal")
        if self.closing and self.worker is None and not self.hotkeys.is_alive():
            self.root.destroy()
            return
        self.root.after(50, self.poll)

    def close(self):
        self.closing = True
        self.stop()
        self.button.configure(state="disabled")
        self.hotkeys.stop.set()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simular", action="store_true", help="abre com a simulação selecionada")
    parser.add_argument("--ligar", action="store_true", help="inicia o envio ao abrir a interface")
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("Este aplicativo usa o controle virtual do Windows 10/11.")
    root = tk.Tk()
    app = App(root, simulate=args.simular)
    if args.ligar:
        root.after(200, app.toggle)
    root.mainloop()


if __name__ == "__main__":
    main()
