import tkinter as tk
from tkinter import ttk
from decimal import Decimal


def mascara_data(entry: ttk.Entry) -> None:
    def formatar(event=None):
        if event and event.keysym in ("Left", "Right", "Home", "End", "Tab", "Up", "Down"):
            return
        digitos = ''.join(c for c in entry.get() if c.isdigit())[:8]
        if len(digitos) >= 5:
            texto = f"{digitos[:2]}/{digitos[2:4]}/{digitos[4:]}"
        elif len(digitos) >= 3:
            texto = f"{digitos[:2]}/{digitos[2:]}"
        else:
            texto = digitos
        entry.delete(0, tk.END)
        entry.insert(0, texto)

    entry.bind("<KeyRelease>", formatar)


def mascara_decimal(entry: ttk.Entry) -> None:
    def formatar(event=None):
        if event and event.keysym in ("Left", "Right", "Home", "End", "Tab", "Up", "Down"):
            return
        # Converte ponto digitado para vírgula (separador decimal BR)
        if event and event.keysym == "period":
            val = entry.get()
            idx = val.rfind(".")
            if idx != -1 and "," not in val:
                entry.delete(idx, idx + 1)
                entry.insert(idx, ",")
        texto = entry.get().replace(".", "")
        tem_decimal = "," in texto
        partes = texto.split(",", 1)
        inteiro_raw = ''.join(c for c in partes[0] if c.isdigit())
        decimal_raw = ''.join(c for c in partes[1] if c.isdigit())[:2] if tem_decimal else None

        if inteiro_raw:
            inteiro_fmt = f"{int(inteiro_raw):,}".replace(",", ".")
        else:
            inteiro_fmt = "0" if tem_decimal else ""

        resultado = f"{inteiro_fmt},{decimal_raw}" if decimal_raw is not None else inteiro_fmt
        entry.delete(0, tk.END)
        entry.insert(0, resultado)
        entry.icursor(tk.END)

    entry.bind("<KeyRelease>", formatar)


def decimal_para_br(valor) -> str:
    """Converte Decimal/float para string no formato brasileiro: 1.000,50"""
    s = str(valor)
    if "." in s:
        inteiro, dec = s.split(".", 1)
        return f"{int(inteiro):,}".replace(",", ".") + f",{dec[:2]}"
    return f"{int(s):,}".replace(",", ".")
