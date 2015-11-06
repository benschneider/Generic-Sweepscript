import InstrumentDriver
from InstrumentConfig import InstrumentQuantity
import PXIDigitizer_wrapper
import numpy as np
import time
import h5py
from cmath import rect

class afDigitizer_BS(InstrumentDriver.InstrumentWorker):
    """ This class implements a digitizer in the PXI rack"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        # check communication
        try:
            # open connection
            self.digitizer = PXIDigitizer_wrapper.afDigitizer_BS()
            self.digitizer.create_object()
            # get address strings
            sVisaDigitizer = self.dComCfg['address']
            sVisaLO = self.getValue('Local oscillator VISA')
            # keep track of number of samples and old I,Q,R and theta values
            self.nSamples = int(self.getValue('Number of samples'))
            self.nTriggers = int(self.getValue('Number of triggers'))
            self.nAverages_per_trigger = int(self.getValue('Averages per trigger'))
            self.Overload = 0
            self.cAvgSignal = None
            self.cAvgSignal2 = None
            self.cTrace = None
            self.vPTrace = None
            self.vPowerMeanUnAvg = None♠
            self.MeanMag = None
            self.MeanPhas = None
            self.vMeanUnAvg = None
            self.cRaw = None
            self.dPower = None
            self.bRaw = self.getValue('Retrive raw data')
            self.bCollectHistogram = self.getValue('Collect IQ Histogram')
            self.nAbove = 0
            self.bSetBandWidth = self.getValue('Set IQ Bandwidth manually')
            self.dBandWidthAim = self.getValue('IQ Bandwidth')
            self.dBandWidthAcc = self.getValue('IQ Bandwidth')
            self.bCutTrace = self.getValue('Cut out part of the trace')
            self.nStartSample = int(self.getValue('Start Sample'))
            self.nStopSample = int(self.getValue('Stop Sample'))
            self.nHistPath = self.getValue('Histogram path')
            self.dFreq = self.getValue('RF Frequency')
            self.nBins = 0
            self.sHistPath = self.getValue('Histogram path')
            # boot instruments
            self.digitizer.boot_instrument(sVisaLO, sVisaDigitizer)
            # set modulation mode to generic
            self.digitizer.modulation_mode_set(5)

        except PXIDigitizer_wrapper.Error as e:
            # re-cast afdigitizer errors as a generic communication error
            msg = str(e)
            raise InstrumentDriver.CommunicationError(msg)

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        # check if digitizer object exists
        if not hasattr(self, 'digitizer'):
            # do nothing, object doesn't exist (probably was never opened)
            return
        try:
            # set max input level to +30dB
            self.digitizer.rf_rf_input_level_set(30)
            # do not check for error if close was called with an error
            self.digitizer.close_instrument(bCheckError=not bError)
        except PXIDigitizer_wrapper.Error as e:
            # do not raise errors if error already exists
            if not bError:
                # re-cast errors as a generic communication error
                msg = str(e)
                raise InstrumentDriver.CommunicationError(msg)
        finally:
            try:
                # destroy dll object
                self.digitizer.destroy_object()
                del self.digitizer
            except:
                # never return error here
                pass

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        try:
            # proceed depending on command
            if quant.name == 'RF Frequency':
                self.dFreq = value
                self.digitizer.rf_centre_frequency_set(value)
                # Reset the stored traces
                self.cAvgSignal = None
                self.cAvgSignal2 = None
                self.cTrace = None
                self.vPTrace = None
                self.vPowerMeanUnAvg = None
                self.cRaw = None
                self.dPower = None
                self.vMeanUnAvg = None
                self.MeanMag = None
                self.MeanPhas = None
            elif quant.name == 'Max input level':
                self.digitizer.rf_rf_input_level_set(value)
            elif quant.name == 'Sampling rate':
                self.digitizer.modulation_generic_sampling_frequency_set(value)
            elif quant.name == 'Number of samples':
                self.nSamples = int(value)
            elif quant.name == 'Cut out part of the trace':
                self.bCutTrace = value
            elif quant.name == 'Start Sample':
                self.nStartSample = int(value)
            elif quant.name == 'Stop Sample':
                self.nStopSample = int(value)
            elif quant.name == 'Histogram path':
                self.sHistPath = str(value)
            elif quant.name == 'Histogram bin number':
                self.nBins = value
            elif quant.name == 'Collect IQ Histogram':
                self.bCollectHistogram = value
            elif quant.name == 'Remove DC offset':
                self.digitizer.rf_remove_dc_offset_set(bool(value))
            elif quant.name == 'Trigger Source':
                # combo, get index
                if isinstance(value, (str, unicode)):
                    valueIndex = quant.combo_defs.index(value)
                else:
                    valueIndex = long(value)
                self.digitizer.trigger_source_set(valueIndex)
            elif quant.name == 'Trigger type':
                # Dont do for SW
                TriggerSourceValue = self.digitizer.trigger_source_get()
                if TriggerSourceValue is not 32:
                    # combo, get index
                    if isinstance(value, (str, unicode)):
                        valueIndex = quant.combo_defs.index(value)
                    else:
                        valueIndex = int(value)
                    self.digitizer.trigger_type_set(valueIndex)
            elif quant.name == 'Trigger polarity':
                # Dont do for SW
                TriggerSourceValue = self.digitizer.trigger_source_get()
                if TriggerSourceValue is not 32:
                    # combo, get index
                    if isinstance(value, (str, unicode)):
                        valueIndex = quant.combo_defs.index(value)
                    else:
                        valueIndex = int(value)
                    self.digitizer.trigger_polarity_set(valueIndex)
            elif quant.name == 'Number of triggers':
                self.nTriggers = int(value)
            elif quant.name == 'Averages per trigger':
                self.nAverages_per_trigger = int(value)
            elif quant.name == "Number of pretrigger samples":
                self.digitizer.trigger_pre_edge_trigger_samples_set(int(value))
            # Only return I and Q vectors if needed,
            # could be a big vector if many triggers and samples
            elif quant.name == 'Retrive raw data':
                self.bRaw = value
            elif quant.name == 'LO Reference Mode':
                # combo, get index
                if isinstance(value, (str, unicode)):
                    valueIndex = quant.combo_defs.index(value)
                else:
                    valueIndex = int(value)
                self.digitizer.lo_reference_set(valueIndex)
            elif quant.name == 'LO Above or Below':
                # combo, get index
                if isinstance(value, (str, unicode)):
                    valueIndex = quant.combo_defs.index(value)
                else:
                    valueIndex = int(value)
                self.digitizer.rf_userLOPosition_set(valueIndex)

            elif quant.name == 'Set IQ Bandwidth manually':
                self.bSetBandWidth = value
            elif quant.name == 'IQ Bandwidth':
                self.dBandWidthAim = value
                self.bSetBandWidth = self.getValue('Set IQ Bandwidth manually')
                if self.bSetBandWidth:
                    self.dBandWidthAcc = self.digitizer.trigger_IQ_bandwidth_set(self.dBandWidthAim, self.nAbove)
            elif quant.name == 'Bandwidth above or below':
                if isinstance(value, (str, unicode)):
                    valueIndex = quant.combo_defs.index(value)
                else:
                    valueIndex = int(value)
                self.nAbove = valueIndex
                self.bSetBandWidth = self.getValue('Set IQ Bandwidth manually')
                if self.bSetBandWidth:
                    self.dBandWidthAcc = self.digitizer.trigger_IQ_bandwidth_set(self.dBandWidthAim, self.nAbove)

            return value
        except PXIDigitizer_wrapper.Error as e:
            # re-cast errors as a generic communication error
            msg = str(e)
            raise InstrumentDriver.CommunicationError(msg)


    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        try:
            # proceed depending on command
            if quant.name == 'RF Frequency':
                value = self.digitizer.rf_centre_frequency_get()
            elif quant.name == 'Max input level':
                value = self.digitizer.rf_rf_input_level_get()
            elif quant.name == 'Sampling rate':
                value = self.digitizer.modulation_generic_sampling_frequency_get()
            elif quant.name == 'Number of samples':
                value = self.nSamples
            elif quant.name == 'Cut out part of the trace':
                value = self.bCutTrace
            elif quant.name == 'LO Reference Mode':
                value = quant.getValueString(self.digitizer.lo_reference_get())
            elif quant.name == 'Start Sample':
                value = self.nStartSample
            elif quant.name == 'Stop Sample':
                value = self.nStopSample
            elif quant.name == 'Remove DC offset':
                value = self.digitizer.rf_remove_dc_offset_get()
            elif quant.name == 'Trigger Source':
                value = self.digitizer.trigger_source_get()
                value = quant.getValueString(value)
            elif quant.name == 'Trigger type':
                value = self.digitizer.trigger_type_get()
                value = quant.getValueString(value)
            elif quant.name == 'LO Above or Below':
                value = self.digitizer.rf_userLOPosition_get()
                value = quant.getValueString(value)
            elif quant.name == 'Trigger polarity':
                value = self.digitizer.trigger_polarity_get()
                value = quant.getValueString(value)
            elif quant.name == 'Number of triggers':
                value = self.nTriggers
            elif quant.name == 'Averages per trigger':
                value = self.nAverages_per_trigger
            elif quant.name == 'Number of pretrigger samples':
                value=self.digitizer.trigger_pre_edge_trigger_samples_get()
            elif quant.name == 'Collect IQ Histogram':
                value = self.bCollectHistogram
            elif quant.name == 'Retrive raw data':
                value = self.bRaw
            elif quant.name == 'Histogram bin number':
                value = self.nBins
            elif quant.name == 'Histogram path':
                value = self.sHistPath
            elif quant.name == 'Trace':
                value = self.getTraceDict(self.getIQTrace())
            elif quant.name == 'Power trace':
                value = self.getTraceDict(self.getPTrace())
            elif quant.name == 'AvgTrace':
                value = self.getTraceAvg()
            elif quant.name == 'AvgMagPhase':
                value = self.getTraceMagPhase()
            elif quant.name == 'Power mean unaveraged':
                value = self.getPowerMeanUnAvg()
            elif quant.name == 'Voltage mean unaveraged':
                value = self.getMeanUnAvg()
            # Only return I and Q vectors if needed, could be a big vector if many triggers and samples
            elif quant.name == 'Raw data':
                if self.bRaw:
                    value = self.getRawData()
            elif quant.name == 'IQ Bandwidth':
                value = self.dBandWidthAcc
            elif quant.name == 'Bandwidth above or below':
                value = quant.getValueString(self.nAbove)
            elif quant.name == 'Set IQ Bandwidth manually':
                value = self.bSetBandWidth
            elif quant.name == 'AvgPower':
                value = self.getAvgPower()
            elif quant.name == 'Level correction':
                value = self.digitizer.rf_level_correction_get()
            return value
        except PXIDigitizer_wrapper.Error as e:
            # re-cast errors as a generic communication error
            msg = str(e)
            raise InstrumentDriver.CommunicationError(msg)

    # Return the signal along with its time vector
    def getTraceDict(self, vSignal):
        dSampFreq = self.getValue('Sampling rate')
        nPreTriggerSamples = int(self.getValue('Number of pretrigger samples'))
        return InstrumentQuantity.getTraceDict(vSignal, t0=-nPreTriggerSamples/dSampFreq, dt=1/dSampFreq)

    # Check if the ADC overloaded and if it was put the max input level to +30dBm and raise an error
    def checkADCOverload(self):
        if self.digitizer.check_ADCOverload():
            self.Overload = self.Overload + 1
            time.sleep(0.2)
            if self.Overload > 3:
                self.digitizer.rf_rf_input_level_set(30)
                raise InstrumentDriver.CommunicationError('ADC overloaded hence the measurement is stopped and the max input level on the digitizer is put to +30 dBm')
        else:
            self.Overload = 0

    def getIQTrace(self):
        """Return I and Q signal in time as a complex vector, resample the signal if needed"""
        # check if old value exists
        if self.cTrace is None:
            # get new trace
            self.sampleAndAverage()
        # return and clear old value for selected signal
        vTrace = self.cTrace
        self.cTrace = None
        return vTrace

    def getPTrace(self):
        """Return the power in time as a vector, resample the signal if needed"""
        # check if old value exists
        if self.vPTrace is None:
            # get new trace
            self.sampleAndAverage()
        # return and clear old value for selected signal
        vTrace = self.vPTrace
        self.vPTrace = None
        return vTrace

    def getRawData(self):
        """Return the raw unaveraged data, if needed resample the signal"""
        # check if old value exists
        if self.cRaw is None:
            # get new trace
            self.sampleAndAverage()
        # return and clear old value for selected signal
        vVector = self.cRaw
        self.cRaw = None
        return vVector

    def getAvgPower(self):
        """Return the averaged power in Watts, resample the signal if necessary"""
        if self.dPower is None:
            self.sampleAndAverage()
        vPower = self.dPower
        self.dPower = None
        return vPower

    def getTraceAvg(self):
        """Return the averaged signal as a complex number I+j*Q, resample the signal if necessary"""
        # check if old value exists
        if self.cAvgSignal is None:
            self.sampleAndAverage()
        # return and clear old value for selected signal
        value = self.cAvgSignal
        self.cAvgSignal = None
        return value

    def getTraceMagPhase(self):
        """Return the averaged Mag signal, resample the signal if necessary"""
        # check if old value exists
        if self.cAvgSignal2 is None:
            self.sampleAndAverage()
        # return and clear old value for selected signal
        value = self.cAvgSignal2
        self.cAvgSignal2 = None
        return value

    def getPowerMeanUnAvg(self):
        """Return the unaveraged power mean, resample the signal if necessary"""
        # check if old value exists
        if self.vPowerMeanUnAvg is None:
            self.sampleAndAverage()
        # return and clear old value for selected signal
        value = self.vPowerMeanUnAvg
        self.vPowerMeanUnAvg = None
        return value

    def getMeanUnAvg(self):
        """Return the unaveraged voltage mean, resample the signal if necessary"""
        # check if old value exists
        if self.vMeanUnAvg is None:
            self.sampleAndAverage()
        # return and clear old value for selected signal
        value = self.vMeanUnAvg
        self.vMeanUnAvg = None
        return value


    def sampleAndAverage(self):
        """Sample the signal, calc I+j*Q theta and store it in the driver object"""

        # Check which trigger source is being used
        TriggerSourceValue = self.digitizer.trigger_source_get()

        # Convert the number of samples and triggers to integers
        nPreTriggers = int(self.getValue('Number of pretrigger samples'))
        nAvgPerTrigger = self.nAverages_per_trigger
        nTotalSamples = self.nSamples*nAvgPerTrigger+nPreTriggers
        dLevelCorrection = self.digitizer.rf_level_correction_get()
        # If the stop sample is set to high, set it to nSamples
        if self.bCutTrace:
            if self.nStopSample > self.nSamples:
                self.nStopSample = self.nSamples
        else: #If we don't want to cut the trace, set start value to 1 and stop value to the last
            self.nStartSample = 1
            self.nStopSample = self.nSamples

        # If the Trigger source is not in 32 = SW trigger, we want to arm the trigger
        if TriggerSourceValue is not 32:
            # Arm the trigger with 2*inSamples
            self.digitizer.trigger_arm_set(nTotalSamples*2)
            self.checkADCOverload()

        # Define two vectors that will be used to collect the raw data
        vI = np.zeros(self.nStopSample-self.nStartSample+1)
        vQ = np.zeros(self.nStopSample-self.nStartSample+1)
        vI2 = np.zeros(self.nStopSample-self.nStartSample+1)
        vQ2 = np.zeros(self.nStopSample-self.nStartSample+1)
        vPowerMean = np.zeros(nAvgPerTrigger*self.nTriggers)
        vIMean = np.zeros(nAvgPerTrigger*self.nTriggers)
        vQMean = np.zeros(nAvgPerTrigger*self.nTriggers)
        MMag = np.zeros(nAvgPerTrigger*self.nTriggers)
        MPhase = np.zeros(nAvgPerTrigger*self.nTriggers)
        # For each trigger, we collect the data
        for i in range(0, self.nTriggers):
            # number 32 corresponds to SW_TRIG, the only trigger mode without external signal
            if TriggerSourceValue is not 32:
                while self.digitizer.data_capture_complete_get()==False:
                    #Sleep some time in between checks
                    self.thread().msleep(1)
                    self.checkADCOverload()

                #Capture the I and Q data
                (lI, lQ) = self.digitizer.capture_iq_capt_mem(nTotalSamples)

                #Re-arm the trigger to prepare the digitizer for the next iteration
                if i < (self.nTriggers-1):
                    self.digitizer.trigger_arm_set(nTotalSamples*2)
                    self.checkADCOverload()
            else:
                #Capture the I and Q data for SW-trig
                self.checkADCOverload()
                (lI, lQ) = self.digitizer.capture_iq_capt_mem(nTotalSamples)

            # The raw data is stored as a long array, continously appending the newly aquired data
            if self.bRaw or self.bCollectHistogram:
                if i == 0:
                    vectorI = np.array(lI)*np.power(10.0,dLevelCorrection/20.0)
                    vectorQ = np.array(lQ)*np.power(10.0,dLevelCorrection/20.0)
                else:
                    vectorI = np.append(vectorI, np.array(lI)*np.power(10.0,dLevelCorrection/20.0))
                    vectorQ = np.append(vectorQ, np.array(lQ)*np.power(10.0,dLevelCorrection/20.0))


            # Fold the data
            reshapedI = np.array(lI).reshape(nAvgPerTrigger, self.nSamples+nPreTriggers)[:,range(self.nStartSample-1, self.nStopSample)]
            reshapedQ = np.array(lQ).reshape(nAvgPerTrigger, self.nSamples+nPreTriggers)[:,range(self.nStartSample-1, self.nStopSample)]
            crep = reshapedI + 1j*reshapedQ

            # We add the aquired data to the vI and vQ arrays
            vI = vI + np.mean(reshapedI, axis=0)
            vQ = vQ + np.mean(reshapedQ, axis=0)
            vI2 = vI2 + np.mean(reshapedI**2, axis=0)
            vQ2 = vQ2 + np.mean(reshapedQ**2, axis=0)
            vPowerMean[i*nAvgPerTrigger:(i+1)*nAvgPerTrigger] = np.mean(reshapedI**2, axis=1)+np.mean(reshapedQ**2, axis=1)
            vIMean[i*nAvgPerTrigger:(i+1)*nAvgPerTrigger] = np.mean(reshapedI, axis=1)
            vQMean[i*nAvgPerTrigger:(i+1)*nAvgPerTrigger] = np.mean(reshapedQ, axis=1)
            
            MMag[i*nAvgPerTrigger:(i+1)*nAvgPerTrigger] = np.mean(np.absolute(crep)*np.power(10.0,dLevelCorrection/20.0), axis=1)
            MPhase[i*nAvgPerTrigger:(i+1)*nAvgPerTrigger] = np.mean(np.angle(crep), axis=1)

        # Average the sum of vI and vQ using the number of triggers and do level correction
        vI = vI/self.nTriggers*np.power(10.0,dLevelCorrection/20.0)
        vQ = vQ/self.nTriggers*np.power(10.0,dLevelCorrection/20.0)
        vIMean = vIMean*np.power(10.0,dLevelCorrection/20.0)
        vQMean = vQMean*np.power(10.0,dLevelCorrection/20.0)
        vI2 = vI2/self.nTriggers*np.power(10.0,dLevelCorrection/10.0)/1000.0 #mW
        vQ2 = vQ2/self.nTriggers*np.power(10.0,dLevelCorrection/10.0)/1000.0
        vPowerMean = vPowerMean*np.power(10.0,dLevelCorrection/10.0)/1000.0

        self.vMeanUnAvg = vIMean+1j*vQMean
        # Create the time trace
        self.cTrace = vI+1j*vQ
        self.vPTrace = (vI2+vQ2)
        self.vPowerMeanUnAvg = vPowerMean
        self.MeanMag = MMag
        self.MeanPhas = MPhase
        # Return the non averaged vectors if wanted
        if self.bRaw:
            self.cRaw = vectorI + 1j*vectorQ

        # If we want to collect IQ histogram
        if self.bCollectHistogram:

          vHistogram = self.CollectHistogram(self.nBins,vectorI, vectorQ)

          f = h5py.File('C:\Users\Juliana\Desktop\Paraamp\Histograms\SampRate\Histogram_' + str(int(self.getValue('Sampling rate'))) + 'Hz_' + time.strftime("%y_%m_%d_%H_%M_%S")+'.hdf5','w')
          f.create_dataset('Histogram',data=vHistogram[0])
          f.create_dataset('Iedges',data=vHistogram[1])
          f.create_dataset('Qedges',data=vHistogram[2])
          f.close()
        # Remove the big vectors (if any)
        if self.bRaw or self.bCollectHistogram:
            vectorI = None
            vectorQ = None

        # Finally, we store the avgeraged signal
        self.cAvgSignal = np.average(vI)+1j*np.average(vQ)
        self.cAvgSignal2 = rect(self.MeanMag, self.MeanPhas)
        self.dPower = np.average(vI2)+np.average(vQ2)

    def CollectHistogram(self,nBins,vI,vQ):

        # Find maximum values in the vectors of I and Q to use for distributing the data in the histogram bins
        vectorImax = np.max(np.abs(vI))
        vectorQmax = np.max(np.abs(vQ))

        # Calculate a start value and step based on the maximum I or Q value and the number of bins
        dStartValue = -np.max((vectorImax,vectorQmax))
        dStep = (2*np.abs(dStartValue))/(self.nBins+1)

        # Construct the I and Q edge vectors for the histogram
        Iedges = np.zeros(self.nBins+1)
        Qedges = np.zeros(self.nBins+1)

        for i in range(0,len(Iedges)):
            Iedges[i] = dStartValue + i*dStep
            Qedges[i] = dStartValue + i*dStep

        #Next, we create a histogram with the raw I and Q data as input
        H, Iedges, Qedges = np.histogram2d(vQ, vI, bins=(Iedges, Qedges))

        return [H, Iedges, Qedges]