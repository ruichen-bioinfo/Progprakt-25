#!/usr/bin/env python3
import sys
import os
import argparse


DB_PATH = "/mnt/extstud/praktikum/bioprakt/Data/swissprot45.dat"

def parse_semicolon_list(s: str):
    parts = [p.strip() for p in s.split(";")]
    return [p for p in parts if p]

def search_keywords(input_keywords, file_handle):
    # set lower for allignment
    query = set(k.lower() for k in input_keywords)
    results = set()
    
    current_ac = []
    current_kw = []
    
    for line in file_handle:
        line = line.rstrip("\n")
        
        if line.startswith("ID"):
            current_ac = []
            current_kw = []
            
        elif line.startswith("AC"):
            # AC   P12345; Q9ABC3; likewise from example
            parts = line[5:].strip().split(';')
            for p in parts:
                if p.strip(): current_ac.append(p.strip())
                
        elif line.startswith("KW"):
            # KW   Kinase; Phosphorylation.
           
            kw_line = line[5:].strip().rstrip('.')
            parts = kw_line.split(';')
            for p in parts:
                if p.strip(): current_kw.append(p.strip().lower())
                
        elif line.startswith("//"):
            # Check apply, as long as one is applied
            if any(q in current_kw for q in query):
                results.update(current_ac)

    return sorted(list(results))

def main():
    #CGI
    if 'REQUEST_METHOD' in os.environ:
        import cgi
        import cgitb
        cgitb.enable()
        
        print("Content-Type: text/plain\n")
        
        form = cgi.FieldStorage()
        kw_input = form.getvalue('keywords', '')
        
        if not kw_input:
            print("Error: No keywords provided.")
            return

        keywords = kw_input.split()
        
        try:
            with open(DB_PATH, 'r', encoding='latin-1') as f:
                results = search_keywords(keywords, f)
                for ac in results:
                    print(ac)
                if not results:
                    print("No matches found.")
        except FileNotFoundError:
            print(f"Error: Database file not found at {DB_PATH}")

    # CLI
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument("--keyword", nargs="+", required=True)
        # User upload the file and check for keywords
        parser.add_argument("--swissprot", required=False, default=DB_PATH)
        args = parser.parse_args()
        
        with open(args.swissprot, 'r', encoding='latin-1') as f:
            results = search_keywords(args.keyword, f)
            for ac in results:
                print(ac)

if __name__ == "__main__":
    main()