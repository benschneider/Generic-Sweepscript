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

    def __init__(self):
        pass

    def ask_overwrite(self):
        ask_overwrite(self._folder+self._filen_1)

    def prepare_data_save(self, folder,
                          filen_0, dim_1, dim_2, dim_3, colour_name):
        self._folder = folder
        self._filen_1 = filen_0 + '_voltage' + '.mtx'
        self._head_1 = make_header(dim_1, dim_2, dim_3, colour_name)
        self._matrix3d_1 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        if dim_1.UD is True:
            self.UD = True
            self._matrix3d_2 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))

    def record_data(self, vdata, kk, jj, ii=1):
        self._matrix3d_1[kk, jj, ii] = vdata

    def record_data2(self, vdata, kk, jj, ii=1):
        self._matrix3d_2[kk, jj, ii] = vdata

    def save_data(self):
        savemtx(self._folder + self._filen_1,
                self._matrix3d_1,
                header=self._head_1)
        if self.UD is True:
            savemtx(self._folder + self._filen_1 + '_2',
                    self._matrix3d_2,
                    header=self._head_1)


class DataStoreVNA():

    def __init__(self):
        pass

    def ask_overwrite(self):
        ask_overwrite(self._folder+self._filen_1)

    def prepare_data_save(self, folder, filen_0, dim_1, dim_2, dim_3):
        self._folder = folder
        self._filen_1 = filen_0 + '_real' + '.mtx'
        self._filen_2 = filen_0 + '_imag' + '.mtx'
        self._filen_3 = filen_0 + '_mag' + '.mtx'
        self._filen_4 = filen_0 + '_phase' + '.mtx'
        self._head_1 = make_header(dim_1, dim_2, dim_3, 'S21 _real')
        self._head_2 = make_header(dim_1, dim_2, dim_3, 'S21 _imag')
        self._head_3 = make_header(dim_1, dim_2, dim_3, 'S21 _mag')
        self._head_4 = make_header(dim_1, dim_2, dim_3, 'S21 _phase')
        self._matrix3d_1 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_2 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_3 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_4 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))

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
        savemtx(self._folder + self._filen_1,
                self._matrix3d_1,
                header=self._head_1)
        savemtx(self._folder + self._filen_2,
                self._matrix3d_2,
                header=self._head_2)
        savemtx(self._folder + self._filen_3,
                self._matrix3d_3,
                header=self._head_3)
        savemtx(self._folder + self._filen_4,
                self._matrix3d_4,
                header=self._head_4)
