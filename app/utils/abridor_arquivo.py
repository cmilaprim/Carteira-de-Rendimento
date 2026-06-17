import os
import subprocess
import sys
from pathlib import Path

def abrir_arquivo(caminho):
    caminho_absoluto = os.path.abspath(str(caminho))
    if sys.platform.startswith("win"):
        os.startfile(caminho_absoluto)
    elif sys.platform == "darwin":
        subprocess.run(["open", caminho_absoluto], check=False)
    else:
        subprocess.run(["xdg-open", caminho_absoluto], check=False)
