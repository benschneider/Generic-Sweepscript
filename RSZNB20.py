'''
Python driver for:
Rohde & Schwartz
ZNB20
Vector Network Analyzer
100kHz - 20Ghz


22/06/2015
- B
'''

import numpy as np
from struct import unpack  # , pack
from time import sleep, time
import visa
from parsers import savemtx, make_header, ask_overwrite
rm = visa.ResourceManager()


# def isNaN(num):
#       ''' this only detects some nan values
#        use numpy.isnan instead '''
#     return num.max() != num.max()

class instrument():
    # name = 'ZNB21'
    # start = -30e-3
    # stop = 30e-3
    # pt = 1001 # number of points
    # power = -30 #rf power
    '''
    vna = instrument1('TCPIP::129.16.115.137::INSTR')
    w write
    r read
    a ask
    '''

    def __init__(self, adress, name='ZNB20', start=0, stop=0, pt=1, BW=1e3, 
                 power=-30, sstep=2e9, stime=0.0, copy_setup=True):
                     
        self._adress = adress
        self._visainstrument = rm.open_resource(self._adress)
        self.name = name      
        if copy_setup:
            self.get_points()
            self.get_freq_start()
            self.get_freq_stop()
            self.get_BW()
            self.get_power()
        else:
            self.set_points(pt)
            self.set_freq_start(start)
            self.set_freq_stop(stop)
            self.set_BW(BW)
            self.set_power(power)
        self.w(':INIT:CONT OFF')  # switch continuous mode off
        self.init_sweep()
        self.sweeptime = self.get_sweeptime() + 0.1
        self._tempdata = self.get_data()            
        self.lin = np.linspace(self.start, self.stop, self.pt)

    def w(self, write_cmd):
        self._visainstrument.write(write_cmd)

    def r(self):
        return self._visainstrument.read()
        
    def r_raw(self):
        return self._visainstrument.read_raw()

    def a(self, ask_cmd):
        return self._visainstrument.ask(ask_cmd)
        
    def aBin(self, ask_cmd):
        return self._visainstrument.query_binary_values(ask_cmd)

    def init_sweep(self):
        self.w(':INIT:IMM;*OPC')
        self.sweep_t0 = time()

    def init_sweep_wait(self):
        self.w(':INIT:IMM;*WAI')

    def abort(self):
        self.w(':ABOR;:INIT:CONT OFF')  # abort current sweep
        self.w(':SENS:AVER:CLE')  # clear prev averages
        self.w(':SENS:SWE:COUN 1')  # set counts to 1

    def set_output(self, outstate):
        self.w(':OUTP ' + str(outstate))
        self.output = outstate

    def get_output(self):
        self.output = self.a(':OUTP?')
        return self.output

    def set_power(self, power):
        self.w(':SOUR:POW ' + str(power))
        self.powerlvl = power

    def get_power(self):
        self.powerlvl = eval(self.a(':SOUR:POW?'))
        return self.powerlvl

    def get_error(self):
        return self.a('SYST:ERR:ALL?')

    def get_sweeptime(self):
        return eval(self.a('SWE:TIME?'))

    def get_freq(self):
        return eval(self.a('FREQ?'))

    def set_freq_cw(self, value):
        self.w('FREQ:CW ' + str(value))

    def set_BW(self, bw):
        self.BW = bw
        self.w(':SENS:BWID ' + str(bw))
        
    def get_BW(self):
        self.BW = self.a(':SENS:BWID?')
        return self.BW

    def set_avg_state(self, bool_state):
        self.w(':SENS:AVER ' + str(bool_state))
        self.avgState = bool_state

    def get_avg_state(self):
        self.avgState = self.w(':SENS:AVER?')
        return self.avgState

    def set_avg_num(self, avgnum):
        self.avgn = avgnum
        self.w(':SENS:AVER:COUN ' + str(avgnum))

    def get_avg_num(self):
        self.avgnum = self.a(':SENS:AVER:COUN?')
        return self.avgnum

    def set_freq_start(self, fstart):
        self.start = fstart
        self.w(':SENS:FREQ:STAR ' + str(fstart))
    
    def get_freq_start(self):
        self.start = eval(self.a(':SENS:FREQ:STAR?'))
        return self.start

    def set_freq_stop(self, fstop):
        self.stop = fstop
        self.w(':SENS:FREQ:STOP ' + str(fstop))
    
    def get_freq_stop(self):
        self.stop = eval(self.a(':SENS:FREQ:STOP?'))
        return self.stop

    def set_freq_span(self, fspan):
        self.w(':SENS:FREQ:SPAN ' + str(fspan))
    
    def get_freq_span(self):
        return eval(self.a(':SENS:FREQ:SPAN?'))

    def set_points(self, points):
        self.pt = points
        self.w(':SENS:SWE:POIN ' + str(points))
    
    def get_points(self):
        self.pt = eval(self.a(':SENS:SWE:POIN?'))
        return self.pt

    def set_sweep_type(self, stype):
        ''' LIN, LOG, CW '''
        self.w(':SENS:SWE:TYPE ' + str(stype))

    def get_data(self):
        try:
            vdata = np.array(self.aBin(':FORM REAL,32;CALC:DATA? SDATA'))
        except:
            print self.get_error()
            sleep(3)
            self.get_data()
        return vdata[::2] + 1j * vdata[1::2]

    def wait(self):
        '''Waits until VNA operation is completed'''
        #wtime = abs(self.sweep_t0 - time())  # time waited so far
        #if wtime < self.sweeptime:
        #    sleep(self.sweeptime-wtime)
        OPC = bool(int(self.a('*OPC?')))
        if OPC:
            return
        sleep(0.1)
        self.wait()

    def prepare_data_save(self, folder, filen_0, dim1, dim_2, dim_3):
        if self.pt > 1:
            dim_1 = self
        else:
            dim_1 = dim1
        self._folder = folder
        self._filen_1 = filen_0 + '_r' + '.mtx'
        self._filen_2 = filen_0 + '_i' + '.mtx'
        self._filen_3 = filen_0 + '_m' + '.mtx'
        self._filen_4 = filen_0 + '_p' + '.mtx'
        self._head_1 = make_header(dim_1, dim_2, dim_3, 'S11 real')
        self._head_2 = make_header(dim_1, dim_2, dim_3, 'S11 imag')
        self._head_3 = make_header(dim_1, dim_2, dim_3, 'S11 mag')
        self._head_4 = make_header(dim_1, dim_2, dim_3, 'S11 phase')
        self._matrix3d_1 = np.memmap('VNAreal.mem', dtype=np.float32, mode='w+', shape=(dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_2 = np.memmap('VNAimag.mem', dtype=np.float32, mode='w+', shape=(dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_3 = np.memmap('VNAmag.mem', dtype=np.float32, mode='w+', shape=(dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_4 = np.memmap('VNAphase.mem', dtype=np.float32, mode='w+', shape=(dim_3.pt, dim_2.pt, dim_1.pt))
        #self._matrix3d_1 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        #self._matrix3d_2 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        #self._matrix3d_3 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        #self._matrix3d_4 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))

    def record_data(self, vnadata, kk, jj, ii):
        self._phase_data = np.angle(vnadata)
        if self.pt == 1:
            self._matrix3d_1[kk, jj, ii] = vnadata.real
            self._matrix3d_2[kk, jj, ii] = vnadata.imag
            self._matrix3d_3[kk, jj, ii] = np.absolute(vnadata)
            self._matrix3d_4[kk, jj, ii] = self._phase_data
        else:
            self._matrix3d_1[kk, jj, :] = vnadata.real
            self._matrix3d_2[kk, jj, :] = vnadata.imag
            self._matrix3d_3[kk, jj, :] = np.absolute(vnadata)
            self._matrix3d_4[kk, jj, :] = self._phase_data

    def save_data(self):
        savemtx(self._folder + self._filen_1, self._matrix3d_1, header=self._head_1)
        savemtx(self._folder + self._filen_2, self._matrix3d_2, header=self._head_2)
        savemtx(self._folder + self._filen_3, self._matrix3d_3, header=self._head_3)
        savemtx(self._folder + self._filen_4, self._matrix3d_4, header=self._head_4)

    def ask_overwrite(self):
        ask_overwrite(self._folder + self._filen_1)


if __name__ == '__main__':
    VNA = instrument('TCPIP::129.16.115.137::INSTR')
    # Required is set VNA into trigger mode 'single'
    
    