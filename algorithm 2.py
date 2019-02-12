//algorithm 1

//import all the librarys that we will use in this project
from SimpleCV import Image
from SimpleCV import Color, ColorCurve, Camera, Image, pg, np, cv
from SimpleCV.Display import Display
import RPi.GPIO as GPIO
import time
from time import gmtime, strftime
from firebase import firebase
from google.cloud import storage
import os

//inshlizing  global variables
feature=0
countEnt=0
countExi=0
countT=0
count=0
//inshlizing the Camera instans and resolution
cam = Camera()
cam.resolution = (1920, 1080)
//getimge() method will tack a picutre and save it to vision dirctory with the name we pass
def getimge(s):
      img = cam.getImage().save('/home/pi/Desktop/vision/'+s+'.jpg')
  return Image('/home/pi/Desktop/vision/'+s+'.jpg')
//exiting() method is the intrupt method for the first IR sensor
//it will increment the global variables  countT and save it in countExi then call the method chack()
def exiting(channel):
    global countExi
    global countT
    countT+=1
    countExi=countT
    chack()
//entering() method is the intrupt method for the socond IR sensor
//it will increment the global variables  countT and save it in countEnt then call the method chack()
def entering(channel):
    global countEnt
    global countT
    countT+=1
    countEnt=countT
    chack()
//chack() method will be called every time an intrupt happen to chack if the two sensor have started so it can dertermint the dircation of movment 
//it do that by comparing the value of countEnt and countExi if one of them is 0 that means thats one of the sensor did not start so it will exit
//if countEnt is > than countExi thats mean the entering sensor have beeen started after the exiting sensor so the state will be entering.
//if countExi is > than countEnt thats mean the exiting sensor have beeen started after the entering sensor so the state will be exiting.
//if we enter one of these two state we will get the exact time using gmtime() method and save it in a local variable called nowtime and we sprat it and the state by a(.) 
//then we will order the camra to tack an image and we name it the value of nowtime and save it in the vision dirctory so it can be procces later.
def chack():
    global countExi
    global countEnt    
    if countExi==0 or countEnt ==0:
      return
    elif countExi > countEnt:
      nowtime=strftime("%Y-%m-%d__%H:%M:%S.Exiting", gmtime())
      img=getimge(nowtime)
      print('exiting')
      countExi=0
      countEnt=0
    elif countExi < countEnt:
      nowtime=strftime("%Y-%m-%d__%H:%M:%S.Entring", gmtime())
      img=getimge(nowtime)
      print('entring')
      countExi=0
      countEnt=0

//inshlizing the location of the json file that hold CREDENTIALS key for our google storge,and we pass the name of project that we want to read from.
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/pi/.config/gcloud/application_default_credentials.json'
client = storage.Client('room-monitoring-c5da7')
bucket = client.get_bucket('room-monitoring-c5da7.appspot.com')
//connact to firebase realtime database
firebase = firebase.FirebaseApplication('https://room-monitoring-c5da7.firebaseio.com/', None)

//inshlizing the pins as input pin with a callback method as intrupt
//bouncetime=500 so we can give the sensor enogh time to reset befor calling the intrupt againg   
GPIO.setmode(GPIO.BCM)
GPIO.setup(15, GPIO.IN)
GPIO.setup(18, GPIO.IN)
GPIO.add_event_detect(15,GPIO.FALLING, callback=exiting,bouncetime=500)
GPIO.add_event_detect(18,GPIO.FALLING, callback=entering,bouncetime=500)

//this will loop forever
//it will keep chacking the file vision for any new images to procces(if intrupt happen it will exucute the intrupt then comeback to contuine exucuteing).
while True:
    //itirat for each image inside the vision file
    for filenames in os.listdir('/home/pi/Desktop/vision'):
          time.sleep(0.01)
          //inshliz the file as image so we can procces it using SimpleCV
          img=Image('/home/pi/Desktop/vision/'+filenames)
          //split the time and the state(first part will containg the time and the scaond will contain the state[entring,exiting])
          state=filenames.split('.')
          
          //procces the Image for human face,if found increment feature
          //we use muliple feature to incrase acurresy.
          faces = img.findHaarFeatures('face.xml', min_neighbors=5)
          if faces:
              feature+=1
          face2 = img.findHaarFeatures('face2.xml', min_neighbors=3)
          if face2:
              feature+=1          
          face3 = img.findHaarFeatures('face3.xml', min_neighbors=3)
          if face3:
              feature+=1
          face4 = img.findHaarFeatures('face4.xml', min_neighbors=3)
          if face4:
              feature+=1
          face_cv2 = img.findHaarFeatures('face_cv2.xml', min_neighbors=3)
          if face_cv2:
              feature+=1    
          print(feature)
          
          //if we found at least 3 feature out of 6 then he is a human.
          //we will add all his data to the realtime database and increment or dicrement the count(number of people on the room) depnding on the state.
          //finaly we will delate the image from the file so we dont procces it again.
          if feature>2:
             if state[1] == 'Entring':
              count+=1
             elif state[1] =='Exiting':
              count-=1
             firebase.patch('/log/' ,{'curent_count': count})                          
             firebase.patch('/log/'+ state[0],{'state':state[1],'time':state[0]})
             Blob = bucket.blob(filenames)
             Blob.upload_from_filename(filename='/home/pi/Desktop/vision/'+filenames)
             print('entring')
             feature=0
             os.remove('/home/pi/Desktop/vision/'+filenames)
             
          //if we found less than 3 feature then he is not humnan
          //we delate the image  
          else:   
             os.remove('/home/pi/Desktop/vision/'+filenames)


