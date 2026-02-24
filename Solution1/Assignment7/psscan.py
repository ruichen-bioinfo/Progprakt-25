#!/usr/bin/env python3
import sys
import re
import argparse
import urllib.request
import os


# Prosite from Fasta to REGEX readable
def to_regex(pattern):

    pattern = pattern.strip().rstrip('.')

    # 1. Docker fore and after
    if pattern.startswith('<'):
        pattern = '^' + pattern[1:]
    if pattern.endswith('>'):
        pattern = pattern[:-1] + '$'

    # 2. Washoff the -
    pattern = pattern.replace('-', '')

    # 3. Exception tear off {ABC} -> [^ABC]

    pattern = re.sub(r'\{([^\}]+)\}', r'[^\1]', pattern)

    # 4. repetitive (n) -> {n}// (n,m) -> {n,m}

    pattern = pattern.replace('(', '{').replace(')', '}')

    # 5. AS x -> .
    pattern = pattern.replace('x', '.')

    return pattern


#  Web catch Pattern
def get_web_pattern(ps_id):
    # ID confirmation (FROM ABGABE SERVER)
    if not ps_id.startswith('PS') and ps_id[0].isdigit():
        ps_id = 'PS' + ps_id

    # .txt transformation
    url = "https://prosite.expasy.org/" + ps_id + ".txt"

    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')

        # PA Search
        for line in data.splitlines():
            if line.startswith('PA'):
                # 格式: PA   Pattern.
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1].rstrip('.')
    except:
        pass
    return ""


# FASTA read
def read_fasta(handle):
    header = None
    seq = []

    for line in handle:
        line = line.strip()
        if not line:
            continue
        if line.startswith('>'):
            if header:
                yield header, "".join(seq)

            # Use whole as ID
            header = line[1:].strip()
            seq = []
        else:
            seq.append(line)

    if header:
        yield header, "".join(seq)


def main():
    if 'REQUEST_METHOD' in os.environ:
        run_cgi()
        return

    # CLI Param
    parser = argparse.ArgumentParser()
    parser.add_argument('--fasta', required=True)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--pattern')
    group.add_argument('--web')

    parser.add_argument('--extern', action='store_true')  # Bonus 占位

    args = parser.parse_args()

    #  stdin
    if args.fasta == '-':
        f_in = sys.stdin
    else:
        try:
            f_in = open(args.fasta, 'r')
        except:
            sys.exit(1)

    # reach Pattern
    pattern_str = ""
    if args.pattern:
        pattern_str = args.pattern
    elif args.web:
        pattern_str = get_web_pattern(args.web)
        if not pattern_str:
            sys.stderr.write("Error: Pattern not found.\n")
            if f_in != sys.stdin: f_in.close()
            sys.exit(1)

    # regex type
    regex = to_regex(pattern_str)

    #  lookahead overlap search (?=(...))
    try:
        search_re = re.compile(f'(?=({regex}))')
    except:
        sys.exit(1)

    # scan sequence
    for head, seq in read_fasta(f_in):

        # standardization for big and small
        seq_upper = seq.upper()

        for m in search_re.finditer(seq_upper):
            # 1-based index
            start_pos = m.start() + 1
            # group(1) as capture
            matched_seq = m.group(1)
            print(f"{head}\t{start_pos}\t{matched_seq}")

    if f_in != sys.stdin:
        f_in.close()






def run_cgi():
    import cgi

    import cgitb
    cgitb.enable()

    print("Content-Type: text/plain\n")

    form = cgi.FieldStorage()

    fasta_val = form.getvalue('fasta', '')
    pattern_val = form.getvalue('pattern', '')
    web_val = form.getvalue('web', '')

    if not fasta_val:
        print("Error: No FASTA.")
        return

    final_pattern = ""
    if web_val:
        final_pattern = get_web_pattern(web_val)
    else:
        final_pattern = pattern_val

    if not final_pattern:
        print("Error: No Pattern.")
        return

    regex = to_regex(final_pattern)
    search_re = re.compile(f'(?=({regex}))')


    from io import StringIO
    f_sim = StringIO(fasta_val)

    for head, seq in read_fasta(f_sim):
        seq_upper = seq.upper()
        for m in search_re.finditer(seq_upper):
            print(f"{head}\t{m.start() + 1}\t{m.group(1)}")


if __name__ == '__main__':
    main()

