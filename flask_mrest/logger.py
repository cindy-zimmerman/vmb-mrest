import logging
from logging.handlers import RotatingFileHandler
import os
from graypy import GELFHandler


def setupLogHandlers(fname, formatter=None, log_dir='./', use_gelf=False, **kwargs):
    """
    Adapted from CoinapultCommon.util.setupLogHandlers

    Create a RotatingFileHandler to be used by a logger, and possibly a
    GELFHandler.

    By default the RotatingFileHandler stores 100 MB before starting a new
    log file and the last 10 log files are kept. The default formatter shows
    the logging level, current time, the function that created the log entry,
    and the specified message.

    :param str fname: path to the filename where logs will be written to
    :param logging.Formatter formatter: a custom formatter for this logger
    :param str log_dir: The directory the log file belongs in
    :param bool use_gelf: Use GELF or not
    :param kwargs: custom parameters for the RotatingFileHandler
    :rtype: tuple
    """
    if formatter is None:
        formatter = logging.Formatter('%(levelname)s [%(asctime)s] %(funcName)s: %(message)s')

    opts = {'maxBytes': 100 * 1024 * 1024, 'backupCount': 10}
    opts.update(kwargs)
    handler = RotatingFileHandler(os.path.join(log_dir, fname), **opts)
    handler.setFormatter(formatter)

    handlers = (handler, )
    if use_gelf:
        gelf_handler = GELFHandler(**use_gelf)
        gelf_handler.setLevel(logging.INFO)  # Ignore DEBUG messages.
        handlers += (gelf_handler, )

    return handlers
