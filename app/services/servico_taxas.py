from datetime import date, timedelta
from decimal import Decimal
import logging
from app.utils.calendario import eh_dia_util
from app.models.aplicacao import Indexador
from app.services.cliente_bcb import ClienteBancoCentral
from app.repositories.repositorio_taxas import RepositorioTaxas

class ServicoTaxas:
    CODIGOS_SGS = {Indexador.CDI.value: 12, Indexador.SELIC.value: 11}

    def __init__(self, logger):
        self.logger: logging.Logger = logger
        self.cliente_bcb = ClienteBancoCentral()
        self.repositorio = RepositorioTaxas()

    def atualizar(self, indexador: Indexador, data_inicial: date, data_final: date) -> dict[date, Decimal]:
        if indexador.value not in self.CODIGOS_SGS:
            self.logger.error(f"Tentativa de atualizar indexador nao suportado: {indexador.value}")
            raise ValueError(f"Indexador {indexador.value} nao e atualizado pelo Banco Central.")

        self.logger.info(f"Atualizando taxas {indexador.value} de {data_inicial} ate {data_final}.")

        taxas_locais = self.repositorio.carregar(indexador.value)
        self.logger.debug(f"Taxas locais carregadas para {indexador.value}: {len(taxas_locais)}")

        registros = self.cliente_bcb.buscar_serie(self.CODIGOS_SGS[indexador.value], data_inicial, data_final)
        self.logger.info(f"Registros recebidos do BCB para {indexador.value}: {len(registros)}")

        for registro in registros:
            taxas_locais[registro["data"]] = registro["valor"]

        self.repositorio.salvar(indexador.value, taxas_locais)
        taxas_filtradas = self.filtrar(taxas_locais, data_inicial, data_final)

        self.logger.info(f"Taxas {indexador.value} salvas. total_local={len(taxas_locais)} total_periodo={len(taxas_filtradas)}")
        return taxas_filtradas

    def obter_taxas(self, indexador: Indexador, data_inicial: date, data_final: date, tentar_atualizar: bool = True) -> dict[date, Decimal]:
        if indexador == Indexador.PREFIXADO:
            self.logger.debug("Indexador prefixado nao usa serie historica de taxas.")
            return {}

        taxas = self.repositorio.carregar(indexador.value)
        fim_atualizacao = min(data_final, date.today())
        self.logger.debug(f"Taxas carregadas para {indexador.value}: total={len(taxas)} periodo={data_inicial} ate {data_final} tentar_atualizar={tentar_atualizar}")
        if tentar_atualizar and self.precisa_atualizar(taxas, data_inicial, fim_atualizacao):
            try:
                self.logger.info(f"Taxas {indexador.value} incompletas. Tentando atualizar ate {fim_atualizacao}.")
                taxas = self.atualizar(indexador, data_inicial, fim_atualizacao)
            except Exception:
                self.logger.exception(f"Falha ao atualizar {indexador.value}. Usando taxas locais disponiveis.")
                taxas = self.repositorio.carregar(indexador.value)

        taxas_filtradas = self.filtrar(taxas, data_inicial, data_final)
        self.logger.debug(f"Taxas retornadas para {indexador.value} no periodo: {len(taxas_filtradas)}")
        return taxas_filtradas

    def precisa_atualizar(self, taxas: dict[date, Decimal], inicio: date, fim: date) -> bool:
        if inicio > fim:
            return False
        atual = inicio
        while atual <= fim:
            if eh_dia_util(atual) and atual not in taxas:
                self.logger.debug(f"Taxa ausente em dia util: {atual}")
                return True
            atual += timedelta(days=1)
        return False

    def filtrar(self, taxas: dict[date, Decimal], inicio: date, fim: date) -> dict[date, Decimal]:
        return {data_taxa: valor for data_taxa, valor in taxas.items() if inicio <= data_taxa <= fim}

