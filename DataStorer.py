'''
This file
- Prepare matricies to store data into
- write result matrix to file using the parser file

Ben
2015-10-21
'''
import numpy as np
# from time import time, sleep
from parsers import savemtx, make_header, ask_overwrite


class DataStoreSP():
    
    def __init__(self, folder, filen_0, dim_1, dim_2, dim_3, label = '_', cname='Voltage x1k'):
        self._folder = folder
        self._filen_1 = filen_0 + label + '.mtx'
        self._head_1 = make_header(dim_1, dim_2, dim_3, cname)
        self._matrix3d_1 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self.UD = False
        if dim_1.UD is True:
            self._filen_2 = filen_0 + label + '_2' + '.mtx'
            self.UD = True
            self._matrix3d_2 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
            
    def ask_overwrite(self):
        ask_overwrite(self._folder+self._filen_1)


    def record_data(self, vdata, kk, jj, ii=1):
        self._matrix3d_1[kk, jj, ii] = vdata

    def record_data2(self, vdata, kk, jj, ii=1):
        self._matrix3d_2[kk, jj, ii] = vdata

    def save_data(self):
        savemtx(self._folder + self._filen_1, self._matrix3d_1, header=self._head_1)
        if self.UD is True:
            savemtx(self._folder + self._filen_2, self._matrix3d_2, header=self._head_1)


class DataStore4Vec():

    def __init__(self, folder, filen_0, dim_1, dim_2, dim_3):
        self._folder = folder
        self._filen_1 = filen_0 + '_real' + '.mtx'
        self._filen_2 = filen_0 + '_imag' + '.mtx'
        self._filen_3 = filen_0 + '_mag' + '.mtx'
        self._filen_4 = filen_0 + '_phase' + '.mtx'
        self._head_1 = make_header(dim_1, dim_2, dim_3, 'S11 _real')
        self._head_2 = make_header(dim_1, dim_2, dim_3, 'S11 _imag')
        self._head_3 = make_header(dim_1, dim_2, dim_3, 'S11 _mag')
        self._head_4 = make_header(dim_1, dim_2, dim_3, 'S11 _phase')
        self._matrix3d_1 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_2 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_3 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_4 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))

    def ask_overwrite(self):
        ask_overwrite(self._folder+self._filen_1)

    def record_data(self, vnadata, kk, jj, ii=1):
        self._phase_data = np.angle(vnadata)
        if vnadata.shape[0] == 1:
            self._matrix3d_1[kk, jj, ii] = vnadata.real
            self._matrix3d_2[kk, jj, ii] = vnadata.imag
            self._matrix3d_3[kk, jj, ii] = np.absolute(vnadata)
            self._matrix3d_4[kk, jj, ii] = self._phase_data
        else:
            self._matrix3d_1[kk, jj] = vnadata.real
            self._matrix3d_2[kk, jj] = vnadata.imag
            self._matrix3d_3[kk, jj] = np.absolute(vnadata)
            self._matrix3d_4[kk, jj] = np.unwrap(self._phase_data)

    def save_data(self):
        savemtx(self._folder + self._filen_1, self._matrix3d_1, header=self._head_1)
        savemtx(self._folder + self._filen_2, self._matrix3d_2, header=self._head_2)
        savemtx(self._folder + self._filen_3, self._matrix3d_3, header=self._head_3)
        savemtx(self._folder + self._filen_4, self._matrix3d_4, header=self._head_4)


class DataStore2Vec():

    def __init__(self, folder, filen_0, dim_1, dim_2, dim_3, label = '_'):
        self._folder = folder
        self._filen_3 = filen_0 + label + '_mag' + '.mtx'
        self._filen_4 = filen_0 + label + '_phase' + '.mtx'
        self._head_3 = make_header(dim_1, dim_2, dim_3, 'S11 _mag')
        self._head_4 = make_header(dim_1, dim_2, dim_3, 'S11 _phase')
        self._matrix3d_3 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_4 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        
    def ask_overwrite(self):
        ask_overwrite(self._folder+self._filen_1)

    def record_data(self, mag, phase, kk, jj, ii=1):
        if len([mag]) == 1:
            self._matrix3d_3[kk, jj, ii] = mag
            self._matrix3d_4[kk, jj, ii] = phase
        else:
            self._matrix3d_3[kk, jj] = mag
            self._matrix3d_4[kk, jj] = np.unwrap(phase)

    def save_data(self):
        savemtx(self._folder + self._filen_3,
                self._matrix3d_3,
                header=self._head_3)
        savemtx(self._folder + self._filen_4,
                self._matrix3d_4,
                header=self._head_4)
                
class DataStore11Vec():

    def __init__(self, folder, filen_0, dim_1, dim_2, dim_3, label = '_'):
        self._folder = folder
        self._filen_1 = filen_0 + label + '_cI1I1' + '.mtx'
        self._filen_2 = filen_0 + label + '_cQ1Q1' + '.mtx'
        self._filen_3 = filen_0 + label + '_cI2I2' + '.mtx'
        self._filen_4 = filen_0 + label + '_cQ2Q2' + '.mtx'
        self._filen_5 = filen_0 + label + '_cI1Q1' + '.mtx'
        self._filen_6 = filen_0 + label + '_cI2Q2' + '.mtx'
        self._filen_7 = filen_0 + label + '_cI1I2' + '.mtx'
        self._filen_8 = filen_0 + label + '_cQ1Q2' + '.mtx'
        self._filen_9 = filen_0 + label + '_cI1Q2' + '.mtx'
        self._filen_10 = filen_0 + label + '_cQ1I2' + '.mtx'
        self._filen_11 = filen_0 + label + '_Squeezing' + '.mtx'
        self._head_0 = make_header(dim_1, dim_2, dim_3, 'cCov')
        self._head_1 = make_header(dim_1, dim_2, dim_3, 'cCov')
        self._head_2 = make_header(dim_1, dim_2, dim_3, 'cCov')
        self._head_3 = make_header(dim_1, dim_2, dim_3, 'cCov')
        self._head_4 = make_header(dim_1, dim_2, dim_3, 'cCov')
        self._head_5 = make_header(dim_1, dim_2, dim_3, 'cCov')
        self._head_6 = make_header(dim_1, dim_2, dim_3, 'cCov')
        self._head_7 = make_header(dim_1, dim_2, dim_3, 'cCov')
        self._head_8 = make_header(dim_1, dim_2, dim_3, 'cCov')
        self._head_9 = make_header(dim_1, dim_2, dim_3, 'cCov')
        self._head_10 = make_header(dim_1, dim_2, dim_3, 'Squeezing')
        self._matrix3d_0 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_1 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_2 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_3 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_4 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_5 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_6 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_7 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_8 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_9 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_10 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))

    def ask_overwrite(self):
        ask_overwrite(self._folder+self._filen_1)

    def record_data(self, data, kk, jj, ii):
        self._matrix3d_0[:, jj, ii] = data[0,:]
        self._matrix3d_1[:, jj, ii] = data[1,:]
        self._matrix3d_2[:, jj, ii] = data[2,:]
        self._matrix3d_3[:, jj, ii] = data[3,:]
        self._matrix3d_4[:, jj, ii] = data[4,:]
        self._matrix3d_5[:, jj, ii] = data[5,:]
        self._matrix3d_6[:, jj, ii] = data[6,:]
        self._matrix3d_7[:, jj, ii] = data[7,:]
        self._matrix3d_8[:, jj, ii] = data[8,:]
        self._matrix3d_9[:, jj, ii] = data[9,:]
        self._matrix3d_10[:, jj, ii] = data[10,:]

    def save_data(self):
        savemtx(self._folder + self._filen_1, self._matrix3d_0, header=self._head_0)
        savemtx(self._folder + self._filen_2, self._matrix3d_1, header=self._head_1)
        savemtx(self._folder + self._filen_3, self._matrix3d_2, header=self._head_2)
        savemtx(self._folder + self._filen_4, self._matrix3d_3, header=self._head_3)
        savemtx(self._folder + self._filen_5, self._matrix3d_4, header=self._head_4)
        savemtx(self._folder + self._filen_6, self._matrix3d_5, header=self._head_5)
        savemtx(self._folder + self._filen_7, self._matrix3d_6, header=self._head_6)
        savemtx(self._folder + self._filen_8, self._matrix3d_7, header=self._head_7)
        savemtx(self._folder + self._filen_9, self._matrix3d_8, header=self._head_8)
        savemtx(self._folder + self._filen_10, self._matrix3d_9, header=self._head_9)
        savemtx(self._folder + self._filen_11, self._matrix3d_10, header=self._head_10)
