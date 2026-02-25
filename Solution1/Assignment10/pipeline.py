#!/usr/bin/env python3
# pipeline.cgi - CGI script for genome to protein pipeline

import cgi
import cgitb
import subprocess
import os
import tempfile

cgitb.enable()

print("Content-Type: text/plain\n")

form = cgi.FieldStorage()


genome_file = form['genome']
features_file = form['features']

if not genome_file or not features_file:
    print("Error: Please upload both genome and features files.")
    sys.exit(0)

# Save file and as input for pipeline
with tempfile.NamedTemporaryFile(mode='w+b', suffix='.fna', delete=False) as tmp_genome:
    tmp_genome.write(genome_file.file.read())
    genome_path = tmp_genome.name

with tempfile.NamedTemporaryFile(mode='w+b', suffix='.txt', delete=False) as tmp_features:
    tmp_features.write(features_file.file.read())
    features_path = tmp_features.name

try:
    # construct pipeline with: genome2orf -> dna2mrna -> mrna2aa
    # popen connection
    p1 = subprocess.Popen(
        ['./genome2orf.py', '--organism', genome_path, '--features', features_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    p2 = subprocess.Popen(
        ['./dna2mrna.py', '--fasta', '-'],
        stdin=p1.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    p3 = subprocess.Popen(
        ['./mrna2aa.py', '--fasta', '-'],
        stdin=p2.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    # Connection
    p1.stdout.close()
    p2.stdout.close()
    output, error = p3.communicate()

    # Output
    if error:
        print("Error during pipeline:\n", error.decode())
    else:
        print(output.decode())
finally:
    # Clear
    os.unlink(genome_path)
    os.unlink(features_path)
