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

import enum
import struct
import time
import Jetson.GPIO as GPIO
import spidev
import serial

"""
.. module:: NanoLambdaNSP32
   :synopsis: NSP32 Python API for RPi
.. moduleauthor:: nanoLambda, Inc.
"""

class CmdCodeEnum(enum.IntEnum):
	"""command code enumeration"""

	Unknown			= 0x00		#: unknown
	Prefix0			= 0x03		#: prefix 0
	Prefix1			= 0xBB		#: prefix 1

	Hello			= 0x01		#: hello
	Standby			= 0x04		#: standby
	GetSensorId		= 0x06		#: get sensor id
	GetWavelength	= 0x24		#: get wavelength
	AcqSpectrum		= 0x26		#: spectrum acquisition
	GetSpectrum		= 0x28		#: get spectrum data
	AcqXYZ			= 0x2A		#: XYZ acquisition
	GetXYZ			= 0x2C		#: get XYZ data


class DataChannelEnum(enum.IntEnum):
	"""data channel enumeration"""

	Spi		= 0		#: SPI
	Uart	= 1		#: UART


class WavelengthInfo:
	"""wavelength info"""

	def __init__(self, packetBytes):
		"""__init__ method
		
		Args:
			packetBytes(bytearray): packet data bytes

		"""

		self._packetBytes = packetBytes
		self._numOfPoints = struct.unpack('<I', self._packetBytes[4:8])[0]		# num of points

	@property
	def NumOfPoints(self):
		"""int: num of points"""
		
		return self._numOfPoints

	@property
	def Wavelength(self):
		"""tuple: wavelength data"""
		
		# convert received bytes to short data
		return struct.unpack('<' + 'H' * self._numOfPoints, self._packetBytes[8 : 8 + self._numOfPoints * 2])


class SpectrumInfo:
	"""spectrum info"""

	def __init__(self, packetBytes):
		"""__init__ method
		
		Args:
			packetBytes(bytearray): packet data bytes

		"""

		self._packetBytes = packetBytes
		self._numOfPoints = struct.unpack('<I', self._packetBytes[8:12])[0]	# num of points

	@property
	def NumOfPoints(self):
		"""int: num of points"""

		return self._numOfPoints

	@property
	def IntegrationTime(self):
		"""int: integration time"""
		
		return struct.unpack('<H', self._packetBytes[4:6])[0]

	@property
	def IsSaturated(self):
		"""bool: saturation flag (True for saturated; False for not saturated)"""
		
		return self._packetBytes[6] == 1

	@property
	def Spectrum(self):
		"""tuple: spectrum data"""
		
		# convert received bytes to float data
		return struct.unpack('<' + 'f' * self._numOfPoints, self._packetBytes[12 : 12 + self._numOfPoints * 4])

	@property
	def X(self):
		"""float: X"""
		
		return struct.unpack('<f', self._packetBytes[12 + 135 * 4 : 12 + 135 * 4 + 4])[0]

	@property
	def Y(self):
		"""float: Y"""
		
		return struct.unpack('<f', self._packetBytes[12 + 135 * 4 + 4 : 12 + 135 * 4 + 8])[0]

	@property
	def Z(self):
		"""float: Z"""
		
		return struct.unpack('<f', self._packetBytes[12 + 135 * 4 + 8 : 12 + 135 * 4 + 12])[0]


class XYZInfo:
	"""XYZ info"""

	def __init__(self, packetBytes):
		"""__init__ method
		
		Args:
			packetBytes(bytearray): packet data bytes

		"""

		self._packetBytes = packetBytes

	@property
	def IntegrationTime(self):
		"""int: integration time"""
		
		return struct.unpack('<H', self._packetBytes[4:6])[0]

	@property
	def IsSaturated(self):
		"""bool: saturation flag (True for saturated; False for not saturated)"""
		
		return self._packetBytes[6] == 1

	@property
	def X(self):
		"""float: X"""

		return struct.unpack('<f', self._packetBytes[8:12])[0]

	@property
	def Y(self):
		"""float: Y"""

		return struct.unpack('<f', self._packetBytes[12:16])[0]

	@property
	def Z(self):
		"""float: Z"""

		return struct.unpack('<f', self._packetBytes[16:20])[0]


class ReturnPacket:
	"""return packet"""

	def __init__(self, cmdCode, userCode, isPacketValid, packetBytes):
		"""__init__ method
		
		Args:
			cmdCode(CmdCodeEnum): command function code

			userCode(int): command user code

			isPacketValid(bool): True for valid packet; False for invalid packet

			packetBytes(bytearray): packet data bytes
			
		"""

		self._cmdCode = cmdCode
		self._userCode = userCode
		self._isPacketValid = isPacketValid
		self._packetBytes = packetBytes

	@property
	def CmdCode(self):
		"""CmdCodeEnum: command function code"""
		
		return self._cmdCode

	@property
	def UserCode(self):
		"""int: command user code"""

		return self._userCode

	@property
	def IsPacketValid(self):
		"""bool: check if the packet is valid (True for valid; False for invalid)"""

		return self._isPacketValid

	@property
	def PacketBytes(self):
		"""bytearray: packet data bytes"""
	
		return self._packetBytes

	def ExtractSensorIdStr(self):
		"""extract sensor id string from the return packet
		
		Returns:
			str: sensor id string (return None if the packet type mismatches)

		"""
		
		return '-'.join( [ "%02X" % x for x in self._packetBytes[4:9] ] ) if self._cmdCode == CmdCodeEnum.GetSensorId else None

	def ExtractWavelengthInfo(self):
		"""extract wavelength info from the return packet
		
		Returns:
			WavelengthInfo: wavelength info (return None if the packet type mismatches)

		"""
		
		return WavelengthInfo(self._packetBytes) if self._cmdCode == CmdCodeEnum.GetWavelength else None

	def ExtractSpectrumInfo(self):
		"""extract spectrum info from the return packet
		
		Returns:
			SpectrumInfo: spectrum info (return None if the packet type mismatches)

		"""
		
		return SpectrumInfo(self._packetBytes) if self._cmdCode == CmdCodeEnum.GetSpectrum else None

	def ExtractXYZInfo(self):
		"""extract XYZ info from the return packet
		
		Returns:
			XYZInfo: XYZ info (return None if the packet type mismatches)

		"""
		
		return XYZInfo(self._packetBytes) if self._cmdCode == CmdCodeEnum.GetXYZ else None


class NSP32:
	"""NSP32 main class"""

	# command length table
	__CmdLen = 																			\
	[																					\
		   0,  5,  0,  0,  5,  0,  5,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x00~0x0F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x10~0x1F	\
		   0,  0,  0,  0,  5,  0, 10,  0,  5,  0, 10,  0,  5,  0,  0,  0 ,  # 0x20~0x2F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x30~0x3F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x40~0x4F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,  # 0x50~0x5F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x60~0x6F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x70~0x7F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,  # 0x80~0x8F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x90~0x9F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0xA0~0xAF	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,  # 0xB0~0xBF	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0xC0~0xCF	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,  # 0xD0~0xDF	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,  # 0xE0~0xEF	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0	# 0xF0~0xFF	\
	]

	# return packet length table
	__RetPacketLen =																	\
	[																					\
		   0,  5,  0,  0,  5,  0, 10,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x00~0x0F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x10~0x1F	\
		   0,  0,  0,  0,279,  0,  5,  0,565,  0,  5,  0, 21,  0,  0,  0 ,	# 0x20~0x2F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x30~0x3F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x40~0x4F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x50~0x5F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x60~0x6F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x70~0x7F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x80~0x8F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0x90~0x9F	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0xA0~0xAF	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0xB0~0xBF	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0xC0~0xCF	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,  # 0xD0~0xDF	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 ,	# 0xE0~0xEF	\
		   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 	# 0xF0~0xFF	\
	]

	__CmdBufSize = max(__CmdLen)			# command buffer size
	__RetBufSize = max(__RetPacketLen)		# return packet buffer size

	__WakeupPulseHoldUs		= 50			# wakeup pulse holding time = 50us
	__CmdProcessTimeMs		= 1				# time interval between "command packet transmission end" and "return packet transmission start" = 1ms (only used when data channel is SPI)
	__CmdRetryIntervalMs	= 150			# retry interval on packet error = 150ms

	__UartLowestBaudRate	= 9600			# lowest UART baud rate option = 9600 bps
	__UartTimeoutMs			= 2 * (__RetBufSize * 8 * 1000 / __UartLowestBaudRate)	# UART trnamission timeout = 941ms (double transmission time for the largest return packet with the lowest UART baud rate)

	def __init__(self, gpioPinRst, gpioPinReady, channelType, spiBus = 0, spiDevice = 0, uartPotName = '/dev/ttyS0'):
		"""__init__ method

		Args:
			gpioPinRst(int): reset pin No. (GPIO pin to reset NSP32)

			gpioPinReady(int): ready pin No. (GPIO pin to receive "ready trigger" from NSP32)

			channelType(CmdCodeEnum): data channel type (need to be one of the value: DataChannelEnum.Spi, DataChannelEnum.Uart)

			spiBus(int): SPI bus No.

			spiDevice(int): SPI device No.

			uartPortName(str): UART port name

		"""

		# RPi adaptor
		self._mcuAdaptor = _RPiAdaptor(gpioPinRst, gpioPinReady, self._OnPinReadyTriggered, channelType, spiBus, spiDevice, uartPotName)

		self._channelType = channelType					# data channel type (SPI or UART)

		self._isActive = False							# "is NSP32 in active mode" flag
		self._userCode = 0								# command user code
		self._asyncCmdCode = CmdCodeEnum.Unknown		# asynchronous command code (command waiting for async result)
		self._isPinReadyTriggered = False				# "is ready pin triggered" flag
		self._cmdBuf = bytearray(NSP32.__CmdBufSize)	# command buffer

		self._retPacketSize = 0							# return packet size
		self._retBuf = bytearray(NSP32.__RetBufSize)	# return packet buffer

		self._fwdBufWriteIdx = 0						# forward buffer write index
		self._fwdCmdLen = 0								# forward command length
		self._isFwdCmdFilled = False					# "is forward command filled" flag
		self._fwdBuf = bytearray(NSP32.__CmdBufSize)	# forward buffer

	def Init(self):
		"""initialize NSP32"""

		# initialize RPi adaptor
		self._mcuAdaptor.Init()
	
		# reset NSP32 and check functionality
		self.Wakeup()

	def IsActive(self):
		"""check if NSP32 is in active mode
		
		Returns:
			bool: True for active mode; False for standby mode

		"""

		return self._isActive

	def Wakeup(self):
		"""	wakeup/reset NSP32"""

		# continuously reset NSP32 until the functionality check passes
		while True:
			# generate a pulse signal to reset NSP32 (low active reset)
			self._mcuAdaptor.PinRstOutputLow()
			self._mcuAdaptor.DelayMicros(NSP32.__WakeupPulseHoldUs)	# hold the signal low for a period of time
		
			self._isPinReadyTriggered = False		# clear the flag, so that we can detect the "ready trigger" later on
		
			self._mcuAdaptor.PinRstHighInput()
		
			# wait until the reboot procedure is done (the "ready trigger" is fired)
			while not self._isPinReadyTriggered :
				pass
	
			# test if the SPI/UART communication is well established
			# send "HELLO" command and check the return packet
			# if the return packet is incorrect, reset again
			if self._SendCmd(CmdCodeEnum.Hello, 0, True, False, False) :
				break
	
		# record that NSP32 is active now
		self._isActive = True
	
	def Hello(self, userCode):
		"""say hello to NSP32
		
		Args:
			userCode(int): user code
	
		"""

		# if NSP32 is in standby mode, wakeup first
		if not self._isActive :
			self.Wakeup()
	
		self._SendCmd(CmdCodeEnum.Hello, userCode, False, False, True)
	
	def Standby(self, userCode):
		"""standby NSP32
		
		Args:
			userCode(int): user code
	
		"""

		# if NSP32 is already in standby mode, we just generate the return packet
		if not self._isActive :
			self._retBuf[0] = CmdCodeEnum.Prefix0
			self._retBuf[1] = CmdCodeEnum.Prefix1
			self._retBuf[2] = CmdCodeEnum.Standby
			self._retBuf[3] = userCode
			self._PlaceChecksum(self._retBuf, NSP32.__CmdLen[CmdCodeEnum.Standby] - 1)
			
			self._retPacketSize = NSP32.__RetPacketLen[CmdCodeEnum.Standby]
			return
	
		# make sure NSP32 correctly enters standy mode
		while True :
			# send command to standby NSP32
			if self._SendCmd(CmdCodeEnum.Standby, userCode, False, False, False) :
				self._isActive = False
				return
			
			# in case we don't get correct respond from NSP32, reset it and retry
			self.Wakeup()

	def GetSensorId(self, userCode):
		"""get sensor id
		
		Args:
			userCode(int): user code
	
		"""

		# if NSP32 is in standby mode, wakeup first
		if not self._isActive :
			self.Wakeup()
	
		self._SendCmd(CmdCodeEnum.GetSensorId, userCode, False, False, True)

	def GetWavelength(self, userCode):
		"""get wavelength
		
		Args:
			userCode(int): user code
	
		"""

		# if NSP32 is in standby mode, wakeup first
		if not self._isActive :
			self.Wakeup()
	
		self._SendCmd(CmdCodeEnum.GetWavelength, userCode, False, False, True)

	def AcqSpectrum(self, userCode, integrationTime, frameAvgNum, enableAE):
		"""start spectrum acquisition
		
		Args:
			userCode(int): user code

			integrationTime(int): integration time

			frameAvgNum(int): frame average num

			enableAE(bool): True to enable AE; False to disable AE

		"""

		# if NSP32 is in standby mode, wakeup first
		if not self._isActive :
			self.Wakeup()

		self._cmdBuf[4] = integrationTime & 0xFF
		self._cmdBuf[5] = integrationTime >> 8
		self._cmdBuf[6] = frameAvgNum
		self._cmdBuf[7] = 1 if enableAE else 0
		self._cmdBuf[8] = 0		# no active return
	
		self._SendCmd(CmdCodeEnum.AcqSpectrum, userCode, True, True, True)

	def AcqXYZ(self, userCode, integrationTime, frameAvgNum, enableAE):
		"""start XYZ acquisition
		
		Args:
			userCode(int): user code

			integrationTime(int): integration time

			frameAvgNum(int): frame average num

			enableAE(bool): True to enable AE; False to disable AE

		"""

		# if NSP32 is in standby mode, wakeup first
		if not self._isActive :
			self.Wakeup()

		self._cmdBuf[4] = integrationTime & 0xFF
		self._cmdBuf[5] = integrationTime >> 8
		self._cmdBuf[6] = frameAvgNum
		self._cmdBuf[7] = 1 if enableAE else 0
		self._cmdBuf[8] = 0		# no active return

		self._SendCmd(CmdCodeEnum.AcqXYZ, userCode, True, True, True)

	def _OnPinReadyTriggered(self, channel):
		"""'ready trigger' handler (call this function when master MCU receives a ready trigger on GPIO from NSP32)
		
		Args:
			channel(int): the event source channel number
		
		"""

		self._isPinReadyTriggered = True

	def UpdateStatus(self):
		"""update status (including checking async results, and processing forward commands)"""

		# check for "AcqSpectrum" async result
		# if "AcqSpectrum" is done, send a command to retrieve the data
		if self._asyncCmdCode == CmdCodeEnum.AcqSpectrum and self._isPinReadyTriggered :
			self._SendCmd(CmdCodeEnum.GetSpectrum, self._userCode, False, False, True)
	
		# check for "AcqXYZ" async result
		# if "AcqXYZ" is done, send a command to retrieve the data
		if self._asyncCmdCode == CmdCodeEnum.AcqXYZ and self._isPinReadyTriggered :
			self._SendCmd(CmdCodeEnum.GetXYZ, self._userCode, False, False, True)
		
		# start processing forward commands
		if not self._isFwdCmdFilled :
			return
		
		# if a forward command is filled, copy the command bytes to command buffer
		self._cmdBuf[0 : self._fwdCmdLen] = self._fwdBuf[0 : self._fwdCmdLen]
		self._isFwdCmdFilled = False	# clear the flag, so that new incoming bytes could be accepted
		
		cmdCode = self._cmdBuf[2]		# extract command function code
		userCode = self._cmdBuf[3]		# extract command user code
		
		# process the command based on its function code
		if cmdCode == CmdCodeEnum.Hello:			# hello
				self.Hello(userCode)
		elif cmdCode == CmdCodeEnum.Standby:		# standby
				self.Standby(userCode)
		elif cmdCode == CmdCodeEnum.GetSensorId:	# get sensor id
				self.GetSensorId(userCode)
		elif cmdCode == CmdCodeEnum.GetWavelength:	# get wavelength
				self.GetWavelength(userCode)
		elif cmdCode == CmdCodeEnum.AcqSpectrum:	# spectrum acquisition
				self.AcqSpectrum(userCode, struct.unpack('<H', self._cmdBuf[4:6]), self._cmdBuf[6], self._cmdBuf[7] != 0)
		elif cmdCode == CmdCodeEnum.AcqXYZ:			# XYZ acquisition
				self.AcqXYZ(userCode, struct.unpack('<H', self._cmdBuf[4:6]), self._cmdBuf[6], self._cmdBuf[7] != 0)

	def FwdCmdByte(self, fwd):
		"""forward a command byte to NSP32 (call this function when master MCU receives a command byte sent from PC/App) (only used when master MCU acts as a forwarder)
		
		Args:
			fwd(int): single byte to forward
	
		"""

		# if a command is filled but not yet being processed, reject new incoming bytes
		if self._isFwdCmdFilled :
			return
		
		# store incoming bytes to the forward buffer
		# align command prefix code to the beginning of the buffer
		if ((self._fwdBufWriteIdx == 0 and fwd == CmdCodeEnum.Prefix0) or self._fwdBufWriteIdx > 0) and self._fwdBufWriteIdx < NSP32.__CmdBufSize :
			self._fwdBuf[self._fwdBufWriteIdx] = fwd
			self._fwdBufWriteIdx += 1
		
		if self._fwdBufWriteIdx > 1 and self._fwdBuf[1] != CmdCodeEnum.Prefix1 :
			# if the command prefix code mismatches, clear the buffer
			self._fwdBufWriteIdx = 0
		elif self._fwdBufWriteIdx > 2 :
			# determine the command length based on command function code
			self._fwdCmdLen = NSP32.__CmdLen[self._fwdBuf[2]]

			if self._fwdCmdLen <= 0 :
				# unrecognized command, clear the buffer
				self._fwdBufWriteIdx = 0
			elif self._fwdBufWriteIdx >= self._fwdCmdLen :
				# if num of bytes in the buffer reaches command length, a full command is filled
				self._fwdBufWriteIdx = 0    # reset the buffer write index
	
				# if checksum is valid, accept it, otherwise discard it
				if self._IsChecksumValid(self._fwdBuf, self._fwdCmdLen) :
					self._isFwdCmdFilled = True		# set the "forward command filled" flag

	def _SendCmd(self, cmdCode, userCode, keepSilent, waitReadyTrigger, errorRetry):
		"""send command to NSP32
		
		Args:
			cmdLen(int): command length (including the checksum)

			retLen(int): expected return packet length (including the checksum)

			cmdCode(CmdCodeEnum): command function code

			userCode(int): command user code

			keepSilent(bool): True to hide the return packet from end users; False to forward the return packet to end users

			waitReadyTrigger(bool): True for async commands (commands that take longer time to execute); False for sync commands (commands that return packets immediately)

			errorRetry(bool): True to retry on return packet error; False to ignore the error

		Returns:
			bool: True for return packet correctly received; False for packet error

		"""

		cmdLen = NSP32.__CmdLen[cmdCode]				# command length
		retLen = NSP32.__RetPacketLen[cmdCode]			# expected return packet length
		
		self._cmdBuf[0] = CmdCodeEnum.Prefix0
		self._cmdBuf[1] = CmdCodeEnum.Prefix1
		self._cmdBuf[2] = cmdCode
		self._cmdBuf[3] = userCode
		self._PlaceChecksum(self._cmdBuf, cmdLen - 1)	# add checksum
	
		self._retPacketSize = 0
		self._asyncCmdCode = cmdCode if waitReadyTrigger else CmdCodeEnum.Unknown
		self._userCode = userCode
		self._isPinReadyTriggered = False

		while True :
			isTimeout = False
			
			if self._channelType == DataChannelEnum.Spi :
				self._mcuAdaptor.SpiSend(list(self._cmdBuf[0 : cmdLen]))		# send the command to NSP32 (through SPI)
				self._mcuAdaptor.DelayMillis(NSP32.__CmdProcessTimeMs)			# wait for a short processing time
				self._retBuf[0 : retLen] = self._mcuAdaptor.SpiReceive(retLen)	# get the return packet					
			elif self._channelType == DataChannelEnum.Uart :
				# clear UART TX buffer (by reading out all remaining bytes in the buffer)
				while self._mcuAdaptor.UartBytesAvailable() :
					self._mcuAdaptor.UartReadByte()
				
				self._mcuAdaptor.UartSend(list(self._cmdBuf[0 : cmdLen]))		# send the command to NSP32 (through UART)
				self._mcuAdaptor.StartMillis()									# start to count milliseconds (for timeout detection)
				
				# read expected length of bytes (return packet) from UART
				writeIdx = 0
				
				while writeIdx < retLen :
					# if we can't receive the expected length of bytes within a period of time, timeout occurs
					if self._mcuAdaptor.GetMillisPassed() > NSP32.__UartTimeoutMs :
						isTimeout = True
						break

					# read bytes from UART
					while self._mcuAdaptor.UartBytesAvailable() and writeIdx < retLen :
						self._retBuf[writeIdx] = self._mcuAdaptor.UartReadByte()
						writeIdx += 1
	
			if not isTimeout :
				# check if the return packet is valid		
				if self._retBuf[0] == CmdCodeEnum.Prefix0 and self._retBuf[1] == CmdCodeEnum.Prefix1 and	\
								self._retBuf[2] == cmdCode and self._retBuf[3] == userCode and				\
								self._IsChecksumValid(self._retBuf, retLen) :
					# if keep silent, hide the return packet from end users
					# if not keep silent, let end users know the return packet is available
					self._retPacketSize = 0 if keepSilent else retLen

					return True
			
			# deal with the packet error situation
			if errorRetry :
				# if packet error, get ready to retry
				self._mcuAdaptor.DelayMillis(NSP32.__CmdRetryIntervalMs)	# delay a short interval before retry
			else :
				# ignore the packet error and return directly
				return False

	def _PlaceChecksum(self, buf, len):
		"""calculate checksum and append it to the end of the buffer (use "modular sum" method)
		
		Args:
			buf(bytearray): buffer

			len(int): data length (excluding the checksum)

		"""

		# sum all bytes
		s = sum(buf[0 : len])
		
		# take two's complement, and append the checksum to the end
		buf[len] = ((~s) + 1) & 0xFF

	def _IsChecksumValid(self, buf, len):
		"""check if the checksum is valid (use "modular sum" method)
		
		Args:
			buf(bytearray): buffer

			len(int): data length (including the checksum)
			
		Returns:
			bool: True for valid; False for invalid

		"""

		# sum all bytes (including the checksum byte)
		# if the summation equals 0, the checksum is valid
		return (sum(buf[0 : len]) & 0xFF) == 0

	def ClearReturnPacket(self):
		"""clear return package"""

		self._retPacketSize = 0

	def GetReturnPacketSize(self):
		"""get the return packet size
		
		Returns:
			int: return packet size (return 0 if the return packet is not yet available or is cleared)
	
		"""

		return self._retPacketSize
	
	def GetReturnPacket(self):
		"""get the return packet
		
		Returns:
			ReturnPacket: return packet (return None if the return packet is not yet available or is cleared)

		"""

		return None if self._retPacketSize <= 0 else ReturnPacket(self._retBuf[2], self._retBuf[3], True, self._retBuf[0 : self._retPacketSize])


class _RPiAdaptor:
	"""RPi adaptor for NSP32 class"""

	def __init__(self, gpioPinRst, gpioPinReady, readyTriggeredDelegate, channelType, spiBus, spiDevice, uartPotName):
		"""__init__ method

		Args:
			gpioPinRst(int): reset pin No. (GPIO pin to reset NSP32)

			gpioPinReady(int): ready pin No. (GPIO pin to receive "ready trigger" from NSP32)

			readyTriggeredDelegate(function): "ready trigger" handler function

			channelType(CmdCodeEnum): data channel type (need to be one of the value: DataChannelEnum.Spi, DataChannelEnum.Uart)

			spiBus(int): SPI bus No.

			spiDevice(int): SPI device No.

			uartPortName(str): UART port name
			
		"""

		self._gpioPinRst = gpioPinRst
		self._gpioPinReady = gpioPinReady
		self._onPinReadyTriggeredDelegate = readyTriggeredDelegate
		
		self._channelType = channelType
		self._spiBus = spiBus
		self._spiDevice = spiDevice
		self._uartPortName = uartPotName
		self._uartBaudRate = 115200		# set UART baud rate = 115200bps

		self._spiControl = None			# SPI controller
		self._serialControl = None		# UART controller

		self._startMillis = 0
	
	def __del__(self):
		"""__del__ method"""

		# GPIO cleanup
		GPIO.cleanup()

		# close SPI
		if (self._spiControl is not None) and self._spiControl.isOpen() :
			self._spiControl.close()

		# close UART
		if (self._serialControl is not None) and self._serialControl.isOpen() :
			self._serialControl.close()

	def Init(self):
		"""initialize adaptor"""

		# setup reset pin, ready pin, and the "ready trigger" event handler
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self._gpioPinRst, GPIO.IN)
		GPIO.setup(self._gpioPinReady, GPIO.IN)
		GPIO.add_event_detect(self._gpioPinReady, GPIO.FALLING, self._onPinReadyTriggeredDelegate)

		# open SPI or UART
		if self._channelType == DataChannelEnum.Spi :
			self._spiControl = spidev.SpiDev()
			self._spiControl.open(self._spiBus, self._spiDevice)
			self._spiControl.max_speed_hz = 4000000		# set SPI max. baud rate = 4Mbits/s
		elif self._channelType == DataChannelEnum.Uart :
			self._serialControl = serial.Serial(self._uartPortName, self._uartBaudRate)
	
	def DelayMicros(self, us):
		"""delay microseconds

		Args:
			us(int): microseconds

		"""

		time.sleep(us * 0.000001)

	def DelayMillis(self, ms):
		"""delay milliseconds

		Args:
			ms(int): milliseconds

		"""

		time.sleep(ms * 0.001)
	
	def PinRstOutputLow(self):
		"""set the reset pin (to reset NSP32) to output mode and set 'low'"""

		GPIO.setup(self._gpioPinRst, GPIO.OUT)
		GPIO.output(self._gpioPinRst, GPIO.LOW)
	
	def PinRstHighInput(self):
		"""set the reset pin (to reset NSP32) 'high' and set it to input mode"""

		GPIO.output(self._gpioPinRst, GPIO.HIGH)
		GPIO.setup(self._gpioPinRst, GPIO.IN)
	
	def SpiSend(self, buf):
		"""send through SPI (only used when data channel is SPI)

		Args:
			buf(list): buffer to send

		"""

		self._spiControl.xfer(buf, 2000000)	# set SPI baud rate = 2Mbits/s
	
	def SpiReceive(self, len):
		"""receive from SPI (only used when data channel is SPI)

		Args:
			len(int): data length

		Returns:
			list: bytes received

		"""

		return self._spiControl.readbytes(len)
	
	def StartMillis(self):
		"""start to count milliseconds (only used when data channel is UART)"""

		self._startMillis = time.time() * 1000
	
	def GetMillisPassed(self):
		"""get milliseconds passed since last call to StartMillis() (only used when data channel is UART)

		 Returns:
			 float: milliseconds passed

		"""

		return time.time() * 1000 - self._startMillis
	
	def UartBytesAvailable(self):
		"""see if any bytes available for reading from UART (only used when data channel is UART)

		Returns:
			bool: True for bytes available; False for none

		"""

		return self._serialControl.in_waiting > 0
	
	def UartReadByte(self):
		"""read a single byte from UART (only used when data channel is UART)

		Returns:
			int: single byte reading from UART

		"""

		return self._serialControl.read()[0]
	
	def UartSend(self, buf):
		"""send through UART (only used when data channel is UART)

		Args:
			buf(list): buffer to send

			len(int): data length

		"""

		self._serialControl.write(buf)
