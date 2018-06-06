#!/usr/bin/env python

import json
import logging
import sys

from scanning.lib import settings
from scanning.lib.log import load_logger
from scanning.vendors import beanstalkc


def send_scan_data(analytics_server, image_under_test, git_url,
                   git_sha, logs_dir, scan_gitpath, gemini_report):
    load_logger()
    logger = logging.getLogger('poll-job')
    conn = beanstalkc.Connection(
        host=settings.BEANSTALKD_HOST,
        port=settings.BEANSTALKD_PORT)

    logger.info("Getting scan details from jenkins")
    scan_details = {}
    scan_details["action"] = "start_scan"
    scan_details["weekly"] = True
    scan_details["analytics_server"] = analytics_server
    scan_details["image_under_test"] = image_under_test
    scan_details["git-url"] = git_url
    scan_details["git-sha"] = git_sha

    scan_details["gemini_report"] = True \
        if (gemini_report == "True") else False

    scan_details["notify_email"] = settings.NOTIFY_EMAILS
    scan_details["logs_dir"] = logs_dir
    scan_details["scan_gitpath"] = scan_gitpath

    logger.info("Pushing scan details to the tube")
    conn.use("master_tube")
    conn.put(json.dumps(scan_details))
    print("scan details are pushed to master tube")


if __name__ == '__main__':
    send_scan_data(sys.argv[1], sys.argv[2], sys.argv[3],
                   sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
