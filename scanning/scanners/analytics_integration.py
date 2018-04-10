#!/usr/bin/python
"""This class is a wrapper for running analytics scanner and grab results."""
import os

from scanning.scanners.base import Scanner


class AnalyticsIntegration(Scanner):
    """Checks updates for packages other than RPM."""

    def __init__(self):
        """Name it to Misc Package update check."""
        self.scanner = "analytics-integration"
        self.scan_types = ["register"]
        self.result_file = "analytics_scanner_results.json"

    def scan(self, image, analytics_server):
        """Run the scanner."""
        # initializing a blank list that will contain results from all the
        # scan types of this scanner
        logs = []
        super(AnalyticsIntegration, self).__init__(
            image=image,
            scanner=self.scanner,
            result_file=self.result_file,
        )

        os.environ["IMAGE_NAME"] = image
        os.environ["SERVER"] = analytics_server

        for st in self.scan_types:
            scan_results = self.scan(scan_type=st, process_output=False)

            if not scan_results("status", False):
                continue

            logs.append(scan_results["logs"])

        # invoke base class's cleanup utility
        self.cleanup()

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
        data["scanner"] = self.scanner
        data["image_under_test"] = self.image
        data["msg"] = ""
        for i in logs:
            data["msg"] += i.get("Summary", "Failed to run the scanner.")
        data["logs"] = logs

        return data
