# coding=utf-8
### Cgmrrd ReportTable
### Version 2
### Created in 2014 by Arijan Siska

import json
import datetime
from markup import page as htmlpage, oneliner as html
import rrdtool

from cgmdefaults import *

def reporttable():
    # Load Hosts
    cgmhosts = None
    with open(cgmhostsfilename) as file:
        cgmhosts = json.load(file)
    for x in cgmhosts["hosts"]:
        try:
            x["port"]
        except:
            x["port"] = defaultport

    # Initialize HTML
    outhtml = htmlpage()
    outhtml.init(title=u"CgmRRD Work Report", css="cgmrrdreport.css", charset="UTF-8")
    outhtml.h1(u"CgmRRD Report")

    # Hosts table
    outhtml.p(u"Hosts:")
    outhtml.table()
    outhtml.tbody()
    headers = ["hostname", "port"]
    outhtml.tr()
    for y in headers:
        outhtml.th(y)
    outhtml.tr.close()
    for x in cgmhosts['hosts']:
        outhtml.tr()
        for y in headers:
            outhtml.td(x[y])
        outhtml.tr.close()
    outhtml.tbody.close()
    outhtml.table.close()

    # Load rrdtables
    for x in cgmhosts['hosts']:
        cgmrrdhashratefilenamefull = str(
            cgmrrdhashratefilename + "_" + x['hostname'] + "_" + x['port'] + cgmrrddotrrd)
        try:
            x['history'] = rrdtool.fetch(cgmrrdhashratefilenamefull, "AVERAGE", "-s", "now-288d")
            x['historylen'] = len(x['history'][2])
            x['has_history'] = True
        except:
            if debugoutpot:
                print("Cannot fetch history for " + cgmrrdhashratefilenamefull)
            x['has_history'] = False

    # check all RRDs are from same period
    rrdlen = False
    rrdtime_start = False
    rrdtime_end = False
    rrdtimestep = False
    for x in cgmhosts['hosts']:
        if x['has_history']:
            if not rrdlen:
               rrdlen = len(x['history'][2])
            else:
                if rrdlen != len(x['history'][2]):
                    print("RRD problem: len=", rrdlen)
                    exit(1)
            if not rrdtime_start:
                rrdtime_start = x['history'][0][0]
            else:
                if rrdtime_start != x['history'][0][0]:
                    print("RRD problem: start=", rrdtime_start, x['history'][0][0])
                    exit(1)
            if not rrdtime_end:
                rrdtime_end = x['history'][0][1]
            else:
                if rrdtime_end != x['history'][0][1]:
                    print("RRD problem: end=", rrdtime_end, x['history'][0][1])
                    exit(1)
            if not rrdtimestep:
                rrdtimestep = x['history'][0][2]
            else:
                if rrdtimestep != x['history'][0][2]:
                    print("RRD problem: step=", rrdtimestep, x['history'][0][2])
                    exit(1)

    # Work table
    outhtml.p(u"Work:")
    outhtml.table()
    outhtml.tbody()
    headers = []
    for x in cgmhosts['hosts']:
        if x['has_history']:
            for y in x['history'][1]:
                headers.append( \
                    {'hostname':x['hostname'], \
                     'GPU':y, \
                     'name':x['hostname']+'_'+y[-1:], \
                     'data':{ \
                         t:r[int(y[-1:])] \
                            for t,r in zip(range(rrdtime_start, rrdtime_end, rrdtimestep), x['history'][2]) } \
                    })
    headers.insert(0, {'name':'Date'})
    headers.append({'name':'Total'})
    outhtml.tr()
    for y in headers:
        outhtml.th(y['name'])
    outhtml.tr.close()
    for x in range(rrdtime_start, rrdtime_end, rrdtimestep):
        outhtml.tr()
        row_total = 0
        for y in headers:
            if y['name'] == "Date":
                outhtml.td(datetime.datetime.fromtimestamp(int(x)).strftime('%Y-%m-%d'))
            elif y['name'] == "Total":
                outhtml.td(row_total)
            else:
                r = y['data'][x]
                if not isinstance(r, float):
                    r = 0.0
                r = int(round(r  * rrdtimestep / cgmhashesperdiff1share))
                row_total += r
                outhtml.td(str(r))
        outhtml.tr.close()
    outhtml.tbody.close()
    outhtml.table.close()

    # Write out HTML
    with open(wwwdir + "/" + reportHTMLfilename, "w") as file:
        file.write(str(outhtml))

reporttable()
