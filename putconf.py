#! /usr/bin/python3

import json
import sys

with open("cgminer.conf", "w") as file:
    try:
        cgminerconf = json.load(sys.stdin)
    except:
        file.close()
        exit(1)
    file.write(json.dumps(cgminerconf, indent=4, separators=(',', ':'), sort_keys=True))
    file.close()

