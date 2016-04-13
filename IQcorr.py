'''
This file containts the procedures for cross correlations using 2 Aeroflex
Digitizers, a signal source and

31/03/2016
- B
'''
import numpy as np
from time import sleep  # , time
from DataStorer import DataStoreSP, DataStore2Vec, DataStore11Vec
from nirack import nit  # load PXI trigger
from covfunc import getCovMatrix  # Function to calculate Covarianve Matrixes
import gc  # Garbage memory collection

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
        self.D1w = self.D1.Digitizer
        self.D2w = self.D2.Digitizer
        self.sgen = sgen
        self.pflux = pflux
        self.pstar = nit()
        self.corrAvg = corrAvg
        self.pstar.send_many_triggers(10)
        self.data_variables()

    def data_variables(self):
        ''' create empty variables to store average values '''
        gc.collect()
        self.D1Ma = np.float(0.0)
        self.D1Pha = np.float(0.0)
        self.D1vMa = np.float(0.0)
        self.D1vPha = np.float(0.0)
        self.D2vMa = np.float(0.0)
        self.D2vPha = np.float(0.0)
        self.D2Ma = np.float(0.0)
        self.D2Pha = np.float(0.0)
        self.covAvgMat = np.zeros([11, self.lags * 2 - 1])
        self.D1aPow = np.float(0.0)
        self.D2aPow = np.float(0.0)

    def create_datastore_objs(self, folder, filen_0, dim_1, dim_2, dim_3):
        ''' Prepare Digitizer data files '''
        self.DS11 = DataStore11Vec(
            folder, filen_0, dim_1, dim_2, self.D1, 'CovMat')
        self.DSP_PD1 = DataStoreSP(
            folder, filen_0, dim_1, dim_2, dim_3,
            label='D1Pow', cname='Watts')
        self.DSP_LD1 = DataStoreSP(
            folder, filen_0, dim_1, dim_2, dim_3,
            label='D1LevCorr', cname='LvLCorr')
        self.DS2vD1 = DataStore2Vec(
            folder, filen_0, dim_1, dim_2, dim_3, 'D1vAvg')
        self.DS2mD1 = DataStore2Vec(
            folder, filen_0, dim_1, dim_2, dim_3, 'D1mAvg')
        self.DSP_PD2 = DataStoreSP(
            folder, filen_0, dim_1, dim_2, dim_3,
            label='D2Pow', cname='Watts')
        self.DSP_LD2 = DataStoreSP(
            folder, filen_0, dim_1, dim_2, dim_3,
            label='D2LevCorr', cname='LvLCorr')
        self.DS2vD2 = DataStore2Vec(
            folder, filen_0, dim_1, dim_2, dim_3, 'D2vAvg')
        self.DS2mD2 = DataStore2Vec(
            folder, filen_0, dim_1, dim_2, dim_3, 'D2mAvg')

    def setup_D1D2(self):
        '''
        Trigger on PXI-Star
        Enable pipelining
        '''
        # self.D1w.trigger_source_set(8)
        # self.D2w.trigger_source_set(8)
        # self.D1w.set_piplining(1)
        # self.D2w.set_piplining(1)

    def init_trigger(self):
        self.D1.init_trigger_buff()
        self.D2.init_trigger_buff()
        sleep(0.01)
        self.pstar.send_software_trigger()
        sleep(0.02)
        det1 = self.D1.digitizer.get_trigger_detected()
        det2 = self.D2.digitizer.get_trigger_detected()
        if det1 is False:
            raise Exception('Trigger1 Not Detected')
        if det2 is False:
            raise Exception('Trigger2 Not Detected')

    def data_grab(self):
        while True:
            try:
                self.D1.downl_data_buff()
                self.D2.downl_data_buff()
            except Exception, e:
                # bug! '==' not same as 'is' here ->
                if str(e) == 'Reclaim timeout':
                    sleep(0.1)
                    continue
                else:
                    raise e
            break

    def data_record(self, kk, jj, ii):

        corrAvg = np.float(self.corrAvg)
        self.D12_corr_average()
        self.DS11.record_data(self.covAvgMat / corrAvg, kk, jj, ii)
        self.DSP_PD1.record_data((self.D1aPow / corrAvg), kk, jj, ii)
        self.DSP_PD2.record_data((self.D2aPow / corrAvg), kk, jj, ii)
        self.DSP_LD1.record_data(self.D1.levelcorr, kk, jj, ii)
        self.DSP_LD2.record_data(self.D2.levelcorr, kk, jj, ii)
        self.DS2mD2.record_data(
            self.D2Ma/corrAvg, self.D2Pha/corrAvg, kk, jj, ii)
        self.DS2mD1.record_data(
            self.D1Ma/corrAvg, self.D1Pha/corrAvg, kk, jj, ii)
        self.DS2vD1.record_data(
            self.D1vMa/corrAvg, self.D1vPha/corrAvg, kk, jj, ii)
        self.DS2vD2.record_data(
            self.D2vMa/corrAvg, self.D2vPha/corrAvg, kk, jj, ii)

    def data_save(self):
        self.DS11.save_data()
        self.DSP_PD1.save_data()
        self.DSP_PD2.save_data()
        self.DS.save_data()
        self.DSP_LD1.save_data()
        self.DSP_LD2.save_data()
        self.DS2mD2.save_data()
        self.DS2mD1.save_data()
        self.DS2vD1.save_data()
        self.DS2vD2.save_data()

    def avg_corr(self):
        '''assumes init trigger was run once before'''
        for cz in range(int(self.corrAvg)):
            self.D1.get_Levelcorr()  # update level correction value
            self.D2.get_Levelcorr()
            self.data_grab()
            if (cz + 1) < self.corrAvg:
                self.init_trigger()

            self.D1.process_data()
            self.D2.process_data()
            # Digitizer 1 Values
            self.D1Ma += self.D1.AvgMag
            self.D1Pha += self.D1.AvgPhase
            self.D1vMa += self.D1.vAvgMag
            self.D1vPha += self.D1.vAvgPh
            self.D1aPow += self.D1.vAvgPow
            # Digitizer 2 Values
            self.D2Ma += self.D2.AvgMag
            self.D2Pha += self.D2.AvgPhase
            self.D2vMa += self.D2.vAvgMag
            self.D2vPha += self.D2.vAvgPh
            self.D2aPow += self.D2.vAvgPow

            self.covAvgMat += getCovMatrix(self.D1.scaledI, self.D1.scaledQ,
                                           self.D2.scaledI, self.D2.scaledQ,
                                           self.lags)

    def full_aqc(self):
        # former record vna data
        ''' This it the function to run
        1. clears variables
        2. triggers and averages correlation
        3. calulates correlations
        4. record data to memory

        still needs data_save to be run to save the data file in the end.
        '''
        self.data_variables()  # 1
        self.init_trigger()  # 2
        self.avg_corr()  # 3
        self.data_record()  # 4

    def get_cov_matrix(self):
        pass

    def get_g2(self):
        pass
