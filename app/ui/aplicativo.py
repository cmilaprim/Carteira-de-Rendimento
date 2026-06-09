from __future__ import annotations

import logging
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

try:
    from tkcalendar import DateEntry
except Exception: 
    DateEntry = None

from app.controllers.carteira_controller import CarteiraController, DadosAplicacaoFormulario
from app.servicos.abridor_arquivo import abrir_arquivo

logger = logging.getLogger(__name__)


class AplicativoCarteira(tk.Tk):
    def __init__(self, controller: CarteiraController | None = None) -> None:
        super().__init__()
        logger.info("Iniciando interface da carteira.")
        self.title("Carteira de Aplicacoes - CDI/Selic")
        self.geometry("980x620")
        self.controller = controller or CarteiraController()
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
        opcoes_indexadores = self.controller.indexadores()
        self.indexador = ttk.Combobox(formulario, values=opcoes_indexadores, state="readonly", width=16)
        self.indexador.set(opcoes_indexadores[0])
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

        rodape = ttk.LabelFrame(self, text="Data do demonstrativo")
        rodape.pack(fill=tk.X, padx=10, pady=8)
        self.data_saldo = self.entrada_data(rodape, "Saldo em", 0, 0)

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
            self.controller.salvar_aplicacao(DadosAplicacaoFormulario(
                nome_produto=self.nome_produto.get(),
                numero_controle=self.numero_controle.get(),
                numero_nota=self.numero_nota.get(),
                valor_aplicado=self.valor_aplicado.get(),
                data_emissao=self.data_emissao.get(),
                data_vencimento=self.data_vencimento.get(),
                indexador=self.indexador.get(),
                percentual_indexador=self.percentual_indexador.get(),
                taxa_prefixada=self.taxa_prefixada.get()))
            
            self.limpar_formulario()
            self.carregar_lista()
            messagebox.showinfo("Sucesso", "Aplicacao salva com sucesso.")
        except Exception as erro:
            logger.exception("Erro ao salvar aplicacao.")
            messagebox.showerror("Erro", str(erro))
    
    
    def carregar_lista(self) -> None:
        for item in self.lista.get_children():
            self.lista.delete(item)
        linhas = self.controller.listar_aplicacoes()
        logger.debug("Carregando lista de aplicacoes na tela: total=%d", len(linhas))
        for linha in linhas:
            self.lista.insert("", tk.END, iid=linha.id, values=(
                linha.produto,
                linha.controle,
                linha.emissao,
                linha.vencimento,
                linha.taxa,
                linha.valor
            ))

    def limpar_formulario(self) -> None:
        for entrada in [self.nome_produto, self.numero_controle, self.numero_nota, self.valor_aplicado, self.taxa_prefixada]:
            entrada.delete(0, tk.END)
        self.percentual_indexador.delete(0, tk.END)
        self.percentual_indexador.insert(0, "100")
        self.indexador.set(self.controller.indexadores()[0])

    def confirmar_exclusao(self) -> None:
        if messagebox.askyesno("Confirmar exclusao", "Deseja realmente excluir a aplicacao selecionada?"):
            self.excluir_selecionada()

    def excluir_selecionada(self) -> None:
        selecionados = self.lista.selection()
        if not selecionados:
            logger.warning("Exclusao solicitada sem aplicacao selecionada.")
            messagebox.showwarning("Aviso", "Selecione uma aplicacao.")
            return
        self.controller.excluir_aplicacao(selecionados[0])
        self.carregar_lista()

    def atualizar_taxas(self) -> None:
        try:
            mensagem = self.controller.atualizar_taxas(self.data_saldo.get())
            messagebox.showinfo("Info", mensagem)
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

            caminho = self.controller.gerar_documento_aplicacao(selecionados[0], self.data_saldo.get())
            abrir_arquivo(caminho)
            messagebox.showinfo("Sucesso", f"Documento da aplicacao gerado:\n{caminho}")
        except Exception as erro:
            logger.exception("Erro ao gerar demonstrativo.")
            messagebox.showerror("Erro", str(erro))


def iniciar_aplicativo() -> None:
    app = AplicativoCarteira()
    app.mainloop()
