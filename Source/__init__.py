import os
import sys
import logging
import traceback


# Set loggers
root_logger = logging.getLogger()   # Get root logger
logging.basicConfig(level=logging.INFO)
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('numexpr').setLevel(logging.WARNING)
logging.getLogger('pyi_splash').setLevel(logging.WARNING)

# Catch Error (if frozen, not needed otherwise)
if getattr(sys, 'frozen', False):
    def except_hook(exc_type, exc_value, exc_tb):
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        root_logger.error(tb)

    sys.excepthook = except_hook

# Setup Path
PACKAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    root_logger.info('Running from PyInstaller bundle')
    PACKAGE_DIR = getattr(sys, '_MEIPASS', PACKAGE_DIR)
    os.chdir(PACKAGE_DIR)
else:
    root_logger.info('Running from source')

PATH_TO_DATA = os.path.join(PACKAGE_DIR, 'Data')
PATH_TO_CONFIG = os.path.join(PACKAGE_DIR, 'Config')
