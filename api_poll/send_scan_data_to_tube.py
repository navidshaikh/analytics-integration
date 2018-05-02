#!/usr/bin/env python

import beanstalkc
import json
import sys

print "Getting scan details from jenkins"
scan_details = {}
scan_details["action"] = "start_scan"
scan_details["weekly"] = "True"
scan_details["analytics_server"] = sys.argv[1]
scan_details["image_under_test"] = sys.argv[2]
scan_details["git-url"] = sys.argv[3]
scan_details["git-sha"] = sys.argv[4]
scan_details["gemini_report"] = sys.argv[5]
scan_details["notify_email"] = settings.NOTIFY_EMAILS


print "Pushing bild details in the tube"
bs = beanstalkc.Connection(host="localhost")
bs.use("master_tube")
bs.put(json.dumps(scan_details))
print "scan details is pushed to master tube"
