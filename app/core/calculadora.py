from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, getcontext

from app.core.calendario import eh_dia_util_simples, intervalo_datas
from app.core.impostos import aliquota_iof, aliquota_ir
from app.core.modelos import Aplicacao, Indexador, PosicaoDiaria
from app.taxas.servico_taxas import ServicoTaxas

getcontext().prec = 28


class CalculadoraAplicacao:
    def __init__(self, servico_taxas: ServicoTaxas | None = None) -> None:
        self.servico_taxas = servico_taxas or ServicoTaxas()

    def calcular(self, aplicacao: Aplicacao, data_posicao: date | None = None, projetar_com_ultima_taxa: bool = True, tentar_atualizar_taxas: bool = True,) -> list[PosicaoDiaria]:
        aplicacao.validar()
        
        data_final = data_posicao or aplicacao.data_vencimento
        if data_final < aplicacao.data_emissao:
            raise ValueError("A data de posicao nao pode ser anterior a data de emissao.")

        taxas = self.servico_taxas.obter_taxas(aplicacao.indexador, aplicacao.data_emissao, data_final, tentar_atualizar=tentar_atualizar_taxas)
        saldo = Decimal(aplicacao.valor_aplicado)
        posicoes: list[PosicaoDiaria] = []
        ultima_taxa_base_diaria: Decimal | None = None

        for data_atual in intervalo_datas(aplicacao.data_emissao, data_final):
            dia_corrido = (data_atual - aplicacao.data_emissao).days
            saldo_abertura = saldo
            juros = Decimal("0")
            houve_rendimento = False
            taxa_base_diaria = Decimal("0")

            if dia_corrido > 0:
                taxa_base_diaria = self.obter_taxa_diaria(aplicacao=aplicacao, data_atual=data_atual, taxas=taxas, ultima_taxa_base_diaria=ultima_taxa_base_diaria, projetar_com_ultima_taxa=projetar_com_ultima_taxa)
                if taxa_base_diaria > 0:
                    ultima_taxa_base_diaria = taxa_base_diaria
                    percentual = aplicacao.percentual_indexador / Decimal("100")
                    juros = saldo * taxa_base_diaria * percentual
                    saldo += juros
                    houve_rendimento = True

            rendimento_bruto = saldo - aplicacao.valor_aplicado
            aliq_iof = aliquota_iof(dia_corrido)
            valor_iof = rendimento_bruto * aliq_iof
            base_ir = rendimento_bruto - valor_iof
            aliq_ir = aliquota_ir(dia_corrido)
            valor_ir = base_ir * aliq_ir
            rendimento_liquido = base_ir - valor_ir
            saldo_liquido = aplicacao.valor_aplicado + rendimento_liquido

            posicoes.append(PosicaoDiaria(
                data=data_atual,
                dia_corrido=dia_corrido,
                houve_rendimento=houve_rendimento,
                taxa_base_diaria=taxa_base_diaria,
                percentual_indexador=aplicacao.percentual_indexador,
                saldo_abertura=saldo_abertura,
                juros=juros,
                saldo_bruto=saldo,
                rendimento_bruto=rendimento_bruto,
                aliquota_iof=aliq_iof,
                valor_iof=valor_iof,
                aliquota_ir=aliq_ir,
                valor_ir=valor_ir,
                rendimento_liquido=rendimento_liquido,
                saldo_liquido=saldo_liquido,
            ))

        return posicoes

    def obter_taxa_diaria(self, aplicacao: Aplicacao, data_atual: date, taxas: dict[date, Decimal], ultima_taxa_base_diaria: Decimal | None, projetar_com_ultima_taxa: bool) -> Decimal:
        if aplicacao.indexador == Indexador.PREFIXADO:
            return self.converter_taxa_anual_para_diaria(aplicacao.taxa_prefixada_anual or Decimal("0"))

        if data_atual in taxas:
            return taxas[data_atual] / Decimal("100")

        if not eh_dia_util_simples(data_atual):
            return Decimal("0")

        if projetar_com_ultima_taxa and ultima_taxa_base_diaria is not None and data_atual > date.today():
            return ultima_taxa_base_diaria

        return Decimal("0")

    def converter_taxa_anual_para_diaria(self, taxa_anual_percentual: Decimal) -> Decimal:
        taxa = Decimal(taxa_anual_percentual) / Decimal("100")
        diaria = (1 + float(taxa)) ** (1 / 252) - 1
        return Decimal(str(diaria))
