import time
import pythoncom
import threading
from win32com.client import WithEvents, Dispatch, constants
from win32com.client import gencache
gencache.EnsureModule('{C866CA3A-32F7-11D2-9602-00C04F8EE628}', 0, 5, 0)

class Speaker(threading.Thread):
    def __init__(self, text):
        super(Speaker, self).__init__()
        self.text = text

    def run(self):
        pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
        tts = Dispatch('SAPI.SpVoice')
        tts.Speak(self.text)

s1 = Speaker('this is a test')
s2 = Speaker('this is another')
s1.start()
s2.start()
time.sleep(3)
