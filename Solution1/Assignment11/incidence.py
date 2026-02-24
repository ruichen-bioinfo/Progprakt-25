#!/usr/bin/env python3


import sys
import argparse

def read_fasta(handle):

    header = None
    seq_lines = []
    for line in handle:
        line = line.strip()
        if not line:
            continue
        if line.startswith('>'):
            if header:
                yield header, ''.join(seq_lines)
            header = line[1:].strip()
            seq_lines = []
        else:
            seq_lines.append(line)
    if header:
        yield header, ''.join(seq_lines)



def count_overlaps(sequence, substring):

    count = 0
    sub_len = len(substring)
    seq_len = len(sequence)
    for i in range(seq_len - sub_len + 1):
        if sequence[i:i+sub_len] == substring:
            count += 1
    return count

def main():
    parser = argparse.ArgumentParser(
        description='Count overlapping occurrences of short sequences in a genome.'
    )
    parser.add_argument('--sequence', required=True, nargs='+',
                        help='One or more short sequences (e.g., CTAG CG AACCCTGTC ATG)')
    parser.add_argument('--genome', required=True,
                        help='FASTA file containing the genome (use "-" for stdin)')
    args = parser.parse_args()

    # Open input (handle '-' as stdin)
    if args.genome == '-':
        infile = sys.stdin
    else:
        try:
            infile = open(args.genome, 'r')
        except Exception as e:
            sys.stderr.write(f"Error opening genome file: {e}\n")
            sys.exit(1)

    # Concatenate all sequences from the FASTA file into one uppercase string
    genome_seq = []
    for header, seq in read_fasta(infile):
        genome_seq.append(seq.upper())   # force uppercase
    full_genome = ''.join(genome_seq)

    if infile != sys.stdin:
        infile.close()

    # Count occurrences for each requested short sequence
    results = {}
    for sub in args.sequence:
        sub_upper = sub.upper()
        cnt = count_overlaps(full_genome, sub_upper)
        results[sub] = cnt

    # Output results
    for sub, cnt in results.items():
        print(f"{sub}: {cnt}")

if __name__ == '__main__':
    main()
