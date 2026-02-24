#!/usr/bin/env python3
import argparse
import sys

import requests

parser = argparse.ArgumentParser()
parser.add_argument("--ac")
args = parser.parse_args()
seqid = args.ac

URL = f"https://rest.uniprot.org/uniprotkb/{seqid}.fasta"

try:
    response = requests.get(URL)
    if response.status_code == 200:
        print(response.text)
    else:
        pass

except requests.exceptions.RequestException:
    pass


