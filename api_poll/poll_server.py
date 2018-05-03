#!/usr/bin/python

"""
This module contains the worker that handles the scanning.
"""
import json
import logging
import sys
import yaml
from jinja2 import Environment, FileSystemLoader

from scanning.vendors import beanstalkc
from scanning.lib import settings
from scanning.lib.queue import JobQueue

queue = JobQueue(host=settings.BEANSTALKD_HOST,
            port=settings.BEANSTALKD_PORT,
            sub="poll_server", pub="poll_failed")

job = None
job_obj = None
try:
    job_obj = queue.get()
    job=json.loads(job_obj.body)
except Exception as e:
    print("Could not retrieve job details:%s " %str(e))

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

if job:
    self.queue.delete(job)
