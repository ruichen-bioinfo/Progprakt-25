#!/usr/bin/biopython

import cgitb
cgitb.enable()

import mycgi
import subprocess

print("Content-type:text/html\n\n")

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



print("<html><body>")
print("<h1>Alignments</h1>")
print("<h2>Alignments Text</h2>")


print("""
<form method="post" enctype="multipart/form-data">
Sequence 1:<br>
<textarea name="seq1" rows="5" cols="60"></textarea><br><br>

Sequence 2:<br>
<textarea name="seq2" rows="5" cols="60"></textarea><br><br>

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

print("<pre>")
print("seq1:", seq1)
print("seq2:", seq2)
print("</pre>")

if(seq1 and seq2):
    matrixpath = f"/mnt/extstud/praktikum/bioprakt/Data/MATRICES/{matrix}.mat"

    seqlib_path = "/tmp/seqLib.txt"
    pairs_path = "/tmp/pairs.txt"

    with open(seqlib_path, "w") as f:
        f.write("seq1:" + seq1 + "\n")
        f.write("seq2:" + seq2 + "\n")

    with open(pairs_path, "w") as f:
        f.write("seq1 seq2\n")

    algoflag = ""
    algoflag2 = ""

    if(algo=="nw"):
        algoflag = f"--{algo}"

    cmd = [
        "java",
        "-jar",
        "/mnt/extstud/praktikum/bioprakt/progprakt-11/Solution3/finaljars/alignment.jar",
        "--pairs", pairs_path,
        "--seqlib", seqlib_path,
        "-m", matrixpath,
        "--go", go,
        "--ge", ge,
        "--mode", mode,
        "--format", "html"
    ]

    if algo == "nw":
        cmd.append("--nw")


    try:
        result = subprocess.check_output(cmd)
        print(result.decode("utf-8"))
    except subprocess.CalledProcessError as e:
        print("<pre>")
        print(e.output.decode("utf-8"))
        print("</pre>")



print("</body></html>")