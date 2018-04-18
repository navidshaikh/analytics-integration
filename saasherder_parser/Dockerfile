FROM registry.centos.org/centos/centos:latest

RUN yum -y update; \
    yum -y install git python-setuptools python-dateutil; \
    yum clean all

WORKDIR /opt/saasherder

ADD set-pre-requisite.sh get_repo_details_from_image.sh repo_list /opt/saasherder/

RUN bash set-pre-requisite.sh

ENTRYPOINT ["./get_repo_details_from_image.sh"]
