# Sentinel: In Field Camera System
## Introduction
This repository contains the relevant code for the Jetson Nano based camera system.
This document describes how to connect and set up all of the hardware added to the system and all code required to 
train object detection models for the current iteration of the system as of June 2022.

## Hardware
### Required Components
- Windows Laptop
- Jetson Nano Developers Kit 4GB
- 10W Barrel Plug Power Source
- Micro-USB to USB-A cable (optional)
- Ethernet cable or wifi adapter
- 128GB micro-SD card (Could be 64GB)
- Raspberry Pi Camera V2
- PimoRoni Pan-Tilt Mount
- NanoLambda NSP32
- USB Mouse and Keyboard (Just for Setup)
- HDMI Monitor (Just for Setup)

### Jetson Nano Initial Setup
First, the micro-SD card will need to be properly formatted so that your computer computer can store data onto it.
This should be the defualt format suggested by Windows. "SD Card Formatter" was used with the quick format option.
After the SD card is properly formatted download the disk image for Jetpack 4.3 from https://developer.nvidia.com/jetpack-43-archive
Then use BalenaEtcher (https://www.balena.io/etcher/) to flash the disk image to the SD card. 

After the OS has been installed connect the mouse, keyboard, and monitor to the Jetson Nano before powering on the board. The system
will then guide you through the basic setup. It is recommended to either connect and setup a usb wifi adapter for the Nano or plug the 
board directly into your wifi router using an ethernet cable. If using a wifi adapter ensure that it is compatibel with the Nano and there
are not known bugs associated with its use alongside the Nano. There are several adapters that are known to consistently drop connnection when
used with certain Jetpack version. After conmpleting the set up prompts open a terminal. Use the command "ifconfig"
to see what the Nano's IP address is on the network and make a note of it.
 
Next, unplug the mouse, keyboard, and monitor from the Nano. Plug the Nano back in. Now on the laptop download Xming (https://sourceforge.net/projects/xming/) 
and install using the .exe file. Set the location to 0.0 when prompted. The tutorial used can be found: https://bhs-av.github.io/devlog/2019-11-11-x11-forwarding/.
Open a Putty terminal on your laptop (Download: https://www.putty.org/). Enter the IP address you wrote down before and then enable X11 forwarding by going to
SSH>>X11 and then check the "Enable X11 Forwarding" and MIT-Magic-Cookie-1. Enter the X-display location of the Xming server (127.0.0.1:0.0). 
If an error occurs you may need to adjust the display location address. From the putty terminal you should now be able to log into the Jetson Nano either over
wifi or by using a micro-USB to USB-A cable. From this point on this document assumes you are communicating with the Nano through SSH. Note that the Nano will need
internet access in order to install python libraries to complete the software setup.

The final step for initial setup is to configure the 40-pin extension of the Jetson Nano to provide UART and PWM access. To configure the pin functions run:
'''

sudo python \opt\nvidia\jetson-io.py

'''

Then choose "Configure 40-pin expansion header" and make sure pwm0, pwm2, and uartb are all selected. Then exit and save the changes. The system will then need to reboot 
for the changes to take effect
'''

sudo reboot

'''

### Connecting Peripherals
- The camera should be connected directly to one of the MIPI CSI camera ports using its ribbon cable
- The NSP32 should be connected to Pin8 (TXD) and Pin10 (RXD) for control through UART
- Each servo motor on the mount needs to be connected to a ground and 5V pin and then the top motor should be connected to Pin33 and the bottom motor to Pin32


## Setting Up Jetson Nano Python Environment



## Tensorflow Object Detection API


### Jetson Nano

### Training Computer
This Project used an intel Xeon CPU and P2000 GPU for model training. HiPerGator could also be used, but setting up the object detection API was not straightforward so the current
model was trained locally. The model training folder in this repository is already structured and ready for model training. It is recommended that Tensorflow 1.15 is used. If you 
are using a newer version of Tensorflow (TF 2.x) you will need to download the newer version of the API here:https://github.com/tensorflow/models/tree/master/research/object_detection
If you are configuring the API from scratch it is recommended you follow this tutorial: https://tensorflow-object-detection-api-tutorial.readthedocs.io/en/tensorflow-1.14/install.html#general-remarks
One note regarding the pycocotools package, if you are using anaconda as your package manager the command:
'''

conda install pycocotools-windows (also try pip if you have trouble)

'''
should get around the compilation errors other techniques run into. You will still need to have VS build tools 2015 installed on your machine
If you are using the Model_Training directory provided you will still need to install tensorflow-gpu 1.15 and get CUDA installed on your machine in order to use GPU or just install tensorflow 1.15
to only use the CPU. However, model training will not be practical without using a GPU. CUDA documentation can be found:
'''

https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/index.html

'''
Once Tensorflow has been successfully installed to use the API you will need to download the newest release of protocol buffers from https://github.com/protocolbuffers/protobuf/releases. Then extract
the zip file to C:\Program Files\Google Protobuf. Add the path to the protobuf directory to your Path environment variable. Instructions for how to do this can be found here: https://www.computerhope.com/issues/ch000549.htm#windows10.
