import numpy as np
from scipy import sparse as sp
from time import time
# from timeit import repeat, timeit


def histogram2d(XX, matdd):
    ''' np.array([X, Y])  data will be mapped 2dnumpy array 'matdd'
        returns: map, xmin, xmax, ymin, ymax values
        this function is currently only fast for small X, Y vectors.
    '''

    # t0 = time()
    ranges = np.zeros([XX.shape[0], 3])
    pos = np.zeros_like(XX, dtype=int)
    # t1 = time()

    for i in range(XX.shape[0]):
        # the digitize function
        ranges[i, 0] = XX[i].min()  # max
        ranges[i, 1] = XX[i].max()  # min
        ranges[i, 2] = (ranges[i, 1] - ranges[i, 0]) / (matdd.shape[i]-1)  # bin size
        pos[i, :] = np.round(XX[i]/ranges[i, 2])  # positions

    # t2 = time()

    # xsorted = x[x[:,0].argsort()]

    # for i in range(XX.shape[1]):
    #     # t3 = time()
    #     x = pos[0, i]
    #     y = pos[1, i]
    #     matdd[x, y] += + 1
    #     # matdd[pos[0, i], pos[1, i]] += 1

    for i in range(matdd.shape[0]):
        t0 = pos[pos[:, 0] == i][:, 1]
        np.bincount(t0,



    # print t1 - t0, t2 - t1, time() - t3
    return matdd, ranges

# if __name__ == "__main__":
X = np.random.random(int(1e7))
Y = np.random.random(int(1e7))
XX = np.array([X, Y])
mat = np.zeros([10, 10])
t0 = time()
m, xy = histogram2d(XX, mat)
t1 = time()
m, x, y = np.histogram2d(X, Y, bins=(10, 10))
t2 = time()
print t1-t0, t2-t1
