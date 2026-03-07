#!/usr/bin/env python3

import sys
sys.stdout.write("Content-Type: text/html\r\n\r\n")
sys.stdout.flush()

# Runs validateGor on the CB513.psipred file and saves results to
# ~/public_html/uploads/psipred_results.json for the Results page to read.
# CB513.psipred uses multi-line AS/SS -- must be preprocessed to single-line
# before validateGor can parse it.

import cgitb, os, subprocess, tempfile, time, html as H, json
cgitb.enable()
sys.path.insert(0, os.path.dirname(__file__))
import gor_config as C

PSIPRED_FILE = "/mnt/extstud/praktikum/bioprakt/Data/GOR/CB513/CB513.psipred"
RESULTS_JSON = os.path.join(C.TMP_DIR, "psipred_results.json")

def parse_multiline_seclib(path):
    """Parse seclib with multi-line AS/SS, return list of (id, seq, ss)."""
    entries = []
    eid = seq_parts = ss_parts = None
    mode = None  # 'as' or 'ss'
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith(">"):
                if eid and seq_parts and ss_parts:
                    entries.append((eid, "".join(seq_parts), "".join(ss_parts)))
                eid = line[1:].strip().split()[0]
                seq_parts = []
                ss_parts  = []
                mode = None
            elif line.startswith("AS "):
                mode = 'as'
                seq_parts.append(line[3:].strip())
            elif line.startswith("SS "):
                mode = 'ss'
                ss_parts.append(line[3:].strip())
            elif line.strip() and mode == 'as' and not line.startswith("SS"):
                seq_parts.append(line.strip())
            elif line.strip() and mode == 'ss':
                ss_parts.append(line.strip())
    if eid and seq_parts and ss_parts:
        entries.append((eid, "".join(seq_parts), "".join(ss_parts)))
    return entries

def write_singleline_seclib(entries, path):
    with open(path, "w") as f:
        for eid, seq, ss in entries:
            f.write(f"> {eid}\nAS {seq}\nSS {ss}\n\n")

def extract_mean(text, label):
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(label + ":") or s.startswith(label + " "):
            parts = s.split("Mean:")
            if len(parts) > 1:
                try: return float(parts[1].strip().split()[0])
                except: pass
    return None

print("""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>PSIPRED Benchmark</title>
<style>
body{font-family:'Segoe UI',sans-serif;background:#f4f7f6;color:#333;padding:2rem;margin:0;}
h2{color:#2c3e50;}h3{color:#2980b9;border-bottom:2px solid #3498db;padding-bottom:6px;}
.card{background:white;border-radius:8px;box-shadow:0 2px 5px rgba(0,0,0,.1);padding:20px;margin-bottom:20px;}
.ok{color:#27ae60}.err{color:#e74c3c}
.back{color:#3498db;text-decoration:none;font-size:.9rem;}
.sgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:12px;margin:14px 0;}
.scard{background:#f8f9fa;border:1px solid #ddd;border-radius:6px;padding:12px;text-align:center;}
.sval{font-size:1.4rem;font-weight:700;color:#2980b9;}.slbl{color:#888;font-size:.78rem;margin-top:3px;}
pre{background:#2d3436;color:#dfe6e9;border-radius:5px;font-size:11px;padding:1rem;
    overflow-x:auto;white-space:pre;max-height:250px;overflow-y:auto;}
</style></head><body>
<h2>PSIPRED Benchmark on CB513</h2>
""")
sys.stdout.flush()

t0 = time.time()
tmp_single  = None
tmp_summary = None
tmp_detail  = None

try:
    # 1. Parse multi-line psipred file
    print('<p>Parsing CB513.psipred (multi-line format)...</p>')
    sys.stdout.flush()
    entries = parse_multiline_seclib(PSIPRED_FILE)
    print(f'<p class="ok">{len(entries)} proteins parsed.</p>')
    sys.stdout.flush()

    # 2. Write single-line version for validateGor
    tmp_single = tempfile.NamedTemporaryFile(delete=False, suffix="_psipred_single.db",
                                             dir=C.TMP_DIR, mode="w")
    tmp_single.close()
    write_singleline_seclib(entries, tmp_single.name)

    tmp_summary = tempfile.NamedTemporaryFile(delete=False, suffix="_psipred_summary.txt",
                                              dir=C.TMP_DIR, mode="w")
    tmp_detail  = tempfile.NamedTemporaryFile(delete=False, suffix="_psipred_detail.html",
                                              dir=C.TMP_DIR, mode="w")
    tmp_summary.close()
    tmp_detail.close()

    # 3. Run validateGor: psipred predictions vs CB513DSSP reference
    print('<p>Running validateGor...</p>')
    sys.stdout.flush()
    cmd = [C.JAVA] + C.JAVA_MEM + [
        "-jar", C.VALIDATE_JAR,
        "-p",   tmp_single.name,   # psipred predictions (AS+SS as pred+ref)
        "-r",   C.CB513_DB,        # CB513DSSP.db as reference
        "-s",   tmp_summary.name,
        "-d",   tmp_detail.name,
        "-f",   "html",
    ]
    # validateGor expects predictions in predict.jar format (PS line)
    # but psipred file has SS line -- rewrite as PS
    tmp_pred = tempfile.NamedTemporaryFile(delete=False, suffix="_psipred_pred.txt",
                                           dir=C.TMP_DIR, mode="w")
    for eid, seq, ss in entries:
        tmp_pred.write(f"> {eid}\nAS {seq}\nPS {ss}\n\n")
    tmp_pred.close()

    cmd[cmd.index(tmp_single.name)] = tmp_pred.name

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True, timeout=C.TIMEOUT)
    elapsed = round(time.time() - t0, 1)

    if proc.returncode != 0:
        print(f'<p class="err">validateGor failed: {H.escape(proc.stderr[:500])}</p>')
        sys.exit(0)

    print(f'<p class="ok">{H.escape(proc.stdout.strip())} ({elapsed}s)</p>')

    with open(tmp_summary.name) as f:
        summary = f.read()

    # 4. Extract and display metrics
    metrics = {
        "q3":   extract_mean(summary, "q3"),
        "qH":   extract_mean(summary, "qObs_H"),
        "qE":   extract_mean(summary, "qObs_E"),
        "qC":   extract_mean(summary, "qObs_C"),
        "sov":  extract_mean(summary, "SOV"),
        "sovH": extract_mean(summary, "SOV_H"),
        "sovE": extract_mean(summary, "SOV_E"),
        "sovC": extract_mean(summary, "SOV_C"),
    }

    print('<div class="card"><h3>PSIPRED Results on CB513</h3>')
    print('<div class="sgrid">')
    labels = [("q3","Q3"),("qH","QH"),("qE","QE"),("qC","QC"),
              ("sov","SOV"),("sovH","SOV_H"),("sovE","SOV_E"),("sovC","SOV_C")]
    for key, lbl in labels:
        v = metrics[key]
        disp = f"{v:.1f}%" if v is not None else "N/A"
        print(f'<div class="scard"><div class="sval">{disp}</div>'
              f'<div class="slbl">{lbl}</div></div>')
    print('</div>')
    print(f'<pre>{H.escape(summary)}</pre>')
    print('</div>')

    # 5. Save to JSON for Results page
    results_data = {}
    if os.path.isfile(RESULTS_JSON):
        try:
            with open(RESULTS_JSON) as f:
                results_data = json.load(f)
        except: pass
    results_data["psipred"] = metrics
    results_data["psipred"]["n"] = len(entries)
    with open(RESULTS_JSON, "w") as f:
        json.dump(results_data, f)
    print('<p class="ok">Results saved to Results page.</p>')

    import base64
    b64 = base64.b64encode(summary.encode()).decode()
    print(f'<a href="data:text/plain;base64,{b64}" download="psipred_summary.txt" '
          f'style="color:#3498db;">Download summary</a>')

except Exception as e:
    print(f'<p class="err">Error: {H.escape(str(e))}</p>')
finally:
    for tmp in [tmp_single, tmp_summary, tmp_detail]:
        if tmp and os.path.isfile(tmp.name):
            try: os.unlink(tmp.name)
            except: pass

print('<br><br><a href="../gor.html" class="back">&lt;- Return to GOR Tool</a></body></html>')
