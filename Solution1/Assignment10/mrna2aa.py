#！/user/bin/env python3
import argparse
import sys
CODON_TABLE = {
    "UUU": "F", "UUC": "F", "UUA": "L", "UUG": "L",
    "UCU": "S", "UCC": "S", "UCA": "S", "UCG": "S",
    "UAU": "Y", "UAC": "Y", "UAA": "*", "UAG": "*",
    "UGU": "C", "UGC": "C", "UGA": "*", "UGG": "W",

    "CUU": "L", "CUC": "L", "CUA": "L", "CUG": "L",
    "CCU": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    "CAU": "H", "CAC": "H", "CAA": "Q", "CAG": "Q",
    "CGU": "R", "CGC": "R", "CGA": "R", "CGG": "R",

    "AUU": "I", "AUC": "I", "AUA": "I", "AUG": "M",
    "ACU": "T", "ACC": "T", "ACA": "T", "ACG": "T",
    "AAU": "N", "AAC": "N", "AAA": "K", "AAG": "K",
    "AGU": "S", "AGC": "S", "AGA": "R", "AGG": "R",

    "GUU": "V", "GUC": "V", "GUA": "V", "GUG": "V",
    "GCU": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "GAU": "D", "GAC": "D", "GAA": "E", "GAG": "E",
    "GGU": "G", "GGC": "G", "GGA": "G", "GGG": "G",
}
def translate_rna(rna):
    rna=rna.strip().upper()
    for character in rna:
        if character not in{"A","U","C","G"}:
            return None
        protein=[]
    for  i in range(0, len(rna), 3):
        codon=rna[i:i+3]
        aa=CODON_TABLE[codon]
        if aa is None:
            return None
        if aa =="*":
            break
        protein.append(aa)
    return "".join(protein)
def fasta_reader(handle):
    header=None
    seq_lines=[]
    for line in handle:
        line=line.rstrip("\n")
        if line.startswith(">"):
            if header is not None:
                yield header, "".join(seq_lines)
            header=line[1:].strip()
            seq_lines=[]
        else:
            if line.strip():
                seq_lines.append(line.strip())
    if header is not None:
        yield header, "".join(seq_lines)
def main():
    parser = argparse.ArgumentParser(description="mrna to protein")
    parser.add_argument("--fasta",type=argparse.FileType("r"),help="Input fasta file or '-' for stdin")
    args = parser.parse_args()
    for header, rna in fasta_reader(args.fasta):
        protein=translate_rna(rna)
        if protein is None:
            continue
        sys.stdout.write(f">{header}\n")
        sys.stdout.write(protein+"\n")
if __name__ == "__main__":
    main()
