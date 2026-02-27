#!/usr/bin/env python3
import argparse
from get_pdb import fetch_pdb #get fetch_pdb
import subprocess #use terminal
import tempfile
import os
def parse_args():
    p=argparse.ArgumentParser()
    p.add_argument('--id',required=True)
    p.add_argument("--output")
    p.add_argument("--html",action="store_true")
    p.add_argument("--colorized",action="store_true")
    return p.parse_args()
def create_script(pid,pdb,output,colorized): #create jmol script
    script=[]
    script.append(f"load {pdb}")
    script.append("cartoon")
    if colorized:
        script.append("color structure")
    script.append(f"write image 800 600 PNG {output}")
    script.append("exit")
    print(script)
    return"\n".join(script)

def main():
    args = parse_args()
    pdb_text=fetch_pdb(args.id)
    with tempfile.NamedTemporaryFile(delete=False,suffix=".pdb") as pdb_file:
        pdb_file.write(pdb_text.encode("utf-8"))
        pdb=pdb_file.name
    output=args.output if args.output else f"{args.id.upper()}.png"
    script_text=create_script(args.id,pdb,output,args.colorized)
    with tempfile.NamedTemporaryFile(delete=False,suffix=".spt") as script_file:
        script_file.write(script_text.encode("utf-8"))
        script=script_file.name
    subprocess.run([
        "java","-jar","Jmol.jar","-n","-s", script
    ])
    os.remove(script)
    os.remove(pdb)
if __name__=="__main__":
    main()
