#!/usr/bin/env python3


import argparse
import os
import sys
import subprocess
import tempfile
import urllib.request
import urllib.error
from math import sqrt
# from get_pdb import fetch_pdb
# Import function from ASS8

PDB_URL = "https://files.rcsb.org/download/{pid}.pdb"

def fetch_pdb(pid: str) -> str:

    pid = pid.strip().upper()
    url = PDB_URL.format(pid=pid)
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
        return data.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise IOError(f"HTTP error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise IOError(f"URL error: {e.reason}")


def parse_secondary_structure(lines):
    #Extract all residues from alpha and beta secondary structure as for chain and residue number

    ss_residues = set()
    for line in lines:
        if line.startswith('HELIX'):
            # gap position for each row (0‑based reffering to real PDB files)
            start_chain = line[19] if len(line) > 19 else ''
            start_res_str = line[21:25].strip()
            end_chain = line[31] if len(line) > 31 else ''
            end_res_str = line[33:37].strip()
            if start_chain and start_res_str.isdigit() and end_chain and end_res_str.isdigit():
                start = int(start_res_str)
                end = int(end_res_str)
                for r in range(start, end + 1):
                    ss_residues.add((start_chain, r))
        elif line.startswith('SHEET'):
            start_chain = line[19] if len(line) > 19 else ''
            start_res_str = line[21:25].strip()
            end_chain = line[31] if len(line) > 31 else ''
            end_res_str = line[33:37].strip()
            if start_chain and start_res_str.isdigit() and end_chain and end_res_str.isdigit():
                start = int(start_res_str)
                end = int(end_res_str)
                for r in range(start, end + 1):
                    ss_residues.add((start_chain, r)) #Copy paste simply, its the same extract protocol
    return ss_residues


def distance(p1, p2):
    # Euclidean distance
    return sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)


def analyze_pdb(pdb_text):
    # Scan and record all the datastructure we can find inside a pdb for later calculations on box and distance
    lines = pdb_text.splitlines()
    ss_residues = parse_secondary_structure(lines)

    ca_coords = []          # Cα‑coordinance
    cb_coords = []          # Cβ‑coordinance
    all_coords = []         # all Atom coordinance for box calc later with comparing min max
    residues_seen = set()   # (chain, resnum)
    ss_count = 0
    total_residues = 0

    for line in lines:
        if not line.startswith('ATOM'):
            continue
        # PDB‑rows!
        atom_name = line[12:16].strip()
        chain = line[21].strip()
        res_str = line[22:26].strip()
        if not res_str.isdigit():
            continue
        res_num = int(res_str)
        x = float(line[30:38])
        y = float(line[38:46])
        z = float(line[46:54])

        all_coords.append((x, y, z))
        key = (chain, res_num)

        if atom_name == 'CA':
            ca_coords.append((x, y, z))
        elif atom_name == 'CB':
            cb_coords.append((x, y, z))

        # count only as once
        if key not in residues_seen:
            residues_seen.add(key)
            total_residues += 1
            if key in ss_residues:
                ss_count += 1

    # head and tail for the  Cα / Cβ as in protein
    ca_dist = distance(ca_coords[0], ca_coords[-1]) if len(ca_coords) >= 2 else 0.0
    cb_dist = distance(cb_coords[0], cb_coords[-1]) if len(cb_coords) >= 2 else 0.0

    # parallel box drawing for 3D structure
    if all_coords:
        xs = [p[0] for p in all_coords]
        ys = [p[1] for p in all_coords]
        zs = [p[2] for p in all_coords]
        x_len = max(xs) - min(xs)
        y_len = max(ys) - min(ys)
        z_len = max(zs) - min(zs)
        volume = x_len * y_len * z_len
    else:
        x_len = y_len = z_len = volume = 0.0

    ss_ratio = ss_count / total_residues if total_residues else 0.0

    return {
        'ca_dist': ca_dist,
        'cb_dist': cb_dist,
        'x_len': x_len,
        'y_len': y_len,
        'z_len': z_len,
        'volume': volume,
        'ss_ratio': ss_ratio
    }


def generate_image(pdb_id, output_dir):

    #headless client for jmolData.jar

    jmol_data_jar = "/mnt/extsoft/software/jmol/JmolData.jar"
    out_file = os.path.join(output_dir, f"{pdb_id}.png")

    # Script command in  ram
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jmol', delete=False) as f:
        script = f"load ={pdb_id}\ncartoon\nwrite image {out_file}\nquit\n"
        f.write(script)
        script_path = f.name

    cmd = ['java', '-jar', jmol_data_jar, '--script', script_path]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.unlink(script_path)          # jar headless cleanup
        return True
    except subprocess.CalledProcessError as e:
        print(f"Jmol‑Error in {pdb_id}: {e.stderr.decode() if e.stderr else ''}",
              file=sys.stderr)
        os.unlink(script_path)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Calculate structure parameters and call out a cartoon image on PDB‑IDs.'
    )
    parser.add_argument('--id', nargs='+', required=True,
                        help='One or more PDB‑IDs (eg. 1MBN 1TIM)')
    parser.add_argument('--output', help='Dictionary for the PNG‑Bilder (optional)')
    args = parser.parse_args()

    if args.output and not os.path.exists(args.output):
        os.makedirs(args.output)

    for pid in args.id:

        try:
            pdb_text = fetch_pdb(pid)
        except Exception as e:
            print(f"  Error with downloads: {e}", file=sys.stderr)
            continue

        data = analyze_pdb(pdb_text)

        # Out put with 4 commapos
        print(f"{pid}\tAnteil AS in Sekundaerstruktur\t{data['ss_ratio']:.4f}")
        print(f"{pid}\tAbstand C_alpha\t{data['ca_dist']:.4f}")
        print(f"{pid}\tAbstand C_beta\t{data['cb_dist']:.4f}")
        print(f"{pid}\tX-Groesse\t{data['x_len']:.4f}")
        print(f"{pid}\tY-Groesse\t{data['y_len']:.4f}")
        print(f"{pid}\tZ-Groesse\t{data['z_len']:.4f}")
        print(f"{pid}\tVolumen\t{data['volume']:.4f}")

        if args.output:
               generate_image(pid, args.output)


if __name__ == '__main__':
    main()
