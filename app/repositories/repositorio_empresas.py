from sqlalchemy import Engine, text
from app.models.empresa import Empresa


class RepositorioEmpresas:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def listar(self) -> list[Empresa]:
        query = text("select id, nome, cnpj from d_empresa order by nome")
        with self.engine.connect() as conn:
            resultado = conn.execute(query)
            empresas = []
            for linha in resultado:
                empresas.append(Empresa(id=str(linha.id), nome=linha.nome, cnpj=linha.cnpj or ""))
            return empresas

    def adicionar(self, empresa: Empresa) -> None:
        query = text("insert into d_empresa (nome, cnpj) VALUES (:nome, :cnpj) RETURNING id")
        with self.engine.begin() as conn:
            linha = conn.execute(query, {"nome": empresa.nome, "cnpj": empresa.cnpj}).fetchone()
            empresa.id = str(linha.id)

    def excluir(self, empresa_id: int) -> None:
        query = text("delete from d_empresa where id = :id")
        with self.engine.begin() as conn:
            conn.execute(query, {"id": empresa_id})

    def obter(self, empresa_id: int) -> Empresa:
        query = text("select id, nome, cnpj from d_empresa where id = :id")
        with self.engine.connect() as conn:
            linha = conn.execute(query, {"id": empresa_id}).fetchone()
        if linha is None:
            raise KeyError("Empresa nao encontrada.")
        return Empresa(id=str(linha.id), nome=linha.nome, cnpj=linha.cnpj or "")
