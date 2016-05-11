import h5py
import numpy as np
import tables as tb

# sample_data = np.zeros([1e3, 1e3])
# I1 = np.random.random(int(1e6))
# I2 = np.random.random(int(1e6)) + 0.01*I1
# histI1I2, xl, yl = np.histogram2d(I1, I2, bins=[int(1e3), int(1e3)])


class storehdf5(object):

    def __init__(self, fname, clev=5, clib='blosc'):
        self.fname = fname
        self.clev = clev  # compression level
        self.clib = clib  # compression library / type
        self.filt = tb.Filters(complevel=clev, complib=clib)
        self.mode = 'w'
        # self.open(self.mode)

    def open(self, mode='a'):
        self.hdf5 = tb.open_file(self.fname, mode)

    def add_data(self, data, label='label1'):
        self.data_storage = self.hdf5.create_carray(
            self.hdf5.root, label, tb.Atom.from_dtype(data.dtype),
            shape=data.shape, filters=self.filt)
        self.data_storage[:] = data

    def close(self):
        self.hdf5.close()

    # def write_hdf5(filen, data, clevel=5):
        '''Writes data to HDF5 file'''
        # hdf5_file = tb.open_file(filen, mode='w')
        # filters = tb.Filters(complevel=clevel, complib='blosc')
        # data_storage = hdf5_file.create_carray(hdf5_file.root, 'label1',
        #                                        tb.Atom.from_dtype(data.dtype),
        #                                        shape=data.shape, filters=filters)
        # data_storage[:] = data
        # hdf5_file.close()
        # return data_storage

# write_hdf5('testfile.hdf5', histI1I2)
# comp_file = tb.open_file(hdf5_path, mode='r')
