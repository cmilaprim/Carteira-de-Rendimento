import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.carteira_controller import CarteiraController


class TelaCadastros(tk.Toplevel):
    def __init__(self, pai, controller: CarteiraController, ao_atualizar):
        super().__init__(pai)
        self.controller = controller
        self.ao_atualizar = ao_atualizar
        self.title("Cadastros")
        self.geometry("600x620")
        self.minsize(480, 500)
        self.resizable(True, True)
        self.grab_set()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.montar()

    def montar(self):
        self.montar_empresas()
        self.montar_bancos()
        ttk.Button(self, text="Fechar", command=self.destroy).grid(
            row=2, column=0, pady=(4, 12)
        )

    # ── Empresas ──────────────────────────────────────────────────────────────

    def montar_empresas(self):
        bloco = ttk.LabelFrame(self, text="Empresas")
        bloco.grid(row=0, column=0, sticky="nsew", padx=14, pady=(14, 6))
        bloco.columnconfigure(0, weight=1)
        bloco.rowconfigure(0, weight=1)

        self._lista_emp = ttk.Treeview(bloco, columns=("nome", "cnpj"), show="headings", height=6)
        self._lista_emp.heading("nome", text="Nome")
        self._lista_emp.heading("cnpj", text="CNPJ")
        self._lista_emp.column("nome", width=280, stretch=True)
        self._lista_emp.column("cnpj", width=160, stretch=True)
        self._lista_emp.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 0))

        scroll = ttk.Scrollbar(bloco, orient="vertical", command=self._lista_emp.yview)
        self._lista_emp.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns", pady=(6, 0))

        form = ttk.Frame(bloco)
        form.grid(row=1, column=0, columnspan=2, sticky="ew", padx=6, pady=6)
        form.columnconfigure(1, weight=2)
        form.columnconfigure(3, weight=1)

        ttk.Label(form, text="Nome").grid(row=0, column=0, sticky="w", padx=(0, 4), pady=4)
        self._nome_emp = ttk.Entry(form)
        self._nome_emp.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=4)

        ttk.Label(form, text="CNPJ").grid(row=0, column=2, sticky="w", padx=(0, 4), pady=4)
        self._cnpj_emp = ttk.Entry(form)
        self._cnpj_emp.grid(row=0, column=3, sticky="ew", pady=4)

        btns = ttk.Frame(bloco)
        btns.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 6))
        ttk.Button(btns, text="Adicionar", command=self.adicionar_empresa).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btns, text="Excluir selecionada", command=self.excluir_empresa).pack(side=tk.LEFT)

        self.carregar_empresas()

    def carregar_empresas(self):
        for item in self._lista_emp.get_children():
            self._lista_emp.delete(item)
        for emp in self.controller.listar_empresas():
            self._lista_emp.insert("", tk.END, iid=emp.id, values=(emp.nome, emp.cnpj_formatado))

    def adicionar_empresa(self):
        nome = self._nome_emp.get().strip()
        cnpj = self._cnpj_emp.get().strip()
        if not nome:
            messagebox.showwarning("Aviso", "Informe o nome da empresa.", parent=self)
            return
        try:
            self.controller.adicionar_empresa(nome, cnpj)
            self._nome_emp.delete(0, tk.END)
            self._cnpj_emp.delete(0, tk.END)
            self.carregar_empresas()
            self.ao_atualizar()
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)

    def excluir_empresa(self):
        selecionados = self._lista_emp.selection()
        if not selecionados:
            messagebox.showwarning("Aviso", "Selecione uma empresa.", parent=self)
            return
        if messagebox.askyesno("Confirmar", "Excluir empresa selecionada?", parent=self):
            self.controller.excluir_empresa(selecionados[0])
            self.carregar_empresas()
            self.ao_atualizar()

    # ── Bancos ────────────────────────────────────────────────────────────────

    def montar_bancos(self):
        bloco = ttk.LabelFrame(self, text="Bancos")
        bloco.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 6))
        bloco.columnconfigure(0, weight=1)
        bloco.rowconfigure(0, weight=1)

        self._lista_banco = ttk.Treeview(bloco, columns=("nome",), show="headings", height=5)
        self._lista_banco.heading("nome", text="Nome")
        self._lista_banco.column("nome", width=400, stretch=True)
        self._lista_banco.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 0))

        scroll = ttk.Scrollbar(bloco, orient="vertical", command=self._lista_banco.yview)
        self._lista_banco.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns", pady=(6, 0))

        form = ttk.Frame(bloco)
        form.grid(row=1, column=0, columnspan=2, sticky="ew", padx=6, pady=6)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Nome").grid(row=0, column=0, sticky="w", padx=(0, 4), pady=4)
        self._nome_banco = ttk.Entry(form)
        self._nome_banco.grid(row=0, column=1, sticky="ew", pady=4)

        btns = ttk.Frame(bloco)
        btns.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 6))
        ttk.Button(btns, text="Adicionar", command=self.adicionar_banco).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btns, text="Excluir selecionado", command=self.excluir_banco).pack(side=tk.LEFT)

        self.carregar_bancos()

    def carregar_bancos(self):
        for item in self._lista_banco.get_children():
            self._lista_banco.delete(item)
        for nome in self.controller.listar_bancos():
            self._lista_banco.insert("", tk.END, values=(nome,))

    def adicionar_banco(self):
        nome = self._nome_banco.get().strip()
        if not nome:
            messagebox.showwarning("Aviso", "Informe o nome do banco.", parent=self)
            return
        try:
            self.controller.adicionar_banco(nome)
            self._nome_banco.delete(0, tk.END)
            self.carregar_bancos()
            self.ao_atualizar()
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)

    def excluir_banco(self):
        selecionados = self._lista_banco.selection()
        if not selecionados:
            messagebox.showwarning("Aviso", "Selecione um banco.", parent=self)
            return
        nome = self._lista_banco.item(selecionados[0], "values")[0]
        if messagebox.askyesno("Confirmar", f"Excluir banco '{nome}'?", parent=self):
            self.controller.excluir_banco(nome)
            self.carregar_bancos()
            self.ao_atualizar()
