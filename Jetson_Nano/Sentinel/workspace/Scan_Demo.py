# Author: Robert Pritchard
# Date Updated: 3/31/22
# This script is a demo that will scan the room for objects of interests
# and save their locations along with store images and spectrums for each.
# The scan can be started from the command line and the user will be notified
# when a scan starts and ends through the terminal as well.
from fileinput import hook_encoded
from datetime import datetime
import os
import PanTilt
import argparse
import cv2
import Jetson.GPIO as GPIO
import tensorflow as tf
from NanoLambdaNSP32 import *
from csv import writer
from csv import reader
import object_detection
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import time

#--- Constants ---#
SCAN_PER = 0

SCAN_MODE = 0 # 0 is manual 1 is auto
SAVE_DIR = os.getcwd()+"/"+datetime.now().strftime("%d-%m-%Y_%H-%M") # default to the cwd
V_START = 0
V_END = 1
H_START = 0
H_END = 1
# MODEL_PATH = 'Models/haarcascade_frontalface_default.xml'
NEXT_ID = 0

def gstreamer_pipeline(
    capture_width =1200,
    capture_height=1200,
    display_width=300,
    display_height=300,
    framerate=21,
    flip_method=0,
):
    return(
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

class detection:
    def __init__(self,id,x,y):
        self.id = id
        self.x = x
        self.y = y
        # when a model with multiple classes is used
        # self.label = label
    def show_image(self):
        # load in image
        plt.figure()
        plt.imshow(mpimg.imread(SAVE_DIR+'/'+str(self.id)+'.jpg'))
        plt.show()

    def show_spectrum(self):
        with open(SAVE_DIR+'/'+str(self.id)+".csv") as f:
            reader_obj = reader(f)
            rows = [row for row in reader_obj]
            global wavelength_info
            plt.figure()
            plt.plot(wavelength_info.Wavelength,rows[-1])
            plt.show()

    
def Cam_init():
    global cap
    cap = cv2.VideoCapture(gstreamer_pipeline(),cv2.CAP_GSTREAMER)
    return cap


def Handle_Args(args):
    if args.save_directory:
        global SAVE_DIR
        SAVE_DIR = args.save_directory + "/" + datetime.now().strftime("%d-%m-%Y_%H-%M")
    if args.scan_period:
        global SCAN_PER
        global SCAN_MODE
        SCAN_MODE = 1
        SCAN_PER = args.scan_period
    if args.vertical_start:
        global V_START
        V_START = args.vertical_start
    if args.vertical_end:
        global V_END 
        V_END = args.vertical_end
    if args.horizontal_start:
        global H_START 
        H_START = args.horizontal_start
        print(H_START)
    if args.horizontal_end:
        global H_END 
        H_END = args.horizontal_end
    if args.model:
        global MODEL_PATH 
        MODEL_PATH = args.horizontal_model

def END():
    global cap
    # perform whatever clean up is necessary
    cap.release()
    cv2.destroyAllWindows()

def Check4Object():
    global cap
    global nsp32
    if not(cap.isOpened()):
        print('Camera stream is not Open!')
        return
    centered_obj = (0,0)
    count = 0
    for i in range(5): # checks the image 5 times to reduce false postives
        ret,frame_orig = cap.read()
        # frame = cv2.resize(frame,None, fx=0.5,fy=0.5, interpolation=cv2.INTER_AREA)
        frame = cv2.resize(frame_orig,(300,300), interpolation=cv2.INTER_AREA)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_expanded = np.expand_dims(frame_rgb,axis=0)
        global detection_scores 
        global detection_boxes
        global detection_classes
        global num_detections
        global image_tensor
        (boxes, scores, classes, num) = model.run(
         [detection_boxes, detection_scores, detection_classes, num_detections],
         feed_dict={image_tensor: frame_expanded})
        # gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        # objects = model.detectMultiScale(gray,1.1,4)

        for(x,y,w,h) in boxes[np.where(scores>0.8)]:
            # draw rectangles
            # cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
            # check if the object in centered enough
            obj_x = x+ 0.5*w
            obj_y = y+0.5*h
            if obj_x < (frame.shape[1]/2+30) and obj_x > (frame.shape[1]/2-30) :
                if obj_y < (frame.shape[0]/2+30) and obj_y > (frame.shape[0]/2-30) :
                    # Object is Centered
                    if centered_obj == (0,0):
                        centered_obj = (x,y)
                        count += 1
                    elif x>centered_obj[0]-10 and x<centered_obj[0]+10:
                        if y>centered_obj[1]-10 and y<centered_obj[1]+10:
                            count += 1
    if count >= 3:
        # take picture and save
        global NEXT_ID
        # in the future I will add the label the detected object was given to this string as well
        image_name = SAVE_DIR+'/'+str(NEXT_ID)+".jpg"
        cv2.imwrite(image_name,frame_orig)
        print('Image Saved!: ',image_name)
        # read in spectroscopy data
        nsp32.AcqSpectrum(0,int(32),3,0)

        #wait for acquisition
        while nsp32.GetReturnPacketSize() <= 0:
            nsp32.UpdateStatus()
        
        spectrum_info = nsp32.GetReturnPacket().ExtractSpectrumInfo()
        global mount
        # write spectrum data into csv files
        with open(SAVE_DIR+'/'+str(NEXT_ID)+".csv",'a',newline='') as f_object:
            writer_obj = writer(f_object)
            writer_obj.writerow([mount.horz_pos,mount.vert_pos])
            writer_obj.writerow(spectrum_info.Spectrum)
            f_object.close()
        object_list.append(detection(NEXT_ID,mount.horz_pos,mount.vert_pos))
        NEXT_ID += 1
    return frame,boxes,scores,classes,num

def draw_boxes(frame,objects):
    for (x,y,w,h) in objects:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
    return frame

def Scan(vStart = 0, hStart = 0, vEnd = 1, hEnd = 1):
    start_time = time.time()
    cv2.namedWindow('Scan_Window', cv2.WINDOW_AUTOSIZE)
    mount.MOVE2D(vStart,hStart)
    go = 1
    num_v = 1
    while go == 1:
        #check view
        frame,boxes,scores,classes,num = Check4Object()
        # annotated_frame = draw_boxes(frame,objects)
        global category_index
        vis_util.visualize_boxes_and_labels_on_image_array(
        frame,
        np.squeeze(boxes),
        np.squeeze(classes).astype(np.int32),
        np.squeeze(scores),
        category_index,
        use_normalized_coordinates=True,
        line_thickness=8,
        min_score_thresh=0.85)
        cv2.imshow("Scan_Window", frame)
        keyCode = cv2.waitKey(5) &  0xFFF
        if keyCode == 27:
            break
        #display to viewer
        #progress
        go = mount.V_STEP(num_v,lower_bound=vStart,upper_bound=vEnd)
        time.sleep(0.2)
        if go == 0:
            go = mount.H_STEP(3,lower_bound=hStart,upper_bound=hEnd)
            num_v = -num_v
    mount.MOVE2D(0.5,0.5)
    end_time = time.time()
    print(end_time-start_time)
# def load_from_save(dir_name):


def Console_Loop():
    # loop for asking the user when to begin a scan
    first_scan = True
    while True:
        if first_scan:
            usr_in = input("Press Enter to begin a scan of the surroundings or 'exit' to end or load: ")
            if(len(usr_in) > 0):
                if usr_in == 'exit':
                    return
                # elif usr_in == 'load':
                #     dir_name = input('What directory should be used to load? ')
                #     load_from_save(dir_name)
                else:
                    print('Command not recognized')
                    break
            else:
                Scan(V_START,H_START,V_END,H_END)
            first_scan = False
        else:
            usr_in = input("Press Enter to begin a scan of the surroundings or type 'exit', 'show_spectrum', or 'show_image': ")
            if(len(usr_in) > 0):
                if usr_in == 'exit':
                    return
                elif usr_in == 'show_spectrum':
                    if(len(object_list)==0):
                        print('No detections to show!')
                        break
                    print(range(len(object_list)))
                    number = input("What ID would you like to plot? ")
                    object_list[int(number)].show_spectrum()
                elif usr_in == 'show_image':
                    if(len(object_list)==0):
                        print('No detections to show!')
                        break
                    print(range(len(object_list)))
                    number = input("What ID would you like to show? ")
                    object_list[int(number)].show_image()
                else:
                    print('Command not recognized')
                    break
            else:
                Scan(V_START,H_START,V_END,H_END)
    
def nsp32_init():
    global nsp32
    nsp32.Init()
    nsp32.GetSensorId(0)
    id = nsp32.GetReturnPacket().ExtractSensorIdStr()

    #get wavelength
    nsp32.GetWavelength(0)
    wavelength = nsp32.GetReturnPacket().ExtractWavelengthInfo()
    return id, wavelength

def main():

    global next_ID
    next_ID = 0
    # initialize the camera
    Cam_init()
    # initialize Pan-Tilt mount
    global mount
    mount = PanTilt.PT_Mount()
    # initialize spectrometer
    PinRst = 13 # pin Reset (the number is based on GPIO.BOARD)
    PinReady = 15 # pin Ready (the number is based on GPIO.BOARD)
	#self._nsp32 = NSP32(PinRst, PinReady, DataChannelEnum.Spi, spiBus = 0, spiDevice = 0)		# use SPI channel
    global nsp32
    nsp32 = NSP32(PinRst, PinReady, DataChannelEnum.Uart, uartPotName = '/dev/ttyTHS1')	# use UART channel
    global wavelength_info
    id, wavelength_info = nsp32_init()
    global object_list
    object_list = []
    os.mkdir(SAVE_DIR)

    with open(SAVE_DIR+'/wavelengths.csv','a+',newline='') as f_object:
        writer_obj = writer(f_object)
        writer_obj.writerow(wavelength_info.Wavelength)
        f_object.close()

    global model
    # model = cv2.CascadeClassifier(MODEL_PATH)
    LABEL_FILENAME = 'annotations/labelmap.pbtxt'

    MODEL_FILENAME = 'Models/ssd_mobilenet_v2_graph/frozen_inference_graph.pb'
    
    NUM_CLASSES= 4 # WHITE, YELLOW, BUD, POD
    cv2.CAP_PROP_FRAME_WIDTH

    label_map = label_map_util.load_labelmap(LABEL_FILENAME)
    categories = label_map_util.convert_label_map_to_categories(label_map,max_num_classes=NUM_CLASSES,use_display_name = True)
    global category_index
    category_index = label_map_util.create_category_index(categories)

    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True


    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(MODEL_FILENAME,'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')
        
        model = tf.Session(graph=detection_graph, config=config)

    # Input tensor is the image
    global image_tensor
    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

    # Output tensors are the detection boxes, scores, and classes
    # Each box represents a part of the image where a particular object was detected
    global detection_boxes
    detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

    # Each score represents level of confidence for each of the objects.
    # The score is shown on the result image, together with the class label.
    global detection_scores
    detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
    global detection_classes
    detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')

    # Number of objects detected
    global num_detections
    num_detections = detection_graph.get_tensor_by_name('num_detections:0')
    
    Console_Loop()
    #if SCAN_MODE == 0:
     #   Console_Loop()
    #else:
     #   Auto_Scan()
    # pass in the camera entity so that it can be properly closed 
    END(cap)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument('-sd','--save_directory', type = str, help = 'path to save images to')
    ap.add_argument('-sp','--scan_period', type = int, help='Number of minutes between scans')
    ap.add_argument('-vs', '--vertical_start', type=float, help = 'vertical start position for scans')
    ap.add_argument('-hs', '--horizontal_start', type=float, help = 'horizontal start position for scans')
    ap.add_argument('-ve','--vertical_end',type=float, help = 'vertical end position for scans')
    ap.add_argument('-he', '--horizontal_end', type=float, help='Horizontal end position for scan')
    ap.add_argument('-md', '--model', type = str, help = 'path to object detection model')

    # ... add more as needed
    ap.add_argument('arg', nargs='*')

    args = ap.parse_args()
    Handle_Args(args)
    main()