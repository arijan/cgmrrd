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
- no dynamic charting at this point in time I'm affraid
- probably there are a few bugs out there so please let me know if you find any. My regular email address is arijan at gmail ok?
- API calls are not asynchronous
- did not polish html styling
- not "autorefresh" of the web page yet

This script uses CGminerAPI developed by Thomas Sileo: http://thomassileo.com/blog/2013/09/17/playing-with-python-and-cgminer-rpc-api/

Please use it, it is a free software, comment, and of course if you feel like it tip me at: LTC LTyruxjwcKdqcEWiaArEYFWe6TKNs341Us or:  BTC 182boxM3bJxsokcdAtXwVJejCpzL1MAvYq

Installation:
1. Create Virtual Machine or use real machine (I'm using an old Atom based laptop)
- 512 MB RAM (could be 256), 1 CPU, 8 GB SATA disk, 8 MB Video RAM

2. Install Ubuntu server
- hostname cgmrrd
- timezone
- keyboard & language
- disk partition: 1GB swap + 7GB root partition
- username  password
- no automatic updates
- software selection: OpenSSH + LAMP server (mysql root password administrator)
- note that mysql and php are not used only plain vanilla Apache server or any other web server.


3. Install needed software: apt-get install ntp rrdtools python-rrd python-htmlgen

- ntp (edit /etc/ntp.conf if necessary, check with 'ntpq -p')
- rrdtools
- python-rrd
- python-htmlgen

4. Copy python script files I supplied in your directory of choice. These are main.py, cgmrrd.py pycgminer.py (from Thomas Sileo), cgmhosts.json

5. Edit your cgmhosts.json file to add your hosts as needed. Make sure you follow the json syntax and if you use hostnames instead of ip numbers that these hosts are indeed reachable. Port number can be specified, however it is 4028 by default. Also make sure your cgminers are started with appropriate options to enable API access. At minimum this is --api-listen and --api-allow NETWORK (where NETWORK is your network from where you will allow access. I use 192.168.0.0/16)

6. Create web directory you specified in cgmrrd.conf file, it is /var/www/cgmrrd by default. Make sure it is writable by you

7. running script file: main.py will read data from all your hosts, display it as index.html file in your web directory, store hash and temperature data in .rrd files in the same directory with the script and will also create .png graph files in your web directory, so opening it with a browser should show your statistics and graphs.

8. run main.py periodically every 5 minutes either with cron or watch. I use 'watch -n 300 main.py' in a byobu session so that my terminal needs not to be open all the time.

9. point your browser to your laptop and web page with graphs and statistics should appear. I use http://nb250/cgmrrs

