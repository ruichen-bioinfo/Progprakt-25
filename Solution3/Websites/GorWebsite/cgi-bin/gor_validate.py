#!/usr/bin/env python3

import sys
sys.stdout.write("Content-Type: text/html\r\n\r\n")
sys.stdout.flush()

# Usage: java -jar validateGor.jar -p <pred> -r <seclib> -s <summary> -d <detailed> [-f txt|html]
# pred file = predict.jar txt output (> id / AS seq / PS pred)
# ref  file = seclib format (> id / AS seq / SS ref) -- CB513DSSP.db or upload

import cgi, cgitb, os, subprocess, tempfile, time, html as H
cgitb.enable()
sys.path.insert(0, os.path.dirname(__file__))
import gor_config as C

form          = cgi.FieldStorage()
ref_preset    = form.getvalue("ref_preset", "cb513")
show_detailed = form.getvalue("show_detailed", "1") == "1"

tmp_pred = None
tmp_ref  = None

# ── prediction input ──────────────────────────────────────────────────────────
pred_text = form.getvalue("pred_text", "").strip()
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
    print("<p>X Please provide prediction output (paste or upload).</p>")
    sys.exit(0)

# ── reference file ────────────────────────────────────────────────────────────
if ref_preset == "cb513":
    ref_path = C.CB513_DB
elif "ref_file" in form and form["ref_file"].filename:
    tmp_ref = tempfile.NamedTemporaryFile(delete=False, suffix=".db",
                                          dir=C.TMP_DIR, mode="wb")
    tmp_ref.write(form["ref_file"].file.read())
    tmp_ref.close()
    ref_path = tmp_ref.name
else:
    print("<p>X Please upload a reference seclib file or select CB513.</p>")
    sys.exit(0)

if not os.path.isfile(ref_path):
    print(f"<p>X Reference file not found: {H.escape(ref_path)}</p>")
    sys.exit(0)

# ── output temp files ─────────────────────────────────────────────────────────
tmp_summary  = tempfile.NamedTemporaryFile(delete=False, suffix="_summary.txt",  dir=C.TMP_DIR, mode="w")
tmp_detailed = tempfile.NamedTemporaryFile(delete=False, suffix="_detailed.html", dir=C.TMP_DIR, mode="w")
tmp_summary.close()
tmp_detailed.close()

cmd = [C.JAVA] + C.JAVA_MEM + [
    "-jar", C.VALIDATE_JAR,
    "-p",   tmp_pred.name,
    "-r",   ref_path,
    "-s",   tmp_summary.name,
    "-d",   tmp_detailed.name,
    "-f",   "html",
]

# ── HTML page ─────────────────────────────────────────────────────────────────
print("""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Validate</title>
<style>
body{font-family:'Segoe UI',sans-serif;background:#f4f7f6;color:#333;padding:2rem;margin:0;}
h2{color:#2c3e50;margin-bottom:.3rem;}
h3{color:#2980b9;border-bottom:2px solid #3498db;padding-bottom:6px;margin-bottom:14px;}
.card{background:white;border-radius:8px;box-shadow:0 2px 5px rgba(0,0,0,.1);
      padding:20px;margin-bottom:20px;}
.ok{color:#27ae60}.err{color:#e74c3c}
.back{color:#3498db;text-decoration:none;font-size:.9rem;}
/* Stats grid */
.sgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:12px;margin:14px 0;}
.scard{background:#f8f9fa;border:1px solid #ddd;border-radius:6px;padding:12px;text-align:center;}
.sval{font-size:1.4rem;font-weight:700;color:#2980b9;}
.slbl{color:#888;font-size:.78rem;margin-top:3px;}
/* summary pre */
pre.summary{background:#2d3436;color:#dfe6e9;border-radius:5px;font-size:12px;
            padding:1rem;overflow-x:auto;white-space:pre;}
/* embedded detailed iframe */
iframe{width:100%;border:none;border-radius:6px;min-height:500px;}
</style></head><body>
<h2>GOR Validation Results</h2>
""")
sys.stdout.flush()

t0 = time.time()
try:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True, timeout=C.TIMEOUT)
    elapsed = round(time.time() - t0, 1)

    stderr_clean = proc.stderr.strip()
    if proc.returncode != 0:
        print(f'<p class="err">validateGor.jar failed (exit {proc.returncode})</p>')
        if "No matching IDs" in stderr_clean:
            print('''<div class="card" style="border-left:4px solid #e74c3c;padding:14px;">
                <b>ID mismatch</b> &mdash; none of the prediction IDs matched the reference database.<br><br>
                <b>Likely cause:</b> You predicted a sequence from RCSB (e.g. 1MBN).
                RCSB headers like <code>1MBN_1|Chain A|...</code> do not match CB513 IDs like <code>154l</code>.<br><br>
                <b>Solutions:</b><br>
                &bull; Run prediction on sequences from <b>CB513.fasta</b> to use this Validate tab.<br>
                &bull; To compare a single arbitrary prediction against a known structure,
                  use the <b>Predict</b> tab &rarr; "Reference structure" field.
            </div>''')
        if stderr_clean:
            print(f'<pre class="summary">{H.escape(stderr_clean[:2000])}</pre>')
        sys.exit(0)

    # Show any warnings
    if stderr_clean:
        print(f'<p style="color:#e67e22;font-size:.85rem;">Warnings: {H.escape(stderr_clean[:500])}</p>')

    print(f'<p class="ok">{H.escape(proc.stdout.strip())} &mdash; {elapsed}s</p>')

    # ── Parse summary file and render as cards ────────────────────────────────
    summary_text = ""
    if os.path.isfile(tmp_summary.name):
        with open(tmp_summary.name) as f:
            summary_text = f.read()

    if summary_text:
        # Extract key values from summary for cards
        def extract(label, text):
            for line in text.splitlines():
                if line.strip().startswith(label + ":") or line.strip().startswith(label + " "):
                    # find Mean: value
                    parts = line.split("Mean:")
                    if len(parts) > 1:
                        val = parts[1].strip().split()[0]
                        try: return f"{float(val):.1f}%"
                        except: pass
            return "N/A"

        print('<div class="card"><h3>Summary Statistics</h3>')
        print('<div class="sgrid">')
        metrics = [
            ("q3",     "Q3 (overall)"),
            ("qObs_H", "Q&#8203;H (Helix)"),
            ("qObs_E", "Q&#8203;E (Sheet)"),
            ("qObs_C", "Q&#8203;C (Coil)"),
            ("SOV",    "SOV"),
            ("SOV_H",  "SOV_H"),
            ("SOV_E",  "SOV_E"),
            ("SOV_C",  "SOV_C"),
        ]
        for key, label in metrics:
            val = extract(key, summary_text)
            print(f'<div class="scard"><div class="sval">{val}</div>'
                  f'<div class="slbl">{label}</div></div>')
        print('</div>')

        # Raw summary
        print(f'<pre class="summary">{H.escape(summary_text)}</pre>')

        # Download summary
        import base64
        b64 = base64.b64encode(summary_text.encode()).decode()
        print(f'<a href="data:text/plain;base64,{b64}" download="validation_summary.txt" '
              f'style="color:#3498db;">Download summary</a>')
        print('</div>')

    # ── Detailed results (embedded HTML from jar) ─────────────────────────────
    if show_detailed and os.path.isfile(tmp_detailed.name):
        with open(tmp_detailed.name) as f:
            detailed_html = f.read()
        print('<div class="card"><h3>Detailed Results</h3>')
        # Embed as iframe using data URI
        b64d = base64.b64encode(detailed_html.encode()).decode()
        print(f'<iframe src="data:text/html;base64,{b64d}"></iframe>')
        b64d2 = base64.b64encode(detailed_html.encode()).decode()
        print(f'<br><a href="data:text/html;base64,{b64d2}" download="validation_detailed.html" '
              f'style="color:#3498db;">Download detailed report</a>')
        print('</div>')

except subprocess.TimeoutExpired:
    print(f'<p class="err">Timeout ({C.TIMEOUT}s)</p>')
except FileNotFoundError:
    print(f'<p class="err">Java not found at {C.JAVA}</p>')
finally:
    for tmp in [tmp_pred, tmp_ref]:
        if tmp and os.path.exists(tmp.name):
            try: os.unlink(tmp.name)
            except: pass
    for path in [tmp_summary.name, tmp_detailed.name]:
        if os.path.exists(path):
            try: os.unlink(path)
            except: pass

print('<br><a href="../gor.html" class="back">&lt;- Return to GOR Tool</a></body></html>')
