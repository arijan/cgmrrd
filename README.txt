1. Create Virtual Machine
- 512 MB RAM (could be 256), 1 CPU, 8 GB SATA disk, 8 MB Video RAM

2. Install Ubuntu server
- hostname cgmrrd
- timezone - UTC is suggested
- keyboard & language
- disk partition: 1GB swap + 7GB root partition
- username  password 
- no automatic updates
- software selection: OpenSSH + LAMP serveri
- if however mysql is not required by other software, you can just install
'sudo apt-get install lighttpd'. Lighttpd uses slightly different directory for
www files, so you will have to change it or make changes in your config as per 6.
Also in Ubunu/Debian lighttp setup has a bug and you need to add 'alias.url =
( "/cgi-bin/" => "/usr/lib/cgi-bin/" )' just below the 'server.modules' line
in '/etc/lighttpd/conf-enabled/10-cgi.conf'. Also you need to enable cgi-bin
module by running 'sudo lighttpd-enable-mod'.


3. Install needed software: 'sudo apt-get install ntp rrdtools, python-rrdtool'

- ntp (edit /etc/ntp.conf if necessary, check with 'ntpq -p')
- rrdtools
- python-rrdtool

4. Clone Github CgmRRD repository in a directory of your choice

5. Edit your cgmhosts.json file to add your hosts as needed

6. edit install_script.sh's first couple of lines where directory enries for
www and cgi-bin files are specified. Default should be fine, change if
necessary. If you do, then make appropriate change to cgmdefaults.py file line
11. This should be the same directory where you will have other www files.
Again, default is fine.

7. run install_script.sh 'sudo sh install_script.sh'. It will link some of the
filed in cgmrrdV2 directiory to wherever your www and your cgi-bin files are.

8. running script file: 'python main.py' will read data from all your hosts, display it
as index.html file in your web directory, store hash and temperature data in .rrd
files in the same directory with the script and will also create .png graph files in
your web directory, so opening it with a browser should show your statistics and graphs.

9. opening your web browser to http:your_server/cgmrrdV2 will show you main
menu, main options are: Dashboard, Current Status Report and Historical Share
Report.

10. run main.py periodically every 5 minutes either with cron or watch to
update Dashboard and current Status report as well as record all the data in
RRD files.

11. running cgmreport.py every 12 hours or so will update 'historical share
report' spreadsheet, which you can access through cgmrrdV2 main menu.
