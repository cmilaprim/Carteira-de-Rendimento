import json
from datetime import date
from decimal import Decimal
from pathlib import Path

class RepositorioTaxas:
    def __init__(self):
        self.pasta = Path("data/taxas")
        self.pasta.mkdir(parents=True, exist_ok=True)

    def carregar(self, indexador: str) -> dict[date, Decimal]:
        caminho = self.caminho(indexador)
        if not caminho.exists() or caminho.stat().st_size == 0:
            return {}
        with caminho.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return {date.fromisoformat(item["data"]): Decimal(str(item["valor"])) for item in dados}

    def salvar(self, indexador: str, taxas: dict[date, Decimal]) -> None:
        caminho = self.caminho(indexador)
        dados = [
            {"data": data_taxa.isoformat(), "valor": str(valor)}
            for data_taxa, valor in sorted(taxas.items())
        ]
        temporario = caminho.with_suffix(".tmp")
        with temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
        temporario.replace(caminho)

    def caminho(self, indexador: str) -> Path:
        return self.pasta / f"{indexador.lower()}.json"
