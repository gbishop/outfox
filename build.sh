#!/bin/bash
# remove old extension build and staging area
rm outfox.xpi
rm -rf build
# create staging area
cp -r ext build
# clean out win32 build area
rm -rf build/platform/ext/build
# remove all svn cruft
find build | grep .svn$ | while read i
do
  rm -rf $i
done
# zip it up
zip -r outfox.xpi build/* -x@exclude.lst
