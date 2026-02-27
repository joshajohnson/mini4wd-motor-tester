from machine import Pin

class MOTORCTRL:
    
    '''
    Control logic for DRV8837 motor driver.
    Does not support PWM speed control, only direction and brake.

    Example:

        motor = MOTORCTRL(motor_en=15, motor_in1=6, motor_in2=5)
        motor.enable()
        motor.forward()
        motor.reverse()
        motor.brake()
        motor.disable()
    
    '''

    def __init__ (self, motor_en: int = 15, motor_in1: int = 6, motor_in2: int = 5):
        self.motor_en = Pin(motor_en, Pin.OUT, Pin.PULL_DOWN)
        self.motor_in1 = Pin(motor_in1, Pin.OUT, Pin.PULL_DOWN)
        self.motor_in2 = Pin(motor_in2, Pin.OUT, Pin.PULL_DOWN)

    def enable(self):
        '''Wake motor from sleep'''
        self.motor_en.value(1)

    def disable(self):
        '''Put motor to sleep'''
        self.motor_en.value(0)

    def coast(self):
        '''Coast motor (free run)'''
        self.motor_in1 = Pin(self.motor_in1, Pin.IN)
        self.motor_in2 = Pin(self.motor_in2, Pin.IN)

    def forward(self):
        '''Set motor direction forward'''
        self.motor_in1 = Pin(self.motor_in1, Pin.OUT, Pin.PULL_UP)
        self.motor_in2 = Pin(self.motor_in2, Pin.OUT, Pin.PULL_DOWN)
        self.motor_in1.value(1)
        self.motor_in2.value(0)

    def reverse(self):
        '''Set motor direction reverse'''
        self.motor_in1 = Pin(self.motor_in1, Pin.OUT, Pin.PULL_DOWN)
        self.motor_in2 = Pin(self.motor_in2, Pin.OUT, Pin.PULL_UP)
        self.motor_in1.value(0)
        self.motor_in2.value(1)

    def brake(self):
        '''Brake motor'''
        self.motor_in1 = Pin(self.motor_in1, Pin.OUT, Pin.PULL_DOWN)
        self.motor_in2 = Pin(self.motor_in2, Pin.OUT, Pin.PULL_DOWN)
        self.motor_in1.value(0)
        self.motor_in2.value(0)