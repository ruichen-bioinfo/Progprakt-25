#!/user/bin/env python3
import argparse
import sys
def convert(handle):
    for line in handle:
        if line.startswith(">"):
            sys.stdout.write(line)
        else:
            seq=line.rstrip("\n")
            seq=seq.replace("T","U").replace("t","u")
            sys.stdout.write(seq+"\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fasta",
        required=True,
        type=argparse.FileType("r")
    )
    args = parser.parse_args()
    convert(args.fasta)
if __name__ == "__main__":
    main()
