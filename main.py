from app.logger import cria_logger
from app.views.aplicativo import AplicativoCarteira

if __name__ == "__main__":
    logger = cria_logger(nome_arquivo="carteira")
    app = AplicativoCarteira(logger=logger)
    app.mainloop()
