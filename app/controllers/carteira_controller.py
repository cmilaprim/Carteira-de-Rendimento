import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from app.utils.conversores import texto_para_data, texto_para_decimal
from app.utils.formatadores import data_br, moeda_com_simbolo
from app.models.aplicacao import Aplicacao, Indexador, TipoProduto
from app.repositories.repositorio_aplicacoes import RepositorioAplicacoes
from app.repositories.repositorio_bancos import RepositorioBancos
from app.services.demonstrativo import MontadorDemonstrativo
from app.services.servico_taxas import ServicoTaxas
from app.services.relatorio_pdf import RelatorioDemonstrativoCarteiraPDF
from app.services.relatorio_excel import RelatorioExcelCarteira


@dataclass(frozen=True)
class DadosAplicacaoFormulario:
    nome_produto: str
    valor_aplicado: str
    data_emissao: str
    data_vencimento: str
    indexador: str
    percentual_indexador: str
    taxa_prefixada: str
    tipo_produto: str = TipoProduto.CDB.value
    banco: str = ""


@dataclass(frozen=True)
class LinhaAplicacaoLista:
    id: str
    produto: str
    banco: str
    tipo: str
    emissao: str
    vencimento: str
    taxa: str
    valor: str
    resgate: str = "-"


class CarteiraController:
    def __init__(self, logger):
        self.logger: logging.Logger = logger
        self.repositorio = RepositorioAplicacoes()
        self.repositorio_bancos = RepositorioBancos()
        self.servico_taxas = ServicoTaxas(logger=self.logger)
        self.montador_demonstrativo = MontadorDemonstrativo(logger=self.logger)
        self.relatorio_pdf = RelatorioDemonstrativoCarteiraPDF()
        self.relatorio_excel = RelatorioExcelCarteira()

    def indexadores(self) -> list[str]:
        return [item.value for item in Indexador]

    def tipos_produto(self) -> list[str]:
        return [item.value for item in TipoProduto]

    def listar_bancos(self) -> list[str]:
        return self.repositorio_bancos.listar()

    def adicionar_banco(self, nome: str) -> None:
        self.repositorio_bancos.adicionar(nome)

    def remover_banco(self, nome: str) -> None:
        self.repositorio_bancos.remover(nome)

    def listar_aplicacoes(self) -> list[LinhaAplicacaoLista]:
        aplicacoes = self.repositorio.listar()
        self.logger.debug(f"Listando aplicacoes para a tela: total={len(aplicacoes)}")
        return [self.linha_lista(aplicacao) for aplicacao in aplicacoes]

    def salvar_aplicacao(self, dados: DadosAplicacaoFormulario) -> Aplicacao:
        self.logger.info("Solicitacao de cadastro de aplicacao recebida.")
        indexador = Indexador(dados.indexador)
        taxa_prefixada = None
        spread_anual = None
        if indexador == Indexador.PREFIXADO:
            taxa_prefixada = texto_para_decimal(dados.taxa_prefixada)
        elif indexador == Indexador.SELIC_MAIS:
            spread_anual = texto_para_decimal(dados.taxa_prefixada)

        aplicacao = Aplicacao.criar(
            nome_produto=dados.nome_produto,
            valor_aplicado=texto_para_decimal(dados.valor_aplicado),
            data_emissao=texto_para_data(dados.data_emissao),
            data_vencimento=texto_para_data(dados.data_vencimento),
            indexador=indexador,
            percentual_indexador=texto_para_decimal(dados.percentual_indexador),
            taxa_prefixada_anual=taxa_prefixada,
            spread_anual=spread_anual,
            tipo_produto=TipoProduto(dados.tipo_produto),
            banco=dados.banco,
        )

        self.repositorio.adicionar(aplicacao)
        return aplicacao

    def excluir_aplicacao(self, aplicacao_id: str) -> None:
        self.repositorio.excluir(aplicacao_id)

    def marcar_resgatada(self, aplicacao_id: str, data_resgate: date | None) -> None:
        aplicacao = self.repositorio.obter(aplicacao_id)
        aplicacao.data_resgate = data_resgate
        self.repositorio.atualizar(aplicacao)

    def atualizar_taxas(self, data_saldo_texto: str) -> str:
        aplicacoes = self.repositorio.listar()
        if not aplicacoes:
            return "Cadastre uma aplicacao antes de atualizar as taxas."

        inicio = min(aplicacao.data_emissao for aplicacao in aplicacoes)
        fim = texto_para_data(data_saldo_texto)
        fim_busca = min(fim, date.today())
        if inicio > fim_busca:
            return "Nao ha datas historicas para atualizar."

        self.logger.info(f"Atualizando CDI/Selic de {inicio} ate {fim_busca}.")
        self.servico_taxas.atualizar(Indexador.CDI, inicio, fim_busca)
        self.servico_taxas.atualizar(Indexador.SELIC, inicio, fim_busca)
        return "Taxas CDI/Selic atualizadas e salvas em JSON."

    def gerar_documento_carteira(self, aplicacao_ids: list[str], data_saldo_texto: str) -> Path:
        data_saldo = texto_para_data(data_saldo_texto)
        aplicacoes = [a for a in (self.repositorio.obter(id) for id in aplicacao_ids) if a.data_resgate is None or a.data_resgate > data_saldo]
        self.logger.info(f"Gerando demonstrativo da carteira: aplicacoes={len(aplicacoes)} saldo={data_saldo}")
        demonstrativo = self.montador_demonstrativo.montar(aplicacoes, data_saldo)
        return self.relatorio_pdf.gerar(demonstrativo)

    def gerar_documento_carteira_excel(self, aplicacao_ids: list[str], data_saldo_texto: str) -> Path:
        data_saldo = texto_para_data(data_saldo_texto)
        aplicacoes = [a for a in (self.repositorio.obter(id) for id in aplicacao_ids) if a.data_resgate is None or a.data_resgate > data_saldo]
        self.logger.info(f"Gerando Excel da carteira: aplicacoes={len(aplicacoes)} saldo={data_saldo}")
        demonstrativo = self.montador_demonstrativo.montar(aplicacoes, data_saldo)
        return self.relatorio_excel.gerar(demonstrativo)

    def linha_lista(self, aplicacao: Aplicacao) -> LinhaAplicacaoLista:
        return LinhaAplicacaoLista(
            id=aplicacao.id,
            produto=aplicacao.nome_produto,
            banco=aplicacao.banco,
            tipo=aplicacao.tipo_produto.value,
            emissao=data_br(aplicacao.data_emissao),
            vencimento=data_br(aplicacao.data_vencimento),
            taxa=aplicacao.rotulo_taxa,
            valor=moeda_com_simbolo(aplicacao.valor_aplicado),
            resgate=data_br(aplicacao.data_resgate) if aplicacao.data_resgate else "-",
        )
