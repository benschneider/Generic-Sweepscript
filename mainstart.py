'''
Generic Sweep script


22/06/2015
- B
'''

#import visa
import numpy as np
from time import sleep
from time import time

execfile('parsers.py')

execfile('RSZNB20.py')
vna = instrument1('TCPIP::169.254.107.192::INSTR')

execfile('Yoko.py')
magnet = instrument2('GPIB0::10::INSTR')
vsource = instrument2('GPIB0::13::INSTR')

execfile('keithley2000.py')
vm2000 = instrument3('GPIB0::29::INSTR')


filen_1 = 'ben_data_130.mtx'
start_v = -0.1
stop_v = 0.15
v_swt = 297 #set time for voltage sweep

averages = 100

'''
vdata = get_vnadata()  #grab data from vna to know data sizes...


#Prepare results matrix
matrix3d = np.zeros(( 4, averages, vdata.shape[0]))

t0 = time()

#execute sweep
for jj in range(averages):
    #voltage - start
    sweep_v(start_v,5)
    sleep(6)

    #start VNA sweep


    #voltage - end
    sweep_v(stop_v,v_swt)
    sleep(v_swt+2)

    #grab [real, imag]  from VNA
    vdata = get_vnadata()

    #save into the matrix
    matrix3d[0,jj] = vdata.real
    matrix3d[1,jj] = vdata.imag
    matrix3d[2,jj] = np.absolute(vdata)
    phase_data = np.angle(vdata)
    matrix3d[3,jj] = np.unwrap(phase_data)


    #store data into a file
    head1 = ['Units', 'real-imag-mag-phase',
            'Yoko', str(start_v), str(stop_v),
            'Y-label', str(jj), '0',
            'Z-label', '1', '4']
    savemtx(filen_1, matrix3d, header = head1)

    t1 = time()
    remaining_time = ((t1-t0)/(jj+1)*averages - (t1-t0))
    print remaining_time #seconds

#Finish measurements
#return Yoko to zero and switch off
sweep_v(0,5)
sleep(6)
#yoko.write('O0 E')
#Leftovers to be deleted later
#def set_voltage(value):
#    yoko.write('S'+str(value)+' E')
'''