#!/bin/bash
export REPLYTO=nshaikh@redhat.com
mkfifo /var/spool/postfix/public/pickup
postfix start
sleep 20
python /root/analytics-integration/mail_service/worker_notify_user.py
