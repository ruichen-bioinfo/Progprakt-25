#!/usr/bin/env python3
import argparse
import re
import urllib.request

URL = "https://ftp.ncbi.nlm.nih.gov/genomes/GENOME_REPORTS/prokaryotes.txt"

def find_index(header_lower, wanted_words):
    # sucht eine Spalte, die alle Wörter enthält
    for i, h in enumerate(header_lower):
        ok = True
        for w in wanted_words:
            if w not in h:
                ok = False
                break
        if ok:
            return i
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--organism", nargs="+", required=True)
    parser.add_argument("--source", default=URL)
    args = parser.parse_args()

    patterns = [re.compile(p) for p in args.organism]

    # Datei laden
    if args.source.startswith(("ftp://", "http://", "https://")):
        with urllib.request.urlopen(args.source) as f:
            lines = f.read().decode("utf-8", errors="ignore").splitlines()
    else:
        with open(args.source, encoding="utf-8", errors="ignore") as f:
            lines = f.read().splitlines()

    # Header finden (erste Zeile mit #)
    header_i = None
    for i, line in enumerate(lines):
        if line.startswith("#"):
            header_i = i
            break
    if header_i is None or header_i + 1 >= len(lines):
        raise SystemExit("Kein Header gefunden.")

    h1 = lines[header_i].lstrip("#")
    h2 = lines[header_i + 1]

    # Tabs oder fixed-width?
    tab_mode = ("\t" in h1)

    if tab_mode:
        # Header zusammensetzen (2 Zeilen)
        a = h1.split("\t")
        b = h2.split("\t")

        header = []
        for x, y in zip(a, b):
            x = x.strip()
            y = y.strip()
            if x and y:
                header.append(x + " " + y)
            else:
                header.append(x or y)

        header_lower = [x.strip().lower() for x in header]

        org_index = find_index(header_lower, ["organism"])
        size_index = find_index(header_lower, ["size", "mb"])
        status_index = find_index(header_lower, ["status"])

        if org_index is None or size_index is None or status_index is None:
            raise SystemExit("Spalten nicht gefunden (Organism, Size (Mb), Status).")

        for line in lines:
            if line.startswith("#") or not line.strip():
                continue

            cols = line.split("\t")
            if len(cols) <= max(org_index, size_index, status_index):
                continue

            organism = cols[org_index].strip()
            status = cols[status_index].strip()
            size_s = cols[size_index].strip()

            # Nur vollständige Genome
            if status != "Complete Genome":
                continue

            if not any(r.search(organism) for r in patterns):
                continue

            try:
                size = float(size_s.replace(",", "."))
            except ValueError:
                continue

            print(f"{organism}\t{size}")

    else:
        # fixed-width: Spaltenpositionen aus Header holen
        starts = []
        name1 = {}
        name2 = {}

        for m in re.finditer(r"\S+", h1):
            starts.append(m.start())
            name1[m.start()] = m.group(0)

        for m in re.finditer(r"\S+", h2):
            name2[m.start()] = m.group(0)

        starts = sorted(starts)

        cols_info = []
        for k, s in enumerate(starts):
            e = starts[k + 1] if k + 1 < len(starts) else None
            colname = (name1.get(s, "") + " " + name2.get(s, "")).strip().lower()
            cols_info.append((colname, s, e))

        def get_value(line, must_have_words):
            for colname, s, e in cols_info:
                ok = True
                for w in must_have_words:
                    if w not in colname:
                        ok = False
                        break
                if ok:
                    return line[s:e].strip() if e is not None else line[s:].strip()
            return None

        for line in lines:
            if line.startswith("#") or not line.strip():
                continue

            organism = get_value(line, ["organism"])
            size_s = get_value(line, ["size", "mb"])
            status = get_value(line, ["status"])

            if organism is None or size_s is None or status is None:
                continue

            # Nur vollständige Genome
            if status != "Complete Genome":
                continue

            if not any(r.search(organism) for r in patterns):
                continue

            try:
                size = float(size_s.replace(",", "."))
            except ValueError:
                continue

            print(f"{organism}\t{size}")


def main():

    if 'REQUEST_METHOD' in os.environ:
        # CGI Mode
        cgitb.enable()
        print("Content-Type: text/plain\n") 
        
        form = cgi.FieldStorage()
        

        raw_patterns = form.getlist('organism')
        patterns = []
        
 
        if not raw_patterns and 'organism' in form:
             val = form.getvalue('organism')
             if val: raw_patterns = [val]

        for p in raw_patterns:
            patterns.extend(p.split())
            
        if not patterns:
            print("Error: No organism regex provided.")
            return

        process_search(patterns, DEFAULT_URL)
        
    else:
        #CLI Mode 
    
        parser = argparse.ArgumentParser()
        parser.add_argument("--organism", nargs="+", required=True)
        parser.add_argument("--source", default=DEFAULT_URL)
        args = parser.parse_args()

        process_search(args.organism, args.source)

        
if __name__ == "__main__":
    main()
