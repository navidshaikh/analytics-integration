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

GET_REPO_SCRIPT = "./get_repo_details_from_image.sh"


def run_saasherder(repository):
    """
    Run saas herder parser on given repository and find out
    git-url and git-sha for image under test.
    Returns None if failed to parse using saasherder
    Returns dict = {"git-url": GIT-URL,
                    "git-sha": GIT-SHA,
                    "image-tag": IMAGE-TAG}
                    on success
    """
    cmd = "cd {} && {} {}".format(
        SAASHERDER_PARSER_DIR, GET_REPO_SCRIPT, repository)
    logger = logging.getLogger("weeklyscan")
    logger.info("Checking repo: {} via saasherder".format(repository))
    try:
        output = run_cmd(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        msg = "Error occurred processing saasherder for {}".format(repository)
        msg = msg + "\n{}".format(e)
        logger.warning(msg)
        return None
    else:
        # lets parse stdout
        try:
            # last 3 lines has git-url, git-sha and image-tag
            # we want -1, -2 and -3 indexed elements
            lines = output.strip().split("\n")[-3:]
        except Exception as e:
            msg = "Error parsing saasherder output. {}".format(e)
            msg = msg + "Output: " + output
            logger.warning(msg)
            return None

        # def f(x): return {x.split("=")[0], x.split("=")[-1]}
        def f(x): return {x.split("=")[0].strip(): x.split("=")[-1].strip()}
        values = {}
        try:
            [values.update(f(x)) for x in lines]
        except Exception as e:
            logger.warning("Error parsing stdout of saasherder.".format(
                repository))
            return None

        if not values.get("image-tag", False) or not values.get(
                "git-url", False) or not values.get(
                "git-sha", False):
            # case where either of the needed value is not found
            logger.warning(
                "Could not locate repo via saas herder. Values: {}".format(
                    values))
            return None
        # case where saasherder exported desired results
        logger.warning("Located repo {} via saasherder. Values: {}".format(
            values))
        return values
