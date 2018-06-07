#!/usr/bin/env python

import json
import logging
import os

# importing config present at root of repository
from config import ALERTS
from scanning.vendors import beanstalkc
from scanning.lib.log import load_logger
from scanning.lib.command import run_cmd

load_logger()

logger = logging.getLogger('notify')

bs = beanstalkc.Connection(host="0.0.0.0")
bs.watch("notify")

SCANNERS_STATUS = "scanners_status.json"


class GitPushWorker(object):
    "Compose and send build status, linter and scanners results"

    def __init__(self, job_info):
        self.alerts = ALERTS

        self.job_info = job_info

        self.image_under_test = job_info.get("image_under_test")

        # the logs directory
        self.logs_dir = self.job_info["logs_dir"]

        # scanners execution status file
        self.scanners_status_file = os.path.join(
            self.logs_dir, SCANNERS_STATUS)

        self.scanners_status = self._read_status(self.scanners_status_file)

    def _read_status(self, filepath):
        "Method to read status JSON files"
        try:
            fin = open(filepath)
        except IOError as e:
            logger.warning("Failed to read %s file, error: %s" %
                           (filepath, str(e)))
            return None
        else:
            return json.load(fin)

    def _write_text_file(self, filepath, text):
        "Method to write text files"
        try:
            fin = open(filepath)
            fin.write(text)
        except IOError as e:
            logger.warning("Failed to write to {} file, error: {}".format(
                           filepath, e))
            return None
        else:
            return True

    def _read_text_file(self, text_file):
        "Method to read text files"

        try:
            fin = open(text_file)
        except IOError as e:
            logger.warning("Failed to read %s file, error: %s" %
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

    def run(self):
        """
        Main method to orchestrate the alert text composition
        and git push the contents
        """
        self.problem = self.is_problem_in_reports()
        alert_contents = self.compose_scanners_summary()

        if "ok" in self.alerts:
            self.gitpush(alert_contents)
        elif "problem" in self.alerts and self.problem:
            self.gitpush(alert_contents)
        else:
            logger.debug("Not pushing scan data to git based on alert config.")
            logger.debug("Image: {}".format(self.image_under_test))
            logger.debug("Contents: {}".format(alert_contents))

    def gitpush(self, alert_contents):
        """
        push the alert contents to configured git repository
        """
        repo_parts = self.split_repo_name(self.image_under_test)
        image = repo_parts.get("image", "")
        image = image.replace("osio-prod/", "")

        # path of the git repo to write alerts inside
        scan_gitpath = self.job_info.get("scan_gitpath")

        # the dir to be created per image for alerts
        # replace / and : with - , this is for sane dir names
        image_dirname = image.replace("/", "-").replace(":", "-")

        # dir for alerts per container
        alert_dirname = os.path.join(scan_gitpath, image_dirname)

        # if dir does not exists, create one
        if not os.path.isdir(alert_dirname):
            os.path.makedirs(alert_dirname)

        # abs path of alert file
        alert_path = os.path.join(alert_dirname, "alerts.txt")

        if not self._write_text_file(alert_path, alert_contents):
            self.logger.critical("Failing to write alert contents.")
            return False

        commit_msg = "Alerts for {}".format(self.image)
        cmd = ("cd {} && git add . && git commit -m '{}' "
               "&& git push origin master && cd -".format(
                   alert_dirname, commit_msg))

        self.logger.info("Adding and pushing alerts to git origin..")
        try:
            run_cmd(cmd)
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


while True:
    logger.debug("Listening to notify tube")
    job = bs.reserve()
    job_id = job.jid
    job_info = json.loads(job.body)
    logger.info("Received Job: {}".format(str(job_info)))
    try:
        gp_worker = GitPushWorker(job_info)
        gp_worker.run()
    except Exception as e:
        logger.critical(
            "Notify worker could not process the job: {} with error : {}"
            .format(str(job_info), e))
    finally:
        job.delete()
