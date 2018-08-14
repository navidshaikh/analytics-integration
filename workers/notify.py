#!/usr/bin/env python

import json
import logging
import os

# importing config present at root of repository
from config import ALERTS
from scanning.lib import log
from scanning.lib.command import run_cmd
from base import BaseWorker
from config import GITBRANCH

from shutil import copy2

SCANNERS_STATUS = "scanners_status.json"

SCANNERS_RESULT_FILENAMES = [
    "analytics_scanner_results.json",
    "misc_package_updates_scanner_results.json",
    "rpm_verify_scanner_results.json",
    "container_capabilities_scanner_results.json",
    "pipeline_scanner_results.json",
]


class GitPushWorker(BaseWorker):
    """
    Notify worker aka gitpush worker. Sends alerts to configured git repo
    """
    NAME = "Notify Worker"

    def __init__(self, logger=None, sub=None, pub=None):
        super(GitPushWorker, self).__init__(logger=logger, sub=sub, pub=pub)

    def handle_job(self, job):
        """
        Handle the notify job
        """
        self.job = job

        self.alerts = ALERTS

        self.gitbranch = GITBRANCH

        self.image_under_test = job.get("image_under_test")

        # the logs directory
        self.logs_dir = self.job["logs_dir"]

        # scanners execution status file
        self.scanners_status_file = os.path.join(
            self.logs_dir, SCANNERS_STATUS)

        self.scanners_status = self._read_status(self.scanners_status_file)
        # call the notify method, which orchestrate functioning
        self.notify()

    def _read_status(self, filepath):
        "Method to read status JSON files"
        try:
            fin = open(filepath)
        except IOError as e:
            self.logger.warning("Failed to read %s file, error: %s" %
                                (filepath, str(e)))
            return None
        else:
            return json.load(fin)

    def _write_text_file(self, filepath, text):
        "Method to write text files"
        try:
            fin = open(filepath, "w")
            fin.write(text)
        except IOError as e:
            self.logger.warning("Failed to write to {} file, error: {}".format(
                filepath, e))
            return None
        else:
            return True

    def _read_text_file(self, text_file):
        "Method to read text files"

        try:
            fin = open(text_file)
        except IOError as e:
            self.logger.warning("Failed to read %s file, error: %s" %
                                (text_file, str(e)))
            return None
        else:
            return fin.read()

    def compose_scanners_summary(self):
        "Composes scanners result summary"

        if not self.scanners_status:
            # TODO: Better handling and reporting here
            return ""

        text = ""
        for scanner in self.scanners_status["logs_file_path"]:
            text += self.scanners_status["msg"][scanner] + "\n"
            text += "\n\n"

        return text.rstrip()

    def is_problem_in_reports(self):
        """
        Go through scanners status file and find out if there are problems
        """
        for scanner, alert in self.scanners_status.get(
                "alert", {}).iteritems():
            if alert:
                return True
        return False

    def notify(self):
        """
        Main method to orchestrate the alert text composition
        and git push the contents
        """
        self.problem = self.is_problem_in_reports()
        # alert_contents could be empty too, which is handled
        # later in notify method, in case of empty alert_contents
        # no alert.txt file will be generated
        alert_contents = self.compose_scanners_summary()

        # "ok" and "problem" are two possible alert configs
        # "ok" means, every scanned container results will be logged
        # irrespective of whether results are "problem" or not
        if "ok" in self.alerts:
            self.gitpush(alert_contents)

        # if "problem" alert configs are configured in config.py
        # only containers identified with problems will be reported
        # at configured git repository
        elif "problem" in self.alerts and self.problem:
            self.gitpuh(alert_contents)

        else:
            self.logger.debug(
                "Not pushing scan data to git based on alert config.")
            self.logger.debug("Image: {}".format(self.image_under_test))
            self.logger.debug("Contents: {}".format(alert_contents))

    def copy_scanners_result_file(self, destdir):
        """
        Copy given scanners result file into output git dir

        destdir: destination dir, a new file with same basename as source will
                 be written
        default scanner=analytics-integration
        """
        logs_dir = self.job.get("logs_dir", "")
        if not logs_dir:
            self.logger.error(
                "Logs dir not found for adding scanners result to git.")
            return

        for each in SCANNERS_RESULT_FILENAMES:
            source = os.path.join(logs_dir, each)
            if not os.path.exists(source):
                self.logger.warning(
                    "Result file {} is absent.".format(source))
                continue

            try:
                copy2(source, destdir)
            except IOError as e:
                self.logger.error("Failed to copy file {}.".format(source))
                self.logger.error("Error: {}".format(e))

    def gitpush(self, alert_contents=None):
        """
        push the alert contents to configured git repository
        """
        repo_parts = self.split_repo_name(self.image_under_test)
        image = repo_parts.get("image", "")
        image = image.replace("osio-prod/", "")

        # path of the git repo to write alerts inside
        scan_gitpath = self.job.get("scan_gitpath")

        # the dir to be created per image for alerts
        # replace / and : with - , this is for sane dir names
        image_dirname = image.replace("/", "-").replace(":", "-")

        # dir for alerts per container
        alert_dirname = os.path.join(scan_gitpath, image_dirname)

        # if dir does not exists, create one
        if not os.path.isdir(alert_dirname):
            os.makedirs(alert_dirname)

        # if alerts_contents are given, then only generate the alerts.txt
        # file, else only log the scanners results
        if alert_contents:
            # abs path of alert file
            alert_path = os.path.join(alert_dirname, "alerts.txt")

            if not self._write_text_file(alert_path, alert_contents):
                self.logger.critical("Failing to write alert contents.")
                return False

        commit_msg = "Scan results for {}".format(self.image_under_test)

        # copy scanner's original result file into git path
        self.copy_scanners_result_file(destdir=alert_dirname)

        cmd = ("cd {0} && git checkout {1} && "
               "git add . && git commit -m '{2}' "
               "&& git push origin {1} && cd -".format(
                   alert_dirname,
                   self.gitbranch,
                   commit_msg)
               )

        self.logger.info("Adding and pushing alerts to git..")
        try:
            run_cmd(cmd, shell=True)
        except Exception as e:
            self.logger.critical(
                "Failed to add alerts to git. Error {}".format(e))
            return False

        return True

    def split_repo_name(self, repo_name):
        """
        Split given repository names
        """
        if not repo_name:
            return {}

        parts = repo_name.split("/")

        if len(parts) == 1:
            # case for foo:latest
            registry = None
            image = repo_name
        elif len(parts) == 2:
            # check if part[0] is a registry
            if "." in parts[0] or ":" in parts[0]:
                # case for r.c.o/foo:latest
                registry = parts[0]
                image = parts[1]
            else:
                # case for foo/bar:latest
                registry = None

                image = repo_name

        # for cases where len(parts) > 2
        else:
            # check if part[0] is a registry
            if "." in parts[0] or ":" in parts[0]:
                # case for r.c.o/foo/bar:latest
                registry = parts[0]
                image = "/".join(parts[1:])
            else:
                # case for prod/foo/bar:latest
                registry = None
                image = repo_name

        # now process tags
        image_parts = image.split(":")
        if len(image_parts) == 2:
            # case for foo:tag1, foo/bar:tag1, prod/foo/bar:latest
            image_name = image_parts[0]
            tag = image_parts[1]
        else:
            # cases for foo , foo/bar, prod/foo/bar
            image_name = image
            # use default tag
            tag = "latest"
        return {"registry": registry, "image": image,
                "image_name": image_name, "tag": tag}


if __name__ == "__main__":

    log.load_logger()
    logger = logging.getLogger("notify")
    gp_worker = GitPushWorker(logger, sub="notify", pub="notify_admin")
    # run method is implemented in base worker
    gp_worker.run()
