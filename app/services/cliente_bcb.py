from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable

import requests

logger = logging.getLogger(__name__)


class ClienteBancoCentral:
    URL_BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"

    def buscar_serie(self, codigo: int, data_inicial: date, data_final: date) -> list[dict]:
        logger.info(f"Buscando serie BCB {codigo} de {data_inicial} ate {data_final}")

        try:
            registros: list[dict] = []
            for inicio, fim in self.quebrar_periodo(data_inicial, data_final):
                parametros = {
                    "formato": "json",
                    "dataInicial": inicio.strftime("%d/%m/%Y"),
                    "dataFinal": fim.strftime("%d/%m/%Y"),
                }
                logger.debug(f"Parametros enviados ao BCB: {parametros}")
                resposta = requests.get(self.URL_BASE.format(codigo=codigo), params=parametros, timeout=30)
                logger.debug(f"Resposta BCB serie {codigo}: status={resposta.status_code}")
                if resposta.status_code == 404:
                    logger.warning(f"BCB nao retornou dados para a serie {codigo} entre {inicio} e {fim}.")
                    continue
                resposta.raise_for_status()
                itens = resposta.json()
                logger.info(f"BCB retornou {len(itens)} registros para a serie {codigo} entre {inicio} e {fim}.")
                for item in itens:
                    registros.append({
                        "data": self.converter_data_bcb(item["data"]),
                        "valor": Decimal(str(item["valor"]).replace(",", "."))
                    })
        except requests.RequestException as e:
            logger.exception(f"Erro ao buscar serie BCB {codigo}: {e}")
            raise
        logger.info(f"Busca BCB finalizada para serie {codigo}: total_registros={len(registros)}")
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
