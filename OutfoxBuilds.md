Outfox builds are most easily performed on a OS X or Linux machine running a Windows virtual machine. The following instructions are written assuming this setup, with both the host OS and the Windows VM having read/write access to an Outfox source sandbox.

  1. Place the FMOD dynamic libraries in the appropriate platform folders under _ext/platforms_.
  1. Update the version number in _ext/platforms/setup.py_.
  1. Do a py2exe build of the Windows platform files using the _ext/platforms/setup.py_ script in the VM.
  1. Update the version number in _ext/install.rdf_.
  1. Update the version number in _ext/content/overlay.js_.
  1. Run the _build.sh_ script in the host OS. It will get the version number from the _install.rdf_ file.
  1. Get the sha1 hash value of the built file using _openssl sha1 outfox-VERSION.xpi_.
  1. Add a new section about the version in _update.rdf_ including the hash. (Just duplicate and change one that's already in there.)
  1. Commit to svn the changes to _update.rdf_.
  1. Use the _ccat@unc.edu_ key-pair in McCoy to sign the _update.rdf_ file. **DO NOT commit the munged file to svn!**

After building, follow these directions to do a release:

  1. Upload the _.xpi_ file to http://www.cs.unc.edu/Research/assist/outfox/xpi/.
    1. Update the _outfox.xpi_ symlink in that folder to point to the newest version.
  1. Upload the current sample and test pages to http://www.cs.unc.edu/Research/assist/outfox/app/.
    1. Only do this step if the samples and/or tests have changed.
    1. Include _js/_ and _test/samples_ from svn.
  1. Upload the McCoy signed _update.rdf_ file to http://www.cs.unc.edu/Research/assist/outfox/update.rdf.
  1. Post a new version of _outfox.js_ in the download section of the Google Code site.
    1. Only do this if there were changes to _outfox.js_, namely if this is a major or minor release (major.minor.revision).
    1. Be sure to upload it with a filename matching _outfox-VERSION.js_ because that's how it will appear in the download section. In other words, copy _outfox.js_ in your svn sandbox to _outfox-VERSION.js_ and then upload the copy.

Now update the Google Code site for the latest release files:

  1. Deprecate the old _outfox.js_ file on Downloads.
  1. Feature the new _outfox.js_ on Downloads.
  1. Edit ReleaseNotes with information about the issues fixed in this release.

Finally, toss a post in the Google Group about the release, perhaps with the same version info in ReleaseNotes.