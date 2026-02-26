#!/usr/bin/env python3
import mysql.connector
import sys
from db_config import DB_CONFIG




# python3 get_seq.py --id P12345,P67890 --source Uniprot [--output out.fasta]
id_list = None
source = None
output_file = None

i = 1
while i < len(sys.argv):
    if sys.argv[i] == '--id':
        i += 1
        id_list = sys.argv[i].split(',')   # divided by , after each like ['P12345', 'P67890']
    elif sys.argv[i] == '--source':
        i += 1
        source = sys.argv[i]
    elif sys.argv[i] == '--output':
        i += 1
        output_file = sys.argv[i]
    else:
        print(f"Unknown: {sys.argv[i]}")
        sys.exit(1)
    i += 1

# Params check
if id_list is None or source is None:
    print(" python3 get_seq.py --id <key1,key2,...> --source <source> [--output <outfile>]")
    sys.exit(1)

# Connect to DB
try:
    cnx = mysql.connector.connect(**DB_CONFIG)
    cursor = cnx.cursor()
except mysql.connector.Error as err:
    print(f"Connection failed: {err}")
    sys.exit(1)

# Output file
if output_file:
    out = open(output_file, 'w')
else:
    out = sys.stdout

# track id in DB
for key in id_list:
    key = key.strip()
    query = "SELECT accession, sequence FROM sequences WHERE source = %s AND accession = %s"
    cursor.execute(query, (source, key))
    result = cursor.fetchone()
    if result:
        acc, seq = result
        out.write(f">{acc}\n")
        for i in range(0, len(seq), 80):
            out.write(seq[i:i + 80] + '\n')
    else:
        out.write(f"> {key} not found in {source}\n")


cursor.close()
cnx.close()
if output_file:
    out.close()
