from sqlalchemy import Engine, text


class RepositorioBancos:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def listar(self) -> list[str]:
        with self.engine.connect() as conn:
            resultado = conn.execute(text("SELECT nome FROM d_banco ORDER BY nome"))
            return [linha.nome for linha in resultado]

    def obter_id_por_nome(self, nome: str) -> int | None:
        if not nome:
            return None
        with self.engine.connect() as conn:
            linha = conn.execute(
                text("SELECT id FROM d_banco WHERE nome = :nome"),
                {"nome": nome},
            ).fetchone()
        return linha.id if linha else None

    def adicionar(self, nome: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("INSERT INTO d_banco (nome) VALUES (:nome)"), {"nome": nome})

    def excluir(self, nome: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM d_banco WHERE nome = :nome"), {"nome": nome})
