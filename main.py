from app.logger import cria_logger
from app.ui.aplicativo import iniciar_aplicativo


if __name__ == "__main__":
    cria_logger(nome_arquivo="Carteira")
    iniciar_aplicativo()
