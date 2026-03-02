#!/usr/bin/env python3
import argparse
import sys


def read_fasta_records(handle):
    # FASTA-Reader
    seq_id = None
    seq_parts = []

    for line in handle:
        line = line.strip()
        if not line:
            continue

        if line.startswith(">"):
            if seq_id is not None:
                yield seq_id, "".join(seq_parts).upper()
            # ID = erstes Wort nach >
            seq_id = line[1:].split()[0]
            seq_parts = []
        else:
            seq_parts.append(line)

    if seq_id is not None:
        yield seq_id, "".join(seq_parts).upper()


def orf_nt_to_aa_len(nt_seq):
    # Protein-Länge ist (Basen/3) - 1 (weil Stop keine Aminosäure ist)
    if len(nt_seq) < 6:
        return None  # zu kurz für ATG + Stop
    if len(nt_seq) % 3 != 0:
        return None  # sollte bei ORFs eigentlich nicht passieren

    aa_len = (len(nt_seq) // 3) - 1
    if aa_len < 0:
        return None
    return aa_len


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fasta", required=True, help="ORF-FASTA Datei oder '-' für stdin")
    parser.add_argument("--histogram", help="optional: PNG Datei für Histogramm, z.B. hist.png")
    parser.add_argument("--lower", type=int, required=True, help="untere Grenze (AA)")
    parser.add_argument("--upper", type=int, required=True, help="obere Grenze (AA)")
    parser.add_argument("--bin_size", type=int, required=True, help="Bin-Größe (AA), z.B. 5")
    args = parser.parse_args()

    # FASTA öffnen (Datei oder stdin)
    if args.fasta == "-":
        fh = sys.stdin
    else:
        fh = open(args.fasta, "r", encoding="utf-8", errors="ignore")

    lower = args.lower
    upper = args.upper
    bin_size = args.bin_size

    if bin_size <= 0:
        print("bin_size muss > 0 sein", file=sys.stderr)
        sys.exit(1)
    if lower > upper:
        print("lower darf nicht größer als upper sein", file=sys.stderr)
        sys.exit(1)

    # AA-Längen sammeln (nur die, die in den Bereich fallen)
    aa_lengths_in_range = []

    for seq_id, nt_seq in read_fasta_records(fh):
        aa_len = orf_nt_to_aa_len(nt_seq)
        if aa_len is None:
            continue

        if lower <= aa_len <= upper:
            aa_lengths_in_range.append(aa_len)

    if args.fasta != "-":
        fh.close()

    # Ausgabe: nur die Anzahl
    print(len(aa_lengths_in_range))

    # Histogramm (optional)
    if args.histogram:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise SystemExit("matplotlib fehlt. Histogramm geht nur, wenn matplotlib installiert ist.")

        # Bins bauen
        # matplotlib braucht Kanten
        edges = list(range(lower, upper + bin_size + 1, bin_size))

        plt.figure()
        plt.hist(aa_lengths_in_range, bins=edges)  # keine Farbe festlegen
        plt.xlabel("Protein-Länge (AA)")
        plt.ylabel("Anzahl ORFs")
        plt.title(f"ORFs mit Länge {lower}-{upper} AA (bin={bin_size})")
        plt.tight_layout()
        plt.savefig(args.histogram, dpi=150)


if __name__ == "__main__":
    main()
