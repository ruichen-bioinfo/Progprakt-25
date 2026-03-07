#!/usr/bin/env python3

# Send HTTP header FIRST
import sys
sys.stdout.write("Content-Type: text/html\r\n\r\n")
sys.stdout.flush()


# Imports functions directly from get_pdb.py and visualize_all.py (must be in cgi-bin/)
# Flow:
#   1. fetch_pdb()      <- get_pdb.py        : download PDB text from RCSB
#   2. pdb_2_fasta()    <- get_pdb.py        : extract FASTA sequence
#   3. analyze_pdb()    <- visualize_all.py  : SS ratio, Ca/Cb dist, bounding box
#   4. generate_image() <- visualize_all.py  : Jmol cartoon PNG (if jar available)
#   5. DSSP file lookup : pre-computed at DATA_DSSP/<xy>/<id>.dssp

import cgi, cgitb, os, time, html as H, tempfile
cgitb.enable()

CGI_DIR = os.path.dirname(__file__)
sys.path.insert(0, CGI_DIR)

# Import functions
from get_pdb      import fetch_pdb, pdb_2_fasta
from visualize_all import analyze_pdb, parse_secondary_structure

import gor_config as C

# Pre-computed DSSP archive (subdir layout: DSSP/<chars1-2>/<id>.dssp)
DATA_DSSP = "/mnt/extstud/praktikum/bioprakt/Data/DSSP"
JMOL_JAR  = "/mnt/extsoft/software/jmol/JmolData.jar"

# DSSP 8-state to 3-state mapping
DSSP_3STATE = {
    'H': 'H', 'G': 'H', 'I': 'H',
    'E': 'E', 'B': 'E',
    'T': 'C', 'S': 'C', ' ': 'C', '-': 'C',
}
SS_COLOR = {'H': '#e74c3c', 'E': '#3498db', 'C': '#95a5a6'}
SS_LABEL = {'H': 'H - Alpha Helix', 'E': 'E - Beta Sheet', 'C': 'C - Coil'}

def find_dssp_file(pid):
    # Standard PDB archive layout: DSSP/<chars1-2 of pid>/<pid>.dssp
    pid_lower = pid.lower()
    subdir    = pid_lower[1:3]
    for candidate in [
        os.path.join(DATA_DSSP, subdir, pid_lower + ".dssp"),
        os.path.join(DATA_DSSP, subdir, pid.upper() + ".dssp"),
        os.path.join(DATA_DSSP, pid_lower + ".dssp"),
    ]:
        if os.path.isfile(candidate):
            return candidate
    return None

def parse_dssp_file(text):
    # Parse DSSP output into list of residue dicts
    residues = []
    in_data  = False
    for line in text.splitlines():
        if line.strip().startswith("#  RESIDUE"):
            in_data = True
            continue
        if not in_data or len(line) < 17:
            continue
        aa      = line[13]
        ss      = line[16] if len(line) > 16 else ' '
        chain   = line[11]
        res_str = line[5:10].strip()
        acc_str = line[35:38].strip() if len(line) > 38 else '0'
        if aa in ('!', '*') or not res_str.isdigit() or aa.islower():
            continue
        residues.append({
            'resnum': int(res_str),
            'chain':  chain,
            'aa':     aa,
            'ss_raw': ss,
            'ss':     DSSP_3STATE.get(ss, 'C'),
            'acc':    int(acc_str) if acc_str.isdigit() else 0,
        })
    return residues

def render_ss_bar(residues):
    # Colored sequence bar, 60 residues per row(optional, can be 80)
    rows = []
    for start in range(0, len(residues), 60):
        block = residues[start:start+60]
        rows.append('<div class="ss-row">')
        rows.append(f'<span class="rnum">{start+1}</span>')
        rows.append('<span class="ssbar">')
        for r in block:
            col   = SS_COLOR[r['ss']]
            tip   = f"{r['aa']}{r['resnum']} chain {r['chain']} | {r['ss']} ({r['ss_raw'].strip() or '-'})"
            rows.append(f'<span class="aa" style="background:{col}" title="{H.escape(tip)}">'
                        f'{H.escape(r["aa"])}</span>')
        rows.append('</span></div>')
    return "\n".join(rows)

def try_generate_image(pid):
    # Try Jmol headless image generation, return image path or None
    if not os.path.isfile(JMOL_JAR):
        return None
    import subprocess
    out_dir  = os.path.join(C.PUBLIC_HTML, "uploads")
    out_file = os.path.join(out_dir, f"{pid.upper()}.png")
    if os.path.isfile(out_file):
        return out_file   # already cached
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jmol',
                                     delete=False, dir=C.TMP_DIR) as f:
        f.write(f"load ={pid}\ncartoon\nwrite image {out_file}\nquit\n")
        script = f.name
    try:
        subprocess.run(['java', '-jar', JMOL_JAR, '--script', script],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=60)
        os.unlink(script)
        return out_file if os.path.isfile(out_file) else None
    except Exception:
        try: os.unlink(script)
        except: pass
        return None

# Read form
form   = cgi.FieldStorage()
pdb_id = form.getvalue("pdb_id", "").strip().upper()

# HTML head
print("""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>DSSP Visualization</title>
<style>
body{font-family:'Segoe UI',sans-serif;background:#f4f7f6;color:#333;padding:2rem;margin:0;}
h2{color:#2c3e50;margin-bottom:.5rem;}
h3{color:#2980b9;border-bottom:2px solid #3498db;padding-bottom:6px;margin-bottom:14px;}
.card{background:white;border-radius:8px;box-shadow:0 2px 5px rgba(0,0,0,.1);
      padding:20px;margin-bottom:20px;}
.ok{color:#27ae60}.err{color:#e74c3c}
.back{color:#3498db;text-decoration:none;font-size:.9rem;}
/* Stats grid */
.sgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:14px;margin:14px 0;}
.scard{background:#f8f9fa;border:1px solid #ddd;border-radius:6px;padding:12px;text-align:center;}
.sval{font-size:1.4rem;font-weight:700;color:#2980b9;}
.slbl{color:#888;font-size:.78rem;margin-top:3px;}
/* SS bar */
.ss-row{margin:3px 0;font-family:'Courier New',monospace;font-size:12px;
        display:flex;align-items:center;gap:8px;}
.rnum{color:#aaa;font-size:10px;min-width:36px;text-align:right;}
.ssbar{display:flex;flex-wrap:nowrap;}
.aa{display:inline-block;width:12px;text-align:center;color:white;font-weight:700;
    font-size:10px;cursor:default;}
/* Legend */
.legend{display:flex;gap:16px;font-size:.85rem;margin-bottom:14px;flex-wrap:wrap;}
.ldot{width:18px;height:11px;border-radius:2px;display:inline-block;
      margin-right:4px;vertical-align:middle;}
/* Raw output */
pre{background:#2d3436;color:#dfe6e9;border-radius:5px;font-size:11px;
    padding:1rem;overflow-x:auto;max-height:300px;overflow-y:auto;white-space:pre;}
/* Two-col */
.two{display:grid;grid-template-columns:1fr 1fr;gap:20px;}
@media(max-width:640px){.two{grid-template-columns:1fr;}}
table{border-collapse:collapse;font-size:.88rem;width:100%;}
th{border-bottom:2px solid #3498db;color:#2980b9;padding:7px 8px;text-align:left;}
td{border-bottom:1px solid #eee;padding:6px 8px;}
td:first-child{color:#555;font-weight:600;}
</style></head><body>
""")

if not pdb_id or len(pdb_id) != 4 or not pdb_id.isalnum():
    print('<div class="card"><p class="err">X Please enter a valid 4-character PDB ID (e.g. 1MBN).</p></div>')
    print('<a href="../gor.html" class="back">&lt;- Return</a></body></html>')
    sys.exit(0)

print(f'<h2>DSSP Analysis: {H.escape(pdb_id)}</h2>')
sys.stdout.flush()

t0 = time.time()
try:
    # 1. Fetch PDB text using get_pdb.py
    pdb_text = fetch_pdb(pdb_id)

    # 2. Get FASTA using get_pdb.py
    fasta_text = pdb_2_fasta(pdb_text, pdb_id)

    # 3. Structural stats using visualize_all.py
    struct_data = analyze_pdb(pdb_text)

    # 4. DSSP residue-level SS from pre-computed file
    dssp_path = find_dssp_file(pdb_id)
    dssp_text = None
    residues  = []
    if dssp_path:
        with open(dssp_path) as f:
            dssp_text = f.read()
        residues = parse_dssp_file(dssp_text)

    elapsed = round(time.time() - t0, 2)
    print(f'<p class="ok">Loaded {H.escape(pdb_id)} in {elapsed}s '
          f'({len(residues)} residues from DSSP)</p>')

    # Structural stats (from visualize_all.py)
    print('<div class="card"><h3>Structural Parameters</h3>')
    print('<div class="sgrid">')
    stats_items = [
        ("SS Fraction",        f"{struct_data['ss_ratio']*100:.1f}%"),
        ("C&alpha; End-to-End",f"{struct_data['ca_dist']:.2f} &Aring;"),
        ("C&beta; End-to-End", f"{struct_data['cb_dist']:.2f} &Aring;"),
        ("X span",             f"{struct_data['x_len']:.1f} &Aring;"),
        ("Y span",             f"{struct_data['y_len']:.1f} &Aring;"),
        ("Z span",             f"{struct_data['z_len']:.1f} &Aring;"),
        ("Bounding Volume",    f"{struct_data['volume']:.0f} &Aring;&sup3;"),
    ]
    for lbl, val in stats_items:
        print(f'<div class="scard"><div class="sval">{val}</div>'
              f'<div class="slbl">{lbl}</div></div>')
    print('</div></div>')

    # FASTA sequence
    if fasta_text:
        print('<div class="card"><h3>FASTA Sequence</h3>')
        print(f'<pre>{H.escape(fasta_text[:3000])}</pre>')
        import base64
        b64 = base64.b64encode(fasta_text.encode()).decode()
        print(f'<a href="data:text/plain;base64,{b64}" download="{pdb_id.lower()}.fasta" '
              f'style="color:#3498db;font-weight:600;">Download FASTA</a>')
        print('</div>')

    # DSSP SS bar + composition
    if residues:
        total  = len(residues)
        counts = {'H': 0, 'E': 0, 'C': 0}
        for r in residues:
            counts[r['ss']] += 1

        print('<div class="two">')

        # Composition
        print('<div class="card"><h3>SS Composition (DSSP)</h3>')
        print('<div class="sgrid" style="grid-template-columns:repeat(3,1fr);">')
        for k in ['H', 'E', 'C']:
            cnt = counts[k]
            pct = cnt / total * 100
            print(f'<div class="scard">'
                  f'<div class="sval" style="color:{SS_COLOR[k]}">{pct:.1f}%</div>'
                  f'<div class="slbl">{SS_LABEL[k]}<br>({cnt} res)</div></div>')
        print('</div></div>')

        # Per-chain breakdown
        chains = {}
        for r in residues:
            c = r['chain']
            if c not in chains:
                chains[c] = {'H':0,'E':0,'C':0,'total':0}
            chains[c][r['ss']] += 1
            chains[c]['total'] += 1

        print('<div class="card"><h3>Per-Chain Breakdown</h3>')
        print('<table><thead><tr><th>Chain</th><th>Total</th>'
              '<th style="color:#e74c3c;">H%</th>'
              '<th style="color:#3498db;">E%</th>'
              '<th style="color:#95a5a6;">C%</th></tr></thead><tbody>')
        for ch, d in sorted(chains.items()):
            t = d['total']
            print(f'<tr><td>{H.escape(ch)}</td><td>{t}</td>'
                  f'<td>{d["H"]/t*100:.1f}%</td>'
                  f'<td>{d["E"]/t*100:.1f}%</td>'
                  f'<td>{d["C"]/t*100:.1f}%</td></tr>')
        print('</tbody></table></div>')
        print('</div>')  # .two

        # SS bar
        print('<div class="card"><h3>Secondary Structure Sequence</h3>')
        print('<div class="legend">')
        for k in ['H','E','C']:
            print(f'<span><span class="ldot" style="background:{SS_COLOR[k]}"></span>'
                  f'{SS_LABEL[k]}</span>')
        print('</div>')
        print(render_ss_bar(residues))
        print('</div>')

        # Raw DSSP
        print('<div class="card"><h3>Raw DSSP Output</h3>')
        print(f'<pre>{H.escape(dssp_text[:6000])}</pre>')
        if len(dssp_text) > 6000:
            print('<p style="color:#aaa;font-size:.85rem;">Truncated to 6000 chars.</p>')
        b64 = base64.b64encode(dssp_text.encode()).decode()
        print(f'<a href="data:text/plain;base64,{b64}" download="{pdb_id.lower()}.dssp" '
              f'style="color:#3498db;font-weight:600;">Download .dssp</a>')
        print('</div>')

    elif not dssp_path:
        print(f'<div class="card"><p style="color:#e67e22;">No pre-computed DSSP file found '
              f'for {H.escape(pdb_id)} in the local database.</p></div>')

    # Jmol image (optional)
    img_path = try_generate_image(pdb_id)
    if img_path and os.path.isfile(img_path):
        rel = os.path.relpath(img_path, C.PUBLIC_HTML)
        print('<div class="card"><h3>3D Structure (Cartoon)</h3>')
        print(f'<img src="../{rel}" alt="{H.escape(pdb_id)} cartoon" '
              f'style="max-width:100%;border-radius:6px;">')
        print('</div>')

except IOError as e:
    print(f'<div class="card"><p class="err">X Could not fetch PDB {H.escape(pdb_id)}: '
          f'{H.escape(str(e))}</p></div>')
except Exception as e:
    print(f'<div class="card"><p class="err">X Error: {H.escape(str(e))}</p></div>')

print('<br><a href="../gor.html" class="back">&lt;- Return</a></body></html>')