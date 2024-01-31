from logger import LoggerManager
from ui import VERSION

logger = LoggerManager.get_logger()
try:

    from ui.mainui import MainUI


    def main():
        logger.debug("BOM Diff Tool version %s" % VERSION)
        ui = MainUI()

        ui.run_tk()
        logger.debug("UI closed normally")


    if __name__ == '__main__':
        main()
except BaseException as e:
    logger.error(str(e), exc_info=True)
    raise
finally:
    logger.debug("Exiting")
