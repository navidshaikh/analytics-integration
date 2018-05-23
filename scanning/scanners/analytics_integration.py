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

    def run(self, image, server, giturl, gitsha, scan_type="register"):
        """Run the scanner."""
        # initializing a blank list that will contain results from all the
        # scan types of this scanner
        super(AnalyticsIntegration, self).__init__(
            image=image,
            scanner=self.scanner,
            result_file=self.result_file,
        )

        # this scanner needs following two env vars for atomic scan command
        env_vars = {
            "IMAGE_NAME": image,
            "SERVER": server,
            "GITURL": giturl,
            "GITSHA": gitsha}

        data = self.scan(
            process_output=False, env_vars=env_vars, scan_type=scan_type)

        # invoke base class's cleanup utility
        self.cleanup()

        return self.process_output(data, scan_type)

    def process_output(self, json_data, scan_type):
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

        # there are logs inside logs
        logs = json_data.get("logs", {})
        data["logs"] = logs
        # default
        data["alert"] = False

        if scan_type == "register":
            data["msg"] = ("Registered container for scanning at server."
                           " Report has registration related info, no data.")
        else:
            deps = logs.get("Scan Results", {}).get("dependencies", [])
            # if dependencies are not found
            if not deps:
                data["msg"] = "No dependencies found. Timed out."
            else:
                msg = ""
                # iterate through all dependencies found
                for each in deps:
                    # if cve count, log the issue in msg
                    if each.get("cve_count", 0) > 0:
                        data["alert"] = True
                        for k, v in each.iteritems():
                            msg = msg + "\n{}:\t\t{}+ \n".format(str(k), str(v))
                    msg = msg + "\n"

                # if no cves found
                if not data["alert"]:
                    data["msg"] = "No CVEs found in image under test."
                # else, if cves found
                else:
                    # store the processed msg
                    data["msg"] = msg

        return data
