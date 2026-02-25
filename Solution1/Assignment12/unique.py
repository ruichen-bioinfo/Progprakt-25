#!/usr/bin/env python3
import argparse


def read_fasta_records(handle):
    # FASTA reader
    seq_id = None
    seq_parts = []
    for line in handle:
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if seq_id is not None:
                yield seq_id, "".join(seq_parts).upper()
            # ID ist erstes "Wort" nach >
            seq_id = line[1:].split()[0]
            seq_parts = []
        else:
            seq_parts.append(line)
    if seq_id is not None:
        yield seq_id, "".join(seq_parts).upper()


def kmers_in_gene(seq, k):
    # alle k-mers einer Sequenz (überlappend)
    for i in range(0, len(seq) - k + 1):
        yield seq[i:i + k]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fasta", required=True, help="FASTA Datei oder '-' für stdin")
    parser.add_argument("--k", nargs="+", type=int, required=True, help="ein oder mehrere k-Werte")
    parser.add_argument("--start", type=int, help="Startposition im Gen (0-basiert)")
    parser.add_argument("--plot", help="Plot als PNG speichern")
    args = parser.parse_args()

    # FASTA öffnen (Datei oder stdin)
    if args.fasta == "-":
        import sys
        fh = sys.stdin
    else:
        fh = open(args.fasta, "r", encoding="utf-8", errors="ignore")

    # alle Gene/Sequenzen einlesen, weil für mehrere k drauf zugreifen
    genes = []
    for gid, seq in read_fasta_records(fh):
        genes.append((gid, seq))

    if args.fasta != "-":
        fh.close()

    total_genes = len(genes)
    if total_genes == 0:
        return

    # x und Prozentwerte sammeln
    plot_x = []
    plot_percent = []

    # pro k zählen wie viele Gene mindestens einen k-mer haben der in keinem anderen Gen vorkommt
    for k in args.k:
        # in wie vielen verschiedenen Genen kommt k-mer vor?
        kmer_gene_count = {}

        # pro Gen k-mers merken
        gene_kmers = []

        for gid, seq in genes:
            seen_in_this_gene = set()

            if args.start is None:
                # Teilaufgabe a): alle k-mers im Gen
                for kmer in kmers_in_gene(seq, k):
                    # mit N/komischen Zeichen skippen
                    if "N" in kmer:
                        continue
                    seen_in_this_gene.add(kmer)
            else:
                # Teilaufgabe b): nur genau ein Stück ab Startposition
                s = args.start
                if s >= 0 and s + k <= len(seq):
                    kmer = seq[s:s + k]
                    if "N" not in kmer:
                        seen_in_this_gene.add(kmer)

            gene_kmers.append(seen_in_this_gene)

            # global zählen
            for kmer in seen_in_this_gene:
                kmer_gene_count[kmer] = kmer_gene_count.get(kmer, 0) + 1

        #  pro Gen checken ob es mindestens einen k-mer hat der nur in dem Gen vorkommt
        unique_genes = 0
        for kmerset in gene_kmers:
            has_unique = False
            for kmer in kmerset:
                if kmer_gene_count.get(kmer, 0) == 1:
                    has_unique = True
                    break
            if has_unique:
                unique_genes += 1

        print(f"{k}\t{unique_genes}")

        # Prozent merken (für Kurve)
        percent = (unique_genes / total_genes) * 100.0

        # x-Achse: a) -> k, b) -> start+k (Anzahl Basen vom Anfang)
        if args.start is None:
            plot_x.append(k)
        else:
            plot_x.append(args.start + k)

        plot_percent.append(percent)

    # Plotten (nur wenn --plot angegeben wurde)
    if args.plot:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise SystemExit("matplotlib fehlt. Plot geht nur, wenn matplotlib installiert ist.")

        # nach x sortieren
        pairs = sorted(zip(plot_x, plot_percent), key=lambda x: x[0])
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]

        plt.figure()
        plt.plot(xs, ys, marker="o")  # keine Farbe festlegen

        if args.start is None:
            plt.xlabel("k")
            plt.title("Eindeutigkeit vs. k")
        else:
            plt.xlabel("Anzahl Basen vom Anfang (start + k)")
            plt.title("Eindeutigkeit vs. sequenzierte Basen")

        plt.ylabel("Prozentsatz eindeutig identifizierbarer Gene")
        plt.tight_layout()
        plt.savefig(args.plot, dpi=150)


if __name__ == "__main__":
    main()
