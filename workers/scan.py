#!/usr/bin/python

"""
This module contains the worker that handles the scanning.
"""
import json
import logging

from scanning.lib import log
from scanning.lib.command import run_cmd
from scanning.scanners.runner import ScannerRunner
from base import BaseWorker


class ScanWorker(BaseWorker):
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

        scan_runner_obj = ScannerRunner(self.job)
        status, scanners_data = scan_runner_obj.scan()
        if not status:
            self.logger.warning(
                "Failed to run scanners on image under test, moving on!")
            self.logger.warning("Job data %s", str(self.job))

        else:
            self.logger.debug(str(scanners_data))

        # Remove the msg and logs from the job_info as they are not
        # needed now
        scanners_data.pop("msg", None)
        scanners_data.pop("logs", None)
        scanners_data.pop("scan_results", None)

        # if weekly scan, push the job for notification
        if self.job.get("weekly"):
            scanners_data["action"] = "notify"
            self.queue.put(json.dumps(scanners_data), 'master_tube')
            self.logger.debug(
                str.format(
                    "Weekly scan for {project} is complete.",
                    project=self.job.get("namespace")
                )
            )
        else:
            # now scanning is complete, relay job for delivery
            # all other details about job stays same
            # change the action
            scanners_data["action"] = "notify"
            # Put the job details on central tube
            self.queue.put(json.dumps(scanners_data), 'master_tube')
            self.logger.debug("Put job for delivery on master tube")

        # run the image and volume cleanup
        self.clean_up()

    def clean_up(self):
        """
        Clean up the system after scan is done.
        This cleans up any unused/dangling images and volumes.
        This is using `docker image prune -f` and `docker volume prune -f`
        commands under the hood. The `-f` option will help avoid the prompt
        for confirmation.
        """
        command = "docker rmi -f `docker images -f dangling=true -q`"
        self.logger.debug("Removing unused/dangling images..")
        try:
            run_cmd(command, shell=True)
        except Exception as e:
            self.logger.critical("Failing to remove dangling images.")
            self.logger.critical("Error: %s", str(e))
        else:
            self.logger.debug("Cleaned unsued images post scan.")

        command = "docker volume rm `docker volume ls -f dangling=true -q`"
        self.logger.debug("Removing unused/dangling volumes..")
        try:
            run_cmd(command, shell=True)
        except Exception as e:
            self.logger.critical("Failing to remove dangling volume.")
            self.logger.critical("Error: %s", str(e))
        else:
            self.logger.debug("Cleaned unsued volumes post scan.")


if __name__ == '__main__':

    log.load_logger()
    logger = logging.getLogger("scan-worker")
    ScanWorker(logger, sub='start_scan', pub='failed_scan').run()
