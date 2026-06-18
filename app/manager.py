import logging
import urllib.parse
from sqlalchemy import Engine, create_engine
from config import Configurator

class Manager:
    def __init__(self, configurator: Configurator, logger):
        self.logger: logging.Logger = logger
        self.configurator = configurator
        self.load_config()

    def load_config(self):
        self.logger.info("Carregando configuracao de conexao com o banco de dados...")

        config = self.configurator.config
        self.servidor_carteira = config["conexoes"]["servidor"]
        self.banco_carteira = config["conexoes"]["banco"]
        self.usuario_carteira = self.configurator.credenciais_carteira["usuario"]
        self.senha_carteira = self.configurator.credenciais_carteira["senha"]

    def conecta_carteira(self) -> Engine:
        engine = create_engine(url=f"postgresql+psycopg2://{self.usuario_carteira}:{self.senha_carteira}@{self.servidor_carteira}/{self.banco_carteira}", client_encoding="utf8", connect_args={"sslmode": "require", "channel_binding": "require"})
        self.logger.info("Conexao com o banco de dados da carteira estabelecida com sucesso.")
        return engine
    
