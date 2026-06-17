import logging
import tkinter as tk
from datetime import date
from tkinter import messagebox, simpledialog, ttk

import sv_ttk
from tkcalendar import DateEntry

from app.controllers.carteira_controller import CarteiraController, DadosAplicacaoFormulario
from app.utils.abridor_arquivo import abrir_arquivo
from app.utils.conversores import texto_para_data


class AplicativoCarteira(tk.Tk):
    def __init__(self, logger):
        super().__init__()
        self.logger: logging.Logger = logger
        self.title("Carteira de Aplicacoes")
        self.geometry("1200x720")
        self.minsize(960, 580)
        sv_ttk.set_theme("light")
        self.controller = CarteiraController(logger=self.logger)
        self.montar_tela()
        self.carregar_lista()

    def montar_tela(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        aba_aplicacoes = ttk.Frame(notebook)
        notebook.add(aba_aplicacoes, text="  Aplicacoes  ")
        self.montar_aba_aplicacoes(aba_aplicacoes)

        aba_bancos = ttk.Frame(notebook)
        notebook.add(aba_bancos, text="  Bancos  ")
        self.montar_aba_bancos(aba_bancos)

    # ── Aba Aplicações ────────────────────────────────────────────────────────

    def montar_aba_aplicacoes(self, pai) -> None:
        formulario = ttk.LabelFrame(pai, text="Nova aplicacao")
        formulario.pack(fill=tk.X, padx=14, pady=(14, 6))

        for i in range(8):
            formulario.columnconfigure(i, weight=1)

        # Linha 0: Produto | Valor | Tipo | Banco
        self.nome_produto = self.campo(formulario, "Produto", 0, 0, largura=28)
        self.valor_aplicado = self.campo(formulario, "Valor aplicado", 0, 2, largura=16)

        ttk.Label(formulario, text="Tipo").grid(row=0, column=4, sticky="w", padx=(10, 4), pady=6)
        opcoes_tipo = self.controller.tipos_produto()
        self.tipo_produto = ttk.Combobox(formulario, values=opcoes_tipo, state="readonly", width=14)
        self.tipo_produto.set(opcoes_tipo[0])
        self.tipo_produto.grid(row=0, column=5, sticky="ew", padx=(4, 10), pady=6)

        ttk.Label(formulario, text="Banco").grid(row=0, column=6, sticky="w", padx=(10, 4), pady=6)
        self.banco_aplicacao = ttk.Combobox(formulario, values=[], state="readonly", width=14)
        self.banco_aplicacao.grid(row=0, column=7, sticky="ew", padx=(4, 14), pady=6)

        # Linha 1: Emissao | Vencimento | Indexador
        self.data_emissao = self.campo_data(formulario, "Emissao", 1, 0)
        self.data_vencimento = self.campo_data(formulario, "Vencimento", 1, 2)

        ttk.Label(formulario, text="Indexador").grid(row=1, column=4, sticky="w", padx=(10, 4), pady=6)
        opcoes_indexadores = self.controller.indexadores()
        self.indexador = ttk.Combobox(formulario, values=opcoes_indexadores, state="readonly", width=14)
        self.indexador.set(opcoes_indexadores[0])
        self.indexador.grid(row=1, column=5, sticky="ew", padx=(4, 10), pady=6)
        self.indexador.bind("<<ComboboxSelected>>", self.ao_mudar_indexador)

        # Linha 2: % indexador | Taxa/Spread | Salvar (colspan 4)
        self.label_percentual = ttk.Label(formulario, text="% indexador")
        self.label_percentual.grid(row=2, column=0, sticky="w", padx=(10, 4), pady=6)
        self.percentual_indexador = ttk.Entry(formulario, width=12)
        self.percentual_indexador.grid(row=2, column=1, sticky="ew", padx=(4, 10), pady=6)
        self.percentual_indexador.insert(0, "100")

        self.label_taxa = ttk.Label(formulario, text="Taxa a.a.")
        self.label_taxa.grid(row=2, column=2, sticky="w", padx=(10, 4), pady=6)
        self.taxa_prefixada = ttk.Entry(formulario, width=12, state="disabled")
        self.taxa_prefixada.grid(row=2, column=3, sticky="ew", padx=(4, 10), pady=6)

        ttk.Button(formulario, text="Salvar aplicacao", command=self.salvar_aplicacao).grid(
            row=2, column=4, columnspan=4, sticky="ew", padx=(10, 14), pady=6)

        # Barra de ações
        acoes = ttk.Frame(pai)
        acoes.pack(fill=tk.X, padx=14, pady=6)

        ttk.Label(acoes, text="Saldo em:").pack(side=tk.LEFT, padx=(0, 6))
        self.data_saldo = DateEntry(acoes, date_pattern="dd/mm/yyyy", width=12)
        self.data_saldo.pack(side=tk.LEFT)

        ttk.Separator(acoes, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=14, pady=2)

        ttk.Label(acoes, text="Banco:").pack(side=tk.LEFT, padx=(0, 4))
        self.filtro_banco = ttk.Combobox(acoes, values=["Todos"], state="readonly", width=16)
        self.filtro_banco.set("Todos")
        self.filtro_banco.pack(side=tk.LEFT)
        self.filtro_banco.bind("<<ComboboxSelected>>", lambda _e: self.carregar_lista())

        ttk.Separator(acoes, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=14, pady=2)

        ttk.Button(acoes, text="Selecionar todas", command=self.selecionar_todas).pack(side=tk.LEFT, padx=3)
        ttk.Button(acoes, text="Marcar resgatada", command=self.marcar_resgatada).pack(side=tk.LEFT, padx=3)
        ttk.Button(acoes, text="Excluir", command=self.confirmar_exclusao).pack(side=tk.LEFT, padx=3)

        ttk.Separator(acoes, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=14, pady=2)

        ttk.Button(acoes, text="Gerar PDF", command=self.gerar_carteira_completa).pack(side=tk.LEFT, padx=3)
        ttk.Button(acoes, text="Exportar Excel", command=self.exportar_excel).pack(side=tk.LEFT, padx=3)

        # Lista de aplicações
        lista_frame = ttk.LabelFrame(pai, text="Aplicacoes cadastradas")
        lista_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(6, 14))

        colunas = ("produto", "banco", "tipo", "emissao", "vencimento", "taxa", "valor", "resgate")
        self.lista = ttk.Treeview(lista_frame, columns=colunas, show="headings", selectmode="extended")
        for coluna, titulo, largura in [
            ("produto", "Produto", 220),
            ("banco", "Banco", 120),
            ("tipo", "Tipo", 100),
            ("emissao", "Emissao", 88),
            ("vencimento", "Vencimento", 88),
            ("taxa", "Taxa", 120),
            ("valor", "Valor", 120),
            ("resgate", "Resgate", 88),
        ]:
            self.lista.heading(coluna, text=titulo)
            self.lista.column(coluna, width=largura, minwidth=60)

        scrollbar = ttk.Scrollbar(lista_frame, orient="vertical", command=self.lista.yview)
        self.lista.configure(yscrollcommand=scrollbar.set)
        self.lista.tag_configure("resgatada", foreground="#999999")

        self.lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0), pady=6)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 6), pady=6)

        self.atualizar_opcoes_banco()

    # ── Aba Bancos ────────────────────────────────────────────────────────────

    def montar_aba_bancos(self, pai) -> None:
        form = ttk.LabelFrame(pai, text="Novo banco")
        form.pack(fill=tk.X, padx=14, pady=(14, 6))
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Nome do banco").grid(row=0, column=0, sticky="w", padx=(10, 4), pady=10)
        self.nome_banco = ttk.Entry(form, width=30)
        self.nome_banco.grid(row=0, column=1, sticky="ew", padx=(4, 10), pady=10)
        self.nome_banco.bind("<Return>", lambda _e: self.adicionar_banco())
        ttk.Button(form, text="Adicionar", command=self.adicionar_banco).grid(
            row=0, column=2, sticky="ew", padx=(4, 14), pady=10)

        lista_frame = ttk.LabelFrame(pai, text="Bancos cadastrados")
        lista_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(6, 14))

        self.lista_bancos = tk.Listbox(lista_frame, selectmode="single", font=("Segoe UI", 10), activestyle="none")
        scrollbar_bancos = ttk.Scrollbar(lista_frame, orient="vertical", command=self.lista_bancos.yview)
        self.lista_bancos.configure(yscrollcommand=scrollbar_bancos.set)

        self.lista_bancos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0), pady=6)
        scrollbar_bancos.pack(side=tk.LEFT, fill=tk.Y, pady=6)

        ttk.Button(lista_frame, text="Remover selecionado", command=self.remover_banco).pack(
            side=tk.LEFT, padx=14, pady=6, anchor="n")

        self.carregar_bancos()

    # ── Helpers de formulário ─────────────────────────────────────────────────

    def campo(self, pai, rotulo: str, linha: int, coluna: int, largura: int = 20) -> ttk.Entry:
        ttk.Label(pai, text=rotulo).grid(row=linha, column=coluna, sticky="w", padx=(10, 4), pady=6)
        entrada = ttk.Entry(pai, width=largura)
        entrada.grid(row=linha, column=coluna + 1, sticky="ew", padx=(4, 10), pady=6)
        return entrada

    def campo_data(self, pai, rotulo: str, linha: int, coluna: int):
        ttk.Label(pai, text=rotulo).grid(row=linha, column=coluna, sticky="w", padx=(10, 4), pady=6)
        entrada = DateEntry(pai, date_pattern="dd/mm/yyyy", width=14)
        entrada.grid(row=linha, column=coluna + 1, sticky="w", padx=(4, 10), pady=6)
        return entrada

    def ao_mudar_indexador(self, _event=None) -> None:
        idx = self.indexador.get()
        if idx == "PREFIXADO":
            self.percentual_indexador.configure(state="disabled")
            self.label_taxa.configure(text="Taxa a.a.")
            self.taxa_prefixada.configure(state="normal")
        elif idx == "SELIC+":
            self.percentual_indexador.configure(state="disabled")
            self.label_taxa.configure(text="Spread a.a.")
            self.taxa_prefixada.configure(state="normal")
        else:
            self.percentual_indexador.configure(state="normal")
            self.label_taxa.configure(text="Taxa a.a.")
            self.taxa_prefixada.configure(state="disabled")

    # ── Ações sobre aplicações ────────────────────────────────────────────────

    def salvar_aplicacao(self) -> None:
        try:
            self.controller.salvar_aplicacao(DadosAplicacaoFormulario(
                nome_produto=self.nome_produto.get(),
                valor_aplicado=self.valor_aplicado.get(),
                data_emissao=self.data_emissao.get(),
                data_vencimento=self.data_vencimento.get(),
                indexador=self.indexador.get(),
                percentual_indexador=self.percentual_indexador.get(),
                taxa_prefixada=self.taxa_prefixada.get(),
                tipo_produto=self.tipo_produto.get(),
                banco=self.banco_aplicacao.get(),
            ))
            self.limpar_formulario()
            self.carregar_lista()
            messagebox.showinfo("Sucesso", "Aplicacao salva com sucesso.")
        except Exception as erro:
            self.logger.exception("Erro ao salvar aplicacao.")
            messagebox.showerror("Erro", str(erro))

    def carregar_lista(self) -> None:
        for item in self.lista.get_children():
            self.lista.delete(item)
        banco_filtro = self.filtro_banco.get()
        for linha in self.controller.listar_aplicacoes():
            if banco_filtro != "Todos" and linha.banco != banco_filtro:
                continue
            tags = ("resgatada",) if linha.resgate != "-" else ()
            self.lista.insert("", tk.END, iid=linha.id, values=(
                linha.produto, linha.banco, linha.tipo, linha.emissao,
                linha.vencimento, linha.taxa, linha.valor, linha.resgate,
            ), tags=tags)

    def limpar_formulario(self) -> None:
        self.taxa_prefixada.configure(state="normal")
        for entrada in [self.nome_produto, self.valor_aplicado, self.taxa_prefixada]:
            entrada.delete(0, tk.END)
        self.percentual_indexador.configure(state="normal")
        self.percentual_indexador.delete(0, tk.END)
        self.percentual_indexador.insert(0, "100")
        self.indexador.set(self.controller.indexadores()[0])
        self.tipo_produto.set(self.controller.tipos_produto()[0])
        self.banco_aplicacao.set("")
        self.ao_mudar_indexador()

    def selecionar_todas(self) -> None:
        self.lista.selection_set(self.lista.get_children())

    def confirmar_exclusao(self) -> None:
        if messagebox.askyesno("Confirmar exclusao", "Deseja realmente excluir a aplicacao selecionada?"):
            self.excluir_selecionada()

    def excluir_selecionada(self) -> None:
        selecionados = self.lista.selection()
        if not selecionados:
            messagebox.showwarning("Aviso", "Selecione uma aplicacao.")
            return
        self.controller.excluir_aplicacao(selecionados[0])
        self.carregar_lista()

    def marcar_resgatada(self) -> None:
        selecionados = self.lista.selection()
        if not selecionados:
            messagebox.showwarning("Aviso", "Selecione uma aplicacao.")
            return
        aplicacao_id = selecionados[0]
        tags = self.lista.item(aplicacao_id, "tags")
        if "resgatada" in tags:
            if messagebox.askyesno("Desfazer resgate", "Deseja desfazer o resgate desta aplicacao?"):
                self.controller.marcar_resgatada(aplicacao_id, None)
                self.carregar_lista()
        else:
            data_str = simpledialog.askstring(
                "Data do resgate",
                "Informe a data do resgate (DD/MM/AAAA):",
                initialvalue=date.today().strftime("%d/%m/%Y"),
            )
            if data_str:
                try:
                    self.controller.marcar_resgatada(aplicacao_id, texto_para_data(data_str))
                    self.carregar_lista()
                except Exception:
                    messagebox.showerror("Erro", "Data invalida. Use o formato DD/MM/AAAA.")

    def exportar_excel(self) -> None:
        try:
            selecionados = list(self.lista.selection())
            if not selecionados:
                messagebox.showwarning("Aviso", "Selecione ao menos uma aplicacao.")
                return
            caminho = self.controller.gerar_documento_carteira_excel(selecionados, self.data_saldo.get())
            abrir_arquivo(caminho)
            messagebox.showinfo("Sucesso", f"Excel gerado ({len(selecionados)} aplicacoes):\n{caminho}")
        except Exception as erro:
            self.logger.exception("Erro ao exportar Excel.")
            messagebox.showerror("Erro", str(erro))

    def gerar_carteira_completa(self) -> None:
        try:
            selecionados = list(self.lista.selection())
            if not selecionados:
                messagebox.showwarning("Aviso", "Selecione ao menos uma aplicacao.")
                return
            caminho = self.controller.gerar_documento_carteira(selecionados, self.data_saldo.get())
            abrir_arquivo(caminho)
            messagebox.showinfo("Sucesso", f"PDF gerado ({len(selecionados)} aplicacoes):\n{caminho}")
        except Exception as erro:
            self.logger.exception("Erro ao gerar relatorio da carteira.")
            messagebox.showerror("Erro", str(erro))

    # ── Ações sobre bancos ────────────────────────────────────────────────────

    def carregar_bancos(self) -> None:
        self.lista_bancos.delete(0, tk.END)
        bancos = self.controller.listar_bancos()
        for banco in bancos:
            self.lista_bancos.insert(tk.END, banco)
        self.atualizar_opcoes_banco(bancos)

    def atualizar_opcoes_banco(self, bancos: list[str] | None = None) -> None:
        if bancos is None:
            bancos = self.controller.listar_bancos()
        opcoes = ["Todos"] + bancos
        self.filtro_banco["values"] = opcoes
        if self.filtro_banco.get() not in opcoes:
            self.filtro_banco.set("Todos")
        self.banco_aplicacao["values"] = bancos

    def adicionar_banco(self) -> None:
        nome = self.nome_banco.get().strip()
        if not nome:
            messagebox.showwarning("Aviso", "Informe o nome do banco.")
            return
        self.controller.adicionar_banco(nome)
        self.nome_banco.delete(0, tk.END)
        self.carregar_bancos()

    def remover_banco(self) -> None:
        selecao = self.lista_bancos.curselection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione um banco.")
            return
        nome = self.lista_bancos.get(selecao[0])
        if messagebox.askyesno("Confirmar", f"Remover o banco '{nome}'?"):
            self.controller.remover_banco(nome)
            self.carregar_bancos()
