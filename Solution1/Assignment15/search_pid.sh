#!/bin/bash
liste="$1"
user="$2"
process="$3"
output="$4"

ArrayListe=($liste)

for x in "${ArrayListe[@]}"
do
./isrunning.sh "$x" "$2"
done
