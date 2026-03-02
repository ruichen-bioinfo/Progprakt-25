#!/usr/bin/env python3
import argparse
import random
import sys


def generate_random_sequence(length, gc_fraction):
    # Anzahl GC-Basen berechnen
    gc_count = int(round(length * gc_fraction))

    # Rest sind AT-Basen
    at_count = length - gc_count

    seq = []

    # GC-Basen zufällig verteilen (G oder C)
    for _ in range(gc_count):
        seq.append(random.choice(["G", "C"]))

    # AT-Basen zufällig verteilen (A oder T)
    for _ in range(at_count):
        seq.append(random.choice(["A", "T"]))

    # Reihenfolge zufällig mischen
    random.shuffle(seq)

    return "".join(seq)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--length", type=int, required=True, help="Länge der Sequenz")
    parser.add_argument("--gc", type=float, required=True, help="GC-Gehalt (zwischen 0 und 1)")
    parser.add_argument("--name", default="random_sequence", help="Name der Sequenz")
    args = parser.parse_args()

    length = args.length
    gc = args.gc
    name = args.name

    # Plausibilitätsprüfung
    if length <= 0:
        print("Länge muss > 0 sein", file=sys.stderr)
        sys.exit(1)

    if not (0.0 <= gc <= 1.0):
        print("GC muss zwischen 0 und 1 liegen", file=sys.stderr)
        sys.exit(1)

    # Sequenz erzeugen
    seq = generate_random_sequence(length, gc)

    # FASTA-Ausgabe
    print(f">{name}")
    print(seq)


if __name__ == "__main__":
    main()
