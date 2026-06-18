import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from app.utils.conversores import texto_para_data, texto_para_decimal
from app.utils.formatadores import data_br, moeda_com_simbolo
from app.models.aplicacao import Aplicacao, Indexador, TipoProduto
from app.repositories.repositorio_aplicacoes import RepositorioAplicacoes
from app.repositories.repositorio_bancos import RepositorioBancos
from app.repositories.repositorio_empresas import RepositorioEmpresas
from app.models.empresa import Empresa
from app.services.demonstrativo import MontadorDemonstrativo
from app.services.servico_taxas import ServicoTaxas


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
    empresa_id: str = ""


@dataclass(frozen=True)
class LinhaAplicacaoLista:
    id: str
    produto: str
    banco: str
    empresa: str
    empresa_id: str
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
        self.repositorio_empresas = RepositorioEmpresas()
        self.servico_taxas = ServicoTaxas(logger=self.logger)
        self.montador_demonstrativo = MontadorDemonstrativo(logger=self.logger)

    def indexadores(self) -> list[str]:
        return [item.value for item in Indexador]

    def tipos_produto(self) -> list[str]:
        return [item.value for item in TipoProduto]

    def listar_bancos(self) -> list[str]:
        return self.repositorio_bancos.listar()

    def listar_empresas(self) -> list[Empresa]:
        return self.repositorio_empresas.listar()

    def adicionar_empresa(self, nome: str, cnpj: str) -> Empresa:
        empresa = Empresa(nome=nome, cnpj=cnpj)
        self.repositorio_empresas.adicionar(empresa)
        return empresa

    def excluir_empresa(self, empresa_id: str) -> None:
        self.repositorio_empresas.excluir(empresa_id)

    def listar_aplicacoes(self) -> list[LinhaAplicacaoLista]:
        aplicacoes = self.repositorio.listar()
        self.logger.debug(f"Listando aplicacoes para a tela: total={len(aplicacoes)}")
        empresas = {e.id: e.nome for e in self.repositorio_empresas.listar()}
        return [self.linha_lista(aplicacao, empresas) for aplicacao in aplicacoes]

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
            empresa_id=dados.empresa_id
        )

        self.repositorio.adicionar(aplicacao)
        return aplicacao

    def excluir_aplicacao(self, aplicacao_id: str) -> None:
        self.repositorio.excluir(aplicacao_id)

    def marcar_resgatada(self, aplicacao_id: str, data_resgate: date | None) -> None:
        aplicacao = self.repositorio.obter(aplicacao_id)
        aplicacao.data_resgate = data_resgate
        self.repositorio.atualizar(aplicacao)

    def obter_aplicacao(self, aplicacao_id: str):
        return self.repositorio.obter(aplicacao_id)

    def editar_aplicacao(self, aplicacao_id: str, dados: DadosAplicacaoFormulario) -> None:
        self.logger.info(f"Solicitacao de edicao de aplicacao: id={aplicacao_id}")
        indexador = Indexador(dados.indexador)
        taxa_prefixada = None
        spread_anual = None
        if indexador == Indexador.PREFIXADO:
            taxa_prefixada = texto_para_decimal(dados.taxa_prefixada)
        elif indexador == Indexador.SELIC_MAIS:
            spread_anual = texto_para_decimal(dados.taxa_prefixada)

        apl = self.repositorio.obter(aplicacao_id)
        apl.nome_produto = dados.nome_produto.strip() or "Produto sem nome"
        apl.valor_aplicado = texto_para_decimal(dados.valor_aplicado)
        apl.data_emissao = texto_para_data(dados.data_emissao)
        apl.data_vencimento = texto_para_data(dados.data_vencimento)
        apl.indexador = indexador
        apl.percentual_indexador = texto_para_decimal(dados.percentual_indexador)
        apl.taxa_prefixada_anual = taxa_prefixada
        apl.spread_anual = spread_anual
        apl.tipo_produto = TipoProduto(dados.tipo_produto)
        apl.banco = dados.banco.strip()
        apl.empresa_id = dados.empresa_id
        apl.validar()
        self.repositorio.atualizar(apl)

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
        empresas = {e.id: e for e in self.repositorio_empresas.listar()}
        demonstrativo = self.montador_demonstrativo.montar(aplicacoes, data_saldo, empresas=empresas)
        from app.services.relatorio_pdf import RelatorioDemonstrativoCarteiraPDF
        return RelatorioDemonstrativoCarteiraPDF().gerar(demonstrativo)

    def gerar_documento_carteira_excel(self, aplicacao_ids: list[str], data_saldo_texto: str) -> Path:
        data_saldo = texto_para_data(data_saldo_texto)
        aplicacoes = [a for a in (self.repositorio.obter(id) for id in aplicacao_ids) if a.data_resgate is None or a.data_resgate > data_saldo]
        self.logger.info(f"Gerando Excel da carteira: aplicacoes={len(aplicacoes)} saldo={data_saldo}")
        empresas = {e.id: e for e in self.repositorio_empresas.listar()}
        demonstrativo = self.montador_demonstrativo.montar(aplicacoes, data_saldo, empresas=empresas)
        from app.services.relatorio_excel import RelatorioExcelCarteira
        return RelatorioExcelCarteira().gerar(demonstrativo)

    def linha_lista(self, aplicacao: Aplicacao, empresas: dict[str, str] | None = None) -> LinhaAplicacaoLista:
        return LinhaAplicacaoLista(
            id=aplicacao.id,
            produto=aplicacao.nome_produto,
            banco=aplicacao.banco,
            empresa=empresas.get(aplicacao.empresa_id, "") if empresas else "",
            empresa_id=aplicacao.empresa_id,
            tipo=aplicacao.tipo_produto.value,
            emissao=data_br(aplicacao.data_emissao),
            vencimento=data_br(aplicacao.data_vencimento),
            taxa=aplicacao.rotulo_taxa,
            valor=moeda_com_simbolo(aplicacao.valor_aplicado),
            resgate=data_br(aplicacao.data_resgate) if aplicacao.data_resgate else "-"
        )
