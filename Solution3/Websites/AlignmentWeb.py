#!/usr/bin/biopython
print("Content-type:text/html\n\n")

#print("debug1")

import cgitb
cgitb.enable()

import mycgi
import subprocess

import sys
import mysql.connector
from db_config import DB_CONFIG



form = mycgi.Form()

seq1 = form.getvalue("seq1")
seq2 = form.getvalue("seq2")

if(seq1 and seq2):
    seq1 = seq1.replace(" ", "").replace("\n", "")
    seq2 = seq2.replace(" ", "").replace("\n", "")



matrix = form.getvalue("matrix") or "blosum62"
go = form.getvalue("go") or "-12"
ge = form.getvalue("ge") or "-1"
mode = form.getvalue("mode") or "global"
algo = form.getvalue("algorithm") or "gotoh"
form_file = form["fasta"] if "fasta" in form else None
filepairs = form.getvalue("filepairs") or "first2"

pdb1 = form.getvalue("pdb1")
pdb2 = form.getvalue("pdb2")
pdb1single = form.getvalue("pdb1single")
if pdb1single:
    pdb1single = pdb1single.strip().lower()



print("<html><body style='background-color:#e6f2ff;'>")
print('<h1 style="text-align:center; font-size:50px; color:#003366;">Alignments</h1>')
print('<hr style="width:60%; margin:20px auto;">')
print('<h2 style="text-align:center; color:#333333;">Sequence Alignment Tool</h2>')


print("""
<form method="post" enctype="multipart/form-data">
<div style="display:flex; gap:40px;">

<div style="flex:1;">
<h3>Sequence Text Input</h3>
Sequence 1:<br>
<textarea name="seq1" rows="5" cols="60"></textarea><br><br>

Sequence 2:<br>
<textarea name="seq2" rows="5" cols="60"></textarea><br><br>

</div>

<div style="flex:1;">

<h3>Fasta Upload</h3>

<input type="file" name="fasta"><br><br>
<p>Upload a file containing sequences</p>

Pairs:<br>
<select name = "filepairs">
  <option value="first2">First 2</option>
  <option value="all">All</option>
</select><br><br>

</div>
<div style="flex:1;">
<h3>Database search</h3>
<p>Single PDB_ID search (Substring)<p>
<small>Outputs all Alignments of the Protein's Family</small></p>
<small>Example: "1qh8a" or "qh"</small></p>
PDB_ID: <input type="text" name="pdb1single"><br><br>

<p>Two PDB_ID search<p>
PDB_ID 1: <input type="text" name="pdb1"><br><br>
PDB_ID 2: <input type="text" name="pdb2"><br><br>

</div>
</div>
<h3>Alignment Parameters</h3>

Algorithm:<br>

<input type="radio" name="algorithm" value="gotoh" checked> Gotoh<br>
<input type="radio" name="algorithm" value="nw"> Needleman-Wunsch<br>

Mode:<br>
<select name="mode">
  <option value="global">Global</option>
  <option value="local">Local</option>
  <option value="freeshift">Freeshift</option>
</select><br><br>

Matrix:<br>
<select name="matrix">
  <option value="BlakeCohenMatrix">Blake-Cohen</option>
  <option value="blosum62">BLOSUM62</option>
  <option value="pam250">PAM250</option>
  <option value="dayhoff">Dayhoff</option>
</select><br><br>

Gap Open:
<input type="number" name="go" value="-12">

Gap Extend:
<input type="number" name="ge" value="-1">

<input type="submit" value="Run Alignment">

</form>
""")

#print("<pre>")
#print("seq1:", seq1)
#print("seq2:", seq2)
#print("</pre>")

if form_file and form_file.filename:
    fasta = form_file.file.read().decode("utf-8")
    seqs = {}
    current = None

    for line in fasta.splitlines():
        if line.startswith(">"):
            current = line[1:].split()[0].split("|")[-1]
            seqs[current] = ""
        else:
            if current:
                seqs[current] += line.strip()

    names = list(seqs.keys())

    if len(names) < 2:
        print("Fasta contains less than 2 sequences")

try:
    cnx = mysql.connector.connect(**DB_CONFIG)
    cursor = cnx.cursor()
except Exception as e:
    print("<pre>DB ERROR:", e, "</pre>")

if pdb1single and len(pdb1single) >= 2:
    seqs = {}
    homstradalis= {}
    query = """
    SELECT am.seq_id,
           am.aligned_sequence
    FROM alignment_member am
    WHERE am.family_id IN (
        SELECT family_id
        FROM alignment_member
        WHERE seq_id LIKE %s
    )
    """

    cursor.execute(query, ("%" + pdb1single + "%",)) #soll substring suche sein

    rows = cursor.fetchall()

    print("<pre>")
    print("Input:", pdb1single)
    print("Rows found:", len(rows))
    print("</pre>")

    for seq_id, aligned_sequence in rows:
        seq = aligned_sequence.replace("-", "").replace(".", "").replace("/", "")
        seqs[seq_id] = seq
        homstradalis[seq_id] = aligned_sequence

    names = list(seqs.keys())


if(pdb1 and pdb2):
    seqs = {}
    homstradalis = {}
    query = """
        SELECT am.seq_id, am.aligned_sequence
        FROM alignment_member am
        WHERE am.family_id = (
            SELECT a.family_id
            FROM alignment_member a
            JOIN alignment_member b
              ON a.family_id = b.family_id
            WHERE a.seq_id = %s
            AND b.seq_id = %s
            LIMIT 1
        );
        """

    cursor.execute(query, (pdb1, pdb2))

    rows = cursor.fetchall()

    print("<pre>")
    print("Input:", pdb1, pdb2)
    print("Rows found:", len(rows))
    print("</pre>")

    for seq_id, aligned_sequence in rows:
        seq = aligned_sequence.replace("-", "").replace(".", "").replace("/", "")
        seqs[seq_id] = seq
        homstradalis[seq_id] = aligned_sequence

    names = list(seqs.keys())

if (seq1 and seq2) or (form_file and form_file.filename) or pdb1single or (pdb1 and pdb2):
    matrixpath = f"/mnt/extstud/praktikum/bioprakt/Data/MATRICES/{matrix}.mat"

    seqlib_path = "/home/w/wendrichj/outputAli/seqLib.txt"
    pairs_path = "/home/w/wendrichj/outputAli/pairs.txt"

    if seq1 and seq2:
        with open(seqlib_path, "w") as f:
            f.write("seq1:" + seq1 + "\n")
            f.write("seq2:" + seq2 + "\n")

        with open(pairs_path, "w") as f:
            f.write("seq1 seq2\n")

    elif form_file and form_file.filename:
        with open(seqlib_path, "w") as f:
            for name, seq in seqs.items():
                f.write(f"{name}:{seq}\n")
        if filepairs == "first2":
            with open(pairs_path, "w") as f:
                f.write(f"{names[0]} {names[1]}\n")
        if filepairs == "all":
            with open(pairs_path, "w") as f:
                for i in range(len(names)):
                    for j in range(i + 1, len(names)):
                        f.write(f"{names[i]} {names[j]}\n")

    elif pdb1single:
        with open(seqlib_path, "w") as f:
            for name, seq in seqs.items():
                f.write(f"{name}:{seq}\n")
        with open(pairs_path, "w") as f:
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    f.write(f"{names[i]} {names[j]}\n")

    elif pdb1 and pdb2:

        with open(seqlib_path, "w") as f:
            for name, seq in seqs.items():
                f.write(f"{name}:{seq}\n")
        with open(pairs_path, "w") as f:
            f.write(f"{pdb1} {pdb2}\n")

        with open("/home/w/wendrichj/outputAli/homstradAli.txt", "w") as f:

            seq1 = seqs[pdb1]
            seq2 = seqs[pdb2]

            ali1 = homstradalis[pdb1]
            ali2 = homstradalis[pdb2]

            f.write(f"Seq1 {pdb1} {seq1}\n")
            f.write(f"Seq2 {pdb2} {seq2}\n")
            f.write(f"Aligned1 {ali1}\n")
            f.write(f"Aligned2 {ali2}\n")
            f.write("Mode G\n")


    cmd = [
        "java",
        "-jar",
        "/mnt/extstud/praktikum/bioprakt/progprakt-11/Solution3/finaljars/gruppe11.jar",
        "--pairs", pairs_path,
        "--seqlib", seqlib_path,
        "-m", matrixpath,
        "--go", go,
        "--ge", ge,
        "--mode", mode,
        "--format", "html"
    ]

    if pdb1 and pdb2:
        cmd.append("--DB")
        cmd.append("--ali")
        cmd.append("/home/w/wendrichj/outputAli/homstradAli.txt")

    if algo == "nw":
        cmd.append("--nw")

    try:
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        print(result.decode("utf-8"))
    except subprocess.CalledProcessError as e:
        print("<pre>")
        print(e.output.decode("utf-8"))
        print("</pre>")

    if(pdb1single):
        print("<h2>HOMSTRAD Alignment</h2>")
        print("<pre>")

        for name, ali in homstradalis.items():
            print(f"{name}: {ali}")

        print("</pre>")



print("</body></html>")

cnx.close()