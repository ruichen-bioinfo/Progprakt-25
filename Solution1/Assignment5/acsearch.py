#!/usr/bin/env python3
import sys
import os
import argparse
import urllib.request
import urllib.error

def get_fasta(ac):
    url = f"https://rest.uniprot.org/uniprotkb/{ac}.fasta"
    try:
        # url
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError:
        return f"Error: AC '{ac}' not found."
    except Exception as e:
        return f"Error: {e}"

def main():
    # CGI
    if 'REQUEST_METHOD' in os.environ:
        import cgi
        import cgitb
        cgitb.enable()
        
        print("Content-Type: text/plain\n")
        
        form = cgi.FieldStorage()
        ac = form.getvalue('ac', '').strip()
        
        if ac:
            print(get_fasta(ac))
        else:
            print("Error: No Accession Number provided.")
            
    # CLI as for add in
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument("--ac", required=True)
        args = parser.parse_args()
        print(get_fasta(args.ac))

if __name__ == "__main__":
    main()