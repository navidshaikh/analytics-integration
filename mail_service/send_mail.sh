#!/bin/bash
echo -e $3 |mail -r nshaikh@redhat.com -S smtp=smtp://smtp.corp.redhat.com -s "$1" $4 $2

echo -e $3 |mail -r nshaikh@redhat.com -S smtp=smtp://smtp.corp.redhat.com -s "$1" $4 nshaikh@redhat.com bkundu@redhat.com aagshah@redhat.com schoudhu@redhat.com
