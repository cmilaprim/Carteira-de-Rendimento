import json
from datetime import date
from decimal import Decimal
from pathlib import Path


class RepositorioTaxas:
    def __init__(self) -> None:
        self.pasta = Path("data/taxas")
        self.pasta.mkdir(parents=True, exist_ok=True)

    def carregar(self, indexador: str) -> dict[date, Decimal]:
        arquivo = self.pasta / f"{indexador}.json"
        if not arquivo.exists():
            return {}
        with arquivo.open("r", encoding="utf-8") as f:
            dados = json.load(f)
        return {date.fromisoformat(k): Decimal(str(v)) for k, v in dados.items()}

    def salvar(self, indexador: str, taxas: dict[date, Decimal]) -> None:
        arquivo = self.pasta / f"{indexador}.json"
        with arquivo.open("w", encoding="utf-8") as f:
            json.dump({k.isoformat(): str(v) for k, v in taxas.items()}, f)
