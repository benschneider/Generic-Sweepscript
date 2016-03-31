
import numpy as np
import matplotlib.pyplot as plt

plt.ion()

np.random.seed(0)
n = 100000
x = np.random.standard_normal(n)
y = 2.0 + 3.0 * x + 4.0 * np.random.standard_normal(n)

mm, xl, yl = np.histogram2d(x, y, bins=200, range=[[-5, 5], [-25, 25]])
# histogram count y axis from bottom 0 to top
# imgshow counts from top 0 to bottom

plt.close("all")
plt.figure()
# plt.imshow(mm[::-1], extent=[-5, 5, -25, 25], aspect="auto")
plt.imshow(mm, extent=[-5, 5, -25, 25], aspect="auto", origin='lower')

# hexbin example from pyplot webpage:
"""
hexbin is an axes method or pyplot function that is essentially
a pcolor of a 2-D histogram with hexagonal cells.  It can be
much more informative than a scatter plot; in the first subplot
below, try substituting 'scatter' for 'hexbin'.
"""
# xmin = x.min()
# xmax = x.max()
# ymin = y.min()
# ymax = y.max()
# plt.figure()
# plt.subplots_adjust(hspace=0.5)
# plt.subplot(121)
# plt.hexbin(x, y)
# # plt.axis([xmin, xmax, ymin, ymax])
# plt.title("Hexagon binning")
# cb = plt.colorbar()
# cb.set_label('counts')
#
# plt.subplot(122)
# plt.hexbin(x, y, bins='log')  # , cmap=plt.cm.YlOrRd_r)
# # plt.axis([xmin, xmax, ymin, ymax])
# plt.title("With a log color scale")
# cb = plt.colorbar()
# cb.set_label('log10(N)')
plt.show()
