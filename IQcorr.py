'''
This file containts the procedures for cross correlations using 2 Aeroflex
Digitizers, a signal source and

31/03/2016
- B
'''
import numpy as np
from time import sleep  # , time
# from DataStorer import DataStoreSP, DataStore2Vec, DataStore11Vec
from nirack import nit  # load PXI trigger
# import gc  # Garbage memory collection
# import os
# from parsers import storehdf5
from time import time
# from tables import tb
from D1D2meastype import meastype


class Process():
    ''' acesses the trigger, handles the data storage, saves the data,
        acesses the procedure to calculate covariance Matrixes
    '''

    def __init__(self, D1, D2, pflux, sgen,
                 lags=20, BW=1e6, lsamples=1e4, corrAvg=1):
        '''
        D1, D2, pgen, pstar
        D1,2: Digitizer 1,2 object
        pgen: Flux Pump (Anritzu pulsed mode)
        sgen: Signal Generator
        pstar: Trigger source (PXI-Star)
        '''
        # Make some object references
        self.D1 = D1
        self.D2 = D2
        self.D1w = self.D1.digitizer
        self.D2w = self.D2.digitizer
        self.sgen = sgen
        self.pflux = pflux
        self.pstar = nit()
        self.corrAvg = corrAvg
        self.lags = lags
        self.BW = BW
        self.lsamples = lsamples
        self.pstar.send_many_triggers(10)
        self.doBG = False
        self.doHist2d = False
        self.doRaw = False
        self.num = 0    # number of missed triggers in a row
        # Define the different measurement types here:
        self.driveON = meastype(D1, D2, lags, 'ON', self.corrAvg)  # Pump drive ON
        self.driveOFF = meastype(D1, D2, lags, 'OFF', self.corrAvg)  # Pump drive off
        # self.driveOFFf1 = meastype(D1, D2, lags, 'f1')  # Pump drive off & Probe Signal f1
        # self.driveOFFf2 = meastype(D1, D2, lags, 'f2')  # Pump drive off & Probe Signal f2

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
        self.driveON.create_objs(folder, filen_0, dim_1, dim_2, dim_3, self.doHist2d, self.doRaw)
        if self.doBG:
            self.driveOFF.create_objs(folder, filen_0, dim_1, dim_2, dim_3, self.doHist2d, self.doRaw)

    def data_save(self):
        self.driveON.data_save()
        if self.doBG:
            self.driveOFF.data_save()

    def data_record(self, kk, jj, ii):
        self.driveON.data_record(kk, jj, ii)
        if self.doBG:
            self.driveOFF.data_record(kk, jj, ii)

    def data_variables(self):
        self.driveON.data_variables()
        if self.doBG:
            self.driveOFF.data_variables()

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
            print 'remeasure this: '+str(self.nnnnn)
            if self.nnnnn > 7:
                raise Exception('Continuous ADC-overflow')
            self.init_trigger()
            self.download_data(cz)

    def avg_corr(self):
        '''init_trigger() should have run once before. This is the averaging,
        processing and measurement main loop '''

        for cz in range(int(self.corrAvg)):
            # Download ON data
            # t00 = time()
            self.nnnnn = 0
            self.download_data(cz)  # grab digitizer data
            # t11 = time()
            if self.doBG:
                self.pflux.output(0)
            self.driveON.process_data()  # process and store ON data
            if self.doBG:
                self.init_trigger()  # Initiate OFF data aquisition
            # slot for calculations
            if self.doBG:
                self.download_data(cz)  # Download OFF data
                self.pflux.output(1)
                # sleep(0.1)
            if self.doBG:
                self.driveOFF.process_data()  # process and store OFF data
            if (cz+1) < int(self.corrAvg):
                self.init_trigger()  # Initiate trigger for next average
            # t22 = time()
            # print  'download ',t11-t00, 'rest ',t22-t11,

    def full_aqc(self, kk, jj, ii):
        ''' This it the function to run
        1. clears variables
        2. triggers and averages correlation
        3. calulates correlations
        4. record data to memory
        still needs data_save to be run to save the data file in the end.
        '''
        # t33 = time()
        self.data_variables()  # 1 clears temp data
        # self.init_trigger()  # 2
        # self.init_trigger_wcheck(True, False)  # Refcheck (Y), Trigcheck (N)
        self.D1.checkADCOverload()
        self.D2.checkADCOverload()
        self.avg_corr()  # 3
        self.data_record(kk, jj, ii)  # 4 (This is fast !)
        # print 'D12 aq ', time()-t33
