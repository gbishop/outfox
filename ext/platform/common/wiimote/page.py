'''
Controller for a single page using the wiimote service.

Copyright (c) 2008, 2009 Carolina Computer Assistive Technology

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
'''
import os
import jsext
import Wii
import time

import sys

print 'in wiimote page.py'

from ..page import BasePageController
                
class WiimoteDriver(object):
    def __init__(self, addr):
        self.addr = addr

        self.pages = [] # pages monitoring events from this wiimote

        self.prev_buttons = set()

        self.report_period = 0.05

        self.wiimote = Wii.wiimoteLibClass(self.addr)
        #self.wiimote.setContinuous(True)
        self.last_post_time = 0

        self.want_accel_reports = 0

    def step(self):
        self.wiimote.step()
        t = time.time()

        curr_buttons = self.wiimote.getPressedButtons()
        new_buttons = curr_buttons - self.prev_buttons
        for button in new_buttons:
            self.postEvent('button-press', t=t, id=self.addr, button=button)
        self.prev_buttons = curr_buttons

        if self.wiimote.wiiMoteState.SEND_ACCEL:
            now = time.time()
            if now - self.last_post_time > self.report_period:
                self.last_post_time = now
                wacc = self.wiimote.wiiMoteState.Accel
                if self.wiimote.hasNunchuck():
                    nacc = self.wiimote.extensionState.Accel
                else:
                    nacc = []
                self.postEvent('accel-report', t=t, id=self.addr, accel=wacc,
                               nunchuck_accel=nacc)

    def addPage(self, page):
        if page not in self.pages:
            self.pages.append(page)

    def removePage(self, page):
        if page in self.pages:
            self.pages.remove(page)

    def postEvent(self, event, **values):
        #print 'post', event, values, self.queues.keys()
        for page in self.pages:
            page.postEvent(event, **values)

    def enableAccel(self, on):
        if on:
            self.want_accel_reports += 1
        else:
            self.want_accel_reports -= 1

        self.wiimote.setAccel(self.want_accel_reports > 0)

    def setReportPeriod(self, period):
        self.report_period = period
        

class WiiManager(object):
    def __init__(self):
        self.drivers = {}
        self.motesFound = []

    def pageConnect(self, page, address):
        if address in self.drivers:
            driver = self.drivers[address]
            if page not in driver.pages:
                driver.addPage(page)
                return address
            return None
        elif address == 'any':
            for address, driver in self.drivers.iteritems():
                if page not in driver.pages:
                    driver.addPage(page)
                    return address
            else: # we need to find a new one
                while self.motesFound:
                    address = self.motesFound.pop()
                    if address not in self.drivers:
                        return self.driverConnect(address, page)
                    
                self.motesFound = Wii.findWiimotes(2)
                while self.motesFound:
                    address = self.motesFound.pop()
                    if address not in self.drivers:
                        return self.driverConnect(address, page)
                return None
        else:
            return self.driverConnect(address, page)

    def driverConnect(self, address, page):
        try:
            driver = WiimoteDriver(address)
        except:
            return None
        self.drivers[address] = driver
        driver.addPage(page)
        return address

    def step(self):
        for driver in self.drivers.itervalues():
            driver.step()

    def removePage(self, page):
        for driver in self.drivers.itervalues():
            driver.removePage(page)

    def enableAccel(self, address, state):
        self.drivers[address].enableAccel(state)

    def setReportPeriod(self, address, period):
        self.drivers[address].setReportPeriod(period)

Manager = WiiManager()

def PollPages():
    Manager.step()

    # so I can see my debugging prints
    sys.stdout.flush()

class PageController(BasePageController):
    def __init__(self, page_id, module):
        BasePageController.__init__(self, page_id, module)
        self.events_to_send = { 'new-wiimote':True,
                                'button-press':True,
                                'accel-report':False }
        
    def onStart(self, cmd):
        return jsext.CLASS

    def onStop(self, cmd):
        Manager.removePage(self)

    def onRequest(self, cmd):
        try:
            action = cmd['action']
            if action == 'set-property':
                name = cmd['name']
                value = cmd['value']
                wm = cmd['wm']
                if name == 'accel-report':
                    self.events_to_send['accel-report'] = value
                    Manager.enableAccel(wm, value)
                elif name == 'accel-period':
                    Manager.setReportPeriod(wm, value)
                else:
                    # error
                    pass

            elif action == 'connect':
                wanted = cmd['address']
                address = Manager.pageConnect(self, wanted)
                if address:
                    self.postEvent('new-wiimote', id=address)
                else:
                    self.postEvent('no-wiimote', id=wanted)

        except Exception, e:
            import traceback
            traceback.print_exc()
    
    def postEvent(self, event, **args):
        if self.events_to_send.get(event, False):
            #print 'post', event
            self.pushResponse(event, **args)
        else:
            print 'skipped', event

                    
    
