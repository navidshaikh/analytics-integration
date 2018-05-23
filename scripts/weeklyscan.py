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


class WeeklyScan(object):
    """
    Class for aggregating operations needed to perform weekly scan
    """

    def __init__(self, sub=None, pub=None):
        # configure logger
        self.logger = logging.getLogger('weeklyscan')
        # initialize beanstalkd queue connection for scan trigger
        self.queue = JobQueue(host=settings.BEANSTALKD_HOST,
                              port=settings.BEANSTALKD_PORT,
                              sub=sub, pub=pub, logger=self.logger)

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

    def read_images(self, images_file):
        """
        Given a file, returns
        [
            [
                $GITURL,
                $GITSHA,
                $IMAGE,
            ],
        [..]
        ]
        """
        try:
            fin = open(images_file)
        except Exception as e:
            self.logger.critical(
                "Failed to read list of images from file {}. {}".format(
                    images_file, str(e)))
            return None

        images = []
        try:
            all_lines = fin.read().strip()
            lines = all_lines.split("\n")
            # remove duplicate lines
            lines = list(set(lines))
            self.logger.info("About {} containers identified for scan.".format(
                len(lines)))
            for line in lines:
                parts = line.strip().split(";")
                if len(parts) != 3:
                    self.logger.warning("Incomplete info for {}".format(parts))
                    continue

                # filter containers which are on r.c.o
                if parts[2].startswith("registry.centos.org"):
                    continue

                images.append(parts)
        except Exception as e:
            self.logger.critical(
                "Failed to parse images via {}.{}".format(images_file, str(e)))
            return None

        return images

    def run(self):
        """
        Finds images on given registry using get-images.sh script,
        and put the job for images for scanning
        """
        self.logger.info("Starting weekly scan..")

        images_file = run_saasherder()
        if not images_file:
            self.logger.critical(
                "No images found via saasherder/get_images.sh. "
                "Aborting weekly scan.")
            return None

        images = self.read_images(images_file)
        if not images:
            self.logger.critical(
                "No images found via saasherder/get_images.sh."
                "Aborting weekly scan.")
            return None

        for image in images:

            # create logs dir
            resultdir = self.new_logs_dir()
            if not resultdir:
                # retry once more
                resultdir = self.new_logs_dir()
                if not resultdir:
                    self.logger.warning(
                        "Can't create result dir for repo {}."
                        "Failed to run weekly scan for it.".format(image[2]))
                    continue

            # image = [git-url, git-hash, image]
            self.put_image_for_scanning(
                image[2], resultdir, image[0], image[1])
            self.logger.info("Queued weekly scanning for {}.".format(image))
        return "Queued containers for weekly scan."

    def put_image_for_scanning(self, image, logs_dir, giturl, gitsha):
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
            "git-url": giturl,
            "git-sha": gitsha,
        }
        self.logger.info("Putting {} for scan..".format(image))
        # now put image for scan
        self.queue.put(json.dumps(job), "master_tube")


if __name__ == "__main__":
    load_logger()
    ws = WeeklyScan(sub="master_tube", pub="master_tube")
    print(ws.run())
