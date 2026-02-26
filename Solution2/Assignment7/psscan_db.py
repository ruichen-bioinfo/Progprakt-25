#!/usr/bin/env python3
import sys
import re
import argparse
import urllib.request
import mysql.connector
from db_config import DB_CONFIG

def to_regex(pattern):
    # same conversion as before
    pattern = pattern.strip().rstrip('.')

    if pattern.startswith('<'):
        pattern = '^' + pattern[1:]
    if pattern.endswith('>'):
        pattern = pattern[:-1] + '$'

    pattern = pattern.replace('-', '')

    pattern = re.sub(r'\{([^\}]+)\}', r'[^\1]', pattern)

    pattern = pattern.replace('(', '{').replace(')', '}')

    pattern = pattern.replace('x', '.')
    return pattern

def get_web_pattern(ps_id):
    if not ps_id.startswith('PS') and ps_id[0].isdigit():
        ps_id = 'PS' + ps_id
    url = "https://prosite.expasy.org/" + ps_id + ".txt"
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
        for line in data.splitlines():
            if line.startswith('PA'):
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1].rstrip('.')
    except:
        pass
    return ""

def read_fasta(handle):
    header = None
    seq = []
    for line in handle:
        line = line.strip()
        if not line:
            continue
        if line.startswith('>'):
            if header:
                yield header, ''.join(seq)
            header = line[1:].strip()
            seq = []
        else:
            seq.append(line)
    if header:
        yield header, ''.join(seq)

def main():
    parser = argparse.ArgumentParser()
    src_group = parser.add_mutually_exclusive_group(required=True)
    src_group.add_argument('--fasta', help="FASTA file (use '-' for stdin)")
    src_group.add_argument('--db', action='store_true', help="search in database")
    pat_group = parser.add_mutually_exclusive_group(required=True)
    pat_group.add_argument('--pattern', help="Prosite pattern")
    pat_group.add_argument('--web', help="Prosite ID e.g. PS00001")
    parser.add_argument('--extern', action='store_true')  # for bonus, unused
    args = parser.parse_args()

    # get pattern string
    pattern_str = ""
    if args.pattern:
        pattern_str = args.pattern
    else:
        pattern_str = get_web_pattern(args.web)
        if not pattern_str:
            sys.stderr.write("Error: could not fetch pattern\n")
            sys.exit(1)

    regex = to_regex(pattern_str)

    if args.db:
        # database search
        try:
            cnx = mysql.connector.connect(**DB_CONFIG)
            cursor = cnx.cursor()
        except mysql.connector.Error as err:
            print(f"DB error: {err}", file=sys.stderr)
            sys.exit(1)

        # use REGEXP and REGEXP_SUBSTR (MariaDB)
        sql = "SELECT accession, sequence FROM sequences WHERE sequence REGEXP %s"
        cursor.execute(sql, (regex,))
        for acc, seq in cursor:
            cursor2 = cnx.cursor()
            cursor2.execute("SELECT REGEXP_SUBSTR(%s, %s)", (seq, regex))
            match = cursor2.fetchone()[0]
            cursor2.close()
            if match:
                print(f"{acc}\t{match}")
        cursor.close()
        cnx.close()
    else:
        # file search
        if args.fasta == '-':
            f_in = sys.stdin
        else:
            try:
                f_in = open(args.fasta, 'r')
            except:
                sys.exit(1)

        search_re = re.compile(f'(?=({regex}))')
        for head, seq in read_fasta(f_in):
            seq_upper = seq.upper()
            for m in search_re.finditer(seq_upper):
                print(f"{head}\t{m.start()+1}\t{m.group(1)}")
        if f_in != sys.stdin:
            f_in.close()

if __name__ == '__main__':
    main()
