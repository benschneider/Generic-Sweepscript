from time import sleep  # , time
import numpy as np
import sys
import PXIDigitizer_wrapper

# Digitizer.boot_instrument('PXI7::15::INSTR', 'PXI6::10::INSTR')
# Digitizer.boot_instrument('3011D1', '3036D1')


class instrument():
    '''Upon start, creates connection to Digitizer and Local oscillator
        this driver only contains some rudimentary functions to run
        the PXI-Aeroflex 3036 Digitizer.
    '''

    def __init__(self, aDigi='3036D1', aLo='3011D1', name='D',
                 start=0, stop=0, pt=1, sstep=20e-3, stime=1e-3):
        self.adressDigi = aDigi
        self.Overload = 3  # to test the overload code
        self.adressLo = aLo
        self.name = name
        self.start = start
        self.stop = stop
        self.pt = pt
        self.lin = np.linspace(self.start, self.stop, self.pt)
        self.digitizer = PXIDigitizer_wrapper.afDigitizer_BS()
        self.digitizer.create_object()
        self.digitizer.boot_instrument(aLo, aDigi)
        self.prep_data()

    def set_settings(self):
        pass

    def prep_data(self):
        self.cAvgSignal = None
        self.cAvgSignal2 = None
        self.cTrace = None
        self.vPTrace = None
        self.vPowerMeanUnAvg = None
        self.MeanMag = None
        self.MeanPhas = None
        self.vMeanUnAvg = None
        self.cRaw = None
        self.dPower = None

    def set_freq(self, var_1):
        sleep(0.01)
        self.var_1 = var_1
        print var_1

    def set_inputLevel(self, value):
        pass

    def get_IQ(self):
        return self.var_1

    def get_Levelcorr(self):
        return (np.random.rand(1)*10-5)*2

    def get_Vcorr(self):
        pass

    def set_bandwidth(self, val):
        pass

    def get_bandwidth(self):
        return 0

    def set_sampRater(self, val):
        self.digitizer.modulation_generic_sampling_frequency_set(value)

    # Check if the ADC overloaded and if it was put the max input level
    # to +30dBm and raise an error
    def checkADCOverload(self):
        if self.digitizer.check_ADCOverload():
            self.Overload = self.Overload + 1
            sleep(0.2)
            if self.Overload > 3:
                self.digitizer.rf_rf_input_level_set(30)
                print 'ADC overloaded 3x in a row', sys.exc_info()[0]
                raise
                # raise InstrumentDriver.CommunicationError('ADC overloaded hence the measurement is stopped and the max input level on the digitizer is put to +30 dBm')
        else:
            self.Overload = 0

