#! /usr/bin/python3

import json

print("Content-type: text/html\n")

with open("cgmhosts.json") as file:
    cgmhosts = json.load(file)
    file.close()

print(json.dumps(cgmhosts, indent=4, separators=(',', ':'), sort_keys=True))

