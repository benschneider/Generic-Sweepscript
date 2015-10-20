from time import sleep
import numpy as np

class instrument():

    def __init__(self, adress='dummy' , name = 'D', start = 0, stop = 0, pt = 1, sstep = 20e-3, stime = 1e-3):
        self.adress = adress
        #self.exp_2 = self.instrument_1(adress)
        self.var_1 = 0
        self.name = name
        self.start = start
        self.stop = stop
        self.pt = pt
        self.lin = np.linspace(self.start,self.stop,self.pt)

    def instrument_1(self, adress):
        return (5,adress)

    def set_var1(self, var_1):
        sleep(0.01) #sim 10ms delay time
        self.var_1 = var_1
        print var_1

    def get_var1(self):
        return self.var_1

    def get_random(self):
        return (np.random.rand(1)*10-5)*2 #+-10

