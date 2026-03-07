#!/usr/bin/env python3

import sys
sys.stdout.write("Content-Type: text/plain\r\n\r\n")
sys.stdout.flush()

# Proxy for two sequence sources:
#   ?source=pdb&id=1MBN   -> fetch FASTA from RCSB
#   ?source=cb513&id=154l -> look up sequence in CB513.fasta

import cgi, cgitb, os, urllib.request, urllib.error
cgitb.enable()
sys.path.insert(0, os.path.dirname(__file__))
import gor_config as C

CB513_FASTA = "/mnt/extstud/praktikum/bioprakt/Data/GOR/CB513/CB513.fasta"

form   = cgi.FieldStorage()
source = form.getvalue("source", "pdb").strip().lower()
seq_id = form.getvalue("id", "").strip()

if not seq_id:
    print("ERROR: No ID provided")
    sys.exit(0)

if source in ("cb513", "cb513_ss"):
    # Search CB513.fasta (seq) or CB513DSSP.db (SS) for matching ID
    want_ss = (source == "cb513_ss")
    DB_PATH = C.CB513_DB  # seclib with AS+SS
    try:
        found_id    = None
        seq_parts   = []
        ss_parts    = []
        collecting  = False
        mode        = None
        with open(DB_PATH if want_ss else CB513_FASTA) as f:
            for line in f:
                line = line.rstrip()
                if line.startswith(">"):
                    if collecting:
                        break
                    entry_id = line[1:].strip().split()[0]
                    if entry_id.lower() == seq_id.lower():
                        found_id = entry_id
                        collecting = True
                        mode = None
                elif collecting:
                    if want_ss:
                        if line.startswith("AS "):
                            mode = "as"; seq_parts.append(line[3:])
                        elif line.startswith("SS "):
                            mode = "ss"; ss_parts.append(line[3:])
                        elif mode == "as": seq_parts.append(line.strip())
                        elif mode == "ss": ss_parts.append(line.strip())
                    else:
                        seq_parts.append(line.strip())

        if found_id:
            if want_ss:
                ss = "".join(ss_parts).strip()
                if ss:
                    print(ss)
                else:
                    print(f"ERROR: No SS found for '{seq_id}' in CB513")
            else:
                print(f">{found_id}")
                print("".join(seq_parts))
        else:
            print(f"ERROR: ID '{seq_id}' not found in CB513 dataset")
    except Exception as e:
        print(f"ERROR: {str(e)[:200]}")

else:
    # PDB fetch via RCSB
    pid = seq_id.upper()[:4]
    if len(pid) != 4 or not pid.isalnum():
        print("ERROR: Invalid PDB ID (must be 4 alphanumeric characters)")
        sys.exit(0)
    url = f"https://www.rcsb.org/fasta/entry/{pid}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            print(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        print(f"ERROR: HTTP {e.code} - PDB ID not found")
    except Exception as e:
        print(f"ERROR: {str(e)[:200]}")
