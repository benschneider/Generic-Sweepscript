# -*- coding: utf-8 -*-
"""
Created on Wed Apr 06 10:52:34 2016

@author: Morran or Lumi
"""

from ctypes import c_long, byref, WinDLL, create_string_buffer, c_double  # ,c_char_p , c_bool
from time import sleep
NISYNC_VAL_SWTRIG_GLOBAL="GlobalSoftwareTrigger"
NISYNC_VAL_PXISTAR1="PXI_Star1"
NISYNC_VAL_PXISTAR5="PXI_Star5"
NISYNC_VAL_PFI0="PFI0"
NISYNC_VAL_SYNC_CLK_FULLSPEED="SyncClkFullSpeed"

NISYNC_VAL_DONT_INVERT=0
NISYNC_VAL_INVERT=1

NISYNC_VAL_UPDATE_EDGE_RISING=0
NISYNC_VAL_UPDATE_EDGE_FALLING=1


class nit(object):
    _lib=WinDLL('niSync.dll')
    #init=_lib.niSync_init

    def __init__(self, adress="PXI7::15::INSTR"):
        self.session=c_long()
        self.msg=create_string_buffer(256)
        res = self._lib.niSync_init(adress, False, False, byref(self.session))
        self.error_message(res)
    
    def error_message(self, error_code):
        if error_code == 0:
            # success
            return
        self._lib.niSync_error_message(self.session.value, error_code, self.msg)
        print self.msg.value


    def connect_SW_trigger(self, num):
        res = self._lib.niSync_ConnectSWTrigToTerminal(self.session, 'GlobalSoftwareTrigger', ('PXI_Star'+str(num)), "SyncClkFullSpeed", 0, 0, c_double(0.0))
        self.error_message(res)

    def send_software_trigger(self):
        res = self._lib.niSync_SendSoftwareTrigger(self.session, 'GlobalSoftwareTrigger')
        self.error_message(res)
    
    def send_many_triggers(self, n):
         for n in range(n):
            self._lib.niSync_SendSoftwareTrigger(self.session, 'GlobalSoftwareTrigger')
            sleep(0.1)

    def disconnect_software_trigger(self, num):
        res = self._lib.niSync_DisconnectSWTrigFromTerminal(self.session, 'GlobalSoftwareTrigger', ('PXI_Star'+str(num)))
        self.error_message(res)
           
    #_lib.niSync_ConnectSWTrigToTerminal(session, 'GlobalSoftwareTrigger', 'PXI_Star1', "SyncClkFullSpeed", 0, 0, c_double(0.0))
    def close(self):
        res = self._lib.niSync_close(self.session)
        self.error_message(res)
            
    def connect_ext_trig(self):
        '''
        source/destination can be 'PXI_Trix#' or 'PFI#' or 'PFI_LVDS#'1,2, 'PXIe_DStarB#'
        "SyncClkFullSpeed" - syncronized clock
        updateEdge=1 on rising edge / 0 on edge falling
        '''
        res = self._lib.niSync_ConnectTrigTerminals(self.session, source='PXI_Trig1', destination='PFI0', clk='SyncClkFullSpeed', invert=0, updateEdge=1) 
        self.error_message(res)

    def reset(self):
        ''' Reset, set DDS to 0Hz...'''
        res = self._lib.niSync_reset (self.session)
        self.error_message(res)


if __name__ == '__main__':
    pstar = nit()
    pstar.connect_SW_trigger(1)
    pstar.connect_SW_trigger(5)
    pstar.send_many_triggers(100)
    pstar.disconnect_software_trigger(1)
    pstar.disconnect_software_trigger(5)