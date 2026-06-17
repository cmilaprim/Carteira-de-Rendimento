
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import uuid4


class Indexador(str, Enum):
    CDI = "CDI"
    SELIC = "SELIC"
    PREFIXADO = "PREFIXADO"
    SELIC_MAIS = "SELIC+"


class TipoProduto(str, Enum):
    CDB = "CDB"
    COMPROMISSADA = "COMPROMISSADA"


class Aplicacao:
    def __init__(self, nome_produto: str, valor_aplicado: Decimal, data_emissao: date, data_vencimento: date, indexador: Indexador, percentual_indexador: Decimal = Decimal("100"), numero_controle: str = "", numero_nota: str = "", taxa_prefixada_anual: Decimal | None = None, spread_anual: Decimal | None = None, tipo_produto: TipoProduto = TipoProduto.CDB, banco: str = "", data_resgate: date | None = None, id: str | None = None) -> None:
        self.id = id or str(uuid4())
        self.nome_produto = nome_produto.strip() or "Produto sem nome"
        self.numero_controle = numero_controle.strip()
        self.numero_nota = numero_nota.strip()
        self.banco = banco.strip()
        self.data_resgate = data_resgate
        self.valor_aplicado = Decimal(valor_aplicado)
        self.data_emissao = data_emissao
        self.data_vencimento = data_vencimento
        self.indexador = Indexador(indexador)
        self.percentual_indexador = Decimal(percentual_indexador)
        self.taxa_prefixada_anual = taxa_prefixada_anual
        self.spread_anual = spread_anual
        self.tipo_produto = TipoProduto(tipo_produto)

        self.validar()

    @classmethod
    def criar(cls, nome_produto: str, valor_aplicado: Decimal, data_emissao: date, data_vencimento: date, indexador: Indexador, percentual_indexador: Decimal = Decimal("100"), numero_controle: str = "", numero_nota: str = "", taxa_prefixada_anual: Decimal | None = None, spread_anual: Decimal | None = None, tipo_produto: TipoProduto = TipoProduto.CDB, banco: str = "") -> "Aplicacao":
        return cls(nome_produto=nome_produto, valor_aplicado=valor_aplicado, data_emissao=data_emissao, data_vencimento=data_vencimento, indexador=indexador, percentual_indexador=percentual_indexador, numero_controle=numero_controle, numero_nota=numero_nota, taxa_prefixada_anual=taxa_prefixada_anual, spread_anual=spread_anual, tipo_produto=tipo_produto, banco=banco)

    def validar(self) -> None:
        if self.valor_aplicado <= 0:
            raise ValueError("O valor aplicado deve ser maior que zero.")

        if self.data_vencimento < self.data_emissao:
            raise ValueError("A data de vencimento nao pode ser anterior a data de emissao.")

        if self.percentual_indexador <= 0:
            raise ValueError("O percentual do indexador deve ser maior que zero.")

        if self.indexador == Indexador.PREFIXADO:
            if self.taxa_prefixada_anual is None:
                raise ValueError("Informe a taxa anual para aplicacao prefixada.")
            if self.taxa_prefixada_anual < 0:
                raise ValueError("A taxa prefixada nao pode ser negativa.")

        if self.indexador == Indexador.SELIC_MAIS:
            if self.spread_anual is None:
                raise ValueError("Informe o spread anual para aplicacao SELIC+.")
            if self.spread_anual < 0:
                raise ValueError("O spread anual nao pode ser negativo.")

    @property
    def prazo_dias_corridos(self) -> int:
        return (self.data_vencimento - self.data_emissao).days

    @property
    def rotulo_taxa(self) -> str:
        if self.indexador == Indexador.PREFIXADO:
            taxa = self.taxa_prefixada_anual or Decimal("0")
            return f"{taxa:.2f}% A.A.".replace(".", ",")

        if self.indexador == Indexador.SELIC_MAIS:
            spread = self.spread_anual or Decimal("0")
            return f"SELIC + {spread:.2f}% A.A.".replace(".", ",")

        return f"{self.percentual_indexador:.2f}% {self.indexador.value}".replace(".", ",")


class PosicaoDiaria:
    def __init__(self, data: date, dia_corrido: int, houve_rendimento: bool, taxa_base_diaria: Decimal, percentual_indexador: Decimal, saldo_abertura: Decimal, juros: Decimal, saldo_bruto: Decimal, rendimento_bruto: Decimal, aliquota_iof: Decimal, valor_iof: Decimal, aliquota_ir: Decimal, valor_ir: Decimal, rendimento_liquido: Decimal, saldo_liquido: Decimal) -> None:
        self.data = data
        self.dia_corrido = dia_corrido
        self.houve_rendimento = houve_rendimento
        self.taxa_base_diaria = taxa_base_diaria
        self.percentual_indexador = percentual_indexador
        self.saldo_abertura = saldo_abertura
        self.juros = juros
        self.saldo_bruto = saldo_bruto
        self.rendimento_bruto = rendimento_bruto
        self.aliquota_iof = aliquota_iof
        self.valor_iof = valor_iof
        self.aliquota_ir = aliquota_ir
        self.valor_ir = valor_ir
        self.rendimento_liquido = rendimento_liquido
        self.saldo_liquido = saldo_liquido


class LinhaMovimentacao:
    def __init__(self, data: date, operacao: str,numero_nota: str, valor_resgate_bruto: Decimal, impostos: Decimal, valor_liquido_operacao: Decimal, dc: str) -> None:
        self.data = data
        self.operacao = operacao
        self.numero_nota = numero_nota
        self.valor_resgate_bruto = valor_resgate_bruto
        self.impostos = impostos
        self.valor_liquido_operacao = valor_liquido_operacao
        self.dc = dc


class LinhaCarteira:
    def __init__(self, produto: str, tipo: str, data_emissao: date, data_vencimento: date, prazo: int, taxa: str, valor_aplicacao: Decimal, rendimento_bruto_percentual: Decimal, rendimento_bruto: Decimal, valor_atualizado: Decimal, valor_ir: Decimal, valor_iof: Decimal, resgate_liquido: Decimal) -> None:
        self.produto = produto
        self.tipo = tipo
        self.data_emissao = data_emissao
        self.data_vencimento = data_vencimento
        self.prazo = prazo
        self.taxa = taxa
        self.valor_aplicacao = valor_aplicacao
        self.rendimento_bruto_percentual = rendimento_bruto_percentual
        self.rendimento_bruto = rendimento_bruto
        self.valor_atualizado = valor_atualizado
        self.valor_ir = valor_ir
        self.valor_iof = valor_iof
        self.resgate_liquido = resgate_liquido


class DemonstrativoCarteira:
    def __init__(self, data_saldo: date, movimentacoes: list[LinhaMovimentacao] | None = None, carteira: list[LinhaCarteira] | None = None) -> None:
        self.data_saldo = data_saldo
        self.movimentacoes = movimentacoes if movimentacoes is not None else []
        self.carteira = carteira if carteira is not None else []
