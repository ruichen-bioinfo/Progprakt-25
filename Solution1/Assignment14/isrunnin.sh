#!/bin/bash
process=$1
user=$2
pgrep -u "$user" -x "$process" >/dev/null
if [ $? -eq 0 ] ; then
exit 1
else
exit 0
fi
