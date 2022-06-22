# Sentinel: In Field Camera System
## Introduction
This repository contains the relevant code for the Jetson Nano based camera system.
This document describes how to connect and set up all of the hardware added to the system and all code required to 
train object detection models for the current iteration of the system as of June 2022.

## Hardware
# Required Components
- Windows Laptop
- Jetson Nano Developers Kit 4GB
- 10W Barrel Plug Power Source
- Micro-USB to USB-A cable (optional)
- 128GB micro-SD card (Could be 64GB)
- Raspberry Pi Camera V2
- PimoRoni Pan-Tilt Mount
- NanoLambda NSP32
- USB Mouse and Keyboard (Just for Setup)
- HDMI Monitor (Just for Setup)

## Jetson Nano Initial Setup
First, the micro-SD card will need to be properly formatted so that your computer computer can store data onto it.
This should be the defualt format suggested by Windows. "SD Card Formatter" was used with the quick format option.
After the SD card is properly formatted download the disk image for Jetpack 4.3 from https://developer.nvidia.com/jetpack-43-archive

