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

conn = beanstalkc.Connection(
    host=settings.BEANSTALKD_HOST,
    port=settings.BEANSTALKD_PORT)

conn.watch("poll_server")

job=None

try:
    if conn.stats_tube("poll_server")['current-jobs-ready'] > 0 :
        job = conn.reserve()
    else:
        print(" No job in tube")
        sys.exit(0)
except Exception as e:
    print("Could not retrieve job details")
    sys.exit(1)

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

