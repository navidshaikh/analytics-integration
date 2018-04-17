FROM registry.centos.org/centos/centos

RUN yum -y install git

WORKDIR /opt/saasherder

ADD set-pre-requisite.sh get_repo_details_from_image.sh repo_list /opt/saasherder

RUN bash set-pre-requisite.sh

ENTRYPOINT ["./get_repo_details_from_image.sh"]
