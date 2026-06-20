from datetime import date
from decimal import Decimal
from sqlalchemy import Engine, text


class RepositorioTaxas:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def carregar(self, indexador: str) -> dict[date, Decimal]:
        query = text("select data, valor from f_taxa where indexador = :indexador")
        with self.engine.connect() as conn:
            resultado = conn.execute(query, {"indexador": indexador})
            taxas = {}
            for linha in resultado:
                data = linha.data
                valor = Decimal(str(linha.valor))
                taxas[data] = valor
            return taxas

    def salvar(self, indexador: str, taxas: dict[date, Decimal]) -> None:
        registros = []
        for data_taxa, valor in taxas.items():
            registros.append({
                "indexador": indexador,
                "data": data_taxa,
                "valor": valor,
            })
        
        query=text("""
            insert into f_taxa (indexador, data, valor)
            values (:indexador, :data, :valor)
            on conflict (indexador, data) do update set valor = excluded.valor
        """)
        
        with self.engine.begin() as conn:
            conn.execute(query, registros)