#! /usr/bin/python3

import cgi
import json
import itertools

form = cgi.FieldStorage()

print("Content-type: text/html\n")

with open("cgminer.conf") as file:
    cgminerconf = json.load(file)
    file.close()

urls = form.getlist('url')
users = form.getlist('user')
passwds = form.getlist('pass')

newcgminerpools = []
for cgminerpool, url, user, passwd in itertools.zip_longest(cgminerconf['pools'], urls, users, passwds):
    if url == None: url = cgminerpool['url']
    if user == None: user = cgminerpool['user']
    if passwd == None:passwd = cgminerpool['pass']

    newcgminerpools.append({'url': url, 'user': user, 'pass': passwd})

cgminerconf['pools'] = newcgminerpools
print(json.dumps(cgminerconf, indent=4, separators=(',', ':'), sort_keys=True))
#print(json.dumps(cgminerconf, sort_keys=True))

