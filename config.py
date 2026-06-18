import toml
import os
import base64
from pathlib import Path
import dotenv
from logging import Logger

class Configurator:
    '''Classe que gerencia as operações de configuração'''

    def __init__(self, logger:Logger) -> None:
        self.config:dict = None
        self.logger = logger
        self.logger.info("Inicializando configurador...")
        self.credenciais_carteira:dict       = self.load_env("CARTEIRA_AUTH")
        self.load()

    def load(self):
        '''Carrega configurações diretamente do arquivo "config.toml"'''
        try:
            with open(Path("config.toml"), "r") as config:
                self.config = toml.load(config)

        except FileNotFoundError as e:
            raise Exception(f"Erro. Arquivo de configurações 'config.toml' não encontrado no diretório {Path('config.toml').absolute()}") from e

    def load_env(self, env):
        '''Carrega credenciais de acesso de variáveis de ambiente'''
        dotenv.load_dotenv()
        credencial_codificada = os.getenv(env)
        
        if credencial_codificada:
            credencial_decodificada = base64.b64decode(credencial_codificada).decode('utf-8')
            usuario, senha = credencial_decodificada.split(":")
            return {'usuario': usuario, 'senha': senha}
        
        else:
            raise Exception(f"Erro. Credencial de acesso ao {env} não encontrada.")