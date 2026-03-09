#!/usr/bin/env python3
import sys
import os
import argparse
import urllib.request
import urllib.error

# ─────────────────────────────────────────────
# Amino acid 3-letter → 1-letter mapping
# ─────────────────────────────────────────────
PDB_2_FASTA = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D",
    "CYS": "C", "GLN": "Q", "GLU": "E", "GLY": "G",
    "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S",
    "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
    "SEC": "U", "PYL": "O", "ASX": "B", "GLX": "Z", "UNK": "X",
}

PDB_URL = "https://files.rcsb.org/download/{pid}.pdb"


# ─────────────────────────────────────────────
# DSSP mode helpers
# ─────────────────────────────────────────────
def dssp_to_3state(dssp_code):
    if dssp_code in ['H', 'G', 'I']:
        return 'H'
    elif dssp_code in ['E', 'B']:
        return 'E'
    else:
        return 'C'


def parse_dssp(filepath):
    """Parse a .dssp file → (sequence, ss_3state)"""
    seq = []
    sec = []
    start_reading = False
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip().startswith("#  RESIDUE"):
                    start_reading = True
                    continue
                if start_reading and len(line) > 16:
                    aa = line[13]
                    ss = line[16]
                    if aa.islower() or aa == '!':
                        continue
                    seq.append(aa)
                    sec.append(dssp_to_3state(ss))
        return "".join(seq), "".join(sec)
    except Exception as e:
        sys.stderr.write(f"Error parsing {filepath}: {e}\n")
        return None, None


# ─────────────────────────────────────────────
# PDB mode helpers
# ─────────────────────────────────────────────
def fetch_pdb(pid: str) -> str:
    """Download PDB file from RCSB."""
    url = PDB_URL.format(pid=pid.strip().upper())
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise IOError(str(e))
    except urllib.error.URLError as e:
        raise IOError(str(e.reason))


def parse_pdb_text(pdb_text: str, pid: str, min_len: int = 50):
    """
    Parse PDB text → list of (chain_id, sequence, ss_3state).
    Uses SEQRES for sequence, HELIX/SHEET records for secondary structure.
    """
    chains_seq = {}
    for line in pdb_text.splitlines():
        if line.startswith("SEQRES"):
            parts = line.split()
            if len(parts) < 5:
                continue
            chain_id = parts[2]
            if chain_id not in chains_seq:
                chains_seq[chain_id] = []
            for res in parts[4:]:
                chains_seq[chain_id].append(PDB_2_FASTA.get(res.upper(), 'X'))

    helix_ranges, sheet_ranges = [], []
    for line in pdb_text.splitlines():
        if line.startswith("HELIX") and len(line) >= 37:
            try:
                helix_ranges.append((line[19], int(line[21:25]), int(line[33:37])))
            except ValueError:
                pass
        elif line.startswith("SHEET") and len(line) >= 37:
            try:
                sheet_ranges.append((line[21], int(line[22:26]), int(line[33:37])))
            except ValueError:
                pass

    chains_resids = {}
    seen = set()
    for line in pdb_text.splitlines():
        if line.startswith("ATOM") and len(line) >= 26 and line[12:16].strip() == 'CA':
            chain_id = line[21]
            try:
                res_seq = int(line[22:26])
            except ValueError:
                continue
            key = (chain_id, res_seq)
            if key in seen:
                continue
            seen.add(key)
            chains_resids.setdefault(chain_id, []).append(res_seq)

    results = []
    for chain_id in sorted(chains_seq.keys()):
        seq = chains_seq[chain_id]
        if len(seq) < min_len:
            continue
        res_ids = chains_resids.get(chain_id, [])
        ss = []
        for i, _ in enumerate(seq):
            res_id = res_ids[i] if i < len(res_ids) else i + 1
            s = 'C'
            for (c, start, end) in helix_ranges:
                if c == chain_id and start <= res_id <= end:
                    s = 'H'
                    break
            if s == 'C':
                for (c, start, end) in sheet_ranges:
                    if c == chain_id and start <= res_id <= end:
                        s = 'E'
                        break
            ss.append(s)
        results.append((chain_id, ''.join(seq), ''.join(ss)))
    return results


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Create seclib files from DSSP files OR PDB IDs/files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # DSSP mode (original):
  python3 create_seclib.py --input *.dssp --output db.seclib

  # PDB mode - download by ID list:
  python3 create_seclib.py --ids pdb_ids.txt --output testset_aln/

  # PDB mode - local .pdb files:
  python3 create_seclib.py --input *.pdb --output testset_aln/
        """
    )
    parser.add_argument("--input", nargs='+',
                        help="DSSP files (.dssp) OR local PDB files (.pdb)")
    parser.add_argument("--output", required=True,
                        help="Output file (DSSP mode) or output directory (PDB mode)")
    parser.add_argument("--ids",
                        help="Text file with one PDB ID per line (PDB download mode)")
    parser.add_argument("--min_len", type=int, default=50,
                        help="Minimum sequence length for PDB mode (default: 50)")
    return parser.parse_args()


def main():
    args = parse_args()

    pdb_mode = args.ids or (
        args.input and any(f.endswith('.pdb') for f in args.input))

    if pdb_mode:
        # ── PDB mode ──────────────────────────────────────────────────────
        os.makedirs(args.output, exist_ok=True)
        pdb_entries = []

        if args.ids:
            with open(args.ids) as f:
                ids = [l.strip() for l in f if l.strip()]
            for pid in ids:
                try:
                    print(f"Downloading {pid}...")
                    pdb_entries.append((pid.lower(), fetch_pdb(pid)))
                except Exception as e:
                    sys.stderr.write(f"Skipping {pid}: {e}\n")

        if args.input:
            for filepath in args.input:
                if not filepath.endswith('.pdb'):
                    continue
                pid = os.path.basename(filepath).split('.')[0]
                try:
                    with open(filepath) as f:
                        pdb_entries.append((pid, f.read()))
                except Exception as e:
                    sys.stderr.write(f"Skipping {filepath}: {e}\n")

        count = 0
        for pid, pdb_text in pdb_entries:
            for chain_id, sequence, structure in parse_pdb_text(
                    pdb_text, pid, args.min_len):
                out_name = f"{pid}_{chain_id}.aln"
                with open(os.path.join(args.output, out_name), 'w') as out:
                    out.write(f"> {pid}_{chain_id}\n")
                    out.write(f"AS {sequence}\n")
                    out.write(f"SS {structure}\n")
                count += 1
                print(f"  -> {out_name} (len={len(sequence)})")
        print(f"\nDone! Generated {count} .aln files in {args.output}/")

    else:
        # ── DSSP mode (original) ──────────────────────────────────────────
        if not args.input:
            sys.stderr.write(
                "Error: provide --input (dssp/pdb files) or --ids (PDB IDs)\n")
            sys.exit(1)

        count = 0
        with open(args.output, 'w') as out:
            for file_path in args.input:
                filename = os.path.basename(file_path)
                pdb_id = filename.split('.')[0]
                sequence, structure = parse_dssp(file_path)
                if sequence and structure and len(sequence) == len(structure):
                    out.write(f"> {pdb_id}\n")
                    out.write(f"AS {sequence}\n")
                    out.write(f"SS {structure}\n")
                    count += 1
                else:
                    sys.stderr.write(f"Skipping {filename}: Empty or mismatch.\n")
        print(f"Successfully converted {count} files to {args.output}")


if __name__ == "__main__":
    main()