#!/usr/bin/env python2


from scanners.base_scanner import BaseScanner

from requests.compat import urljoin
from datetime import datetime

import json
import logging
import os
import requests
import sys


class AnalyticsIntegration(BaseScanner):
    """
    Analytics integration with server
    """
    NAME = "analytics-integration-scanner"
    DESCRIPTION = ("Analytics integration scanner fetching"
                   " report from Analytics server.")
    TOKEN = open("osio_token.txt").read().strip()

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
        # scan_type = [register, scan, get_report]
        self.scan_type = scan_type
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
        self.json_out = self.template_json_data()

    def configure_logging(self, name="integration-scanner"):
        """
        Configures logging and returns logger object
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s p%(process)s %(name)s %(lineno)d "
            "%(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger

    def get_env_var(self, env_name):
        """
        Gets the configured given env_name or None
        """
        if not os.environ.get(env_name, False):
            raise ValueError(
                "No value for {0} env var. Please re-run with: "
                "{0}=<VALUE> [..] atomic scan [..] ".format(env_name)
            )
        return os.environ.get(env_name)

    def post_request(self, endpoint, api, data):
        """
        Make a post call to analytics server with given data

        :param endpoint: API server end point
        :param api: API to make POST call against
        :param data: JSON data needed for POST call to api endpoint

        :return: Tuple (status, error_if_any, status_code)
                 where status = True/False
                       error_if_any = string message on error, "" on success
                       status_code = status_code returned by server
        """
        url = urljoin(endpoint, api)
        # TODO: check if we need API key in data
        try:
            r = requests.post(
                url,
                json.dumps(data),
                headers=self.HEADERS)
        except requests.exceptions.RequestException as e:
            error = ("Could not send POST request to URL {0}, "
                     "with data: {1}.").format(url, str(data))
            return False, error + " Error: " + str(e), 0
        else:
            # requests.codes.ok == 200
            if r.status_code == requests.codes.ok:
                return True, json.loads(r.text), r.status_code
            else:
                return False, "Returned {} status code for {}".format(
                    r.status_code, url), r.status_code

    def get_request(self, endpoint, api, data):
        """
        Make a get call to analytics server

        :param endpoint: API server end point
        :param api: API to make GET call against
        :param data: JSON data needed for GET call

        :return: Tuple (status, error_if_any, status_code)
                 where status = True/False
                       error_if_any = string message on error, "" on success
                       status_code = status_code returned by server
        """
        url = urljoin(endpoint, api)
        # TODO: check if we need API key in data
        try:
            r = requests.get(
                url,
                params=data,
                headers=self.HEADERS)

        except requests.exceptions.RequestException as e:
            error = "Failed to process URL: {} with params {}".format(
                    url, data)
            return False, error + " Error: " + str(e), 0
        else:
            # requests.codes.ok == 200 or
            # check for 400 code - as this is a valid response
            # as per the workflow
            if r.status_code in [requests.codes.ok, 400]:
                return True, json.loads(r.text), r.status_code
            else:
                msg = "Returned {} status code for {}. {}".format(
                    r.status_code, url, r.json().get(
                        "summary", "no summary returned from server."))
                return False, msg, r.status_code

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

    def template_json_data(self):
        """
        Populate and return a template standard json data out for scanner.
        """
        current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        json_out = {
            "Start Time": current_time,
            "Successful": False,
            "Scan Type": self.scan_type,
            "UUID": "",
            "CVE Feed Last Updated": "NA",
            "Scanner": self.NAME,
            "Scan Results": {},
            "Summary": ""
        }
        return json_out

    def record_fatal_error(self, error):
        """
        Appends fatal error and returns during exit
        """
        self.errors.append(str(error))

    def run(self):
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
                data=request_data)
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
                data=request_data)
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
        return False, self.json_out

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
        return True, self.json_out

    def export_results(self, data, export_dir, export_filename):
        """
        Export the JSON data in output_file
        """
        os.makedirs(export_dir)

        result_filename = os.path.join(export_dir, export_filename)

        with open(result_filename, "w") as f:
            json.dump(data, f, indent=4, separators=(",", ": "))


if __name__ == "__main__":
    # configure_logging()
    command = sys.argv[1]
    scanner = AnalyticsIntegration(scan_type=command)
    status, output = scanner.run()
    print ("Scanner execution status: {}".format(status))
    print ("api_status_code: {}".format(output.get(
        "api_status_code",
        "Unable to retrieve status code!")))
    scanner.export_results(output, ".", scanner.result_file)
