#!/bin/bash
echo -e $3 |mail -r images-scan@redhat.com -c images-scan@redhat.com -S smtp=smtp://smtp.corp.redhat.com -s "$1" $4 $2
