import json
from pathlib import Path


class RepositorioBancos:
    def __init__(self) -> None:
        self.caminho = Path("data/bancos.json")
        self.caminho.parent.mkdir(parents=True, exist_ok=True)

    def listar(self) -> list[str]:
        if not self.caminho.exists() or self.caminho.stat().st_size == 0:
            return []
        with self.caminho.open("r", encoding="utf-8") as f:
            return json.load(f)

    def adicionar(self, nome: str) -> None:
        nome = nome.strip()
        if not nome:
            return
        bancos = self.listar()
        if nome not in bancos:
            bancos.append(nome)
            bancos.sort()
            self.salvar(bancos)

    def remover(self, nome: str) -> None:
        self.salvar([b for b in self.listar() if b != nome])

    def salvar(self, bancos: list[str]) -> None:
        temporario = self.caminho.with_suffix(".tmp")
        with temporario.open("w", encoding="utf-8") as f:
            json.dump(bancos, f, ensure_ascii=False, indent=2)
        temporario.replace(self.caminho)
