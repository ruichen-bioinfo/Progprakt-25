#!/usr/bin/env python3
import argparse
import math
import sys
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


PDB_URL = "https://files.rcsb.org/download/{pid}.pdb"

AA3_TO_1 = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--id", required=True)
    p.add_argument("--distance", required=True, type=float)
    p.add_argument("--type", required=True, dest="atom_type")
    p.add_argument("--length", required=True, type=int)
    p.add_argument("--contactmatrix")
    return p.parse_args()


def fetch_pdb(pid: str) -> str:
    pid = pid.strip().upper()
    url = PDB_URL.format(pid=pid)
    with urllib.request.urlopen(url) as resp:
        data = resp.read()
    return data.decode("utf-8", errors="replace")


@dataclass(frozen=True)
class Residue:
    chain: str
    position: int   # resSeq
    serial: int     # atom serial of chosen atom
    aa3: str        # 3-letter residue name
    x: float
    y: float
    z: float


def _first_model_filter(line: str, in_model: Optional[int]) -> Tuple[bool, Optional[int]]:
    """
    If MODEL blocks exist, only process MODEL 1.
    If no MODEL blocks, process all ATOM/HETATM lines.
    """
    if line.startswith("MODEL"):
        parts = line.split()
        if len(parts) >= 2 and parts[1].isdigit():
            return False, int(parts[1])
        return False, in_model
    if line.startswith("ENDMDL"):
        return False, None
    if in_model is None:
        return True, None
    return (in_model == 1), in_model


def get_residues_with_atom(pdb_text: str, atom_type: str) -> List[Residue]:
    atom_type = atom_type.strip().upper()
    residues: Dict[Tuple[str, int], Residue] = {}
    in_model: Optional[int] = None

    for line in pdb_text.splitlines():
        ok, in_model = _first_model_filter(line, in_model)
        if not ok:
            continue

        if not (line.startswith("ATOM") or line.startswith("HETATM")):
            continue

        # altLoc: keep blank or 'A'
        altloc = line[16:17]
        if altloc not in (" ", "A"):
            continue

        name = line[12:16].strip().upper()
        if name != atom_type:
            continue

        aa3 = line[17:20].strip().upper()
        chain = line[21:22].strip() or "_"

        try:
            pos = int(line[22:26].strip())
            serial = int(line[6:11].strip())
            x = float(line[30:38].strip())
            y = float(line[38:46].strip())
            z = float(line[46:54].strip())
        except ValueError:
            continue

        key = (chain, pos)
        # keep first occurrence per residue
        if key not in residues:
            residues[key] = Residue(chain=chain, position=pos, serial=serial, aa3=aa3, x=x, y=y, z=z)

    return sorted(residues.values(), key=lambda r: (r.chain, r.position))


def secondary_structure_map(pdb_text: str) -> Dict[Tuple[str, int], str]:
    """
    Return (chain, resSeq) -> 'H' or 'E'.
    Not present => treat as 'C'.
    Helix wins over sheet.
    """
    ss: Dict[Tuple[str, int], str] = {}

    for line in pdb_text.splitlines():
        if line.startswith("HELIX"):
            init_chain = (line[19:20].strip() or "_")
            end_chain = (line[31:32].strip() or "_")
            try:
                init_pos = int(line[21:25].strip())
                end_pos = int(line[33:37].strip())
            except ValueError:
                continue
            if init_chain != end_chain:
                continue
            for p in range(min(init_pos, end_pos), max(init_pos, end_pos) + 1):
                ss[(init_chain, p)] = "H"

        elif line.startswith("SHEET"):
            init_chain = (line[21:22].strip() or "_")
            end_chain = (line[32:33].strip() or "_")
            try:
                init_pos = int(line[22:26].strip())
                end_pos = int(line[33:37].strip())
            except ValueError:
                continue
            if init_chain != end_chain:
                continue
            for p in range(min(init_pos, end_pos), max(init_pos, end_pos) + 1):
                ss.setdefault((init_chain, p), "E")

    return ss


def calc_distance(a: Residue, b: Residue) -> float:
    dx = a.x - b.x
    dy = a.y - b.y
    dz = a.z - b.z
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def compute_contacts(
    residues: List[Residue],
    ss_map: Dict[Tuple[str, int], str],
    dist_thresh: float,
    length_threshold: int,
) -> Tuple[List[Tuple[Residue, str, int, int]], List[List[int]]]:
    """
    Returns:
      rows: (Residue, ss, global_count, local_count)
      matrix: NxN 0/1 contact matrix (same order as residues list)
    """
    n = len(residues)
    matrix = [[0] * n for _ in range(n)]
    local = [0] * n
    glob = [0] * n

    # Build per-chain sequence indices (for local contacts)
    chain_to_indices: Dict[str, List[int]] = {}
    for idx, r in enumerate(residues):
        chain_to_indices.setdefault(r.chain, []).append(idx)

    # Map residue global index -> its index within the chain list (0..)
    chain_pos_index: Dict[int, int] = {}
    for ch, idx_list in chain_to_indices.items():
        for k, idx in enumerate(idx_list):
            chain_pos_index[idx] = k

    for i in range(n):
        for j in range(i + 1, n):
            if calc_distance(residues[i], residues[j]) < dist_thresh:
                matrix[i][j] = 1
                matrix[j][i] = 1

                if residues[i].chain == residues[j].chain:
                    # local/global decided by distance in that chain sequence
                    if abs(residues[i].position - residues[j].position) < length_threshold:
                        local[i] += 1
                        local[j] += 1
                    else:
                        glob[i] += 1
                        glob[j] += 1
                else:
                    # different chains -> always global
                    glob[i] += 1
                    glob[j] += 1

    rows: List[Tuple[Residue, str, int, int]] = []
    for i, r in enumerate(residues):
        ss = ss_map.get((r.chain, r.position), "C")
        rows.append((r, ss, glob[i], local[i]))

    return rows, matrix


def write_matrix(path: str, matrix: List[List[int]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in matrix:
            f.write(" ".join(str(x) for x in row) + "\n")


def main() -> None:
    args = parse_args()

    pdb_text = fetch_pdb(args.id)
    residues = get_residues_with_atom(pdb_text, args.atom_type)
    ss_map = secondary_structure_map(pdb_text)

    rows, matrix = compute_contacts(
        residues=residues,
        ss_map=ss_map,
        dist_thresh=args.distance,
        length_threshold=args.length,
    )
    sys.stdout.write("chain\tpos\tserial\taa\tss\tglobal\tlocal\n")
    for r, ss, g, l in rows:
        aa1 = AA3_TO_1.get(r.aa3, "X")
        print(f"{r.chain}\t{r.position}\t{r.serial}\t{aa1}\t{ss}\t{g}\t{l}")

    if args.contactmatrix:
        write_matrix(args.contactmatrix, matrix)


if __name__ == "__main__":
    main()
