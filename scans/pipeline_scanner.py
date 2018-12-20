#!/usr/bin/python
"""pipeline scanner class."""

from scanning.scanners.base import Scanner


class PipelineScanner(Scanner):
    """pipeline-scanner atomic scanner handler."""

    def __init__(self):
        self.scanner = "pipeline-scanner"
        self.result_file = "pipeline_scanner_results.json"

    def run(self, image):
        """
        Run the given scanner
        """
        super(PipelineScanner, self).__init__(
            image=image,
            scanner=self.scanner,
            result_file=self.result_file)
        self.mount_image()
        data = self.scan(rootfs=True, process_output=False)

        # invoke base class's cleanup utility, also unmount
        self.cleanup(unmount=True)

        return self.process_output(data)

    def process_output(self, json_data):
        """
        Process output based on its content.

        Process the output from the scanner, parse the json and
        add meaningful information based on validations
        """
        data = {}
        data["image_under_test"] = self.image
        data["scanner"] = self.scanner
        data["alert"] = False
        # if status of execution as False
        if not json_data.get("status", False):
            data["msg"] = "Failed to run the scanner."
            data["logs"] = {}
            return data

        # actual results are present inside json_data["logs"]
        logs = json_data.get("logs", {})

        # if check if there are available package updates
        if logs.get("Scan Results", {}).get("Package Updates", []):
            msg = "RPM updates available for the image.\n Updates:\n"
            for update in logs.get("Scan Results").get("Package Updates"):
                msg = msg + update + "\n"
            data["msg"] = msg
            # We are not counting RPM updates as alerts for now
            data["alert"] = False
        else:
            data["msg"] = "No updates required."

        data["logs"] = logs
        return data
