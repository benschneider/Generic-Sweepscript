import gc
import numpy as np
from DataStorer import DataStoreSP, DataStore2Vec, DataStore11Vec
import os
from parsers import storehdf5
from covfunc import getCovMatrix  # Function to calculate Covarianve Matrixes


class meastype(object):
    ''' This class contains the different types of measurements done:
        one where the Drive is switched off, one, where its on,
        one where a Probe signal is present at f1 one at f2... '''

    def __init__(self, D1, D2, lags, name, corrAvg):
        gc.collect()
        self.D1 = D1
        self.D2 = D2
        self.nSamples = D1.nSamples
        self.lags = lags
        self.name = name
        self.corrAvg = corrAvg
        self.doHist2d = False  # Default is Nope
        self.doRaw = False
        self.doCorrel = True
        self.bin_size = [150, 150]  # Estimated to be ok for 1e6 data points
        self.data_variables()

    def create_objs(self, folder, filen_0, dim_1, dim_2, dim_3, doHist2d, doRaw, doCorrel=True):
        ''' Prepare Data files, where processed information will be stored '''
        self.doHist2d = doHist2d
        self.doRaw = doRaw
        self.doCorrel = doCorrel
        nfolder = folder + filen_0 + self.name + '\\'  # -> data\\subfolder\\
        self.nfolder = nfolder
        if not os.path.exists(nfolder):
            os.makedirs(nfolder)
        self.DSP_PD1 = DataStoreSP(nfolder, filen_0, dim_1, dim_2, dim_3, 'D1Pow', cname='Watts')
        self.DSP_PD2 = DataStoreSP(nfolder, filen_0, dim_1, dim_2, dim_3, 'D2Pow', cname='Watts')
        self.DSP_LD1 = DataStoreSP(nfolder, filen_0, dim_1, dim_2, dim_3, 'D1LevCor', cname='LC')
        self.DSP_LD2 = DataStoreSP(nfolder, filen_0, dim_1, dim_2, dim_3, 'D2LevCor', cname='LC')
        self.DS2vD1 = DataStore2Vec(nfolder, filen_0, dim_1, dim_2, dim_3, 'D1vAvg')
        self.DS2vD2 = DataStore2Vec(nfolder, filen_0, dim_1, dim_2, dim_3, 'D2vAvg')
        self.DS2mD1 = DataStore2Vec(nfolder, filen_0, dim_1, dim_2, dim_3, 'D1mAvg')
        self.DS2mD2 = DataStore2Vec(nfolder, filen_0, dim_1, dim_2, dim_3, 'D2mAvg')
        if self.doCorrel:
            self.DS11 = DataStore11Vec(nfolder, filen_0, dim_1, dim_2, self.D1, 'CovMat')
            # Cov Matrix D1 has dim_3 info

        if self.doHist2d:
            '''If doHist2d is set to True, a hdf5 file will be created
            to save the histogram data.'''
            Hname = nfolder+'Hist2d'+self.name+'.hdf5'
            self.Hdata = storehdf5(Hname)
            self.Hdata.clev = 1  # Compression level to a minimum for speed
            self.Hdata.open_f(mode='w')  # create a new empty file
            self.create_Htables(dim_3.pt, dim_2.pt, dim_1.pt)
        if self.doRaw:
            Rname = nfolder+'Raw'+self.name+'.hdf5'
            self.Rdata = storehdf5(Rname)
            self.Rdata.clev = 1  # Compression level to a minimum for speed
            self.Rdata.open_f(mode='w')  # create a new empty file
            self.create_Rtables(dim_3.pt, dim_2.pt, dim_1.pt)

    def create_Htables(self, d3pt, d2pt, d1pt):
        shape = (d3pt, d2pt, d1pt, self.bin_size[0], self.bin_size[1])
        # atom = tb.Float64Atom()  # kind of defines the file dtype def 64Float
        xyshape = (d3pt, d2pt, d1pt, 6, 3)
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

    def create_Rtables(self, d3pt, d2pt, d1pt):
        es = d3pt*d2pt*d1pt
        self.Rdata.create_dset32((0, 4, self.nSamples), label='D12raw', esize=es)
        self.Rdata.create_dset32((0, 3), label='ijk', esize=es)
        self.Rdata.create_dset32((0, 2), label='D12freq', esize=es)
        self.Rdata.close()
        self.Rdata.open_f()  # opens and keeps open

    def process_data(self):
        self.D1.process_data()  # process data, while measurement is running
        self.D2.process_data()
        self.add_avg()
        if self.doHist2d:
            self.calculate_histograms()
        if self.doRaw:
            self.record_raw()  # just records the raw data without coordinates

    def record_raw(self):
        ''' Records raw IQ data without the sweep coordinates'''
        if bool(self.Rdata.h5.isopen) is False:
            self.Rdata.open_f()  # opens the file to be edited
        r5 = self.Rdata.h5.root
        r5.D12raw.append([[self.D1.scaledI, self.D1.scaledQ, self.D2.scaledI, self.D2.scaledQ]])
        r5.D12raw.flush()
        self.Rdata.h5.flush()

    def calculate_histograms(self):
        I1 = self.D1.scaledI
        Q1 = self.D1.scaledQ
        I2 = self.D2.scaledI
        Q2 = self.D2.scaledQ
        self.hmap[0], self.xl[0], self.yl[0] = np.histogram2d(I1, Q1, bins=self.bin_size)
        self.hmap[1], self.xl[1], self.yl[0] = np.histogram2d(I2, Q2, bins=self.bin_size)
        self.hmap[2], self.xl[2], self.yl[2] = np.histogram2d(I1, I2, bins=self.bin_size)
        self.hmap[3], self.xl[3], self.yl[3] = np.histogram2d(Q1, Q2, bins=self.bin_size)
        self.hmap[4], self.xl[4], self.yl[4] = np.histogram2d(I1, Q2, bins=self.bin_size)
        self.hmap[5], self.xl[5], self.yl[5] = np.histogram2d(Q1, I2, bins=self.bin_size)

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
        self.covAvgMat = np.zeros([14, self.lags * 2 + 1])  # For one particular ii, jj, kk
        self.D1aPow = np.float(0.0)
        self.D2aPow = np.float(0.0)
        if self.doHist2d:
            self.hmap = np.zeros([6, self.bin_size[0], self.bin_size[1]])
            self.xl = np.zeros([6, self.bin_size[0]+1])
            self.yl = np.zeros([6, self.bin_size[1]+1])
        if self.doRaw:
            self.ijk = np.zeros([1, 3])
            self.D12freq = np.zeros([1, 2])

    def add_avg(self):
        self.D1Ma += self.D1.AvgMag
        self.D1Pha += self.D1.AvgPhase
        self.D1vMa += self.D1.vAvgMag
        self.D1vPha += self.D1.vAvgPh
        self.D1aPow += self.D1.vAvgPow
        self.D2Ma += self.D2.AvgMag
        self.D2Pha += self.D2.AvgPhase
        self.D2vMa += self.D2.vAvgMag
        self.D2vPha += self.D2.vAvgPh
        self.D2aPow += self.D2.vAvgPow
        if self.doCorrel:
            self.covAvgMat += getCovMatrix(self.D1.scaledI, self.D1.scaledQ,
                                           self.D2.scaledI, self.D2.scaledQ,
                                           self.lags)

    def data_record(self, kk, jj, ii):
        '''This loads the new information into the matices'''
        corrAvg = np.float(self.corrAvg)
        self.DSP_PD1.record_data((self.D1aPow / corrAvg), kk, jj, ii)
        self.DSP_PD2.record_data((self.D2aPow / corrAvg), kk, jj, ii)
        self.DSP_LD1.record_data(self.D1.levelcorr, kk, jj, ii)
        self.DSP_LD2.record_data(self.D2.levelcorr, kk, jj, ii)
        self.DS2mD2.record_data(self.D2Ma / corrAvg, self.D2Pha / corrAvg, kk, jj, ii)
        self.DS2mD1.record_data(self.D1Ma / corrAvg, self.D1Pha / corrAvg, kk, jj, ii)
        self.DS2vD1.record_data(self.D1vMa / corrAvg, self.D1vPha / corrAvg, kk, jj, ii)
        self.DS2vD2.record_data(self.D2vMa / corrAvg, self.D2vPha / corrAvg, kk, jj, ii)
        if self.doCorrel:
            self.DS11.record_data(self.covAvgMat / corrAvg, kk, jj, ii)
        if self.doHist2d:
            self.record_histM(kk, jj, ii)
        if self.doRaw:
            if bool(self.Rdata.h5.isopen) is False:
                self.Rdata.open_f()  # opens the file to be edited
            self.ijk[0, 0] = ii
            self.ijk[0, 1] = jj
            self.ijk[0, 2] = kk
            self.D12freq[0, 0] = self.D1.freq/1e9
            self.D12freq[0, 1] = self.D2.freq/1e9
            self.Rdata.h5.root.ijk.append(self.ijk)
            self.Rdata.h5.root.D12freq.append(self.D12freq)
            self.Rdata.h5.flush()

    def record_histM(self, kk, jj, ii):
        ''' This creates a figure of the histogram at one specific point'''
        if bool(self.Hdata.h5.isopen) is False:
            self.Hdata.open_f()  # opens the file to be edited
        h5 = self.Hdata.h5.root
        for i in range(self.xl.shape[0]):
            h5.XminXmaxXNum[kk, jj, ii, i] = [self.xl[i][0], self.xl[i][-1], len(self.xl[i])]
            h5.YminYmaxYNum[kk, jj, ii, i] = [self.yl[i][0], self.yl[i][-1], len(self.yl[i])]
        h5.I1Q1_0[kk, jj, ii] = self.hmap[0]
        h5.I2Q2_1[kk, jj, ii] = self.hmap[1]
        h5.I1I2_2[kk, jj, ii] = self.hmap[2]
        h5.Q1Q2_3[kk, jj, ii] = self.hmap[3]
        h5.I1Q2_4[kk, jj, ii] = self.hmap[4]
        h5.Q1I2_5[kk, jj, ii] = self.hmap[5]
        self.Hdata.h5.flush()

    def data_save(self):
        '''save the data in question, at the moment these functions rewrite the matrix eachtime,
        instead of just appending to it.'''
        self.DSP_PD1.save_data()
        self.DSP_PD2.save_data()
        self.DSP_LD1.save_data()
        self.DSP_LD2.save_data()
        self.DS2mD2.save_data()
        self.DS2mD1.save_data()
        self.DS2vD1.save_data()
        self.DS2vD2.save_data()
        if self.doCorrel:
            self.DS11.save_data()
        if self.doHist2d:
            self.Hdata.h5.flush()
            self.Hdata.close()
        if self.doRaw:
            self.Rdata.h5.flush()
            self.Rdata.close()


class meastype_single_digitizer(object):
    ''' This class contains the different types of measurements done:
        one where the Drive is switched off, one, where its on,
        one where a Probe signal is present at f1 one at f2... '''

    def __init__(self, D1, D2, lags, name, corrAvg):
        gc.collect()
        self.D1 = D1
        self.D2 = D2
        self.nSamples = D1.nSamples
        self.lags = lags
        self.name = name
        self.corrAvg = corrAvg
        self.doHist2d = False  # Default is Nope
        self.doRaw = False
        self.doCorrel = True
        self.bin_size = [150, 150]  # Estimated to be ok for 1e6 data points
        self.data_variables()

    def create_objs(self, folder, filen_0, dim_1, dim_2, dim_3, doHist2d, doRaw, doCorrel=True):
        ''' Prepare Data files, where processed information will be stored '''
        self.doHist2d = doHist2d
        self.doRaw = doRaw
        self.doCorrel = doCorrel
        nfolder = folder + filen_0 + self.name + '\\'  # -> data\\subfolder\\
        self.nfolder = nfolder
        if not os.path.exists(nfolder):
            os.makedirs(nfolder)
        self.DSP_PD1 = DataStoreSP(nfolder, filen_0, dim_1, dim_2, dim_3, 'D1Pow', cname='Watts')
        self.DSP_PD2 = DataStoreSP(nfolder, filen_0, dim_1, dim_2, dim_3, 'D2Pow', cname='Watts')
        self.DSP_LD1 = DataStoreSP(nfolder, filen_0, dim_1, dim_2, dim_3, 'D1LevCor', cname='LC')
        self.DSP_LD2 = DataStoreSP(nfolder, filen_0, dim_1, dim_2, dim_3, 'D2LevCor', cname='LC')
        self.DS2vD1 = DataStore2Vec(nfolder, filen_0, dim_1, dim_2, dim_3, 'D1vAvg')
        self.DS2vD2 = DataStore2Vec(nfolder, filen_0, dim_1, dim_2, dim_3, 'D2vAvg')
        self.DS2mD1 = DataStore2Vec(nfolder, filen_0, dim_1, dim_2, dim_3, 'D1mAvg')
        self.DS2mD2 = DataStore2Vec(nfolder, filen_0, dim_1, dim_2, dim_3, 'D2mAvg')
        if self.doCorrel:
            self.DS11 = DataStore11Vec(nfolder, filen_0, dim_1, dim_2, self.D1, 'CovMat')
            # Cov Matrix D1 has dim_3 info

        if self.doHist2d:
            '''If doHist2d is set to True, a hdf5 file will be created
            to save the histogram data.'''
            Hname = nfolder+'Hist2d'+self.name+'.hdf5'
            self.Hdata = storehdf5(Hname)
            self.Hdata.clev = 1  # Compression level to a minimum for speed
            self.Hdata.open_f(mode='w')  # create a new empty file
            self.create_Htables(dim_3.pt, dim_2.pt, dim_1.pt)
        if self.doRaw:
            Rname = nfolder+'Raw'+self.name+'.hdf5'
            self.Rdata = storehdf5(Rname)
            self.Rdata.clev = 1  # Compression level to a minimum for speed
            self.Rdata.open_f(mode='w')  # create a new empty file
            self.create_Rtables(dim_3.pt, dim_2.pt, dim_1.pt)

    def create_Htables(self, d3pt, d2pt, d1pt):
        shape = (d3pt, d2pt, d1pt, self.bin_size[0], self.bin_size[1])
        # atom = tb.Float64Atom()  # kind of defines the file dtype def 64Float
        xyshape = (d3pt, d2pt, d1pt, 6, 3)
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

    def create_Rtables(self, d3pt, d2pt, d1pt):
        es = d3pt*d2pt*d1pt
        self.Rdata.create_dset32((0, 4, self.nSamples), label='D12raw', esize=es)
        self.Rdata.create_dset32((0, 3), label='ijk', esize=es)
        self.Rdata.create_dset32((0, 2), label='D12freq', esize=es)
        self.Rdata.close()
        self.Rdata.open_f()  # opens and keeps open

    def process_data(self):
        self.D1.process_data()  # process data, while measurement is running
        self.D2.process_data()
        self.add_avg()
        if self.doHist2d:
            self.calculate_histograms()
        if self.doRaw:
            self.record_raw()  # just records the raw data without coordinates

    def record_raw(self):
        ''' Records raw IQ data without the sweep coordinates'''
        if bool(self.Rdata.h5.isopen) is False:
            self.Rdata.open_f()  # opens the file to be edited
        r5 = self.Rdata.h5.root
        r5.D12raw.append([[self.D1.scaledI, self.D1.scaledQ, self.D2.scaledI, self.D2.scaledQ]])
        r5.D12raw.flush()
        self.Rdata.h5.flush()

    def calculate_histograms(self):
        I1 = self.D1.scaledI
        Q1 = self.D1.scaledQ
        I2 = self.D2.scaledI
        Q2 = self.D2.scaledQ
        self.hmap[0], self.xl[0], self.yl[0] = np.histogram2d(I1, Q1, bins=self.bin_size)
        self.hmap[1], self.xl[1], self.yl[0] = np.histogram2d(I2, Q2, bins=self.bin_size)
        self.hmap[2], self.xl[2], self.yl[2] = np.histogram2d(I1, I2, bins=self.bin_size)
        self.hmap[3], self.xl[3], self.yl[3] = np.histogram2d(Q1, Q2, bins=self.bin_size)
        self.hmap[4], self.xl[4], self.yl[4] = np.histogram2d(I1, Q2, bins=self.bin_size)
        self.hmap[5], self.xl[5], self.yl[5] = np.histogram2d(Q1, I2, bins=self.bin_size)

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
        self.covAvgMat = np.zeros([13, self.lags * 2 + 1])  # For one particular ii, jj, kk
        self.D1aPow = np.float(0.0)
        self.D2aPow = np.float(0.0)
        if self.doHist2d:
            self.hmap = np.zeros([6, self.bin_size[0], self.bin_size[1]])
            self.xl = np.zeros([6, self.bin_size[0]+1])
            self.yl = np.zeros([6, self.bin_size[1]+1])
        if self.doRaw:
            self.ijk = np.zeros([1, 3])
            self.D12freq = np.zeros([1, 2])

    def add_avg(self):
        self.D1Ma += self.D1.AvgMag
        self.D1Pha += self.D1.AvgPhase
        self.D1vMa += self.D1.vAvgMag
        self.D1vPha += self.D1.vAvgPh
        self.D1aPow += self.D1.vAvgPow
        self.D2Ma += self.D2.AvgMag
        self.D2Pha += self.D2.AvgPhase
        self.D2vMa += self.D2.vAvgMag
        self.D2vPha += self.D2.vAvgPh
        self.D2aPow += self.D2.vAvgPow
        if self.doCorrel:
            self.covAvgMat += getCovMatrix(self.D1.scaledI, self.D1.scaledQ,
                                           self.D2.scaledI, self.D2.scaledQ,
                                           self.lags)

    def data_record(self, kk, jj, ii):
        '''This loads the new information into the matices'''
        corrAvg = np.float(self.corrAvg)
        self.DSP_PD1.record_data((self.D1aPow / corrAvg), kk, jj, ii)
        self.DSP_PD2.record_data((self.D2aPow / corrAvg), kk, jj, ii)
        self.DSP_LD1.record_data(self.D1.levelcorr, kk, jj, ii)
        self.DSP_LD2.record_data(self.D2.levelcorr, kk, jj, ii)
        self.DS2mD2.record_data(self.D2Ma / corrAvg, self.D2Pha / corrAvg, kk, jj, ii)
        self.DS2mD1.record_data(self.D1Ma / corrAvg, self.D1Pha / corrAvg, kk, jj, ii)
        self.DS2vD1.record_data(self.D1vMa / corrAvg, self.D1vPha / corrAvg, kk, jj, ii)
        self.DS2vD2.record_data(self.D2vMa / corrAvg, self.D2vPha / corrAvg, kk, jj, ii)
        if self.doCorrel:
            self.DS11.record_data(self.covAvgMat / corrAvg, kk, jj, ii)
        if self.doHist2d:
            self.record_histM(kk, jj, ii)
        if self.doRaw:
            if bool(self.Rdata.h5.isopen) is False:
                self.Rdata.open_f()  # opens the file to be edited
            self.ijk[0, 0] = ii
            self.ijk[0, 1] = jj
            self.ijk[0, 2] = kk
            self.D12freq[0, 0] = self.D1.freq/1e9
            self.D12freq[0, 1] = self.D2.freq/1e9
            self.Rdata.h5.root.ijk.append(self.ijk)
            self.Rdata.h5.root.D12freq.append(self.D12freq)
            self.Rdata.h5.flush()

    def record_histM(self, kk, jj, ii):
        ''' This creates a figure of the histogram at one specific point'''
        if bool(self.Hdata.h5.isopen) is False:
            self.Hdata.open_f()  # opens the file to be edited
        h5 = self.Hdata.h5.root
        for i in range(self.xl.shape[0]):
            h5.XminXmaxXNum[kk, jj, ii, i] = [self.xl[i][0], self.xl[i][-1], len(self.xl[i])]
            h5.YminYmaxYNum[kk, jj, ii, i] = [self.yl[i][0], self.yl[i][-1], len(self.yl[i])]
        h5.I1Q1_0[kk, jj, ii] = self.hmap[0]
        h5.I2Q2_1[kk, jj, ii] = self.hmap[1]
        h5.I1I2_2[kk, jj, ii] = self.hmap[2]
        h5.Q1Q2_3[kk, jj, ii] = self.hmap[3]
        h5.I1Q2_4[kk, jj, ii] = self.hmap[4]
        h5.Q1I2_5[kk, jj, ii] = self.hmap[5]
        self.Hdata.h5.flush()

    def data_save(self):
        '''save the data in question, at the moment these functions rewrite the matrix eachtime,
        instead of just appending to it.'''
        self.DSP_PD1.save_data()
        self.DSP_PD2.save_data()
        self.DSP_LD1.save_data()
        self.DSP_LD2.save_data()
        self.DS2mD2.save_data()
        self.DS2mD1.save_data()
        self.DS2vD1.save_data()
        self.DS2vD2.save_data()
        if self.doCorrel:
            self.DS11.save_data()
        if self.doHist2d:
            self.Hdata.h5.flush()
            self.Hdata.close()
        if self.doRaw:
            self.Rdata.h5.flush()
            self.Rdata.close()
