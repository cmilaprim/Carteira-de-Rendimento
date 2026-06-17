from app.views.aplicativo import AplicativoCarteira
from app.logger import Logger



if __name__ == "__main__":
    logger = Logger()
    app = AplicativoCarteira(logger=logger)
    app.mainloop()
