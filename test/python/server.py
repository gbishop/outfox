'''
Asynchat socket server.
'''
import threading
import asynchat
import asyncore
import socket

DELIMITER = '\3'

class Handler(asynchat.async_chat):
    def __init__(self, conn, addr):
        asynchat.async_chat.__init__(self, conn)
        self.addr = addr
        self.in_buff = []
        self.set_terminator(DELIMITER)
        self.doCommand('{"action" : "get-config"}')

    def doCommand(self, text):
        self.sendMessage('{"page_id" : 0, "cmd" : %s}' % text)

    def sendMessage(self, msg):
        # add delimiter to message
        self.push(msg+DELIMITER)
        print 'sent message'

    def collect_incoming_data(self, data):
        self.in_buff.append(data)
        print 'collected incoming'

    def found_terminator(self):
        msg = ''.join(self.in_buff)
        self.in_buff = []
        print msg

class TestServer(asyncore.dispatcher):
    def __init__(self, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(('127.0.0.1', port))
        self.listen(5)
        self.hand = None

    def close(self):
        asyncore.dispatcher.close(self)
        if self.hand:
            self.hand.close()

    def handle_close(self):
        if self.hand:
            self.hand.close()
        
    def handle_accept(self):
        try:
            conn, addr = self.accept()
        except socket.error:
            return
        except TypeError:
            return
        print 'accepted'
        self.hand = Handler(conn, addr)

s = TestServer(20512)
t = threading.Thread(target=asyncore.loop, args=[2])
t.start()

def test2():
    s.hand.doCommand('{"action" : "say", "text" : "hello out there", "channel" : 0}')
    s.hand.doCommand('{"action" : "say", "text" : "i am sam", "channel" : 1}')

def testQ():
    s.hand.doCommand('{"action" : "say", "text" : "hello out there"}')
    s.hand.doCommand('{"action" : "say", "text" : "i am sam"}')

def testP(v=0.5,r=100):
    s.hand.doCommand('{"action" : "set-queued", "name" : "rate", "value" : %d}' % r)

    s.hand.doCommand('{"action" : "set-queued", "name" : "volume", "value" : %f}' % v)
    s.hand.doCommand('{"action" : "say", "text" : "hello out there"}')

    s.hand.doCommand('{"action" : "set-queued", "name" : "rate", "value" : %d}' % (r*2))

    s.hand.doCommand('{"action" : "set-queued", "name" : "volume", "value" : %f}' % (v*2))
    s.hand.doCommand('{"action" : "say", "text" : "hello out there again"}')

