#!/usr/bin/env python3
import argparse
import sys
from tkinter.constants import INSERT

import mysql.connector
from db_config import DB_CONFIG


parser = argparse.ArgumentParser()
parser.add_argument("--Input")
args = parser.parse_args()
spDatei = args.Input

osname = ""
source = "Swiss Prot"
description = ""
function = ""
oscategory = ""
seq = ""
with open (spInput, "r") as f:
    for line in f:
        spKuerzel = line[0:2]
        Inhalt = line[2:].strip()
        if spKuerzel[0] == "ID":
            seqname = Inhalt.split(" ")[0]
            seqlength = Inhalt.split(";")[1].strip()

        if spKuerzel == "AC":
            #AccessionNumber ist primärer Schlüssel für Datenbank
            accessionNumber = Inhalt.split(";")[0]

        if spKuerzel == "OS":
            osname += Inhalt

        if spKuerzel == "DE":
            description += Inhalt

        if spKuerzel == "CC":
            function += Inhalt

        if spKuerzel == "OC":
            oscategory += (spKuerzel[1])

        if spKuerzel == "SQ":
            sq = True

        if spKuerzel == "//":
            sq = False

        while sq:
            seq += Inhalt

try:
    cnx = mysql.connector.connect(**DB_CONFIG)
    cursor = cnx.cursor()
except mysql.connector.Error as err:
    print(f"Connection failed: {err}")
    sys.exit(1)

sql = "INSERT INTO sequences (source, organism, sequence, length, description) VALUES (%s, %s, %s, %s, %s)"
werte = f"{source}, {osname}, {seq}, {seqlength} {description}"

cursor.execute(sql, werte)


cursor.close()
cnx.close()

