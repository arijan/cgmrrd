cgmrrd
======

Use rrdtools to chart cgminer performance

Motivation:
Probably the only notable difference between this one and all other software out there is that:
- it is utterly small python script that you can probably run from just about anything
- it charts what I believe IMHO to be relevant data. So rather than charting so called average hash rate which is telling you nothing further down the line you go as it is the all time average, it polls number of diff1 submitted shares and calculates hash rate from that. Submitted shares are relevant to you as this is what pool is paying, also you can see if there are any daily variations in the pool performance etc. As it makes no sense to poll less than every 5 minutes (any decent pool will diffserv you so that you don't get to submit many shares per minute) chart is slow to appear (you need at least 30 min of data), and has a lot of jitter. But weekly and monthly averages should look smooth.
- It also charts temperature of course
- please let me know if you feel something should be added...

Shortcommings:
- it uses rrd with all quirks of that software
- no dynamic charting at this point in time
- probably there are a few bugs out there so please let me know if you find any. My regular email address is arijan at gmail ok?

This script uses CGminerAPI developed by Thomas Sileo: http://thomassileo.com/blog/2013/09/17/playing-with-python-and-cgminer-rpc-api/

It also uses 'public domain' script 'markup.py' v 1.9 by Roel Mathys, Brian Blais, Davide Cesari, Carsten Bock, Fred Gansevles, Thorsten Kampe, Jason Moiron, Jerry Davis, Morten Kjeldgaard. Please see http://markup.sourceforge.net.

Also 'jsoneditor.min.js' v3.1.2 by  Jos de Jong is used.

Please use it, it is a free software, comment, and of course if you feel like it tip me at: LTC LTyruxjwcKdqcEWiaArEYFWe6TKNs341Us or:  BTC 182boxM3bJxsokcdAtXwVJejCpzL1MAvYq

Lastly please read the README.txt for installation information.
