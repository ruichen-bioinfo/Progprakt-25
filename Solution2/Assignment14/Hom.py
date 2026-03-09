#!/usr/bin/env python3

import time
print("Content-type:text/html\n\n")
start = time.time()
print("A", time.time() - start)
import subprocess
print("C", time.time() - start)

import sys
import mysql.connector
from db_config import DB_CONFIG

if len(sys.argv) < 2:
    print("Usage: script.py <pdb_id>")
    sys.exit(1)

pdb1 = sys.argv[1].lower()

cnx = mysql.connector.connect(**DB_CONFIG)
cursor = cnx.cursor()

query = """
SELECT af.family_name,
       am.seq_id,
       am.aligned_sequence,
       am.secondary_structure
FROM alignment_family af
JOIN alignment_member am ON af.id = am.family_id
WHERE am.seq_id = %s
"""

cursor.execute(query, (pdb1,))

for family_name, seq_id, ali, sec in cursor:
    print("Family:", family_name)
    print("SeqID :", seq_id)
    print(ali)
    print(sec)
    print()

cnx.close()
