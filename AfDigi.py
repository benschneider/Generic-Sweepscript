from ctypes import c_float, POINTER, pointer
from time import sleep
import numpy as np
import PXIDigitizer_wrapper
reload(PXIDigitizer_wrapper)

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

    def __init__(self, adressDigi='3036D1', adressLo='3011D1',
                 LoPosAB=1, LoRef=2, name='D', cfreq=4.8e9, inputlvl=0,
                 start=4.1e9, stop=0, pt=1, nSample=1e6, sampFreq=1e6,
                 buffmode=True):
        self.ADCFAIL = False
        self.capture_ref = None
        self.ADCoverflow = 0
        self.buffmode = buffmode
        self.bandwidth = sampFreq
        self.removeDCoff = 0
        self.LoPos = LoPosAB          # Lo Above (1) or Below (0)
        self.freq = cfreq
        self.nSamples = int(nSample)   # Samples taken/trigger
        self.inputLvl = inputlvl
        self.Overload = 0
        self.LoRef = LoRef          # 0=ocxo, 1=int 2=extDaisy, 3=extTerminated
        self.trig_source = 8        # 8=Star, 32=SW, 35=internal
        self.adressLo = adressLo
        self.adressDigi = adressDigi
        self.name = name
        self.start = start
        self.stop = stop
        self.pt = pt
        self.lin = np.linspace(self.start, self.stop, self.pt)
        self.prep_data()
        self.performOpen()
        self.set_settings()
        if self.buffmode:
            self.setup_buffer()
        else:
            self.setup_captmem()

    def performOpen(self):
        if hasattr(self, 'digitizer'):
            ''' If Digitizer exists then close it first 
            and then reopen it '''
            self.performClose()

        self.digitizer = PXIDigitizer_wrapper.afDigitizer_BS()
        try:
            # self.digitizer.create_object()
            self.digitizer.boot_instrument(self.adressLo, self.adressDigi)
            print 'Digitizer ', self.name, ' started'
        except PXIDigitizer_wrapper.Error as e:
            print "Digitizer start failed"
            self.digitizer.close_instrument()
            self.digitizer.destroy_object()
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
            self.digitizer.close_instrument()
            self.digitizer.destroy_object()
            del self.digitizer
            self.close_memfiles()

    def set_settings(self):
        '''
        right now its easies to simply set the settings here
        '''
        self.digitizer.rf_remove_dc_offset_set(bool(self.removeDCoff))
        self.digitizer.modulation_generic_sampling_frequency_set(self.bandwidth)
        # self.digitizer.trigger_IQ_bandwidth_set(self.bandwidth, iOption)
        self.digitizer.rf_rf_input_level_set(self.inputLvl)
        self.digitizer.rf_userLOPosition_set(self.LoPos)
        self.digitizer.modulation_mode_set(5)  # Set to Generic
        self.digitizer.rf_centre_frequency_set(self.freq)
        self.digitizer.lo_reference_set(self.LoRef)
        self.digitizer.trigger_source_set(self.trig_source)
        self.digitizer.set_piplining(1)  # activate Pipelining (download data while it keeps measuring)

    def set_frequency(self, freq):
        self.freq = freq
        self.digitizer.rf_centre_frequency_set(self.freq)

    def prep_data(self):
        '''Creates a range of empty variables which are used store data in'''
        self.vAvgIQ = None
        self.vAvgPow = None
        self.cRawIQ = None
        self.AvgMag = None
        self.AvgPhase = None
        self.vAvgMag = None
        self.vAvgPh = None
        self.create_memfiles()

    def create_memfiles(self):
        '''This creates on DISK Temp files to store large data chunks '''
        if self.buffmode:
            self.i_buffer = np.zeros(self.nSamples, dtype=c_float)
            self.q_buffer = np.zeros(self.nSamples, dtype=c_float)
        if self.nSamples > 1e6:
            self.cIQ = np.memmap(self.name[:2]+'.cIQ.mem', dtype='complex64', mode='w+', shape=self.nSamples)
            self.scaledI = np.memmap(self.name[:2]+'.I.mem', dtype=np.float32, mode='w+', shape=self.nSamples)
            self.scaledQ = np.memmap(self.name[:2]+'.Q.mem', dtype=np.float32, mode='w+', shape=self.nSamples)
            self.cfftsig = np.memmap(self.name[:2]+'.FFT.mem', dtype='complex64', mode='w+', shape=self.nSamples)
            # self.i_buffer = np.memmap(self.name[:2]+'.IB.mem', dtype=c_float, mode='w+', shape=self.nSamples)
            # self.q_buffer = np.memmap(self.name[:2]+'.QB.mem', dtype=c_float, mode='w+', shape=self.nSamples)
        else:
            # self.i_buffer = np.zeros(self.nSamples, dtype=c_float)
            # self.q_buffer = np.zeros(self.nSamples, dtype=c_float)
            self.cIQ = np.zeros(self.nSamples, dtype='complex64')
            self.scaledI = np.zeros(self.nSamples, dtype=np.float32)
            self.scaledQ = np.zeros(self.nSamples, dtype=np.float32)
            self.cfftsig = np.zeros(self.nSamples, dtype='complex64')

    def close_memfiles(self):
        del self.cIQ, self.scaledI, self.scaledQ, self.cfftsig
        if self.buffmode:
            del self.i_buffer, self.q_buffer

    def set_freq(self, freq):
        self.digitizer.rf_centre_frequency_set(freq)

    def get_freq(self):
        return self.digitizer.rf_centre_frequency_get()

    def set_inputLevel(self, value):
        self.digitizer.rf_rf_input_level_set(value)

    def get_Levelcorr(self):
        self.levelcorr = self.digitizer.rf_level_correction_get()
        return self.levelcorr

    def set_LoAboveBelow(self, val):
        ''' below(0), above(1) '''
        self.digitizer.rf_userLOPosition_set(val)

    def wait_capture_complete(self):
        while self.digitizer.data_capture_complete_get() is False:
            sleep(10e-3)
        pass

    def setup_buffer(self):
        '''
        The following is for setting the digitizer up in a buffering mode
        '''
        self.checkADCOverload()
        self.capture_ref = PXIDigitizer_wrapper.afDigitizerCaptureIQ_t()
        self.timeout = int(1000*self.nSamples/self.bandwidth+10000)
        i_ctypes = self.i_buffer.ctypes.data_as(POINTER(c_float))
        q_ctypes = self.q_buffer.ctypes.data_as(POINTER(c_float))
        self.buffer_ref = PXIDigitizer_wrapper.afDigitizerBufferIQ_t(
            i_ctypes, q_ctypes, self.nSamples)
        self.buffer_ref_pointer = pointer(self.buffer_ref)
        # print 'buffer setup'

    def setup_captmem(self):
        typeBuffer=c_float*self.nSamples
        self.i_buffer=typeBuffer()
        self.q_buffer=typeBuffer()
        
    def trigger_arm(self):
        self.digitizer.TriggerArmIQ(2*self.nSamples)

    def init_trigger_IF(self):
        return self.digitizer.TriggerArmIF(self.nSamples)

    def init_trigger_buff(self):
        ''' Initiate the Digitizer capturing into the buffer,
        once a trigger signal is received  '''
        self.digitizer.capture_iq_issue_buffer(
            buffer_ref=self.buffer_ref, capture_ref=self.capture_ref, timeout=self.timeout)

    def init_trigger(self):
        if self.buffmode:
            self.init_trigger_buff()
        else: 
            self.digitizer.trigger_arm_set(self.nSamples * 2)

    def downl_data_check(func):
        '''This is a property used when downloading data from the buffer.
        it excecutes the func until download beginns
        '''
        def new_func(*args, **kwargs):
            s = args[0]
            while True:
                try:
                    func(*args, **kwargs)
                except Exception, e:
                    if str(e) == 'Reclaim timeout':
                        # print 'Reclaim timeout'
                        sleep(0.05)
                        continue
                    elif str(e) == 'ADC overflow occurred in reclaimed buffer':
                        s.ADCFAIL = True
                        print 'handle'
                        print e.message
                        s.ADCoverflow += 1
                        if s.ADCoverflow > 4:
                            raise e.message
                    else:
                        raise e
                break
        return new_func

    @downl_data_check
    def downl_data_buff(self):
        self.ADCoverflow = 0
        a = self.digitizer.capture_iq_reclaim_buffer(
            capture_ref=self.capture_ref, buffer_ref_pointer=self.buffer_ref_pointer)
        if a == 0:
            '''for successfull download of buffer store IQ as complex array'''
            self.scaledI[:] = self.i_buffer[:]
            self.scaledQ[:] = self.q_buffer[:]

    def downl_data_old(self):
        '''grabs the biggest chunks of data '''
        self.checkADCOverload()
        (self.scaledI[:], self.scaledQ[:]) = self.digitizer.capture_iq_capt_mem(self.nSamples)

    @downl_data_check
    def downl_data_IQmem(self):
        a = self.digitizer.Capture_IQ_Mem(self.nSamples, self.i_buffer, self.q_buffer)
        if a == 0:
            '''for successfull download of buffer store IQ as complex array'''
            self.scaledI[:] = self.i_buffer[:]
            self.scaledQ[:] = self.q_buffer[:]

    def downl_data(self):
        if self.buffmode:
            self.downl_data_buff()
        else:
            self.downl_data_IQmem()

    def get_data_complete(self):
        ''' Downloads Data, Lvl Correction and processes the data
        stored as self.scaledI ...'''
        self.downl_data_buff()
        self.levelcorr = self.digitizer.rf_level_correction_get()
        self.process_data()

    def killsideband(self, onlyfft=False):
        '''
        Generates complex FFT of the data and kills the side-band.
        cleared FFT data is stored in self.cfftsig
        #Easier to kill the sidbands and a lot of Noise 
        by using two Digitizers and correlating the data.
        '''
        self.cfftsig[:] = np.fft.fft(self.cIQ)
        self.cfftsig[:] = np.fft.fftshift(self.cfftsig)  # temporarily used for bug hunting
        smid = int(len(self.cfftsig)/2) + 1
        if self.LoPos is 0:
            self.cfftsig[smid:-1] = 0.0
        else:
            self.cfftsig[0:smid] = 0.0
        if onlyfft:
            return
        # self.cIQ[:] = np.fft.ifft(np.fft.ifftshift(self.cfftsig))
        self.scaledI[:] = np.imag(self.cIQ)
        self.scaledQ[:] = np.real(self.cIQ)

    def process_data(self):
        ''' Sample the signal, calc I+j*Q theta
         and store it in the driver object
         of each trigger there are x samples... which can be averaged...
        '''
        self.scaledI[:] = np.array((np.array(self.scaledI[:])*np.power(10.0, self.levelcorr/20.0)/np.sqrt(1000)))
        self.scaledQ[:] = np.array((np.array(self.scaledQ[:])*np.power(10.0, self.levelcorr/20.0)/np.sqrt(1000)))
        self.cIQ[:] = 1j * self.scaledQ + self.scaledI
        # self.killsideband()  # Not yet working using hardware filters for now

        vI = np.zeros(1)
        vQ = np.zeros(1)
        vI2 = np.zeros(1)
        vQ2 = np.zeros(1)

        # Avg I/Q and scale data to Volt / sqrt(1Ohm)
        vI = np.mean(self.scaledI, axis=0)
        vQ = np.mean(self.scaledQ, axis=0)
        vI2 = np.mean(self.scaledI**2, axis=0)
        vQ2 = np.mean(self.scaledQ**2, axis=0)

        self.vAvgIQ = vI + 1j * vQ
        self.vAvgPow = (vI2 + vQ2)
        self.vAvgMag = np.absolute(self.vAvgIQ)
        self.vAvgPh = np.angle(self.vAvgIQ)

        # Average Magnitudes and Phases
        self.AvgMag = np.mean(np.absolute(self.cIQ))
        self.AvgPhase = np.mean(np.angle(self.cIQ))

    def set_bandwidth(self, val):
        self.digitizer.trigger_IQ_bandwidth_set(val)

    def set_sampRate(self, val):
        self.digitizer.modulation_generic_sampling_frequency_set(val)

    def checkADCOverload(self):
        if self.digitizer.check_ADCOverload():
            self.Overload = self.Overload + 1
            print 'Overload number:', self.Overload, self.name
            if self.Overload > 2:
                self.inputLvl +=1
                self.digitizer.rf_rf_input_level_set(self.inputLvl)
                print 'ajdust input level to:', self.inputLvl
            #     raise Exception('ADC overloaded 4x in a row')
        else:
            self.Overload = 0
    
    def digi_adjust_ADC(self):
         if self.ADCOverload > 2:
            self.inputLvl +=1
            self.digitizer.rf_rf_input_level_set(self.inputLvl)
            print 'ajdust input level to:', self.inputLvl
       
    def do_measurement(self, pstar):
        ''' Arms the digitizer,
        Sends a Trigger via the refered object pstar,
        downloads the data.
        '''
        self.init_trigger_buff()
        sleep(0.020)
        pstar.send_software_trigger()
        self.wait_capture_complete()
        self.get_data_complete()


if __name__ == '__main__':
    ''' Test code to see if this Driver works on its own '''
    from nirack import nit
    pstar = nit()
    lags = 30
    BW = 10e6
    lsamples = 1e5
    corrAvg = 1
    f1 = 4.799999e9
    D1 = instrument(adressDigi='3036D1', adressLo='3011D1', LoPosAB=1, LoRef=2,
           name='D1 Lags (sec)', cfreq=f1, inputlvl=-6,
           start=(-lags / BW), stop=(lags / BW), pt=(lags * 2 - 1),
           nSample=lsamples, sampFreq=BW)

    D1.do_measurement(pstar)
    print D1.cIQ
    # D1.setup_captmem()
    # D1.init_trigger()
    # pstar.send_software_trigger()
    # sleep(1)
    # D1.digitizer.get_IQ_trigger_detected()
    # D1.downl_data()
    # D1.get_Levelcorr()
    # D1.process_data()
    # #D1.set_freq(f1)