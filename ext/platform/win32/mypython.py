#!/usr/bin/python

'''Experiment with making one python executable for outfox instead of building every time'''

import array
import asynchat
import asyncore
import atexit
import bluetooth
import ctypes
import math
import os
import pyTTS
import Queue
import socket
import sys
import threading
import time
import traceback

sys.path.append('.')
sys.path.append('..')

sys.stderr = sys.stdout = file('c:/outfox.log', 'w')

mydir = os.path.dirname(sys.argv[0])
if mydir:
    os.chdir(mydir)

print os.getcwd(), mydir, sys.argv[0]

execfile('..\outfox.py')
