from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.utils.conversores import texto_para_data, texto_para_decimal
from app.utils.formatadores import data_br, moeda_com_simbolo
from app.models.aplicacao import Aplicacao, Indexador, TipoProduto
from app.repositories.repositorio_aplicacoes import RepositorioAplicacoes
from app.services.demonstrativo import MontadorDemonstrativo
from app.services.servico_taxas import ServicoTaxas
from app.services.relatorio_pdf import RelatorioDemonstrativoCarteiraPDF


@dataclass(frozen=True)
class DadosAplicacaoFormulario:
    nome_produto: str
    numero_controle: str
    numero_nota: str
    valor_aplicado: str
    data_emissao: str
    data_vencimento: str
    indexador: str
    percentual_indexador: str
    taxa_prefixada: str
    tipo_produto: str = TipoProduto.CDB.value


@dataclass(frozen=True)
class LinhaAplicacaoLista:
    id: str
    produto: str
    tipo: str
    controle: str
    emissao: str
    vencimento: str
    taxa: str
    valor: str


class CarteiraController:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.repositorio = RepositorioAplicacoes()
        self.servico_taxas = ServicoTaxas(logger=self.logger)
        self.montador_demonstrativo = MontadorDemonstrativo(logger=self.logger)
        self.relatorio_pdf = RelatorioDemonstrativoCarteiraPDF()

    def indexadores(self) -> list[str]:
        return [item.value for item in Indexador]

    def tipos_produto(self) -> list[str]:
        return [item.value for item in TipoProduto]

    def listar_aplicacoes(self) -> list[LinhaAplicacaoLista]:
        aplicacoes = self.repositorio.listar()
        self.logger.debug(f"Listando aplicacoes para a tela: total={len(aplicacoes)}")
        return [self.linha_lista(aplicacao) for aplicacao in aplicacoes]

    def salvar_aplicacao(self, dados: DadosAplicacaoFormulario) -> Aplicacao:
        self.logger.info("Solicitacao de cadastro de aplicacao recebida.")
        indexador = Indexador(dados.indexador)
        taxa_prefixada = None
        if indexador == Indexador.PREFIXADO:
            taxa_prefixada = texto_para_decimal(dados.taxa_prefixada)

        aplicacao = Aplicacao.criar(
            nome_produto=dados.nome_produto,
            numero_controle=dados.numero_controle,
            numero_nota=dados.numero_nota,
            valor_aplicado=texto_para_decimal(dados.valor_aplicado),
            data_emissao=texto_para_data(dados.data_emissao),
            data_vencimento=texto_para_data(dados.data_vencimento),
            indexador=indexador,
            percentual_indexador=texto_para_decimal(dados.percentual_indexador),
            taxa_prefixada_anual=taxa_prefixada,
            tipo_produto=TipoProduto(dados.tipo_produto)
        )

        self.logger.info(f"Salvando aplicacao {aplicacao.id}: produto={aplicacao.nome_produto} controle={aplicacao.numero_controle} indexador={aplicacao.indexador.value} valor={aplicacao.valor_aplicado} emissao={aplicacao.data_emissao} vencimento={aplicacao.data_vencimento}")
        self.repositorio.adicionar(aplicacao)
        self.logger.info(f"Aplicacao {aplicacao.id} salva com sucesso.")
        return aplicacao

    def excluir_aplicacao(self, aplicacao_id: str) -> None:
        self.logger.info(f"Excluindo aplicacao selecionada: {aplicacao_id}")
        self.repositorio.excluir(aplicacao_id)
        self.logger.info(f"Aplicacao excluida com sucesso: {aplicacao_id}")

    def atualizar_taxas(self, data_saldo_texto: str) -> str:
        self.logger.info("Solicitacao de atualizacao de taxas recebida.")
        aplicacoes = self.repositorio.listar()
        if not aplicacoes:
            self.logger.info("Atualizacao de taxas ignorada: nenhuma aplicacao cadastrada.")
            return "Cadastre uma aplicacao antes de atualizar as taxas."

        inicio = min(aplicacao.data_emissao for aplicacao in aplicacoes)
        fim = texto_para_data(data_saldo_texto)
        fim_busca = min(fim, date.today())
        if inicio > fim_busca:
            self.logger.info(f"Atualizacao de taxas ignorada: inicio={inicio} fim_busca={fim_busca}")
            return "Nao ha datas historicas para atualizar."

        self.logger.info(f"Atualizando CDI/Selic de {inicio} ate {fim_busca}.")
        self.servico_taxas.atualizar(Indexador.CDI, inicio, fim_busca)
        self.servico_taxas.atualizar(Indexador.SELIC, inicio, fim_busca)
        self.logger.info("Taxas CDI/Selic atualizadas com sucesso.")
        return "Taxas CDI/Selic atualizadas e salvas em JSON."

    def gerar_documento_carteira(self, aplicacao_ids: list[str], data_saldo_texto: str) -> Path:
        aplicacoes = [self.repositorio.obter(id) for id in aplicacao_ids]
        data_saldo = texto_para_data(data_saldo_texto)
        self.logger.info(f"Gerando demonstrativo da carteira: aplicacoes={len(aplicacoes)} saldo={data_saldo}")
        demonstrativo = self.montador_demonstrativo.montar(aplicacoes, data_saldo)
        caminho = self.relatorio_pdf.gerar(demonstrativo)
        self.logger.info(f"Demonstrativo da carteira gerado com sucesso: {caminho}")
        return caminho

    def gerar_documento_aplicacao(self, aplicacao_id: str, data_saldo_texto: str) -> Path:
        aplicacao = self.repositorio.obter(aplicacao_id)
        data_saldo = texto_para_data(data_saldo_texto)
        self.logger.info(f"Gerando demonstrativo da aplicacao {aplicacao.numero_controle}: saldo={data_saldo}")
        demonstrativo = self.montador_demonstrativo.montar([aplicacao], data_saldo)
        caminho = self.relatorio_pdf.gerar_aplicacao(demonstrativo, numero_controle=aplicacao.numero_controle)
        self.logger.info(f"Demonstrativo gerado com sucesso: {caminho}")
        return caminho

    def linha_lista(self, aplicacao: Aplicacao) -> LinhaAplicacaoLista:
        return LinhaAplicacaoLista(
            id=aplicacao.id,
            produto=aplicacao.nome_produto,
            tipo=aplicacao.tipo_produto.value,
            controle=aplicacao.numero_controle,
            emissao=data_br(aplicacao.data_emissao),
            vencimento=data_br(aplicacao.data_vencimento),
            taxa=aplicacao.rotulo_taxa,
            valor=moeda_com_simbolo(aplicacao.valor_aplicado)
        )
