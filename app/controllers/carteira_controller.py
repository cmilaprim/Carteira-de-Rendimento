from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from app.core.conversores import texto_para_data, texto_para_decimal
from app.core.demonstrativo import MontadorDemonstrativo
from app.core.formatadores import data_br, moeda_com_simbolo
from app.core.modelos import Aplicacao, Indexador, RelatorioAplicacao, LinhaAplicacaoLista, DadosAplicacaoFormulario
from app.armazenamento.repositorio_aplicacoes import RepositorioAplicacoes
from app.taxas.servico_taxas import ServicoTaxas
from pathlib import Path
logger = logging.getLogger(__name__)



class CarteiraController:
    def __init__(self, repositorio: RepositorioAplicacoes | None = None, servico_taxas: ServicoTaxas | None = None, montador_demonstrativo: MontadorDemonstrativo | None = None, relatorio_pdf: RelatorioAplicacao | None = None) -> None: 
        self.repositorio = repositorio or RepositorioAplicacoes()
        self.servico_taxas = servico_taxas or ServicoTaxas()
        self.montador_demonstrativo = montador_demonstrativo or MontadorDemonstrativo()
        self.relatorio_pdf = relatorio_pdf

    def indexadores(self) -> list[str]:
        return [item.value for item in Indexador]

    def listar_aplicacoes(self) -> list[LinhaAplicacaoLista]:
        aplicacoes = self.repositorio.listar()
        logger.debug("Listando aplicacoes para a tela: total=%d", len(aplicacoes))
        return [self.linha_lista(aplicacao) for aplicacao in aplicacoes]

    def salvar_aplicacao(self, dados: DadosAplicacaoFormulario) -> Aplicacao:
        logger.info("Solicitacao de cadastro de aplicacao recebida.")
        indexador = Indexador(dados.indexador)
        taxa_prefixada = None
        if indexador == Indexador.PREFIXADO:
            taxa_prefixada = texto_para_decimal(dados.taxa_prefixada)

        aplicacao = Aplicacao.criar(nome_produto=dados.nome_produto, numero_controle=dados.numero_controle, numero_nota=dados.numero_nota, valor_aplicado=texto_para_decimal(dados.valor_aplicado), data_emissao=texto_para_data(dados.data_emissao), data_vencimento=texto_para_data(dados.data_vencimento), indexador=indexador, percentual_indexador=texto_para_decimal(dados.percentual_indexador), taxa_prefixada_anual=taxa_prefixada)

        logger.info("Salvando aplicacao %s: produto=%s controle=%s indexador=%s valor=%s emissao=%s vencimento=%s", aplicacao.id, aplicacao.nome_produto, aplicacao.numero_controle, aplicacao.indexador.value, aplicacao.valor_aplicado, aplicacao.data_emissao, aplicacao.data_vencimento)
        
        self.repositorio.adicionar(aplicacao)
        logger.info("Aplicacao %s salva com sucesso.", aplicacao.id)
        return aplicacao

    def excluir_aplicacao(self, aplicacao_id: str) -> None:
        logger.info("Excluindo aplicacao selecionada: %s", aplicacao_id)
        self.repositorio.excluir(aplicacao_id)
        logger.info("Aplicacao excluida com sucesso: %s", aplicacao_id)

    def atualizar_taxas(self, data_saldo_texto: str) -> str:
        logger.info("Solicitacao de atualizacao de taxas recebida.")
        aplicacoes = self.repositorio.listar()
        if not aplicacoes:
            logger.info("Atualizacao de taxas ignorada: nenhuma aplicacao cadastrada.")
            return "Cadastre uma aplicacao antes de atualizar as taxas."

        inicio = min(aplicacao.data_emissao for aplicacao in aplicacoes)
        fim = texto_para_data(data_saldo_texto)
        fim_busca = min(fim, date.today())
        if inicio > fim_busca:
            logger.info("Atualizacao de taxas ignorada: inicio=%s fim_busca=%s", inicio, fim_busca)
            return "Nao ha datas historicas para atualizar."

        logger.info("Atualizando CDI/Selic de %s ate %s.", inicio, fim_busca)
        self.servico_taxas.atualizar(Indexador.CDI, inicio, fim_busca)
        self.servico_taxas.atualizar(Indexador.SELIC, inicio, fim_busca)
        logger.info("Taxas CDI/Selic atualizadas com sucesso.")
        return "Taxas CDI/Selic atualizadas e salvas em JSON."

    def gerar_documento_aplicacao(self, aplicacao_id: str, data_saldo_texto: str) -> Path:
        aplicacao = self.repositorio.obter(aplicacao_id)
        data_saldo = texto_para_data(data_saldo_texto)
        logger.info("Gerando demonstrativo da aplicacao %s: saldo=%s", aplicacao.numero_controle, data_saldo)

        demonstrativo = self.montador_demonstrativo.montar([aplicacao], data_saldo)
        relatorio_pdf = self.relatorio_pdf or self.criar_relatorio_pdf()
        caminho = relatorio_pdf.gerar_aplicacao(demonstrativo, numero_controle=aplicacao.numero_controle)
        logger.info("Demonstrativo gerado com sucesso: %s", caminho)
        return caminho

    def criar_relatorio_pdf(self) -> RelatorioAplicacao:
        from app.relatorios.demonstrativo_carteira_pdf import RelatorioDemonstrativoCarteiraPDF

        return RelatorioDemonstrativoCarteiraPDF()

    def linha_lista(self, aplicacao: Aplicacao) -> LinhaAplicacaoLista:
        return LinhaAplicacaoLista(id=aplicacao.id, produto=aplicacao.nome_produto, controle=aplicacao.numero_controle, emissao=data_br(aplicacao.data_emissao), vencimento=data_br(aplicacao.data_vencimento), taxa=aplicacao.rotulo_taxa, valor=moeda_com_simbolo(aplicacao.valor_aplicado))
