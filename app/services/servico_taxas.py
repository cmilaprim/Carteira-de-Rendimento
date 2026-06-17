import logging
from datetime import date, timedelta
from decimal import Decimal

from app.utils.calendario import eh_dia_util
from app.models.aplicacao import Indexador
from app.services.cliente_bcb import ClienteBancoCentral
from app.repositories.repositorio_taxas import RepositorioTaxas


class ServicoTaxas:
    CODIGOS_SGS = {
        Indexador.CDI.value: 12,
        Indexador.SELIC.value: 11,
    }

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.cliente_bcb = ClienteBancoCentral()
        self.repositorio = RepositorioTaxas()

    def atualizar(self, indexador: Indexador | str, data_inicial: date, data_final: date) -> dict[date, Decimal]:
        indexador_texto = self.normalizar_indexador(indexador)
        if indexador_texto not in self.CODIGOS_SGS:
            self.logger.error(f"Tentativa de atualizar indexador nao suportado: {indexador_texto}")
            raise ValueError(f"Indexador {indexador_texto} nao e atualizado pelo Banco Central.")

        self.logger.info(f"Atualizando taxas {indexador_texto} de {data_inicial} ate {data_final}.")

        taxas_locais = self.repositorio.carregar(indexador_texto)
        self.logger.debug(f"Taxas locais carregadas para {indexador_texto}: {len(taxas_locais)}")

        registros = self.cliente_bcb.buscar_serie(self.CODIGOS_SGS[indexador_texto], data_inicial, data_final)
        self.logger.info(f"Registros recebidos do BCB para {indexador_texto}: {len(registros)}")

        for registro in registros:
            taxas_locais[registro["data"]] = registro["valor"]

        self.repositorio.salvar(indexador_texto, taxas_locais)
        taxas_filtradas = self.filtrar(taxas_locais, data_inicial, data_final)

        self.logger.info(f"Taxas {indexador_texto} salvas. total_local={len(taxas_locais)} total_periodo={len(taxas_filtradas)}")
        return taxas_filtradas

    def obter_taxas(self, indexador: Indexador | str, data_inicial: date, data_final: date, tentar_atualizar: bool = True) -> dict[date, Decimal]:
        indexador_texto = self.normalizar_indexador(indexador)
        if indexador_texto == Indexador.PREFIXADO.value:
            self.logger.debug("Indexador prefixado nao usa serie historica de taxas.")
            return {}

        taxas = self.repositorio.carregar(indexador_texto)
        fim_atualizacao = min(data_final, date.today())
        self.logger.debug(f"Taxas carregadas para {indexador_texto}: total={len(taxas)} periodo={data_inicial} ate {data_final} tentar_atualizar={tentar_atualizar}")
        if tentar_atualizar and self.precisa_atualizar(taxas, data_inicial, fim_atualizacao):
            try:
                self.logger.info(f"Taxas {indexador_texto} incompletas. Tentando atualizar ate {fim_atualizacao}.")
                taxas = self.atualizar(indexador_texto, data_inicial, fim_atualizacao)
            except Exception:
                self.logger.exception(f"Falha ao atualizar {indexador_texto}. Usando taxas locais disponiveis.")
                taxas = self.repositorio.carregar(indexador_texto)

        taxas_filtradas = self.filtrar(taxas, data_inicial, data_final)
        self.logger.debug(f"Taxas retornadas para {indexador_texto} no periodo: {len(taxas_filtradas)}")
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

    def normalizar_indexador(self, indexador: Indexador | str) -> str:
        if isinstance(indexador, Indexador):
            return indexador.value
        return str(indexador).upper().strip()
