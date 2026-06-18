import json
from pathlib import Path


class RepositorioBancos:
    def __init__(self) -> None:
        self.caminho = Path("data/bancos.json")

    def listar(self) -> list[str]:
        if not self.caminho.exists() or self.caminho.stat().st_size == 0:
            return []
        with self.caminho.open("r", encoding="utf-8") as f:
            return json.load(f)
