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
import os
from parsers import storehdf5

class Process():
    ''' acesses the trigger, handles the data storage, saves the data,
        acesses the procedure to calculate covariance Matrixes
    '''

    def __init__(self, D1, D2, pflux, sgen,
                 lags=20, BW=1e6, lsamples=1e4, corrAvg=1, doHist2d=False):
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
        self._takeBG = True
        self.doHist2d = doHist2d
        self.num = 0    # number of missed triggers in a row
        # Define the different measurement types here:
        self.driveON = meastype(D1, D2, lags, 'ON', self.corrAvg, doHist2d)  # Pump drive ON
        self.driveOFF = meastype(D1, D2, lags, 'OFF', self.corrAvg, doHist2d)  # Pump drive off
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
        self.D1.init_trigger_buff()
        self.D2.init_trigger_buff()
        sleep(0.022)
        self.pstar.send_software_trigger()

    def create_datastore_objs(self, folder, filen_0, dim_1, dim_2, dim_3):
        self.driveON.create_objs(folder, filen_0, dim_1, dim_2, dim_3)
        if self._takeBG:
            self.driveOFF.create_objs(folder, filen_0, dim_1, dim_2, dim_3)

    def data_save(self):
        self.driveON.data_save()
        if self._takeBG:
            self.driveOFF.data_save()

    def data_record(self, kk, jj, ii):
        self.driveON.data_record(kk, jj, ii)
        if self._takeBG:
            self.driveOFF.data_record(kk, jj, ii)

    def data_variables(self):
        self.driveON.data_variables()
        if self._takeBG:
            self.driveOFF.data_variables()

    def download_data(self, cz):
        '''This downloads data from D1 and D2,
        once downloaded, data acquisition can continue.
        At the same time D1 and D2 data can be processed
        '''
        self.D1.get_Levelcorr()  # update level correction value
        self.D2.get_Levelcorr()
        self.D1.downl_data_buff()
        self.D2.downl_data_buff()
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

    def process_data(self):
        self.D1.process_data()  # process data, while measurement is running
        self.D2.process_data()       

    def avg_corr(self):
        '''init_trigger() should have run once before. This is the averaging,
        processing and measurement main loop '''

        for cz in range(int(self.corrAvg)):
            # Download ON data
            self.nnnnn = 0
            self.download_data(cz)  
            
            # Initiate OFF data aquisition
            if self._takeBG:
                self.pflux.output(0)
                # print 'output off'
                sleep(0.1)
                self.init_trigger()  # Initiate next measurement set

            # Process digitizer ON data
            self.process_data() 
            self.driveON.add_avg()  # store ON data

            # Download OFF data
            if self._takeBG:
                self.download_data(cz)  # Download data from digitizer

                #After download Drive can be switched ON again
                self.pflux.output(1)
                # print 'output on'
                sleep(0.1)

            # Initiate trigger for next average
            if (cz+1) < int(self.corrAvg):             
                self.init_trigger()  
                # self.init_trigger_wcheck(True, True)  # Refcheck (Y), Trigcheck (N)

            # Process OFF data
            if self._takeBG:                
                self.process_data()  # Processing digitizer data                
                self.driveOFF.add_avg()  # store OFF data

                

    def full_aqc(self, kk, jj, ii):
        ''' This it the function to run
        1. clears variables
        2. triggers and averages correlation
        3. calulates correlations
        4. record data to memory
        still needs data_save to be run to save the data file in the end.
        '''
        self.data_variables()  # 1 clears temp data
        # self.init_trigger()  # 2
        # self.init_trigger_wcheck(True, False)  # Refcheck (Y), Trigcheck (N)
        self.D1.checkADCOverload()
        self.D2.checkADCOverload()
        self.avg_corr()  # 3
        self.data_record(kk, jj, ii)  # 4


class meastype(object):
    ''' This class contains the different types of measurements done:
        one where the Drive is switched off, one, where its on,
        one where a Probe signal is present at f1 one at f2... '''

    def __init__(self, D1, D2, lags, name, corrAvg, doHist2d):
        gc.collect()
        self.D1 = D1
        self.D2 = D2
        self.lags = lags
        self.name = name
        self.corrAvg = corrAvg
        self.data_variables()
        self.doHist2d = doHist2d
        #if doHist2d:
        #    self.setup_Hist2d()

    def create_objs(self, folder, filen_0, dim_1, dim_2, dim_3):
        ''' Prepare Data files, where processed information will be stored '''
        nfolder = folder+filen_0+self.name+'\\'
        if not os.path.exists(nfolder):
            os.makedirs(nfolder)
        self.DSP_PD1 = DataStoreSP(nfolder, filen_0, dim_1, dim_2, dim_3, 'D1Pow', cname='Watts')
        self.DSP_PD2 = DataStoreSP(nfolder, filen_0, dim_1, dim_2, dim_3, 'D2Pow', cname='Watts')
        self.DSP_LD1 = DataStoreSP(nfolder, filen_0, dim_1, dim_2, dim_3, 'D1LevCorr', cname='LvLCorr')
        self.DSP_LD2 = DataStoreSP(nfolder, filen_0, dim_1, dim_2, dim_3, 'D2LevCorr', cname='LvLCorr')
        self.DS2vD1 = DataStore2Vec(nfolder, filen_0, dim_1, dim_2, dim_3, 'D1vAvg')
        self.DS2vD2 = DataStore2Vec(nfolder, filen_0, dim_1, dim_2, dim_3, 'D2vAvg')
        self.DS2mD1 = DataStore2Vec(nfolder, filen_0, dim_1, dim_2, dim_3, 'D1mAvg')
        self.DS2mD2 = DataStore2Vec(nfolder, filen_0, dim_1, dim_2, dim_3, 'D2mAvg')
        self.DS11 = DataStore11Vec(nfolder, filen_0, dim_1, dim_2, self.D1, 'CovMat')
        # Cov Matrix D1 has dim_3 info
        if self.doHist2d:
            '''If doHist2d is set to True, a hdf5 file will be created
            to save the histogram data.'''
            Hname = folder+'Hist2d.hdf5'
            self.Hdata = storehdf5(Hname)
            self.Hdata.open_f(mode='w')  # create a new empty file
            
    def data_variables(self):
        ''' create empty variables to store average values '''
        self.D1Ma = np.float(0.0)
        self.D1Pha = np.float(0.0)
        self.D1vMa = np.float(0.0)
        self.D1vPha = np.float(0.0)
        self.D2vMa = np.float(0.0)
        self.D2vPha = np.float(0.0)
        self.D2Ma = np.float(0.0)
        self.D2Pha = np.float(0.0)
        self.covAvgMat = np.zeros([12, self.lags * 2 - 1])  # For one particular ii, jj, kk
        self.D1aPow = np.float(0.0)
        self.D2aPow = np.float(0.0)

    def add_avg(self):
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

    def data_record(self, kk, jj, ii):
        '''This loads the new information into the matices'''
        corrAvg = np.float(self.corrAvg)
        self.DS11.record_data(self.covAvgMat / corrAvg, kk, jj, ii)
        self.DSP_PD1.record_data((self.D1aPow / corrAvg), kk, jj, ii)
        self.DSP_PD2.record_data((self.D2aPow / corrAvg), kk, jj, ii)
        self.DSP_LD1.record_data(self.D1.levelcorr, kk, jj, ii)
        self.DSP_LD2.record_data(self.D2.levelcorr, kk, jj, ii)
        self.DS2mD2.record_data(self.D2Ma / corrAvg, self.D2Pha / corrAvg, kk, jj, ii)
        self.DS2mD1.record_data(self.D1Ma / corrAvg, self.D1Pha / corrAvg, kk, jj, ii)
        self.DS2vD1.record_data(self.D1vMa / corrAvg, self.D1vPha / corrAvg, kk, jj, ii)
        self.DS2vD2.record_data(self.D2vMa / corrAvg, self.D2vPha / corrAvg, kk, jj, ii)
        if self.doHist2d:
            self.make_densityM(kk, jj, ii)

    def make_densityM(self, kk, jj, ii):
        ''' This creates a figure of the histogram at one specific point'''
        I1 = self.D1.scaledI
        Q1 = self.D1.scaledQ
        I2 = self.D2.scaledI
        Q2 = self.D2.scaledQ
        histI1Q1, xl, yl = np.histogram2d(I1, Q1)
        histI2Q2, xl, yl = np.histogram2d(I2, Q2)
        histI1I2, xl, yl = np.histogram2d(I1, I2)
        histQ1Q2, xl, yl = np.histogram2d(Q1, Q2)
        histI1Q2, xl, yl = np.histogram2d(I1, Q2)
        histQ1I2, xl, yl = np.histogram2d(Q1, I2)

    def data_save(self):
        '''save the data in question, at the moment these functions rewrite the matrix eachtime,
        instead of just appending to it.'''
        self.DS11.save_data()
        self.DSP_PD1.save_data()
        self.DSP_PD2.save_data()
        self.DSP_LD1.save_data()
        self.DSP_LD2.save_data()
        self.DS2mD2.save_data()
        self.DS2mD1.save_data()
        self.DS2vD1.save_data()
        self.DS2vD2.save_data()
