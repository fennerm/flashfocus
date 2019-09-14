import logging
import os
import sys

from flashfocus.color import green, red
from flashfocus.errors import UnsupportedWM

# Set LOGLEVEL environment variable to DEBUG or WARNING to change logging verbosity.
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"), format="%(levelname)s: %(message)s")

if sys.stderr.isatty():
    # Colored logging categories
    logging.addLevelName(logging.WARNING, red(logging.getLevelName(logging.WARNING)))
    logging.addLevelName(logging.ERROR, red(logging.getLevelName(logging.ERROR)))
    logging.addLevelName(logging.INFO, green(logging.getLevelName(logging.INFO)))


# Check if the user is running a supported WM
try:
    import flashfocus.compat  # noqa F401
except UnsupportedWM as error:
    logging.error(str(error))
    sys.exit("Unrecoverable error, exiting...")
