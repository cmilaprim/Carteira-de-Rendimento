from datetime import date
from decimal import Decimal, ROUND_HALF_UP


CENTAVOS = Decimal("0.01")


def arredondar_centavos(valor: Decimal) -> Decimal:
    return Decimal(valor).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def moeda(valor: Decimal | float | int) -> str:
    valor_decimal = arredondar_centavos(Decimal(str(valor)))
    texto = f"{valor_decimal:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def moeda_com_simbolo(valor: Decimal | float | int) -> str:
    return f"R$ {moeda(valor)}"


def percentual(valor: Decimal | float | int, casas: int = 2) -> str:
    valor_decimal = Decimal(str(valor)).quantize(Decimal("1." + "0" * casas), rounding=ROUND_HALF_UP)
    return f"{valor_decimal:,.{casas}f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def data_br(data: date) -> str:
    return data.strftime("%d/%m/%Y")


def data_curta(data: date) -> str:
    return data.strftime("%d/%m/%y")
