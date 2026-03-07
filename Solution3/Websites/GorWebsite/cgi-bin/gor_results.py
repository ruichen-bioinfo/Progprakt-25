#!/usr/bin/env python3
import sys
sys.stdout.write("Content-Type: application/json\r\n\r\n")
sys.stdout.flush()

import os, json
sys.path.insert(0, os.path.dirname(__file__))
import gor_config as C

RESULTS_JSON = os.path.join(C.TMP_DIR, "psipred_results.json")
try:
    with open(RESULTS_JSON) as f:
        print(f.read())
except FileNotFoundError:
    print("{}")
except Exception as e:
    print("{}")
