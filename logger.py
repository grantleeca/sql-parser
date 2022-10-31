import datetime
import json
import logging
import os.path

from logging.config import dictConfig

_log_name = __name__
_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(levelname)s %(asctime)s %(filename)s %(lineno)-6s: %(message)s",
            "datefmt": "%H:%M:%S"
        },
        "single_line": {
            "format": "%(levelname)-8s %(asctime)-20s %(filename)-16s %(lineno)-6s %(funcName)-20s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S %A"
        },
        "multiline": {
            "format": "Level:\t\t%(levelname)s\n"
                      "Time:\t\t%(asctime)s\n"
                      "Process:\t%(process)d\n"
                      "Thread:\t\t%(threadName)s\n"
                      "Logger:\t\t%(name)s\n"
                      "Module:\t\t%(module)s\n"
                      "File:\t\t%(filename)s\n"
                      "Line:\t\t%(lineno)s\n"
                      "Function:\t%(funcName)s\n"
                      "Message:\t%(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "console",
            "stream": "ext://sys.stderr"
        },
        "info_file_handler": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "single_line",
            "delay": True
        },
        "error_file_handler": {
            "class": "logging.FileHandler",
            "level": "WARN",
            "formatter": "multiline",
            "delay": True
        },
    },
    "loggers": {
        _log_name: {
            "level": "INFO",
            "handlers": ["console", "info_file_handler", "error_file_handler"]
        }
    }
}


def setup_logger(config=None, app_name=None, level=None, log_path=None, mail=None, **kwargs):
    if config:
        return dictConfig(config)

    if log_path is None:
        log_path = 'log'

    if not os.path.exists(log_path):
        os.mkdir(log_path)

    filename = app_name if app_name else _log_name
    today = datetime.datetime.today().strftime('%Y-%m-%d')

    _config['handlers']['info_file_handler']['filename'] = os.path.join(log_path, f"{filename}_info_{today}.log")
    _config['handlers']['error_file_handler']['filename'] = os.path.join(log_path, f"{filename}_error_{today}.log")

    if mail:
        mail.update({
            "class": "logging.handlers.SMTPHandler",
            "level": "ERROR",
            "formatter": "multiline",
        })

        _config['handlers']['smtp_handler'] = mail
        _config['loggers'][_log_name]['handlers'].append("smtp_handler")

    if level:
        _config['loggers'][_log_name]['level'] = level

    dictConfig(_config)
    return logging.getLogger(_log_name)


class Trace(object):
    def __call__(self, func):  # Tracking function calls
        def wrapped_function(*args, **kwargs):
            logging.getLogger(_log_name).debug(func.__name__ + " starts executing")
            return func(*args, **kwargs)

        return wrapped_function


def main():
    with open('config.json', 'rt') as fp:
        cfg = json.load(fp)

    logger = setup_logger(**cfg['logger'])
    logger.debug("This is a DEBUG log information.")
    logger.info("This is a normal log information.")
    logger.warning("This is a warning log information.")
    logger.error("This is a error log information.")


if __name__ == '__main__':
    main()
