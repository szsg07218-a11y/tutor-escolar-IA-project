#!/usr/bin/env python3
import json
import os
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import urllib.request
import urllib.error

API_URL = os.getenv("TUTOR_API_URL", "http://127.0.0.1:8090/ask")
API_HEALTH_URL = os.getenv("TUTOR_API_HEALTH_URL", "http://127.0.0.1:8090/health")


class TutorTkinterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mi Tutor Escolar IA")
        self.geometry("560x460")
        self.minsize(420, 320)
        self.configure(bg="#F3F4F6")

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=8, pady=(8, 0))

        self.status_label = ttk.Label(top_frame, text="API: comprobando...", foreground="#6B7280")
        self.status_label.pack(side="left", fill="x", expand=True)

        self.output = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            state="disabled",
            bg="#FFFFFF",
            fg="#111827",
            insertbackground="#111827",
            font=("DejaVu Sans", 11),
            padx=10,
            pady=10,
        )
        self.output.pack(fill="both", expand=True, padx=8, pady=8)

        input_frame = ttk.Frame(self)
        input_frame.pack(fill="x", padx=8, pady=(0, 8))

        self.entry = ttk.Entry(input_frame, font=("DejaVu Sans", 11))
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry.bind("<Return>", lambda event: self.enviar())

        self.send_button = ttk.Button(input_frame, text="Enviar", command=self.enviar)
        self.send_button.pack(side="right")

        self.after(300, self.comprobar_api)
        self.agregar("Sistema: escribe tu pregunta y presiona Enter o Enviar.")
        self.agregar(f"API: {API_URL}")

    def agregar(self, texto):
        self.output.configure(state="normal")
        self.output.insert("end", texto + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def comprobar_api(self):
        try:
            with urllib.request.urlopen(API_HEALTH_URL, timeout=3) as response:
                data = json.loads(response.read().decode("utf-8"))
            if data.get("ok"):
                self.status_label.configure(text="API: conectada", foreground="#047857")
                self.agregar("API: conectada correctamente.")
            else:
                self.status_label.configure(text="API: respuesta inesperada", foreground="#B45309")
        except Exception as e:
            self.status_label.configure(text="API: no disponible", foreground="#B91C1C")
            self.agregar(f"API: no disponible. Inicia json_api_server.py primero. Error: {e}")

    def enviar(self):
        texto = self.entry.get().strip()
        if not texto:
            return
        self.entry.delete(0, "end")
        self.agregar(f"Tú: {texto}")
        self.agregar("Tutor: pensando...")
        self.send_button.configure(state="disabled")

        thread = threading.Thread(target=self.llamar_api, args=(texto,), daemon=True)
        thread.start()

    def llamar_api(self, texto):
        try:
            payload = json.dumps({"texto": texto}, ensure_ascii=False).encode("utf-8")
            request = urllib.request.Request(
                API_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=240) as response:
                data = json.loads(response.read().decode("utf-8"))
            if "error" in data:
                respuesta = f"Error del servidor: {data['error']}"
            else:
                respuesta = data.get("respuesta", "No hubo respuesta del tutor.")
            self.after(0, lambda: self.mostrar_respuesta(respuesta))
        except Exception as e:
            self.after(0, lambda: self.mostrar_respuesta(f"Error: {e}"))
        finally:
            self.after(0, lambda: self.send_button.configure(state="normal"))

    def mostrar_respuesta(self, respuesta):
        texto_actual = self.output.get("1.0", "end")
        texto_actual = texto_actual.replace("Tutor: pensando...\n", "")
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("end", texto_actual)
        self.output.insert("end", f"Tutor: {respuesta}\n")
        self.output.see("end")
        self.output.configure(state="disabled")


if __name__ == "__main__":
    app = TutorTkinterApp()
    app.mainloop()
