BEANSTALKD_HOST = "127.0.0.1"
BEANSTALKD_PORT = 11300
DOCKER_HOST = "127.0.0.1"
DOCKER_PORT = "4243"

SCANNERS_OUTPUT = {
    "pipeline-scanner:rhel7": [
        "image_scan_results.json"
    ],
    "misc-package-updates:rhel7": [
        "image_scan_results.json"
    ],
    "scanner-rpm-verify:rhel7": [
        "RPMVerify.json"
    ],
    "container-capabilities-scanner:rhel7": [
        "container_capabilities_scanner_results.json"
    ],
    "scanner-analytics-integration:rhel7": [
        "scanner-analytics-integration.json"
    ]
}
SCANNERS_RESULTFILE = {
    "pipeline-scanner": [
        "pipeline_scanner_results.json"],
    "misc-package-updates": [
        "misc_package_updates_scanner_results.json"],
    "scanner-rpm-verify": [
        "RPMVerify_scanner_results.json"],
    "container-capabilities-scanner": [
        "container-capabilities-results.json"
    ]

}
SCANNERS_STATUS_FILE = "scanners_status.json"

LOG_LEVEL = "DEBUG"
LOG_PATH = "scanning.log"

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
    }
)
