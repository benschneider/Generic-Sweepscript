'''
Generic Sweep script
(currently setup for no more than 3 dims)

22/06/2015
- B
'''
import numpy as np
from time import time, sleep
from inspect import currentframe, getfile
thisfile = getfile(currentframe())

#for storing results
execfile('parsers.py')
execfile('ramp_mod.py')

filen_0 = 'S1_137'
folder = 'data\\'

dim_1name = 'VNA S21 - Time'
dim_1start = -30e-3 
dim_1stop = 30e-3
execfile('RSZNB20.py')
dim_1 = instrument1('TCPIP::169.254.107.192::INSTR')
dim_1data = dim_1.get_data()
dim_1pt = dim_1data.shape[0]

dim_1b_name = 'Yoko M'
dim_1b_start = -1 
dim_1b_stop = 1
dim_1b_pt = 101
dim_1b_time = 60 #sweep in 200 seconds, while VNA records
execfile('Yoko.py')
dim_1b = instrument2('GPIB0::10::INSTR') #'Yoko M' 
dim_1b.set_mode(1) #V mode
dim_1b.set_vrange(4) #2  10mV, 3  100mV, 4  1V, 5  10V, 6  30V
dim_1b.sweep_v(0.0,4) #sweep to 0 V
sleep(4.2)
dim_1b.output(1) #turn Yoko ON
sleep(1)

dim_2name = 'Yoko V' 
dim_2start = -10e-3
dim_2stop = 10e-3
dim_2pt = 201
execfile('Yoko.py')
dim_2 = instrument2('GPIB0::13::INSTR') #'Yoko V' 
dim_2.set_mode(1)
dim_2.set_vrange(3) 
dim_2.sweep_v(0.0,4)
sleep(4.2)
dim_2.output(1)
sleep(1)

dim_3name = 'Nothing' 
dim_3start = 0
dim_3stop = 0
dim_3pt = 1
#dim_3 = 0 #Nothing

'''
#Other Equipment
execfile('keithley2000.py')
vm = instrument3('GPIB0::29::INSTR')
vm.optimise()
sleep(0.1)
vm.testspeed()
'''

#for the VNA I want 4 data files for Real, Imag, MAG, Phase
filen_1 = filen_0 + '_real'  + '.mtx'
filen_2 = filen_0 + '_imag'  + '.mtx'
filen_3 = filen_0 + '_mag'   + '.mtx'
filen_4 = filen_0 + '_phase' + '.mtx'
head_1 = ['Units', 'S21 _real',
        dim_1b_name, str(dim_1start), str(dim_1stop),
        dim_2name, str(dim_2stop), str(dim_2start),
        dim_3name, str(dim_3start), str(dim_3stop),]
head_2 = ['Units', 'S21 _imag',
        dim_1b_name, str(dim_1start), str(dim_1stop),
        dim_2name, str(dim_2stop), str(dim_2start),
        dim_3name, str(dim_3start), str(dim_3stop),]

head_3 = ['Units', 'S21 _mag',
        dim_1b_name, str(dim_1start), str(dim_1stop),
        dim_2name, str(dim_2stop), str(dim_2start),
        dim_3name, str(dim_3start), str(dim_3stop),]
head_4 = ['Units', 'S21 _phase',
        dim_1b_name, str(dim_1start), str(dim_1stop),
        dim_2name, str(dim_2stop), str(dim_2start),
        dim_3name, str(dim_3start), str(dim_3stop),]
matrix3d_1 = np.zeros((dim_3pt, dim_2pt, dim_1pt))
matrix3d_2 = np.zeros((dim_3pt, dim_2pt, dim_1pt))
matrix3d_3 = np.zeros((dim_3pt, dim_2pt, dim_1pt))
matrix3d_4 = np.zeros((dim_3pt, dim_2pt, dim_1pt))

dim_1lin = np.linspace(dim_1start,dim_1stop,dim_1pt)
dim_2lin = np.linspace(dim_2start,dim_2stop,dim_2pt)
dim_3lin = np.linspace(dim_3start,dim_3stop,dim_3pt)

ask_overwrite(folder+filen_1)
copy_file(thisfile, filen_0, folder) #backup this script

#execute sweep
print 'req est time (min):'+str(dim_3pt*dim_2pt*dim_1pt*0.03/60)
t0 = time()
for kk in range(dim_3pt): 
    ''' Do Dim 3 '''
    dim_3val = dim_3lin[kk] 
    #dim_3.sweep_v(dim_3val, 5) #Do nothing at the moment
    #sleep(5.2)
    '''Do Dim 2 prep'''
    dim_2.sweep_v(dim_2start, 5)
    sleep(5.2)
    
    for jj in range(dim_2pt):
        '''Do Dim 2 '''
        dim_2val = dim_2lin[jj] 
        dim_2.sweep_v(dim_2val, 0.1)

        '''Do Dim 1 prep'''
        dim_1b.sweep_v(dim_1b_start, 5)
        sleep(5.2)
        '''Do Dim 1 '''
        #Sweep magnet while measuring with the VNA
        #Start VNA sweep
        dim_1.init_sweep()
        #Start 
        dim_1b.sweep_v(dim_1b_stop, dim_1b_time)        
        #Wait for both to be finished
        sleep(dim_1b_time+1)
        vdata = dim_1.get_data2() # np.array(real+ i* imag)
        phase_data = np.angle(vdata)        
        matrix3d_1[kk,jj] = vdata.real
        matrix3d_2[kk,jj] = vdata.imag
        matrix3d_3[kk,jj] = np.absolute(vdata)
        matrix3d_4[kk,jj] = np.unwrap(phase_data)
        savemtx(folder + filen_1, matrix3d_1, header = head_1)
        savemtx(folder + filen_2, matrix3d_2, header = head_2)
        savemtx(folder + filen_3, matrix3d_3, header = head_3)
        savemtx(folder + filen_4, matrix3d_4, header = head_4)
        
        t1 = time()
        remaining_time = ((t1-t0)/(jj+1)*dim_2pt - (t1-t0))
        print 'req est time (h):'+str(remaining_time/3600)

#Finish measurements
#return Yoko to zero and switch off
dim_1b.sweep_v(0, 5)
dim_2.sweep_v(0, 5)
sleep(5.2)
dim_1b.output(0) #turn Yoko Off
dim_2.output(0)