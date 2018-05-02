#!/usr/bin/python

"""
This module contains the worker that handles the scanning.
"""
import json
import logging

from base import BaseWorker


class PollServer(BaseWorker):
    """Scan Base worker."""
    NAME = 'Scanner worker'

    def __init__(self, logger=None, sub=None, pub=None):
        super(ScanWorker, self).__init__(logger=logger, sub=sub, pub=pub)

    def handle_job(self, job):
        """
        Handle jobs in scan tube.

        This scans the images for the job requests in start_scan tube.
        this calls the ScannerRunner for performing the scan work
        """
        self.job = job
        image_under_test = job.get("image_under_test")
        analytics_server = job.get("analytics_server")
        git-sha = job.get("git-sha")
        git-url = job.get("git-url")


if __name__ == '__main__':

    log.load_logger()
    logger = logging.getLogger("poll-server")
    ScanWorker(logger, sub='poll_server', pub='failed_polling').run()
