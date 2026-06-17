import logging
from datetime import datetime
from pathlib import Path
from os import mkdir
import inspect
import glob
import os
from datetime import timedelta



def limpa_logs(criterio="TEMPO"):
    max_tempo = 7
    max_quantidade = 14
    try:
        files = glob.glob("logs/*.log")
        if criterio == "TEMPO":
            antigos = [f for f in files if datetime.fromtimestamp(os.path.getmtime(f)) < (datetime.now() - timedelta(days=max_tempo))]
            for f in antigos:
                os.remove(Path(f))
        if criterio == "QUANTIDADE":
            files.sort(key=lambda x: os.path.getmtime(x))
            while len(files) > max_quantidade:
                os.remove(Path(files.pop(0)))
    except Exception:
        pass

def cria_logger(nome_arquivo=None, limpar=True):

    if limpar:
        limpa_logs()

    timestamp = datetime.now().strftime("%d-%m-%Y %H%M%S")

    logger = logging.getLogger()
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s | %(filename)s | %(funcName)s | %(message)s', datefmt="%d/%m/%Y %H:%M:%S")

    # Printa no stdout
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    def cria_pasta_logs():
        '''Se a pasta logs ainda não tiver sido criada, cria'''
        if not Path("logs").exists():
            logger.info("A pasta de logs ainda não foi criada. Criando...")
            mkdir(Path("logs"))

    cria_pasta_logs()

    # Salva logs em arquivos
    if nome_arquivo:
        filename = f"logs/Log-{timestamp}-{nome_arquivo}.log"
    else:
        filename = f"logs/Log-{timestamp}.log"

    output_handler = logging.FileHandler(filename, encoding='utf-8')
    output_handler.setFormatter(formatter)
    output_handler.setLevel(logging.INFO)
    logger.addHandler(output_handler)

    return logger

class Logger:
    def __init__(self, nome_arquivo=None):
        self.logger = cria_logger(nome_arquivo=nome_arquivo)

    def info(self, msg):
        self.logger.info(msg, stacklevel=2)

    def warning(self, msg):
        self.logger.warning(msg, stacklevel=2)

    def error(self, msg):
        self.logger.error(msg, stacklevel=2)

    def exception(self, msg):
        self.logger.exception(msg, stacklevel=2)

    def debug(self, msg):
        self.logger.debug(msg, stacklevel=2)