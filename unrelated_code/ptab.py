import numpy as np
import tables as tb


class CovarianceMat(tb.IsDescription):
    name = tb.StringCol(16)
    cI1I1 = tb.Float32Col()  # I phot 1
    cQ1Q1 = tb.Float32Col()  # Q phot 1
    cI2I2 = tb.Float32Col()  # I phot 2
    cQ2Q2 = tb.Float32Col()  # Q phot 2
    cQ1I1 = tb.Float32Col()  # Corr Single Mode 1
    cQ2I2 = tb.Float32Col()  # Corr Single Mode 2
    cI1I2 = tb.Float32Col()  # CCorr Two Mode
    cI2I1 = tb.Float32Col()
    cQ1Q2 = tb.Float32Col()
    cQ2Q1 = tb.Float32Col()


class bilder(tb.IsDescription):
    name = tb.StringCol(16)
    bild = tb.Float32Col()
