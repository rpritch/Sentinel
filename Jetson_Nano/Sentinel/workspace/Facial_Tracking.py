import cv2
import Jetson.GPIO as GPIO
import time
#********************************************************************
#----------------------------Constants-------------------------------
#********************************************************************
PWM_MAX = 10
PWM_MIN = 5
DC_STEP = 0.025
#********************************************************************
#----------------------------Functions-------------------------------
#********************************************************************
def gstreamer_pipeline(
    capture_width = 3280,
    capture_height=2464,
    display_width=820,
    display_height=616,
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

#********************************************************************
#----------------------------Main------------------------------------
#********************************************************************
# initialize PWM and mount to the middle
GPIO.setmode(GPIO.BOARD)

GPIO.setup(33, GPIO.OUT)
GPIO.setup(32, GPIO.OUT)

pwm_vert = GPIO.PWM(33, 50)
pwm_horz = GPIO.PWM(32, 50)

vert_dc = 7.5
horz_dc = 7.5
pwm_vert.start(vert_dc)
pwm_horz.start(horz_dc)

# initialize camera stream
cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)

# initialize facial recognition
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# implement tracking
cv2.namedWindow("Face Detect", cv2.WINDOW_AUTOSIZE)
while cap.isOpened():
    ret,frame = cap.read()
    frame = cv2.resize(frame,None, fx=0.5,fy=0.5, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray,1.1,4)
    for (x,y,w,h) in faces:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
    if faces.__len__() > 0:
        if faces.__len__() > 1:
            face1 = faces[0]
            face2 = faces[1]
            if face1[0] > face2[0]:
                print('first face x is bigger')
            else:
                print('second face x is bigger')
            if face1[1] > face2[1]:
                print('first face y is bigger')
            else:
                print('second face y is bigger')
        # check if the first face is in the center
        if faces[0][0]+faces[0][2]*.5 < (frame.shape[1]/2 - 20):
            print('move right')
            if horz_dc < (PWM_MAX-DC_STEP):
                horz_dc += DC_STEP
                pwm_horz.ChangeDutyCycle(horz_dc)
        elif faces[0][0]+faces[0][2]*.5 > (frame.shape[1]/2 + 20):
            print('move left')
            if horz_dc > (PWM_MIN+DC_STEP):
                horz_dc -= DC_STEP
                pwm_horz.ChangeDutyCycle(horz_dc)
        else:
            print('x centered')
        if faces[0][1]+faces[0][3]*.5 < (frame.shape[0]/2-20):
            print('move up')
            if vert_dc > (PWM_MIN+DC_STEP):
                vert_dc -= DC_STEP
                pwm_vert.ChangeDutyCycle(vert_dc)
        elif faces[0][1]+faces[0][3]*.5 > (frame.shape[0]/2+20):
            print('move down')
            if vert_dc < (PWM_MAX-DC_STEP):
                vert_dc += DC_STEP
                pwm_vert.ChangeDutyCycle(vert_dc)
        else:
            print('y centered')
    print('vert_dc: ',vert_dc)
    print('horz_dc: ',horz_dc)        
    cv2.imshow("Face Detect", frame)
    keyCode = cv2.waitKey(5) &  0xFFF
    if keyCode == 27:
        break
cap.release()
cv2.destroyAllWindows()
