from time import sleep
import numpy as np


class instrument():
    """This dummy has no comment. Test of forking on github"""

    def __init__(self, adress='dummy', name='D', start=0, stop=0, pt=1, sstep=20e-3, stime=1e-3):
        self.adress = adress
        # self.exp_2 = self.instrument_1(adress)
        self.name = name
        self.start = start
        self.stop = stop
        self.pt = pt
        self.lin = np.linspace(self.start, self.stop, self.pt)
        self.sweep_par = 'val'
        self.sstep = sstep
        self.stime = stime
        self.var1 = 0.0

    def instrument_1(self, adress):
        return (5, adress)

    def get_val(self):
        return self.var1

    def set_val(self, value):
        self.var1 = value

    def get_random(self):
        return (np.random.rand(1) * 10 - 5) * 2  # +-10
        
    def output(self, val):
        self.output_val = val
        
    def _dconn(self):
        return
