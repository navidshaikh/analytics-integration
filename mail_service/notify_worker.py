#!/usr/bin/env python

import json
import logging
import os
import subprocess

import beanstalkc
# importing config present at root of repository
from config import ALERTS

from scanning.lib.log import load_logger

load_logger()

logger = logging.getLogger('mail-service')

bs = beanstalkc.Connection(host="0.0.0.0")
bs.watch("notify")

SCANNERS_STATUS = "scanners_status.json"
SUBJECT = "[osio-scan]{}: Report for {}"
EMAIL_HEADER = "Atomic scanners report for image: {}"


class NotifyUser(object):
    "Compose and send build status, linter and scanners results"

    def __init__(self, job_info):
        self.alerts = ALERTS

        self.send_mail_command = \
            "/opt/scanning/mail_service/send_mail.sh"
        self.job_info = job_info

        self.image_under_test = job_info.get("image_under_test")

        # the logs directory
        self.logs_dir = self.job_info["logs_dir"]

        # scanners execution status file
        self.scanners_status_file = os.path.join(
            self.logs_dir, SCANNERS_STATUS)

        self.scanners_status = self._read_status(self.scanners_status_file)

    def _escape_text_(self, text):
        "Escapes \n,\t with \\n,\\tt for rendering in email body"

        return text.replace("\n", "\\n").replace("\t", "\\t")

    def send_email(self, subject, contents, attachments):
        "Sends email to user"
        to_emails = " ".join(
            email for email in self.job_info.get("notify_email"))
        subprocess.call([
            self.send_mail_command,
            subject,
            to_emails,
            self._escape_text_(contents),
            attachments])

    def _read_status(self, filepath):
        "Method to read status JSON files"
        try:
            fin = open(filepath)
        except IOError as e:
            logger.warning("Failed to read %s file, error: %s" %
                           (filepath, str(e)))
            return None
        else:
            return json.load(fin)

    def _read_text_file(self, text_file):
        "Method to read text files"

        try:
            fin = open(text_file)
        except IOError as e:
            logger.warning("Failed to read %s file, error: %s" %
                           (text_file, str(e)))
            return None
        else:
            return fin.read()

    def _dump_logs(self, logs, logfile):
        "Method to dump logs into logfile"

        try:
            # open in append mode, if there are more logs already
            fin = open(logfile, "a+")
        except IOError as e:
            logger.warning("Failed to open %s file in append mode. Error: %s"
                           % (logfile, str(e)))
        else:
            fin.write(logs)

    def _separate_section(self, char="-", count=99):
        " Creates string with char x count and returns"

        return char * count

    def compose_email_subject(self):
        " Composes email subject "
        repo_parts = self.split_repo_name(self.image_under_test)
        image = repo_parts.get("image", "")
        image = image.replace("osio-prod/", "")
        if not image:
            image = self.image_under_test
        if self.problem:
            return SUBJECT.format("PROBLEM", image)
        else:
            return SUBJECT.format("OK", image)

    def compose_scanners_summary(self):
        "Composes scanners result summary"

        if not self.scanners_status:
            # TODO: Better handling and reporting here
            return ""

        text = ""
        for scanner in self.scanners_status["logs_file_path"]:
            text += scanner + ":\n"
            text += self.scanners_status["msg"][scanner] + "\n"
            text += "Detailed logs: check attached file "
            text += os.path.basename(
                self.scanners_status["logs_file_path"][scanner])
            text += "\n\n"

        return text

    def compose_email_contents(self):
        "Aggregates contents from different modules and composes one email"
        repo_parts = self.split_repo_name(self.image_under_test)
        image = repo_parts.get("image", "")
        image = image.replace("osio-prod/", "")
        if not image:
            image = self.image_under_test

        text = EMAIL_HEADER.format(image)
        # new line and separate section with hyphens
        text += "\n" + self._separate_section()

        text += "\n" + self.compose_scanners_summary() + "\n"
        return text

    def get_attachments(self):
        return " ".join(
            ["-a {}".format(a) for a in
             self.scanners_status["logs_file_path"].values()])

    def is_problem_in_reports(self):
        """
        Go through scanners status file and find out if there are problems
        """
        for scanner, alert in self.scanners_status.get(
                "alert", {}).iteritems():
            if alert:
                return True
        return False

    def notify_user(self):
        """
        Main method to orchestrate the email body composition
        and sending email
        """
        self.problem = self.is_problem_in_reports()
        subject = self.compose_email_subject()
        email_contents = self.compose_email_contents()
        attachments = self.get_attachments()
        # send email
        logger.info("Sending email to user %s" %
                    self.job_info["notify_email"])

        if "ok" in self.alerts:
            self.send_email(subject, email_contents, attachments)
        if "probelm" in self.alerts and self.problem:
            self.send_email(subject, email_contents, attachments)

    def remove_status_files(self, status_files):
        "Removes the status file"
        logger.debug("Cleaning statuses files %s" % str(status_files))
        for each in status_files:
            try:
                os.remove(each)
            except OSError as e:
                logger.info("Failed to remove file: %s , error: %s" %
                            (each, str(e)))

    def split_repo_name(self, repo_name):
        """
        Split given repository names
        """
        if not repo_name:
            return {}

        parts = repo_name.split("/")

        if len(parts) == 1:
            # case for foo:latest
            registry = None
            image = repo_name
        elif len(parts) == 2:
            # check if part[0] is a registry
            if "." in parts[0] or ":" in parts[0]:
                # case for r.c.o/foo:latest
                registry = parts[0]
                image = parts[1]
            else:
                # case for foo/bar:latest
                registry = None
                image = repo_name

        # for cases where len(parts) > 2
        else:
            # check if part[0] is a registry
            if "." in parts[0] or ":" in parts[0]:
                # case for r.c.o/foo/bar:latest
                registry = parts[0]
                image = "/".join(parts[1:])
            else:
                # case for prod/foo/bar:latest
                registry = None
                image = repo_name

        # now process tags
        image_parts = image.split(":")
        if len(image_parts) == 2:
            # case for foo:tag1, foo/bar:tag1, prod/foo/bar:latest
            image_name = image_parts[0]
            tag = image_parts[1]
        else:
            # cases for foo , foo/bar, prod/foo/bar
            image_name = image
            # use default tag
            tag = "latest"
        return {"registry": registry, "image": image,
                "image_name": image_name, "tag": tag}


while True:
    logger.debug("Listening to notify_user tube")
    job = bs.reserve()
    job_id = job.jid
    job_info = json.loads(job.body)
    logger.info("Received Job: {}".format(str(job_info)))
    try:
        notify_user = NotifyUser(job_info)
        notify_user.notify_user()
    except Exception as e:
        logger.critical(
            "Mail server could not process the job: {} with error : {}"
            .format(str(job_info), e))
    finally:
        job.delete()
