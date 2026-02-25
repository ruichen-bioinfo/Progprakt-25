#!/bin/bash

host="$1"

ssh "$host" "cat /proc/loadavg" | awk '{print $1}'
