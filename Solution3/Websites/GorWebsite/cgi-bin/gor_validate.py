#!/usr/bin/env python3

# Send HTTP header FIRST before any import can fail and cause 500 error
import sys
sys.stdout.write("Content-Type: text/html\r\n\r\n")
sys.stdout.flush()

# Format: pred_file or pred_text, ref_preset or ref_file, show_detailed
# Usage: java -jar GORFiles/jars/validateGor.jar -p <pred> -r <ref> -s <sum> -d <det> -f txt

import cgi, cgitb, os, subprocess, tempfile, time, html as H
cgitb.enable()
sys.path.insert(0, os.path.dirname(__file__))
import gor_config as C

form        = cgi.FieldStorage()
ref_preset  = form.getvalue("ref_preset", "cb513")
show_detail = form.getvalue("show_detailed") == "1"

# Predictions
pred_text = form.getvalue("pred_text", "").strip()
tmp_pred  = None

if "pred_file" in form and form["pred_file"].filename:
    tmp_pred = tempfile.NamedTemporaryFile(delete=False, suffix=".txt",
                                           dir=C.TMP_DIR, mode="wb")
    tmp_pred.write(form["pred_file"].file.read())
    tmp_pred.close()
elif pred_text:
    tmp_pred = tempfile.NamedTemporaryFile(delete=False, suffix=".txt",
                                           dir=C.TMP_DIR, mode="w")
    tmp_pred.write(pred_text)
    tmp_pred.close()
else:
    print("<p>X Please Upload Prediction Result.</p>")
    sys.exit(0)

# Reference db
tmp_ref = None
if "ref_file" in form and form["ref_file"].filename:
    tmp_ref = tempfile.NamedTemporaryFile(delete=False, suffix=".db",
                                          dir=C.TMP_DIR, mode="wb")
    tmp_ref.write(form["ref_file"].file.read())
    tmp_ref.close()
    ref_path = tmp_ref.name
elif ref_preset in C.PRESET_DBS:
    ref_path = C.PRESET_DBS[ref_preset]
else:
    print("<p>X Please Select or Upload Ref-Database.</p>")
    sys.exit(0)

if not os.path.isfile(ref_path):
    print(f"<p>X Ref-Database doesn't Exist: {H.escape(ref_path)}</p>")
    sys.exit(0)

# Temp output files for summary and detail
tmp_sum = tempfile.NamedTemporaryFile(delete=False, suffix="_sum.txt", dir=C.TMP_DIR)
tmp_sum.close()
tmp_det = tempfile.NamedTemporaryFile(delete=False, suffix="_det.txt", dir=C.TMP_DIR)
tmp_det.close()

# Build command
cmd = [C.JAVA] + C.JAVA_MEM + [
    "-jar", C.VALIDATE_JAR,
    "-p",   tmp_pred.name,
    "-r",   ref_path,
    "-s",   tmp_sum.name,
    "-d",   tmp_det.name,
    "-f",   "txt",
]

# HTML output
print("""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Validate</title>
<style>
body{font-family:monospace;background:#0d0f14;color:#c8cdd8;padding:2rem;}
h2,h3{color:#eef0f5;margin-bottom:.8rem;}
pre{background:#000;border:1px solid #252a35;padding:1rem;white-space:pre-wrap;
    max-height:400px;overflow-y:auto;font-size:12px;}
.ok{color:#00d4aa}.err{color:#e05c73}.back{color:#00d4aa;text-decoration:none;}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:1rem;margin:1rem 0;}
.stat{background:#151820;border:1px solid #252a35;border-radius:4px;padding:1rem;text-align:center;}
.val{color:#00d4aa;font-size:22px;font-weight:600;}
.lbl{color:#5a6075;font-size:11px;margin-top:4px;}
</style></head><body>
<h2>GOR Validation</h2>
""")
sys.stdout.flush()

t0 = time.time()
try:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True, timeout=C.TIMEOUT)
    elapsed = round(time.time() - t0, 1)

    if proc.returncode != 0:
        print(f'<p class="err">validateGor.jar failed (exit {proc.returncode})</p>')
        print(f'<pre class="err">{H.escape(proc.stderr[:2000])}</pre>')
    else:
        print(f'<p class="ok">Done, runtime {elapsed}s</p>')

        # Read summary file
        summary = ""
        if os.path.isfile(tmp_sum.name):
            with open(tmp_sum.name) as f:
                summary = f.read()

        # Try parsing key metrics and show as stat cards
        def extract(text, key):
            for line in text.splitlines():
                if line.strip().lower().startswith(key.lower()):
                    for tok in line.split()[1:]:
                        try:
                            v = float(tok.strip("%"))
                            return v / 100.0 if v > 1.0 else v
                        except ValueError:
                            pass
            return None

        stats = {k: extract(summary, k) for k in ["Q3","SOV","QH","QE","QC"]}
        stats = {k: v for k, v in stats.items() if v is not None}

        if stats:
            print('<div class="grid">')
            labels = {"Q3":"Q3 Total Accuracy","SOV":"SOV",
                      "QH":"Q_Helix","QE":"Q_Sheet","QC":"Q_Coil"}
            for k, v in stats.items():
                print(f'<div class="stat"><div class="val">{v*100:.1f}%</div>'
                      f'<div class="lbl">{labels.get(k,k)}</div></div>')
            print('</div>')

        print(f'<h3>Summary</h3><pre>{H.escape(summary)}</pre>')

        if show_detail and os.path.isfile(tmp_det.name):
            with open(tmp_det.name) as f:
                detail = f.read()
            if detail:
                print(f'<h3>Per-protein Details</h3><pre>{H.escape(detail[:15000])}</pre>')

        # Download button
        import base64
        if summary:
            b64 = base64.b64encode(summary.encode()).decode()
            print(f'<a href="data:text/plain;base64,{b64}" download="summary.txt" '
                  f'style="color:#00d4aa;">Download Summary</a>')

except subprocess.TimeoutExpired:
    print(f'<p class="err">Timeout ({C.TIMEOUT}s)</p>')
except FileNotFoundError:
    print(f'<p class="err">Java not found: {C.JAVA}</p>')
finally:
    for f in [tmp_pred, tmp_ref]:
        if f and os.path.exists(f.name):
            try: os.unlink(f.name)
            except: pass
    for f in [tmp_sum, tmp_det]:
        if os.path.exists(f.name):
            try: os.unlink(f.name)
            except: pass

print('<br><br><a href="../gor.html" class="back">&lt;- Return</a></body></html>')