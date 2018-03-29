#!/bin/bash
echo -e $3 |mail -r nshaikh@redhat.com -S smtp=smtp://smtp.corp.redhat.com -s "$1" $2 -a $4
