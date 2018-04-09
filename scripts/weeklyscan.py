#!/usr/bin/env python

"""
This module iniializes the weekly scan by finding out the list of images
on the registry and initializing the scan tasks scan-worker.
"""

import json
import logging

import requests

from scanning.lib.queue import JobQueue
from scanning.lib.log import load_logger
from scanning.lib import settings


class WeeklyScan(object):
    """
    Class for aggregating operations needed to perform weekly scan
    """

    def __init__(self, sub=None, pub=None):
        # configure logger
        self.logger = logging.getLogger('scan-worker')
        # initialize beanstalkd queue connection for scan trigger
        # self.queue = JobQueue(host=settings.BEANSTALKD_HOST,
        #                      port=settings.BEANSTALKD_PORT,
        #                      sub=sub, pub=pub, logger=self.logger)
        # we need registry name for docker pull operations
        self.registry = settings.REGISTRY
        # we need this for REST API calls
        self.reg_url = self.secure_registry()

    def secure_registry(self):
        """
        Checks the config for registry and sets proper registry schema
        """
        if settings.SECURE_REGISTRY:
            return "https://{}".format(self.registry)
        return "http://{}".format(self.registry)

    def get_call(self, url, params=None):
        """
        Performs GET call on given URL

        returns json loaded reposnse and headers
        """
        try:
            r = requests.get(url, params)
        except requests.exceptions.RequestException as e:
            self.logger.critical(
                "Failed to process URL: {} with params: {}".format(
                    url, params))
            self.logger.critical(str(e))
            return None, None
        else:
            try:
                content = json.loads(r.text)
            except ValueError as e:
                self.logger.critical(
                    "Failed to load json from {}".format(r.text))
                return None, None
            else:
                return content,  r.headers

    def find_repos(self, api="{}/v2/_catalog", page=30):
        """
        Find repositories in configured registry

        Returns: list of all images with tags available in registry
                 None if REST calls failed
        """
        # the repositories in registry could grow large in number
        # using pagination for same
        # lets hit registry catalog to get first len(page) repos
        params = {"n": 30}

        # using https:// based registry URL for REST calls
        url = api.format(self.reg_url)

        # call catalog call with parameters for pagination
        resp, headers = self.get_call(url, params)

        # if failed to get repos, return None
        if not resp:
            self.logger.fatal(
                "Failed to retrieve repositories from registry catalog.")
            return None

        # sample response = {"repositories":["repo1", "repo2"]}
        # retrieve repositories from response
        repositories = resp.get("repositories", None)

        # if no repositories are present, return None
        if not repositories:
            self.logger.info(
                "No repositories available in configured registry.")
            return None
        # else, repositories now have a list of <= 30 repos

        # now lets do pagination
        while True:
            next_page = headers.get("Link", None)
            if not next_page:
                break

            # form next page required parameters, need last element last page
            params = {"n": page, "last": repositories[-1]}

            # call next page
            resp, headers = self.get_call(url, params)
            # check if we received repositories
            if not resp:
                self.logger.critical(
                    "Failed to paginate while retrieving repos from registry."
                    "URL: {}, Params: {}".format(url, params))
                self.logger.critical(
                    "Continuing with already retrieved repositories.")
            # if we received next page, add to retrieved repositories
            repositories.extend(resp.get("repositories", []))

        self.logger.info(
            "Total {} repos available in registry.".format(len(repositories)))

        # now return the available repositories
        return repositories

    def subset_repos_on_namespace(self, repos, namespace=[]):
        """
        Return only matching configured namespaced repositories
        """
        srepos = []
        # check if there is a namespace provided else use configured one
        namespace = namespace or settings.TARGET_NAMESPACE
        # no filtering, return all repos
        if not namespace:
            return repos

        for repo in repos:
            if repo.startswith(tuple(namespace)):
                srepos.append(repo)

        # remove duplicates if any
        return list(set(srepos))

    def find_repo_tags(self, repo, api="{}/v2/{}/tags/list"):
        """
        Given a repository name, find the available tags for it
        Returns a list of tags available for given repository
        """
        url = api.format(self.reg_url, repo)
        tags, _ = self.get_call(url)
        if not tags:
            self.logger.critical(
                "Failed to retrieve tags for {}.".format(repo))
            return None
        # reponse has {"name": <image_of_repo>, "tags": ["tag1", "tag2"]}
        return tags["tags"]

    def images_of_repo(self, repo):
        """
        Given a repo name, finds all the tags for repo and form
        URL for images in given repository

        Returns a list of REGISTRY/REPO:TAG available for given repo
        """
        # first find available tags for given repository
        tags = self.find_repo_tags(repo)
        if not tags:
            # return None, if failed to retrieve tags
            return None
        # now form the image registry URL
        # we are using registry URL without https:// for docker pull ops
        url = self.registry + "/" + repo + ":{}"
        images = [url.format(tag) for tag in tags]
        return images

    def run(self):
        """
        Lists all images in given registry with registry URL which is
        compatible with docker pull command (no https://) and puts each
        image for scanning
        """
        repositories = self.find_repos()
        if not repositories:
            return None

        repositories = self.subset_repos_on_namespace(repositories)
        if not repositories:
            return None

        images = []
        for repo in repositories:
            image = self.images_of_repo(repo)
            if not image:
                continue
            self.put_image_for_scanning(image, "/tmp")
            images.extend(image)
        return images

    def put_image_for_scanning(self, image, logs_dir):
        """
        Put the images
        """
        job = {
            "action": "start_scan",
            "weekly": True,
            "image_under_test": image,
            "analytics_server": settings.ANALYTICS_SERVER,
            "notify_email": settings.NOTIFY_EMAILS,
            "logs_dir": logs_dir,
        }
        # self.queue.put(json.dumps(job))


if __name__ == "__main__":
    load_logger()
    ws = WeeklyScan(sub="master_tube", pub="master_tube")
    images = ws.run()
    print len(images)
    with open("prod_devshift_images.txt", "w") as fin:
        fin.write("\n".join([str(image) for image in images]))
