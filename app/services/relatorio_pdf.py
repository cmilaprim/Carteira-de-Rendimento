from decimal import Decimal
from itertools import groupby
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from app.utils.formatadores import cnpj, data_br, data_curta, moeda, percentual
from app.models.aplicacao import DemonstrativoCarteira, LinhaCarteira


class RelatorioDemonstrativoCarteiraPDF:
    def __init__(self) -> None:
        self.pasta_saida = Path("data/pdf")
        self.pasta_saida.mkdir(parents=True, exist_ok=True)

    def gerar(self, demonstrativo: DemonstrativoCarteira) -> Path:
        caminho = self.pasta_saida / f"demonstrativo_carteira_{demonstrativo.data_saldo.isoformat()}.pdf"
        documento = self.criar_documento(caminho)
        estilos = getSampleStyleSheet()
        elementos = []

        titulo_saldo = f"SALDO DA CARTEIRA ({data_br(demonstrativo.data_saldo)})"
        elementos.append(Paragraph(f"<b>{titulo_saldo}</b>", estilos["Normal"]))
        elementos.append(Spacer(1, 4 * mm))

        grupos = self.agrupar_por_empresa(demonstrativo.carteira)
        for empresa_nome, empresa_cnpj, itens in grupos:
            if empresa_nome:
                rotulo = empresa_nome
                if empresa_cnpj:
                    rotulo += f" — CNPJ: {cnpj(empresa_cnpj)}"
                elementos.append(Paragraph(f"<b>{rotulo}</b>", estilos["Normal"]))
                elementos.append(Spacer(1, 2 * mm))
            elementos.append(self.tabela_carteira(itens))
            elementos.append(Spacer(1, 6 * mm))

        documento.build(elementos)
        return caminho

    def criar_documento(self, caminho: Path) -> SimpleDocTemplate:
        return SimpleDocTemplate(str(caminho), pagesize=landscape(A4), leftMargin=8 * mm, rightMargin=8 * mm, topMargin=8 * mm, bottomMargin=8 * mm)

    def agrupar_por_empresa(self, carteira: list[LinhaCarteira]) -> list[tuple]:
        ordenado = sorted(carteira, key=lambda x: (x.empresa_nome or "", x.produto))
        resultado = []
        for (nome, cnpj_val), grupo in groupby(ordenado, key=lambda x: (x.empresa_nome, x.empresa_cnpj)):
            resultado.append((nome, cnpj_val, list(grupo)))
        return resultado

    def tabela_carteira(self, itens: list[LinhaCarteira]) -> Table:
        dados = [
            ["PRODUTO", "BANCO", "TIPO", "DATA\nEMISSAO", "DATA\nVCTO", "PRAZO", "TAXA", "VALOR DA\nAPLICACAO", "RENDIMENTO\nBRUTO NO\nPERIODO", "VALOR ATUALIZADO\nNA DATA\n(FLUTUANTE)", "RENDIMENTO\nBRUTO (R$)", "IR", "IOF", "RESGATE LIQ."],
            ["", "", "", "", "", "", "", "", "", "", "", "", "", ""]
        ]

        total_aplicado = Decimal("0")
        total_atualizado = Decimal("0")
        total_ir = Decimal("0")
        total_iof = Decimal("0")
        total_liquido = Decimal("0")
        total_rendimento_bruto = Decimal("0")

        for item in itens:
            total_aplicado += item.valor_aplicacao
            total_atualizado += item.valor_atualizado
            total_ir += item.valor_ir
            total_iof += item.valor_iof
            total_liquido += item.resgate_liquido
            total_rendimento_bruto += item.rendimento_bruto
            dados.append([
                item.produto,
                item.banco,
                item.tipo,
                data_curta(item.data_emissao),
                data_curta(item.data_vencimento),
                f"{item.prazo:,}".replace(",", "."),
                item.taxa,
                moeda(item.valor_aplicacao),
                percentual(item.rendimento_bruto_percentual),
                moeda(item.valor_atualizado),
                moeda(item.rendimento_bruto),
                "-" if item.valor_ir == 0 else moeda(item.valor_ir),
                "-" if item.valor_iof == 0 else moeda(item.valor_iof),
                moeda(item.resgate_liquido)
            ])

        dados.append(["TOTAIS", "", "", "", "", "", "", moeda(total_aplicado), "", moeda(total_atualizado), moeda(total_rendimento_bruto), moeda(total_ir), moeda(total_iof), moeda(total_liquido)])

        ultima_linha = len(dados) - 1

        tabela = Table(dados, colWidths=[22 * mm, 36 * mm, 24 * mm, 15 * mm, 15 * mm, 10 * mm, 18 * mm,
            22 * mm, 18 * mm, 26 * mm, 26 * mm, 15 * mm, 20 * mm, 22 * mm
        ], repeatRows=2)
        estilos = [
            ("SPAN", (0, 0), (0, 1)),
            ("SPAN", (1, 0), (1, 1)),
            ("SPAN", (2, 0), (2, 1)),
            ("SPAN", (3, 0), (3, 1)),
            ("SPAN", (4, 0), (4, 1)),
            ("SPAN", (5, 0), (5, 1)),
            ("SPAN", (6, 0), (6, 1)),
            ("SPAN", (7, 0), (7, 1)),
            ("SPAN", (8, 0), (8, 1)),
            ("SPAN", (9, 0), (9, 1)),
            ("SPAN", (10, 0), (10, 1)),
            ("SPAN", (11, 0), (11, 1)),
            ("SPAN", (12, 0), (12, 1)),
            ("SPAN", (13, 0), (13, 1)),
            ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#BFBFBF")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 6.5),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (0, 2), (0, ultima_linha), "LEFT"),
            ("ALIGN", (7, 2), (13, ultima_linha), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
            ("TOPPADDING", (0, 0), (-1, -1), 1.8),
            ("BACKGROUND", (0, ultima_linha), (-1, ultima_linha), colors.HexColor("#E6E6E6")),
            ("FONTNAME", (0, ultima_linha), (-1, ultima_linha), "Helvetica-Bold")
        ]
        tabela.setStyle(TableStyle(estilos))
        return tabela
