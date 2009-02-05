import sys
sys.path.insert(0, '../../ext/platform/')
import nix.audio as audio
import threading
import Queue

class Debug(object):
    def __init__(self, page):
        self.cmds = [
            0.0, {'action' : 'start-service'},
            0.0, {'channel' : 0, 'action': 'say', 'text' : 'This is a test.', 'name' : 'first'},
            0.25, {'channel' : 0, 'action': 'stop'},
            0.0, {'channel' : 0, 'action': 'say', 'text' : 'This is another utterance.', 'name' : 'second'},
            0.0, {'channel' : 0, 'action': 'play', 'url' : '../../js/sounds/SignOff.mp3', 'name' : 'third'},
            0.25, {'channel' : 1, 'action': 'play', 'url' : '../../js/sounds/SignOn.mp3', 'name' : 'fourth'},
            0.5, {'channel' : 0, 'action': 'stop'},
            1.0, {'channel' : 0, 'action': 'play', 'url' : 'http://www.cs.unc.edu/Research/assist/outfox/0.2.0/sounds/FileRequest.mp3'},
            4.0
        ]
        self.page = page
        self.waiting = Queue.Queue()
        self.timer = None
        self.onTimer()

    def _newTimer(self, delay):
        self.timer = threading.Timer(delay, self.onTimer)
        self.timer.start()
    
    def pushResponse(self, id, cmd):
        if cmd['action'] != 'started-service':
            print id, cmd
        
    def onTimer(self):
        try:
            cmd = self.cmds.pop(0)
        except IndexError:
            audio.shutdown(audio)
            return
        if type(cmd) == float:
            self._newTimer(cmd)
        else:
            self.waiting.put(cmd)
            self.onTimer()
    
    def next(self):
        try:
            cmd = self.waiting.get(False)
        except Exception, e:
            return
        self.page.pushRequest(cmd)


page = audio.buildPage(audio, 0)
debug = Debug(page)
page.setObserver(debug)
audio.run(audio, debug.next)
