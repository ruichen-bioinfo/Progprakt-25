#!/usr/bin/env python3
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path


@dataclass
class HomstradEntry:
    family: str
    entry_id: str
    full_id: str
    description: str
    aligned_sequence: str


@dataclass
class ReferencePair:
    family: str
    id1: str
    id2: str
    ref_seq1: str
    ref_seq2: str
    raw_seq1: str
    raw_seq2: str


def parse_homstrad_ali(file_path: Path, family: str):
    entries = []

    current_id = None
    current_description = ""
    seq_parts = []

    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            # kommentarzeilen ignorieren
            if line.startswith("C;"):
                continue

            # neuer eintrag startet
            if line.startswith(">P1;"):
                if current_id is not None:
                    aligned = "".join(seq_parts).replace("*", "")
                    entries.append(
                        HomstradEntry(
                            family=family,
                            entry_id=current_id,
                            full_id=f"{family}_{current_id}",
                            description=current_description,
                            aligned_sequence=aligned
                        )
                    )

                current_id = line[4:].strip()
                current_description = ""
                seq_parts = []
                continue

            # erste zeile nach dem header ist die beschreibung
            if current_id is not None and current_description == "":
                current_description = line
                continue

            if current_id is not None:
                seq_parts.append(line.replace(" ", ""))

    # letzten eintrag noch speichern
    if current_id is not None:
        aligned = "".join(seq_parts).replace("*", "")
        entries.append(
            HomstradEntry(
                family=family,
                entry_id=current_id,
                full_id=f"{family}_{current_id}",
                description=current_description,
                aligned_sequence=aligned
            )
        )

    return entries


def remove_double_gap_columns(seq1: str, seq2: str):
    cleaned1 = []
    cleaned2 = []

    for c1, c2 in zip(seq1, seq2):
        if c1 == "-" and c2 == "-":
            continue

        cleaned1.append(c1)
        cleaned2.append(c2)

    return "".join(cleaned1), "".join(cleaned2)


def build_reference_pairs(entries):
    pairs = []

    for entry1, entry2 in combinations(entries, 2):
        ref_seq1, ref_seq2 = remove_double_gap_columns(
            entry1.aligned_sequence,
            entry2.aligned_sequence
        )

        raw_seq1 = ref_seq1.replace("-", "")
        raw_seq2 = ref_seq2.replace("-", "")

        pair = ReferencePair(
            family=entry1.family,
            id1=entry1.full_id,
            id2=entry2.full_id,
            ref_seq1=ref_seq1,
            ref_seq2=ref_seq2,
            raw_seq1=raw_seq1,
            raw_seq2=raw_seq2
        )

        pairs.append(pair)

    return pairs


def choose_one_pair_per_family(entries):
    family_pairs = build_reference_pairs(entries)

    if not family_pairs:
        return None

    # erstmal einfach das erste Paar der Familie nehmen
    return family_pairs[0]


def collect_limited_reference_pairs(homstrad_root: Path, max_pairs: int):
    all_pairs = []

    for family_dir in sorted(homstrad_root.iterdir()):
        if not family_dir.is_dir():
            continue

        family = family_dir.name
        ali_file = family_dir / f"{family}.ali"

        if not ali_file.exists():
            continue

        entries = parse_homstrad_ali(ali_file, family)

        if len(entries) < 2:
            continue

        pair = choose_one_pair_per_family(entries)
        if pair is None:
            continue

        all_pairs.append(pair)

        if len(all_pairs) >= max_pairs:
            break

    return all_pairs


def write_seqlib(pairs, output_file: Path):
    sequences = {}

    for pair in pairs:
        sequences[pair.id1] = pair.raw_seq1
        sequences[pair.id2] = pair.raw_seq2

    with output_file.open("w", encoding="utf-8") as f:
        for seq_id in sorted(sequences):
            f.write(f"{seq_id}:{sequences[seq_id]}\n")


def write_pairs(pairs, output_file: Path):
    with output_file.open("w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(f"{pair.id1} {pair.id2} family={pair.family}\n")


def write_references(pairs, output_file: Path):
    with output_file.open("w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(f">{pair.id1} {pair.id2} family={pair.family}\n")
            f.write(f"{pair.id1}: {pair.ref_seq1}\n")
            f.write(f"{pair.id2}: {pair.ref_seq2}\n")
            f.write("\n")


def main():
    homstrad_root = Path("/mnt/extstud/praktikum/bioprakt-ws25/Data/HOMSTRAD_DB/2019_Feb")
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    max_pairs = 10
    selected_pairs = collect_limited_reference_pairs(homstrad_root, max_pairs)

    write_seqlib(selected_pairs, output_dir / "homstrad.seqlib")
    write_pairs(selected_pairs, output_dir / "homstrad.pairs")
    write_references(selected_pairs, output_dir / "homstrad.references")

    print(f"Done. Created {len(selected_pairs)} reference pairs.")
    print(f"Files written to: {output_dir}")


if __name__ == "__main__":
    main()
