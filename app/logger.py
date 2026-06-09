import logging
from datetime import datetime, timedelta
from pathlib import Path


def limpa_logs(criterio="QUANTIDADE"):
    max_tempo = 7
    max_quantidade = 50
    pasta_logs = Path("logs")

    try:
        if not pasta_logs.exists():
            return

        arquivos = list(pasta_logs.glob("*.log"))
        if criterio == "TEMPO":
            limite = datetime.now() - timedelta(days=max_tempo)
            arquivos_para_remover = filter(lambda arquivo: datetime.fromtimestamp(arquivo.stat().st_mtime) < limite, arquivos)
            for arquivo in arquivos_para_remover:
                arquivo.unlink()

        if criterio == "QUANTIDADE":
            arquivos.sort(key=lambda arquivo: arquivo.stat().st_mtime)
            while len(arquivos) > max_quantidade:
                arquivos.pop(0).unlink()
    except Exception as erro:
        log = cria_logger(nome_arquivo="logger", limpar=False)
        log.exception("Falha ao apagar logs.")
        raise Exception("Falha ao apagar logs.") from erro


def cria_logger(nome_arquivo=None, limpar=True):
    if limpar:
        limpa_logs()

    timestamp = datetime.now().strftime("%d-%m-%Y %H%M%S")
    pasta_logs = Path("logs")
    pasta_logs.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(levelname)s] %(asctime)s | %(filename)s | %(funcName)s | %(message)s", datefmt="%d/%m/%Y %H:%M:%S")

    handler_console = logging.StreamHandler()
    handler_console.setFormatter(formatter)
    handler_console.setLevel(logging.DEBUG)
    logger.addHandler(handler_console)

    if nome_arquivo:
        caminho_log = pasta_logs / f"Log-{timestamp}-{nome_arquivo}.log"
    else:
        caminho_log = pasta_logs / f"Log-{timestamp}.log"

    handler_arquivo = logging.FileHandler(caminho_log, encoding="utf-8")
    handler_arquivo.setFormatter(formatter)
    handler_arquivo.setLevel(logging.DEBUG)
    logger.addHandler(handler_arquivo)

    logger.info("Logger iniciado: %s", caminho_log)
    return logger
