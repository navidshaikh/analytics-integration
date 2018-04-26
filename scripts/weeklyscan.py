#!/usr/bin/env python

"""
This module iniializes the weekly scan by finding out the list of images
on the registry and initializing the scan tasks scan-worker.
"""

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

    def target_image_in_repository(self, repo):
        """
        Given a repository name, run saas herder parser and
        return a container image name (with tag)
        """
        values = run_saasherder(repo)
        if not values or values.get("image_tag", False):
            self.logger.warning(
                "Failed to find tag for repo {} using saasherder.".format(
                    repo))
            return None
        return repo + ":" + values.get("image_tag")

    def random_string(self, size=6):
        """
        Returns a unique random chars string name of size given
        """
        chars = string.ascii_lowercase + string.digits
        return "".join(random.choice(chars) for _ in range(size))

    def new_logs_dir(self, basedir="/tmp"):
        """
        Creates a temp dir in /tmp location
        """
        dirname = os.path.join(basedir, self.random_string)
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
        # lets get needed repos in given registry
        repos = self.repos_in_registry()

        if not repos:
            self.logger.critical(
                "No repos found in registry for {} namespace.".format(
                    self.target_namespaces))
            return None

        for repo in repos:
            image = self.target_image_in_repository(repo)
            if not image:
                self.logger.warning(
                    "Failed to run weekly scan for repo {}.".format(repo))
                continue

            resultdir = self.new_logs_dir()
            if not resultdir:
                # retry once more
                resultdir = self.new_logs_dir()
                if not resultdir:
                    self.logger.warning(
                        "Failed to run weekly scan for repo {}.".format(
                            repo))
                continue
            # now put image for scan
            self.put_image_for_scanning(image, resultdir)
            self.logger.info("Queued weekly scanning for {}.".format(image))
        return "Queued containers for weekly scan."

    def put_image_for_scanning(self, image, logs_dir):
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
        }
        self.queue.put(json.dumps(job))


if __name__ == "__main__":
    load_logger()
    ws = WeeklyScan(sub="master_tube", pub="master_tube")
    print(ws.run())
