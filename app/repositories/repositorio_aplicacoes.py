from decimal import Decimal
from sqlalchemy import Engine, text
from app.models.aplicacao import Aplicacao, Indexador, TipoProduto


class RepositorioAplicacoes:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def listar(self) -> list[Aplicacao]:
        with self.engine.connect() as conn:
            resultado = conn.execute(text("""
                SELECT f.*, b.nome AS banco_nome
                FROM f_aplicacao f
                LEFT JOIN d_banco b ON b.id = f.banco_id
                ORDER BY f.data_criacao DESC
            """))
            return [self.para_aplicacao(linha) for linha in resultado]

    def adicionar(self, aplicacao: Aplicacao) -> None:
        with self.engine.begin() as conn:
            linha = conn.execute(text("""
                INSERT INTO f_aplicacao (
                    nome_produto, valor_aplicado, data_emissao, data_vencimento,
                    indexador, percentual_indexador, taxa_prefixada_anual, spread_anual,
                    tipo_produto, banco_id, data_resgate, empresa_id
                ) VALUES (
                    :nome_produto, :valor_aplicado, :data_emissao, :data_vencimento,
                    :indexador, :percentual_indexador, :taxa_prefixada_anual, :spread_anual,
                    :tipo_produto, :banco_id, :data_resgate, :empresa_id
                ) RETURNING id
            """), self.para_dict(aplicacao)).fetchone()
            aplicacao.id = str(linha.id)

    def excluir(self, aplicacao_id: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM f_aplicacao WHERE id = :id"), {"id": int(aplicacao_id)})

    def obter(self, aplicacao_id: str) -> Aplicacao:
        with self.engine.connect() as conn:
            linha = conn.execute(text("""
                SELECT f.*, b.nome AS banco_nome
                FROM f_aplicacao f
                LEFT JOIN d_banco b ON b.id = f.banco_id
                WHERE f.id = :id
            """), {"id": int(aplicacao_id)}).fetchone()
        if linha is None:
            raise KeyError("Aplicacao nao encontrada.")
        return self.para_aplicacao(linha)

    def atualizar(self, aplicacao: Aplicacao) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("""
                UPDATE f_aplicacao SET
                    nome_produto         = :nome_produto,
                    valor_aplicado       = :valor_aplicado,
                    data_emissao         = :data_emissao,
                    data_vencimento      = :data_vencimento,
                    indexador            = :indexador,
                    percentual_indexador = :percentual_indexador,
                    taxa_prefixada_anual = :taxa_prefixada_anual,
                    spread_anual         = :spread_anual,
                    tipo_produto         = :tipo_produto,
                    banco_id             = :banco_id,
                    data_resgate         = :data_resgate,
                    empresa_id           = :empresa_id
                WHERE id = :id
            """), {**self.para_dict(aplicacao), "id": int(aplicacao.id)})

    def para_dict(self, aplicacao: Aplicacao) -> dict:
        return {
            "nome_produto":         aplicacao.nome_produto,
            "valor_aplicado":       float(aplicacao.valor_aplicado),
            "data_emissao":         aplicacao.data_emissao,
            "data_vencimento":      aplicacao.data_vencimento,
            "indexador":            aplicacao.indexador.value,
            "percentual_indexador": float(aplicacao.percentual_indexador),
            "taxa_prefixada_anual": float(aplicacao.taxa_prefixada_anual) if aplicacao.taxa_prefixada_anual is not None else None,
            "spread_anual":         float(aplicacao.spread_anual) if aplicacao.spread_anual is not None else None,
            "tipo_produto":         aplicacao.tipo_produto.value,
            "banco_id":             aplicacao.banco_id,
            "data_resgate":         aplicacao.data_resgate,
            "empresa_id":           int(aplicacao.empresa_id) if aplicacao.empresa_id else None,
        }

    def para_aplicacao(self, linha) -> Aplicacao:
        return Aplicacao(
            id=str(linha.id),
            nome_produto=linha.nome_produto,
            valor_aplicado=Decimal(str(linha.valor_aplicado)),
            data_emissao=linha.data_emissao,
            data_vencimento=linha.data_vencimento,
            indexador=Indexador(linha.indexador),
            percentual_indexador=Decimal(str(linha.percentual_indexador)),
            taxa_prefixada_anual=Decimal(str(linha.taxa_prefixada_anual)) if linha.taxa_prefixada_anual is not None else None,
            spread_anual=Decimal(str(linha.spread_anual)) if linha.spread_anual is not None else None,
            tipo_produto=TipoProduto(linha.tipo_produto),
            banco_id=linha.banco_id,
            banco=linha.banco_nome or "",
            empresa_id=str(linha.empresa_id) if linha.empresa_id else "",
            data_resgate=linha.data_resgate if linha.data_resgate else None,
        )
