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
