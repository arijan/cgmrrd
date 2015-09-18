#! /usr/bin/python3

import json
import sys

with open("cgmhosts.json", "w") as file:
    try:
        cgmhosts = json.load(sys.stdin)
    except:
        file.close()
        exit(1)
    file.write(json.dumps(cgmhosts, indent=4, separators=(',', ':'), sort_keys=True))
    file.close()

