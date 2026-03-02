#!/usr/bin/env python3
import argparse
import sys


def parse_md(md):
    # Liefert 1-basierte Positionen der Mismatches im Read
    positions = set()
    pos = 0
    i = 0

    while i < len(md):
        if md[i].isdigit():
            j = i
            while j < len(md) and md[j].isdigit():
                j += 1
            pos += int(md[i:j])
            i = j
        elif md[i] == "^":
            i += 1
            while i < len(md) and md[i].isalpha():
                i += 1
        else:
            pos += 1
            positions.add(pos)
            i += 1

    return positions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sam", required=True)
    parser.add_argument("--no-off-targets")
    parser.add_argument("--with-mismatch")
    args = parser.parse_args()

    if args.sam == "-":
        fh = sys.stdin
    else:
        fh = open(args.sam, "r")

    no_off = []
    with_mm = []

    for line in fh:
        if line.startswith("@"):
            continue

        cols = line.strip().split("\t")
        if len(cols) < 11:
            continue

        qname = cols[0]
        rname = cols[2]
        seq = cols[9]

        # unmapped -> kein Off-Target
        if rname == "*":
            no_off.append((qname, seq))
            continue

        # mapped -> prüfen auf Mismatch im GG-Suffix
        md = None
        for field in cols[11:]:
            if field.startswith("MD:Z:"):
                md = field[5:]
                break

        if md:
            mism = parse_md(md)
            L = len(seq)
            if L in mism or (L - 1) in mism:
                with_mm.append((qname, seq))

    if args.sam != "-":
        fh.close()

    # Ausgabe
    if args.no_off_targets:
        out = open(args.no_off_targets, "w")
        for h, s in no_off:
            out.write(f">{h}\n{s}\n")
        out.close()

    if args.with_mismatch:
        out = open(args.with_mismatch, "w")
        for h, s in with_mm:
            out.write(f">{h}\n{s}\n")
        out.close()


if __name__ == "__main__":
    main()
