#!/usr/bin/env python3
import argparse
import sys
from tkinter.constants import INSERT

import mysql.connector
from db_config import DB_CONFIG


parser = argparse.ArgumentParser()
parser.add_argument("--input")
args = parser.parse_args()
spInput = args.input

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
        if spKuerzel == "ID":
            parts = Inhalt.split()
            seqname = parts[0]
            seqlength = int(parts[2])

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

        if spKuerzel == "SQ" or spKuerzel == "  ":
            seq += Inhalt

try:
    cnx = mysql.connector.connect(**DB_CONFIG)
    cursor = cnx.cursor()
except mysql.connector.Error as err:
    print(f"Connection failed: {err}")
    sys.exit(1)

sql = "INSERT INTO sequences (accession, source, organism, sequence, length, description) VALUES (%s, %s, %s, %s, %s, %s)"
werte = (accessionNumber, source, osname, seq, seqlength, description)

print("vor Execute")
cursor.execute(sql, werte)
print("nach Ececute")
cnx.commit()

print("nach Insert")
cursor.close()
cnx.close()

