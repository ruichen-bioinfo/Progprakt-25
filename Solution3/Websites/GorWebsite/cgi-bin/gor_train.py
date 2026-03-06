#!/usr/bin/env python3

# Send HTTP header FIRST before any import can fail and cause 500 error
import sys
sys.stdout.write("Content-Type: text/html\r\n\r\n")
sys.stdout.flush()

# Format: db_file (Upload) or db_preset, method, model_name
# Usage: java -jar GORFiles/jars/train.jar --db <db> --method <m> --model GORFiles/models/<n>.mod

import cgi, cgitb, os, subprocess, tempfile, time
cgitb.enable()
sys.path.insert(0, os.path.dirname(__file__))
import gor_config as C

form        = cgi.FieldStorage()
method      = form.getvalue("method", "gor3").lower()
db_preset   = form.getvalue("db_preset", "cb513")
model_name  = form.getvalue("model_name", "my_model").strip().replace("/","_").replace("..","_")

# db path
tmp_db = None
if "db_file" in form and form["db_file"].filename:
    tmp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db",
                                         dir=C.TMP_DIR, mode="wb")
    tmp_db.write(form["db_file"].file.read())
    tmp_db.close()
    db_path = tmp_db.name
elif db_preset in C.PRESET_DBS:
    db_path = C.PRESET_DBS[db_preset]
else:
    print("<p>X No Database Found, Please Upload File or Use Preset Data.</p>")
    sys.exit(0)

if not os.path.isfile(db_path):
    print(f"<p>X Database File doesn't Exist: {db_path}</p>")
    sys.exit(0)

# Output model path
model_out = os.path.join(C.MODELS_DIR, f"{model_name}_{method}.mod")

# Build command
cmd = [C.JAVA] + C.JAVA_MEM + [
    "-jar",     C.TRAIN_JAR,
    "--db",     db_path,
    "--method", method,
    "--model",  model_out,
]

# HTML output
print(f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Train</title>
<style>
body{{font-family:monospace;background:#0d0f14;color:#c8cdd8;padding:2rem;}}
pre{{background:#000;border:1px solid #333;padding:1rem;white-space:pre-wrap;color:#7de8c5;}}
.ok{{color:#00d4aa}}.err{{color:#e05c73}}.back{{color:#00d4aa;text-decoration:none;}}
</style></head><body>
<h2>GOR Training -- {method.upper()} on {db_preset}</h2>
<p>Command: <code>{" ".join(cmd)}</code></p>
<pre>""")
sys.stdout.flush()

t0 = time.time()
try:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True, timeout=C.TIMEOUT)
    elapsed = round(time.time() - t0, 1)

    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(f"\n--- stderr ---\n{proc.stderr}")

    print("</pre>")

    if proc.returncode == 0 and os.path.isfile(model_out):
        size_kb = round(os.path.getsize(model_out) / 1024, 1)
        # Web-accessible path relative to public_html
        rel = os.path.relpath(model_out, C.PUBLIC_HTML)
        print(f'<p class="ok">Done, runtime {elapsed}s -- Model saved ({size_kb} KB)</p>')
        print(f'<p><a href="../{rel}" download class="back">Download {os.path.basename(model_out)}</a></p>')
    else:
        print(f'<p class="err">Training failed (exit code {proc.returncode})</p>')

except subprocess.TimeoutExpired:
    print(f'</pre><p class="err">Timeout ({C.TIMEOUT}s)</p>')
except FileNotFoundError:
    print(f'</pre><p class="err">Java not found: {C.JAVA}</p>')
finally:
    if tmp_db and os.path.exists(tmp_db.name):
        os.unlink(tmp_db.name)

print('<br><a href="../gor.html" class="back">&lt;- Return</a></body></html>')