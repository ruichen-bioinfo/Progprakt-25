#!/usr/bin/env python3
import mysql.connector
import sys
from db_config import DB_CONFIG

def main():
    id_list = None
    source = None
    output_file = None

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--id':
            i += 1
            if i < len(sys.argv):
                # divide by ,
                id_list = [x.strip() for x in sys.argv[i].split(',') if x.strip()]
        elif sys.argv[i] == '--source':
            i += 1
            if i < len(sys.argv):
                source = sys.argv[i]
        elif sys.argv[i] == '--output':
            i += 1
            if i < len(sys.argv):
                output_file = sys.argv[i]
        else:
            print(f"Ignore Unknown: {sys.argv[i]}")
        i += 1

    if id_list is None or source is None:
        print("Format: python3 get_seq.py --id <key1,key2,...> --source <source> [--output <outfile>]")
        sys.exit(1)

    # Connection to db
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()
    except mysql.connector.Error as err:
        print(f"Databank loss: {err}", file=sys.stderr)
        sys.exit(1)

    # Output
    out = open(output_file, 'w') if output_file else sys.stdout

    # search through key
    query = "SELECT accession, sequence FROM sequences WHERE source = %s AND accession = %s"
    for key in id_list:
        cursor.execute(query, (source, key))
        row = cursor.fetchone()
        if row:
            acc, seq = row
            out.write(f">{acc}\n")
            # change after 80 rows for a new page
            for j in range(0, len(seq), 80):
                out.write(seq[j:j+80] + "\n")
        else:
            # exception when not found
            out.write(f"> {key} ERROR! DOESNT EXIST! {source}\n")

    cursor.close()
    cnx.close()
    if output_file:
        out.close()

if __name__ == '__main__':
    main()
