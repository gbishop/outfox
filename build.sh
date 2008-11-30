#!/bin/bash
# get the version number
VERSION=`grep em:version ext/install.rdf | tr -d ' ' | sed 's/^<.*>\([^<].*\)<.*>$/\1/'`
# remove old extension build and staging area
rm outfox*.xpi
rm -rf build
# create staging area
cp -r ext build
# clean out win32 build area
rm -rf build/platform/build
# remove all svn cruft
find build | grep .svn$ | while read i
do
  rm -rf $i
done
find build | grep .pyc$ | while read i
do
  rm -rf $i
done
# zip it up
cd build
zip -r ../outfox-$VERSION.xpi * -x@../exclude.lst
