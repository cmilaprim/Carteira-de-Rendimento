from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import uuid4
from typing import Protocol
from pathlib import Path
class Indexador(str, Enum):
    CDI = "CDI"
    SELIC = "SELIC"
    PREFIXADO = "PREFIXADO"


@dataclass
class Aplicacao:
    id: str
    nome_produto: str
    numero_controle: str
    numero_nota: str
    valor_aplicado: Decimal
    data_emissao: date
    data_vencimento: date
    indexador: Indexador
    percentual_indexador: Decimal = Decimal("100")
    taxa_prefixada_anual: Decimal | None = None

    @classmethod
    def criar(cls, nome_produto: str, valor_aplicado: Decimal, data_emissao: date, data_vencimento: date, indexador: Indexador, percentual_indexador: Decimal = Decimal("100"), numero_controle: str = "", numero_nota: str = "", taxa_prefixada_anual: Decimal | None = None) -> "Aplicacao":
        aplicacao = cls(
            id=str(uuid4()),
            nome_produto=nome_produto.strip() or "Produto sem nome",
            numero_controle=numero_controle.strip(),
            numero_nota=numero_nota.strip(),
            valor_aplicado=Decimal(valor_aplicado),
            data_emissao=data_emissao,
            data_vencimento=data_vencimento,
            indexador=Indexador(indexador),
            percentual_indexador=Decimal(percentual_indexador),
            taxa_prefixada_anual=taxa_prefixada_anual
        )
        aplicacao.validar()
        return aplicacao

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

    @property
    def prazo_dias_corridos(self) -> int:
        return (self.data_vencimento - self.data_emissao).days

    @property
    def rotulo_taxa(self) -> str:
        if self.indexador == Indexador.PREFIXADO:
            taxa = self.taxa_prefixada_anual or Decimal("0")
            return f"{taxa:.2f}% A.A.".replace(".", ",")
        return f"{self.percentual_indexador:.2f}% {self.indexador.value}".replace(".", ",")


@dataclass(frozen=True)
class PosicaoDiaria:
    data: date
    dia_corrido: int
    houve_rendimento: bool
    taxa_base_diaria: Decimal
    percentual_indexador: Decimal
    saldo_abertura: Decimal
    juros: Decimal
    saldo_bruto: Decimal
    rendimento_bruto: Decimal
    aliquota_iof: Decimal
    valor_iof: Decimal
    aliquota_ir: Decimal
    valor_ir: Decimal
    rendimento_liquido: Decimal
    saldo_liquido: Decimal


@dataclass(frozen=True)
class LinhaMovimentacao:
    data: date
    operacao: str
    numero_nota: str
    valor_resgate_bruto: Decimal
    impostos: Decimal
    valor_liquido_operacao: Decimal
    dc: str


@dataclass(frozen=True)
class LinhaCarteira:
    produto: str
    numero_controle: str
    data_emissao: date
    data_vencimento: date
    prazo: int
    taxa: str
    valor_aplicacao: Decimal
    rendimento_bruto_percentual: Decimal
    valor_atualizado: Decimal
    valor_ir: Decimal
    valor_iof: Decimal
    resgate_liquido: Decimal


@dataclass(frozen=True)
class DemonstrativoCarteira:
    data_saldo: date
    movimentacoes: list[LinhaMovimentacao] = field(default_factory=list)
    carteira: list[LinhaCarteira] = field(default_factory=list)


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


@dataclass(frozen=True)
class LinhaAplicacaoLista:
    id: str
    produto: str
    controle: str
    emissao: str
    vencimento: str
    taxa: str
    valor: str


class RelatorioAplicacao(Protocol):
    def gerar_aplicacao(self, demonstrativo, numero_controle: str = "") -> Path:
        ...