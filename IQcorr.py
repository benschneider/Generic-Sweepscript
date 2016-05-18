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
from time import time
# from tables import tb

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
        self.takeBG = False
        self.doHist2d = False
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
        self.D1.init_trigger_buff()
        self.D2.init_trigger_buff()
        sleep(0.022)
        self.pstar.send_software_trigger()

    def create_datastore_objs(self, folder, filen_0, dim_1, dim_2, dim_3):
        self.driveON.create_objs(folder, filen_0, dim_1, dim_2, dim_3, self.doHist2d)
        if self.takeBG:
            self.driveOFF.create_objs(folder, filen_0, dim_1, dim_2, dim_3, self.doHist2d)

    def data_save(self):
        self.driveON.data_save()
        if self.takeBG:
            self.driveOFF.data_save()

    def data_record(self, kk, jj, ii):
        self.driveON.data_record(kk, jj, ii)
        if self.takeBG:
            self.driveOFF.data_record(kk, jj, ii)

    def data_variables(self):
        self.driveON.data_variables()
        if self.takeBG:
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
            # t00 = time()
            self.nnnnn = 0
            self.download_data(cz)  # grab digitizer data
            # t11 = time()
            if self.takeBG:
                self.pflux.output(0)
            self.process_data()  # Process digitizer ON data
            self.driveON.add_avg()  # store ON data        
            if self.takeBG:
                self.init_trigger()  # Initiate OFF data aquisition
            # slot for calculations
            if self.takeBG:
                self.download_data(cz)  # Download OFF data
                self.pflux.output(1)
                # sleep(0.1)            
            if self.takeBG:
                self.process_data()  # Process OFF data
                self.driveOFF.add_avg()  # store OFF data
            if (cz+1) < int(self.corrAvg):
                self.init_trigger() # Initiate trigger for next average
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

class meastype(object):
    ''' This class contains the different types of measurements done:
        one where the Drive is switched off, one, where its on,
        one where a Probe signal is present at f1 one at f2... '''

    def __init__(self, D1, D2, lags, name, corrAvg):
        gc.collect()
        self.D1 = D1
        self.D2 = D2
        self.lags = lags
        self.name = name
        self.corrAvg = corrAvg
        self.data_variables()
        self.doHist2d = False  # Default is Nope
        self.bin_size = [60, 60]  # Estimated to be ok for 1e6 data points

    def create_objs(self, folder, filen_0, dim_1, dim_2, dim_3, doHist2d):
        self.doHist2d = doHist2d
        ''' Prepare Data files, where processed information will be stored '''
        nfolder = folder+filen_0+self.name+'\\'  #-> data\\subfolder\\
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
            Hname = nfolder+'Hist2d.hdf5'
            self.Hdata = storehdf5(Hname)
            self.Hdata.clev = 1  # Compression level to a minimum for speed
            self.Hdata.open_f(mode='w')  # create a new empty file
            self.create_Htables(dim_3.pt, dim_2.pt, dim_1.pt)      

    def create_Htables(self, d3pt, d2pt, d1pt):
        shape = (d3pt, d2pt, d1pt, self.bin_size[0], self.bin_size[1])
        # atom = tb.Float64Atom()  # kind of defines the file dtype def 64Float
        xyshape = (d3pt, d2pt, d1pt, 6,3)
        self.Hdata.create_dset(shape, label='I1Q1_0')
        self.Hdata.create_dset(shape, label='I2Q2_1')
        self.Hdata.create_dset(shape, label='I1I2_2')
        self.Hdata.create_dset(shape, label='Q1Q2_3')
        self.Hdata.create_dset(shape, label='I1Q2_4')
        self.Hdata.create_dset(shape, label='Q1I2_5')
        self.Hdata.create_dset(xyshape, label='XminXmaxXNum')
        self.Hdata.create_dset(xyshape, label='YminYmaxYNum')
        self.Hdata.close()
        self.Hdata.open_f()  # opens and keeps open

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
            self.make_histM(kk, jj, ii)

    def make_histM(self, kk, jj, ii):
        # t00 = time()
        # the resulting histogram matrix has a large number of zeros (sparse)
        # and can easily be compressed. Question is: how best to handle those? 
        # MAT1 = scipy.sparse.csr_matrix(matrix) ?
        # Or Pytables, as data needs to be stored on HDD in the end...
        ''' This creates a figure of the histogram at one specific point'''
        I1 = self.D1.scaledI
        Q1 = self.D1.scaledQ
        I2 = self.D2.scaledI
        Q2 = self.D2.scaledQ
        if bool(self.Hdata.h5.isopen) is False:
            self.Hdata.open_f()  # opens the file to be edited
        
        h5 = self.Hdata.h5.root
        h5.I1Q1_0[kk, jj, ii], xl, yl = np.histogram2d(I1, Q1, bins=self.bin_size)
        h5.XminXmaxXNum[kk, jj, ii, 0] = [xl[0], xl[-1], len(xl)]  # axis: Xmin Xmax XNum
        h5.YminYmaxYNum[kk, jj, ii, 0] = [yl[0], yl[-1], len(yl)]
        h5.I2Q2_1[kk, jj, ii], xl, yl = np.histogram2d(I2, Q2, bins=self.bin_size)
        h5.XminXmaxXNum[kk, jj, ii, 1] = [xl[0], xl[-1], len(xl)]
        h5.YminYmaxYNum[kk, jj, ii, 1] = [yl[0], yl[-1], len(yl)]
        h5.I1I2_2[kk, jj, ii], xl, yl = np.histogram2d(I1, I2, bins=self.bin_size)
        h5.XminXmaxXNum[kk, jj, ii, 2] = [xl[0], xl[-1], len(xl)]
        h5.YminYmaxYNum[kk, jj, ii, 2] = [yl[0], yl[-1], len(yl)]
        h5.Q1Q2_3[kk, jj, ii], xl, yl = np.histogram2d(Q1, Q2, bins=self.bin_size)
        h5.XminXmaxXNum[kk, jj, ii, 3] = [xl[0], xl[-1], len(xl)]
        h5.YminYmaxYNum[kk, jj, ii, 3] = [yl[0], yl[-1], len(yl)]
        h5.I1Q2_4[kk, jj, ii], xl, yl = np.histogram2d(I1, Q2, bins=self.bin_size)
        h5.XminXmaxXNum[kk, jj, ii, 4] = [xl[0], xl[-1], len(xl)]
        h5.YminYmaxYNum[kk, jj, ii, 4] = [yl[0], yl[-1], len(yl)]
        h5.Q1I2_5[kk, jj, ii], xl, yl = np.histogram2d(Q1, I2, bins=self.bin_size)
        h5.XminXmaxXNum[kk, jj, ii, 5] = [xl[0], xl[-1], len(xl)]
        h5.YminYmaxYNum[kk, jj, ii, 5] = [yl[0], yl[-1], len(yl)]
        # self.Hdata.close()
        # print time() - t00

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
        if self.doHist2d:
            self.Hdata.close()
