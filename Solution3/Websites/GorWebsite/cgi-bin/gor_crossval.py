#!/usr/bin/env python3

import sys
sys.stdout.write("Content-Type: text/html\r\n\r\n")
sys.stdout.flush()

# 5-Fold Cross-Validation
# For each fold:
#   1. Split CB513DSSP.db into train (4 folds) and test (1 fold) seclib files
#   2. java -jar train.jar   -> .mod file
#   3. java -jar predict.jar -> predictions txt
#   4. java -jar validateGor.jar -> summary + detailed
# Aggregate mean Q3 / SOV across all folds

import cgi, cgitb, os, subprocess, tempfile, time, html as H, random
cgitb.enable()
sys.path.insert(0, os.path.dirname(__file__))
import gor_config as C

form   = cgi.FieldStorage()
method = form.getvalue("method", "gor3")   # gor1 / gor3 / gor4 / all
seed   = int(form.getvalue("seed", "42"))
K      = 5

# ── HTML head ─────────────────────────────────────────────────────────────────
print("""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>5-Fold CV</title>
<style>
body{font-family:'Segoe UI',sans-serif;background:#f4f7f6;color:#333;padding:2rem;margin:0;}
h2{color:#2c3e50;margin-bottom:.3rem;}
h3{color:#2980b9;border-bottom:2px solid #3498db;padding-bottom:6px;margin-bottom:14px;}
.card{background:white;border-radius:8px;box-shadow:0 2px 5px rgba(0,0,0,.1);
      padding:20px;margin-bottom:20px;}
.ok{color:#27ae60}.err{color:#e74c3c}.info{color:#2980b9}
.back{color:#3498db;text-decoration:none;font-size:.9rem;}
.sgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px;margin:14px 0;}
.scard{background:#f8f9fa;border:1px solid #ddd;border-radius:6px;padding:12px;text-align:center;}
.sval{font-size:1.4rem;font-weight:700;color:#2980b9;}
.slbl{color:#888;font-size:.78rem;margin-top:3px;}
table{border-collapse:collapse;width:100%;font-size:.88rem;}
th{border-bottom:2px solid #3498db;color:#2980b9;padding:7px 8px;text-align:left;}
td{border-bottom:1px solid #eee;padding:6px 8px;}
pre{background:#2d3436;color:#dfe6e9;border-radius:5px;font-size:11px;
    padding:1rem;overflow-x:auto;white-space:pre;max-height:200px;overflow-y:auto;}
</style></head><body>
<h2>5-Fold Cross-Validation</h2>
""")
sys.stdout.flush()

def parse_seclib(path):
    """Parse seclib file, return list of (id, seq, ss) tuples."""
    entries = []
    with open(path) as f:
        eid, seq, ss = None, None, None
        for line in f:
            line = line.rstrip()
            if line.startswith(">"):
                if eid and seq and ss:
                    entries.append((eid, seq, ss))
                eid = line[1:].strip().split()[0]
                seq = ss = None
            elif line.startswith("AS "):
                seq = line[3:].strip()
            elif line.startswith("SS "):
                ss = line[3:].strip()
        if eid and seq and ss:
            entries.append((eid, seq, ss))
    return entries

def write_seclib(entries, path):
    with open(path, "w") as f:
        for eid, seq, ss in entries:
            f.write(f"> {eid}\n")
            f.write(f"AS {seq}\n")
            f.write(f"SS {ss}\n\n")

def extract_mean(summary_text, label):
    for line in summary_text.splitlines():
        s = line.strip()
        if s.startswith(label + ":") or s.startswith(label + " "):
            parts = s.split("Mean:")
            if len(parts) > 1:
                try: return float(parts[1].strip().split()[0])
                except: pass
    return float("nan")

# ── Load CB513 ────────────────────────────────────────────────────────────────
print('<div class="card">')
print(f'<p class="info">Loading CB513 database...</p>')
sys.stdout.flush()

try:
    all_entries = parse_seclib(C.CB513_DB)
except Exception as e:
    print(f'<p class="err">X Failed to load {H.escape(C.CB513_DB)}: {H.escape(str(e))}</p>')
    sys.exit(0)

n_total = len(all_entries)
print(f'<p class="ok">{n_total} proteins loaded.</p>')
sys.stdout.flush()

# Shuffle deterministically
rng = random.Random(seed)
indices = list(range(n_total))
rng.shuffle(indices)
shuffled = [all_entries[i] for i in indices]

# Split into K folds
folds = [shuffled[i::K] for i in range(K)]

methods = ["gor1", "gor3", "gor4"] if method == "all" else [method]

# Results: method -> list of fold dicts
all_results = {m: [] for m in methods}

t_total = time.time()

for m in methods:
    print(f'<p><b>Running {m.upper()} cross-validation...</b></p>')
    sys.stdout.flush()

    for fold_idx in range(K):
        t_fold = time.time()
        print(f'<p class="info">&nbsp;&nbsp;Fold {fold_idx+1}/{K}...</p>')
        sys.stdout.flush()

        test_entries  = folds[fold_idx]
        train_entries = []
        for j in range(K):
            if j != fold_idx:
                train_entries.extend(folds[j])

        # Write train and test seclib files
        tmp_train = tempfile.NamedTemporaryFile(delete=False, suffix="_train.db", dir=C.TMP_DIR, mode="w")
        tmp_test  = tempfile.NamedTemporaryFile(delete=False, suffix="_test.db",  dir=C.TMP_DIR, mode="w")
        tmp_train.close(); tmp_test.close()
        write_seclib(train_entries, tmp_train.name)
        write_seclib(test_entries,  tmp_test.name)

        # Write test FASTA for predict.jar
        tmp_fasta = tempfile.NamedTemporaryFile(delete=False, suffix="_test.fasta", dir=C.TMP_DIR, mode="w")
        for eid, seq, ss in test_entries:
            tmp_fasta.write(f">{eid}\n{seq}\n")
        tmp_fasta.close()

        tmp_mod     = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{m}_fold{fold_idx}.mod", dir=C.TMP_DIR, mode="w")
        tmp_pred    = tempfile.NamedTemporaryFile(delete=False, suffix="_pred.txt",    dir=C.TMP_DIR, mode="w")
        tmp_summary = tempfile.NamedTemporaryFile(delete=False, suffix="_summary.txt", dir=C.TMP_DIR, mode="w")
        tmp_detail  = tempfile.NamedTemporaryFile(delete=False, suffix="_detail.txt",  dir=C.TMP_DIR, mode="w")
        for t in [tmp_mod, tmp_pred, tmp_summary, tmp_detail]:
            t.close()

        fold_ok = True
        try:
            # 1. Train
            cmd_train = [C.JAVA] + C.JAVA_MEM + [
                "-jar", C.TRAIN_JAR,
                "--db",     tmp_train.name,
                "--method", m,
                "--model",  tmp_mod.name,
            ]
            r = subprocess.run(cmd_train, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True, timeout=C.TIMEOUT)
            if r.returncode != 0:
                print(f'<p class="err">Train failed fold {fold_idx+1}: {H.escape(r.stderr[:300])}</p>')
                fold_ok = False

            if fold_ok:
                # 2. Predict
                cmd_pred = [C.JAVA] + C.JAVA_MEM + [
                    "-jar",    C.PREDICT_JAR,
                    "--model", tmp_mod.name,
                    "--seq",   tmp_fasta.name,
                    "--format","txt",
                ]
                r2 = subprocess.run(cmd_pred, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    universal_newlines=True, timeout=C.TIMEOUT)
                if r2.returncode != 0:
                    print(f'<p class="err">Predict failed fold {fold_idx+1}: {H.escape(r2.stderr[:300])}</p>')
                    fold_ok = False
                else:
                    with open(tmp_pred.name, "w") as pf:
                        pf.write(r2.stdout)

            if fold_ok:
                # 3. Validate
                cmd_val = [C.JAVA] + C.JAVA_MEM + [
                    "-jar", C.VALIDATE_JAR,
                    "-p",   tmp_pred.name,
                    "-r",   tmp_test.name,
                    "-s",   tmp_summary.name,
                    "-d",   tmp_detail.name,
                    "-f",   "txt",
                ]
                r3 = subprocess.run(cmd_val, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    universal_newlines=True, timeout=C.TIMEOUT)
                if r3.returncode != 0:
                    print(f'<p class="err">Validate failed fold {fold_idx+1}: {H.escape(r3.stderr[:300])}</p>')
                    fold_ok = False
                else:
                    with open(tmp_summary.name) as sf:
                        summary = sf.read()
                    result = {
                        "fold":  fold_idx + 1,
                        "n":     len(test_entries),
                        "q3":    extract_mean(summary, "q3"),
                        "sov":   extract_mean(summary, "SOV"),
                        "qH":    extract_mean(summary, "qObs_H"),
                        "qE":    extract_mean(summary, "qObs_E"),
                        "qC":    extract_mean(summary, "qObs_C"),
                        "sovH":  extract_mean(summary, "SOV_H"),
                        "sovE":  extract_mean(summary, "SOV_E"),
                        "sovC":  extract_mean(summary, "SOV_C"),
                    }
                    all_results[m].append(result)
                    elapsed_fold = round(time.time() - t_fold, 1)
                    print(f'<p class="ok">&nbsp;&nbsp;&nbsp;&nbsp;'
                          f'Fold {fold_idx+1}: Q3={result["q3"]:.1f}% '
                          f'SOV={result["sov"]:.1f}% ({elapsed_fold}s)</p>')
                    sys.stdout.flush()

        finally:
            for tmp in [tmp_train, tmp_test, tmp_fasta, tmp_mod, tmp_pred, tmp_summary, tmp_detail]:
                if os.path.exists(tmp.name):
                    try: os.unlink(tmp.name)
                    except: pass

print('</div>')

# ── Aggregate results ─────────────────────────────────────────────────────────
import math

def nanmean(vals):
    v = [x for x in vals if not math.isnan(x)]
    return sum(v) / len(v) if v else float("nan")

print('<div class="card"><h3>Final Results</h3>')
for m in methods:
    folds_res = all_results[m]
    if not folds_res:
        print(f'<p class="err">{m.upper()}: no results collected.</p>')
        continue

    q3   = nanmean([r["q3"]   for r in folds_res])
    sov  = nanmean([r["sov"]  for r in folds_res])
    qH   = nanmean([r["qH"]   for r in folds_res])
    qE   = nanmean([r["qE"]   for r in folds_res])
    qC   = nanmean([r["qC"]   for r in folds_res])
    sovH = nanmean([r["sovH"] for r in folds_res])
    sovE = nanmean([r["sovE"] for r in folds_res])
    sovC = nanmean([r["sovC"] for r in folds_res])

    print(f'<h3>{m.upper()} &mdash; 5-Fold CV on CB513</h3>')
    print('<div class="sgrid">')
    for label, val in [("Q3", q3), ("SOV", sov),
                        ("QH", qH), ("QE", qE), ("QC", qC),
                        ("SOV_H", sovH), ("SOV_E", sovE), ("SOV_C", sovC)]:
        disp = f"{val:.1f}%" if not math.isnan(val) else "N/A"
        print(f'<div class="scard"><div class="sval">{disp}</div>'
              f'<div class="slbl">{label}</div></div>')
    print('</div>')

    # Per-fold table
    print('<table><thead><tr><th>Fold</th><th>N</th><th>Q3</th><th>SOV</th>'
          '<th>QH</th><th>QE</th><th>QC</th></tr></thead><tbody>')
    for r in folds_res:
        def f1(v): return f"{v:.1f}%" if not math.isnan(v) else "-"
        print(f'<tr><td>{r["fold"]}</td><td>{r["n"]}</td>'
              f'<td>{f1(r["q3"])}</td><td>{f1(r["sov"])}</td>'
              f'<td>{f1(r["qH"])}</td><td>{f1(r["qE"])}</td><td>{f1(r["qC"])}</td></tr>')
    print('</tbody></table><br>')

total_elapsed = round(time.time() - t_total, 1)
print(f'<p class="ok">Total time: {total_elapsed}s</p>')

# Save results to JSON for Results page
try:
    import json
    RESULTS_JSON = os.path.join(C.TMP_DIR, "psipred_results.json")
    results_data = {}
    if os.path.isfile(RESULTS_JSON):
        try:
            with open(RESULTS_JSON) as jf:
                results_data = json.load(jf)
        except: pass
    for m in methods:
        folds_res = all_results[m]
        if not folds_res: continue
        key = f"cv_{m}"
        results_data[key] = {
            "q3":   float(nanmean([r["q3"]   for r in folds_res])),
            "qH":   float(nanmean([r["qH"]   for r in folds_res])),
            "qE":   float(nanmean([r["qE"]   for r in folds_res])),
            "qC":   float(nanmean([r["qC"]   for r in folds_res])),
            "sov":  float(nanmean([r["sov"]  for r in folds_res])),
            "sovH": float(nanmean([r["sovH"] for r in folds_res])),
            "sovE": float(nanmean([r["sovE"] for r in folds_res])),
            "sovC": float(nanmean([r["sovC"] for r in folds_res])),
            "n_folds": len(folds_res),
        }
    with open(RESULTS_JSON, "w") as jf:
        json.dump(results_data, jf)
    print('<p class="ok">Results saved &rarr; Results page updated.</p>')
except Exception as e:
    print(f'<p style="color:#e67e22;">Could not save results: {str(e)}</p>')

print('</div>')
print('<br><a href="../gor.html" class="back">&lt;- Return to GOR Tool</a></body></html>')
