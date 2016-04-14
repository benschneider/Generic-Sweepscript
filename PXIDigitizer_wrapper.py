# -*- coding: utf-8 -*-
"""
Created on Tue Nov 03 16:52:38 2015

-B
"""

# import numpy as np
# from struct import unpack #, pack
# from time import sleep
# import visa
# from parsers import savemtx, make_header, ask_overwrite

from ctypes import c_int, c_long, c_float, c_double, c_ulong, POINTER, byref, WinDLL, c_char_p, Structure, c_void_p


class Error(Exception):
    pass

_lib = WinDLL('afDigitizerDll_32')

# define data types used by this dll
STRING = c_char_p
AFBOOL = c_long

# define variables
afDigitizerInstance_t = c_long
afDigitizerCaptureIQ_t = c_long

class afDigitizerBufferIQ_t(Structure):
    pass

afDigitizerBufferIQ_t._fields_ = [
        ('iBuffer', POINTER(c_float)),
        ('qBuffer', POINTER(c_float)),
        ('samples', c_ulong),
        ('userData', c_void_p)]

# define dll function objects in python
CreateObject = _lib.afDigitizerDll_CreateObject
CreateObject.restype = c_long
CreateObject.argtypes = [POINTER(afDigitizerInstance_t)]
DestroyObject = _lib.afDigitizerDll_DestroyObject
DestroyObject.restype = c_long
DestroyObject.argtypes = [afDigitizerInstance_t]
BootInstrument = _lib.afDigitizerDll_BootInstrument
BootInstrument.restype = c_long
BootInstrument.argtypes = [afDigitizerInstance_t, STRING, STRING, AFBOOL]
CloseInstrument = _lib.afDigitizerDll_CloseInstrument
CloseInstrument.restype = c_long
CloseInstrument.argtypes = [afDigitizerInstance_t]
ErrorMessage_Get = _lib.afDigitizerDll_ErrorMessage_Get
ErrorMessage_Get.restype = c_long
ErrorMessage_Get.argtypes = [afDigitizerInstance_t, STRING, c_ulong]


def getDllObject(sName, argtypes=[afDigitizerInstance_t], restype=c_long):
    """Create a dll ojbect with input and output types"""
    obj = getattr(_lib, sName)
    obj.restype = restype
    obj.argypes = argtypes
    return obj


class afDigitizer_BS():

    def error_check(func):
        buffLen = c_ulong(256)
        msgBuff = c_char_p(' '*256)       
        err = c_long()
        def new_func(*args, **kwargs):
            # something required here to get the helptags right
            ses = args[0].session
            _lib.afDigitizerDll_ClearErrors(ses)
            a = func(*args, **kwargs)
            _lib.afDigitizerDll_ErrorCode_Get(ses, byref(err))
            if err.value < 0 :
                _lib.afDigitizerDll_ErrorMessage_Get(ses, msgBuff, buffLen)
                raise Exception(msgBuff.value)
            if err.value > 0 :
                _lib.afDigitizerDll_ErrorMessage_Get(ses, msgBuff, buffLen)
                print 'Warning ' + str(msgBuff.value)
            return a
        return new_func

    def __init__(self):
        """The init case defines a session ID, used to identify the instrument"""
        # create a session id
        self.session = afDigitizerInstance_t()
        #ready some variables to be used
        self.state = c_long()
        self.cint = c_int()
        self.cdouble = c_double()
        self._lib = WinDLL('afDigitizerDll_32')
        self.create_object()

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

    # @error_check
    def capture_iq_reclaim_buffer_wait(self, capture_ref, buffer_ref_pointer):
        obj=getDllObject('afDigitizerDll_Capture_IQ_ReclaimBuffer',
                          argtypes = [afDigitizerInstance_t, afDigitizerCaptureIQ_t, POINTER(POINTER(afDigitizerBufferIQ_t))])
        error = obj(self.session, capture_ref, byref(buffer_ref_pointer))
        #_lib.afDigitizerDll_ErrorMessage_Get(ses, msgBuff, buffLen)
        self.check_error(error)

    def create_object(self):
        error = CreateObject(self.session)
        self.check_error(error)

    def destroy_object(self):
        error = DestroyObject(self.session)
        self.check_error(error)

    def shutdown(self):
        self.close_instrument()
        self.destroy_object()
        
    def boot_instrument(self, sLoResource, sRfResource, bLoIsPlugin=False):
        cLoResource = STRING(sLoResource)
        cRfResource = STRING(sRfResource)
        error = BootInstrument(self.session, cLoResource,
                               cRfResource, AFBOOL(bLoIsPlugin))
        self.check_error(error)
        return (cLoResource.value, cRfResource.value)

    def close_instrument(self, bCheckError=True):
        error = CloseInstrument(self.session)
        if bCheckError:
            self.check_error(error)

    def lo_reference_set(self, lLORef):
        """Modes are [lormOCXO=0, lormInternal=1, lormExternalDaisy=2, lormExternalTerminated=3]"""
        obj = getDllObject('afDigitizerDll_LO_Reference_Set',
                           argtypes=[afDigitizerInstance_t, c_long])
        error = obj(self.session, c_long(lLORef))
        self.check_error(error)

    def lo_reference_get(self):
        """Modes are [lormOCXO=0, lormInternal=1, lormExternalDaisy=2, lormExternalTerminated=3]"""
        obj = getDllObject('afDigitizerDll_LO_Reference_Get',
                           argtypes=[afDigitizerInstance_t, POINTER(c_long)])
        dValue = c_long()
        error = obj(self.session, byref(dValue))
        self.check_error(error)
        return dValue.value

    def ref_is_locked(self):
        #Returns whether LO is locked to the external 10 Mhz reference when
        #Reference is set to ExternalDaisy or ExternalTerminated.
        obj = getDllObject('afDigitizerDll_LO_ReferenceLocked_Get',
                           argtypes=[afDigitizerInstance_t, POINTER(c_long)])
        dValue = c_long()
        error = obj(self.session, byref(dValue))
        self.check_error(error)
        return dValue.value

    @error_check
    def rf_centre_frequency_set(self, dFreq):
        obj = getDllObject('afDigitizerDll_RF_CentreFrequency_Set',
                           argtypes=[afDigitizerInstance_t, c_double])
        obj(self.session, c_double(dFreq))

    def rf_centre_frequency_get(self):
        obj = getDllObject('afDigitizerDll_RF_CentreFrequency_Get',
                           argtypes=[afDigitizerInstance_t, POINTER(c_double)])
        dValue = c_double()
        error = obj(self.session, byref(dValue))
        self.check_error(error)
        return dValue.value

    def rf_rf_input_level_set(self, dValue):
        obj = getDllObject('afDigitizerDll_RF_RFInputLevel_Set',
                           argtypes=[afDigitizerInstance_t, c_double])
        error = obj(self.session, c_double(dValue))
        self.check_error(error)

    def rf_rf_input_level_get(self):
        obj = getDllObject('afDigitizerDll_RF_RFInputLevel_Get',
                           argtypes=[afDigitizerInstance_t, POINTER(c_double)])
        dValue = c_double()
        error = obj(self.session, byref(dValue))
        self.check_error(error)
        return dValue.value


    def modulation_generic_sampling_frequency_set(self, dValue):
        obj = getDllObject('afDigitizerDll_Modulation_SetGenericSamplingFreqRatio',
                           argtypes=[afDigitizerInstance_t, c_long, c_long])
        error = obj(self.session, c_long(int(dValue)), c_long(1))
        self.check_error(error)

    def modulation_generic_sampling_frequency_get(self):
        obj = getDllObject('afDigitizerDll_Modulation_GenericSamplingFrequency_Get',
                           argtypes=[afDigitizerInstance_t, POINTER(c_double)])
        dValue = c_double()
        error = obj(self.session, byref(dValue))
        self.check_error(error)
        return dValue.value

    def rf_remove_dc_offset_set(self, bOn=True):
        obj = getDllObject('afDigitizerDll_RF_RemoveDCOffset_Set',
                           argtypes=[afDigitizerInstance_t, AFBOOL])
        error = obj(self.session, AFBOOL(bOn))
        self.check_error(error)

    def rf_remove_dc_offset_get(self):
        obj = getDllObject('afDigitizerDll_RF_RemoveDCOffset_Get',
                           argtypes=[afDigitizerInstance_t, POINTER(AFBOOL)])
        pOn = AFBOOL()
        error = obj(self.session, byref(pOn))
        self.check_error(error)
        return bool(pOn.value)

    def capture_iq_capt_mem(self, nSamples):
        # define buffer type
        nSamples = int(nSamples)
        typeBuffer = c_float*nSamples
        obj = getDllObject('afDigitizerDll_Capture_IQ_CaptMem',
                           argtypes=[afDigitizerInstance_t, c_ulong,
                                     POINTER(typeBuffer),
                                     POINTER(typeBuffer)])
        # pre-allocate memory
        lValueI = typeBuffer()
        lValueQ = typeBuffer()
        error = obj(self.session, c_ulong(nSamples),
                    byref(lValueI), byref(lValueQ))
        self.check_error(error)
        return (list(lValueI), list(lValueQ))

    def trigger_source_set(self, iOption=0):
        """Options for the trigger source are found in the .ini file for the digitizer
        Sources are
        [PXI_TRIG_0=0, PXI_TRIG_1=1, PXI_TRIG_2=2, PXI_TRIG_3=3, PXI_TRIG_4=4, PXI_TRIG_5=5,
        PXI_TRIG_6=6, PXI_TRIG_7=7, PXI_STAR=8, PXI_LBL_0=9, PXI_LBL_1=10, PXI_LBL_2=11,
        PXI_LBL_3=12, PXI_LBL_4=13, PXI_LBL_5=14, PXI_LBL_6=15, PXI_LBL_7=16, PXI_LBL_8=17,
        PXI_LBL_9=18, PXI_LBL_10=19, PXI_LBL_11=20, PXI_LBL_12=21, LVDS_MARKER_0=22, LVDS_MARKER_1=23,
        LVDS_MARKER_2=24, LVDS_MARKER_3=25, LVDS_AUX_0=26, LVDS_AUX_1=27, LVDS_AUX_2=28, LVDS_AUX_3=29,
        LVDS_AUX_4=30, LVDS_SPARE_0=31, SW_TRIG=32, LVDS_MARKER_4=33, INT_TIMER=34, INT_TRIG=35, FRONT_SMB=36]"""
        obj = getDllObject('afDigitizerDll_Trigger_Source_Set',
                           argtypes=[afDigitizerInstance_t, c_long])
        error = obj(self.session, c_long(iOption))
        self.check_error(error)

    def trigger_source_get(self):
        """Options for the trigger source are found in the .ini file for the digitizer
        Sources are
        [PXI_TRIG_0=0, PXI_TRIG_1=1, PXI_TRIG_2=2, PXI_TRIG_3=3, PXI_TRIG_4=4, PXI_TRIG_5=5,
        PXI_TRIG_6=6, PXI_TRIG_7=7, PXI_STAR=8, PXI_LBL_0=9, PXI_LBL_1=10, PXI_LBL_2=11,
        PXI_LBL_3=12, PXI_LBL_4=13, PXI_LBL_5=14, PXI_LBL_6=15, PXI_LBL_7=16, PXI_LBL_8=17,
        PXI_LBL_9=18, PXI_LBL_10=19, PXI_LBL_11=20, PXI_LBL_12=21, LVDS_MARKER_0=22, LVDS_MARKER_1=23,
        LVDS_MARKER_2=24, LVDS_MARKER_3=25, LVDS_AUX_0=26, LVDS_AUX_1=27, LVDS_AUX_2=28, LVDS_AUX_3=29,
        LVDS_AUX_4=30, LVDS_SPARE_0=31, SW_TRIG=32, LVDS_MARKER_4=33, INT_TIMER=34, INT_TRIG=35, FRONT_SMB=36]"""
        obj = getDllObject('afDigitizerDll_Trigger_Source_Get',
                           argtypes=[afDigitizerInstance_t, POINTER(c_long)])
        iOption = c_long()
        error = obj(self.session, byref(iOption))
        self.check_error(error)
        return int(iOption.value)

    def modulation_mode_set(self, iOption=0):
        """Modes are [mmUMTS=0, mmGSM=1, mmCDMA20001x=2, mmEmu2319=4, mmGeneric=5]"""
        obj = getDllObject('afDigitizerDll_Modulation_Mode_Set',
                           argtypes=[afDigitizerInstance_t, c_int])
        error = obj(self.session, c_int(iOption))
        self.check_error(error)

    def modulation_mode_get(self):
        """Modes are [mmUMTS=0, mmGSM=1, mmCDMA20001x=2, mmEmu2319=4, mmGeneric=5]"""
        obj = getDllObject('afDigitizerDll_Modulation_Mode_Get',
                           argtypes=[afDigitizerInstance_t, POINTER(c_int)])
        iOption = c_int()
        error = obj(self.session, byref(iOption))
        self.check_error(error)
        return int(iOption.value)

    def trigger_polarity_set(self, iOption=0):
        """Modes are [Positive=0, Negative=1]"""
        obj = getDllObject('afDigitizerDll_Trigger_EdgeGatePolarity_Set',
                           argtypes=[afDigitizerInstance_t, c_int])
        error = obj(self.session, c_int(iOption))
        self.check_error(error)

    def trigger_polarity_get(self):
        """Modes are [Positive=0, Negative=1]"""
        obj = getDllObject('afDigitizerDll_Trigger_EdgeGatePolarity_Get',
                           argtypes=[afDigitizerInstance_t, POINTER(c_int)])
        dValue = c_int()
        error = obj(self.session, byref(c_int))
        self.check_error(error)
        return dValue.value

    def trigger_type_set(self, iOption=0):
        """Modes are [Edge=0, Gate=1]
        OLD        
        """
        obj = getDllObject('afDigitizerDll_Trigger_TType_Set',
                           argtypes=[afDigitizerInstance_t, c_int])
        error = obj(self.session, c_int(iOption))
        self.check_error(error)

    def trigger_type_get(self):
        """Modes are [Positive=0, Negative=1]
        OLD
        """
        obj = getDllObject('afDigitizerDll_Trigger_TType_Get',
                           argtypes=[afDigitizerInstance_t, POINTER(c_int)])
        dValue = c_int()
        error = obj(self.session, byref(c_int))
        self.check_error(error)
        return dValue.value

    def trigger_arm_set(self, inSamples=0):
        obj = getDllObject('afDigitizerDll_Trigger_Arm',
                           argtypes=[afDigitizerInstance_t, c_int])
        error = obj(self.session, c_int(inSamples))
        self.check_error(error)

    @error_check
    def set_trigger_mode(self, mode):
        '''The internal level trigger mode (Absolute 0 or Relative 1)'''
        _lib.afDigitizerDll_Trigger_IntTriggerMode_Set(self.session, c_int(mode))
 
    @error_check
    def get_trigger_mode(self):
        '''The internal level trigger mode (Absolute 0 or Relative 1)'''
        _lib.afDigitizerDll_Trigger_IntTriggerMode_Get(self.session, byref(self.state))
        return self.state.value
    
    @error_check
    def set_trigger_type(self, mode):
        ''' Edge 0, Gate 1'''
        _lib.afDigitizerDll_Trigger_TType_Set(self.session, c_int(mode))
 
    @error_check
    def get_trigger_type(self):
        ''' Edge 0, Gate 1'''
        _lib.afDigitizerDll_Trigger_TType_Get(self.session, byref(self.state))
        return self.state.value
        
    def data_capture_complete_get(self):
        obj = getDllObject('afDigitizerDll_Capture_IQ_CaptComplete_Get',
                           argtypes=[afDigitizerInstance_t, POINTER(AFBOOL)])
        dValue = AFBOOL()
        error = obj(self.session, byref(dValue))
        self.check_error(error)
        return bool(dValue.value)

    def error_message_get(self):
        bufferLen = c_ulong(256)
        msgBuffer = STRING(' '*256)
        ErrorMessage_Get(self.session, msgBuffer, bufferLen)
        return msgBuffer.value

    def check_error(self, error=0):
        """If error occurred, get error message and raise error"""
        if error:
            raise Exception(self.error_message_get())

    def rf_level_correction_get(self):
        #OLD
        return self.get_rf_level_correction()

    @error_check
    def get_rf_level_correction(self):
        '''Returns level correction value in dB'''
        _lib.afDigitizerDll_RF_LevelCorrection_Get(self.session.value, byref(self.cdouble))
        return self.cdouble.value

    @error_check
    def set_IFaliasFilter(self, boolval=0):
        _lib.afDigitizerDll_RF_IFFilterBypass_Set(self.session.value, c_int(boolval))

    @error_check
    def get_IFaliasFilter(self):
        _lib.afDigitizerDll_RF_IFFilterBypass_Get(self.session.value, byref(self.state))
        return self.state.value

    @error_check
    def set_piplining(self, boolval=1):
        '''
        Enables (True) or disables (False) the Capture Pipelining mechanism.
        To realize the optimum performance improvement, you must follow the sequence below: 
        TriggerArm(...)          // If Armed trigger is used
        TriggerDetected_Get(...) // If Armed trigger is used
        CaptMem(...)
        '''
        _lib.afDigitizerDll_Capture_PipeliningEnable_Set(self.session.value, c_int(boolval))
 
    @error_check
    def get_piplining(self):
        _lib.afDigitizerDll_Capture_PipeliningEnable_Get(self.session.value, byref(self.state))
        return bool(self.state.value)

    @error_check
    def get_trigger_detected(self):
        _lib.afDigitizerDll_Capture_IF_TriggerDetected_Get(self.session, byref(self.state))
        return bool(self.state.value)
 
    @error_check
    def TriggerArmIF(self, nsamp):
        _lib.afDigitizerDll_Capture_IF_TriggerArm(self.session, c_int(nsamp))
       
    def trigger_pre_edge_trigger_samples_get(self):
        afDigitizerDll_Trigger_PreEdgeTriggerSamples_Get = getDllObject('afDigitizerDll_Trigger_PreEdgeTriggerSamples_Get',
                                                                       argtypes = [afDigitizerInstance_t, POINTER(c_ulong)])
        dValue=c_ulong()
        error = afDigitizerDll_Trigger_PreEdgeTriggerSamples_Get(self.session, byref(dValue))
        self.check_error(error)
        return dValue.value

    def trigger_pre_edge_trigger_samples_set(self, preEdgeTriggerSamples):
        afDigitizerDll_Trigger_PreEdgeTriggerSamples_Set = getDllObject('afDigitizerDll_Trigger_PreEdgeTriggerSamples_Set',
                                                              argtypes = [afDigitizerInstance_t, c_ulong])
        error = afDigitizerDll_Trigger_PreEdgeTriggerSamples_Set(self.session, c_ulong(preEdgeTriggerSamples))
        self.check_error(error)

    def trigger_IQ_bandwidth_set(self, dBandWidth, iOption=0):
        afDigitizerDll_Trigger_SetIntIQTriggerDigitalBandwidth = getDllObject('afDigitizerDll_Trigger_SetIntIQTriggerDigitalBandwidth',
                                                                       argtypes = [afDigitizerInstance_t, c_double, c_int, POINTER(c_double)])
        dValue=c_double()
        error = afDigitizerDll_Trigger_SetIntIQTriggerDigitalBandwidth(self.session, c_double(dBandWidth), c_int(iOption), byref(dValue))
        self.check_error(error)
        return dValue.value

    def check_ADCOverload(self):
        afDigitizerDll_Capture_IQ_ADCOverload_Get = getDllObject('afDigitizerDll_Capture_IQ_ADCOverload_Get',
                                                                 argtypes =[afDigitizerInstance_t, POINTER(AFBOOL)])
        bADCOverload = AFBOOL()
        error = afDigitizerDll_Capture_IQ_ADCOverload_Get(self.session, byref(bADCOverload))
        self.check_error(error)
        return bADCOverload.value

    def rf_userLOPosition_get(self):
        afDigitizerDll_RF_UserLOPosition_Get = getDllObject('afDigitizerDll_RF_UserLOPosition_Get', argtypes=[afDigitizerInstance_t, POINTER(c_int)])
        iValue = c_int()
        error = afDigitizerDll_RF_UserLOPosition_Get(self.session, byref(iValue))
        self.check_error(error)
        return iValue.value

    def rf_userLOPosition_set(self, iLOPosition):
        afDigitizerDll_RF_UserLOPosition_Set = getDllObject('afDigitizerDll_RF_UserLOPosition_Set', argtypes = [afDigitizerInstance_t, c_int])
        error = afDigitizerDll_RF_UserLOPosition_Set(self.session, iLOPosition)
        self.check_error(error)


if __name__ == '__main__':
    # test driver
    D1 = afDigitizer_BS()
    # D1.create_object()  # Implemented in the __init__
    # Digitizer.boot_instrument('PXI8::15::INSTR', 'PXI8::14::INSTR')
    # Digitizer.boot_instrument('PXI7::15::INSTR', 'PXI6::10::INSTR')
    D1.boot_instrument('3011D1', '3036D1')
    print D1.modulation_mode_get()
    dFreq = D1.modulation_generic_sampling_frequency_get()
    print 'Current frequency: ' + str(dFreq)
    D1.modulation_generic_sampling_frequency_set(250E6)
    dFreq = D1.modulation_generic_sampling_frequency_get()
    print 'Current frequency: ' + str(dFreq)
    [lI, lQ] = D1.capture_iq_capt_mem(2048)
    print D1.modulation_mode_get()
    #print lI, lQ
    D1.close_instrument()
    D1.destroy_object()
