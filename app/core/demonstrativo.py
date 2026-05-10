from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.core.calculadora import CalculadoraAplicacao
from app.core.modelos import Aplicacao, DemonstrativoCarteira, LinhaCarteira, LinhaMovimentacao


class MontadorDemonstrativo:
    def __init__(self, calculadora: CalculadoraAplicacao | None = None) -> None:
        self.calculadora = calculadora or CalculadoraAplicacao()

    def montar(self, aplicacoes: list[Aplicacao], periodo_inicio: date, periodo_fim: date, data_saldo: date) -> DemonstrativoCarteira:
        movimentacoes: list[LinhaMovimentacao] = []
        carteira: list[LinhaCarteira] = []

        for aplicacao in aplicacoes:
            if periodo_inicio <= aplicacao.data_emissao <= periodo_fim:
                movimentacoes.append(LinhaMovimentacao(
                    data=aplicacao.data_emissao,
                    operacao="Aplicacao",
                    numero_nota=aplicacao.numero_nota,
                    valor_resgate_bruto=aplicacao.valor_aplicado,
                    impostos=Decimal("0"),
                    valor_liquido_operacao=aplicacao.valor_aplicado,
                    dc="D"
                ))

            if aplicacao.data_emissao > data_saldo:
                continue

            posicoes = self.calculadora.calcular(aplicacao, data_posicao=min(data_saldo, aplicacao.data_vencimento))
            if not posicoes:
                continue
            ultima = posicoes[-1]

            if aplicacao.valor_aplicado > 0:
                rendimento_percentual = (ultima.saldo_bruto / aplicacao.valor_aplicado - Decimal("1")) * Decimal("100")
            else:
                rendimento_percentual = Decimal("0")

            carteira.append(LinhaCarteira(
                produto=aplicacao.nome_produto,
                numero_controle=aplicacao.numero_controle,
                data_emissao=aplicacao.data_emissao,
                data_vencimento=aplicacao.data_vencimento,
                prazo=aplicacao.prazo_dias_corridos,
                taxa=aplicacao.rotulo_taxa,
                valor_aplicacao=aplicacao.valor_aplicado,
                rendimento_bruto_percentual=rendimento_percentual,
                valor_atualizado=ultima.saldo_bruto,
                valor_ir=ultima.valor_ir,
                valor_iof=ultima.valor_iof,
                resgate_liquido=ultima.saldo_liquido
            ))

        movimentacoes.sort(key=lambda item: item.data)
        carteira.sort(key=lambda item: (item.produto, item.numero_controle))

        return DemonstrativoCarteira(periodo_inicio=periodo_inicio, periodo_fim=periodo_fim, data_saldo=data_saldo, movimentacoes=movimentacoes, carteira=carteira)
