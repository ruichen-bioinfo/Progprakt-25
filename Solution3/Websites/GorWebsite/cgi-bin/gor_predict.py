#!/usr/bin/env python3

import sys
sys.stdout.write("Content-Type: text/html\r\n\r\n")
sys.stdout.flush()

# Usage (GOR I/III/IV): java -jar predict.jar --model M --seq F [--ref R] [--probabilities]
# Usage (GOR V):        java -jar predict.jar --model M --maf ALN_DIR_OR_FILE

import cgi, cgitb, os, subprocess, tempfile, time, html as H
cgitb.enable()
sys.path.insert(0, os.path.dirname(__file__))
import gor_config as C

MAF_DIR = "/mnt/extstud/praktikum/bioprakt/Data/GOR/CB513/CB513MultipleAlignments"

form         = cgi.FieldStorage()
model_choice = form.getvalue("model_choice", "cb513_gor3")
# GOR V uses GOR IV model but with MAF input
is_gor5 = (model_choice == "cb513_gor4_v")
if is_gor5:
    model_choice = "cb513_gor4"
method_type  = "gorV" if is_gor5 else form.getvalue("method_type", "standard")
show_prob    = form.getvalue("probabilities", "") == "1"

tmp_fasta = None
tmp_model = None
tmp_ref   = None

# ── model path ────────────────────────────────────────────────────────────────
if model_choice == "upload":
    if "model_file" in form and form["model_file"].filename:
        tmp_model = tempfile.NamedTemporaryFile(delete=False, suffix=".mod",
                                                dir=C.TMP_DIR, mode="wb")
        tmp_model.write(form["model_file"].file.read())
        tmp_model.close()
        model_path = tmp_model.name
    else:
        print("<p>X Please upload a model file.</p>"); sys.exit(0)
elif model_choice in C.PRESET_MODELS:
    model_path = C.PRESET_MODELS[model_choice]
else:
    print(f"<p>X Unknown model: {H.escape(model_choice)}</p>"); sys.exit(0)

if not os.path.isfile(model_path):
    print(f"<p>X Model not found: {H.escape(model_path)}</p>"); sys.exit(0)

# ── input sequence ────────────────────────────────────────────────────────────
if method_type == "gorv":
    prot_id = form.getvalue("prot_id", "").strip()
    if prot_id:
        aln_path = os.path.join(MAF_DIR, prot_id + ".aln")
        if not os.path.isfile(aln_path):
            try:
                for fname in os.listdir(MAF_DIR):
                    if fname.lower() == prot_id.lower() + ".aln":
                        aln_path = os.path.join(MAF_DIR, fname); break
            except Exception: pass
        if not os.path.isfile(aln_path):
            print(f"<p>X No .aln file found for: {H.escape(prot_id)}</p>"); sys.exit(0)
        maf_input = aln_path
    elif "aln_file" in form and form["aln_file"].filename:
        tmp_fasta = tempfile.NamedTemporaryFile(delete=False, suffix=".aln",
                                                dir=C.TMP_DIR, mode="wb")
        tmp_fasta.write(form["aln_file"].file.read())
        tmp_fasta.close()
        maf_input = tmp_fasta.name
    else:
        print("<p>X For GOR V: enter a protein ID or upload an .aln file.</p>"); sys.exit(0)
else:
    fasta_text = form.getvalue("fasta_text", "").strip()
    if "fasta_file" in form and form["fasta_file"].filename:
        tmp_fasta = tempfile.NamedTemporaryFile(delete=False, suffix=".fasta",
                                                dir=C.TMP_DIR, mode="wb")
        tmp_fasta.write(form["fasta_file"].file.read())
        tmp_fasta.close()
    elif fasta_text:
        tmp_fasta = tempfile.NamedTemporaryFile(delete=False, suffix=".fasta",
                                                dir=C.TMP_DIR, mode="w")
        tmp_fasta.write(fasta_text)
        tmp_fasta.close()
    else:
        print("<p>X Please provide a sequence.</p>"); sys.exit(0)

# ── reference structure (optional) ───────────────────────────────────────────
ref_text = form.getvalue("ref_text", "").strip()
if "ref_file" in form and form["ref_file"].filename:
    tmp_ref = tempfile.NamedTemporaryFile(delete=False, suffix=".ss",
                                          dir=C.TMP_DIR, mode="wb")
    tmp_ref.write(form["ref_file"].file.read())
    tmp_ref.close()
elif ref_text:
    tmp_ref = tempfile.NamedTemporaryFile(delete=False, suffix=".ss",
                                          dir=C.TMP_DIR, mode="w")
    # Write as simple SS string (jar loadRefSS handles plain string too)
    tmp_ref.write(ref_text)
    tmp_ref.close()

# ── build command ─────────────────────────────────────────────────────────────
if method_type == "gorv":
    cmd = [C.JAVA] + C.JAVA_MEM + [
        "-jar", C.PREDICT_JAR,
        "--model", model_path,
        "--maf",   maf_input,
    ]
    if show_prob: cmd.append("--probabilities")
    if tmp_ref:   cmd += ["--ref", tmp_ref.name]
    method_label = "GOR V (multiple alignment)"
else:
    cmd = [C.JAVA] + C.JAVA_MEM + [
        "-jar",    C.PREDICT_JAR,
        "--model", model_path,
        "--seq",   tmp_fasta.name,
        "--format","txt",
    ]
    if show_prob: cmd.append("--probabilities")
    if tmp_ref:   cmd += ["--ref", tmp_ref.name]
    method_label = f"GOR ({model_choice})"

# ── HTML page ─────────────────────────────────────────────────────────────────
print(f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Predict</title>
<style>
body{{font-family:monospace;background:#0d0f14;color:#c8cdd8;padding:2rem;margin:0;}}
h2{{color:#eef0f5;margin-bottom:.3rem;font-family:'Segoe UI',sans-serif;}}
.subtitle{{color:#636e7e;font-size:.85rem;margin-bottom:1.4rem;font-family:'Segoe UI',sans-serif;}}
pre{{background:#060809;border:1px solid #1e2530;border-radius:6px;padding:1.2rem;
     white-space:pre-wrap;line-height:1.8;font-size:13px;overflow-x:auto;}}
.ok{{color:#00d4aa}}.err{{color:#e05c73}}
.back{{color:#00d4aa;text-decoration:none;font-family:'Segoe UI',sans-serif;font-size:.9rem;}}
/* sequence lines */
.H{{color:#e05c73;font-weight:700}}.E{{color:#5b8dee;font-weight:700}}.C{{color:#8a9bb5}}
.hdr{{color:#00d4aa;font-weight:600}}
.seq{{color:#eef0f5}}
.rs{{color:#f39c12;font-weight:600}}   /* reference SS */
.mt{{color:#636e7e}}                   /* match line */
.q3{{color:#00d4aa;font-weight:700;font-size:.95rem;margin-top:.5rem;}}
/* prob bars */
.ph{{color:#e05c73}}.pe{{color:#5b8dee}}.pc{{color:#8a9bb5}}
/* legend */
.legend{{display:flex;gap:1.5rem;margin-bottom:1rem;font-size:12px;
         font-family:'Segoe UI',sans-serif;flex-wrap:wrap;}}
.ldot{{display:inline-block;width:18px;height:10px;border-radius:2px;
       margin-right:4px;vertical-align:middle;}}
/* info box */
.info{{background:#0f1620;border:1px solid #1e2530;border-radius:6px;
       padding:12px 16px;font-family:'Segoe UI',sans-serif;font-size:.82rem;
       color:#8a9bb5;margin-bottom:1rem;line-height:1.6;}}
.info b{{color:#c8cdd8;}}
</style></head><body>
<h2>GOR Prediction Result</h2>
<p class="subtitle">Method: {H.escape(method_label)}&nbsp;&nbsp;|&nbsp;&nbsp;Model: {H.escape(model_choice)}</p>

<div class="legend">
  <span><span class="ldot" style="background:#e05c73"></span>H = &alpha;-Helix</span>
  <span><span class="ldot" style="background:#5b8dee"></span>E = &beta;-Sheet</span>
  <span><span class="ldot" style="background:#8a9bb5"></span>C = Coil / Loop</span>
  {'<span><span class="ldot" style="background:#f39c12"></span>RS = Reference structure</span>' if tmp_ref else ''}
</div>

<div class="info">
  <b>Output format:</b> &nbsp;
  <b>AS</b> = amino acid sequence &nbsp;|&nbsp;
  <b>PS</b> = predicted secondary structure &nbsp;|&nbsp;
  {'<b>PH/PE/PC</b> = helix/sheet/coil probability (0=low, 9=high) &nbsp;|&nbsp;' if show_prob else ''}
  {'<b>RS</b> = reference structure &nbsp;|&nbsp; <b>MT</b> = match markers + Q3 accuracy' if tmp_ref else ''}
</div>
""")
sys.stdout.flush()

t0 = time.time()
try:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True, timeout=C.TIMEOUT)
    elapsed = round(time.time() - t0, 1)

    if proc.returncode != 0:
        print(f'<p class="err">predict.jar failed (exit {proc.returncode})</p>')
        print(f'<pre>{H.escape(proc.stderr[:2000])}</pre>')
    else:
        output = proc.stdout

        def render(text):
            lines = []
            q3_vals = []
            for line in text.splitlines():
                if line.startswith("> ") or line.startswith(">"):
                    lines.append(f'<span class="hdr">{H.escape(line)}</span>')
                elif line.startswith("AS "):
                    lines.append(f'<span class="seq">{H.escape(line)}</span>')
                elif line.startswith("PS "):
                    colored = '<span class="seq">PS </span>'
                    for ch in line[3:]:
                        if ch in "HEC":
                            colored += f'<span class="{ch}">{ch}</span>'
                        else:
                            colored += H.escape(ch)
                    lines.append(colored)
                elif line.startswith("PH "):
                    lines.append(f'<span class="ph">{H.escape(line)}</span>')
                elif line.startswith("PE "):
                    lines.append(f'<span class="pe">{H.escape(line)}</span>')
                elif line.startswith("PC "):
                    lines.append(f'<span class="pc">{H.escape(line)}</span>')
                elif line.startswith("RS "):
                    lines.append(f'<span class="rs">{H.escape(line)}</span>')
                elif line.startswith("MT "):
                    # Extract Q3 score from match line
                    q3part = ""
                    if "Q3=" in line:
                        q3part = line[line.index("Q3="):]
                        q3_vals.append(q3part)
                    lines.append(f'<span class="mt">{H.escape(line)}</span>')
                else:
                    lines.append(H.escape(line))
            return "\n".join(lines), q3_vals

        rendered, q3_vals = render(output)
        print(f"<pre>{rendered}</pre>")

        # Highlight Q3 scores prominently
        if q3_vals:
            for q in q3_vals:
                print(f'<p class="q3">&#10003; {H.escape(q)}</p>')

        print(f'<p class="ok" style="font-family:\'Segoe UI\',sans-serif;">Done in {elapsed}s</p>')

        import base64
        b64 = base64.b64encode(output.encode()).decode()
        print(f'<a href="data:text/plain;base64,{b64}" download="prediction.txt" '
              f'style="color:#00d4aa;font-family:\'Segoe UI\',sans-serif;">Download result</a>')

except subprocess.TimeoutExpired:
    print(f'<p class="err">Timeout ({C.TIMEOUT}s)</p>')
except FileNotFoundError:
    print(f'<p class="err">Java not found at {C.JAVA}</p>')
finally:
    for tmp in [tmp_fasta, tmp_model, tmp_ref]:
        if tmp and os.path.exists(tmp.name):
            try: os.unlink(tmp.name)
            except: pass

print('<br><br><a href="../gor.html" class="back">&lt;- Return to GOR Tool</a></body></html>')
