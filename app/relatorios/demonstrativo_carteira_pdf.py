from __future__ import annotations

from pathlib import Path
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.formatadores import data_br, data_curta, moeda, percentual
from app.core.modelos import DemonstrativoCarteira


class RelatorioDemonstrativoCarteiraPDF:
    def __init__(self, pasta_saida: str | Path = "data/pdfs") -> None:
        self.pasta_saida = Path(pasta_saida)
        self.pasta_saida.mkdir(parents=True, exist_ok=True)

    def gerar(self, demonstrativo: DemonstrativoCarteira) -> Path:
        caminho = self.pasta_saida / f"demonstrativo_carteira_{demonstrativo.data_saldo.isoformat()}.pdf"
        documento = self.criar_documento(caminho)
        estilos = getSampleStyleSheet()
        elementos = []

        titulo_mov = f"MOVIMENTACAO DA CARTEIRA ({data_br(demonstrativo.periodo_inicio)} A {data_br(demonstrativo.periodo_fim)})"
        elementos.append(Paragraph(f"<b>{titulo_mov}</b>", estilos["Normal"]))
        elementos.append(Spacer(1, 3 * mm))
        elementos.append(self.tabela_movimentacao(demonstrativo))
        elementos.append(Spacer(1, 7 * mm))

        titulo_saldo = f"SALDO DA CARTEIRA ({data_br(demonstrativo.data_saldo)})"
        elementos.append(Paragraph(f"<b>{titulo_saldo}</b>", estilos["Normal"]))
        elementos.append(Spacer(1, 3 * mm))
        elementos.append(self.tabela_carteira(demonstrativo, mostrar_totais=True))

        documento.build(elementos)
        return caminho

    def gerar_aplicacao(self, demonstrativo: DemonstrativoCarteira, numero_controle: str = "") -> Path:
        identificador = numero_controle.strip().replace("/", "-").replace("\\", "-") or "aplicacao"
        caminho = self.pasta_saida / f"aplicacao_{identificador}_{demonstrativo.data_saldo.isoformat()}.pdf"
        documento = self.criar_documento(caminho)
        estilos = getSampleStyleSheet()
        elementos = []

        titulo = f"DADOS DA APLICACAO ({data_br(demonstrativo.data_saldo)})"
        elementos.append(Paragraph(f"<b>{titulo}</b>", estilos["Normal"]))
        elementos.append(Spacer(1, 3 * mm))
        elementos.append(self.tabela_carteira(demonstrativo, mostrar_totais=False))

        documento.build(elementos)
        return caminho

    def criar_documento(self, caminho: Path) -> SimpleDocTemplate:
        return SimpleDocTemplate(
            str(caminho),
            pagesize=landscape(A4),
            leftMargin=8 * mm,
            rightMargin=8 * mm,
            topMargin=8 * mm,
            bottomMargin=8 * mm
        )

    def tabela_movimentacao(self, demonstrativo: DemonstrativoCarteira) -> Table:
        dados = [
            ["DATA", "OPERACAO", "NUMERO\nDA NOTA", "VALOR\nRESGATE BRUTO", "IMPOSTO", "IOF", "LIQUIDO DA OPERACAO", ""],
            ["", "", "", "", "", "D/C"],
        ]
        for item in demonstrativo.movimentacoes:
            dados.append([
                data_curta(item.data),
                item.operacao,
                item.numero_nota,
                moeda(item.valor_resgate_bruto),
                "-" if item.valor_ir == 0 else moeda(item.valor_ir),
                moeda(item.valor_iof),
                moeda(item.valor_liquido_operacao),
                item.dc
            ])
        if len(dados) == 2:
            dados.append(["-", "Sem movimentacao no periodo", "", "", "", "", ""])

        tabela = Table(dados, colWidths=[
                                42*mm,  # produto
                                18*mm,  # controle
                                16*mm,  # emissao
                                16*mm,  # vencimento
                                12*mm,  # prazo
                                20*mm,  # taxa
                                25*mm,  # valor aplicacao
                                22*mm,  # rendimento
                                30*mm,  # valor atualizado
                                16*mm,  # IR
                                16*mm,  # IOF
                                22*mm   # resgate liquido
                            ], repeatRows=2)
        tabela.setStyle(TableStyle([
            ("SPAN", (5, 0), (6, 0)),
            ("SPAN", (0, 0), (0, 1)),
            ("SPAN", (1, 0), (1, 1)),
            ("SPAN", (2, 0), (2, 1)),
            ("SPAN", (3, 0), (3, 1)),
            ("SPAN", (4, 0), (4, 1)),
            ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#BFBFBF")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.2),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (1, 2), (1, -1), "LEFT"),
            ("ALIGN", (3, 2), (5, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
        ]))
        return tabela

    def tabela_carteira(self, demonstrativo: DemonstrativoCarteira, mostrar_totais: bool) -> Table:
        dados = [
            ["PRODUTO", "N\u00b0\nCONTROLE", "DATA\nEMISSAO", "DATA\nVCTO", "PRAZO", "TAXA", "VALOR DA\nAPLICACAO", "RENDIMENTO\nBRUTO NO\nPERIODO", "VALOR ATUALIZADO\nNA DATA\n(FLUTUANTE)", "IR", "IOF", "RESGATE LIQ."],
            ["", "", "", "", "", "", "", "", "", "", "", ""],
        ]

        total_aplicado = Decimal("0")
        total_atualizado = Decimal("0")
        total_ir = Decimal("0")
        total_iof = Decimal("0")
        total_liquido = Decimal("0")

        for item in demonstrativo.carteira:
            total_aplicado += item.valor_aplicacao
            total_atualizado += item.valor_atualizado
            total_ir += item.valor_ir
            total_iof += item.valor_iof
            total_liquido += item.resgate_liquido
            dados.append([
                item.produto,
                item.numero_controle,
                data_curta(item.data_emissao),
                data_curta(item.data_vencimento),
                f"{item.prazo:,}".replace(",", "."),
                item.taxa,
                moeda(item.valor_aplicacao),
                percentual(item.rendimento_bruto_percentual),
                moeda(item.valor_atualizado),
                "-" if item.valor_ir == 0 else moeda(item.valor_ir),
                "-" if item.valor_iof == 0 else moeda(item.valor_iof),
                moeda(item.resgate_liquido)
            ])

        if mostrar_totais:
            dados.append(["TOTAIS", "", "", "", "", "", moeda(total_aplicado), "", moeda(total_atualizado), moeda(total_ir), moeda(total_iof), moeda(total_liquido)])

        ultima_linha = len(dados) - 1

        tabela = Table(dados, 
                        colWidths=[
                                42*mm,  # produto
                                18*mm,  # controle
                                16*mm,  # emissao
                                16*mm,  # vencimento
                                12*mm,  # prazo
                                20*mm,  # taxa
                                25*mm,  # valor aplicacao
                                22*mm,  # rendimento
                                30*mm,  # valor atualizado
                                16*mm,  # IR
                                16*mm,  # IOF
                                22*mm   # resgate liquido
                            ],repeatRows=2)
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
            ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#BFBFBF")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 6.5),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (0, 2), (0, ultima_linha), "LEFT"),
            ("ALIGN", (6, 2), (11, ultima_linha), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
            ("TOPPADDING", (0, 0), (-1, -1), 1.8)
        ]
        if mostrar_totais:
            estilos.extend([
                ("BACKGROUND", (0, ultima_linha), (-1, ultima_linha), colors.HexColor("#E6E6E6")),
                ("FONTNAME", (0, ultima_linha), (-1, ultima_linha), "Helvetica-Bold")
            ])
        tabela.setStyle(TableStyle(estilos))
        return tabela
0