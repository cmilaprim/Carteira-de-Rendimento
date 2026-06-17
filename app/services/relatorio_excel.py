from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font
from app.models.aplicacao import DemonstrativoCarteira
from app.utils.formatadores import data_curta


CABECALHOS = [
    "PRODUTO", "TIPO", "DATA EMISSAO", "DATA VCTO",
    "PRAZO", "TAXA", "VALOR DA APLICACAO", "RENDIMENTO BRUTO (%)",
    "RENDIMENTO BRUTO (R$)", "VALOR ATUALIZADO", "IR", "IOF", "RESGATE LIQUIDO",
]

LARGURAS = [40, 18, 14, 14, 10, 18, 20, 20, 20, 20, 14, 14, 20]
FORMATO_MOEDA = '#,##0.00'
FORMATO_PERCENTUAL = '0.00%'
COLUNAS_MOEDA = [7, 9, 10, 11, 12, 13]
COLUNA_PERCENTUAL = 8


class RelatorioExcelCarteira:
    def __init__(self) -> None:
        self.pasta_saida = Path("data/excel")
        self.pasta_saida.mkdir(parents=True, exist_ok=True)

    def gerar(self, demonstrativo: DemonstrativoCarteira) -> Path:
        caminho = self.pasta_saida / f"carteira_{demonstrativo.data_saldo.isoformat()}.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.title = "Saldo da Carteira"

        ws.append(CABECALHOS)
        for cell in ws[1]:
            cell.font = Font(bold=True)

        for item in demonstrativo.carteira:
            ws.append([
                item.produto,
                item.tipo,
                data_curta(item.data_emissao),
                data_curta(item.data_vencimento),
                item.prazo,
                item.taxa,
                float(item.valor_aplicacao),
                float(item.rendimento_bruto_percentual) / 100,
                float(item.rendimento_bruto),
                float(item.valor_atualizado),
                float(item.valor_ir) if item.valor_ir > 0 else None,
                float(item.valor_iof) if item.valor_iof > 0 else None,
                float(item.resgate_liquido),
            ])
            linha = ws.max_row
            for col in COLUNAS_MOEDA:
                ws.cell(linha, col).number_format = FORMATO_MOEDA
            ws.cell(linha, COLUNA_PERCENTUAL).number_format = FORMATO_PERCENTUAL

        ws.append([
            "TOTAIS", "", "", "", "", "",
            float(sum(i.valor_aplicacao for i in demonstrativo.carteira)), "",
            float(sum(i.rendimento_bruto for i in demonstrativo.carteira)),
            float(sum(i.valor_atualizado for i in demonstrativo.carteira)),
            float(sum(i.valor_ir for i in demonstrativo.carteira)),
            float(sum(i.valor_iof for i in demonstrativo.carteira)),
            float(sum(i.resgate_liquido for i in demonstrativo.carteira))
        ])
        linha_totais = ws.max_row
        for cell in ws[linha_totais]:
            cell.font = Font(bold=True)
        for col in COLUNAS_MOEDA:
            ws.cell(linha_totais, col).number_format = FORMATO_MOEDA

        for i, largura in enumerate(LARGURAS, 1):
            ws.column_dimensions[ws.cell(1, i).column_letter].width = largura

        wb.save(caminho)
        return caminho
