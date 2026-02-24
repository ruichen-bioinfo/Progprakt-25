#!/usr/bin/env python3
import argparse

def parse_semicolon_list(s: str):
    parts = [p.strip() for p in s.split(";")]
    return [p for p in parts if p]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyword", nargs="+", required=True)
    parser.add_argument("--swissprot", type=argparse.FileType("r"), required=True,
                        help="path to swissprot .dat or '-' for stdin")
    args = parser.parse_args()

    query = set(args.keyword)
    results = set()

    entry_lines = []
    for line in args.swissprot:
        line = line.rstrip("\n")
        entry_lines.append(line)

        if line.startswith("//"):
            ac_text = []
            kw_text = []

            for l in entry_lines:
                if l.startswith("AC"):
                    ac_text.append(l[5:].strip())   # after "AC   "
                elif l.startswith("KW"):
                    kw_text.append(l[5:].strip())   # after "KW   "

            acs = set(parse_semicolon_list(" ".join(ac_text)))
            kws = set(parse_semicolon_list(" ".join(kw_text)))

            if acs and (kws & query):
                results.update(acs)

            entry_lines = []

    for ac in sorted(results):
        print(ac)

if __name__ == "__main__":
    main()
