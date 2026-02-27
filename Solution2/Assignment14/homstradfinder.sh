#!/bin/bash

Homstrad_Dir="/mnt/extstud/praktikum/bioprakt/Data/HOMSTRAD"

find "$Homstrad_Dir" -file \( -name "*.ali"\) | while read file
do
  python3 Homstrad.py "$file"
done
