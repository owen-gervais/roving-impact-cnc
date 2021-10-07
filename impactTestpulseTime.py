from machine import Pin, PWM, ADC, I2C
from mpu9250 import MPU9250
from utime import sleep

class Motor():
    def __init__(self, A,B):
        self.A = PWM(A) # Creating a PWM object for motor phase A
        self.A.freq(500) # Establishing PWM frequency
        self.A.duty_u16(0) # Setting 0% duty cycle
        self.B = PWM(B) # Creating a PWM object for motor phase B
        self.B.freq(500) # Esablishing PWM frequency
        self.B.duty_u16(0) # Setting 0% duty cycle
        
    def u16(self,percent): # Helper function converting the speed to u16
        return int(percent * 65536) 
        
    def mbreak(self):
        self.A.duty_u16(0) # Set both PWM low in order to break
        self.B.duty_u16(0)
        
    def mfloat(self):
        self.A.duty_u16(self.u16(1)) #
        self.B.duty_u16(self.u16(1)) #

    def speed(self, vel):
        speed = self.u16(min(abs(vel/100),1)) # Define the speed of the motor
        a,b = (self.A,self.B) if vel < 0 else (self.B,self.A) # Reverse the direction if the comm
        a.duty_u16(0)  # to float between pulses, make this a 1
        b.duty_u16(speed)
        
    def pulse(self,vel,time):
        self.speed(vel)
        sleep(time)
        self.speed(0)


class Count(object):
    def __init__(self,A,B):
        self.A = A
        self.B = B
        self.counter = 0
        self.rotation = 0
        self.angle = 0
        A.irq(self.cb,self.A.IRQ_FALLING|self.A.IRQ_RISING) #interrupt on line A
        B.irq(self.cb,self.B.IRQ_FALLING|self.B.IRQ_RISING) #interrupt on line B

    def cb(self,msg):
        other,inc = (self.B,1) if msg == self.A else (self.A,-1) #define other line and increment
        self.counter += -inc if msg.value()!=other.value() else  inc #XOR the two lines and increment
        self.rotation = self.counter/12/4.995
        self.angle = (self.rotation % 1) * 360
    
    def reset(self):
        self.counter = 0
        self.rotation = 0
        self.angle = 0
        
        
# Encoder count
tach = Count(Pin(18, Pin.IN),Pin(19, Pin.IN))
motor = Motor(Pin(21, Pin.OUT),Pin(20, Pin.OUT))
button = Pin(14, Pin.IN)
i2c = I2C(id=0, scl=Pin(17), sda=Pin(16))
m = MPU9250(i2c)


# Reset the tachometer
tach.reset()
motor.mfloat()


# Control system design requirements
desired = 0
Kp = 0.0078


while True:
    if button.value():
        motor.pulse(-100, 0.1) # Send a pulse into the system
    
    # Filter the noise out of the y_acceleration
    y_acceleration = 0 if m.acceleration[2] < impactThreshold else m.acceleration[2] 
    
    # Calculate feedback loop error
    error = Kp*abs((desired - y_acceleration))
    
    if error:
        motor.pulse(100, error)
    sleep(0.001) # slow the loop


    
