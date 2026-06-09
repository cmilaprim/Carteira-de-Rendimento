from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def abrir_arquivo(caminho: str | Path) -> None:
    caminho_absoluto = os.path.abspath(str(caminho))
    logger.info("Abrindo arquivo: %s", caminho_absoluto)
    if sys.platform.startswith("win"):
        os.startfile(caminho_absoluto)
    elif sys.platform == "darwin":
        subprocess.run(["open", caminho_absoluto], check=False)
    else:
        subprocess.run(["xdg-open", caminho_absoluto], check=False)
