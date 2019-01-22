#!/usr/bin/env python2


from config import ACCESS_TOKEN_FILE
from scanners.base_scanner import BaseScanner

import sys

from datetime import datetime


class AnalyticsIntegration(BaseScanner):
    """
    Analytics integration with server
    """
    NAME = "analytics-integration-scanner"
    DESCRIPTION = ("Analytics integration scanner fetching"
                   " report from Analytics server.")
    TOKEN = open(ACCESS_TOKEN_FILE).read().strip()

    HEADERS = {
        "content-type": "application/json",
        "Authorization": "Bearer {}".format(TOKEN)
    }

    def __init__(self, scan_type):
        """
        Initialize object variables specific to per container scanning
        """
        super(AnalyticsIntegration, self).__init__()
        self.result_file = "analytics_scanner_results.json"
        self.scan_type = scan_type  # possible values ["register", "report"]
        self.api = self.api_name()
        self.image_name = None
        self.server = None
        self.git_url = None
        self.git_sha = None
        self.errors = []
        self.failure = True
        # the needed data to be logged in scanner output
        self.data = {}
        # the templated data this scanner will export
        self.json_out = self.template_json_data(self.NAME, self.scan_type)
        self.configure_stdout_logging(self.NAME)

    def api_name(self):
        """
        Returns API name based on scan type
        """
        # post request
        if self.scan_type == "register":
            return "/api/v1/register"

        # get request
        elif self.scan_type == "report":
            return "/api/v1/report"

    def record_fatal_error(self, error):
        """
        Appends fatal error and returns during exit
        """
        self.errors.append(str(error))

    def _run(self):
        """
        Run the needed tasks for scanning container under test
        """
        try:
            self.image_name = self.get_env_var("IMAGE_NAME")
            self.server = self.get_env_var("SERVER")
            self.git_url = self.get_env_var("GITURL")
            self.git_sha = self.get_env_var("GITSHA")
        except ValueError as e:
            self.record_fatal_error(e)
            self.failure = True
            return self.return_on_failure()
        else:
            self.failure = False
            # set the data right away for ensuring its exported
            self.data["image_name"] = self.image_name
            self.data["server"] = self.server
            self.data["git-url"] = self.git_url
            self.data["git-sha"] = self.git_sha

        # this operation is clubbed with above operations
        if self.failure:
            return self.return_on_failure()

        # post request
        if self.scan_type == "register":
            # Handles /register POST API call
            request_data = {"git-url": self.data["git-url"],
                            "git-sha": self.data["git-sha"]}

            status, resp, s_code = self.post_request(
                endpoint=self.server,
                api=self.api,
                data=request_data,
                headers=self.HEADERS)
            if not status:
                self.failure = True
                self.record_fatal_error(resp)
                return self.return_on_failure(s_code)

            # if there are no return on data failures, return True
            return self.return_on_success(resp, status_code=s_code)

        # get request
        elif self.scan_type == "report":

            # Handles /report GET API call
            request_data = {"git-url": self.data["git-url"],
                            "git-sha": self.data["git-sha"]}

            status, resp, s_code = self.get_request(
                endpoint=self.server,
                api=self.api,
                data=request_data,
                headers=self.HEADERS)
            if not status:
                self.failure = True
                self.record_fatal_error(resp)
                return self.return_on_failure(s_code)

            # if there are no return on data failures, return True
            return self.return_on_success(resp, status_code=s_code)

    def return_on_failure(self, status_code=None):
        """
        Upon failure in running operation this method is called
        """
        self.json_out["Successful"] = False
        current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        self.json_out["Finished Time"] = current_time
        self.json_out["Summary"] = \
            "{} API failed. Error: {}".format(self.api, self.errors)
        self.json_out["api"] = self.api
        self.json_out["api_data"] = self.data
        self.json_out["api_status_code"] = status_code or 0
        return False

    def return_on_success(self, resp, status_code):
        """
        Process output of scanner after successful POST call to server
        """
        self.json_out["Successful"] = True
        current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        self.json_out["Finished Time"] = current_time
        if status_code == 400:
            self.json_out["Summary"] = resp.get(
                "summary",
                "Report can't be generated at server as source git repo has "
                "missing dependency/lock/manifest file.")
        else:
            self.json_out["Summary"] = resp.get(
                "summary", "Check detailed report for more info.")
        self.json_out["Scan Results"] = resp
        self.json_out["api"] = self.api
        self.json_out["api_data"] = self.data
        self.json_out["api_status_code"] = status_code
        return True

    def run(self):
        """
        Run the scanner and print the result on stdout
        """
        status = self._run()
        print ("Scanner execution status: {}".format(status))
        print ("api_status_code: {}".format(
            self.json_out.get("api_status_code",
                              "Unable to retrieve status code!")))

        # TODO: Configure export dir to export results
        # Write scan results to json file
        output_dir = self.get_env_var(self.RESULT_DIR_ENV_VAR)
        self.export_json_results(self.json_out, output_dir, self.result_file)
        print ("Exported the scanner results.")


if __name__ == "__main__":
    command = sys.argv[1]
    scanner = AnalyticsIntegration(scan_type=command)
    scanner.run()
