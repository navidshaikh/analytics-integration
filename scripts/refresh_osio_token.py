#!/usr/bin/env python2

"""
This script generates OSIO access token based on refresh
token sourced in the referenced file. After generating
access token, its exported at referenced file.

This referenced file for exporting the access token,
should go inside scanning container for analytics-integration
scanner usage and proper functioning.
"""


import sys

from scanning.lib.command import run_cmd
from config import REFRESH_TOKEN_FILE, ACCESS_TOKEN_FILE


def refresh_token():
    """
    Refreshes an access token using refresh_token referenced
    """
    command = """\
curl -H "Content-Type: application/json" -X POST -d \
'{"refresh_token":"%s"}' \
https://auth.openshift.io/api/token/refresh """

    command = command % open(REFRESH_TOKEN_FILE).read().strip()

    # curl returns a complete json with multiple fields
    # we just want the access_token value (string) inside
    # token dictionary
    command = command + " | jq -r .token.access_token"

    access_token = run_cmd(command, shell=True)
    if not access_token:
        print ("Error fetching access token")
        sys.exit(1)

    return access_token


def rebuild_scanning_container(access_token):
    """
    Rebuilt the scanning container with new OSIO access token
    """
    with open(ACCESS_TOKEN_FILE, "w") as fin:
        fin.write(access_token)

    command = """\
sudo docker build -t scanning:latest -f \
Dockerfiles/Dockerfile.scanning ."""

    return run_cmd(command, shell=True)


if __name__ == "__main__":
    # grab the access token
    print ("Grabbing an access token using refresh token..")
    access_token = refresh_token()
    # rebuilt the client analytics-integration-scanner with
    # access token so that it can talk to analytics/gemini api server
    print ("Rebuilding scanning container with new OSIO access token..")
    response = rebuild_scanning_container(access_token)
    print (response)
