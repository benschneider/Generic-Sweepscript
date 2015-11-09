from time import sleep
import numpy as np
import sys
import PXIDigitizer_wrapper
from cmath import rect  # to get polar coordinates..

# Digitizer.boot_instrument('PXI7::15::INSTR', 'PXI6::10::INSTR')
# Digitizer.boot_instrument('3011D1', '3036D1')


class instrument():

    '''Upon start, creates connection to Digitizer and Local oscillator
        this driver only contains some rudimentary functions to run
        the PXI-Aeroflex 3036 Digitizer.
        To speed things up one function is used to record data which is
        then stored in the object.
        From this various aspects are then calculated as needed and
        retriggered/recoreded again when actually needed instead of every time
        again...
    '''

    def __init__(self, 
                 adressDigi='3036D1', 
                 adressLo='3011D1', 
                 LoPosAB=1, 
                 LoRef=0, 
                 name='D',
                 cfreq = 4.57e9,
                 start=4.43e9, 
                 stop=0, 
                 pt=1, 
                 nSample=50e3,
                 sampFreq=10e6):
        self.sampFreq = sampFreq        # in Hz
        self.bandwidth = 10e6
        self.removeDCoff = 1
        self.LoPos = LoPosAB          # Lo Above (1) or Below (0)
        self.freq = cfreq
        self.nSamples = int(nSample)   # Samples taken/trigger
        self.inputLvl = -10
        self.Overload = 4           # to test the overload code
        self.LoRef = LoRef          # 0=ocxo, 1=int 2=extDaisy, 3=extTerminated
        self.trig_source = 8        # 8=Star, 32=SW, 35=internal
        self.adressLo = adressLo
        self.adressDigi = adressDigi
        self.name = name
        self.start = start
        self.stop = stop
        self.pt = pt
        self.lin = np.linspace(self.start, self.stop, self.pt)
        self.digitizer = PXIDigitizer_wrapper.afDigitizer_BS()
        try:
            self.digitizer.create_object()
            self.digitizer.boot_instrument(adressLo, adressDigi)
            self.prep_data()
            self.set_settings()
            print self.digitizer.ref_is_locked()  # print Lo locked confirmation
            print 'Digitizer started'        
        except PXIDigitizer_wrapper.Error as e:
            print "Digitizer start failed"
            raise Exception(e)

    def performClose(self, bError=False):
        ''' assume digitizer exists'''
        try:
            self.digitizer.rf_rf_input_level_set(30)
            self.digitizer.close_instrument(bCheckError=not bError)
        except PXIDigitizer_wrapper.Error as e:
            if not bError:
                 raise Exception(e)
        finally:
            try:
                self.digitizer.destroy_object()
                del self.digitizer
            except:
                pass

    def set_settings(self):
        '''
        #right now its easies to simply set the settings here
        '''
        self.digitizer.rf_remove_dc_offset_set(bool(self.removeDCoff))
        self.digitizer.modulation_generic_sampling_frequency_set(self.sampFreq)
        # self.digitizer.trigger_IQ_bandwidth_set(self.bandwidth, iOption)
        self.digitizer.rf_rf_input_level_set(self.inputLvl)
        self.digitizer.rf_userLOPosition_set(self.LoPos)
        self.digitizer.modulation_mode_set(5)  # Set to Generic
        self.digitizer.rf_centre_frequency_set(self.freq)
        self.digitizer.lo_reference_set(self.LoRef)
        self.digitizer.trigger_source_set(self.trig_source)

    def prep_data(self):
        self.vAvgIQ = None
        self.vAvgPow = None  
        self.cRawIQ =None
        self.AvgMag = None
        self.AvgPhase = None
        self.vAvgMag = None
        self.vAvgPh = None
        self.scaledI = None
        self.scaledQ = None

    def set_freq(self, freq):
        self.digitizer.rf_centre_frequency_set(freq)

    def get_freq(self):
        return self.digitizer.rf_centre_frequency_get()

    def set_inputLevel(self, value):
        self.digitizer.rf_rf_input_level_set(value)

    def get_Levelcorr(self):
        return self.digitizer.rf_level_correction_get()

    def set_LoAboveBelow(self, val):
        ''' below(0), above(1) '''
        self.digitizer.rf_userLOPosition_set(val)

    def get_avgIQ(self):
        """Return Averaged I and Q signal in time as a complex vector,
        resample the signal if needed, and then clear cTrace to indicate
        capture has been taken.
        """
        if self.vAvgIQ is None:
            self.sampleAndAverage()
        vAvgIQ = self.vAvgIQ
        self.vAvgIQ = None
        return vAvgIQ

    def get_rawIQ(self):
        ''' Returns the unaveraged (vI,vQ) Data '''
        if self.scaledI is None or self.scaledQ is None:
            self.sampleAndAverage()
        vI = self.scaledI
        vQ = self.scaledQ
        self.scaledI = None
        self.scaledQ = None
        return np.array(vI), np.array(vQ)

    def get_AvgMagPhs(self):
        ''' Returns the average Magnitude and Phase '''
        if self.AvgMag is None or self.AvgPhase is None:
            self.sampleAndAverage()
        AvgMag = self.AvgMag
        AvgPhase = self.AvgPhase
        self.AvgMag = None
        self.AvgPhase = None
        return np.array(AvgMag), np.array(AvgPhase)   
      
    def get_vAvgMagPhs(self):
        ''' Returns the voltage averaged Magnitude and Phase '''
        if self.vAvgMag is None or self.vAvgPh is None:
            self.sampleAndAverage()
        vAvgMag = self.vAvgMag
        vAvgPh = self.vAvgPh
        self.vAvgMag = None
        self.vAvgPh = None
        return np.array(vAvgMag), np.array(vAvgPh)
    
    def get_AvgPower(self):
        ''' Returns the Averaged Power '''
        if self.vAvgPow is None:
            self.sampleAndAverage()
        vAvgPow = self.vAvgPow
        self.vAvgPow = None
        return np.array(vAvgPow)
               
    def sampleAndAverage(self):
        '''# Sample the signal, calc I+j*Q theta
        # and store it in the driver object
        # of each triger there are x samples... which can be averaged...
        '''
        TriggerSourceValue = self.digitizer.trigger_source_get()
        dLevelCorrection = self.digitizer.rf_level_correction_get()
        self.digitizer.trigger_arm_set(self.nSamples*2)
        self.checkADCOverload()
        vI = np.zeros(1)
        vQ = np.zeros(1)
        vI2 = np.zeros(1)
        vQ2 = np.zeros(1)

        # TriggersourceValue 32 = SW trigger
        if TriggerSourceValue is not 32:
            self.digitizer.trigger_arm_set(self.nSamples*2)
            self.checkADCOverload()
            # wait for external trigger signal
            while self.digitizer.data_capture_complete_get() is False:
                sleep(5e-3)
                self.checkADCOverload()
                (lI, lQ) = self.digitizer.capture_iq_capt_mem(self.nSamples)
        else:
                self.checkADCOverload()
                (lI, lQ) = self.digitizer.capture_iq_capt_mem(self.nSamples)

        # scale data to Volt / sqrt(1Ohm)
        self.scaledI = (np.array(lI) 
                        * np.power(10.0, dLevelCorrection/20.0)
                        / np.sqrt(1000))
        self.scaledQ = (np.array(lQ)
                        * np.power(10.0, dLevelCorrection/20.0)
                        / np.sqrt(1000))
        # Average I and Q voltages
        vI = np.mean(self.scaledI, axis=0)
        vQ = np.mean(self.scaledQ, axis=0)
        vI2 = np.mean(self.scaledI**2, axis=0)
        vQ2 = np.mean(self.scaledQ**2, axis=0)

        self.vAvgIQ = vI+1j*vQ
        self.vAvgPow = (vI2+vQ2)                
        self.vAvgMag = np.absolute(self.vAvgIQ)     
        self.vAvgPh = np.angle(self.vAvgIQ)

        # Average Magnitued and Phases
        cRawIQ = self.scaledI + 1j*self.scaledQ        
        self.AvgMag = np.mean(np.absolute(cRawIQ))
        self.AvgPhase = np.mean(np.angle(cRawIQ))      
        #self.AvgMagPow = np.mean((self.scaledI**2 + self.scaledQ**2), axis=0)


    def set_bandwidth(self, val):
        self.digitizer.trigger_IQ_bandwidth_set(val)

    def set_sampRate(self, val):
        self.digitizer.modulation_generic_sampling_frequency_set(val)

    def checkADCOverload(self):
        if self.digitizer.check_ADCOverload():
            self.Overload = self.Overload + 1
            sleep(0.2)
            if self.Overload > 3:
                self.digitizer.rf_rf_input_level_set(30)
                raise Exception('ADC overloaded 3x in a row')
        else:
            self.Overload = 0
