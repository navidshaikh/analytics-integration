#!/usr/bin/python
"""This class is a wrapper for running analytics scanner and grab results."""
import os

from container_pipeline.scanners.base import Scanner


class AnalyticsIntegration(Scanner):
    """Checks updates for packages other than RPM."""

    def __init__(self):
        """Name it to Misc Package update check."""
        self.scanner_name = "analytics-integration"
        self.full_scanner_name = "scanner-analytics-integration:rhel7"
        self.scan_types = ["register"]

    def scan(self, image_under_test, analytics_server):
        """Run the scanner."""
        # initializing a blank list that will contain results from all the
        # scan types of this scanner
        logs = []
        super(AnalyticsIntegration, self).__init__(
            image_under_test=image_under_test,
            scanner_name=self.scanner_name,
            full_scanner_name=self.full_scanner_name,
            to_process_output=False
        )

        os.environ["IMAGE_NAME"] = image_under_test
        if analytics_server:
            os.environ["SERVER"] = analytics_server

        for _ in self.scan_types:
            scan_cmd = [
                "atomic",
                "scan",
                "--scanner={}".format(self.scanner_name),
                "--scan_type={}".format(_),
                "{}".format(image_under_test)
            ]

            scan_results = super(AnalyticsIntegration, self).scan(scan_cmd)

            if not scan_results[0]:
                return False, None

            logs.append(scan_results[1])

        return True, self.process_output(logs)

    def process_output(self, logs):
        """
        Genaralising output.

        Processing data for this scanner is unlike other scanners
        because, for this scanner we need to send logs of three
        different scan types of same atomic scanner unlike other
        atomic scanners which have only one, and hence treated
        as default, scan type
        """
        data = {}
        data["scanner_name"] = self.scanner_name
        data["msg"] = ""
        for i in logs:
            data["msg"] += i["Summary"]
        data["logs"] = logs

        return data
