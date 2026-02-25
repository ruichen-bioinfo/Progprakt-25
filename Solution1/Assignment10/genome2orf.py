#!/user/bin/env python
import  argparse
import sys
def read_fasta(handle):
    seq={}
    name=None
    parts=[]
    for line in handle:
        line = line.rstrip("\n")
        if line.startswith(">"):
            if name is not None:
                seq[name] = "".join(parts).upper()
            name = line[1:].strip().split()[0]
            parts=[]
        else:
            if line.strip():
                parts.append(line.strip())
    if name is not None:
        seq[name] = "".join(parts).upper()
    return seq
def revcomp(dna):
    comp={"A":"T","C":"G","G":"C","T":"A","N":"N"}
    return "".join(comp.get(b,"N") for b in reversed(dna))
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--organism",required=True,type=argparse.FileType("r"))
    parser.add_argument("--features",required=True,type=argparse.FileType("r"))
    args=parser.parse_args()
    genome=read_fasta(args.organism)
    idx=None
    for line in args.features:
        line=line.rstrip("\n")
        if not line:
            continue
        if line.startswith("#"):
            if line.startswith("# feature"):
                header=line.lstrip("# ").split("\t")
                idx={name:i for i,name in enumerate(header)}
            continue
        if idx is None:
            continue
        cols=line.split("\t")
        if cols[idx["feature"]]!= "CDS":
            continue
        seqid=cols[idx["genomic_accession"]]
        start=int(cols[idx["start"]])
        end=int(cols[idx["end"]])
        strand=cols[idx["strand"]]
        locus_tag=cols[idx["locus_tag"]]
        if seqid not in genome:
            continue
        dna=genome[seqid][start-1:end]
        if strand == "-":
            dna=revcomp(dna)
        sys.stdout.write(f">{locus_tag}\n")
        sys.stdout.write(dna+"\n")
if __name__=="__main__":
    main()


