#!/usr/bin/env python3


import re
import sys
import argparse
import urllib.request
import os
import cgi
import cgitb

DEFAULT_URL = "ftp://ftp.ncbi.nlm.nih.gov/genomes/GENOME_REPORTS/prokaryotes.txt"

def find_column_index(header_words, keywords):

    for i, h in enumerate(header_words):
        h_lower = h.lower()
        if all(kw.lower() in h_lower for kw in keywords):
            return i
    return None

def parse_header(header_line1, header_line2):

    if '\t' in header_line1:

        col1 = header_line1.strip('#').split('\t')
        col2 = header_line2.split('\t')

        header = []
        for a, b in zip(col1, col2):
            a = a.strip()
            b = b.strip()
            if a and b:
                header.append(f"{a} {b}")
            else:
                header.append(a or b)
        return header, True, None
    else:

        starts = []
        name1 = {}
        name2 = {}

        for m in re.finditer(r'\S+', header_line1):
            starts.append(m.start())
            name1[m.start()] = m.group(0)

        for m in re.finditer(r'\S+', header_line2):
            name2[m.start()] = m.group(0)
        starts.sort()

        col_info = []
        for i, s in enumerate(starts):
            e = starts[i+1] if i+1 < len(starts) else None
            col_name = (name1.get(s, '') + ' ' + name2.get(s, '')).strip()
            col_info.append((col_name.lower(), s, e))
        return col_info, False, None

def extract_value_fixed_width(line, col_info, keywords):

    for col_name, s, e in col_info:
        if all(kw in col_name for kw in keywords):
            return line[s:e].strip() if e else line[s:].strip()
    return None

def process_search(patterns, source_url_or_file):

    try:
        if source_url_or_file.startswith(('ftp://', 'http://', 'https://')):
            with urllib.request.urlopen(source_url_or_file) as resp:
                lines = resp.read().decode('utf-8', errors='ignore').splitlines()
        else:
            with open(source_url_or_file, encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
    except Exception as e:
        print(f"Error reading data: {e}", file=sys.stderr)
        sys.exit(1)

    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith('#'):
            header_idx = i
            break
    if header_idx is None or header_idx + 1 >= len(lines):
        print("No valid header found.", file=sys.stderr)
        sys.exit(1)

    h1 = lines[header_idx].lstrip('#')
    h2 = lines[header_idx + 1]


    if '\t' in h1:

        header, is_tab, _ = parse_header(h1, h2)

        org_idx = find_column_index(header, ['organism'])
        size_idx = find_column_index(header, ['size', 'mb'])
        status_idx = find_column_index(header, ['status'])
        if org_idx is None or size_idx is None or status_idx is None:
            print("Could not find required columns (Organism, Size(Mb), Status).", file=sys.stderr)
            sys.exit(1)

        
        for line in lines[header_idx+2:]:
            line = line.rstrip('\n')
            if not line or line.startswith('#'):
                continue
            cols = line.split('\t')
            if len(cols) <= max(org_idx, size_idx, status_idx):
                continue
            organism = cols[org_idx].strip()
            status = cols[status_idx].strip()
            size_str = cols[size_idx].strip()
            if status != 'Complete Genome':
                continue

            if not any(p.search(organism) for p in patterns):
                continue
            try:
                size = float(size_str.replace(',', '.'))
            except ValueError:
                continue
            print(f"{organism}\t{size}")
    else:
     
        col_info, _, _ = parse_header(h1, h2) 

        for line in lines[header_idx+2:]:
            line = line.rstrip('\n')
            if not line or line.startswith('#'):
                continue
            organism = extract_value_fixed_width(line, col_info, ['organism'])
            status = extract_value_fixed_width(line, col_info, ['status'])
            size_str = extract_value_fixed_width(line, col_info, ['size', 'mb'])
            if organism is None or status is None or size_str is None:
                continue
            if status != 'Complete Genome':
                continue
            if not any(p.search(organism) for p in patterns):
                continue
            try:
                size = float(size_str.replace(',', '.'))
            except ValueError:
                continue
            print(f"{organism}\t{size}")

def main():
    if 'REQUEST_METHOD' in os.environ:
        # CGI mode
        cgitb.enable()
        print("Content-Type: text/plain\n")
        form = cgi.FieldStorage()

        raw = form.getvalue('organism', '')
        if not raw:
            print("Error: No organism regex provided.")
            return
        patterns = []
        for part in raw.split():
            try:
                patterns.append(re.compile(part))
            except re.error as e:
                print(f"Invalid regex: {part} ({e})")
                return
        process_search(patterns, DEFAULT_URL)
    else:
        # Command line mode
        parser = argparse.ArgumentParser(description='Search prokaryotes.txt for complete genomes matching regex patterns.')
        parser.add_argument('--organism', nargs='+', required=True,
                            help='Regular expression(s) for organism name')
        parser.add_argument('--source', default=DEFAULT_URL,
                            help='Path or URL to prokaryotes.txt (default: NCBI FTP)')
        args = parser.parse_args()
        patterns = []
        for p in args.organism:
            try:
                patterns.append(re.compile(p))
            except re.error as e:
                print(f"Invalid regex: {p} ({e})", file=sys.stderr)
                sys.exit(1)
        process_search(patterns, args.source)

if __name__ == '__main__':
    main()