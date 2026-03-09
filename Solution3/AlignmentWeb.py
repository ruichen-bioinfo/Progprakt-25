#!/usr/bin/biopython


#print("debug1")
#import time
print("Content-type:text/html\n\n")
#start = time.time()
#print("A", time.time() - start)
import mycgi
#print("B", time.time() - start)
import subprocess
#print("C", time.time() - start)
import sys

Hom = False
form = mycgi.Form()
#print("G", time.time() - start)

seq1 = form.getvalue("seq1")
seq2 = form.getvalue("seq2")

if(seq1 and seq2):
    seq1 = seq1.replace(" ", "").replace("\n", "")
    seq2 = seq2.replace(" ", "").replace("\n", "")

validate = form.getvalue("validate")
showids = form.getvalue("showids")
matrix = form.getvalue("matrix") or "blosum62"
go = form.getvalue("go") or "-12"
ge = form.getvalue("ge") or "-1"
mode = form.getvalue("mode") or "global"
algo = form.getvalue("algorithm") or "gotoh"
form_file = form["fasta"] if "fasta" in form else None
filepairs = form.getvalue("filepairs") or "first2"
showdp = form.getvalue("showdp")
pair1 = form.getvalue("validate_pair1")
pair2 = form.getvalue("validate_pair2")
validate_file = form.getvalue("validate_file")

pdb1 = form.getvalue("pdb1")
pdb2 = form.getvalue("pdb2")
pdb1single = form.getvalue("pdb1single")
if pdb1single:
    pdb1single = pdb1single.strip().lower()

#print("E", time.time() - start)
if showids or pdb1single or pdb1 or pdb2:
    import mysql.connector
#    print("sql", time.time() - start)
    from db_config import DB_CONFIG



print("<html><body style='background-color:#F4F7F6; font-family:Arial, Helvetica, sans-serif;'>")
print("""<style>
.header{
background:#2C3E50;
color:white;
text-align:center;
font-size:50px;
padding:25px;
margin:0;
}
</style>""")
print('<h1 class="header">Alignments</h1>')
print('<hr style="width:60%; margin:20px auto;">')
print('<h2 style="text-align:center; color:#2C3E50;">Sequence Alignment Tool</h2>')
print("""
<p style="text-align:center; max-width:800px; margin:auto;">
This tool can compute pairwise sequence alignments using Needleman-Wunsch or Gotoh.
If a HOMSTRAD reference alignment is available, additional validation metrics
(sensitivity, specificity, coverage and shift error) can be calculated.
</p>
""")



print("""
<style>
.runbutton{
    background-color:#439c9a;
    color:white;
    font-size:22px;
    font-weight:bold;
    padding:15px 40px;
    border:none;
    border-radius:10px;
    cursor:pointer;
}

.runbutton:hover{
    background-color:#e65c00;
    transform:scale(1.05);
}
</style>

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
<small>Upload a file containing sequences</small></p>

Pairs:<br>
<select name = "filepairs">
  <option value="first2">First 2</option>
  <option value="all">All</option>
</select><br><br>
<small>Which Sequences Will be aligned</small></p>

</div>
<div style="flex:1;">
<h3>Database search</h3>
<p>Single PDB_ID search (Prefix)<p>
<small>Outputs all Alignments of the Protein's Family</small></p>
<small>Example: "1qh8a" or "1q"</small></p>
PDB_ID: <input type="text" name="pdb1single"><br><br>

<p>Two PDB_ID search<p>
<small>Pairwise Alignment of the two Proteins and Homstrad Reference</small></p>
<small>Example: "1pfc" and "1cqka"</small></p>
PDB_ID 1: <input type="text" name="pdb1"><br><br>
PDB_ID 2: <input type="text" name="pdb2"><br><br>
<small>List Database Entries</small></p>
<input type="submit" name="showids" value="Show available IDs">



</div>
</div>


<div style="text-align:center; margin-top:30px;">
<input type="submit" value="Run Alignment" class="runbutton">
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

<label>
<input type="checkbox" name="showdp">
 Show DP Matrices
</label>
<br><br>



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

if showids or pdb1single or pdb1 or pdb2:

    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()
    except Exception as e:
        print("<pre>DB ERROR:", e, "</pre>")

if showids:
    #print("ACHTUNG!")
    cursor.execute("""
    SELECT seq_id AS id, 'Homstrad' AS source
    FROM alignment_member
    UNION
    SELECT accession AS id, source 
    FROM sequences
    ORDER BY id
    """)

    rows = list(cursor)
    cols = 12

    print("<table border='1'>")
    for i in range(0, len(rows), cols):
        print("<tr>")
        for j in range(cols):
            if i + j < len(rows):
                id, source = rows[i + j]
                print(f"<td>{id}<br><small>{source}</small></td>")
            else:
                print("<td></td>")
        print("</tr>")

    print("</table>")

    for id, source in cursor:
        print(f"<tr><td>{id}</td><td>{source}</td></tr>")

    print("</table>")


if pdb1single and len(pdb1single) >= 2:
    #print("ACHTUNG2")
    seqs = {}
    homstradalis= {}
    query = """
    SELECT am.seq_id, am.aligned_sequence
        FROM alignment_member am
        WHERE am.family_id = (
    SELECT family_id
    FROM alignment_member
    WHERE seq_id LIKE %s
    LIMIT 1
    )
    """


    cursor.execute(query, (pdb1single + "%",)) #soll Praefix suche sein

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
    #print("Achtung!")
    Hom = True
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

    if len(rows) == 0:
        print("ACHTUNG")
        Hom = False

        query = """
        SELECT seq_id, aligned_sequence
        FROM alignment_member
        WHERE seq_id IN (%s,%s)
        
        UNION
        
        SELECT accession, sequence
        FROM sequences
        WHERE accession IN (%s,%s)
        """

        cursor.execute(query,(pdb1,pdb2,pdb1,pdb2))
        rows = cursor.fetchall()

        if len(rows) > 1:
            print(f"no Homstrad Reference Alignment available for {pdb1} and {pdb2}")
            print("either they aren't in the same family or Homstrad is not the source")

        for acc, seq in rows:
            seq = seq.replace("-", "").replace(".", "").replace("/", "")
            seqs[acc] = seq
    else:
        Hom = True
        for seq_id, aligned_sequence in rows:
            seq = aligned_sequence.replace("-", "").replace(".", "").replace("/", "")
            seqs[seq_id] = seq
            homstradalis[seq_id] = aligned_sequence

    names = list(seqs.keys())

if pdb1single or (pdb1 and pdb2 and Hom):

    msa_path = "/home/w/wendrichj/outputAli/homstrad_msa.txt"

    with open(msa_path, "w") as f:
        for name, ali in homstradalis.items():
            f.write(name + " " + ali + "\n")

if Hom:
    print("<p style='text-align:center;'>Validation available for this alignment</p>")
    print("""
    <form method="post">
    <div style="text-align:center; margin-top:20px;">
    <input type="submit" name="validate" value="Validate Alignment" class="runbutton">
    </div>
    </form>
    """)


if validate or validate_file:
    if validate_file:
        file_to_use = "/home/w/wendrichj/outputAli/" + validate_file
    else:
        file_to_use = "/home/w/wendrichj/outputAli/validation.txt"

    cmd = [
        "java",
        "-jar",
        "/mnt/extstud/praktikum/bioprakt/progprakt-11/Solution3/finaljars/validateAli.jar",
        "-f",
        file_to_use
    ]

    try:
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)

        print("<h2>Validation Results</h2>")
        print("<pre style='background:#f0f0f0;padding:10px;'>")
        print(result.decode("utf-8"))
        print("The scores represent: Sensitivity, Specificity, Coverage, Mean Shift Error, Inverse Mean Shift Error")
        print("</pre>")

    except subprocess.CalledProcessError as e:
        print("<pre>")
        print(e.output.decode("utf-8"))
        print("</pre>")

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
        if Hom:
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

    #if pdb1 and pdb2 and Hom:
    #    cmd.append("--DB")
    #    cmd.append("--ali")
    #    cmd.append("/home/w/wendrichj/outputAli/homstradAli.txt")

    if algo == "nw":
        cmd.append("--nw")

    if showdp:
        cmd.append("--dpmatrices")
        cmd.append("DPMatrixOut")

    if pdb1single or (pdb1 and pdb2 and Hom):
        cmd.append("--DB")
        cmd.append("--ali")
        cmd.append(msa_path)
        cmd.append("--validation")


    print("test")
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

if showids or pdb1single or pdb1 or pdb2:
    cnx.close()