#!/bin/bash
echo -e $3 |mail -r nshaikh@redhat.com -c nshaikh@redhat.com -c bkundu@redhat.com -c aagshah@redhat.com -c schoudhu@redhat.com -S smtp=smtp://smtp.corp.redhat.com -s "$1" $4 $2
