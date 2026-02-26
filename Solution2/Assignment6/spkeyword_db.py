#!/usr/bin/env python3
import sys
import argparse
import mysql.connector
from db_config import DB_CONFIG

DB_PATH = "/mnt/extstud/praktikum/bioprakt/Data/swissprot45.dat"

def search_keywords_in_file(keywords, file_handle):
    # same as before: parse Swissprot file, return list of ACs
    query = set(k.lower() for k in keywords)
    results = set()
    current_ac = []
    current_kw = []
    for line in file_handle:
        line = line.rstrip("\n")
        if line.startswith("ID"):
            current_ac = []
            current_kw = []
        elif line.startswith("AC"):
            parts = line[5:].strip().split(';')
            for p in parts:
                if p.strip():
                    current_ac.append(p.strip())
        elif line.startswith("KW"):
            kw_line = line[5:].strip().rstrip('.')
            parts = kw_line.split(';')
            for p in parts:
                if p.strip():
                    current_kw.append(p.strip().lower())
        elif line.startswith("//"):
            if any(q in current_kw for q in query):
                results.update(current_ac)
    return sorted(results)

def search_keywords_in_db(keywords):
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()
    except mysql.connector.Error as err:
        print(f"DB error: {err}", file=sys.stderr)
        sys.exit(1)

    placeholders = ','.join(['%s'] * len(keywords))
    sql = f"""
        SELECT DISTINCT s.accession
        FROM sequences s
        JOIN seq_keywords sk ON s.id = sk.seq_id
        JOIN keywords k ON sk.kw_id = k.id
        WHERE s.source = 'Uniprot'
          AND LOWER(k.keyword) IN ({placeholders})
    """
    cursor.execute(sql, [kw.lower() for kw in keywords])
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()
    return [r[0] for r in rows]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyword", nargs="+", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--swissprot", help="Swissprot file")
    group.add_argument("--db", action="store_true", help="use database")
    args = parser.parse_args()

    if args.db:
        results = search_keywords_in_db(args.keyword)
    else:
        with open(args.swissprot, 'r', encoding='latin-1') as f:
            results = search_keywords_in_file(args.keyword, f)

    for ac in results:
        print(ac)

if __name__ == "__main__":
    main()
