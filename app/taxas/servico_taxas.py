from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal

from app.core.calendario import eh_dia_util
from app.core.modelos import Indexador
from app.taxas.cliente_bcb import ClienteBancoCentral
from app.taxas.repositorio_taxas import RepositorioTaxas

logger = logging.getLogger(__name__)


class ServicoTaxas:
    CODIGOS_SGS = {
        Indexador.CDI.value: 12,     
        Indexador.SELIC.value: 11,  
    }

    def __init__(self, cliente_bcb: ClienteBancoCentral | None = None, repositorio: RepositorioTaxas | None = None) -> None:
        self.cliente_bcb = cliente_bcb or ClienteBancoCentral()
        self.repositorio = repositorio or RepositorioTaxas()

    def atualizar(self, indexador: Indexador | str, data_inicial: date, data_final: date) -> dict[date, Decimal]:
        indexador_texto = self.normalizar_indexador(indexador)
        if indexador_texto not in self.CODIGOS_SGS:
            logger.error("Tentativa de atualizar indexador nao suportado: %s", indexador_texto)
            raise ValueError(f"Indexador {indexador_texto} nao e atualizado pelo Banco Central.")

        logger.info("Atualizando taxas %s de %s ate %s.", indexador_texto, data_inicial, data_final)
        
        taxas_locais = self.repositorio.carregar(indexador_texto)
        logger.debug("Taxas locais carregadas para %s: %d", indexador_texto, len(taxas_locais))
        
        registros = self.cliente_bcb.buscar_serie(self.CODIGOS_SGS[indexador_texto], data_inicial, data_final)
        logger.info("Registros recebidos do BCB para %s: %d", indexador_texto, len(registros))
        
        for registro in registros:
            taxas_locais[registro["data"]] = registro["valor"]
        
        self.repositorio.salvar(indexador_texto, taxas_locais)
        taxas_filtradas = self.filtrar(taxas_locais, data_inicial, data_final)
        
        logger.info("Taxas %s salvas. total_local=%d total_periodo=%d", indexador_texto, len(taxas_locais), len(taxas_filtradas))
        return taxas_filtradas

    def obter_taxas(self, indexador: Indexador | str, data_inicial: date, data_final: date, tentar_atualizar: bool = True) -> dict[date, Decimal]:
        indexador_texto = self.normalizar_indexador(indexador)
        if indexador_texto == Indexador.PREFIXADO.value:
            logger.debug("Indexador prefixado nao usa serie historica de taxas.")
            return {}

        taxas = self.repositorio.carregar(indexador_texto)
        fim_atualizacao = min(data_final, date.today())
        logger.debug("Taxas carregadas para %s: total=%d periodo=%s ate %s tentar_atualizar=%s", indexador_texto, len(taxas), data_inicial, data_final, tentar_atualizar)
        if tentar_atualizar and self.precisa_atualizar(taxas, data_inicial, fim_atualizacao):
            try:
                logger.info("Taxas %s incompletas. Tentando atualizar ate %s.", indexador_texto, fim_atualizacao)
                taxas = self.atualizar(indexador_texto, data_inicial, fim_atualizacao)
            except Exception:
                logger.exception("Falha ao atualizar %s. Usando taxas locais disponiveis.", indexador_texto)
                taxas = self.repositorio.carregar(indexador_texto)

        taxas_filtradas = self.filtrar(taxas, data_inicial, data_final)
        logger.debug("Taxas retornadas para %s no periodo: %d", indexador_texto, len(taxas_filtradas))
        return taxas_filtradas

    def precisa_atualizar(self, taxas: dict[date, Decimal], inicio: date, fim: date) -> bool:
        if inicio > fim:
            return False
        atual = inicio
        while atual <= fim:
            if eh_dia_util(atual) and atual not in taxas:
                logger.debug("Taxa ausente em dia util: %s", atual)
                return True
            atual += timedelta(days=1)
        return False

    def filtrar(self, taxas: dict[date, Decimal], inicio: date, fim: date) -> dict[date, Decimal]:
        return {data_taxa: valor for data_taxa, valor in taxas.items() if inicio <= data_taxa <= fim}

    def normalizar_indexador(self, indexador: Indexador | str) -> str:
        if isinstance(indexador, Indexador):
            return indexador.value
        return str(indexador).upper().strip()
