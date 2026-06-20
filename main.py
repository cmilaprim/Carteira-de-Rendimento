from app.views.aplicativo import AplicativoCarteira
from app.controllers.carteira_controller import CarteiraController
from app.logger import Logger
from config import Configurator
from app.manager import Manager


if __name__ == "__main__":
    logger = Logger()
    configurator = Configurator(logger=logger)
    engine = Manager(configurator=configurator, logger=logger).conecta_carteira()
    controller = CarteiraController(logger=logger, engine=engine)
    app = AplicativoCarteira(logger=logger, controller=controller)
    app.mainloop()
