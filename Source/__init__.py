import os
import sys
import logging

root_logger = logging.getLogger()   # Get root logger
logging.basicConfig(level=logging.INFO)

# Setup Path
if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
    root_logger.info('Running in bundled mode')
    package_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    os.chdir(package_dir)
else:
    root_logger.info('Running from source')
    package_dir = os.path.dirname(__file__)
PATH_TO_DATA = os.path.join(package_dir, 'Data')
