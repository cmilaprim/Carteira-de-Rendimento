from datetime import date, datetime
from decimal import Decimal, InvalidOperation

def texto_para_decimal(texto: str) -> Decimal:
    limpo = str(texto).strip().replace("R$", "").replace(" ", "")
    if not limpo:
        raise ValueError("Valor vazio.")
    limpo = limpo.replace(".", "").replace(",", ".")
    try:
        return Decimal(limpo)
    except InvalidOperation as erro:
        raise ValueError(f"Valor invalido: {texto}") from erro


def texto_para_data(texto: str) -> date:
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except ValueError as erro:
        raise ValueError(f"Data invalida: {texto}. Use dd/mm/aaaa.") from erro
