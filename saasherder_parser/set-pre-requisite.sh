#!/bin/bash
yum install python-pip || exit 1
pip install --upgrade pip || exit 1
git clone https://github.com/openshiftio/saasherder
cd saasherder
pip install -v -r requirements.txt ||cd ../ && exit 1
python setup.py install || cd ../ && exit 1
cd ../
git clone https://github.com/openshiftio/saas-openshiftio
git clone https://github.com/openshiftio/saas-analytics
git clone https://github.com/openshiftio/saas-launchpad
git clone https://github.com/openshiftio/saas-chat
