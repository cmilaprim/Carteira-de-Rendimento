from datetime import date
from decimal import Decimal

from app.core.calculadora import CalculadoraAplicacao
from app.core.demonstrativo import MontadorDemonstrativo
from app.core.formatadores import moeda_com_simbolo
from app.core.modelos import Aplicacao, Indexador
from app.relatorios.demonstrativo_carteira_pdf import RelatorioDemonstrativoCarteiraPDF


aplicacoes = [
    Aplicacao.criar(
        nome_produto="LC-POS KREDILIG",
        numero_controle="0000464-8",
        numero_nota="0000464-8",
        valor_aplicado=Decimal("500000"),
        data_emissao=date(2026, 4, 30),
        data_vencimento=date(2029, 4, 16),
        indexador=Indexador.CDI,
        percentual_indexador=Decimal("115")
    )
]

calculadora = CalculadoraAplicacao()
posicoes = calculadora.calcular(aplicacoes[0], data_posicao=date(2026, 4, 30), tentar_atualizar_taxas=False)
print("Saldo liquido:", moeda_com_simbolo(posicoes[-1].saldo_liquido))

demonstrativo = MontadorDemonstrativo(calculadora).montar(
    aplicacoes=aplicacoes,
    periodo_inicio=date(2026, 4, 1),
    periodo_fim=date(2026, 4, 30),
    data_saldo=date(2026, 4, 30)
)

caminho_pdf = RelatorioDemonstrativoCarteiraPDF().gerar(demonstrativo)
print("PDF gerado em:", caminho_pdf)
