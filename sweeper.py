'''
(Uploaded and intended use is for myself)
This little script sweeps both a Yokogawa Voltage source and a VNA in CW mode,
most setting on the VNA still have to be set by hand first.
(This is more of a quick and dirty measurement)
The data is then stored into an *.mtx file format (1st 2 lines is the header (sizes, limits e.t.c), rest of the file is a 3d numpy data array in binary).
This file can then be quickly opened with a program called 'spyview'

-Cheers,
Ben
'''
import visa
import numpy as np
from time import sleep
from time import time

execfile('parsers.py')

filen_1 = 'ben_data_019.mtx'

start_v = -0.1
stop_v = 0.15
v_swt = 297 #set time for voltage sweep

averages = 100


#Voltage sweeper
yoko = visa.instrument('GPIB0::10::INSTR')
yoko.write('F1 E') #F1 -- Voltage mode, F5 -- Current mode
range1 = 4 # 2 10mV, 3 100mV, 4 1V, 5 10V, 6 30V
yoko.write('R'+str(range1) +' E')
yoko.write('O1 E') # output on O1, off O0


def sweep_v(value,sweeptime):
    yoko.write('M1 PI'+str(sweeptime)+' SW'+str(sweeptime)+' PRS S'+str(value)+' PRE RU2')


#VNA prepare VNA by hand first
vna = visa.instrument('TCPIP::169.254.107.192::INSTR')
vna.write(':ABOR;:INIT:CONT OFF') #abort current sweep
vna.write(':SENS:AVER:CLE') #clear prev averages
vna.write(':SENS:SWE:COUN 1') #set counts to 1

def get_vnadata():
    sData = vna.ask(':FORM REAL,32;CALC:DATA? SDATA') #grab data from VNA
    i0 = sData.find('#')
    nDig = int(sData[i0+1])
    nByte = int(sData[i0+2:i0+2+nDig])
    nData = nByte/4
    nPts = nData/2
    # get data to numpy array
    vData = np.frombuffer(sData[(i0+2+nDig):(i0+2+nDig+nByte)],
                          dtype='>f', count=nData)
    # data is in I0,Q0,I1,Q1,I2,Q2,.. format, convert to complex
    mC = vData.reshape((nPts,2))
    vComplex = mC[:,0] + 1j*mC[:,1]
    return vComplex

vdata = get_vnadata()  #grab data from vna to know data sizes...
vdata.shape
#before start get data size
matrix3d = np.zeros(( 4, averages, vdata.shape[0]))

t0 = time()

#execute sweep
for jj in range(averages):
    #voltage - start
    sweep_v(start_v,5)
    sleep(6)

    #start VNA sweep
    vna.write(':INIT:IMM;*OPC')

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
    print ((t1-t0)/(jj+1)*averages - (t1-t0))

#return Yoko to zero and switch off
sweep_v(0,5)
sleep(6)
#yoko.write('O0 E')
#Leftovers to be deleted later
#def set_voltage(value):
#    yoko.write('S'+str(value)+' E')