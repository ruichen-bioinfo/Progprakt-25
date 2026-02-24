import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()
inputt = args.input
outputFolder = args.output
os.makedirs(outputFolder, exist_ok=True)
DataTypes = {}
Zelllinien = {}
RNAseqSet = set()
ChipseqSet = set()
with open (inputt, "r") as f:
    for line in f:
        line = line.strip()
        spalten = line.split(",")
        Datatype = spalten[0]
        Zelllinie = spalten[1]
        if "=" in spalten[2]:

            Antibody = spalten[2].split("=")[1]
        else:
            Antibody = None
        DCCNummer = spalten[9]
        if Datatype in DataTypes:
            DataTypes[Datatype] += 1
        else:
            DataTypes[Datatype] = 1

        if Zelllinie not in Zelllinien:
            Zelllinien[Zelllinie] = set()

        if Datatype == "ChIP-seq":
            Zelllinien[Zelllinie].add(Antibody)

        #für dritten Teil der Aufgabe

        if Datatype == "RNA-seq":
            RNAseqSet.add(Zelllinie)
        if Datatype == "ChIP-seq" and Antibody == "H3K27me3":
            ChipseqSet.add(Zelllinie)


RNAundChIp = RNAseqSet & ChipseqSet
RNAundChIPDCC = {}

with open (inputt, "r") as f:
    for line in f:
        line = line.strip()
        spalten = line.split(",")
        Datatype = spalten[0]
        Zelllinie = spalten[1]
        if "=" in spalten[2]:

            Antibody = spalten[2].split("=")[1]
        else:
            Antibody = None

        DCCNummer = spalten[9]

        if Zelllinie in RNAundChIp and (
        Datatype == "RNA-seq" or
        (Datatype == "ChIP-seq" and Antibody == "H3K27me3")
            ):
            if DCCNummer:
                if Zelllinie not in RNAundChIPDCC:
                    RNAundChIPDCC[Zelllinie] = set()
                RNAundChIPDCC[Zelllinie].add(DCCNummer)

exptypes_path = os.path.join(outputFolder, "exptypes.tsv")
antibodies_path = os.path.join(outputFolder, "antibodies.tsv")
chip_path = os.path.join(outputFolder, "chip_rna_seq.tsv")


with open(exptypes_path, "w") as f:
    for key, value in DataTypes.items():
        f.write(key + "\t" + str(value) + "\n")

with open(antibodies_path, "w") as f:
    for zelllinie, antibodies in Zelllinien.items():
        f.write(zelllinie + "\t" + str(len(antibodies)) + "\n")

with open(chip_path, "w") as f:
    for key, values in RNAundChIPDCC.items():
        for v in sorted(values):
            f.write(key + "\t" + str(v) + "\n")














