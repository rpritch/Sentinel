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

import traceback
import enum
import time
import threading
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import style
style.use("ggplot")
import matplotlib.animation as animation
from NanoLambdaNSP32 import *

"""A GUI program to visualize the spectrum measured by NSP32"""

class SpectrumMeter:
	"""spectrum meter application"""

	class _AppRunModeEnum(enum.IntEnum):
		"""app run mode enumeration"""

		Disconnected	= 0
		Connected		= 1
		Spectrum		= 2

	def __init__(self):
		"""__init__ method"""

		#***********************************************************************************
		# modify this section to fit your need                                             *
		#***********************************************************************************

		PinRst		= 13  	# pin Reset (the number is based on GPIO.BOARD)
		PinReady	= 15 	# pin Ready (the number is based on GPIO.BOARD)

		#self._nsp32 = NSP32(PinRst, PinReady, DataChannelEnum.Spi, spiBus = 0, spiDevice = 0)		# use SPI channel
		self._nsp32 = NSP32(PinRst, PinReady, DataChannelEnum.Uart, uartPotName = '/dev/ttyTHS1')	# use UART channel

		#***********************************************************************************
		
		self._root = tk.Tk()

		self._lblSensorId = None
		self._btnCmdSpectrum = None
		self._lblIntegrationTime = None
		self._opmIntegrationTime = None
		self._varSelectedIntegrationTime = None
		self._opmFrameAvgNum = None
		self._varSelectedFrameAvgNum = None
		self._varEnableAEChecked = None
		self._lblRoundTripTime = None
		self._lblCieX = None
		self._lblCieY = None
		self._lblCieZ = None

		self._wavelength = None				# wavelength data
		self._stopSpectrum = False			# stop spectrum acquisition and discard return packets
		self._curAppMode = SpectrumMeter._AppRunModeEnum.Disconnected	# current app mode

		self._figure = None					# spectrum figure
		self._plot = None					# spectrum plot
		self._plotDataX = None				# x data series for plot
		self._plotDataY = None				# y data series for plot
		self._plotAnimation = None			# plot animation

		self._CreateUi()	# create UI components
		self._Init()		# UI and button event handler initialization

		# start the NSP32 initialization thread
		thread = threading.Thread(target = self._NSP32Init)
		thread.daemon = True
		thread.start()

		self._root.mainloop()

	def __del__(self):
		"""__del__ method"""
	
		try :
			self._root.quit()
			self._root.destroy()
		except :
			pass

	def _Init(self):
		"""UI and button event handler initialization"""

		# add integration time options to the OptionMenu
		self._opmIntegrationTime['menu'].delete(0, 'end')
		self._varSelectedIntegrationTime.set('32')	# set default to 32
		
		for option in range(1, 501) :
			self._opmIntegrationTime['menu'].add_command(label = option, command = tk._setit(self._varSelectedIntegrationTime, option))		

		# add frame avg num options to the OptionMenu
		self._opmFrameAvgNum['menu'].delete(0, 'end')
		self._varSelectedFrameAvgNum.set('3')	# set default to 3
		
		for option in range(1, 41) :
			self._opmFrameAvgNum['menu'].add_command(label = option, command = tk._setit(self._varSelectedFrameAvgNum, option))		

		# add event handler to "Start/Stop Spectrum" button
		self._btnCmdSpectrum['command'] = self._BtnCmdSpectrumClicked

		# set GUI
		self._SetGuiByAppMode(SpectrumMeter._AppRunModeEnum.Disconnected)
		
		# set spectrum plot animation
		self._animation = animation.FuncAnimation(self._figure, self._PlotSpectrum, interval = 300)

	def _NSP32Init(self):
		"""NSP32 initialization"""
		
		self._nsp32.Init()

		# get sensor id
		self._nsp32.GetSensorId(0)
		self._lblSensorId['text'] = self._nsp32.GetReturnPacket().ExtractSensorIdStr()

		# get wavelength
		self._nsp32.GetWavelength(0)
		self._wavelength = self._nsp32.GetReturnPacket().ExtractWavelengthInfo().Wavelength
				
		# set GUI
		self._SetGuiByAppMode(SpectrumMeter._AppRunModeEnum.Connected)
			
	def _PlotSpectrum(self, i):
		"""plot spectrum"""

		try :
			dataX, dataY = self._plotDataX, self._plotDataY
		
			if dataX is not None and dataY is not None :
				self._plot.clear()
				self._plot.plot(dataX, dataY)
		except :
			pass

	def _SetGuiByAppMode(self, appMode):
		"""set GUI by different app mode
		
		Args:
			appMode(AppRunModeEnum): current app mode
		
		"""
		
		self._curAppMode = appMode 	# record the current app mode
		
		if appMode == SpectrumMeter._AppRunModeEnum.Disconnected :
			self._lblSensorId['text'] = '  Retrieving...  '
			self._btnCmdSpectrum.state(['disabled'])
			self._UpdateSaturationStatus(False)

		elif appMode == SpectrumMeter._AppRunModeEnum.Connected :
			self._btnCmdSpectrum.state(['!disabled'])
			self._btnCmdSpectrum['text'] = 'Spectrum'
			self._UpdateSaturationStatus(False)

		elif appMode == SpectrumMeter._AppRunModeEnum.Spectrum :
			self._btnCmdSpectrum['text'] = 'Stop'
			self._lblCieX['text'] = '-'
			self._lblCieY['text'] = '-'
			self._lblCieZ['text'] = '-'
			self._lblRoundTripTime['text'] = ''
			self._UpdateSaturationStatus(False)

	def _UpdateSaturationStatus(self, isSaturated):
		"""update saturation status on UI
		
		Args:
			isSaturated(bool): True for saturated; False for not saturated
		
		"""

		# use different color to identify the saturation status
		style = ttk.Style()
		style.configure('Red.TLabel', foreground = 'red')

		self._lblIntegrationTime.configure(style = 'Red.TLabel' if isSaturated else 'TLabel')

	def _AcqSpectrum(self):
		"""start spectrum acquisition"""

		while(not self._stopSpectrum) :
			# record the single command round trip start time
			roundTripTimeStart = time.time()

			# start acquisition
			self._nsp32.AcqSpectrum(0, int(self._varSelectedIntegrationTime.get()), int(self._varSelectedFrameAvgNum.get()), self._varEnableAEChecked.get() == 1)

			# wait for acquisition done
			while self._nsp32.GetReturnPacketSize() <= 0 :
				if self._stopSpectrum :
					return
			
				self._nsp32.UpdateStatus()	# call UpdateStatus() to check async result

			# calculate the round trip time and display
			elapsedTime = time.time() - roundTripTimeStart
			self._lblRoundTripTime['text'] = int(elapsedTime * 1000)
			
			# update spectrum data to plot data series
			info = self._nsp32.GetReturnPacket().ExtractSpectrumInfo()

			self._plotDataX = self._wavelength
			self._plotDataY = info.Spectrum
			
			# if AE is enabled, let the OptionMenu auto select the found integration time
			if self._varEnableAEChecked.get() == 1 :
				self._varSelectedIntegrationTime.set(str(info.IntegrationTime))

			# update saturation status
			self._UpdateSaturationStatus(info.IsSaturated)

			# display XYZ
			self._lblCieX['text'] = round(info.X, 2)
			self._lblCieY['text'] = round(info.Y, 2)
			self._lblCieZ['text'] = round(info.Z, 2)

	def _BtnCmdSpectrumClicked(self):
		"""'Start/Stop Spectrum' button click event handler"""

		if self._curAppMode == SpectrumMeter._AppRunModeEnum.Spectrum :
			# stop spectrum acquisition
			self._stopSpectrum = True
			self._SetGuiByAppMode(SpectrumMeter._AppRunModeEnum.Connected)
		else :
			# start spectrum acquisition
			self._SetGuiByAppMode(SpectrumMeter._AppRunModeEnum.Spectrum)
			self._stopSpectrum = False

			# start spectrum acquisition thread
			thread = threading.Thread(target = self._AcqSpectrum)
			thread.daemon = True
			thread.start()

	def _CreateUi(self):
		"""create UI components"""
	
		# setup the window		
		self._root.title('NSP32 Spectrum Meter')
		self._root.resizable(0, 0)

		frmAll = tk.Frame(self._root)
		frmAll.pack()

		# sensor id frame
		frmSensorId = ttk.Labelframe(frmAll, text = 'Sensor ID')
		frmSensorId.grid(row = 0, column = 0, sticky = 'nwe', padx = 5, pady = 5)

		# sensor id frame -> sensor id label
		self._lblSensorId = ttk.Label(frmSensorId, text = '-')
		self._lblSensorId.pack(padx = 5, pady = 5)

		# spectrum plot
		self._figure = Figure(figsize = (5, 4), dpi = 100)
		self._plot = self._figure.add_subplot(111)

		canvas = FigureCanvasTkAgg(self._figure, master = frmAll)
		canvas.draw()
		canvas.get_tk_widget().grid(row = 0, column = 1, sticky = 'nwes')

		# spectrum info frame
		frmSpectrumInfo = ttk.LabelFrame(frmAll, text = 'Spectrum')
		frmSpectrumInfo.grid(row = 3, column = 0, columnspan = 2, sticky = 'nwes', padx = 5, pady = 5)
		
		for x in range(7) :
			frmSpectrumInfo.columnconfigure(x, weight = 1)

		# spectrum info frame -> spectrum button
		self._btnCmdSpectrum = ttk.Button(frmSpectrumInfo, text = 'Spectrum')
		self._btnCmdSpectrum.grid(row = 0, column = 0, sticky = 'we', padx = 3, pady = 2)
		
		# spectrum info frame -> integration time
		self._lblIntegrationTime = ttk.Label(frmSpectrumInfo, text = 'IntegTime: ')
		self._lblIntegrationTime.grid(row = 1, column = 0, sticky = 'w', padx = 3, pady = 2)
		
		self._varSelectedIntegrationTime = tk.StringVar(self._root)
		self._opmIntegrationTime = ttk.OptionMenu(frmSpectrumInfo, self._varSelectedIntegrationTime, None)
		self._opmIntegrationTime.grid(row = 1, column = 1, sticky = 'we', padx = 3, pady = 2)

		# spectrum info frame -> frame avg num
		lblFrameAvgNum = ttk.Label(frmSpectrumInfo, text = 'FrameAvg: ')
		lblFrameAvgNum.grid(row = 1, column = 2, sticky = 'w', padx = 3, pady = 2)
		
		self._varSelectedFrameAvgNum = tk.StringVar(self._root)
		self._opmFrameAvgNum = ttk.OptionMenu(frmSpectrumInfo, self._varSelectedFrameAvgNum, None)
		self._opmFrameAvgNum.grid(row = 1, column = 3, sticky = 'we', padx = 3, pady = 2)

		# spectrum info frame -> AE checkbox
		self._varEnableAEChecked = tk.IntVar()
		chkbxEnableAE = ttk.Checkbutton(frmSpectrumInfo, text = 'AE', variable = self._varEnableAEChecked, width = 8)
		chkbxEnableAE.grid(row = 1, column = 4, sticky = 'w', padx = 3, pady = 2)

		# spectrum info frame -> round trip time
		lblTime = ttk.Label(frmSpectrumInfo, text = 'Time(ms): ')
		lblTime.grid(row = 1, column = 5, sticky = 'w', padx = 3, pady = 2)
		
		self._lblRoundTripTime = ttk.Label(frmSpectrumInfo, text = '-', width = 8)
		self._lblRoundTripTime.grid(row = 1, column = 6, sticky = 'w', padx = 3, pady = 2)
		
		# spectrum info frame -> X
		lblCieX = ttk.Label(frmSpectrumInfo, text = 'X: ')
		lblCieX.grid(row = 2, column = 0, sticky = 'w', padx = 3, pady = 2)
		
		self._lblCieX = ttk.Label(frmSpectrumInfo, text = '-', width = 8)
		self._lblCieX.grid(row = 2, column = 1, sticky = 'w', padx = 3, pady = 2)
		
		# spectrum info frame -> Y
		lblCieY = ttk.Label(frmSpectrumInfo, text = 'Y: ')
		lblCieY.grid(row = 2, column = 2, sticky = 'w', padx = 3, pady = 2)
		
		self._lblCieY = ttk.Label(frmSpectrumInfo, text = '-', width = 8)
		self._lblCieY.grid(row = 2, column = 3, sticky = 'w', padx = 3, pady = 2)

		# spectrum info frame -> Z
		lblCieZ = ttk.Label(frmSpectrumInfo, text = 'Z: ')
		lblCieZ.grid(row = 2, column = 4, sticky = 'w', padx = 3, pady = 2)
		
		self._lblCieZ = ttk.Label(frmSpectrumInfo, text = '-', width = 8)
		self._lblCieZ.grid(row = 2, column = 5, sticky = 'w', padx = 3, pady = 2)


# start the program
try :
	app = SpectrumMeter()
except Exception as e :
	print('error occurred: ' + str(e))
	print(traceback.format_exc())
