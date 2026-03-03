#!/usr/bin/env python3
import sys
import os
import argparse



# Seclib Reader for DSSP files
# Converts DSSP secondary structure codes to 3-state (H, E, C)


def dssp_to_3state(dssp_code):

    if dssp_code in ['H', 'G', 'I']:
        return 'H'
    elif dssp_code in ['E', 'B']:
        return 'E'
    else:
        return 'C'


def parse_dssp(filepath):

    seq = []
    sec = []
    start_reading = False

    try:
        with open(filepath, 'r') as f:
            for line in f:
                # The data starts after the line containing "  #  RESIDUE"
                if line.strip().startswith("#  RESIDUE"):
                    start_reading = True
                    continue

                if start_reading and len(line) > 16:
                    # DSSP format is fixed width
                    # AA is at index 13, SS is at index 16
                    aa = line[13]
                    ss = line[16]

                    # Skip lower case AA (often cysteines bridges marked differently or errors)
                    # and check for valid amino acids
                    if aa.islower() or aa == '!':
                        continue

                    seq.append(aa)
                    sec.append(dssp_to_3state(ss))

        return "".join(seq), "".join(sec)
    except Exception as e:
        sys.stderr.write(f"Error parsing {filepath}: {e}\n")
        return None, None


def main():
    parser = argparse.ArgumentParser(description="Create Seclib file from DSSP files")
    parser.add_argument("--input", nargs='+', required=True, help="List of DSSP files")
    parser.add_argument("--output", required=True, help="Output .seclib file (or .db)")
    args = parser.parse_args()

    count = 0
    with open(args.output, 'w') as out:
        for file_path in args.input:
            filename = os.path.basename(file_path)
            pdb_id = filename.split('.')[0]  # Assuming filename is like 1mbn.dssp

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
