#!/usr/bin/python

"""
This module contains the worker that handles the scanning.
"""
import json
import logging
import os
import sys

from jinja2 import Environment, FileSystemLoader

from scanning.lib import settings
from scanning.lib.log import load_logger
from scanning.lib.queue import JobQueue


def poll_server(template_location):
    load_logger()
    logger = logging.getLogger('poll-job')
    queue = JobQueue(host=settings.BEANSTALKD_HOST,
                     port=settings.BEANSTALKD_PORT,
                     sub="poll_server", pub="poll_failed", logger=logger)

    job = None
    job_obj = None
    project = {}
    job_details = None
    try:
        job_obj = queue.get()
        job = json.loads(job_obj.body)
        logger.info("Got job: %s" % str(job))
    except Exception as e:
        logger.warning("Could not retrieve job details:%s " % str(e))

    image_under_test = job.get("image_under_test")
    project["image_under_test"] = image_under_test
    project["analytics_server"] = job.get("analytics_server")
    project["git-sha"] = job.get("git-sha")
    project["git-url"] = job.get("git-url")
    project[
        "api-server-poll-job-name"] = image_under_test.replace(
            "/", "-").replace(".", "-")

    try:
        env = Environment(loader=FileSystemLoader(
            './'), trim_blocks=True, lstrip_blocks=True)
        template = env.get_template("api-server-poll.yml")
        logger.info("Project details got is: %s" % str(project))
        job_details = template.render(project)
        logger.info("Template is rendered with project: %s" % str(project))
    except Exception as e:
        logger.critical("Error template is not updated: %s" % str(e))

    try:
        generated_filename = os.path.join(
            template_location, "poll_server_generated.yaml")
        with open(generated_filename, 'w') as outfile:
            outfile.write(job_details)
            outfile.flush()
    except Exception as e:
        logger.critical("Error job_details could not be updated %s" % str(e))

    if job:
        queue.delete(job_obj)


if __name__ == '__main__':
    template_location = sys.argv[1]
    poll_server(template_location)
