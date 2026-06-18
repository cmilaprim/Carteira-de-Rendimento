from uuid import uuid4
from app.utils.formatadores import cnpj as formatar_cnpj


class Empresa:
    def __init__(self, nome: str, cnpj: str, id: str | None = None) -> None:
        self.id = id or str(uuid4())
        self.nome = nome.strip()
        self.cnpj = cnpj.strip()

    @property
    def cnpj_formatado(self) -> str:
        return formatar_cnpj(self.cnpj) if self.cnpj else ""

    @property
    def rotulo(self) -> str:
        return f"{self.nome} ({self.cnpj_formatado})" if self.cnpj else self.nome
