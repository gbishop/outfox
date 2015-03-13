TODO: in progress

# services.xml #

  * Open `ext/platform/services.xml`.
  * Locate the placeholder ` <service id="joystick"> ` tag and its descendants.
  * We will build the echo extension in Python so we can use the existing ` outfox.py ` to launch it. The first ` <executable> ` tag is fine as it is. Note that we could specify any executable here which takes at least one parameter when launched by the browser exception: the port number on localhost the service executable should connect to to communicate with the browser extension.
  * Change ` <arg> ` tag value to `echo` under the first ` <executable> ` tag. This value is passed to the executable when the browser extension launches it. We could define more arguments, but we only need the one: the name of the module we want ` outfox.py ` to import for this service.
  * Notice there is a second executable listed. This is a py2exe version of the regular ` outfox.py ` script built for Windows. The browser extension attempts to launch the executables in the order given in the file until one succeeds.
  * Change all the ` joystick ` references to ` echo ` for the second executable.
