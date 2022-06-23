# Sentinel: In Field Camera System
## Introduction
This repository contains the relevant code for the Jetson Nano based camera system.
This document describes how to connect and set up all of the hardware added to the system and all code required to 
train object detection models for the current iteration of the system as of June 2022.

If you run into any issues with the code provided or setting up a new Sentinel system please feel free to reach out to me at
rpritchard@ufl.edu for help.

Current Sentinel Login:
username: robert
password: sentinel

to activate virtual environment use: /home/robert/Sentinel/workspace
$ workon TF1
- The main code folder is located in /home/robert/Sentinel/workspace
- Scan_Demo.py is the most complicated program as of now and scans the surroundings while storing data about detected objects
- Model_Test_Image.py is to test the inference time of a model
- Facial_Tracking.py uses a lightweight facial detection model to move to the camera to track faces as they move
- Beginner.py is the most basic test script for the NSP32
- SpectrumMeter.py is a GUI example for the NSP32
- PanTilt.py is the library for controlling the mount
- NanoLambdaNSP32.py is the library for communicating with the NSP32

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
```
$ sudo python \opt\nvidia\jetson-io.py
```

Then choose "Configure 40-pin expansion header" and make sure pwm0, pwm2, and uartb are all selected. Then exit and save the changes. The system will then need to reboot 
for the changes to take effect
```
$ sudo reboot
```

### Connecting Peripherals
- The camera should be connected directly to one of the MIPI CSI camera ports using its ribbon cable
- The NSP32 should be connected to Pin8 (TXD) and Pin10 (RXD) for control through UART
- Each servo motor on the mount needs to be connected to a ground and 5V pin and then the top motor should be connected to Pin33 and the bottom motor to Pin32


## Setting Up Jetson Nano Python Environment
First install pip using
```
$ wget https://bootstrap.pypa.io/get-pip.py
$ sudo python3 get-pip.py
$ rm get-pip.py
```
Then install virtualenv and virtualenvwrapper
```
$ sudo pip install virtualenv virtualenvwrapper
````

After installation you will need to add the following lines to the bottom of the .bashrc file
```
# virtualenv and virtualenvwrapper
export WORKON_HOME=$HOME/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh
```
to do so you can use the nano editor
```
$ pip install nano
$ nano ~/.bashrc
```
and then edit the file and make sure to save when exiting then run
```
$ source ~./bashrc 
```
so the changes take effect.

Jetpack 4.3 comes with OpenCV and CUDA already installed and configured on the Nano. To install Tensorflow-gpu for python 3.6 on Jetpack 4.3 use the following commands
```
$ sudo apt-get install libhdf5-serial-dev hdf5-tools libhdf5-dev zlib1g-dev zip libjpeg8-dev
$ sudo apt-get install python3-pip
$ sudo pip3 install -U pip
$ sudo pip3 install -U numpy grpcio absl-py py-cpuinfo psutil portpicker six mock requests gast h5py astor termcolor protobuf keras-applications keras-preprocessing wrapt google-pasta
$ sudo pip3 install --pre --extra-index-url https://developer.download.nvidia.com/compute/redist/jp/v43 tensorflow==1.15.2+nv20.3
```

## Tensorflow Object Detection API


### Jetson Nano

After TensorFlow has been installed on the system copy the Sentinel folder into your user's home directory on the Nano (eg. /home/robert) and extract the protoc .zip file into a /home/usr/Protobuf
then navigate to /home/usr/Sentinel/models/research and run:
```
$ protoc object_detection/protos/*.proto --python_out=.
```
you may need to install protoc first using
```
$ sudo apt-get install libprotobuf-dev protobuf-compiler
```
Then run
```
$ pip install .
```
to complete the API installation. Then all of the code should be able to run without error.

### Training Computer

This Project used an intel Xeon CPU and P2000 GPU for model training. HiPerGator could also be used, but setting up the object detection API was not straightforward so the current
model was trained locally. The two main packages that were used were TensorFlow-gpu 1.15 and OpenCV. The model training folder in this repository is already structured and ready for model training. It is recommended that Tensorflow 1.15 is used. If you 
are using a newer version of Tensorflow (TF 2.x) you will need to download the newer version of the API here:https://github.com/tensorflow/models/tree/master/research/object_detection
If you are configuring the API from scratch it is recommended you follow this tutorial: https://tensorflow-object-detection-api-tutorial.readthedocs.io/en/tensorflow-1.14/install.html#general-remarks
It is also recommended that the training be performed in a conda virtual environment. You can create one using
```
$ conda create --name myenv
```
where myenv is the name of the new environment. To activate and deactivate environments simply use 
```
$ conda activate myenv  or   conda deactivate myenv
```
If you are using the Model_Training directory provided you will still need to install tensorflow-gpu 1.15 and get CUDA installed on your machine in order to use GPU or just install tensorflow 1.15
to only use the CPU. However, model training will not be practical without using a GPU. CUDA documentation can be found:

https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/index.html

Once Tensorflow and OpenCV have been successfully installed to use the API you will need to download the newest release of protocol buffers from https://github.com/protocolbuffers/protobuf/releases. Then extract
the zip file to C:\Program Files\Google Protobuf. Add the path to the protobuf directory to your Path environment variable. Instructions for how to do this can be found here: https://www.computerhope.com/issues/ch000549.htm#windows10.
Once the PATH is updated navigate to Model_Training/Tensorflow/models/research and run
```
$ protoc object_detection/protos/*.proto --python_out=.
```
Then form within this same folder run
```
$ pip install .
```
and the base API shoud be all set to go. The last step is to add pycocotools which are used in various scripts within the API. This should be as simple as running the following command if you are using anconda package manager
```
$ conda install pycocotools-windows (also try pip if you have trouble)
```
you will need to have microsoft VS build tools 2015 installed on your machine. Once this installation is complete your system should be ready to begin training models. Please refer to https://tensorflow-object-detection-api-tutorial.readthedocs.io/en/latest/training.html
for help training new models. The Tensorflow Directory is structured to match this tutorial. 

The model zoo for tensorflow 1 can be found at https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/tf1_detection_zoo.md however so far only the ssd_mobilenet_v2 has been successfully run on the Nano and all the data
needed to train new models with this architecture is included in the Model_Training directory.

