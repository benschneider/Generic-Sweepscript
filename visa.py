# -*- coding: utf-8 -*-
"""
Created on Thu Jan 28 00:16:29 2016
@author: thomasaref

Modified on Fri Feb 12 20:14 2016
@author: Ben Schneider

This is a fake visa driver, such that the instrument drivers can be tested 
without them being connected.
delete this file from the running folder when actually using an instrument
"""

class instrument(object):
    def __init__(self, adress='noadress'):
        pass
    def clear(self):
        print "clear"
    def close(self):
        print "close"
    def write(self, wstr):
        print "write "+wstr
    def ask(self, astr):
        print "ask "+astr
        return "0.0"
    def read(self):
        print "read"
        return "read"
