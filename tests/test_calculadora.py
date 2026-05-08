from datetime import date
from decimal import Decimal

from app.core.calculadora import CalculadoraAplicacao
from app.core.modelos import Aplicacao, Indexador


class ServicoTaxasFalso:
    def obter_taxas(self, indexador, data_inicial, data_final, tentar_atualizar=True):
        return {
            date(2024, 1, 2): Decimal("0.05"),
            date(2024, 1, 3): Decimal("0.05"),
            date(2024, 1, 4): Decimal("0.05"),
            date(2024, 1, 5): Decimal("0.05"),
        }


def test_calcula_115_porcento_cdi_usando_taxa_diaria():
    aplicacao = Aplicacao.criar(
        nome_produto="CDB TESTE",
        valor_aplicado=Decimal("1000"),
        data_emissao=date(2024, 1, 1),
        data_vencimento=date(2024, 1, 5),
        indexador=Indexador.CDI,
        percentual_indexador=Decimal("115"),
    )
    calculadora = CalculadoraAplicacao(servico_taxas=ServicoTaxasFalso())
    posicoes = calculadora.calcular(aplicacao, tentar_atualizar_taxas=False)

    assert posicoes[-1].saldo_bruto > Decimal("1000")
    assert posicoes[-1].rendimento_bruto > Decimal("0")
    assert posicoes[0].juros == Decimal("0")


def test_prefixado_nao_precisa_de_taxa_do_banco_central():
    aplicacao = Aplicacao.criar(
        nome_produto="PREFIXADO TESTE",
        valor_aplicado=Decimal("1000"),
        data_emissao=date(2024, 1, 1),
        data_vencimento=date(2024, 1, 5),
        indexador=Indexador.PREFIXADO,
        percentual_indexador=Decimal("100"),
        taxa_prefixada_anual=Decimal("13.50"),
    )
    calculadora = CalculadoraAplicacao(servico_taxas=ServicoTaxasFalso())
    posicoes = calculadora.calcular(aplicacao, tentar_atualizar_taxas=False)

    assert posicoes[-1].saldo_bruto > Decimal("1000")
