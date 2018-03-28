from scanning.vendors import beanstalkc
from scanning.lib import settings
import sys
import os
import json

conn = beanstalkc.Connection(
    host=settings.BEANSTALKD_HOST,
    port=settings.BEANSTALKD_PORT)

conn.use("start_scan")

if len(sys.argv) < 2:
    print "Please provide image under test as argument to script."
    print "example: python put_job.py centos:latest"

image_under_test = sys.argv[1].strip()

if len(sys.argv) > 2:
    logs_dir = sys.argv[2].strip()

image_under_test = sys.argv[1]
job_data = {
    "image_under_test": image_under_test,
    "action": "start_scan",
    "logs_dir": logs_dir,
}

conn.put(json.dumps(job_data))
