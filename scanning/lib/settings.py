# import configs from root directory of repository
from config import *

BEANSTALKD_HOST = "127.0.0.1"
BEANSTALKD_PORT = 11300
DOCKER_HOST = "127.0.0.1"
DOCKER_PORT = "4243"

SCANNERS_STATUS_FILE = "scanners_status.json"

LOG_LEVEL = "DEBUG"
LOG_PATH = "/tmp/scanning.log"

LOGGING = dict(
    version=1,
    level=LOG_LEVEL,
    formatters=dict(
        bare={
            "format": ('[%(asctime)s] %(name)s p%(process)s %(lineno)d '
                       '%(levelname)s - %(message)s')
        },
    ),
    handlers=dict(
        console={
            "class": "logging.StreamHandler",
            "formatter": "bare",
            "level": LOG_LEVEL,
        },
        log_to_file={
            'level': LOG_LEVEL,
            'class': 'logging.FileHandler',
            'filename': LOG_PATH,
            'mode': 'a+',
            'formatter': 'bare',
        }
    ),
    loggers={
        'scan-worker': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console", "log_to_file"],
        },
        'dispatcher': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console", "log_to_file"],
        },
        'mail-service': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console", "log_to_file"],
        },
        'console': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console"]

        },
        'weeklyscan': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console", "log_to_file"],

        },
        'poll-job': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console", "log_to_file"],

        },
    }
)
