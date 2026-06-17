from decimal import Decimal


_TABELA_IOF = {
    1: Decimal("0.96"), 2: Decimal("0.93"), 3: Decimal("0.90"), 4: Decimal("0.86"), 5: Decimal("0.83"),
    6: Decimal("0.80"), 7: Decimal("0.76"), 8: Decimal("0.73"), 9: Decimal("0.70"), 10: Decimal("0.66"),
    11: Decimal("0.63"), 12: Decimal("0.60"), 13: Decimal("0.56"), 14: Decimal("0.53"), 15: Decimal("0.50"),
    16: Decimal("0.46"), 17: Decimal("0.43"), 18: Decimal("0.40"), 19: Decimal("0.36"), 20: Decimal("0.33"),
    21: Decimal("0.30"), 22: Decimal("0.26"), 23: Decimal("0.23"), 24: Decimal("0.20"), 25: Decimal("0.16"),
    26: Decimal("0.13"), 27: Decimal("0.10"), 28: Decimal("0.06"), 29: Decimal("0.03"), 30: Decimal("0.00")
}


def aliquota_iof(dias_corridos: int) -> Decimal:
    if dias_corridos <= 0:
        return Decimal("0")
    return _TABELA_IOF.get(dias_corridos, Decimal("0"))


def aliquota_ir(dias_corridos: int) -> Decimal:
    if dias_corridos <= 180:
        return Decimal("0.225")
    if dias_corridos <= 360:
        return Decimal("0.20")
    if dias_corridos <= 720:
        return Decimal("0.175")
    return Decimal("0.15")
