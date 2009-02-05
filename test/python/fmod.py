import sys
sys.path.insert(0, '../../ext/platform/')
import osx.audio
from PyObjCTools import AppHelper

class Debug(object):
    def __init__(self, page):
        self.cmds = [
            0.0, {'action' : 'start-service', 'name' : 'audio'},
            #0.0, {'channel' : 0, 'action': 'say', 'text' : 'This is a test.', 'name' : 'first'},
            #0.25, {'channel' : 0, 'action': 'stop'},
            #0.0, {'channel' : 0, 'action': 'say', 'text' : 'This is another utterance.', 'name' : 'second'},
            0.0, {'channel' : 0, 'action': 'play', 'url' : u'../../js/sounds/SignOff.mp3', 'name' : 'third'},
            #0.25, {'channel' : 1, 'action': 'play', 'url' : '../../js/sounds/SignOn.mp3', 'name' : 'fourth'},
            #0.5, {'channel' : 0, 'action': 'stop'},
            #1.0, {'channel' : 0, 'action': 'play', 'url' : 'http://www.cs.unc.edu/Research/assist/outfox/0.2.0/sounds/FileRequest.mp3'},
            10.0
        ]
        self.page = page
        #self.onTimer()
            
    def pushRequest(self, cmd):
        print cmd
        self.onTimer()
    
    def pushResponse(self, id, cmd):
        if cmd['action'] != 'started-service':
            print id, cmd
        
    def onTimer(self):
        try:
            cmd = self.cmds.pop(0)
        except IndexError:
            osx.audio.shutdown(osx.audio)
            return
        if type(cmd) == float:
            AppHelper.callLater(cmd, self.onTimer)
        else:
            print 'push request', cmd
            self.page.pushRequest(cmd)
            self.onTimer()

page = osx.audio.buildPage(osx.audio, 0)
server = osx.audio.buildServer(osx.audio, 20512)
d = Debug(page)
server.setObserver(d)
server.doConnect()
page.setObserver(d)
osx.audio.run(osx.audio)
