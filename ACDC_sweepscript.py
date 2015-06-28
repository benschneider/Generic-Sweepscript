'''
Generic Sweep script
(currently setup for no more than 3 dims)

22/06/2015
- B
'''

#how to update functions of a module when loading from console ? ??? or tell Python to recompile its files :
import ramp_mod, parsers, RSZNB20, Yoko, dummydriver
reload(RSZNB20)
reload(Yoko)
reload(parsers)
reload(ramp_mod)
reload(dummydriver)
del ramp_mod, parsers, RSZNB20, Yoko, dummydriver

import numpy as np
from time import time, sleep
from inspect import currentframe, getfile #
thisfile = getfile(currentframe())
from parsers import savemtx, ask_overwrite, copy_file, make_header
from ramp_mod import ramp

filen_0 = 'S1_146'
folder = 'data\\'

### MEASURING SHAPIRO-STEPS ###

#Drivers
from RSZNB20 import instrument as znb20
from keithley2000 import instrument as key2000
from Yoko import instrument as yoko
from dummydriver import instrument as ddriver
#Data aquisition instruments
vna = znb20('TCPIP::169.254.107.192::INSTR')
vm = key2000('GPIB0::29::INSTR')
def get_dim1_data(dim_1,vna,vm):
    vna.init_sweep()
    vdata = vm.get_val()
    sleep(0.001)
    vnadata = vna.get_data2() # np.array(real+ i* imag)
    return vnadata,vdata
#Sweep instruments
dim_1 = yoko('GPIB0::13::INSTR',
           name = 'Yoko V R=14.8KOhm',
           start = -100e-3, 
           stop = 100e-3, 
           pt = 1001 ) #'Yoko V' 
dim_1.prepare_v(vrange = 3)  # vrange =2 -- 10mV, 3 -- 100mV, 4 -- 1V, 5 -- 10V, 6 -- 30V

dim_2 = ddriver(name = 'RF-Power',
                start = 12,
                stop = -30,
                pt = 43) #VNA POWER sweep
dim_2.set_power = vna.set_power

dim_3 = yoko('GPIB0::10::INSTR',
            name = 'Magnet V R=2.19KOhm',
            start = -0.5, 
            stop = 0.5, 
            pt = 51) #'Yoko M' 
dim_3.prepare_v(vrange = 4)


#for the VNA I want 4 data files for Real, Imag, MAG, Phase
filen_1 = filen_0 + '_real'  + '.mtx'
filen_2 = filen_0 + '_imag'  + '.mtx'
filen_3 = filen_0 + '_mag'   + '.mtx'
filen_4 = filen_0 + '_phase' + '.mtx'
filen_5 = filen_0 + '_voltage'  + '.mtx'
head_1 = make_header(dim_1, dim_2, dim_3, 'S21 _real')
head_2 = make_header(dim_1, dim_2, dim_3, 'S21 _imag')
head_3 = make_header(dim_1, dim_2, dim_3, 'S21 _mag')
head_4 = make_header(dim_1, dim_2, dim_3, 'S21 _phase')
head_5 = make_header(dim_1, dim_2, dim_3, 'Voltage (V) x1k')
matrix3d_1 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
matrix3d_2 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
matrix3d_3 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
matrix3d_4 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
matrix3d_5 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))

ask_overwrite(folder+filen_1)
copy_file(thisfile, filen_0, folder) #backup this script


print 'Executing sweep'
print 'req time (h):'+str(dim_3.pt*dim_2.pt*dim_1.pt*0.13/3600)
t0 = time()
try:
    for kk in range(dim_3.pt): 
        #dim_3 = Magnet V
        ramp(dim_3, 'v', dim_3.lin[kk], 0.002, 0.01)

        for jj in range(dim_2.pt):
            #dim_2 = RF Power
            dim_2.set_power(dim_2.lin[jj])
            
            ramp(dim_1, 'v', dim_1.start, 0.002, 0.01)
            for ii in range(dim_1.pt):
                
                if dim_1.pt > 300:
                    dim_1.set_v(dim_1.lin[ii]) #sets value imediately (Dangerous!)
                else:
                    ramp(dim_1, 'v', dim_1.lin[ii], 0.002, 0.01) #slower but safer sweep

                vnadata, vdata = get_dim1_data(dim_1,vna,vm)
                
                phase_data = np.angle(vdata)        
                matrix3d_1[kk,jj,ii] = vdata.real
                matrix3d_2[kk,jj,ii] = vdata.imag
                matrix3d_3[kk,jj,ii] = np.absolute(vdata)
                matrix3d_4[kk,jj,ii] = phase_data #np.unwrap(phase_data)
                matrix3d_5[kk,jj,ii] = vdata

            savemtx(folder + filen_1, matrix3d_1, header = head_1)
            savemtx(folder + filen_2, matrix3d_2, header = head_2)
            savemtx(folder + filen_3, matrix3d_3, header = head_3)
            savemtx(folder + filen_4, matrix3d_4, header = head_4)
            savemtx(folder + filen_5, matrix3d_5, header = head_5)
            
            t1 = time()
            remaining_time = ((t1-t0)/(jj+1)*dim_2.pt*dim_3.pt - (t1-t0))
            print 'req time (h):'+str(remaining_time/3600)

finally:
    print 'Finish measurements'
    print 'Time used :' +str(time()-t0)
    print 'Yokos -> zero and switch off'
    dim_1.sweep_v(0, 5)
    dim_3.sweep_v(0, 5)
    sleep(5.2)
    dim_1.output(0) #Yoko Off
    dim_3.output(0)
    