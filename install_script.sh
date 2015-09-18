#!/bin/sh

# make sure with DIR has trailing '/' and not at beginning
CGMRRDDIR=cgmrrdV2/

# these are standard and they need a '/' at the beginning as they are planted in root
WWWDIR=/var/www/
WWWCGIDIR=/usr/lib/cgi-bin/

# code
user=$( who am i | cut -d' ' -f1 )
if test -d $WWWDIR$CGMRRDDIR
then
	echo $WWWDIR$CGMRRDDIR" exists."
else
	echo "Creating "$WWWDIR$CGMRRDDIR
	mkdir $WWWDIR$CGMRRDDIR
	chown $user:$user $WWWDIR$CGMRRDDIR
	chmod g+w $WWWDIR$CGMRRDDIR
	chmod o+w $WWWDIR$CGMRRDDIR
fi
echo "Link files to: "$WWWDIR$CGMRRDDIR
filelist="LICENCE.txt index.html cgmrrdmenu.css conf.svg dash.svg data.svg graph.svg host.svg paragraph.svg cgmdash.css cgmrrd.css cgmrrdreport.css editconf.html edithosts.html jsoneditor.min.css jsoneditor.min.js jsoneditor-icons.png"
for file in $filelist
do
	if test -s $WWWDIR$CGMRRDDIR$file
	then
		rm $WWWDIR$CGMRRDDIR$file
	fi
	ln $file $WWWDIR$CGMRRDDIR$file
done
if test -d $WWWCGIDIR$CGMRRDDIR
then
        echo $WWWCGIDIR$CGMRRDDIR" exists."
else
        echo "Creating "$WWWCGIDIR$CGMRRDDIR
        mkdir $WWWCGIDIR$CGMRRDDIR
	chown $user:$user $WWWCGIDIR$CGMRRDDIR
	chmod g+w $WWWCGIDIR$CGMRRDDIR
	chmod o+w $WWWCGIDIR$CGMRRDDIR
fi
echo "Link files to: "$WWWCGIDIR$CGMRRDDIR
filelist="cgmhosts.json cgminer.conf getconf.py gethosts.py markup.py putconf.py puthosts.py"
for file in $filelist
do
        if test -s $WWWCGIDIR$CGMRRDDIR$file
        then
                rm $WWWCGIDIR$CGMRRDDIR$file
        fi
        ln $file $WWWCGIDIR$CGMRRDDIR$file
done

