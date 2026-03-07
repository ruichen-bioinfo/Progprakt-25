#!/usr/bin/env python3

# Send HTTP header FIRST
import sys
sys.stdout.write("Content-Type: text/html\r\n\r\n")
sys.stdout.flush()

# Form fields: fasta_text or fasta_file, model_choice (or model_file upload), method_type
# Usage (GOR I/III/IV): java -jar predict.jar --model <mod> --seq <fasta> [--format txt]
# Usage (GOR V):        java -jar predict.jar --model <mod> --maf <aln_dir>
# Note: --help output is misleading, jar actually uses named flags (see source)

import cgi, cgitb, os, subprocess, tempfile, time, html as H
cgitb.enable()
sys.path.insert(0, os.path.dirname(__file__))
import gor_config as C

# Directory containing CB513 multiple alignments for GOR V
MAF_DIR = "/mnt/extstud/praktikum/bioprakt/Data/GOR/CB513/CB513MultipleAlignments"

form         = cgi.FieldStorage()
model_choice = form.getvalue("model_choice", "cb513_gor3")
method_type  = form.getvalue("method_type", "standard")  # "standard" or "gorv"

# Parse FASTA input (used for standard GOR I/III/IV)
fasta_text = form.getvalue("fasta_text", "").strip()
tmp_fasta  = None

if method_type == "gorv":
    # GOR V uses pre-existing .aln files -- no FASTA upload needed
    # User provides a protein ID to look up its .aln file
    prot_id = form.getvalue("prot_id", "").strip()
    if prot_id:
        # Look for matching .aln file in MAF_DIR
        aln_path = os.path.join(MAF_DIR, prot_id + ".aln")
        if not os.path.isfile(aln_path):
            # Try case-insensitive search
            try:
                for fname in os.listdir(MAF_DIR):
                    if fname.lower() == prot_id.lower() + ".aln":
                        aln_path = os.path.join(MAF_DIR, fname)
                        break
            except Exception:
                pass
        if not os.path.isfile(aln_path):
            print(f"<p>X No .aln file found for ID: {H.escape(prot_id)}</p>")
            sys.exit(0)
        maf_input = aln_path
    elif "aln_file" in form and form["aln_file"].filename:
        # User uploads a custom .aln file
        tmp_fasta = tempfile.NamedTemporaryFile(delete=False, suffix=".aln",
                                                dir=C.TMP_DIR, mode="wb")
        tmp_fasta.write(form["aln_file"].file.read())
        tmp_fasta.close()
        maf_input = tmp_fasta.name
    else:
        print("<p>X For GOR V: enter a protein ID or upload an .aln file.</p>")
        sys.exit(0)
else:
    # Standard mode: need FASTA sequence
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
        print("<p>X Please provide a sequence (paste or upload).</p>")
        sys.exit(0)

# Parse model path
tmp_model = None
if model_choice == "upload":
    if "model_file" in form and form["model_file"].filename:
        tmp_model = tempfile.NamedTemporaryFile(delete=False, suffix=".mod",
                                                dir=C.TMP_DIR, mode="wb")
        tmp_model.write(form["model_file"].file.read())
        tmp_model.close()
        model_path = tmp_model.name
    else:
        print("<p>X Please upload a model file.</p>")
        sys.exit(0)
elif model_choice in C.PRESET_MODELS:
    model_path = C.PRESET_MODELS[model_choice]
else:
    print(f"<p>X Unknown model: {H.escape(model_choice)}</p>")
    sys.exit(0)

if not os.path.isfile(model_path):
    print(f"<p>X Model file not found: {H.escape(model_path)}<br>Please train the model first.</p>")
    sys.exit(0)

# Build command
if method_type == "gorv":
    # GOR V: --maf flag, model must be gor4 for best results
    cmd = [C.JAVA] + C.JAVA_MEM + [
        "-jar",    C.PREDICT_JAR,
        "--model", model_path,
        "--maf",   maf_input,
    ]
    method_label = "GOR V (multiple alignment)"
else:
    # Standard GOR I/III/IV: --seq flag
    cmd = [C.JAVA] + C.JAVA_MEM + [
        "-jar",     C.PREDICT_JAR,
        "--model",  model_path,
        "--seq",    tmp_fasta.name,
        "--format", "txt",
    ]
    method_label = f"GOR ({model_choice})"

# HTML output
print(f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Predict</title>
<style>
body{{font-family:monospace;background:#0d0f14;color:#c8cdd8;padding:2rem;}}
h2{{color:#eef0f5;margin-bottom:1rem;}}
pre{{background:#000;border:1px solid #252a35;padding:1rem;white-space:pre-wrap;
    line-height:1.7;font-size:13px;}}
.ok{{color:#00d4aa}}.err{{color:#e05c73}}.back{{color:#00d4aa;text-decoration:none;}}
.H{{color:#e05c73;font-weight:600}}
.E{{color:#5b8dee;font-weight:600}}
.C{{color:#8a9bb5}}
.hdr{{color:#00d4aa;font-weight:600}}
.seq{{color:#eef0f5}}
.legend{{display:flex;gap:1.5rem;margin-bottom:1rem;font-size:12px;}}
.ldot{{display:inline-block;width:18px;height:10px;border-radius:2px;margin-right:4px;vertical-align:middle;}}
</style></head><body>
<h2>GOR Prediction Result -- {H.escape(method_label)}</h2>
<div class="legend">
  <span><span class="ldot" style="background:#e05c73"></span>H = &alpha;-Helix</span>
  <span><span class="ldot" style="background:#5b8dee"></span>E = &beta;-Sheet</span>
  <span><span class="ldot" style="background:#8a9bb5"></span>C = Coil</span>
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
        print(f'<pre class="err">{H.escape(proc.stderr[:2000])}</pre>')
    else:
        output = proc.stdout

        # Render txt output with SS color coding
        def render(text):
            lines = []
            for line in text.splitlines():
                if line.startswith(">"):
                    lines.append(f'<span class="hdr">{H.escape(line)}</span>')
                elif line.startswith("AS "):
                    lines.append(f'<span class="seq">{H.escape(line)}</span>')
                elif line.startswith("PS "):
                    colored = "PS "
                    for ch in line[3:]:
                        if ch in "HEC":
                            colored += f'<span class="{ch}">{ch}</span>'
                        else:
                            colored += H.escape(ch)
                    lines.append(colored)
                else:
                    lines.append(H.escape(line))
            return "\n".join(lines)

        print(f"<pre>{render(output)}</pre>")
        print(f'<p class="ok">Finished, runtime {elapsed}s</p>')

        # Download button
        import base64
        b64 = base64.b64encode(output.encode()).decode()
        print(f'<a href="data:text/plain;base64,{b64}" download="prediction.txt" '
              f'style="color:#00d4aa;">Download Result</a>')

except subprocess.TimeoutExpired:
    print(f'<p class="err">Timeout ({C.TIMEOUT}s)</p>')
except FileNotFoundError:
    print(f'<p class="err">Java not found: {C.JAVA}</p>')
finally:
    for tmp in [tmp_fasta, tmp_model]:
        if tmp and os.path.exists(tmp.name):
            try: os.unlink(tmp.name)
            except: pass

print('<br><br><a href="../gor.html" class="back">&lt;- Return</a></body></html>')