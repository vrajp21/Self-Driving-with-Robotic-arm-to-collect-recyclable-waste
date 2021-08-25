import time
from adafruit_servokit import ServoKit


def orginalposition():
    time.sleep(1)
    kit.servo[1].angle = 0
    time.sleep(1)
    kit.servo[5].angle = 40
    time.sleep(1)
    kit.servo[7].angle = 50
    time.sleep(1)
    kit.servo[11].angle = 100
    time.sleep(1)
    



def bio():
    
    orginalposition()
    kit.servo[5].angle = 70
    time.sleep(1)
    kit.servo[7].angle = 50
    time.sleep(1)
    kit.servo[1].angle = 60
    #kit.continuous_servo[1].throttle = 1
    time.sleep(1)
    kit.servo[7].angle = 70
    time.sleep(1)
    kit.servo[5].angle = 30
    time.sleep(1)
    kit.servo[7].angle = 90
    time.sleep(1)
    kit.servo[5].angle = 0
    time.sleep(1)
    kit.servo[7].angle = 120
    time.sleep(1)
    kit.servo[11].angle = 0
    time.sleep(1)
    orginalposition()
    
    
    
def nonbio():
    
    orginalposition()
    kit.servo[5].angle = 70
    time.sleep(1)
    kit.servo[7].angle = 50
    time.sleep(1)
    kit.servo[1].angle = 60
    #kit.continuous_servo[1].throttle = 1
    time.sleep(1)
    kit.servo[7].angle = 70
    time.sleep(1)
    kit.servo[5].angle = 30
    time.sleep(1)
    kit.servo[7].angle = 90
    time.sleep(1)
    kit.servo[5].angle = 0
    time.sleep(1)
    kit.servo[7].angle = 120
    time.sleep(1)
    kit.servo[11].angle = 180
    time.sleep(1)
    orginalposition()



if __name__ == '__main__' :
    try:
        kit = ServoKit(channels=16)
        #orginalposition()
        bio()
        nonbio()
    except Exception as e:
        print(e)
