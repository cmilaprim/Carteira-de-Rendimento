import logging
from datetime import date, timedelta
from decimal import Decimal, getcontext
from app.utils.calendario import eh_dia_util, intervalo_datas
from app.utils.impostos import aliquota_iof, aliquota_ir
from app.models.aplicacao import Aplicacao, Indexador, PosicaoDiaria, TipoProduto
from app.services.servico_taxas import ServicoTaxas

getcontext().prec = 28


class CalculadoraAplicacao:
    def __init__(self, logger):
        self.logger: logging.Logger = logger
        self.servico_taxas = ServicoTaxas(logger=self.logger)

    def buscar_taxa_com_defasagem(self, taxas_por_data: dict[date, Decimal], data_atual: date, defasagem_dias: int = 1) -> tuple[date, Decimal] | None:
        data_taxa = data_atual - timedelta(days=defasagem_dias)
        menor_data_disponivel = min(taxas_por_data.keys()) if taxas_por_data else None

        while data_taxa not in taxas_por_data:
            data_taxa -= timedelta(days=1)
            if menor_data_disponivel is not None and data_taxa < menor_data_disponivel:
                self.logger.debug(f"Nenhuma taxa encontrada com defasagem para a data {data_atual}.")
                return None

        return data_taxa, taxas_por_data[data_taxa]

    def calcular(self, aplicacao: Aplicacao, data_posicao: date | None = None, projetar_com_ultima_taxa: bool = True, tentar_atualizar_taxas: bool = True) -> list[PosicaoDiaria]:
        aplicacao.validar()
        data_final = data_posicao or aplicacao.data_vencimento
        self.logger.info(f"Calculando aplicacao {aplicacao.id}: controle={aplicacao.numero_controle} indexador={aplicacao.indexador.value} emissao={aplicacao.data_emissao} data_final={data_final}")
        if data_final < aplicacao.data_emissao:
            self.logger.error(f"Data de posicao anterior a emissao: aplicacao={aplicacao.id} emissao={aplicacao.data_emissao} data_final={data_final}")
            raise ValueError("A data de posicao nao pode ser anterior a data de emissao.")

        taxas = self.servico_taxas.obter_taxas(aplicacao.indexador, aplicacao.data_emissao, data_final, tentar_atualizar=tentar_atualizar_taxas)
        self.logger.debug(f"Taxas disponiveis para calculo da aplicacao {aplicacao.id}: {len(taxas)}")
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
            aliq_iof = Decimal("0") if aplicacao.tipo_produto == TipoProduto.COMPROMISSADA else aliquota_iof(dia_corrido)
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
                saldo_liquido=saldo_liquido
            ))

        if posicoes:
            ultima = posicoes[-1]
            self.logger.info(f"Calculo finalizado para aplicacao {aplicacao.id}: dias={len(posicoes)} saldo_bruto={ultima.saldo_bruto} saldo_liquido={ultima.saldo_liquido}")
        else:
            self.logger.warning(f"Calculo finalizado sem posicoes para aplicacao {aplicacao.id}.")
        return posicoes

    def obter_taxa_diaria(self, aplicacao: Aplicacao, data_atual: date, taxas: dict[date, Decimal], ultima_taxa_base_diaria: Decimal | None, projetar_com_ultima_taxa: bool) -> Decimal:
        if aplicacao.indexador == Indexador.PREFIXADO:
            if not eh_dia_util(data_atual):
                return Decimal("0")
            return self.converter_taxa_anual_para_diaria(aplicacao.taxa_prefixada_anual or Decimal("0"))

        maior_data_disponivel = max(taxas.keys()) if taxas else None
        pode_usar_defasagem = data_atual in taxas or (maior_data_disponivel is not None and data_atual > maior_data_disponivel and data_atual <= date.today())

        if not pode_usar_defasagem:
            if projetar_com_ultima_taxa and ultima_taxa_base_diaria is not None and data_atual > date.today() and eh_dia_util(data_atual):
                self.logger.debug(f"Projetando aplicacao {aplicacao.id} em {data_atual} com ultima taxa diaria conhecida: {ultima_taxa_base_diaria}")
                return ultima_taxa_base_diaria

            if eh_dia_util(data_atual):
                self.logger.warning(f"Taxa {aplicacao.indexador.value} ausente para dia util {data_atual} na aplicacao {aplicacao.id}.")
            return Decimal("0")

        resultado_taxa = self.buscar_taxa_com_defasagem(taxas_por_data=taxas, data_atual=data_atual, defasagem_dias=1)

        if resultado_taxa is None:
            self.logger.warning(f"Nao foi encontrada taxa com defasagem para {data_atual} na aplicacao {aplicacao.id}.")
            return Decimal("0")

        self.logger.debug(f"Taxa encontrada para a data {data_atual}: {resultado_taxa}")
        data_taxa_usada, taxa_percentual_dia = resultado_taxa

        return taxa_percentual_dia / Decimal("100")

    def converter_taxa_anual_para_diaria(self, taxa_anual_percentual: Decimal) -> Decimal:
        taxa = Decimal(taxa_anual_percentual) / Decimal("100")
        diaria = (1 + float(taxa)) ** (1 / 252) - 1
        return Decimal(str(diaria))
