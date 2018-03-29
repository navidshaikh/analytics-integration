from scanning.vendors import beanstalkc
from scanning.lib import settings
import sys
import json

conn = beanstalkc.Connection(
    host=settings.BEANSTALKD_HOST,
    port=settings.BEANSTALKD_PORT)

conn.use("notify")

data = {u'analytics_server': u'http://f8a-gemini-server-aagshah-greenfield-test.dev.rdu2c.fabric8.io', u'notify_email': u'nshaikh@redhat.com', u'image_under_test': u'che-starter:rhel7', u'logs_dir': u'/tmp/demo4', u'action': u'notify', u'logs_file_path': {u'analytics-integration': u'/tmp/demo4/analytics_integration_results.json', u'pipeline-scanner': u'/tmp/demo4/pipeline_scanner_results.json', u'container-capabilities-scanner': u'/tmp/demo4/container-capabilities-results.json', u'scanner-rpm-verify': u'/tmp/demo4/RPMVerify_scanner_results.json', u'misc-package-updates': u'/tmp/demo4/misc_package_updates_scanner_results.json'}}


conn.put(json.dumps(data))
