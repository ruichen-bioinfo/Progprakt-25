#!/usr/bin/env python3


# File use form: fasta_text or fasta_file,model_choice (or model_file Uploads, it's readable), format, probabilities
# usage: java -jar GORFiles/jars/predict.jar --model <mod> --seq <fasta> --format txt [--probabilities]

import cgi, cgitb, os, sys, subprocess, tempfile, time, html as H
cgitb.enable()
sys.path.insert(0, os.path.dirname(__file__))
import gor_config as C

print("Content-Type: text/html\r\n\r\n")

form         = cgi.FieldStorage()
fmt          = form.getvalue("format", "txt")
use_prob     = form.getvalue("probabilities") == "1"
model_choice = form.getvalue("model_choice", "cb513_gor3")

# Analyse FASTA input
fasta_text = form.getvalue("fasta_text", "").strip()
tmp_fasta  = None

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
    print("<p>❌ Please Upload Sequence(Paste or Upload)</p>")
    sys.exit(0)

# Analyse Model Path
tmp_model = None
if model_choice == "upload":
    if "model_file" in form and form["model_file"].filename:
        tmp_model = tempfile.NamedTemporaryFile(delete=False, suffix=".mod",
                                                dir=C.TMP_DIR, mode="wb")
        tmp_model.write(form["model_file"].file.read())
        tmp_model.close()
        model_path = tmp_model.name
    else:
        print("<p>❌ Please Upload Model File</p>")
        sys.exit(0)
elif model_choice in C.PRESET_MODELS:
    model_path = C.PRESET_MODELS[model_choice]
else:
    print(f"<p>❌ Unknown Model: {H.escape(model_choice)}</p>")
    sys.exit(0)

if not os.path.isfile(model_path):
    print(f"<p>❌ Model doesn't Exist: {H.escape(model_path)}<br>Please Train the Model First.</p>")
    sys.exit(0)

# CONSTRUCTION!!!
cmd = [C.JAVA] + C.JAVA_MEM + [
    "-jar",    C.PREDICT_JAR,
    "--model", model_path,
    "--seq",   tmp_fasta.name,
    "--format","txt",          # Take txt first, we can make it better
]
if use_prob:
    cmd.append("--probabilities")

# HTML
print("""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Predict</title>
<style>
body{font-family:monospace;background:#0d0f14;color:#c8cdd8;padding:2rem;}
h2{color:#eef0f5;margin-bottom:1rem;}
pre{background:#000;border:1px solid #252a35;padding:1rem;white-space:pre-wrap;
    line-height:1.7;font-size:13px;}
.ok{color:#00d4aa}.err{color:#e05c73}.back{color:#00d4aa;text-decoration:none;}
/* SS Coloring */
.H{color:#e05c73;font-weight:600}
.E{color:#5b8dee;font-weight:600}
.C{color:#8a9bb5}
.hdr{color:#00d4aa;font-weight:600}
.seq{color:#eef0f5}
.ph{color:#e05c73}.pe{color:#5b8dee}.pc{color:#8a9bb5}
.legend{display:flex;gap:1.5rem;margin-bottom:1rem;font-size:12px;}
.ldot{display:inline-block;width:18px;height:10px;border-radius:2px;margin-right:4px;vertical-align:middle;}
</style></head><body>
<h2>🔬 GOR Prediction Result</h2>
<div class="legend">
  <span><span class="ldot" style="background:#e05c73"></span>H = α-Helix</span>
  <span><span class="ldot" style="background:#5b8dee"></span>E = β-Sheet</span>
  <span><span class="ldot" style="background:#8a9bb5"></span>C = Coil</span>
</div>
""")
sys.stdout.flush()

t0 = time.time()
try:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=C.TIMEOUT)
    elapsed = round(time.time() - t0, 1)

    if proc.returncode != 0:
        print(f'<p class="err">✗ predict.jar failed (exit {proc.returncode})</p>')
        print(f'<pre class="err">{H.escape(proc.stderr[:2000])}</pre>')
    else:
        output = proc.stdout

        # Render txt to color
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
                elif line.startswith("PH "):
                    lines.append(f'<span class="ph">{H.escape(line)}</span>')
                elif line.startswith("PE "):
                    lines.append(f'<span class="pe">{H.escape(line)}</span>')
                elif line.startswith("PC "):
                    lines.append(f'<span class="pc">{H.escape(line)}</span>')
                else:
                    lines.append(H.escape(line))
            return "\n".join(lines)

        print(f"<pre>{render(output)}</pre>")
        print(f'<p class="ok">✓ Finished,RunTime {elapsed}s</p>')

        # BTN for Download
        import base64
        b64 = base64.b64encode(output.encode()).decode()
        print(f'<a href="data:text/plain;base64,{b64}" download="prediction.txt" '
              f'style="color:#00d4aa;">⬇ Result</a>')

except subprocess.TimeoutExpired:
    print(f'<p class="err">✗ TIME OUT OF STACK ({C.TIMEOUT}s)</p>')
except FileNotFoundError:
    print(f'<p class="err">✗ Java Not Found: {C.JAVA}</p>')
finally:
    for tmp in [tmp_fasta, tmp_model]:
        if tmp and os.path.exists(tmp.name):
            os.unlink(tmp.name)

print('<br><br><a href="../gor.html" class="back">← Return</a></body></html>')
