#!/usr/bin/env python3
import argparse
import sys


def read_fasta_records(handle):
    # FASTA-Reader (Blatt 1 Aufgabe 12)
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


def reverse_complement(seq):
    # Reverse Complement berechnen
    comp = {
        "A": "T",
        "T": "A",
        "G": "C",
        "C": "G"
    }

    rev = []
    for base in reversed(seq):
        rev.append(comp.get(base, "N"))

    return "".join(rev)


def find_orfs_in_sequence(seq):
    # alle ORFs in einer Sequenz finden
    stop_codons = {"TAA", "TAG", "TGA"}
    orfs = []

    # 3 Reading Frames
    for frame in range(3):
        i = frame
        while i <= len(seq) - 3:
            codon = seq[i:i+3]

            if codon == "ATG":
                # Start gefunden -> bis erstes Stop-Codon gehen
                j = i + 3
                found_stop = False

                while j <= len(seq) - 3:
                    stop = seq[j:j+3]
                    if stop in stop_codons:
                        # ORF speichern (inkl. Stop)
                        orf_seq = seq[i:j+3]
                        orfs.append(orf_seq)
                        found_stop = True
                        break
                    j += 3

                # Wenn ein Stop gefunden wurde, direkt hinter das Stopcodon springen,
                # damit ATGs innerhalb dieses ORFs nicht als eigene ORFs gezählt werden.
                if found_stop:
                    i = j + 3
                else:
                    i += 3
            else:
                i += 3

    return orfs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fasta", required=True, help="FASTA Datei oder '-' für stdin")
    parser.add_argument("--db", action="store_true", help="ORFs in Datenbank speichern")
    parser.add_argument("--output", help="optional: Ausgabe-Datei")
    args = parser.parse_args()

    # FASTA öffnen (Datei oder stdin)
    if args.fasta == "-":
        fh = sys.stdin
    else:
        fh = open(args.fasta, "r", encoding="utf-8", errors="ignore")

    # Ausgabe vorbereiten
    if args.output:
        out = open(args.output, "w", encoding="utf-8")
    else:
        out = sys.stdout

    # DB vorbereiten (nur wenn --db gesetzt)
    if args.db:
        try:
            import mysql.connector
            from db_config import DB_CONFIG

            cnx = mysql.connector.connect(**DB_CONFIG)
            cursor = cnx.cursor()
        except Exception as e:
            print(f"DB-Verbindung fehlgeschlagen: {e}", file=sys.stderr)
            sys.exit(1)

    # alle Sequenzen durchgehen
    for seq_id, seq in read_fasta_records(fh):

        all_orfs = []

        # ORFs auf Vorwärts-Strang
        forward_orfs = find_orfs_in_sequence(seq)
        all_orfs.extend(forward_orfs)

        # ORFs auf Reverse-Strang
        rev_seq = reverse_complement(seq)
        reverse_orfs = find_orfs_in_sequence(rev_seq)
        all_orfs.extend(reverse_orfs)

        # ORFs ausgeben
        for idx, orf in enumerate(all_orfs):
            header = f">{seq_id}_{idx}"
            out.write(header + "\n")
            out.write(orf + "\n")

            # optional in DB speichern
            if args.db:
                try:
                    insert_sql = """
                        INSERT INTO sequences
                            (accession, source, seq_type, organism, sequence, length, description, gene_name)
                        VALUES
                            (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        f"{seq_id}_{idx}",      # accession
                        "ORF_FINDER",           # source
                        "dna",                  # seq_type (ORF ist Nukleotid-Sequenz)
                        None,                   # organism (haben wir hier nicht)
                        orf,                    # sequence
                        len(orf),               # length
                        f"ORF aus {seq_id}",    # description
                        None                    # gene_name (haben wir hier nicht)
                    )
                    cursor.execute(insert_sql, values)
                except Exception as e:
                    print(f"Insert fehlgeschlagen: {e}", file=sys.stderr)

    # DB commit + schließen
    if args.db:
        cnx.commit()
        cursor.close()
        cnx.close()

    if args.output:
        out.close()

    if args.fasta != "-":
        fh.close()


if __name__ == "__main__":
    main()
