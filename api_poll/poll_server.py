#!/usr/bin/python

"""
This module contains the worker that handles the scanning.
"""
import json
import logging

import yaml
from jinja2 import Environment, FileSystemLoader

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
        project["image_under_test"] = job.get("image_under_test")
        project["analytics_server"] = job.get("analytics_server")
        project["git-sha"] = job.get("git-sha")
        project["git-url"] = job.get("git-url")

        try:
            env = Environment(loader=FileSystemLoader(
                './'), trim_blocks=True, lstrip_blocks=True)
            template = env.get_template("api-poll-server.yml")
            job_details = template.render(project)
        except Exception as e:
            print("Error template is not updated: %s" % str(e))

        try:
             generated_filename = "poll_server_generated.yaml"
             with open(generated_filename, 'w') as outfile:
                 outfile.write(job_details)
                 outfile.flush()
        except Exception as e:
            print("Error job_details could not be updated %s" % str(e))

if __name__ == '__main__':

    log.load_logger()
    logger = logging.getLogger("poll-server")
    PollServer(logger, sub='poll_server', pub='failed_polling').run()
