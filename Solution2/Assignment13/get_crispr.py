#!/usr/bin/env python3
import argparse
from collections import defaultdict

parser = argparse.ArgumentParser()
parser.add_argument("--fasta", required=True)
args = parser.parse_args()
fasta_file = args.fasta

seq = []
header = []
fullseq = []


with open(fasta_file, "r") as f:
    for line in f:
        line = line.strip()
        if line.startswith(">"):
            if header and seq:
                fullseq.append((header[-1], "".join(seq)))
            ID = line[1:]
            header.append(ID)
            seq = []
        else:
            s = line
            seq.append(s)
    if header and seq:
        fullseq.append((header[-1], "".join(seq)))

crisprseq = defaultdict(list)

for header, seq in fullseq:
    for i in range(len(seq)-2):
        if seq[i+1:i+3] == "GG" and i >= 20:
            crispr = seq[i-20:i+3]
            startpos = i-20+1
            crisprseq[header].append(crispr)

            print(f">{header}\t{startpos}")
            print(crispr)


#with open("output.fasta", "w") as f:
#    for header, seq in crisprseq.items():

#        f.write(">".join(header)+"\n")
#        for seq in seq:
#            f.write(seq)


