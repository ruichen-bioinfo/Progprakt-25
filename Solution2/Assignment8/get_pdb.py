#!/usr/bin/env python3
import argparse
import sys
import urllib.request
import urllib.error
PDB_2_FASTA= {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D",
    "CYS": "C", "GLN": "Q", "GLU": "E", "GLY": "G",
    "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S",
    "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
    "SEC": "U", "PYL": "O", "ASX": "B", "GLX": "Z", "UNK": "X",
}
def parse_args():
    parser=argparse.ArgumentParser()
    parser.add_argument("--id",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--fasta",action="store_true")
    return parser.parse_args()
PDB_URL = "https://files.rcsb.org/download/{pid}.pdb"
def fetch_pdb(pid:str)->str:
    pid=pid.strip().upper()
    url=PDB_URL.format(pid=pid)
    try:
        with urllib.request.urlopen(url) as response:
            data=response.read()
        text=data.decode("utf-8",errors="replace")
        return text
    except urllib.error.HTTPError as e:
        raise IOError(e.read())
    except urllib.error.URLError as e:
        raise IOError(e.reason)
def pdb_2_fasta(pdb_text:str,pid:str)->str:
    chains={}
    for line in pdb_text.splitlines():
        if not line.startswith("SEQRES"):
            continue
        parts=line.split()
        if len(parts)<5:
            continue
        chainid=parts[2]
        pdblist=parts[4:]
        if chainid not in chains:
            chains[chainid]=[]
        for pdb in pdblist:
            pdb=pdb.upper()
            chains[chainid].append(PDB_2_FASTA.get(pdb,"X"))
    if not chains:
        return""
    outlines=[]
    for chainid in sorted(chains.keys()):
        seq="".join(chains[chainid])
        outlines.append(f">{pid.upper()}|chain_{chainid}")
        outlines.append(seq)
    return"\n".join(outlines)+"\n"
def open_output(path:str):
    if path=="-":
        return sys.stdout
    return open(path,"w",encoding="utf-8")
def main():
    args = parse_args()
    out=open_output(args.output)
    pdb_text=fetch_pdb(args.id)
    if args.fasta:
        fasra_text=pdb_2_fasta(pdb_text,args.id)
        out.write(fasra_text)
    else:
        out.write(pdb_text)

    if out is not sys.stdout:
        out.close()
if __name__=="__main__":
    main()
