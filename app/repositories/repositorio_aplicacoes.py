import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Iterable
from app.models.aplicacao import Aplicacao, Indexador, TipoProduto

class RepositorioAplicacoes:
    def __init__(self) -> None:
        self.caminho = Path("data/aplicacoes.json")
        self.caminho.parent.mkdir(parents=True, exist_ok=True)

    def listar(self) -> list[Aplicacao]:
        if not self.caminho.exists() or self.caminho.stat().st_size == 0:
            return []
        with self.caminho.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return [self.para_aplicacao(item) for item in dados]

    def salvar_todos(self, aplicacoes: Iterable[Aplicacao]) -> None:
        dados = [self.para_dict(aplicacao) for aplicacao in aplicacoes]
        temporario = self.caminho.with_suffix(".tmp")
        with temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
        temporario.replace(self.caminho)

    def adicionar(self, aplicacao: Aplicacao) -> None:
        aplicacoes = self.listar()
        aplicacoes.append(aplicacao)
        self.salvar_todos(aplicacoes)

    def excluir(self, aplicacao_id: str) -> None:
        aplicacoes = [item for item in self.listar() if item.id != aplicacao_id]
        self.salvar_todos(aplicacoes)

    def obter(self, aplicacao_id: str) -> Aplicacao:
        for aplicacao in self.listar():
            if aplicacao.id == aplicacao_id:
                return aplicacao
        raise KeyError("Aplicacao nao encontrada.")

    def atualizar(self, aplicacao: Aplicacao) -> None:
        aplicacoes = self.listar()
        for indice, atual in enumerate(aplicacoes):
            if atual.id == aplicacao.id:
                aplicacoes[indice] = aplicacao
                self.salvar_todos(aplicacoes)
                return
        raise KeyError("Aplicacao nao encontrada.")

    def para_dict(self, aplicacao: Aplicacao) -> dict:
        return {
            "versao": 2,
            "id": aplicacao.id,
            "nome_produto": aplicacao.nome_produto,
            "numero_controle": aplicacao.numero_controle,
            "numero_nota": aplicacao.numero_nota,
            "valor_aplicado": str(aplicacao.valor_aplicado),
            "data_emissao": aplicacao.data_emissao.isoformat(),
            "data_vencimento": aplicacao.data_vencimento.isoformat(),
            "indexador": aplicacao.indexador.value,
            "percentual_indexador": str(aplicacao.percentual_indexador),
            "taxa_prefixada_anual": None if aplicacao.taxa_prefixada_anual is None else str(aplicacao.taxa_prefixada_anual),
            "tipo_produto": aplicacao.tipo_produto.value,
            "data_resgate": aplicacao.data_resgate.isoformat() if aplicacao.data_resgate else None,
        }

    def para_aplicacao(self, dados: dict) -> Aplicacao:
        return Aplicacao(
            id=dados["id"],
            nome_produto=dados["nome_produto"],
            numero_controle=dados.get("numero_controle", ""),
            numero_nota=dados.get("numero_nota", ""),
            valor_aplicado=Decimal(str(dados["valor_aplicado"])),
            data_emissao=date.fromisoformat(dados["data_emissao"]),
            data_vencimento=date.fromisoformat(dados["data_vencimento"]),
            indexador=Indexador(dados["indexador"]),
            percentual_indexador=Decimal(str(dados.get("percentual_indexador", "100"))),
            taxa_prefixada_anual=None if dados.get("taxa_prefixada_anual") is None else Decimal(str(dados["taxa_prefixada_anual"])),
            tipo_produto=TipoProduto(dados.get("tipo_produto", TipoProduto.CDB.value)),
            data_resgate=date.fromisoformat(dados["data_resgate"]) if dados.get("data_resgate") else None,
        )
