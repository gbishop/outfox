#!/bin/bash
# get the version number
VERSION=`grep em:version ext/install.rdf | tr -d ' ' | sed 's/^em:version="\(.*\)"$/\1/'`
# remove old extension build and staging area
rm outfox*.xpi
rm -rf build
# create staging area
cp -r ext build
# copy win32 fmod into dist directory
cp build/platform/win32/audio/fmodex.dll build/platform/dist/
# clean out win32 source and build areas
rm -rf build/platform/build
rm -rf build/platform/win32
# remove all svn, pyc, and mac cruft
find build | grep .svn$ | while read i
do
  rm -rf $i
done
find build | grep .pyc$ | while read i
do
  rm -rf $i
done
find build | grep .DS_Store | while read i
do
  rm -rf $i
done
# zip it up
cd build
zip -r ../outfox-$VERSION.xpi * -x@../exclude.lst
# clean up build
cd ..
rm -rf build