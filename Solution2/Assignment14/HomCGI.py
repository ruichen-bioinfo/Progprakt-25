#!/usr/bin/biopython

import mycgi
import subprocess

print("Content-type:text/html\n\n")

form = mycgi.Form()
pdb1 = form.getvalue("pdb1")

print("<html><body>")
print("<h1>Homstrad Search</h1>")

if not pdb1:
    print("""
    <form method="post">
    PDB ID: <input type="text" name="pdb1">
    <input type="submit">
    </form>
    """)
else:
    try:
        result = subprocess.check_output(
            [
                "python3",
                "/mnt/extstud/praktikum/bioprakt/progprakt-11/Solution2/Assignment14/Hom.py",

                pdb1
            ]
        )

        print("<pre>")
        print(result.decode("utf-8"))
        print("</pre>")

    except Exception as e:
        print("Error")

print("</body></html>")