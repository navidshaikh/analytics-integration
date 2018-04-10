#!/usr/bin/python
"""This class is a wrapper for running analytics scanner and grab results."""

from scanning.scanners.base import Scanner


class AnalyticsIntegration(Scanner):
    """
    Scanner to invoke scanning job at Analytics server.
    """

    def __init__(self):
        """
        Initialize the invoker class.
        """
        self.scanner = "analytics-integration"
        self.result_file = "analytics_scanner_results.json"

    def run(self, image, analytics_server):
        """Run the scanner."""
        # initializing a blank list that will contain results from all the
        # scan types of this scanner
        super(AnalyticsIntegration, self).__init__(
            image=image,
            scanner=self.scanner,
            result_file=self.result_file,
        )

        # this scanner needs following two env vars for atomic scan command
        env_vars = {"IMAGE_NAME": image, "SERVER": analytics_server}

        data = self.scan(process_output=False, env_vars=env_vars)

        # invoke base class's cleanup utility
        self.cleanup()

        return self.process_output(data)

    def process_output(self, json_data):
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
        # if status of execution is False
        if not json_data.get("status", False):
            data["msg"] = "Failed to run the scanner."
            data["logs"] = {}
            return data
        # there are logs inside logs
        logs = json_data.get("logs", {})
        if not logs:
            data["msg"] = "Failed to run the scanner."
        else:
            data["msg"] = logs.get("Scan Results", {}).get(
                "summary", "Failed to run the scanner")
        data["logs"] = logs
        return data
