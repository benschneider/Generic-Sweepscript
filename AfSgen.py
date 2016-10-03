# -*- coding: utf-8 -*-
"""
Created on Sun May 22 14:56:11 2016

@author: Ben
"""

# from ctypes import WinDLL
# _lib = WinDLL('afSigGenDll_32')

import numpy as np
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
            # args[0].S.ClearErrors()
            a = func(*args, **kwargs)
            if args[0].S.ErrorCode < 0 :
                raise Exception(args[0].S.ErrorMessage)
            elif args[0].S.ErrorCode > 0 :
                print 'Warning ' + str(args[0].S.ErrorMessage)
            
            args[0].S.ClearErrors()
            return a
        return new_func

    def __init__(self, adressSig='PXI8::9::INSTR', adressLo='PXI8::10::INSTR', 
                 LoRef=2, name='Signal Gen', start=2e9, stop=6e9, pt=1,
                 sstep=1e9, stime=0.0):
        self.S=CreateObject('afComSigGen.afCoSigGen')
        self.boot(adressLo, adressSig)
        self.set_LO_Ref(LoRef)
        self.RF = self.S.RF
        self.name = name
        self.start = start
        self.stop = stop
        self.pt = pt
        self.sstep = sstep
        self.stime = stime
        self.lin = np.linspace(self.start, self.stop, self.pt)
        self.sweep_par = 'frequency'
        
    @error_check
    def boot(self, LO, SIG):
        self.S.BootInstrument('PXI8::10::INSTR','PXI8::9::INSTR', False)
    
    @error_check    
    def set_LO_Ref(self, loref=2):
        ''' 0 lormOCXO - plugin is set to Internal 
            1 lormInternal - plugin is set to Internal 
            2 lormExternalDaisy - plugin is set to External 
            3 lormExternalTerminated - plugin is set to External. 
        '''
        self.S.LO.Reference = loref    
    
    @error_check    
    def set_frequency(self, f):
        self.S.RF.CurrentFrequency = f

    def get_frequency(self):
        return self.S.RF.CurrentFrequency
        
    @error_check
    def set_power(self, power):
        self.S.RF.CurrentLevel = power
    
    def get_power(self):
        return self.S.RF.CurrentLevel

    @error_check
    def output(self, Outputbool):
        self.S.RF.CurrentOutputEnable = Outputbool
        
    def get_output(self):
        return self.S.RF.CurrentOutputEnable
    
    @error_check
    def set_trigger_mode(self, mode):
        pass

    @error_check
    def set_trigger_type(self, TriggerType=0):
        """Edge=0, Gate=1"""
        self.S.Trigger.TType = TriggerType

    def get_trigger_type(self):
        return self.D.Trigger.TType
    
    @error_check
    def set_trigger(self):
        pass
    
    def closeInstrument(self):
        self.closeInstrument()
    
if __name__ == '__main__':
    sig = instrument(adressSig='PXI8::9::INSTR', adressLo='PXI8::10::INSTR', 
                     LoRef=2, name='Signal Gen', start=2e9, stop=6e9, pt=1, 
                     sstep=1e9, stime=0.0)