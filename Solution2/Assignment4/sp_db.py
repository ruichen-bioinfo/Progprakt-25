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

genename = ""
osname = ""
source = "SwissProt"
type = "Protein"
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

        if spKuerzel == "KW":
            Keywords = Inhalt.split(";")

try:
    cnx = mysql.connector.connect(**DB_CONFIG)
    cursor = cnx.cursor()
except mysql.connector.Error as err:
    print(f"Connection failed: {err}")
    sys.exit(1)


#CHECKEN OB SCHON IN DATENBANK DRIN!

sql = "INSERT INTO sequences (accession, source, seq_type, organism, sequence, length, description,gene_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

werte = (accessionNumber, source, type, osname, seq, seqlength, description, genename)

print("vor Execute")
cursor.execute(sql, werte)
print("nach Execute")
cnx.commit()

print("nach Insert")
print("Rows inserted:", cursor.rowcount)
cursor.close()
cnx.close()

