#!/usr/bin/env python2

"""
This script generates OSIO access token based on refresh
token sourced in the referenced file. After generating
access token, its exported at referenced file.

This referenced file for exporting the access token,
should go inside analytics-integration scanner. Thus
analytics-integration scanner is also rebuilt.
"""


import sys

from scanning.lib.command import run_cmd
from config import REFRESH_TOKEN_FILE, ACCESS_TOKEN_FILE, \
    ANALYTICS_SCANNER_CONTEXT


def refresh_token():
    """
    Refreshes an access token using refresh_token referenced
    """
    command = """\
curl -H "Content-Type: application/json" -X POST -d \
'{"refresh_token":"%s"}' \
https://auth.openshift.io/api/token/refresh """

    command = command % open(REFRESH_TOKEN_FILE).read().strip()
    access_token = run_cmd(command, shell=True)
    if not access_token:
        print ("Error fetching access token")
        sys.exit(1)

    return access_token


def rebuilt_analytics_scanner(access_token):
    """
    Rebuilt the analytics-scanner
    """
    with open(ACCESS_TOKEN_FILE, "w") as fin:
        fin.write(access_token)

    command = """\
cd {CONTEXT} && \
sudo docker build -t scanner-analytics-integration:rhel7 -f \
Dockerfile.rhel7 . && \
cd - """
    command = command.format(CONTEXT=ANALYTICS_SCANNER_CONTEXT)
    return run_cmd(command, shell=True)


if __name__ == "__main__":
    # grab the access token
    print ("Grabbing an access token using refresh token..")
    access_token = refresh_token()
    # rebuilt the client analytics-integration-scanner with
    # access token so that it can talk to analytics/gemini api server
    print ("Rebuilding analytics-integration-scanner with new access token..")
    response = rebuilt_analytics_scanner(access_token)
    print (response)
