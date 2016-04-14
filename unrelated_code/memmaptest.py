import numpy as np
from struct import pack

data = np.arange(24, dtype='float32')
data.resize((2, 3, 4))
filename = 'npfile.txt'
# fp = np.memmap(filename, dtype='float32',
#                mode='w+', shape=(2, 3, 4), order='F')
# fp[:] = data[:]
# del fp


def np_farray(filename, myshape, new=False):
    ''' This uses a very useful function to deal with slightly larger data files
        maps an numpy array of the shape (myshape) into the hard disk as a file
        if new is set to True it deletes the old one and creates a new file.
        Otherwise it simply opens the old one.
        Important to note is the shape information.
    '''
    if new:
        return np.memmap(
            filename, dtype='float32', mode='w+', shape=myshape, order='C')
    return np.memmap(
        filename, dtype='float32', mode='r+', shape=myshape, order='C')


def farray2mtx(farrayfilen, shape, header='Units,ufo,d1,0,1,d2,0,1,d3,0,1'):
    '''changes the farray file into an mtx file for spyview'''
    newfile = farrayfilen + '.mtx'
    line = str(shape[2])+' '+str(shape[1])+' '+str(shape[0])+' '+'8'
    fp = np.memmap(filename, dtype='float32', mode='r', shape=shape, order='C')
    with open(newfile, 'wb') as f:
        f.write(header + '\n')
        f.write(line + '\n')
        for ii in range(shape[2]):
            for jj in range(shape[1]):
                content = pack('%sd' % shape[0], *fp[:, jj, ii])
                f.write(content)
        f.close()
