from scanning.vendors import beanstalkc
from scanning.lib import settings
import sys
import json

conn = beanstalkc.Connection(
    host=settings.BEANSTALKD_HOST,
    port=settings.BEANSTALKD_PORT)

conn.use("master_tube")

EMAIL = "nshaikh@redhat.com"
ANALYTICS_SERVER = "http://f8a-gemini-server-aagshah-greenfield-test.dev.rdu2c.fabric8.io"

if len(sys.argv) < 2:
    print "Please provide image under test as argument to script."
    print "example: python put_job.py centos:latest"

image_under_test = sys.argv[1].strip()

if len(sys.argv) > 2:
    logs_dir = sys.argv[2].strip()
else:
    logs_dir = "/tmp/"

image_under_test = sys.argv[1]
job_data = {
    "image_under_test": image_under_test,
    "action": "start_scan",
    "logs_dir": logs_dir,
    "analytics_server": ANALYTICS_SERVER,
    "notify_email": EMAIL,
}

conn.put(json.dumps(job_data))
