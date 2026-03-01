#!/usr/bin/env python3
import argparse
import sys
from tkinter.constants import INSERT
from pathlib import Path
import mysql.connector
from db_config import DB_CONFIG
import re

try:
    cnx = mysql.connector.connect(**DB_CONFIG)
    cursor = cnx.cursor()
except mysql.connector.Error as err:
    print(f"Connection failed: {err}")
    sys.exit(1)

def insertseq(family_id, current_seq_id, current_sequence, start, end, chain):


    cursor.execute("""
            INSERT INTO alignment_member
        (family_id, seq_id, aligned_sequence, start_in_seq, end_in_seq, chain_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        aligned_sequence = VALUES(aligned_sequence),
        start_in_seq = VALUES(start_in_seq),
        end_in_seq = VALUES(end_in_seq)
""",
     (
            family_id,
            current_seq_id,
            current_sequence,
            start,
            end,
            chain
            ))


HOMSTRAD_DIR = Path("/mnt/extstud/praktikum/bioprakt/Data/HOMSTRAD")

for folder in HOMSTRAD_DIR.iterdir():

    if folder.is_dir():
        ali_files = list(folder.glob("*.ali"))
        tem_files = list(folder.glob("*.tem"))

        for ali_file in ali_files:


            print(ali_file)
            family = ""
            aliclass = ""
            domain = ""
            seq_id = ""
            pdb_id = ""
            chain = ""


            mapping = {}

            with open (ali_file, "r") as f:
                lines = f.readlines()
                i = 0

                #erste Schleife für Header Zeilen
                while i < len(lines) and not lines[i].startswith(">P1"):
                    line = lines[i]

                    kuerzel = line[0:2]
                    content = line[3:].strip()

                    if kuerzel == "C;":
                        if content.startswith("family:"):
                            family = content.split(":", 1)[1].strip()

                        elif content.startswith("class:"):
                            class_name = content.split(":", 1)[1].strip()

                        elif content.startswith("domain:"):
                            domain = "0"
                        elif content.startswith("type"):
                            typeName = "0"

                        elif ":" in content:
                            left, combined = content.split(":", 1)
                            left_parts = left.split()

                            if len(left_parts) == 2 and len(left_parts[0]) == 4:
                                pdb_id = left_parts[0]
                                chain = left_parts[1]

                                if chain == "-":
                                    chain = None
                                else:
                                    chain = chain.upper()

                                seq_id = combined.strip()

                                mapping[seq_id] = (pdb_id, chain)
                    i += 1

                cursor.execute("""
                        INSERT INTO alignment_family (family_name, family_description)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)
                        """, (family, None))

                family_id = cursor.lastrowid




                #Dieser Teil für die Sequenzen
                current_seq_id = None
                start = None
                end = None
                current_sequence = ""

                while i < len(lines):
                    line = lines[i].strip()

                    if line.startswith(">P1"):
                        if current_seq_id:
                           insertseq(family_id, current_seq_id,
                                     current_sequence, start, end, chain)
                        current_seq_id = line.strip().split(";")[1]
                        current_sequence = ""
                        start = None
                        end = None

                        if current_seq_id in mapping:
                            pdb_id, chain = mapping[current_seq_id]
                        else:
                            pdb_id, chain = None, None


                    elif line.startswith("structureX"):
                        parts = line.split(":")
                        start_str = parts[2].strip()
                        m = re.match(r"\d+", start_str)
                        if m:
                            start = int(m.group())
                        else:
                            start = None
                        end_str = parts[4].strip()
                        m2 = re.match(r"\d+", end_str)
                        if m2:
                            start = int(m2.group())
                        else:
                            start = None

                    elif current_seq_id:

                        seq_line = line.strip()
                        if seq_line.endswith("*"):
                            current_sequence += seq_line[:-1]
                        else:
                            current_sequence += seq_line
                    i += 1

                if current_seq_id:
                    insertseq(family_id, current_seq_id,
                              current_sequence, start, end, chain)





            for tem_file in tem_files:
                print(tem_file)


                with open (tem_file, "r") as f:
                    cseq_id = None
                    secondary_structure = None
                    reading = False
                    for line in f:
                        line = line.strip()
                        if line.startswith(">P1"):
                            if cseq_id and secondary_structure:
                                cursor.execute("""
                                                    UPDATE alignment_member
                                                    SET secondary_structure = %s
                                                    WHERE family_id = %s AND seq_id = %s
                                                """, (secondary_structure, family_id, cseq_id))

                            cseq_id = line.split(";")[1]
                            secondary_structure = ""
                            reading = False

                        elif line.startswith("secondary"):
                            reading = True

                        elif reading:
                            structure_line = line.strip()
                            if structure_line.endswith("*"):
                                secondary_structure += structure_line[:-1]
                                reading = False
                            else:

                                secondary_structure += structure_line

                    if cseq_id and secondary_structure:
                        cursor.execute("""
                                    UPDATE alignment_member
                                    SET secondary_structure = %s
                                    WHERE family_id = %s AND seq_id = %s
                                """, (secondary_structure, family_id, cseq_id))



cnx.commit()