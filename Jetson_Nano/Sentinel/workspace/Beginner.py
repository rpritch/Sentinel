#
# Copyright (C) 2019 nanoLambda, Inc.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from NanoLambdaNSP32 import *

"""A clean and simple example for beginners to start with NSP32."""

#***********************************************************************************
# modify this section to fit your need                                             *
#***********************************************************************************

PinRst		= 13  	# pin Reset (the number is based on GPIO.BOARD)
PinReady	= 15 	# pin Ready (the number is based on GPIO.BOARD)

#nsp32 = NSP32(PinRst, PinReady, DataChannelEnum.Spi, spiBus = 0, spiDevice = 0)		# use SPI channel
nsp32 = NSP32(PinRst, PinReady, DataChannelEnum.Uart, uartPotName = '/dev/ttyTHS1')	    # use UART channel

#***********************************************************************************

# inform user to press ENTER to exit the program
print("\n*** press ENTER to exit program ***\n")

# initialize NSP32
nsp32.Init()

# =============== standby ===============
nsp32.Standby(0)

# =============== wakeup ===============
nsp32.Wakeup()

# =============== hello ===============
nsp32.Hello(0)

# =============== get sensor id ===============
nsp32.GetSensorId(0)
print('sensor id = ' + nsp32.GetReturnPacket().ExtractSensorIdStr())

# =============== get wavelength ===============
nsp32.GetWavelength(0)

infoW = nsp32.GetReturnPacket().ExtractWavelengthInfo()
print('first element of wavelength = ', infoW.Wavelength[0])
# TODO: get more information you need from infoW

# =============== spectrum acquisition ===============
nsp32.AcqSpectrum(0, 32, 3, False)	# integration time = 32; frame avg num = 3; disable AE

# "AcqSpectrum" command takes longer time to execute, the return packet is not immediately available
# when the acquisition is done, a "ready trigger" will fire, and nsp32.GetReturnPacketSize() will be > 0	
while nsp32.GetReturnPacketSize() <= 0 :
	# TODO: can go to sleep or do other tasks here
	
	nsp32.UpdateStatus()	# call UpdateStatus() to check async result

infoS = nsp32.GetReturnPacket().ExtractSpectrumInfo()
print('first element of spectrum = ', infoS.Spectrum[0])
# TODO: get more information you need from infoS

# press ENTER to exit the program
input()
