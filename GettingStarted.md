# What is Outfox? #

Outfox is a Firefox extension that web pages can use to speak text, play sound, use gamepads, recognize speech, and so on. When you have Outfox installed, a web page can choose to do more than draw on the screen and listen to the mouse and keyboard.

On its own, Outfox does nothing. You have to visit a web page or site that makes use of Outfox for speech, sound, input devices, speech recognition, or other services.

# Installing Outfox #

Locate your platform in the sections below. Follow the instructions for your platform to install Outfox the first time.

## Windows ##

  1. Visit this http://cs.unc.edu/Research/assist/outfox/xpi/outfox.xpi Outfox download link] to get the latest version.
  1. If a popup appears at the top of your browser, click _Allow_.
  1. Read the dialog that appears.
  1. When the _Install Now_ button lights up, click it to install Outfox.
  1. Wait for the download to complete.
  1. Click the _Restart Firefox_ button in the yellow information bar.
  1. If a Windows firewall dialog appears, click _Keep Blocking_ to prevent remote connections to Outfox.
  1. When Firefox restarts, confirm that Outfox is listed in the _Add-ons_ dialog.
  1. Close the _Add-ons_ dialog.
  1. Visit the Outfox sample page at http://www.cs.unc.edu/Research/assist/outfox/app/test/samples/.
  1. Click the link for the audio examples.
  1. A dialog appears asking if the web page can access Outfox. Click _Allow_.
    1. For other web sites, you should consider if you trust the site or not before allowing it access to Outfox.
    1. You can tick the _Remember_ check box to have Outfox remember your decision to allow or deny access for your future visits to the site.
    1. You can change your permanent access decisions in the Outfox options dialog by selecting _Tools_ -> _Add-ons_ and then clicking the _Preferences_ button in the Outfox row.
  1. If Outfox is working properly, the _Run_ buttons should light up and no error message should appear at the top of the page.
  1. Click the _Run_ buttons, one at a time, to test speech and sound output.

Firefox will automatically notify you when new versions of Outfox are available. See the help below for assistance in upgrading.

## Mac OS X ##

  1. Visit this http://cs.unc.edu/Research/assist/outfox/xpi/outfox.xpi Outfox download link] to get the latest version.
  1. If a popup appears at the top of your browser, click _Allow_.
  1. Read the dialog that appears.
  1. When the _Install Now_ button lights up, click it to install Outfox.
  1. Wait for the download to complete.
  1. Click the _Restart Firefox_ button in the yellow information bar.
  1. If a Mac firewall dialog appears, click _Deny_ to prevent remote connections to Outfox.
  1. When Firefox restarts, confirm that Outfox is listed in the _Add-ons_ dialog.
  1. Close the _Add-ons_ dialog.
  1. Visit the Outfox sample page at http://www.cs.unc.edu/Research/assist/outfox/app/test/samples/.
  1. Click the link for the audio examples.
  1. A dialog appears asking if the web page can access Outfox. Click _Allow_.
    1. For other web sites, you should consider if you trust the site or not before allowing it access to Outfox.
    1. You can tick the _Remember_ check box to have Outfox remember your decision to allow or deny access for your future visits to the site.
    1. You can change your permanent access decisions in the Outfox options dialog by selecting _Tools_ -> _Add-ons_ and then clicking the _Preferences_ button in the Outfox row.
  1. If Outfox is working properly, the _Run_ buttons should light up and no error message should appear at the top of the page.
  1. Click the _Run_ buttons, one at a time, to test speech and sound output.

Firefox will automatically notify you when new versions of Outfox are available. See the help below for assistance in upgrading.

## Linux ##

You are required to manually install Outfox prerequisites on Linux. Instructions for configuring common Linux distributions are given below. Even if your distro is not listed, you can still run Outfox as long as you can satisfy all of the prerequisites. If you succeed, please post the instructions for your distro to the [outfox-discuss](http://groups.google.com/group/outfox-discuss) Google Group so we can include them here.

### Ubuntu Intrepid Ibex (Desktop Edition 8.10) ###

  1. Visit this http://cs.unc.edu/Research/assist/outfox/xpi/outfox.xpi Outfox download link] to get the latest version.
  1. If a popup appears at the top of your browser, click _Allow_.
  1. Click the _Add to Firefox_ button.
  1. Read the dialog that appears.
  1. When the _Install Now_ button lights up, click it to install Outfox.
  1. Wait for the download to complete.
  1. Click the _Restart Firefox_ button in the yellow information bar.
  1. When Firefox restarts, confirm that Outfox is listed in the _Add-ons_ dialog.
  1. Close the _Add-ons_ dialog.
  1. Visit the Outfox sample page at http://www.cs.unc.edu/Research/assist/outfox/app/test/samples/.
  1. Click the link for the audio examples.
  1. A dialog appears asking if the web page can access Outfox. Click _Allow_.
    1. For other web sites, you should consider if you trust the site or not before allowing it access to Outfox.
    1. You can tick the _Remember_ check box to have Outfox remember your decision to allow or deny access for your future visits to the site.
    1. You can change your permanent access decisions in the Outfox options dialog by selecting _Tools_ -> _Add-ons_ and then clicking the _Preferences_ button in the Outfox row.
  1. If Outfox is working properly, the _Run_ buttons should light up and no error message should appear at the top of the page.
  1. Click the _Run_ buttons, one at a time, to test speech and sound output.

Firefox will automatically notify you when new versions of Outfox are available. See the help below for assistance in upgrading.

Firefox will automatically notify you when new versions of Outfox are available. See the help below for assistance in upgrading.

# Upgrading Outfox #

If Firefox notifies you that a new version of Outfox is available, do the following to upgrade.

  1. Open the _Add-ons_ dialog. (Firefox may open it for you.)
  1. Click the row containing the word _Outfox_.
  1. Click the _Install_ button in that row.
  1. Click the _Restart_ button that appears.

When Firefox restarts, you will be using the newest version of Outfox.

# Using Outfox in JavaScript #

Outfox services are controlled by web page JavaScript. If you are a web developer and want to make use of Outfox in you wep app or site, follow the instructions below to get started.

  1. Visit the _Download_ tab of this site.
  1. Download the latest _outfox.js_ file.
  1. Put the _.js_ file on your web server.
  1. Include the _.js_ file in every document that will access Outfox services.
    1. `<script type="text/javascript" src="outfox.js"></script>`
  1. Use the JS client API to access Outfox.

For more information on writing web applications that use Outfox, see the [DeveloperTutorial](DeveloperTutorial.md) page.