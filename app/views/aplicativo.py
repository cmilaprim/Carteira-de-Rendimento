import logging
import tkinter as tk
from datetime import date
from tkinter import messagebox, simpledialog, ttk

import sv_ttk
from tkcalendar import DateEntry

from app.controllers.carteira_controller import CarteiraController, DadosAplicacaoFormulario
from app.utils.abridor_arquivo import abrir_arquivo
from app.utils.conversores import texto_para_data
from app.utils.formatadores import data_br
from app.utils.mascaras import decimal_para_br, mascara_data, mascara_decimal
from app.views.tela_cadastros import TelaCadastros


class AplicativoCarteira(tk.Tk):
    def __init__(self, logger, controller: CarteiraController):
        super().__init__()
        self.withdraw()
        self.logger: logging.Logger = logger
        self.title("Carteira de Aplicações")
        self.minsize(1000, 580)
        sv_ttk.set_theme("light")
        self.controller = controller
        self._mapa_empresas: dict[str, str] = {}
        self.montar_tela()
        self.carregar_lista()
        try:
            self.state('zoomed') 
        except:
            self.attributes('-zoomed', True)
        self.deiconify()

    def montar_tela(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        aba_aplicacoes = ttk.Frame(notebook)
        notebook.add(aba_aplicacoes, text="  Aplicações  ")
        self.montar_aba_aplicacoes(aba_aplicacoes)

    # ── Aba Aplicações ────────────────────────────────────────────────────────

    def montar_aba_aplicacoes(self, pai) -> None:
        formulario = ttk.LabelFrame(pai, text="Nova aplicação")
        formulario.pack(fill=tk.X, padx=14, pady=(14, 6))

        for i in range(8):
            formulario.columnconfigure(i, weight=1)

        # Linha 0: Empresa | Produto | Valor | Tipo
        ttk.Label(formulario, text="Empresa").grid(row=0, column=0, sticky="w", padx=(10, 4), pady=6)
        self.empresa_aplicacao = ttk.Combobox(formulario, values=[], state="readonly", width=36)
        self.empresa_aplicacao.grid(row=0, column=1, sticky="ew", padx=(4, 10), pady=6)
        self._sem_selecao(self.empresa_aplicacao)

        self.nome_produto = self.campo(formulario, "Produto", 0, 2, largura=28)
        self.valor_aplicado = self.campo(formulario, "Valor aplicado", 0, 4, largura=16)
        mascara_decimal(self.valor_aplicado)

        ttk.Label(formulario, text="Tipo").grid(row=0, column=6, sticky="w", padx=(10, 4), pady=6)
        opcoes_tipo = self.controller.tipos_produto()
        self.tipo_produto = ttk.Combobox(formulario, values=opcoes_tipo, state="readonly", width=14)
        self.tipo_produto.set(opcoes_tipo[0])
        self.tipo_produto.grid(row=0, column=7, sticky="ew", padx=(4, 14), pady=6)
        self._sem_selecao(self.tipo_produto)

        # Linha 1: Emissao | Vencimento | Indexador | Banco
        self.data_emissao = self.campo_data(formulario, "Emissao", 1, 0)
        self.data_vencimento = self.campo_data(formulario, "Vencimento", 1, 2)

        ttk.Label(formulario, text="Indexador").grid(row=1, column=4, sticky="w", padx=(10, 4), pady=6)
        opcoes_indexadores = self.controller.indexadores()
        self.indexador = ttk.Combobox(formulario, values=opcoes_indexadores, state="readonly", width=14)
        self.indexador.set(opcoes_indexadores[0])
        self.indexador.grid(row=1, column=5, sticky="ew", padx=(4, 10), pady=6)
        self.indexador.bind("<<ComboboxSelected>>", self.ao_mudar_indexador)
        self._sem_selecao(self.indexador)

        ttk.Label(formulario, text="Banco").grid(row=1, column=6, sticky="w", padx=(10, 4), pady=6)
        self.banco_aplicacao = ttk.Combobox(formulario, values=[], width=14)
        self.banco_aplicacao.grid(row=1, column=7, sticky="ew", padx=(4, 14), pady=6)

        # Linha 2: % indexador | Taxa/Spread | Salvar (colspan 4)
        self.label_percentual = ttk.Label(formulario, text="% indexador")
        self.label_percentual.grid(row=2, column=0, sticky="w", padx=(10, 4), pady=6)
        self.percentual_indexador = ttk.Entry(formulario, width=12)
        self.percentual_indexador.grid(row=2, column=1, sticky="ew", padx=(4, 10), pady=6)
        self.percentual_indexador.insert(0, "100")
        mascara_decimal(self.percentual_indexador)

        self.label_taxa = ttk.Label(formulario, text="Taxa a.a.")
        self.label_taxa.grid(row=2, column=2, sticky="w", padx=(10, 4), pady=6)
        self.taxa_prefixada = ttk.Entry(formulario, width=12, state="disabled")
        self.taxa_prefixada.grid(row=2, column=3, sticky="ew", padx=(4, 10), pady=6)

        ttk.Button(formulario, text="Salvar aplicacao", command=self.salvar_aplicacao).grid(row=2, column=4, columnspan=4, sticky="ew", padx=(10, 14), pady=6)

        # Barra de ações
        acoes = ttk.Frame(pai)
        acoes.pack(fill=tk.X, padx=14, pady=6)

        ttk.Label(acoes, text="Saldo em:").pack(side=tk.LEFT, padx=(0, 6))
        self.data_saldo = DateEntry(acoes, date_pattern="dd/mm/yyyy", width=12)
        self.data_saldo.pack(side=tk.LEFT)

        ttk.Separator(acoes, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=14, pady=2)

        ttk.Label(acoes, text="Banco:").pack(side=tk.LEFT, padx=(0, 4))
        self.filtro_banco = ttk.Combobox(acoes, values=["Todos"], width=16)
        self.filtro_banco.set("Todos")
        self.filtro_banco.pack(side=tk.LEFT)
        self.filtro_banco.bind("<<ComboboxSelected>>", lambda _e: self.carregar_lista())

        ttk.Separator(acoes, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=14, pady=2)

        ttk.Label(acoes, text="Empresa:").pack(side=tk.LEFT, padx=(0, 4))
        self.filtro_empresa = ttk.Combobox(acoes, values=["Todas"], state="readonly", width=36)
        self.filtro_empresa.set("Todas")
        self.filtro_empresa.pack(side=tk.LEFT)
        self.filtro_empresa.bind("<<ComboboxSelected>>", lambda _e: self.carregar_lista())
        self._sem_selecao(self.filtro_empresa)

        ttk.Separator(acoes, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=14, pady=2)

        ttk.Button(acoes, text="Selecionar todas", command=self.selecionar_todas).pack(side=tk.LEFT, padx=3)
        ttk.Button(acoes, text="Marcar resgatada", command=self.marcar_resgatada).pack(side=tk.LEFT, padx=3)
        ttk.Button(acoes, text="Editar", command=self.abrir_edicao).pack(side=tk.LEFT, padx=3)
        ttk.Button(acoes, text="Excluir", command=self.confirmar_exclusao).pack(side=tk.LEFT, padx=3)

        ttk.Separator(acoes, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=14, pady=2)

        ttk.Button(acoes, text="Gerar PDF", command=self.gerar_carteira_completa).pack(side=tk.LEFT, padx=3)
        ttk.Button(acoes, text="Exportar Excel", command=self.exportar_excel).pack(side=tk.LEFT, padx=3)

        ttk.Separator(acoes, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=14, pady=2)

        ttk.Button(acoes, text="Cadastros", command=self.abrir_cadastros).pack(side=tk.LEFT, padx=3)

        # Lista de aplicações
        lista_frame = ttk.LabelFrame(pai, text="Aplicações cadastradas")
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
            ("resgate", "Resgate", 88)
        ]:
            self.lista.heading(coluna, text=titulo)
            self.lista.column(coluna, width=largura, minwidth=60)

        scrollbar = ttk.Scrollbar(lista_frame, orient="vertical", command=self.lista.yview)
        self.lista.configure(yscrollcommand=scrollbar.set)
        self.lista.tag_configure("resgatada", foreground="#999999")

        self.lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0), pady=6)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 6), pady=6)

        self.lista.bind("<Double-1>", self.abrir_edicao)

        self.atualizar_opcoes_banco()
        self.atualizar_opcoes_empresa()
        self.configurar_autocomplete_banco(self.banco_aplicacao)
        self.configurar_autocomplete_banco(self.filtro_banco, incluir_todos=True, ao_alterar=self.carregar_lista)

    # ── Helpers de formulário ─────────────────────────────────────────────────

    def campo(self, pai, rotulo: str, linha: int, coluna: int, largura: int = 20) -> ttk.Entry:
        ttk.Label(pai, text=rotulo).grid(row=linha, column=coluna, sticky="w", padx=(10, 4), pady=6)
        entrada = ttk.Entry(pai, width=largura)
        entrada.grid(row=linha, column=coluna + 1, sticky="ew", padx=(4, 10), pady=6)
        return entrada

    def campo_data(self, pai, rotulo: str, linha: int, coluna: int):
        ttk.Label(pai, text=rotulo).grid(row=linha, column=coluna, sticky="w", padx=(10, 4), pady=6)
        entrada = ttk.Entry(pai, width=14)
        entrada.insert(0, date.today().strftime("%d/%m/%Y"))
        entrada.grid(row=linha, column=coluna + 1, sticky="ew", padx=(4, 10), pady=6)
        mascara_data(entrada)
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

    def _sem_selecao(self, combo: ttk.Combobox):
        combo.bind("<<ComboboxSelected>>", lambda _: combo.selection_clear())

    def configurar_autocomplete_banco(self, combobox: ttk.Combobox, incluir_todos: bool = False, ao_alterar=None):
        def filtrar(event=None):
            if event and event.keysym in ("Return", "Escape", "Tab", "Up", "Down"):
                return
            texto = combobox.get().strip().lower()
            bancos = self.controller.listar_bancos()
            opcoes = (["Todos"] + bancos) if incluir_todos else bancos
            filtrados = [b for b in opcoes if texto in b.lower()] if texto else opcoes
            combobox["values"] = filtrados
            if ao_alterar:
                ao_alterar()

        combobox.bind("<KeyRelease>", filtrar)

    def atualizar_opcoes_banco(self) -> None:
        bancos = self.controller.listar_bancos()
        opcoes = ["Todos"] + bancos
        self.filtro_banco["values"] = opcoes
        if self.filtro_banco.get() not in opcoes:
            self.filtro_banco.set("Todos")
        self.banco_aplicacao["values"] = bancos

    def atualizar_opcoes_empresa(self) -> None:
        empresas = self.controller.listar_empresas()
        self._mapa_empresas = {e.rotulo: e.id for e in empresas}
        rotulos = list(self._mapa_empresas.keys())
        self.empresa_aplicacao["values"] = rotulos
        opcoes_filtro = ["Todas"] + rotulos
        self.filtro_empresa["values"] = opcoes_filtro
        if self.filtro_empresa.get() not in opcoes_filtro:
            self.filtro_empresa.set("Todas")

    # ── Ações sobre aplicações ────────────────────────────────────────────────

    def salvar_aplicacao(self) -> None:
        try:
            empresa_rotulo = self.empresa_aplicacao.get().strip()
            empresa_id = self._mapa_empresas.get(empresa_rotulo, "")
            self.controller.salvar_aplicacao(
                DadosAplicacaoFormulario(
                        nome_produto=self.nome_produto.get(),
                        valor_aplicado=self.valor_aplicado.get(),
                        data_emissao=self.data_emissao.get(),
                        data_vencimento=self.data_vencimento.get(),
                        indexador=self.indexador.get(),
                        percentual_indexador=self.percentual_indexador.get(),
                        taxa_prefixada=self.taxa_prefixada.get(),
                        tipo_produto=self.tipo_produto.get(),
                        banco=self.banco_aplicacao.get(),
                        empresa_id=empresa_id
                    )
                )
            self.limpar_formulario()
            self.carregar_lista()
            messagebox.showinfo("Sucesso", "Aplicacao salva com sucesso.")
        except Exception as erro:
            self.logger.exception("Erro ao salvar aplicacao.")
            messagebox.showerror("Erro", str(erro))

    def carregar_lista(self) -> None:
        for item in self.lista.get_children():
            self.lista.delete(item)
        banco_filtro = self.filtro_banco.get().strip()
        empresa_filtro = self.filtro_empresa.get().strip()
        empresa_id_filtro = self._mapa_empresas.get(empresa_filtro)
        for linha in self.controller.listar_aplicacoes():
            if banco_filtro and banco_filtro.lower() != "todos":
                if banco_filtro.lower() not in linha.banco.lower():
                    continue
            if empresa_id_filtro is not None:
                if str(linha.empresa_id) != str(empresa_id_filtro):
                    continue
            tags = ("resgatada",) if linha.resgate != "-" else ()
            self.lista.insert("", tk.END, iid=linha.id, values=(linha.produto, linha.banco, linha.tipo, linha.emissao, linha.vencimento, linha.taxa, linha.valor, linha.resgate), tags=tags)

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
        self.empresa_aplicacao.set("")
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
            data_str = simpledialog.askstring("Data do resgate", "Informe a data do resgate (DD/MM/AAAA):", initialvalue=date.today().strftime("%d/%m/%Y"))
            if data_str:
                try:
                    self.controller.marcar_resgatada(aplicacao_id, texto_para_data(data_str))
                    self.carregar_lista()
                except Exception:
                    messagebox.showerror("Erro", "Data invalida. Use o formato DD/MM/AAAA.")

    def abrir_edicao(self, _event=None) -> None:
        selecionados = self.lista.selection()
        if not selecionados:
            return
        if len(selecionados) > 1:
            messagebox.showwarning("Aviso", "Selecione apenas uma aplicacao para editar.")
            return

        aplicacao_id = selecionados[0]
        try:
            apl = self.controller.obter_aplicacao(aplicacao_id)
        except Exception as erro:
            messagebox.showerror("Erro", str(erro))
            return

        dlg = tk.Toplevel(self)
        dlg.title("Editar Aplicacao")
        dlg.geometry("1400x350")
        dlg.resizable(True, False)
        dlg.update()
        dlg.grab_set()

        frame = ttk.LabelFrame(dlg, text="Dados da aplicacao")
        frame.pack(fill=tk.X, padx=14, pady=14)
        for i in range(8):
            frame.columnconfigure(i, weight=1)

        # Linha 0: Produto | Valor | Tipo | Banco
        ttk.Label(frame, text="Empresa").grid(row=0, column=0, sticky="w", padx=(10, 4), pady=6)
        empresa_rotulo_atual = next((rotulo for rotulo, eid in self._mapa_empresas.items() if eid == apl.empresa_id), "")
        empresa_dlg = ttk.Combobox(frame, values=list(self._mapa_empresas.keys()), state="readonly", width=40)
        empresa_dlg.set(empresa_rotulo_atual)
        empresa_dlg.grid(row=0, column=1, sticky="ew", padx=(4, 10), pady=6)

        ttk.Label(frame, text="Valor aplicado").grid(row=0, column=2, sticky="w", padx=(10, 4), pady=6)
        valor_dlg = ttk.Entry(frame, width=16)
        valor_dlg.insert(0, decimal_para_br(apl.valor_aplicado))
        mascara_decimal(valor_dlg)
        valor_dlg.grid(row=0, column=3, sticky="ew", padx=(4, 10), pady=6)

        ttk.Label(frame, text="Tipo").grid(row=0, column=4, sticky="w", padx=(10, 4), pady=6)
        tipo_dlg = ttk.Combobox(frame, values=self.controller.tipos_produto(), state="readonly", width=14)
        tipo_dlg.set(apl.tipo_produto.value)
        tipo_dlg.grid(row=0, column=5, sticky="ew", padx=(4, 10), pady=6)

        ttk.Label(frame, text="Banco").grid(row=0, column=6, sticky="w", padx=(10, 4), pady=6)
        banco_dlg = ttk.Combobox(frame, values=self.controller.listar_bancos(), width=14)
        banco_dlg.set(apl.banco)
        banco_dlg.grid(row=0, column=7, sticky="ew", padx=(4, 14), pady=6)
        self.configurar_autocomplete_banco(banco_dlg)

        # Linha 1: Emissao | Vencimento | Indexador | Produto
        ttk.Label(frame, text="Emissao").grid(row=1, column=0, sticky="w", padx=(10, 4), pady=6)
        emissao_dlg = ttk.Entry(frame, width=14)
        emissao_dlg.insert(0, data_br(apl.data_emissao))
        mascara_data(emissao_dlg)
        emissao_dlg.grid(row=1, column=1, sticky="ew", padx=(4, 10), pady=6)

        ttk.Label(frame, text="Vencimento").grid(row=1, column=2, sticky="w", padx=(10, 4), pady=6)
        vencimento_dlg = ttk.Entry(frame, width=14)
        vencimento_dlg.insert(0, data_br(apl.data_vencimento))
        mascara_data(vencimento_dlg)
        vencimento_dlg.grid(row=1, column=3, sticky="ew", padx=(4, 10), pady=6)

        ttk.Label(frame, text="Indexador").grid(row=1, column=4, sticky="w", padx=(10, 4), pady=6)
        indexador_dlg = ttk.Combobox(frame, values=self.controller.indexadores(), state="readonly", width=14)
        indexador_dlg.set(apl.indexador.value)
        indexador_dlg.grid(row=1, column=5, sticky="ew", padx=(4, 10), pady=6)

        ttk.Label(frame, text="Produto").grid(row=1, column=6, sticky="w", padx=(10, 4), pady=6)
        nome_dlg = ttk.Entry(frame, width=28)
        nome_dlg.insert(0, apl.nome_produto)
        nome_dlg.grid(row=1, column=7, sticky="ew", padx=(4, 14), pady=6)

        # Linha 2: % indexador | Taxa | Botões
        label_pct_dlg = ttk.Label(frame, text="% indexador")
        label_pct_dlg.grid(row=2, column=0, sticky="w", padx=(10, 4), pady=6)
        percentual_dlg = ttk.Entry(frame, width=12)
        mascara_decimal(percentual_dlg)
        percentual_dlg.grid(row=2, column=1, sticky="ew", padx=(4, 10), pady=6)

        label_taxa_dlg = ttk.Label(frame, text="Taxa a.a.")
        label_taxa_dlg.grid(row=2, column=2, sticky="w", padx=(10, 4), pady=6)
        taxa_dlg = ttk.Entry(frame, width=12)
        mascara_decimal(taxa_dlg)
        taxa_dlg.grid(row=2, column=3, sticky="ew", padx=(4, 10), pady=6)

        idx_val = apl.indexador.value
        if idx_val == "PREFIXADO":
            percentual_dlg.insert(0, decimal_para_br(apl.percentual_indexador))
            percentual_dlg.configure(state="disabled")
            taxa_dlg.insert(0, decimal_para_br(apl.taxa_prefixada_anual) if apl.taxa_prefixada_anual else "")
        elif idx_val == "SELIC+":
            percentual_dlg.insert(0, decimal_para_br(apl.percentual_indexador))
            percentual_dlg.configure(state="disabled")
            label_taxa_dlg.configure(text="Spread a.a.")
            taxa_dlg.insert(0, decimal_para_br(apl.spread_anual) if apl.spread_anual else "")
        else:
            percentual_dlg.insert(0, decimal_para_br(apl.percentual_indexador))
            taxa_dlg.configure(state="disabled")

        def ao_mudar_indexador_dlg(_event=None):
            idx = indexador_dlg.get()
            if idx == "PREFIXADO":
                percentual_dlg.configure(state="disabled")
                label_taxa_dlg.configure(text="Taxa a.a.")
                taxa_dlg.configure(state="normal")
            elif idx == "SELIC+":
                percentual_dlg.configure(state="disabled")
                label_taxa_dlg.configure(text="Spread a.a.")
                taxa_dlg.configure(state="normal")
            else:
                percentual_dlg.configure(state="normal")
                label_taxa_dlg.configure(text="Taxa a.a.")
                taxa_dlg.configure(state="disabled")

        indexador_dlg.bind("<<ComboboxSelected>>", ao_mudar_indexador_dlg)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=4, columnspan=4, sticky="ew", padx=(10, 14), pady=6)

        def salvar_edicao():
            try:
                empresa_rotulo = empresa_dlg.get().strip()
                empresa_id = self._mapa_empresas.get(empresa_rotulo, "")
                self.controller.editar_aplicacao(
                    aplicacao_id, 
                    DadosAplicacaoFormulario(
                        nome_produto=nome_dlg.get(),
                        valor_aplicado=valor_dlg.get(),
                        data_emissao=emissao_dlg.get(),
                        data_vencimento=vencimento_dlg.get(),
                        indexador=indexador_dlg.get(),
                        percentual_indexador=percentual_dlg.get(),
                        taxa_prefixada=taxa_dlg.get(),
                        tipo_produto=tipo_dlg.get(),
                        banco=banco_dlg.get(),
                        empresa_id=empresa_id
                        )   
                    )
                self.carregar_lista()
                dlg.destroy()
                messagebox.showinfo("Sucesso", "Aplicacao atualizada com sucesso.")
            except Exception as erro:
                self.logger.exception("Erro ao editar aplicacao.")
                messagebox.showerror("Erro", str(erro))

        ttk.Button(btn_frame, text="Salvar", command=salvar_edicao).pack(side=tk.LEFT, padx=(0, 4), fill=tk.X, expand=True)
        ttk.Button(btn_frame, text="Cancelar", command=dlg.destroy).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def abrir_cadastros(self) -> None:
        def ao_atualizar():
            self.atualizar_opcoes_empresa()
            self.atualizar_opcoes_banco()

        TelaCadastros(self, controller=self.controller, ao_atualizar=ao_atualizar)

    # ── Relatórios ────────────────────────────────────────────────────────────

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
