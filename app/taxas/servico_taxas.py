from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.core.calendario import eh_dia_util_simples
from app.core.modelos import Indexador
from app.taxas.cliente_bcb import ClienteBancoCentral
from app.taxas.repositorio_taxas import RepositorioTaxas


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
            raise ValueError(f"Indexador {indexador_texto} nao e atualizado pelo Banco Central.")

        taxas_locais = self.repositorio.carregar(indexador_texto)
        registros = self.cliente_bcb.buscar_serie(self.CODIGOS_SGS[indexador_texto], data_inicial, data_final)
        for registro in registros:
            taxas_locais[registro["data"]] = registro["valor"]
        self.repositorio.salvar(indexador_texto, taxas_locais)
        return self.filtrar(taxas_locais, data_inicial, data_final)

    def obter_taxas(self, indexador: Indexador | str, data_inicial: date, data_final: date, tentar_atualizar: bool = True) -> dict[date, Decimal]:
        indexador_texto = self.normalizar_indexador(indexador)
        if indexador_texto == Indexador.PREFIXADO.value:
            return {}

        taxas = self.repositorio.carregar(indexador_texto)
        if tentar_atualizar and self.precisa_atualizar(taxas, data_inicial, min(data_final, date.today())):
            try:
                taxas = self.atualizar(indexador_texto, data_inicial, min(data_final, date.today()))
            except Exception:
                taxas = self.repositorio.carregar(indexador_texto)

        return self.filtrar(taxas, data_inicial, data_final)

    def precisa_atualizar(self, taxas: dict[date, Decimal], inicio: date, fim: date) -> bool:
        if inicio > fim:
            return False
        atual = inicio
        while atual <= fim:
            if eh_dia_util_simples(atual) and atual not in taxas:
                return True
            atual += timedelta(days=1)
        return False

    def filtrar(self, taxas: dict[date, Decimal], inicio: date, fim: date) -> dict[date, Decimal]:
        return {data_taxa: valor for data_taxa, valor in taxas.items() if inicio <= data_taxa <= fim}

    def normalizar_indexador(self, indexador: Indexador | str) -> str:
        if isinstance(indexador, Indexador):
            return indexador.value
        return str(indexador).upper().strip()
