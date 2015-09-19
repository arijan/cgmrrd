<<<<<<< HEAD
# coding=utf-8
# CgmRRD
# version 2
# Created in 2014 by Arijan Siska

import os.path
import re
import json
from time import localtime, strftime
from multiprocessing.dummy import Pool, Lock
import rrdtool

import pycgminer
from markup import page as htmlpage, oneliner as html
from cgmdefaults import *


def second2weekdayhourminsec(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    weeks, days = divmod(days, 7)

    return weeks, days, hours, minutes, seconds


class Encoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


def interpolatecolors(colors):
    newcolors = [colors[0]]
    prevcolor = None
    for c in colors:
        if prevcolor:
            newc = "#"
            for rgb in [1, 3, 5]:
                newc = newc + format(int(0.5*(int(c[rgb:rgb+2], 16) + int(prevcolor[rgb:rgb+2], 16))), '02X')
            newcolors.append(newc)
            newcolors.append(c)
        prevcolor = c
    return newcolors


def darkencolor(color, f):
    newc = "#"

    for rgb in [1, 3, 5]:
        newc = newc + format(int(f * (int(color[rgb:rgb+2], 16)) + (1 - f) * 255), '02X')

    return newc


def getcgminerdata( data ):
    host, lock = data

    if debugoutput:
        with lock:
            print("Getting data from: " + host['hostname'] + ':' + host['port'])

    try:
        host['is hashing'] = True
        host['CgminerAPI'] = pycgminer.CgminerAPI(host['hostname'], int(host['port']))
        host['Summary'] = host['CgminerAPI'].summary()
        host['Devs'] = host['CgminerAPI'].devs()
        host['Pools'] = host['CgminerAPI'].pools()
    except:
        with lock:
            print("Cannot connect via API to", host['hostname'], host['port'])

        host['is hashing'] = False


def cgmrrdgetdata():

    # Get host configuration data from file

    cgmhosts = None

    try:
        cgmhostsfile = open(cgmhostsfilename)
        cgmhosts = json.load(cgmhostsfile)
        cgmhostsfile.close()
    except:
        print("Cgminer hosts file (" + cgmhostsfilename + ") format error or file missing!")
        exit(1)

    pseudoshelf = 1
    for host in cgmhosts['hosts']:
        if 'hostname' not in host:
            print("Hostname missing: ", host)
            exit(1)

        if 'port' not in host:
            host['port'] = defaultport

        if 'name' not in host:
            host['name'] = host['hostname']

        if 'row' not in host:
            host['row'] = "1"

        if 'rack' not in host:
            host['rack'] = "1"

        if 'shelf' not in host:
            host['shelf'] = str(pseudoshelf)
            pseudoshelf += 1

    # Get cgminer data for all hosts via cgminerAPI

    print("Fetching data.")

    pool = Pool(numberofIOthreads)
    lock = Lock()

    pool.map(getcgminerdata, [(x, lock) for x in cgmhosts['hosts']])
    pool.close()
    pool.join()

    # Dump all host data

    # with open("cgmhostsdata.json", "w") as file:
    #     json.dump(cgmhosts, file, cls=Encoder)
    # file.close()

    for host in cgmhosts['hosts']:
        i = 0

        if host['is hashing']:
            for device in host['Devs']['DEVS']:
                if device['MHS 5s'] > 0:
                    device['is hashing'] = True
                else:
                    print("Host " + host['hostname'] + ":" + host['port'] + ", device not working: GPU" + str(i))
                    device['is hashing'] = False

                i += 1

    # Quick report

    print("All hosts: " + str(len(cgmhosts['hosts'])))

    allGPUs = 0
    livehosts = 0

    for host in cgmhosts['hosts']:
        if host['is hashing']:
            livehosts += 1
            allGPUs += len(host['Devs']['DEVS'])
            if debugoutput:
                print("    " + host['hostname'] + ':' + host['port'])
                print("        Devices:" + str(len(host['Devs']['DEVS'])))
                print("        Pools:" + str(len(host['Pools']['POOLS'])))

    print("Live hosts: " + str(livehosts))
    print("Dead hosts: " + str(len(cgmhosts['hosts']) - livehosts))

    if debugoutput:
        for host in cgmhosts['hosts']:
            print(("+   " if host['is hashing'] else "-   ") + host['hostname'] + ':' + host['port'])

    # Generate HTML report file

    print("Generating html.")

    currentlocaltime = strftime("%s", localtime())
    currentlocaltimelongstring = strftime("%Y-%m-%d_%H:%M:%S", localtime())

    htmldoc = htmlpage()
    htmldoc.init(title=u"CgminerRRD Report", css=mainCSSfilename, charset="UTF-8")
    htmldoc.meta(http_equiv="refresh", content=cgmrrdstep)
    htmldoc.h1(u"CgminerRRD (2014)")
    htmldoc.p(u"Reported at: " + currentlocaltimelongstring)
    htmldoc.p(u"Overall performance graphs:")

    htmldoc.p()
    htmldoc.table()
    htmldoc.tbody()
    htmldoc.tr()

    for timemarker in sorted(cgmrrdtimepostfix):
        htmldoc.td(html.img(src=str(cgmrrdtotalgraphfilename + "_" + timemarker + cgmrrddotimage)))

    htmldoc.tr.close()
    htmldoc.tbody.close()
    htmldoc.table.close()
    htmldoc.p.close()

    for host in cgmhosts['hosts']:
        htmldoc.h2("Host " + host['hostname'] + ":" + host['port'])

        if host['is hashing']:
            hostsummary = host['Summary']['SUMMARY'][0]
            hoststatus = host['Summary']['STATUS'][0]

            htmldoc.p()
            htmldoc.table()
            htmldoc.thead(html.tr(html.th([u"Hostname", u"Port", u"CGminer Ver", u"Work Util", u"Pool MHs",
                                           u"Rejected Shares %", u"Total MH", u"Found Blocks", u"Uptime"])))
            htmldoc.tbody()
            htmldoc.tr(html.td([host['hostname'],
                                host['port'],
                                hoststatus['Description'],
                                hostsummary['Work Utility'],
                                round(float(hostsummary['Work Utility']) * cgmhashesperdiff1share / 60.0 / 1.0E6, 3),  # WU * H/diff1share / 60s / 1E6 H/MH
                                round(100.0 * float(hostsummary['Difficulty Rejected']) / (
                                    0.0001 + float(hostsummary['Difficulty Accepted']) + float(hostsummary['Difficulty Rejected'])), 2),
                                hostsummary['Total MH'],
                                hostsummary['Found Blocks'],
                                "{0}w {1}d {2}h {3}m {4}s".format(*second2weekdayhourminsec(hostsummary['Elapsed']))
                                ]))

            htmldoc.tbody.close()
            htmldoc.table.close()
            htmldoc.p.close()

            htmldoc.p()
            htmldoc.table()
            htmldoc.thead(html.tr(html.th([u"Status", u"Activity %", u"Intensity", u"Temper. C", u"Fan Speed", u"Fan Percent",
                                           u"GPU Clock", u"Memory Clock", u"Voltage", u"MHS 5s", u"MHS av",
                                           u"Difficulty Accepted", u"Difficulty Rejected", u"Hardware Errors",
                                           u"Rejected Shares %"])))
            htmldoc.tbody()

            for device in host['Devs']['DEVS']:
                if device['is hashing']:
                    htmldoc.tr(html.td(
                        [device['Status'], device['GPU Activity'], device['Intensity'], device['Temperature'],
                         device['Fan Speed'], device['Fan Percent'], device['GPU Clock'], device['Memory Clock'],
                         device['GPU Voltage'], device['MHS 5s'], device['MHS av'], device['Difficulty Accepted'],
                         device['Difficulty Rejected'], device['Hardware Errors'], round(device['Difficulty Rejected'] / (
                         0.0001 + device['Difficulty Rejected'] + device['Difficulty Accepted']) * 100, 2)]))
                else:
                    htmldoc.tr(html.td('Dead!'))


            htmldoc.tbody.close()
            htmldoc.table.close()
            htmldoc.p.close()

            htmldoc.p()
            htmldoc.table()
            htmldoc.thead(html.tr(html.th([u"Pool", u"Priority", u"Status", u"Difficulty Accepted", u"Difficulty Rejected",
                                           u"Rejected Shares %", u"Difficulty Stale", u"Remote Failures", u"Best Share"])))
            htmldoc.tbody()

            for pool in host['Pools']['POOLS']:
                htmldoc.tr(html.td([pool['URL'], pool['Priority'], pool['Status'], pool['Difficulty Accepted'],
                                    pool['Difficulty Rejected'], round(pool['Difficulty Rejected'] / (
                                    0.0001 + pool['Difficulty Rejected'] + pool['Difficulty Accepted']) * 100, 2),
                                    pool['Difficulty Stale'], pool['Remote Failures'], pool['Best Share']]))

            htmldoc.tbody.close()
            htmldoc.table.close()
            htmldoc.p.close()

        else:
            htmldoc.p('Host is not responding!')

        htmldoc.p()
        htmldoc.table()
        htmldoc.tbody()

        for timemarker in sorted(cgmrrdtimepostfix):
            htmldoc.tr(html.td([
                html.img(src="cgmhashrate_" + host['hostname'] + "_" + host['port'] + "_" + timemarker + cgmrrddotimage),
                html.img(src="cgmtemperature_" + host['hostname'] + "_" + host['port'] + "_" + timemarker + cgmrrddotimage)]))

        htmldoc.tbody.close()
        htmldoc.table.close()
        htmldoc.p.close()

    try:
        htmlfile = open(os.path.join(wwwdir, mainHTMLfilename), "w")
        htmlfile.write(str(htmldoc))
        htmlfile.close()
    except:
        print("Cannot open HTML file " + mainHTMLfilename + " for writing")
        exit(1)

    # Generate HTML dashboard file

    htmldoc2 = htmlpage()
    htmldoc2.init(title=u"CgminerRRD Dashboard", css=dashCSSfilename, charset="UTF-8")
    htmldoc2.meta(http_equiv="refresh", content=cgmrrdstep)
    htmldoc2.h1(u'CgminerRRD (2014)')
    htmldoc2.p(u'Reported at: ' + currentlocaltimelongstring)
    htmldoc2.p(u'Dashboard:')

    dashrows = [int(h['row']) for h in cgmhosts['hosts']]
    htmldoc2.p()
    htmldoc2.table(class_=u'row')
    htmldoc2.tbody()

    for row in range(min(dashrows), max(dashrows) + 1):
        htmldoc2.tr(html.td(u"Row: " + str(row)))

        htmldoc2.tr()
        htmldoc2.td()
        htmldoc2.table(class_=u'rack')
        htmldoc2.tbody()
        htmldoc2.tr()
        dashracks = [int(h['rack']) for h in cgmhosts['hosts'] if int(h['row']) == row]

        for rack in range(min(dashracks), max(dashracks) + 1):
            htmldoc2.td(u"Rack: " + str(rack))

        htmldoc2.tr.close()
        htmldoc2.tr()

        for rack in range(min(dashracks), max(dashracks) + 1):
            htmldoc2.td()
            htmldoc2.table(class_='shelf')
            htmldoc2.tbody()

            dashshelfs = [int(h['shelf']) for h in cgmhosts['hosts'] if int(h['row']) == row and int(h['rack']) == rack]

            for shelf in range(max(dashshelfs), min(dashshelfs)-1, -1):  # Alternative: for shelf in range(5, 0, -1):
                htmldoc2.tr(html.td(u"Shelf:" + str(shelf)))

                dashhost = [h for h in cgmhosts['hosts'] if int(h['row']) == row and int(h['rack']) == rack and int(h['shelf']) == shelf]

                htmldoc2.tr()
                htmldoc2.td()
                htmldoc2.table(class_=u'hostup' if len(dashhost) == 1 and 'Summary' in dashhost[0] else u'hostdown')
                htmldoc2.tbody()

                if len(dashhost) > 1:
                    print("Shelf overocupied! row=", row, "rack=", rack, "shelf=", shelf)
                    exit(1)

                if len(dashhost) == 1:
                    htmldoc2.tr(html.td([u"Name", dashhost[0]['name']]))
                    htmldoc2.tr(html.td([u"IP-Port", dashhost[0]['CgminerAPI'].host + u"-" + str(dashhost[0]['CgminerAPI'].port)]))

                    if 'Summary' in dashhost[0]:
                        htmldoc2.tr(html.td([u"Uptime", u"{0}w {1}d {2}h {3}m {4}s".format(*second2weekdayhourminsec(int(dashhost[0]['Summary']['SUMMARY'][0]['Elapsed'])))]))
                        htmldoc2.tr(html.td([u"kH/s", str(1000.0 * dashhost[0]['Summary']['SUMMARY'][0]['MHS 5s'])]))

                        dashhwerr = dashhost[0]['Summary']['SUMMARY'][0]['Hardware Errors']
                        if dashhwerr > dashhwerrhigh:
                            dashclass = u"hwerr"
                        else:
                            dashclass = u""

                        htmldoc2.tr(html.td([u"HW_Errors", str(dashhwerr)], class_=dashclass))

                        dashrej = dashhost[0]['Summary']['SUMMARY'][0]['Pool Rejected%']
                        if dashrej > dashrejecthigh:
                            dashclass = u"rej"
                        else:
                            dashclass = u""

                        htmldoc2.tr(html.td([u"Pool_Rej%", str(dashrej)], class_=dashclass))
                        htmldoc2.tr(html.td([u"Dev_Rej%", str(dashhost[0]['Summary']['SUMMARY'][0]['Device Rejected%'])]))
                        htmldoc2.tr(html.td([u"Blocks", str(dashhost[0]['Summary']['SUMMARY'][0]['Found Blocks'])]))
                        htmldoc2.tr(html.td([u"Utility", str(dashhost[0]['Summary']['SUMMARY'][0]['Utility'])]))

                        htmldoc2.tr()
                        htmldoc2.td(colspan=2)
                        htmldoc2.table(class_=u'gpu')
                        htmldoc2.thead(html.tr(html.td([u"Device", u"Temper", u"Fan", u"kH/s"])))
                        htmldoc2.tbody()

                        if dashhost[0]['is hashing']:
                            for g in dashhost[0]['Devs']['DEVS']:
                                if g['is hashing']:
                                    dashtem = g['Temperature']
                                    if dashtem > dashtemphigh:
                                        dashclass = u"hitemp"
                                    else:
                                        dashclass = u""

                                    htmldoc2.tr()
                                    htmldoc2.td(u"GPU" + str(g['GPU']))
                                    htmldoc2.td(str(dashtem) + u"C", class_=dashclass)
                                    htmldoc2.td(str(g['Fan Speed']))
                                    htmldoc2.td(str(1000.0 * g['MHS 5s']))
                                    htmldoc2.tr.close()
                                else:
                                    htmldoc2.tr(html.td(u'GPU DEAD!', class_=u"hitemp", colspan=4))

                        htmldoc2.tbody.close()
                        htmldoc2.table.close()  # gpu
                        htmldoc2.td.close()
                        htmldoc2.tr.close()
                    else:
                        htmldoc2.tr(html.td(u"Host DOWN!", colspan=2))

                    htmldoc2.tbody.close()
                    htmldoc2.table.close()  # host
                    htmldoc2.td.close()
                    htmldoc2.tr.close()
                else:
                    htmldoc2.table(html.tbody(u'Empty shelf!'), class_='hostup')

            htmldoc2.tbody.close()
            htmldoc2.table.close()  # shelf
            htmldoc2.td.close()

        htmldoc2.tr.close()
        htmldoc2.tbody.close()
        htmldoc2.table.close()  # rack
        htmldoc2.td.close()
        htmldoc2.tr.close()

    htmldoc2.tbody.close()
    htmldoc2.table.close()  # row
    htmldoc2.p.close()

    try:
        htmlfile = open(os.path.join(wwwdir, dashHTMLfilename), "w")
        htmlfile.write(str(htmldoc2))
        htmlfile.close()
    except:
        print("Cannot write to file:", os.path.join(wwwdir, dashHTMLfilename))
        exit(1)

    # Assure we have enough colors available

    allGPUs = 0

    for host in cgmhosts['hosts']:
        cgmrrdhashratefilenamefull = str(cgmrrdhashratefilename + "_" + host['hostname'] + "_" + host['port'] + cgmrrddotrrd)

        if os.path.exists(cgmrrdhashratefilenamefull):
            for x in [re.search(r'GPU([0-9]+)', x).group(1) for x in rrdtool.info(cgmrrdhashratefilenamefull) if x.startswith('ds') and x.endswith('.index')]:
                allGPUs += 1
        else:
            if host['is hashing']:
                for device in host['Devs']['DEVS']:
                    if device['is hashing']:
                        allGPUs += 1

    global cgmrrdcolors

    while len(cgmrrdcolors) < allGPUs:
        cgmrrdcolors = interpolatecolors(cgmrrdcolors)

    for number, color in enumerate(cgmrrdcolors):
        if number % 2 == 0:
            color = darkencolor(color, 0.5)
            cgmrrdcolors[number] = color

    # Update RRDs

    print("Updating:"),

    colorindex = 0

    for host in cgmhosts['hosts']:
        cgmrrdhashratefilenamefull = str(cgmrrdhashratefilename + "_" + host['hostname'] + "_" + host['port'] + cgmrrddotrrd)
        cgmrrdtemperaturefilenamefull = str(cgmrrdtemperaturefilename + "_" + host['hostname'] + "_" + host['port'] + cgmrrddotrrd)

        if (not host['is hashing']) and (not os.path.exists(cgmrrdhashratefilenamefull)):
            continue

        if not host['is hashing']:
            cgmrrdhashratefileinfo = rrdtool.info(cgmrrdhashratefilenamefull)
            temperaturestring = hashratestring = currentlocaltime
            host['Devs'] = {}
            hostdeviceindexes = [int(re.search(r'GPU([0-9]+)', x).group(1)) for x in cgmrrdhashratefileinfo if x.startswith('ds') and x.endswith('.index')]
            host['Devs']['DEVS'] = range(len(hostdeviceindexes))

            for x in hostdeviceindexes:
                host['Devs']['DEVS'][x] = {}
                host['Devs']['DEVS'][x]['Difficulty Accepted'] = 0
                host['Devs']['DEVS'][x]['Temperature'] = "NaN"
        else:
            temperaturestring = hashratestring = str(host['Summary']['STATUS'][0]['When'])

        rrddatasource = []
        rrddatasourcegauge = []
        index = 0

        for device in host['Devs']['DEVS']:
            hashratestring += ":" + str(int(cgmhashesperdiff1share * device['Difficulty Accepted']))
            temperaturestring += ":" + str(device['Temperature'])
            rrddatasource.append("DS:GPU" + str(index) + ":DERIVE:" + str(cgmrrdstep * 3) + ":0:1E+8")
            rrddatasourcegauge.append("DS:GPU" + str(index) + ":GAUGE:" + str(cgmrrdstep * 3) + ":-50:150")
            index += 1

        print("RRDs"),
        if debugoutput:
            print("Updating rrd file: " + cgmrrdhashratefilenamefull + "," + cgmrrdtemperaturefilenamefull)
            print("    Hashrate: " + hashratestring)
            print("    Temperature: " + temperaturestring)

        # Update RRD Hash Database with data, if database does not exists, create one

        try:
            rrdtool.update(cgmrrdhashratefilenamefull, hashratestring)
        except:
            print("Cannot update rrd file: " + cgmrrdhashratefilenamefull + " with " + hashratestring)

            if os.path.exists(cgmrrdhashratefilenamefull):
                print("Rrd file exsists. Something is wrong.")
                exit(1)

            try:
                print("Creating rrd file: " + cgmrrdhashratefilenamefull)
                rrdtool.create(cgmrrdhashratefilenamefull, "--start", "now-1d", "--step", str(cgmrrdstep), rrddatasource + cgmrrdrradefs)
            except:
                print("Cannot create rrd file: " + cgmrrdhashratefilenamefull + ":" + str(rrdtool.error()))
                exit(1)

        # Update RRD Temperature Database with data, if database does not exists, create one

        try:
            rrdtool.update(cgmrrdtemperaturefilenamefull, temperaturestring)
        except:
            print("Cannot update rrd file: " + cgmrrdtemperaturefilenamefull + " with " + temperaturestring)

            if os.path.exists(cgmrrdtemperaturefilenamefull):
                print("Rrd file exsists. Something is wrong.")
                exit(1)

            try:
                print("Creating rrd file: " + cgmrrdtemperaturefilenamefull)
                rrdtool.create(cgmrrdtemperaturefilenamefull, "--start", "now-1d", "--step", str(cgmrrdstep), rrddatasourcegauge + cgmrrdrradefs)
            except:
                print("Cannot create rrd file: " + cgmrrdtemperaturefilenamefull + ":" + str(rrdtool.error()))
                exit(1)

        # Fetch RRD HashrateHistory

        # print("Fetching rrd " + cgmrrdhashratefilenamefull + " for " + "now-24d")

        # try:
        #     host['HashrateHistory'] = rrdtool.fetch(cgmrrdhashratefilenamefull, "AVERAGE", "-s", "now-24d")
        # except:
        #     print("Cannot fetch history for " + cgmrrdhashratefilenamefull)
        #     exit(1)

        # Fetch RRD TemperatureHistory

        # print("Fetching rrd " + cgmrrdtemperaturefilenamefull + " for " + "now-24d")

        # try:
        #     host['TemperatureHistory'] = rrdtool.fetch(cgmrrdtemperaturefilenamefull, "AVERAGE", "-s", "now-24d")
        # except:
        #     print("Cannot fetch history for " + cgmrrdtemperaturefilenamefull)
        #     exit(1)

        # Generate RRD Hash Graphs

        print("Graphs"),
        defstrings = []
        cdefstrings = []
        areastrings = []
        averagestrings = []
        gprintstrings = []
        totalstrings = "CDEF:Total=0"
        totalaveragestrings = "VDEF:Average=Total,AVERAGE"
        totalaveragelinestrings = "LINE1:Average" + cgmrrdaveragecolors[0]
        index = 0
        hostcolorindex = colorindex

        for device in host['Devs']['DEVS']:
            indexstr = str(index)
            defstrings.append(str("DEF:G" + indexstr + "=" + cgmrrdhashratefilenamefull + ":GPU" + indexstr + ":AVERAGE"))
            cdefstrings.append(str("CDEF:GPU" + indexstr + "=G" + indexstr))
            averagestrings.append(str("VDEF:avg" + indexstr + "=GPU" + indexstr + ",AVERAGE"))
            areastrings.append(str("AREA:GPU" + indexstr + cgmrrdcolors[hostcolorindex] + ":GPU" + indexstr + ":STACK"))
            areastrings.append(str("GPRINT:avg" + indexstr + ":%.0lf%s"))
            totalstrings += ",GPU" + indexstr + ",+"
            index += 1
            hostcolorindex += 1

        gprintstrings.append(str("GPRINT:Average:Average %.0lf%S\l"))

        try:
            for timemarker in cgmrrdtimepostfix:
                cgmrrdgraphhashfilenamefull = str(cgmrrdhashratefilename + "_" + host['hostname'] + "_" + host['port'] + "_" + timemarker + cgmrrddotimage)
                if debugoutput:
                    print("Creating graph image: " + cgmrrdgraphhashfilenamefull)
                rrdtool.graph(os.path.join(wwwdir, cgmrrdgraphhashfilenamefull), "-c", "BACK#FAF4F4", "-a", fileformatstr, "-w",
                              str(cgmrrdgraphw), "-h", str(cgmrrdgraphh), "-l", "0", "--disable-rrdtool-tag",
                              "--border", "0", "--grid-dash", "1:0", "--start", cgmrrdtimepostfix[timemarker], "--step",
                              cgmrrdtimestep[timemarker], "--legend-position", "north", "--vertical-label", "Hashes/s",
                              defstrings, cdefstrings, averagestrings, areastrings, totalstrings, totalaveragestrings,
                              totalaveragelinestrings, gprintstrings)
        except:
            print("Cannot create graph image")

        # Generate RRD Temperature Graphs

        defstrings = []
        linestrings = []
        averagestrings = []
        maxstrings = []
        index = 0
        hostcolorindex = colorindex

        for device in host['Devs']['DEVS']:
            indexstr = str(index)
            defstrings.append(
                str("DEF:GPU" + indexstr + "=" + cgmrrdtemperaturefilenamefull + ":GPU" + indexstr + ":AVERAGE"))
            averagestrings.append(str("VDEF:avg" + indexstr + "=GPU" + indexstr + ",AVERAGE"))
            maxstrings.append(str("VDEF:max" + indexstr + "=GPU" + indexstr + ",MAXIMUM"))
            linestrings.append(str("LINE1:GPU" + indexstr + cgmrrdcolors[hostcolorindex] + ":GPU" + indexstr))
            linestrings.append(str("GPRINT:avg" + indexstr + ":Avg %.1lfC"))
            linestrings.append(str("GPRINT:max" + indexstr + ":Max %.1lfC"))
            index += 1
            hostcolorindex += 1

        linestrings.append(str("COMMENT:\l"))

        try:
            for timemarker in cgmrrdtimepostfix:
                cgmrrdgraphtemperaturefilenamefull = str(
                    cgmrrdtemperaturefilename + "_" + host['hostname'] + "_" + host['port'] + "_" + timemarker + cgmrrddotimage)
                if debugoutput:
                    print("Creating graph image: " + cgmrrdgraphtemperaturefilenamefull)
                rrdtool.graph(os.path.join(wwwdir, cgmrrdgraphtemperaturefilenamefull), "-c", "BACK#FAF4F4", "-a", fileformatstr,
                              "-w", str(cgmrrdgraphw), "-h", str(cgmrrdgraphh), "-l", "60", "-u", "90", "-r",
                              "--disable-rrdtool-tag", "--border", "0", "--grid-dash", "1:0", "--start",
                              cgmrrdtimepostfix[timemarker], "--step", cgmrrdtimestep[timemarker], "--legend-position",
                              "north", "--vertical-label", "C", defstrings, averagestrings, maxstrings, linestrings)
        except:
            print("Cannot create graph image")

        colorindex = hostcolorindex

    # Generate RRD Hash Summary Graphs

    print("Summary_graph.")
    defstrings = []
    cdefstrings = []
    areastrings = []
    averagestrings = []
    gprintstrings = []
    totalstrings = "CDEF:Total=0"
    totalaveragestrings = "VDEF:Average=Total,AVERAGE"
    totalaveragelinestrings = "LINE1:Average" + cgmrrdaveragecolors[0]
    index = 0

    for host in cgmhosts['hosts']:
        cgmrrdhashratefilenamefull = str(cgmrrdhashratefilename + "_" + host['hostname'] + "_" + host['port'] + cgmrrddotrrd)
        indexforhostdata = 0

        if os.path.exists(cgmrrdhashratefilenamefull):
            try:
                cgmrrdhashratefileinfo = rrdtool.info(cgmrrdhashratefilenamefull)

                for x in [re.search(r'GPU([0-9]+)', x).group(1) for x in cgmrrdhashratefileinfo if x.startswith('ds') and x.endswith('.index')]:
                    indexstr = str(index)
                    indexforhostdatastr = str(indexforhostdata)
                    defstrings.append(str("DEF:G" + indexstr + "=" + cgmrrdhashratefilenamefull + ":GPU" + indexforhostdatastr + ":AVERAGE"))
                    cdefstrings.append(str("CDEF:GPU" + indexstr + "=G" + indexstr))
                    averagestrings.append(str("VDEF:avg" + indexstr + "=GPU" + indexstr + ",AVERAGE"))
                    areastrings.append(str("AREA:GPU" + indexstr + cgmrrdcolors[index] + ":GPU" + indexstr + ":STACK"))
                    areastrings.append(str("GPRINT:avg" + indexstr + ":%.0lf%s"))
                    totalstrings += ",GPU" + indexstr + ",+"
                    index += 1
                    indexforhostdata += 1
            except:
                print("Cannot get hash rate info for:", cgmrrdhashratefilenamefull)

    gprintstrings.append(str("GPRINT:Average:Average %.0lf%S\l"))

    try:
        for timemarker in cgmrrdtimepostfix:
            cgmrrdgraphhashfilenamefull = str(cgmrrdtotalgraphfilename + "_" + timemarker + cgmrrddotimage)
            if debugoutput:
                print("Creating graph image: " + cgmrrdgraphhashfilenamefull)
            rrdtool.graph(os.path.join(wwwdir, cgmrrdgraphhashfilenamefull), "-a", fileformatstr, "-w",
                          str(cgmrrdgraphw), "-h", str(cgmrrdgraphh * 2), "-l", "0", "--disable-rrdtool-tag",
                          "--border", "0", "--grid-dash", "1:0", "--start", cgmrrdtimepostfix[timemarker], "--step",
                          cgmrrdtimestep[timemarker], "--legend-position", "north", "--vertical-label", "Hashes/s",
                          defstrings, cdefstrings, averagestrings, areastrings, totalstrings, totalaveragestrings,
                          totalaveragelinestrings, gprintstrings)
    except:
        print("Cannot create graph image:", cgmrrdtotalgraphfilename)

    # Write data file with results

    # try:
    #     htmlfile = open(os.path.join(wwwdir, cgmresultsfilename), "w")
    #     json.dump(cgmhosts, htmlfile, cls=Encoder)
    #     htmlfile.close()
    # except:
    #     print("Cannot write to results file " + cgmresultsfilename)
    #     exit(1)

    # End.

    print("All done.")
=======
### CgminerRRD
### version Beta
### Created in 2013 by Arijan Siska
### this is free software, enjoy

import os.path
import pycgminer
import json
import HTMLgen
from time import localtime, strftime
import rrdtool

def cgmrrdgetdata():

### Get host configuration data from file

	cgmhostsfilename = "cgmhosts.json"

	try:
		file = open(cgmhostsfilename)
		cgmhosts = json.load(file)
		file.close()
	except:
		print "Cgminer hosts file ("+cgmhostsfilename+") format error or file missing!"
		exit(1)

	defaultport = "4028"
	faultyhostslist = []

### Get cgminer data for all hosts, dead hosts are erased from the list

	for host in cgmhosts["hosts"]:
 		try:
			host["port"]
		except:
			host["port"] = defaultport

		print "Getting data from: "+host["hostname"]+':'+host["port"]

		try:
			host["CgminerAPI"]=pycgminer.CgminerAPI(host["hostname"], int(host["port"]))
			host["Summary"]=host["CgminerAPI"].summary()
			host["Devs"]=host["CgminerAPI"].devs()
			host["Pools"]=host["CgminerAPI"].pools()
		except:
			print "Cannot connect API to", host["hostname"], host["port"]
			faultyhostslist.append(host)

	for faultyhost in faultyhostslist:
		for host in cgmhosts["hosts"]:
			if faultyhost["hostname"] == host["hostname"] and faultyhost["port"] == host["port"]:
				cgmhosts["hosts"].remove(host)
				break

	for host in cgmhosts["hosts"]:
		i = 0

		for device in host["Devs"]["DEVS"]:
			if device["MHS av"] > 0 :
				device["is hashing"] = True 
			else:
				print "Host "+host["hostname"]+":"+host["port"]+", device not working: GPU" + str(i)
				device["is hashing"] = False

			i += 1

#	print json.dumps(host["Summary"], indent=1)
#	print json.dumps(host["Devs"], indent=1)
#	print json.dumps(host["Pools"], indent=1)

	print "Alive Hosts: "+str(len(cgmhosts["hosts"]))

	for host in cgmhosts["hosts"]:
		print "    "+host["hostname"]+':'+host["port"]
		print "        Devices:"+str(len(host["Devs"]["DEVS"]))
		print "        Pools:"+str(len(host["Pools"]["POOLS"]))

	print "Dead Hosts: "+str(len(faultyhostslist))

	for host in faultyhostslist:
		print "    "+host["hostname"]+':'+host["port"]

### Generate HTML index file

	print "Generating main html."

	mainHTMLfilename = "index.html"
	cgmrrdtotalgraphfilename = "totalgraph"
	cgmrrdgraphw = 576
	cgmrrdgraphh = 150
	usesvg = 0

	if usesvg:
		fileformatstr = "SVG"
		cgmrrddotimage = ".svg"
	else:
		fileformatstr = "PNG"
		cgmrrddotimage = ".png"
		

	currentlocaltime = strftime("%s", localtime())
	currentlocaltimestring = strftime("%Y-%m-%d_%H:%M:%S", localtime())
	cgmrrdtimepostfix = { "1hourly":"end-12h", "2daily":"end-2d", "3weekly":"end-8d", "4monthly":"end-32d", "5yearly":"end-360d" }
#	cgmrrdtimepostfix = { "2daily":"end-2d", "3weekly":"end-8d", "4monthly":"end-4w" }

	htmldoc = HTMLgen.SimpleDocument(title="CgminerRRD")
	htmldoc.append(HTMLgen.Heading(1, "CgminerRRD (2013)"))
	htmldoc.append(HTMLgen.Paragraph("Reported at: "+currentlocaltimestring))

	for timemarker in sorted(cgmrrdtimepostfix):
		htmldoc.append(HTMLgen.Image(str(cgmrrdtotalgraphfilename+"_"+timemarker+cgmrrddotimage)))

	for host in cgmhosts["hosts"]:
		hostsummary = host["Summary"]["SUMMARY"][0]
		hoststatus = host["Summary"]["STATUS"][0]

		htmldoc.append(HTMLgen.Heading(2, "Host "+host["hostname"]+":"+host["port"]))

		for timemarker in sorted(cgmrrdtimepostfix):
			htmldoc.append(HTMLgen.Image(str("cgmhashrate_"+host["hostname"]+"_"+host["port"]+"_"+timemarker+cgmrrddotimage)))
			htmldoc.append(HTMLgen.Image(str("cgmtemperature_"+host["hostname"]+"_"+host["port"]+"_"+timemarker+cgmrrddotimage)))

		htmltable = HTMLgen.Table(border=0, width=0, cell_align="right", heading=[ "Hostname", "Port", "CGminer Ver", "Work Util", "Pool MHs", "Rejected Shares %", "Total MH", "Found Blocks", "Time" ] )
		htmltable.body = []
		htmltable.body.append( [ host["hostname"], host["port"], hoststatus["Description"], hostsummary["Work Utility"], round(float(hostsummary["Work Utility"]) * 0.001092283 * float(hostsummary["Difficulty Accepted"]) / ( 0.0001 + float(hostsummary["Difficulty Accepted"]) + float(hostsummary["Difficulty Rejected"]) ), 3), round( 100.0 * float(hostsummary["Difficulty Rejected"]) / ( 0.0001 + float(hostsummary["Difficulty Accepted"]) + float(hostsummary["Difficulty Rejected"]) ), 2), hostsummary["Total MH"], hostsummary["Found Blocks"], strftime("%a, %d %b %Y %H:%M:%S", localtime(hoststatus["When"] )) ] )
		htmldoc.append(htmltable)

		htmltable = HTMLgen.Table(border=0, width=0, cell_align='right', heading=[ "Status", "Activity %", "Intensity", "Temper. C", "Fan Speed", "Fan Percent", "GPU Clock", "Memory Clock", "Voltage", "MHS 5s", "MHS av", "Difficulty Accepted", "Difficulty Rejected", "Hardware Errors", "Rejected Shares %" ] )
		htmltable.body = []

		for device in host["Devs"]["DEVS"]:
			if device["is hashing"]:
				htmltable.body.append( [ device["Status"], device["GPU Activity"], device["Intensity"], device["Temperature"], device["Fan Speed"], device["Fan Percent"], device["GPU Clock"], device["Memory Clock"], device["GPU Voltage"], device["MHS 5s"], device["MHS av"], device["Difficulty Accepted"], device["Difficulty Rejected"], device["Hardware Errors"], round(device["Difficulty Rejected"] / ( 0.0001 + device["Difficulty Rejected"] + device["Difficulty Accepted"] ) * 100, 2 ) ] )

		htmldoc.append(htmltable)

		htmltable = HTMLgen.Table(border=0, width=0, cell_align='right', heading=[ "Pool", "Priority", "Status", "Difficulty Accepted", "Difficulty Rejected", "Rejected Shares %", "Difficulty Stale", "Remote Failures", "Best Share" ] )
		htmltable.body = []

		for pool in host["Pools"]["POOLS"]:
			htmltable.body.append( [ pool["URL"], pool["Priority"], pool["Status"], pool["Difficulty Accepted"], pool["Difficulty Rejected"], round(pool["Difficulty Rejected"] / ( 0.0001 + pool["Difficulty Rejected"] + pool["Difficulty Accepted"] ) * 100, 2 ), pool["Difficulty Stale"], pool["Remote Failures"], pool["Best Share"] ] )

		htmldoc.append(htmltable)

	try:
		htmlfile = open(cgmhosts["wwwdir"]+"/"+mainHTMLfilename, "w")
		htmlfile.write(str(htmldoc))
		htmlfile.close()
	except:
		print "Cannot open HTML file "+mainHTMLfilename+" for writing"
		exit(1)

#	try:
#		htmlfile = open(cgmhosts["wwwdir"]+"/"+mainHTMLfilename+"_"+currentlocaltimestring, "w")
#		htmlfile.write(str(htmldoc))
#		htmlfile.close()
#	except:
#		print "Cannot open HTML file "+mainHTMLfilename+" for writing"
#		exit(1)

### Update RRD Hash Database with data, if database does not exsist, create one

	cgmrrdhashratefilename = "cgmhashrate"
	cgmrrdtemperaturefilename = "cgmtemperature"
	cgmrrddotrrd = ".rrd"
	cgmrrdrradefs = ['RRA:AVERAGE:0.5:1:576', 'RRA:AVERAGE:0.5:4:576', 'RRA:AVERAGE:0.5:16:576', 'RRA:AVERAGE:0.5:180:576']
	cgmrrdcolors = [ "#000070", "#104090", "#1060A0", "#108060", "#20A040", "#30C020", "#40D010", "#A0D010", "#D8D800", "#D0A010", "#C06010", "#B03000", "#901000", "#A01050", "#701070", "#403040", "#606070", "#808090", "#A0A0B0", "#808080", "#909090", "#A0A0A0", "#B0B0B0", "#C0C0C0" ]
	cgmrrdaveragecolors = [ "#E02020" ]
	colorindex = 0

	for host in cgmhosts["hosts"]:
		cgmrrdhashratefilenamefull = str(cgmrrdhashratefilename+"_"+host["hostname"]+"_"+host["port"]+cgmrrddotrrd)
		cgmrrdtemperaturefilenamefull = str(cgmrrdtemperaturefilename+"_"+host["hostname"]+"_"+host["port"]+cgmrrddotrrd)
		hashratestring = currentlocaltime
		temperaturestring = currentlocaltime
		rrddatasource = [] 
		rrddatasourcegauge = [] 
		index = 0

		for device in host["Devs"]["DEVS"]:
			hashratestring += ":"+str(int(device["Difficulty Accepted"]))
			temperaturestring += ":"+str(device["Temperature"])
			rrddatasource.append("DS:GPU"+str(index)+":COUNTER:700:0:2000")
			rrddatasourcegauge.append("DS:GPU"+str(index)+":GAUGE:700:-100:150")
			index += 1

		print "Updating rrd file: "+cgmrrdhashratefilenamefull+","+cgmrrdtemperaturefilenamefull
		print "    Hashrate: "+hashratestring
		print "    Temperature: "+temperaturestring

		try:
			rrdtool.update(cgmrrdhashratefilenamefull, hashratestring)
		except:
			print "Cannot update rrd file: "+cgmrrdhashratefilenamefull+" with "+hashratestring
			
			if os.path.exists(cgmrrdhashratefilenamefull):
				print "Rrd file exsists. Something is wrong."
				exit(1)

			try:
				print "Creating rrd file: "+cgmrrdhashratefilenamefull
				rrdtool.create(cgmrrdhashratefilenamefull, "--start", currentlocaltime, rrddatasource + cgmrrdrradefs)
			except:
				print "Cannot create rrd file: "+cgmrrdhashratefilenamefull+":"+str(rrdtool.error())
				exit(1)

### Fetch RRD HashrateHistory

		print "Fetching rrd "+cgmrrdhashratefilenamefull+" for "+"now-2d"

		try:
			host["HashrateHistory"] = rrdtool.fetch(cgmrrdhashratefilenamefull, "AVERAGE", "-s", "now-2d")
		except:
			print "Cannot fetch history for "+cgmrrdhashratefilenamefull
			exit(1)

### Generate RRD Hash Graphs

		defstrings = []
		cdefstrings = []
		areastrings = []
		averagestrings = []
		gprintstrings = []
		totalstrings = "CDEF:Total=0"
		totalaveragestrings = "VDEF:Average=Total,AVERAGE"
		totalaveragelinestrings = "LINE1:Average" + cgmrrdaveragecolors[0]
		index = 0
		hostcolorindex = colorindex

		for device in host["Devs"]["DEVS"]:
			indexstr = str(index)
			if device["is hashing"]:
				defstrings.append(str("DEF:G"+indexstr+"="+cgmrrdhashratefilenamefull+":GPU"+indexstr+":AVERAGE"))
				cdefstrings.append(str("CDEF:GPU"+indexstr+"=G"+indexstr+",65536,*"))
				averagestrings.append(str("VDEF:avg"+indexstr+"=GPU"+indexstr+",AVERAGE"))
				areastrings.append(str("AREA:GPU"+indexstr+cgmrrdcolors[hostcolorindex]+":GPU"+indexstr+":STACK"))
				areastrings.append(str("GPRINT:avg"+indexstr+":%.0lf%s"))
				totalstrings += ",GPU"+indexstr+",+"
			index += 1
			hostcolorindex += 1

		gprintstrings.append(str("GPRINT:Average:Average %.0lf%S\l"))

		try:
			for timemarker in cgmrrdtimepostfix:
				cgmrrdgraphhashfilenamefull=str(cgmrrdhashratefilename+"_"+host["hostname"]+"_"+host["port"]+"_"+timemarker+cgmrrddotimage)
				print "Creating graph image: "+cgmrrdgraphhashfilenamefull
				rrdtool.graph(str(cgmhosts["wwwdir"]+"/"+cgmrrdgraphhashfilenamefull), "-a", fileformatstr, "-w", str(cgmrrdgraphw), "-h", str(cgmrrdgraphh), "-l", "0", "--start", cgmrrdtimepostfix[timemarker], "--legend-position", "north", "--vertical-label", "Hashes/s", defstrings, cdefstrings, averagestrings, areastrings, totalstrings, totalaveragestrings, totalaveragelinestrings, gprintstrings)
		except:
			print "Cannot create graph image: "+cgmrrdgraphhashfilenamefull

### Update RRD Temperature Database with data, if database does not exsist, create one

		try:
			rrdtool.update(cgmrrdtemperaturefilenamefull, temperaturestring)
		except:
			print "Cannot update rrd file: "+cgmrrdtemperaturefilenamefull+" with "+temperaturestring

			if os.path.exists(cgmrrdtemperaturefilenamefull):
				print "Rrd file exsists. Something is wrong."
                                exit(1)

			try:
				print "Creating rrd file: "+cgmrrdtemperaturefilenamefull
				rrdtool.create(cgmrrdtemperaturefilenamefull, "--start", currentlocaltime, rrddatasourcegauge + cgmrrdrradefs)
			except:
				print "Cannot create rrd file: "+cgmrrdtemperaturefilenamefull+":"+str(rrdtool.error())
				exit(1)

### Fetch RRD TemperatureHistory

		print "Fetching rrd "+cgmrrdhashratefilenamefull+" for "+"now-2d"

		try:
			host["TemperatureHistory"] = rrdtool.fetch(cgmrrdtemperaturefilenamefull, "AVERAGE", "-s", "now-2d")
		except:
			print "Cannot fetch history for "+cgmrrdtemperaturefilenamefull
			exit(1)

### Generate RRD Temperature Graphs

		defstrings = []
		linestrings = []
		averagestrings = []
		maxstrings = []
		index = 0
		hostcolorindex = colorindex

		for device in host["Devs"]["DEVS"]:
			indexstr = str(index)
			if device["is hashing"]:
				defstrings.append(str("DEF:GPU"+indexstr+"="+cgmrrdtemperaturefilenamefull+":GPU"+indexstr+":AVERAGE"))
				averagestrings.append(str("VDEF:avg"+indexstr+"=GPU"+indexstr+",AVERAGE"))
				maxstrings.append(str("VDEF:max"+indexstr+"=GPU"+indexstr+",MAXIMUM"))
				linestrings.append(str("LINE1:GPU"+indexstr+cgmrrdcolors[hostcolorindex]+":GPU"+indexstr))
                        	linestrings.append(str("GPRINT:avg"+indexstr+":Avg %.1lfC"))
	                        linestrings.append(str("GPRINT:max"+indexstr+":Max %.1lfC"))
			index += 1
			hostcolorindex += 1

		linestrings.append(str("COMMENT:\l"))

		colorindex = hostcolorindex

		try:
			for timemarker in cgmrrdtimepostfix:
				cgmrrdgraphtemperaturefilenamefull=str(cgmrrdtemperaturefilename+"_"+host["hostname"]+"_"+host["port"]+"_"+timemarker+cgmrrddotimage)
				print "Creating graph image: "+cgmrrdgraphtemperaturefilenamefull
				rrdtool.graph(str(cgmhosts["wwwdir"]+"/"+cgmrrdgraphtemperaturefilenamefull), "-a", fileformatstr, "-w", str(cgmrrdgraphw), "-h", str(cgmrrdgraphh), "-l", "60", "-u", "90", "-r", "--start", cgmrrdtimepostfix[timemarker], "--legend-position", "north", "--vertical-label", "C", defstrings, averagestrings, maxstrings, linestrings)
		except:
			print "Cannot create graph image: "+cgmrrdgraphtemperaturefilenamefull

### Generate RRD Hash Summary Graphs

	defstrings = []
	cdefstrings = []
	areastrings = []
	averagestrings = []
	gprintstrings = []
	totalstrings = "CDEF:Total=0"
	totalaveragestrings = "VDEF:Average=Total,AVERAGE"
	totalaveragelinestrings = "LINE1:Average" + cgmrrdaveragecolors[0]
	index = 0

	for host in cgmhosts["hosts"]:
		cgmrrdhashratefilenamefull = str(cgmrrdhashratefilename+"_"+host["hostname"]+"_"+host["port"]+cgmrrddotrrd)
		indexforhostdata = 0
		
		for device in host["Devs"]["DEVS"]:
			indexstr = str(index)
			indexforhostdatastr = str(indexforhostdata)
			if device["is hashing"]:
				defstrings.append(str("DEF:G"+indexstr+"="+cgmrrdhashratefilenamefull+":GPU"+indexforhostdatastr+":AVERAGE"))
				cdefstrings.append(str("CDEF:GPU"+indexstr+"=G"+indexstr+",65536,*"))
				averagestrings.append(str("VDEF:avg"+indexstr+"=GPU"+indexstr+",AVERAGE"))
				areastrings.append(str("AREA:GPU"+indexstr+cgmrrdcolors[index]+":GPU"+indexstr+":STACK"))
				areastrings.append(str("GPRINT:avg"+indexstr+":%.0lf%s"))
				totalstrings += ",GPU"+indexstr+",+"
				index += 1
			indexforhostdata += 1

	gprintstrings.append(str("GPRINT:Average:Average %.0lf%S\l"))

	try:
		for timemarker in cgmrrdtimepostfix:
			cgmrrdgraphhashfilenamefull=str(cgmrrdtotalgraphfilename+"_"+timemarker+cgmrrddotimage)
			print "Creating graph image: "+cgmrrdgraphhashfilenamefull
			rrdtool.graph(str(cgmhosts["wwwdir"]+"/"+cgmrrdgraphhashfilenamefull), "-a", fileformatstr, "-w", str(cgmrrdgraphw), "-h", str(cgmrrdgraphh * 2), "-l", "0", "--start", cgmrrdtimepostfix[timemarker], "--legend-position", "north", "--vertical-label", "Hashes/s", defstrings, cdefstrings, averagestrings, areastrings, totalstrings, totalaveragestrings, totalaveragelinestrings, gprintstrings)
	except:
		print "Cannot create graph image: "+cgmrrdgraphhashfilenamefull

### Write data file with results


	cgmresultsfilename = "cgmresults.json"

	class Encoder(json.JSONEncoder):
		def default(self, o):
			return o.__dict__

	try:
		file = open(str(cgmhosts["wwwdir"]+"/"+cgmresultsfilename), "w")
		json.dump(cgmhosts, file, cls=Encoder)
		file.close()
	except:
		print "Cannot write to results file "+cgmresultsfilename
		exit(1)


### End.

	print "Done."
>>>>>>> dd1802420fcf302cbb78773e06b05709b0a52a26
