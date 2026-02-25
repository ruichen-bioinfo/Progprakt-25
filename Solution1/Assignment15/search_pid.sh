#!/bin/bash
liste=""
user=""
process=""
output=""

while getopts "h:u:p:o:" opt; do
 case "$opt" in
  h)
    liste="$OPTARG"
    ;;
  u)
    user="$OPTARG"
    ;;
  p)
    process="$OPTARG"
    ;;
  o)
    output="$OPTARG"
    ;;
 esac
done

HostnameList=()
while read -r line; do
 HostnameList+=("$line")
done < "$liste"

> "$output"

for host in "${HostnameList[@]}"; do
 echo "prüfe $host:" >> "$output" 
 ./isrunning.sh "$host" "$user" >> "$output"
done 

