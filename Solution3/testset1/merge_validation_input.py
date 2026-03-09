#!/usr/bin/env python3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PairAlignment:
    header: str
    id1: str
    id2: str
    seq1: str
    seq2: str


def read_next_non_empty_line(lines, start_index):
    i = start_index

    while i < len(lines):
        line = lines[i].strip()
        if line:
            return line, i + 1
        i += 1

    return None, i


def parse_alignment_line(line: str):
    colon = line.find(":")
    if colon < 0:
        raise ValueError(f"Invalid alignment line, missing ':': {line}")

    seq_id = line[:colon].strip()
    sequence = line[colon + 1:].strip()

    if not seq_id or not sequence:
        raise ValueError(f"Invalid alignment line: {line}")

    return seq_id, sequence


def read_alignment_blocks(file_path: Path):
    blocks = []
    lines = file_path.read_text(encoding="utf-8").splitlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line:
            continue

        if not line.startswith(">"):
            raise ValueError(f"Expected header line starting with '>': {line}")

        header = line

        line1, i = read_next_non_empty_line(lines, i)
        line2, i = read_next_non_empty_line(lines, i)

        if line1 is None or line2 is None:
            raise ValueError(f"Incomplete alignment block after header: {header}")

        id1, seq1 = parse_alignment_line(line1)
        id2, seq2 = parse_alignment_line(line2)

        blocks.append(PairAlignment(header, id1, id2, seq1, seq2))

    return blocks


def build_key(id1: str, id2: str):
    return id1, id2


def write_validation_input(candidate_blocks, reference_blocks, output_file: Path):
    reference_map = {}

    for ref in reference_blocks:
        key = build_key(ref.id1, ref.id2)
        reference_map[key] = ref

    written = 0

    with output_file.open("w", encoding="utf-8") as f:
        for candidate in candidate_blocks:
            key = build_key(candidate.id1, candidate.id2)

            if key not in reference_map:
                print(f"Warning: no reference found for {candidate.id1} {candidate.id2}")
                continue

            reference = reference_map[key]

            f.write(candidate.header + "\n")
            f.write(f"{candidate.id1}: {candidate.seq1}\n")
            f.write(f"{candidate.id2}: {candidate.seq2}\n")
            f.write(f"{reference.id1}: {reference.seq1}\n")
            f.write(f"{reference.id2}: {reference.seq2}\n")
            f.write("\n")

            written += 1

    print(f"Done. Wrote {written} validation blocks to {output_file}")


def main():
    candidate_file = Path("output/candidate.ali")
    reference_file = Path("output/homstrad.references")
    output_file = Path("output/validation_input.txt")

    candidate_blocks = read_alignment_blocks(candidate_file)
    reference_blocks = read_alignment_blocks(reference_file)

    write_validation_input(candidate_blocks, reference_blocks, output_file)


if __name__ == "__main__":
    main()
