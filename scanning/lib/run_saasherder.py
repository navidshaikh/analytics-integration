#!/usr/bin/env python2

"""
This module is aimed at running saasherder parser to find
latest tag, git-url and image tag for given container repository.
"""

import subprocess
import logging

from command import run_cmd


SAASHERDER_PARSER_DIR = \
    "/opt/scanning/saasherder_parser/"

GET_IMAGES_SCRIPT = "get-images.sh"
IMAGES_FILE = "/opt/scanning/saasherder_parser/images.txt"


def run_saasherder():
    """
    """
    cmd = "cd {} & bash {}".format(SAASHERDER_PARSER_DIR, GET_IMAGES_SCRIPT)

    logger = logging.getLogger("weeklyscan")
    try:
        run_cmd(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        msg = "Error occurred processing images using saasherder."
        msg = msg + "\n{}".format(e)
        logger.warning(msg)
        return None
    else:
        return IMAGES_FILE
