import logging
from datetime import date
from decimal import Decimal
from app.services.calculadora import CalculadoraAplicacao
from app.models.aplicacao import Aplicacao, DemonstrativoCarteira, LinhaCarteira, LinhaMovimentacao


class MontadorDemonstrativo:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger 
        self.calculadora = CalculadoraAplicacao(logger=self.logger)

    def montar(self, aplicacoes: list[Aplicacao], data_saldo: date) -> DemonstrativoCarteira:
        self.logger.info(f"Montando demonstrativo: aplicacoes={len(aplicacoes)} data_saldo={data_saldo}")
        movimentacoes: list[LinhaMovimentacao] = []
        carteira: list[LinhaCarteira] = []

        for aplicacao in aplicacoes:
            self.logger.debug(f"Processando aplicacao no demonstrativo: id={aplicacao.id} controle={aplicacao.numero_controle} emissao={aplicacao.data_emissao} vencimento={aplicacao.data_vencimento}")
            if aplicacao.data_emissao <= data_saldo:
                movimentacoes.append(LinhaMovimentacao(
                    data=aplicacao.data_emissao,
                    operacao="Aplicacao",
                    numero_nota=aplicacao.numero_nota,
                    valor_resgate_bruto=aplicacao.valor_aplicado,
                    impostos=Decimal("0"),
                    valor_liquido_operacao=aplicacao.valor_aplicado,
                    dc="D"
                ))
                self.logger.debug(f"Movimentacao adicionada para aplicacao {aplicacao.id}.")

            if aplicacao.data_emissao > data_saldo:
                self.logger.info(f"Aplicacao {aplicacao.id} ignorada na carteira: emissao={aplicacao.data_emissao} posterior a data_saldo={data_saldo}")
                continue

            posicoes = self.calculadora.calcular(aplicacao, data_posicao=min(data_saldo, aplicacao.data_vencimento))
            if not posicoes:
                self.logger.warning(f"Aplicacao {aplicacao.id} nao gerou posicoes para o demonstrativo.")
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
            self.logger.debug(f"Aplicacao {aplicacao.id} adicionada na carteira: saldo_bruto={ultima.saldo_bruto} saldo_liquido={ultima.saldo_liquido}")

        movimentacoes.sort(key=lambda item: item.data)
        carteira.sort(key=lambda item: (item.produto, item.numero_controle))

        self.logger.info(f"Demonstrativo montado: movimentacoes={len(movimentacoes)} carteira={len(carteira)}")
        return DemonstrativoCarteira(data_saldo=data_saldo, movimentacoes=movimentacoes, carteira=carteira)
