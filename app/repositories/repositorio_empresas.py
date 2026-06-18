import json
from pathlib import Path
from typing import Iterable
from app.models.empresa import Empresa


class RepositorioEmpresas:
    def __init__(self) -> None:
        self.caminho = Path("data/empresas.json")
        self.caminho.parent.mkdir(parents=True, exist_ok=True)

    def listar(self) -> list[Empresa]:
        if not self.caminho.exists() or self.caminho.stat().st_size == 0:
            return []
        with self.caminho.open("r", encoding="utf-8") as f:
            dados = json.load(f)
        return [self._para_empresa(d) for d in dados]

    def salvar_todos(self, empresas: Iterable[Empresa]) -> None:
        dados = [self._para_dict(e) for e in empresas]
        tmp = self.caminho.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        tmp.replace(self.caminho)

    def adicionar(self, empresa: Empresa) -> None:
        empresas = self.listar()
        empresas.append(empresa)
        self.salvar_todos(empresas)

    def excluir(self, empresa_id: str) -> None:
        self.salvar_todos(e for e in self.listar() if e.id != empresa_id)

    def obter(self, empresa_id: str) -> Empresa:
        for e in self.listar():
            if e.id == empresa_id:
                return e
        raise KeyError("Empresa nao encontrada.")

    def _para_dict(self, empresa: Empresa) -> dict:
        return {"id": empresa.id, "nome": empresa.nome, "cnpj": empresa.cnpj}

    def _para_empresa(self, dados: dict) -> Empresa:
        
        return Empresa(id=dados["id"], nome=dados["nome"], cnpj=dados["cnpj"])
