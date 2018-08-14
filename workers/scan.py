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
        scan_runner_obj = ScannerRunner(job)
        status, scanners_data = scan_runner_obj.scan()
        if not status:
            self.logger.warning(
                "Failed to run scanners on image under test, moving on!")
            self.logger.warning("Job data %s", str(job))
            self.logger.warning("Not sending job to poll_server tube.")
            # run the image and volume cleanup
            self.clean_up()
            return
        else:
            self.logger.debug("Scan is completed. Result {}".format(
                scanners_data))

        # Remove the msg and logs from the job_info as they are not
        # needed now
        scanners_data.pop("msg", None)
        scanners_data.pop("logs", None)

        # presence of `gemini_report` hints if polling is done or not
        # if its present, it means, the scan job is coming after polling
        # and report api call needs to be made

        # if "gemini_report" is absent in job, it means, the job needs
        # to be put for polling
        if "gemini_report" not in job:
            # copy the job in another var to avoid action var overwrite
            poll_job = job.copy()
            # here there is another clone of job params loaded on beanstalkd
            self.put_job_for_polling(poll_job)

        scanners_data["action"] = "notify"
        self.queue.put(json.dumps(scanners_data), 'master_tube')

        # remove the image and volume cleanup
        self.clean_up()

    def put_job_for_polling(self, job):
        """
        Put job on polling tube
        """
        poll_tube = "poll_server"
        self.queue.put(json.dumps(job), tube=poll_tube)
        self.logger.info("Queued job at {} tube.".format(poll_tube))

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
        except Exception:
            pass
        else:
            self.logger.debug("Cleaned unsued images post scan.")

        command = "docker volume rm `docker volume ls -f dangling=true -q`"
        self.logger.debug("Removing unused/dangling volumes..")
        try:
            run_cmd(command, shell=True)
        except Exception:
            pass
        else:
            self.logger.debug("Cleaned unsued volumes post scan.")


if __name__ == '__main__':

    log.load_logger()
    logger = logging.getLogger("scan-worker")
    ScanWorker(logger, sub='start_scan', pub='failed_scan').run()
