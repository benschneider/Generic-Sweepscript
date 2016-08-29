'''
This file containts the procedures for cross correlations using 2 Aeroflex
Digitizers, a signal source and

This is designed for the use with a Hybrid coupler
Measure procedure is as follows:


15/07/2016
- B
'''
from time import sleep  # , time
from nirack import nit  # load PXI trigger
from D1D2meastype import meastype


class Process():
    ''' acesses the trigger, handles the data storage, saves the data,
        acesses the procedure to calculate covariance Matrixes
    '''

    def __init__(self, D1, D2, pflux, sgen, lags=20,
                 BW=1e6, lsamples=1e4,
                 mTypeNames=('ON12', 'ON11', 'ON21', 'ON22', 'OFF21', 'OFF12'), corrAvg=1):
        '''
        D1, D2, pgen, pstar
        D1,2: Digitizer 1,2 object
        pgen: Flux Pump (Anritzu pulsed mode)
        sgen: Signal Generator
        pstar: Trigger source (PXI-Star)
        '''
        self.D1 = D1
        self.D2 = D2
        self.f1 = D1.freq
        self.f2 = D2.freq
        self.D1w = self.D1.digitizer
        self.D2w = self.D2.digitizer
        self.sgen = sgen
        self.pflux = pflux
        self.pstar = nit()
        self.corrAvg = corrAvg
        self.lags = lags
        self.BW = BW
        self.mTypeNames = mTypeNames
        self.mTypes = {}
        self.lsamples = lsamples
        self.pstar.send_many_triggers(10)
        self.doBG = False
        self.doHist2d = False
        self.doRaw = False
        self.doCorrel = True
        self.num = 0    # number of missed triggers in a row
        for mName in mTypeNames:
            self.mTypes[mName] = meastype(D1, D2, lags, mName, self.corrAvg)

    def init_trigger_wcheck(self, Refcheck=True, Trigcheck=False):
        if Refcheck is True:
            ref1 = bool(self.D1w.ref_is_locked())
            ref2 = bool(self.D2w.ref_is_locked())
            if (ref1 and ref2):
                self.init_trigger()
                if Trigcheck:
                    sleep(0.017)
                    self.confirm_Trigger(Refcheck, Trigcheck)

            else:
                print ref1, ref2
                print 'No reference lock! waiting..'
                sleep(0.2)
                self.init_trigger_wcheck(Refcheck, Trigcheck)

    def confirm_Trigger(self, Refcheck, Trigcheck):
        det1 = self.D1.digitizer.get_trigger_detected()
        det2 = self.D2.digitizer.get_trigger_detected()
        if det1 is False:
            self.num += 1
            sleep(0.1)
            self.init_trigger_wcheck(Refcheck, Trigcheck)
            if self.num > 3:
                raise Exception('Trigger1 Not Detected 3x')
        if det2 is False:
            self.num += 1
            sleep(0.1)
            self.init_trigger_wcheck(Refcheck, Trigcheck)
            if self.num > 3:
                raise Exception('Trigger2 Not Detected 3x')
        self.num = 0

    def init_trigger(self):
        self.D1.init_trigger()
        self.D2.init_trigger()
        sleep(0.025)
        self.pstar.send_software_trigger()

    def create_datastore_objs(self, folder, filen_0, dim_1, dim_2, dim_3):
        for mType in self.mTypes:
            self.mTypes[mType].create_objs(folder, filen_0, dim_1, dim_2, dim_3,
                                           self.doHist2d, self.doRaw, self.doCorrel)

    def data_save(self):
        for mType in self.mTypes:
            self.mTypes[mType].data_save()

    def data_record(self, kk, jj, ii):
        for mType in self.mTypes:
            self.mTypes[mType].data_record(kk, jj, ii)

    def data_variables(self):
        for mType in self.mTypes:
            self.mTypes[mType].data_variables()

    def download_data(self, cz):
        '''This downloads data from D1 and D2,
        once downloaded, data acquisition can continue.
        At the same time D1 and D2 data can be processed
        '''
        self.D1.get_Levelcorr()  # update level correction value
        self.D2.get_Levelcorr()
        self.D1.downl_data()
        self.D2.downl_data()
        if (self.D1.ADCFAIL or self.D2.ADCFAIL):
            print 'Remeasure --'
            self.init_trigger()
            self.D1.ADCFAIL = False
            self.D2.ADCFAIL = False
            self.download_data(cz)
        elif (bool(self.D1.ADCoverflow) or bool(self.D1.ADCoverflow)):
            self.nnnnn += 1
            print 'remeasure this: ' + str(self.nnnnn)
            if self.nnnnn > 7:
                raise Exception('Continuous ADC-overflow')
            self.init_trigger()
            self.download_data(cz)

    def dDsFiT(self, f1, f2, cz, drive=1):
        ''' Grab old Data set new settings and initiate trigger'''
        self.download_data(cz)  # ['ON12']
        self.pflux.output(drive)
        self.D1.set_freq(f1)
        self.D2.set_freq(f2)
        sleep(0.1)  # Wait for Digitizer settings to be complete
        self.init_trigger()

    def avg_corr(self):
        '''init_trigger() should have run once before. This is the averaging,
        processing and measurement main loop '''
        for cz in range(int(self.corrAvg)):
            # 'ON12','ON11','ON21','ON22','OFF21','OFF12'
            # Download ON data
            self.nnnnn = 0
            self.dDsFiT(self.f1, self.f1, cz)  # Get Prev data update settings
            self.mTypes['ON12'].process_data()  # process and store ON data
            self.dDsFiT(self.f2, self.f1, cz)
            self.mTypes['ON11'].process_data()
            self.dDsFiT(self.f2, self.f2, cz)
            self.mTypes['ON21'].process_data()
            self.dDsFiT(self.f2, self.f1, cz, drive=0)
            self.mTypes['ON22'].process_data()
            self.dDsFiT(self.f1, self.f2, cz, drive=0)
            self.mTypes['OFF21'].process_data()
            self.download_data(cz)  # ['OFF12']
            self.pflux.output(1)  # Drive ON
            self.mTypes['OFF12'].process_data()
            if (cz + 1) < int(self.corrAvg):
                self.init_trigger()  # Initiate trigger for next average

    def full_aqc(self, kk, jj, ii):
        ''' This it the function to run
        1. clears variables
        2. triggers and averages correlation
        3. calulates correlations
        4. record data to memory
        still needs data_save to be run to save the data file in the end.
        '''
        self.data_variables()  # 1 clears temp data
        self.D1.checkADCOverload()
        self.D2.checkADCOverload()
        self.avg_corr()  # 3
        self.data_record(kk, jj, ii)  # 4 (This is fast !)

if __name__ == '__main__':
    D1 = 'D1'
    D2 = 'D2'
    mTypeNames = ('ON12', 'ON11', 'ON21', 'ON22', 'OFF21', 'OFF12')
    test0 = Process(
        D1=D1,
        D2=D2,
        pflux=None,
        sgen=None,
        lags=10,
        BW=1e5,
        lsamples=1e3,
        mTypeNames=mTypeNames)
