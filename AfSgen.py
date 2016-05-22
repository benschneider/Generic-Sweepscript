# -*- coding: utf-8 -*-
"""
Created on Sun May 22 14:56:11 2016

@author: Ben
"""

# from ctypes import WinDLL
# _lib = WinDLL('afSigGenDll_32')


from comtypes.client import CreateObject
# s=CreateObject('afComSigGen.afCoSigGen') 
#Location of drive will be: C:\Python27\Lib\site-packages\comtypes\gen
from comtypes.gen import AFCOMSIGGENLib as afsiglib

#print  afdiglib.afDigitizerDll_tsSW_TRIG
#D1.BootInstrument('3011D1', '3036D1', False)
#print  D1.ErrorCode,  D1.ErrorSource, D1.ErrorMessage
#print D1.RF.CentreFrequency
#D1.RF.CentreFrequency=3e9
#print D1.RF.CentreFrequency
#D1.CloseInstrument()


class instrument(object):
    
    def error_check(func):
        def new_func(*args, **kwargs):
            args[0].D.ClearErrors()
            a = func(*args, **kwargs)
            if args[0].D.ErrorCode < 0 :
                raise Exception(args[0].D.ErrorMessage)
            elif args[0].D.ErrorCode > 0 :
                print 'Warning ' + str(args[0].D.ErrorMessage)
            return a
        return new_func

    @error_check
    def __init__(self):
        self.S=CreateObject('afComSigGen.afCoSigGen')
        
    def startup(self):
        pass

    @error_check
    def boot(self):
        self.D.BootInstrument('3011D1', '3036D1', False)
    
    
    @error_check
    def set_frequency(self, f):
        self.D.RF.CentreFrequency=f

    def get_frequency(self):
        return self.D.RF.CentreFrequency
        
    @error_check
    def set_LOpos(self, ALBool):
        '''ALBOOL 0 below, 1 above'''
        pass
    
    @error_check
    def set_trigger_mode(self, mode):
        pass

    @error_check
    def set_trigger_type(self, TriggerType=0):
        """Edge=0, Gate=1"""
        self.D.Trigger.TType = TriggerType

    def get_trigger_type(self):
        return self.D.Trigger.TType
    
    @error_check
    def set_trigger(self):
        pass