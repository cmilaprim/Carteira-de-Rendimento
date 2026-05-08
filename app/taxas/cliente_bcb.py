from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable
import requests


class ClienteBancoCentral:
    URL_BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"

    def buscar_serie(self, codigo: int, data_inicial: date, data_final: date) -> list[dict]:
        registros: list[dict] = []
        for inicio, fim in self.quebrar_periodo(data_inicial, data_final):
            parametros = {
                "formato": "json",
                "dataInicial": inicio.strftime("%d/%m/%Y"),
                "dataFinal": fim.strftime("%d/%m/%Y"),
            }
            resposta = requests.get(self.URL_BASE.format(codigo=codigo), params=parametros, timeout=30)
            resposta.raise_for_status()
            for item in resposta.json():
                registros.append({
                    "data": self.converter_data_bcb(item["data"]),
                    "valor": Decimal(str(item["valor"]).replace(",", "."))
                })
        return registros

    def converter_data_bcb(self, texto: str) -> date:
        dia, mes, ano = texto.split("/")
        return date(int(ano), int(mes), int(dia))

    def quebrar_periodo(self, data_inicial: date, data_final: date) -> Iterable[tuple[date, date]]:
        inicio = data_inicial
        while inicio <= data_final:
            fim = min(data_final, inicio + timedelta(days=3650))
            yield inicio, fim
            inicio = fim + timedelta(days=1)
