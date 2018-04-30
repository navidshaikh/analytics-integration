#!/usr/bin/env python

"""
This module iniializes the weekly scan by finding out the list of images
on the registry and initializing the scan tasks scan-worker.
"""

import datetime
import json
import logging
import os
import random
import string

from scanning.lib.queue import JobQueue
from scanning.lib.log import load_logger
from scanning.lib import settings
from scanning.lib.run_saasherder import run_saasherder
from inspect_registry import InspectRegistry


class WeeklyScan(object):
    """
    Class for aggregating operations needed to perform weekly scan
    """

    def __init__(self, sub=None, pub=None):
        # configure logger
        self.logger = logging.getLogger('weeklyscan')
        self.registry = settings.REGISTRY
        self.target_namespaces = settings.TARGET_NAMESPACES
        self.ir = InspectRegistry(
            self.registry,
            settings.SECURE_REGISTRY,
            self.logger
        )
        # initialize beanstalkd queue connection for scan trigger
        self.queue = JobQueue(host=settings.BEANSTALKD_HOST,
                              port=settings.BEANSTALKD_PORT,
                              sub=sub, pub=pub, logger=self.logger)

    def repos_in_registry(self):
        """
        Find repository names available in give registry
        """
        # find all available repositories (not images)
        repos = self.ir.find_repos()
        # subset repositories to ones that are required
        repos = self.ir.subset_repos_on_namespace(
            repos,
            self.target_namespaces
        )
        return repos

    def random_string(self, size=3):
        """
        Returns a unique random chars string name of size given
        """
        ts = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        chars = string.ascii_lowercase + string.digits
        rc = "".join(random.choice(chars) for _ in range(size))
        return "{}-{}-scan".format(ts, rc)

    def new_logs_dir(self, basedir="/tmp"):
        """
        Creates a temp dir in /tmp location
        """
        dirname = os.path.join(basedir, self.random_string())
        try:
            os.makedirs(dirname)
        except OSError as e:
            self.logger.warning(
                "Failing to create {} dir for scanner results. {}".format(
                    dirname, e))
            return None
        else:
            return dirname

    def run(self):
        """
        Finds repositories on given registry,
        subset the repositories as per required/target repositories
        finds out latest/deployed tag or container image in given repository
        and put the job for given container images for scanning
        """

        self.logger.info("Starting weekly scan for containers in {}".format(
            self.registry))
        # lets get needed repos in given registry
        repos = self.repos_in_registry()

        if not repos:
            self.logger.critical(
                "No repos found in registry for {} namespace.".format(
                    self.target_namespaces))
            return None

        for repo in repos:
            self.logger.debug("Checking {} via saasherder".format(repo))
            # running saasherder
            values = run_saasherder(repo)
            # case where repo is not located by saasherder
            if not values:
                continue

            self.logger.debug("Values found via saas herder {}".format(values))
            # run_saasherder function ensures values has "image-tag"
            image = self.registry + "/" + repo + ":" + values.get("image-tag")

            # create logs dir
            resultdir = self.new_logs_dir()
            if not resultdir:
                # retry once more
                resultdir = self.new_logs_dir()
                if not resultdir:
                    self.logger.warning(
                        "Can't create result dir for repo {}."
                        "Failed to run weekly scan for it.".format(repo))
                    continue
            # now put image for scan
            self.put_image_for_scanning(image, resultdir, values)
            # now job for polling tube so that jenkins can poll the /report api
            self.put_image_for_polling(image, resultdir, values)
            self.logger.info("Queued weekly scanning for {}.".format(image))
        return "Queued containers for weekly scan."

    def put_image_for_polling(self, image, logs_dir, values):
        """
        Put the job on polling tube
        """
        poll_tube = "poll_server"
        job = {
            "action": "start_scan",
            "weekly": "True",
            "image_under_test": image,
            "analytics_server": settings.ANALYTICS_SERVER,
            "notify_email": settings.NOTIFY_EMAILS,
            "logs_dir": logs_dir,
            "git-sha": values.get("git-sha"),
            "git-url": values.get("git-url"),
        }
        # set tube param to method call explicitly here
        self.queue.put(json.dumps(job), tube=poll_tube)
        self.logger.info("Queued job at {} queue.".format(poll_tube))

    def put_image_for_scanning(self, image, logs_dir, values):
        """
        Put the image for scanning on beanstalkd tube
        """
        job = {
            "action": "start_scan",
            "weekly": True,
            "image_under_test": image,
            "analytics_server": settings.ANALYTICS_SERVER,
            "notify_email": settings.NOTIFY_EMAILS,
            "logs_dir": logs_dir,
            "git-url": values.get("git-url"),
            "git-sha": values.get("git-sha")
        }
        self.queue.put(json.dumps(job))


if __name__ == "__main__":
    load_logger()
    ws = WeeklyScan(sub="master_tube", pub="master_tube")
    print(ws.run())
