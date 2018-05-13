#!/usr/bin/python
"""
Scanner Runner.

This module invokes all registered scanners and orchestrates the processing.
"""

import json
import logging
import os
import sys

import docker
from scanning.lib import settings
from scanning.lib.log import load_logger
from scanning.scanners.analytics_integration import AnalyticsIntegration
from scanning.scanners.base import Scanner
from scanning.scanners.container_capabilities import ContainerCapabilities
from scanning.scanners.misc_package_updates import MiscPackageUpdates
from scanning.scanners.pipeline_scanner import PipelineScanner
from scanning.scanners.rpm_verify import ScannerRPMVerify


class ScannerRunner(Scanner):
    """
    Scanner Handler orchestration.

    Scanner runner class handling basic operation and orchestration of
    multiple scanner handlers
    """

    def __init__(self, job):
        """Initialize runner."""
        # initializing logger
        load_logger()
        self.logger = logging.getLogger('scan-worker')
        self.docker_conn = self.docker_client()
        if not self.docker_conn:
            self.logger.fatal("Not able to connect to docker daemon.")
            sys.exit(1)
        self.job = job

        # register all scanners
        self.scanners = [
            PipelineScanner,
            AnalyticsIntegration,
            ScannerRPMVerify,
            MiscPackageUpdates,
            ContainerCapabilities
        ]

    def docker_client(self, base_url="unix:///var/run/docker.sock"):
        """
        returns Docker client object on success else False on failure
        """
        try:
            conn = docker.Client(base_url=base_url)
        except Exception as e:
            self.logger.fatal(
                "Failed to connect to Docker daemon. {}".format(e),
                exc_info=True)
            return False
        else:
            return conn

    def remove_image(self, image):
        """
        Remove the image under test using docker client
        """
        self.logger.info("Removing image {}".format(image))
        self.docker_conn.remove_image(image=self.image, force=True)

    def pull_image(self, image):
        """
        Pull image under test on scanner host machine
        """
        self.logger.info("Pulling image {}".format(image))
        pull_data = self.docker_conn.pull(repository=image)

        if 'error' in pull_data:
            self.logger.fatal("Error pulling requested image {}: {}".format(
                image, pull_data
            ))
            return False

        self.logger.info("Pulled image {}".format(image))
        return True

    def export_scanners_status(self, status, status_file_path):
        """
        Export status of scanners execution for build in process.
        """
        try:
            fin = open(status_file_path, "w")
            json.dump(status, fin, indent=4, sort_keys=True)
        except IOError as e:
            self.logger.critical(
                "Failed to write scanners status on NFS share.")
            self.logger.critical(str(e))
        else:
            self.logger.info(
                "Wrote scanners status to file: {}".format(status_file_path))

    def export_scanner_result(self, data, result_file):
        """
        Export scanner logs in given directory.
        """
        try:
            fin = open(result_file, "w")
            json.dump(data, fin, indent=4, sort_keys=True)
        except IOError as e:
            self.logger.critical(
                "Failed to write scanner result file {}".format(result_file))
            self.logger.critical(str(e), exc_info=True)
            return None
        else:
            self.logger.info(
                "Exported scanner result file {}".format(result_file))
            return True

    def run_a_scanner(self, obj, image,
                      server=None, giturl=None, gitsha=None,
                      scan_type=None):
        """
        Run the given scanner on image.
        """
        # if its analytics integration scanner
        if server:
            # pass server, giturl, gitsha to analytics-integration scanner
            data = obj.run(image, server, giturl, gitsha, scan_type)
        else:
            # should receive the JSON data loaded
            data = obj.run(image)

        self.logger.info("Finished running {} scanner.".format(
            obj.scanner))

        return data

    def handle_gemini_register(self, scanner_obj, image, scan_type="register"):
        """
        Handles integration scanner register scan type
        default scan_type=register
        """
        server = self.job.get("analytics_server", None)
        giturl = self.job.get("git-url", None)
        gitsha = self.job.get("git-sha", None)
        if not server or not giturl or not gitsha:
            self.logger.critical(
                "scanner-analytics-integration is registered, but"
                "server/git-url/git-sha values are not present "
                "in job data. Skipping to run the scanner for "
                "{}.".format(image))
            # the caller for loop will continue if return is None/{}
            return {}
        else:
            # execute analytics scanner and provide server url
            result = self.run_a_scanner(
                scanner_obj, image, server, giturl, gitsha, scan_type)
            return result

    def handle_normal_scan(self, image):
        """
        Handle scan which happens before polling at jenkins
        This runs 5 scanners. analytics-integration scanner is
        ran with scan_type=register
        returns scanners_data
        """
        # initialize scanners data
        scanners_data = {}
        scanners_data["msg"] = {}
        scanners_data["logs_file_path"] = {}
        scanners_data["alert"] = {}

        # run the multiple scanners on image under test
        for scanner in self.scanners:
            # create object for the respective scanner class
            scanner_obj = scanner()

            # if analytics_integration scanner, provide extra arg
            if scanner_obj.__class__.__name__ == "AnalyticsIntegration":
                result = self.handle_gemini_register(scanner_obj, image)
                if not result:
                    # case where git-url, git-sha is not present in job
                    continue

            # or if its any other scanner, run with
            else:
                # execute atomic scan and grab the results
                result = self.run_a_scanner(scanner_obj, image)

            # each scanner invoker class defines the output result file
            result_file = os.path.join(
                self.job["logs_dir"], scanner_obj.result_file)

            # for only the cases where export/write operation could fail
            if not self.export_scanner_result(result, result_file):
                continue

            # keep the message
            scanners_data["msg"][result["scanner"]] = result["msg"]
            scanners_data["alert"][result["scanner"]] = result.get(
                "alert", False)

            # pass the logs filepath via beanstalk tube
            # TODO: change the respective key from logs ==> logs_URL while
            # accessing this
            # scanner results logs URL
            # scanners_data["logs_URL"][result["scanner"]]=result_file.replace(
            #    settings.LOGS_DIR,
            #    settings.LOGS_URL_BASE)

            # put the logs file name as well here in data
            scanners_data["logs_file_path"][result["scanner"]] = result_file
        return scanners_data

    def handle_gemini_report(self, scanner_obj, image, scan_type="report"):
        """
        Handles integration scanner report scan type
        this will be triggerred only if job has gemini_report key
        default scan_type="report"
        """
        if self.job.get("gemini_report", False):
            self.logger.info(
                "Report found by jenkins at gemini server for {}".format(
                    self.job.get("image_under_test")))
        else:
            self.logger.info(
                "No report found by jenkins at server for {}".format(
                    self.job.get("image_under_test")))

        server = self.job.get("analytics_server", None)
        giturl = self.job.get("git-url", None)
        gitsha = self.job.get("git-sha", None)
        if not server or not giturl or not gitsha:
            self.logger.critical(
                "scanner-analytics-integration is registered, but"
                "server/git-url/git-sha values are not present "
                "in job data. Skipping to run the scanner for "
                "{}.".format(image))
            # since scanners_data.update() is called at caller method
            return {}
        else:
            # execute analytics scanner and provide server url
            result = self.run_a_scanner(
                scanner_obj, image, server, giturl, gitsha, scan_type)
            return result

    def handle_post_polling_scan(self, image):
        """
        Handle scan job received after polling jobs are complete
        at jenkins. This will run a single scanner;  analytics-integration
        scanner with scan_type=report.
        """
        scanners_data = {}
        scanners_data["msg"] = {}
        scanners_data["alert"] = {}
        scanners_data["logs_file_path"] = {}

        # create the specific scanner object
        scanner_obj = AnalyticsIntegration()
        self.logger.debug(
            "Running integration-scanner after polling for {}".format(
                self.job.get("image_under_test")))

        # run the analytics-integration scanner with scan_type=report
        result = self.handle_gemini_report(scanner_obj, image)

        # case for incomplete job info
        if not result:
            return {}

        # each scanner invoker class defines the output result file
        result_file = os.path.join(
            self.job["logs_dir"], scanner_obj.result_file)

        # for only the cases where export/write operation could fail
        if not self.export_scanner_result(result, result_file):
            return {}

        # keep the message
        scanners_data["msg"][result["scanner"]] = result["msg"]
        scanners_data["alert"][result["scanner"]] = result.get("alert", False)

        # pass the logs filepath via beanstalk tube
        # TODO: change the respective key from logs ==> logs_URL while
        # accessing this
        # scanner results logs URL
        # scanners_data["logs_URL"][result["scanner"]]=result_file.replace(
        #    settings.LOGS_DIR,
        #    settings.LOGS_URL_BASE)

        # put the logs file name as well here in data
        scanners_data["logs_file_path"][result["scanner"]] = result_file
        return scanners_data

    def scan(self):
        """
        Run the listed atomic scanners on image under test.

        # FIXME: at the moment this menthod is returning the results of
        multiple scanners in one json and sends over the bus

                             scan
                ______________|________________
                |                             |
        handle_post_polling_scan    handle_normal_scan
                |                       _____|________________
                |                       |                     |
        handle_gemini_report      handle_gemini_register  run_a_scanner

        """
        self.logger.info("Received scanning job : {}".format(self.job))

        image = self.job.get("image_under_test")

        self.logger.info("Image under test for scanning :{}".format(image))
        # copy the job info into scanners data,
        # as we are going to add logs and msg
        scanners_data = self.job
        scanners_data["msg"] = {}
        scanners_data["alert"] = {}
        # scanners_data["logs_URL"] = {}
        scanners_data["logs_file_path"] = {}

        # pull the image first, if failed move on to start_delivery
        if not self.pull_image(image):
            self.logger.info(
                "Image pulled failed, moving job to notify_admin tube.")
            scanners_data["action"] = "notify_admin"
            return False, scanners_data

        # case where this job is running after jenkins polling jobs
        # we need to run only one scanner; analytics-integration with
        # scan_type=report
        if self.job.get("gemini_report"):
            data = self.handle_post_polling_scan(image)

        # case where this job is running before jenkins polling jobs
        # we need to run all scanners and analytics-integration with
        # scan_type=register
        else:
            data = self.handle_normal_scan(image)

        # update scanners_data dict with results from scanners
        scanners_data.update(data)

        # keep notify_user action in data, even if we are deleting the job,
        # since whenever we will read the response, we should be able to see
        # action
        scanners_data["action"] = "notify_user"

        # TODO: Check here if at least one scanner ran successfully
        self.logger.info("Finished executing all scanners.")

        status_file_path = os.path.join(
            self.job["logs_dir"],
            settings.SCANNERS_STATUS_FILE)

        # We export the scanners_status on NFS
        self.export_scanners_status(scanners_data, status_file_path)

        # clean up the system post scan
        self.clean_up(image)

        return True, scanners_data

    def clean_up(self, image):
        """
        Clean up the system post scan
        """
        # after all scanners are ran, remove the image
        self.logger.info("Removing the image: {}".format(image))
        self.docker_conn.remove_image(image=image, force=True)
