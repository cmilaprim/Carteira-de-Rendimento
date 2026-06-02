from __future__ import annotations

import os
import logging
import subprocess
import sys
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

try:
    from tkcalendar import DateEntry
except Exception: 
    DateEntry = None

from app.armazenamento.repositorio_aplicacoes import RepositorioAplicacoes
from app.core.conversores import texto_para_data, texto_para_decimal
from app.core.demonstrativo import MontadorDemonstrativo
from app.core.formatadores import data_br, moeda_com_simbolo
from app.core.modelos import Aplicacao, Indexador
from app.relatorios.demonstrativo_carteira_pdf import RelatorioDemonstrativoCarteiraPDF
from app.taxas.servico_taxas import ServicoTaxas

logger = logging.getLogger(__name__)


class AplicativoCarteira(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        logger.info("Iniciando interface da carteira.")
        self.title("Carteira de Aplicacoes - CDI/Selic")
        self.geometry("980x620")
        self.repositorio = RepositorioAplicacoes()
        self.servico_taxas = ServicoTaxas()
        self.montar_tela()
        self.carregar_lista()

    def montar_tela(self) -> None:
        formulario = ttk.LabelFrame(self, text="Cadastro da aplicacao")
        formulario.pack(fill=tk.X, padx=10, pady=8)

        self.nome_produto = self.entrada(formulario, "Produto", 0, 0, largura=28)
        self.numero_controle = self.entrada(formulario, "N controle", 0, 2, largura=15)
        self.numero_nota = self.entrada(formulario, "N nota", 0, 4, largura=15)

        self.valor_aplicado = self.entrada(formulario, "Valor aplicado", 1, 0, largura=18)
        self.data_emissao = self.entrada_data(formulario, "Data emissao", 1, 2)
        self.data_vencimento = self.entrada_data(formulario, "Data vencimento", 1, 4)

        ttk.Label(formulario, text="Indexador").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.indexador = ttk.Combobox(formulario, values=[item.value for item in Indexador], state="readonly", width=16)
        self.indexador.set(Indexador.CDI.value)
        self.indexador.grid(row=2, column=1, sticky="w", padx=5, pady=4)

        self.percentual_indexador = self.entrada(formulario, "% do indexador", 2, 2, largura=12)
        self.percentual_indexador.insert(0, "100")
        self.taxa_prefixada = self.entrada(formulario, "Taxa prefixada a.a.", 2, 4, largura=12)

        botoes = ttk.Frame(formulario)
        botoes.grid(row=3, column=0, columnspan=6, sticky="w", padx=5, pady=8)
        ttk.Button(botoes, text="Salvar aplicacao", command=self.salvar_aplicacao).pack(side=tk.LEFT, padx=4)
        ttk.Button(botoes, text="Excluir selecionada", command=self.confirmar_exclusao).pack(side=tk.LEFT, padx=4)
        ttk.Button(botoes, text="Atualizar CDI/Selic", command=self.atualizar_taxas).pack(side=tk.LEFT, padx=4)
        ttk.Button(botoes, text="Gerar documento", command=self.gerar_demonstrativo).pack(side=tk.LEFT, padx=4)

        rodape = ttk.LabelFrame(self, text="Periodo do demonstrativo")
        rodape.pack(fill=tk.X, padx=10, pady=8)
        self.periodo_inicio = self.entrada_data(rodape, "Inicio", 0, 0)
        self.periodo_fim = self.entrada_data(rodape, "Fim", 0, 2)
        self.data_saldo = self.entrada_data(rodape, "Saldo em", 0, 4)

        lista_frame = ttk.LabelFrame(self, text="Aplicacoes cadastradas")
        lista_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        colunas = ("produto", "controle", "emissao", "vencimento", "taxa", "valor")
        self.lista = ttk.Treeview(lista_frame, columns=colunas, show="headings")
        for coluna, titulo, largura in [
            ("produto", "Produto", 260),
            ("controle", "N controle", 90),
            ("emissao", "Emissao", 90),
            ("vencimento", "Vencimento", 90),
            ("taxa", "Taxa", 110),
            ("valor", "Valor", 120),
        ]:
            self.lista.heading(coluna, text=titulo)
            self.lista.column(coluna, width=largura)
        self.lista.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def entrada(self, pai, rotulo: str, linha: int, coluna: int, largura: int = 20) -> ttk.Entry:
        ttk.Label(pai, text=rotulo).grid(row=linha, column=coluna, sticky="w", padx=5, pady=4)
        entrada = ttk.Entry(pai, width=largura)
        entrada.grid(row=linha, column=coluna + 1, sticky="w", padx=5, pady=4)
        return entrada

    def entrada_data(self, pai, rotulo: str, linha: int, coluna: int):
        ttk.Label(pai, text=rotulo).grid(row=linha, column=coluna, sticky="w", padx=5, pady=4)
        if DateEntry:
            entrada = DateEntry(pai, date_pattern="dd/mm/yyyy", width=14)
        else:
            entrada = ttk.Entry(pai, width=16)
            entrada.insert(0, date.today().strftime("%d/%m/%Y"))
        entrada.grid(row=linha, column=coluna + 1, sticky="w", padx=5, pady=4)
        return entrada

    def salvar_aplicacao(self) -> None:
        try:
            logger.info("Solicitacao de cadastro de aplicacao recebida.")
            indexador = Indexador(self.indexador.get())
            taxa_prefixada = None
            if indexador == Indexador.PREFIXADO:
                taxa_prefixada = texto_para_decimal(self.taxa_prefixada.get())

            aplicacao = Aplicacao.criar(
                nome_produto=self.nome_produto.get(),
                numero_controle=self.numero_controle.get(),
                numero_nota=self.numero_nota.get(),
                valor_aplicado=texto_para_decimal(self.valor_aplicado.get()),
                data_emissao=texto_para_data(self.data_emissao.get()),
                data_vencimento=texto_para_data(self.data_vencimento.get()),
                indexador=indexador,
                percentual_indexador=texto_para_decimal(self.percentual_indexador.get()),
                taxa_prefixada_anual=taxa_prefixada
            )
            logger.info("Salvando aplicacao %s: produto=%s controle=%s indexador=%s valor=%s emissao=%s vencimento=%s",
                aplicacao.id,
                aplicacao.nome_produto,
                aplicacao.numero_controle,
                aplicacao.indexador.value,
                aplicacao.valor_aplicado,
                aplicacao.data_emissao,
                aplicacao.data_vencimento)
            self.repositorio.adicionar(aplicacao)
            self.limpar_formulario()
            self.carregar_lista()
            logger.info("Aplicacao %s salva com sucesso.", aplicacao.id)
            messagebox.showinfo("Sucesso", "Aplicacao salva com sucesso.")
        except Exception as erro:
            logger.exception("Erro ao salvar aplicacao.")
            messagebox.showerror("Erro", str(erro))
    
    
    def carregar_lista(self) -> None:
        for item in self.lista.get_children():
            self.lista.delete(item)
        aplicacoes = self.repositorio.listar()
        logger.debug("Carregando lista de aplicacoes na tela: total=%d", len(aplicacoes))
        for aplicacao in aplicacoes:
            self.lista.insert("", tk.END, iid=aplicacao.id, values=(
                aplicacao.nome_produto,
                aplicacao.numero_controle,
                data_br(aplicacao.data_emissao),
                data_br(aplicacao.data_vencimento),
                aplicacao.rotulo_taxa,
                moeda_com_simbolo(aplicacao.valor_aplicado)
            ))

    def limpar_formulario(self) -> None:
        for entrada in [self.nome_produto, self.numero_controle, self.numero_nota, self.valor_aplicado, self.taxa_prefixada]:
            entrada.delete(0, tk.END)
        self.percentual_indexador.delete(0, tk.END)
        self.percentual_indexador.insert(0, "100")
        self.indexador.set(Indexador.CDI.value)

    def confirmar_exclusao(self) -> None:
        if messagebox.askyesno("Confirmar exclusao", "Deseja realmente excluir a aplicacao selecionada?"):
            self.excluir_selecionada()

    def excluir_selecionada(self) -> None:
        selecionados = self.lista.selection()
        if not selecionados:
            logger.warning("Exclusao solicitada sem aplicacao selecionada.")
            messagebox.showwarning("Aviso", "Selecione uma aplicacao.")
            return
        logger.info("Excluindo aplicacao selecionada: %s", selecionados[0])
        self.repositorio.excluir(selecionados[0])
        self.carregar_lista()
        logger.info("Aplicacao excluida com sucesso: %s", selecionados[0])

    def atualizar_taxas(self) -> None:
        try:
            logger.info("Solicitacao de atualizacao de taxas recebida.")
            inicio = texto_para_data(self.periodo_inicio.get())
            fim = texto_para_data(self.periodo_fim.get())
            hoje = date.today()
            fim_busca = min(fim, hoje)
            if inicio > fim_busca:
                logger.info("Atualizacao de taxas ignorada: inicio=%s fim_busca=%s", inicio, fim_busca)
                messagebox.showinfo("Info", "Nao ha periodo historico para atualizar.")
                return
            logger.info("Atualizando CDI/Selic de %s ate %s.", inicio, fim_busca)
            self.servico_taxas.atualizar(Indexador.CDI, inicio, fim_busca)
            self.servico_taxas.atualizar(Indexador.SELIC, inicio, fim_busca)
            logger.info("Taxas CDI/Selic atualizadas com sucesso.")
            messagebox.showinfo("Sucesso", "Taxas CDI/Selic atualizadas e salvas em JSON.")
        except Exception as erro:
            logger.exception("Erro ao atualizar taxas CDI/Selic.")
            messagebox.showerror("Erro ao atualizar taxas", str(erro))

    def gerar_demonstrativo(self) -> None:
        try:
            logger.info("Solicitacao de geracao de demonstrativo recebida.")
            selecionados = self.lista.selection()
            if not selecionados:
                logger.warning("Geracao de demonstrativo solicitada sem aplicacao selecionada.")
                messagebox.showwarning("Aviso", "Selecione uma aplicacao para gerar o documento.")
                return

            aplicacao = self.repositorio.obter(selecionados[0])
            periodo_inicio = texto_para_data(self.periodo_inicio.get())
            periodo_fim = texto_para_data(self.periodo_fim.get())
            data_saldo = texto_para_data(self.data_saldo.get())
            logger.info("Gerando demonstrativo da aplicacao %s: periodo=%s ate %s saldo=%s", aplicacao.numero_controle,
                periodo_inicio,
                periodo_fim,
                data_saldo
            )

            demonstrativo = MontadorDemonstrativo().montar([aplicacao], periodo_inicio, periodo_fim, data_saldo)
            caminho = RelatorioDemonstrativoCarteiraPDF().gerar_aplicacao(demonstrativo,numero_controle=aplicacao.numero_controle)
            logger.info("Demonstrativo gerado com sucesso: %s", caminho)
            self.abrir_arquivo(caminho)
            messagebox.showinfo("Sucesso", f"Documento da aplicacao gerado:\n{caminho}")
        except Exception as erro:
            logger.exception("Erro ao gerar demonstrativo.")
            messagebox.showerror("Erro", str(erro))

    def abrir_arquivo(self, caminho) -> None:
        caminho = os.path.abspath(str(caminho))
        logger.info("Abrindo arquivo: %s", caminho)
        if sys.platform.startswith("win"):
            os.startfile(caminho)  
        elif sys.platform == "darwin":
            subprocess.run(["open", caminho], check=False)
        else:
            subprocess.run(["xdg-open", caminho], check=False)


def iniciar_aplicativo() -> None:
    app = AplicativoCarteira()
    app.mainloop()
