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
Keywords = []
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

        if line.startswith("SQ"):
            continue

        if line.startswith("     "):
            seq += line.strip().replace(" ", "")

        if spKuerzel == "KW":
            Keywords.extend(Inhalt.split(";"))

try:
    cnx = mysql.connector.connect(**DB_CONFIG)
    cursor = cnx.cursor()
except mysql.connector.Error as err:
    print(f"Connection failed: {err}")
    sys.exit(1)


#CHECKEN OB SCHON IN DATENBANK DRIN!
sql = "SELECT id FROM sequences WHERE accession=%s AND source=%s AND seq_type=%s"
werte = (accessionNumber, source, type)
cursor.execute(sql, werte)
result = cursor.fetchone()

if result is None:
    sql = "INSERT INTO sequences (accession, source, seq_type, organism, sequence, length, description,gene_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

    werte = (accessionNumber, source, type, osname, seq, seqlength, description, genename)
    cursor.execute(sql, werte)
    seq_id = cursor.lastrowid

else:
    seq_id = result[0]

for keyword in Keywords:
    keyword = keyword.strip().rstrip(".")
    if keyword == "":
        continue

    cursor.execute("""
        INSERT INTO keywords (keyword)
        VALUES (%s)
        ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)
    """, (keyword,))

    kw_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO seq_keywords (seq_id, kw_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE seq_id = seq_id
    """, (seq_id, kw_id))

cnx.commit()

print("Rows inserted:", cursor.rowcount)
if cursor.rowcount == 0:
    print(f"{accessionNumber} already in DB")
else:
    print(f"sequence added: {accessionNumber}")
cursor.close()
cnx.close()

