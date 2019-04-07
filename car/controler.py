import tty
import sys
import termios
import time
from threading import Timer

from pwm import PWM


class CarControl:
    
    def _init_cons(self):
        self.PERIOD = 20000000

        self.STOP = 1000000
        self.MAX_SPEED = 1200000

        self.MAX_TURN = 300000
        self.MID = 2226500

        #for timer
        self.SPEED_TIMES = 50
        #self.SPEED_STEPS = (self.MAX_SPEED - self.STOP) // self.SPEED_TIMES pre:整除
        self.ANGLE_TIMES = 50
        #self.ANGLE_STEPS = self.MAX_TURN // self.ANGLE_TIMES pre
     
    def __init__(self):
        self._init_cons()
        self._speed_flag = False
        self._angle_flag = False
        
        #init motor
        self.motor = PWM(0)
        self.motor.export()
        self.motor.period = self.PERIOD
        self._set_speed(0.0)
        self.motor.enable = True
        
        #init servo
        self.servo = PWM(1)
        self.servo.export()
        self.servo.period = self.PERIOD
        self._set_angle(0.0)
        self.servo.enable = True
        
        
    def _set_speed(self, speed):
        ''' speed : 0 - 1 (double)'''
        if speed < 0 or speed > 1:
            print("invalid speed!")
            return 
        print("Set speed: {}".format(speed))
        self._speed = speed
        self.motor.duty_cycle = int(self.STOP + (self.MAX_SPEED - self.STOP)*speed) 
    
    def _set_angle(self, angle):
        ''' angle: -1 - 1 (double) -1 - 0 right, 0 - 1 left'''
        if angle < -1:
            angle = -1
        if angle > 1:
            angle = 1
        print("Set angle: {}".format(angle))
        self._angle = angle
        self.servo.duty_cycle =  int(self.MID + self.MAX_TURN*angle) 
        
    def set_angle(self, angle):
        self._set_angle(angle)
        
    def get_angle(self):
        return self._angle
    
    def get_speed(self):
        return self._speed
    
    def __del__(self):
        self.motor.enable = False
        self.servo.enable = False
        self.motor.unexport()
        self.servo.unexport()
    
    def _speed_up(self):
        if not self._speed_flag:
            return
        if self._speed + 1 / self.SPEED_TIMES > 1:
            return
        self._set_speed(self._speed+1/self.SPEED_TIMES)
        t = Timer(0.5/self.SPEED_TIMES, self._speed_up)
        t.start()
        
    def speed_up(self):
        self._speed_flag = True
        self._speed_up()
    
    def speed_down(self):
        self._speed_flag = False
        self._set_speed(0)
        
    def _turn_left(self):
        if not self._angle_flag:
            return
        if self._angle + 1 / self.ANGLE_TIMES > 1:
            return
        print(self._angle)
        self._set_angle(self._angle+1/self.ANGLE_TIMES)
        t = Timer(0.5/self.ANGLE_TIMES, self._turn_left)
        t.start()
        
    def _turn_right(self):
        if not self._angle_flag:
            return
        if self._angle - 1 / self.ANGLE_TIMES < -1:
            return
        self._set_angle(self._angle-1/self.ANGLE_TIMES)
        t = Timer(0.5/self.ANGLE_TIMES, self._turn_right)
        t.start()
    
    def turn_left(self):
        self._angle_flag = True
        self._turn_left()
        
    def turn_right(self):
        self._angle_flag = True
        self._turn_right()
        
    def turn_back(self):
        self._angle_flag = False
        self._set_angle(0)

control = CarControl()

'''
def test():
    orig_settings = termios.tcgetattr(sys.stdin)

    tty.setcbreak(sys.stdin)
    x = 0

    control = CarControl()
    while x != chr(27): # ESC
        x=sys.stdin.read(1)[0]
        if x == "a":
            print("left")
            control.turn_left()
        elif x == "d":
            print("right")
            control.turn_right()
        elif x == "w":
            print("speed up")
            control.speed_up()

        elif x == "s":
            print("speed down")
            control.speed_down()

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)  
'''
