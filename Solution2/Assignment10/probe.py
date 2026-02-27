#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess
from math import sqrt
from get_pdb import fetch_pdb  # get_pdb

# ---------- secondary structure (HELIX/SHEET) ----------
def parse_secondary_structure(lines):
    
    ss_residues = set()
    for line in lines:
        if line.startswith('HELIX'):
            # ana (0‑based)
            # head chain: col 19, head residue: col 21-25, tail: col 31, tail residue: col 33-37
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
            # singularity check!
            start_chain = line[19] if len(line) > 19 else ''
            start_res_str = line[21:25].strip()
            end_chain = line[31] if len(line) > 31 else ''
            end_res_str = line[33:37].strip()
            if start_chain and start_res_str.isdigit() and end_chain and end_res_str.isdigit():
                start = int(start_res_str)
                end = int(end_res_str)
                for r in range(start, end + 1):
                    ss_residues.add((start_chain, r))
    return ss_residues

def distance(p1, p2):
    return sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)

def analyze_pdb(pdb_text):
   
    lines = pdb_text.splitlines()
    ss_residues = parse_secondary_structure(lines)

    ca_coords = []          #  Cα 
    cb_coords = []          #  Cβ 
    all_coords = []         #  Atom for box
    residues_seen = set()   # calc'ed resi (chain, resnum)
    ss_count = 0
    total_residues = 0

    for line in lines:
        if not line.startswith('ATOM'):
            continue
        # read resi,atom and location
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

        # Collect Cα  Cβ
        if atom_name == 'CA':
            ca_coords.append((x, y, z))
        elif atom_name == 'CB':
            cb_coords.append((x, y, z))

        # Secondary structure ratio
        if key not in residues_seen:
            residues_seen.add(key)
            total_residues += 1
            if key in ss_residues:
                ss_count += 1

    # Euclidean distance
    ca_dist = distance(ca_coords[0], ca_coords[-1]) if len(ca_coords) >= 2 else 0.0
    cb_dist = distance(cb_coords[0], cb_coords[-1]) if len(cb_coords) >= 2 else 0.0

    #Box
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

    jmol_path = "/mnt/extsoft/software/jmol/jmol.sh"   # pathway
    out_file = os.path.join(output_dir, f"{pdb_id}.png")
    # USAGE: jmol.sh -i "load ={pdb_id}; cartoon; write image {out_file}; quit"
    cmd = [jmol_path, "-i", f'load ={pdb_id}; cartoon; write image "{out_file}"; quit']
    try:
        subprocess.run(cmd, check = True,stdout = subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Jmol wrong!: {e.stderr.decode() if e.stderr else ''}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', nargs='+', required=True, help='PDB IDs')
    parser.add_argument('--output', help='Verzeichnis für Bilder (optional)')
    args = parser.parse_args()

    if args.output and not os.path.exists(args.output):
        os.makedirs(args.output)

    for pid in args.id:
        print(pid)
        try:
            pdb_text = fetch_pdb(pid)
        except Exception as e:
            print(f"  Fehler beim Herunterladen: {e}", file=sys.stderr)
            continue

        data = analyze_pdb(pdb_text)

        print(f"  Anteil AS in Sekundaerstruktur {data['ss_ratio']:.4f}")
        print(f"  Abstand C_alpha {data['ca_dist']:.4f}")
        print(f"  Abstand C_beta {data['cb_dist']:.4f}")
        print(f"  X-Groesse {data['x_len']:.4f}")
        print(f"  Y-Groesse {data['y_len']:.4f}")
        print(f"  Z-Groesse {data['z_len']:.4f}")
        print(f"  Volumen {data['volume']:.4f}")

        if args.output:
            if generate_image(pid, args.output):
                print(f"  Bild gespeichert: {args.output}/{pid}.png")
            else:
                print("  Fehler bei Bildgenerierung.")

if __name__ == '__main__':
    main()
