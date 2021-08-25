# This script contains the client side program which runs on the Raspberry Pi 3.
# The following dependencies are imported.
# picamera ---> PiCamera library.
# cv2 ---> OpenCV for Image Processing.
# os ---> system file handling.
# socket ---> To create the connection to remote cloud system.
# RPi.GPIO ---> Raspberry Pi GPIO handling.
# servoControl ---> Contains codes for controlling the robotic arm.
# twilio ---> SMS API library.

from picamera import PiCamera
from picamera.array import PiRGBArray
import cv2,os,socket,sys,time,Adafruit_PCA9685
import numpy as np
from twilio.rest import Client
import RPi.GPIO as GPIO
import lcdsetup as lcd

# Intialize the LCD display.

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line

# Default message to be dsiplayed when no object is detected.

def default_lcd_msg():
    lcd.lcd_string("Automatic Waste",LCD_LINE_1)
    lcd.lcd_string("Segregator",LCD_LINE_2)
    time.sleep(2)

'''
* Following function handles the SMS sending.
* account_sid , auth_token ---> used for authenticating.
* client ---> initialised to Twilion SMS API Class.
'''

def sendSMS(msg):
    account_sid = "TWILIO_ACCOUNT_SID"
    auth_token = "TWILIO_AUTH_TOKEN"
    client = Client(account_sid, auth_token)
    client.api.account.messages.create(to="+918147661833",from_="+18043125524",body=msg)
    print("SMS sent !")

'''
* Following function checks the status of the bins to trigger SMS sending.
* 2 IR sensors are used to detect level of filling.
* bio ---> sensor over bio bin.
* non-bio ---> sensor over the non-bio bin.
* Respective SMS are sent and the LCD display is updated.
'''

def binStatus():

    bio = GPIO.input(37)
    nonbio= GPIO.input(38)
    if  GPIO.input(37) != False : #object is near   
        time.sleep(2)
        if  GPIO.input(37) != False :
            msg="Biodegradable bin is full. Please REPLACE."
            lcd.lcd_string("Alert!!!",LCD_LINE_1)
            lcd.lcd_string("Bio bin full",LCD_LINE_2)
            sendSMS(msg)
            print(msg)
            time.sleep(2)

    if  GPIO.input(38) != False : #object is near  
        time.sleep(2)
        if  GPIO.input(38) !=False :
            msg="Non-biodegradable bin is full. Please REPLACE."
            lcd.lcd_string("Alert!!!",LCD_LINE_1)
            lcd.lcd_string("Non-Bio bin full",LCD_LINE_2)
            sendSMS(msg)
            print(msg)
            time.sleep(2)

    print("Bin status is updated !")
    default_lcd_msg()

'''
* The following function handles the direction of rotation of the flap.
* direction ---> flag representing direction of rotation.
* center ---> flap resting position.
* left ---> flap left side rotated.
* right ---> flap right side rotated.
'''

def flap(direction):
    print("Operating flap..")
    center=185
    left=80
    right=340
    pin=0
    if direction=='l':
        for i in range(center,left,-1):
            pwm.set_pwm(pin,0,i)
            time.sleep(0.01)
        time.sleep(2)
        for i in range(left,215,1):
            pwm.set_pwm(pin,0,i)
            time.sleep(0.01)
    elif direction=='r':
        center=170
        for i in range(center,right,1):
            pwm.set_pwm(pin,0,i)
            time.sleep(0.01)
        time.sleep(2)
        for i in range(right,center,-1):
            pwm.set_pwm(pin,0,i)
            time.sleep(0.01)

''' 
* The following function handles the communication with the Cloud system where Machine Learning 
analysis of the image takes place.
* Port 60000 is used for establishing the connection.
* img ---> refers to the image of the detected image.
* s---> instance of the socket class.
* data ---> stores the byte content of the image.
* length ---> length of the total bytes in data.
* status ---> acknowledgemnt from server.
* binFlag ---> Direction to rotate the flap.
'''

def clientResponse(img,Ip_addr):
    filename="newimg.jpg"
    cv2.imwrite(filename,img)
    s = socket.socket()         
    port = 60000              
    s.connect((Ip_addr, port))
    print("Established connection.")
    f=open(filename,"rb")
    data=f.read()
    f.close()
    print("\nSending Length information..")
    length=str(len(data))
    s.send(bytes(length,"utf-8"))
    
    status=s.recv(2)
    print("Length Reception Acknowledgement - "+str(status.decode("utf-8")))
    print("Sending the image to Google Cloud for Tensorflow processing. . .")
    f=open(filename,"rb")
    data=f.read(1)
    # Progress bar to indicate status of sending the image.
    length=int(length)
    count=0
    counter=0
    slab=int(length/10)
    print("\nProgress-")
    while data:
        s.send(data)
        data=f.read(1)
        count+=1
        if count==slab:
            counter+=1
            sys.stdout.write('\r')
            sys.stdout.write('['+"#"*counter+" "*(10-counter)+']'+" "+str(counter*10)+"%")
            sys.stdout.flush()
            count=0
    sys.stdout.write("\n")
    sys.stdout.flush()
    print("Sent sucessfully!")
    f.close()
    
    binFlag=s.recv(1)
    print("Cloud response received.")
    if str(binFlag.decode("utf-8"))=="l":
        print("Object is biodegradable. Rotating bin on the left side.")
    elif str(binFlag.decode("utf-8"))=="r":
        print("Object is non-biodegradable. Rotating bin on the right side.")
    s.close()
    os.system("clear")
    return binFlag.decode("utf-8")

# The following function converts the RGB image into HSV color space.

def imageSubtract(img):
    hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    return hsv

'''
* The following function analyses the presence of any object.
* camera ---> Initialises to PiCamera class.
* First 30 frames are rejected to properly intialise the camera on startup.
* Reference image and new images are subtracted.
* Contours of size > 1000 and number <4 are searched. If found, object is detected.
* cX, cY ---> centre of the object in the image frame.
* binDir ---> contains the ML analysis of the detected object.
* The background image is refreshed after every 30 frames for maintaining keeping noise effects to minimum.
'''

def  imageProcessing(Ip_addr):
    camera = PiCamera()
    camera.resolution = (512,512)
    camera.awb_mode="fluorescent"
    camera.iso = 800
    camera.contrast=25
    camera.brightness=64
    camera.sharpness=100
    rawCapture = PiRGBArray(camera, size=(512, 512))
    first_time=0
    frame_buffer=0
    counter=0
    camera.start_preview()
    time.sleep(1)

    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        if first_time==0:
            rawCapture.truncate(0)
            if frame_buffer<30:
                print("Frame rejected -",str(frame_buffer))
                frame_buffer+=1
                continue
            refImg=frame.array
            refImg=refImg[40:490,25:]
            refThresh=imageSubtract(refImg)
            first_time=1
            frame_buffer=0

        frame_buffer+=1
        image = frame.array
        image=image[40:490,25:]
        rawCapture.truncate(0)
        newThresh=imageSubtract(image)
        cv2.imshow("Foreground", newThresh)
        key = cv2.waitKey(1)

        diff=cv2.absdiff(refThresh,newThresh)
        cv2.imshow("Background",refThresh)
        diff=cv2.cvtColor(diff,cv2.COLOR_BGR2GRAY)
        kernel = np.ones((5,5),np.uint8)
        diff = cv2.morphologyEx(diff, cv2.MORPH_OPEN, kernel)
        diff=cv2.erode(diff,kernel,iterations = 2)
        diff=cv2.dilate(diff,kernel,iterations = 3)

        _, thresholded = cv2.threshold(diff, 0 , 255, cv2.THRESH_BINARY +cv2.THRESH_OTSU)
        _, contours, _= cv2.findContours(thresholded,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        try:
            c=max(contours,key=cv2.contourArea)
            mask = np.zeros(newThresh.shape[:2],np.uint8)
            new_image = cv2.drawContours(mask,[c],0,255,-1,)
            cv2.imshow("new",new_image)
            cv2.imshow("threshold",thresholded)
            if cv2.contourArea(c)>1000 and len(contours)<=4:
                if counter==0:
                    print("Possible object detcted ! Going to sleep for 3 seconds")
                    time.sleep(3)
                    counter=1
                    continue
                else:
                    os.system("clear")
                    M=cv2.moments(c)
                    cX = int(M['m10']/M['m00'])
                    cY = int(M['m01']/M['m00'])
                    print("Total contours found=",len(contours))
                    print("Object detected with area = ",cv2.contourArea(c))
                    lcd.lcd_string("Alert!!!",LCD_LINE_1)
                    lcd.lcd_string("Detected Object",LCD_LINE_2)
                    time.sleep(2)
                    binDir=clientResponse(image,Ip_addr)
                    lcd.lcd_string("Waste Detected:-",LCD_LINE_1)
                    if binDir=='l':
                        print("Waste is Biodegradable")
                        lcd.lcd_string("Biodegradable",LCD_LINE_2)
                    elif binDir=='r':
                        print("Waste is Non-biodegradable")
                        lcd.lcd_string("Non-Bio",LCD_LINE_2)
                    flap(binDir) # call the flap function
                    first_time=0
                    frame_buffer=0
                    counter=0
                    print("Waste segregated !")
                    time.sleep(2)
                    binStatus()
                    continue
                default_lcd_msg()
            
        except Exception as e:
            print(e)
            pass
        
        if key == ord('q'):
            camera.close()
            cv2.destroyAllWindows()
            break

'''
* The script execution starts from here.
* The IR sensors connected to the GPIO pins are intialised.
* The pwm needed for operating the motor is initialised.
* The IP address is hardcoded here which is generally considered a bad practice. 
  Avoid hardcoding any value. 
* The system is started by invoking the imageProcessing function.
'''

if __name__ == "__main__" :
    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(37,GPIO.IN) #GPIO 16 for IR connected over bio degradable  bin
        GPIO.setup(38,GPIO.IN) #GPIO 18 for IR connected over non bio degradable bin
        pwm = Adafruit_PCA9685.PCA9685()
        pwm.set_pwm_freq(50)
        print("Started the system !")
        lcd.main()
        default_lcd_msg()
        Ip_addr = "192.168.43.39"
        imageProcessing(Ip_addr)
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
        GPIO.cleanup() 
    except Exception as e:
        print(e)
