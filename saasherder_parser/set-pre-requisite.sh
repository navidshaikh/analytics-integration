#!/bin/bash
yum install -y python-pip
pip install --upgrade pip
git clone https://github.com/openshiftio/saasherder
cd saasherder && pip install -v -r requirements.txt; python setup.py install
cd ../
git clone https://github.com/openshiftio/saas-openshiftio
git clone https://github.com/openshiftio/saas-analytics
git clone https://github.com/openshiftio/saas-launchpad
git clone https://github.com/openshiftio/saas-chat
