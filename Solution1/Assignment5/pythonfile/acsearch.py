
import argparse

import requests

parser = argparse.ArgumentParser()
parser.add_argument("--ac")
args = parser.parse_args()
seqid = args.ac

URL = f"https://rest.uniprot.org/uniprotkb/{seqid}.fasta"

response = requests.get(URL)

print(response.text)
