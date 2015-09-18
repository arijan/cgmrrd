# coding=utf-8
### CgmRRD Def parameters
### version 2
### Created in 2014 by Arijan Siska

cgmhostsfilename = "cgmhosts.json"
defaultport = "4028"

numberofIOthreads = 16

wwwdir = "/var/www/cgmrrdV2"
mainHTMLfilename = "cgmrrd.html"
mainCSSfilename = "cgmrrd.css"
reportHTMLfilename = "report.html"
reportCSSfilename = "cgmrrdreport.css"
dashHTMLfilename = "cgmdash.html"
dashCSSfilename = "cgmdash.css"
dashhwerrhigh = 0
dashrejecthigh = 5.0
dashtemphigh = 80.0
cgmrrdtotalgraphfilename = "totalgraph"
cgmrrdgraphw = 576
cgmrrdgraphh = 120
usesvg = False # use SVG fileformat or PNG fileformat

if usesvg:
    fileformatstr = "SVG"
    cgmrrddotimage = ".svg"
else:
    fileformatstr = "PNG"
    cgmrrddotimage = ".png"

cgmrrdstep = 600 # seconds
cgmrrdtimepostfix = {"2daily": "end-6d", "5yearly": "end-144d"}
cgmrrdtimestep = {"2daily": "3600s", "5yearly": "1d"}
cgmhashesperdiff1share = 65536 * 65536  # for Bitcoin, X11 etc., for some coins this should be 65536 or 2^16

cgmrrdhashratefilename = "cgmhashrate"
cgmrrdtemperaturefilename = "cgmtemperature"
cgmrrddotrrd = ".rrd"
cgmrrdrradefs = ['RRA:AVERAGE:0.5:' + str(3600 / cgmrrdstep) + ':576', 'RRA:AVERAGE:0.5:' + str(24 * 3600 / cgmrrdstep) + ':576']
#cgmrrdcolors = ["#000070", "#104090", "#1060A0", "#108060", "#20A040", "#30C020", "#40D010", "#A0D010", "#D8D800",
#                "#D0A010", "#C06010", "#B03000", "#901000", "#A01050", "#701070", "#403040", "#606070", "#808090",
#                "#A0A0B0", "#808080"]
#cgmrrdcolors = [ "#0000FF", "#00FFFF", "#00FF00", "#FFFF00", "#FF0000", "#FF00FF" ]
cgmrrdcolors = [ "#0035F9", "#1E798E", "#46A228", "#9EBC17", "#F0CB24", "#FE9B18", "#FB5D0E", "#FF5E70", "#FD92FA" ]
#cgmrrdcolors = [ "#0000FF", "#00A9FF", "#00FFFF", "#00FF00", "#BEFF00", "#FFFF00", "#FFAA00", "#FF5500", "#FF0000" ]

cgmrrdaveragecolors = ["#E02020"]

cgmresultsfilename = "cgmresults.json"

debugoutput = False
