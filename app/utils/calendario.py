from datetime import date, timedelta

def intervalo_datas(inicio: date, fim: date):
    atual = inicio
    while atual <= fim:
        yield atual
        atual += timedelta(days=1)


def eh_dia_util(data: date) -> bool:
    return data.weekday() < 5
