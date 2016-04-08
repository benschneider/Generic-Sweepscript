# -*- coding: utf-8 -*-
"""
Created on Thu Apr 07 15:06:04 2016

@author: Ben
"""

from ctypes import c_int, c_long, c_float, c_double, c_ulong, POINTER, byref, WinDLL, c_char_p, Structure, c_void_p


class digitizer(object):

    '''    
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
    '''

    def __init__(self):
        self.lib = WinDLL('afDigitizerDll_32')
        self.session=c_long()
    
    def error_check(func):
        buffLen = c_ulong(256)
        msgBuff = c_char_p(' '*256)       
        err = c_long()
        def new_func(*args, **kwargs):
            ses = args[0].session
            args[0].lib.afDigitizerDll_ClearErrors(ses)
            a = func(*args, **kwargs)
            args[0].lib.afDigitizerDll_ErrorCode_Get(ses, byref(err))
            if err.value < 0 :
                args[0].lib.afDigitizerDll_ErrorMessage_Get(ses, msgBuff, buffLen)
                raise Exception(msgBuff.value)
            if err.value > 0 :
                args[0].lib.afDigitizerDll_ErrorMessage_Get(ses, msgBuff, buffLen)
                print 'Warning ' + str(msgBuff.value)
            return a
        return new_func

        

    def error_message_get(self):
        bufferLen = c_ulong(256)
        msgBuffer = c_char_p(' '*256)
        self.lib.afDigitizerDll_ErrorMessage_Get(self.session, msgBuffer, bufferLen)
        return msgBuffer.value

    def check_error(self, error=0):
        """If error occurred, get error message and raise error"""
        if error:
            raise Exception(self.error_message_get())

        
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

    
    def capture_iq_issue_buffer(self, buffer_ref, capture_ref, timeout=1):
        obj=getDllObject('afDigitizerDll_Capture_IQ_IssueBuffer',
                          argtypes = [afDigitizerInstance_t, POINTER(afDigitizerBufferIQ_t), c_long, POINTER(afDigitizerCaptureIQ_t)])
        error=obj(self.session, byref(buffer_ref), 1000*timeout, byref(capture_ref))
        self.check_error(error)

    def capture_iq_reclaim_buffer(self, capture_ref, buffer_ref_pointer):
        obj=getDllObject('afDigitizerDll_Capture_IQ_ReclaimBuffer',
                          argtypes = [afDigitizerInstance_t, afDigitizerCaptureIQ_t, POINTER(POINTER(afDigitizerBufferIQ_t))])
        error = obj(self.session, capture_ref, byref(buffer_ref_pointer))
        self.check_error(error)
           
