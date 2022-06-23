# Author: Robert Pritchard
# Date Updated: March 25 2022
# PanTilt class containing helper functions for moving the pantilt mount interfacing directly with
# the servo motors using PWM on the Jetson Nano

import Jetson.GPIO as GPIO
# PWM_MAX = 10
# PWM_MIN = 2.5
# DC_STEP = 0.025

class PT_Mount:
    
    def __init__(self, vert_start = 0.5, horz_start = 0.5, PWM_MAX = 12, PWM_MIN = 3, DC_STEP = 0.25):
        # vert_start and horz_start are in 
        # Define class constants
        self.PWM_MAX = PWM_MAX
        self.PWM_MIN = PWM_MIN
        self.DC_STEP = DC_STEP
        self.PWM_RANGE = PWM_MAX-PWM_MIN

        # set up GPIO
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(33, GPIO.OUT)
        GPIO.setup(32,GPIO.OUT)

        self.pwm_vert = GPIO.PWM(33,50)
        self.pwm_horz = GPIO.PWM(32,50)

        # initialize the camera to starting position
        self.vert_dc = self.PWM_MIN+vert_start * self.PWM_RANGE
        self.horz_dc = self.PWM_MIN+ horz_start * self.PWM_RANGE

        self.vert_pos = vert_start
        self.horz_pos = horz_start

        self.pwm_vert.start(self.vert_dc)
        self.pwm_horz.start(self.horz_dc)

    def H_STEP(self,num_steps,lower_bound = 0, upper_bound = 1):
        temp = self.horz_dc + num_steps*self.DC_STEP
        l_bound = self.PWM_MIN+lower_bound*self.PWM_RANGE
        u_bound = self.PWM_MIN+upper_bound*self.PWM_RANGE
        if temp < l_bound or temp > u_bound:
            # do nothing
            return 0
        self.horz_dc = temp
        self.horz_pos = (temp-self.PWM_MIN)/self.PWM_RANGE
        self.pwm_horz.ChangeDutyCycle(self.horz_dc)
        return 1
    
    def V_STEP(self, num_steps, lower_bound = 0, upper_bound = 1):
        temp = self.vert_dc + num_steps * self.DC_STEP
        l_bound = self.PWM_MIN+lower_bound*self.PWM_RANGE
        u_bound = self.PWM_MIN+upper_bound*self.PWM_RANGE
        if temp < l_bound or temp > u_bound:
            # do nothing
            return 0
        self.vert_dc = temp
        self.vert_pos = (temp-self.PWM_MIN)/self.PWM_RANGE
        self.pwm_vert.ChangeDutyCycle(self.vert_dc)
        return 1

    def MOVE2D(self, vert_position, horz_position):
        if vert_position<0 or vert_position>1:
            print('Vertical position must be between 0 and 1')
            return -1
        if horz_position<0 or horz_position>1:
            print('Horizontal position must be between 0 and 1')
            return -1
        self.vert_dc = self.PWM_MIN+vert_position*self.PWM_RANGE
        self.horz_dc = self.PWM_MIN+horz_position*self.PWM_RANGE
        self.pwm_vert.ChangeDutyCycle(self.vert_dc)
        self.pwm_horz.ChangeDutyCycle(self.horz_dc)
        self.vert_pos = vert_position
        self.horz_pos = horz_position