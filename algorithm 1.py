from SimpleCV import Image
import RPi.GPIO as GPIO
import time
from time import gmtime, strftime
from firebase import firebase
from google.cloud import storage
import os

count=0
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/pi/.config/gcloud/application_default_credentials.json'
client = storage.Client('room-monitoring-c5da7')
bucket = client.get_bucket('room-monitoring-c5da7.appspot.com')
firebase = firebase.FirebaseApplication('https://room-monitoring-c5da7.firebaseio.com/', None)

def getimge(s):
  os.system('fswebcam --no-banner -r 640x480 -S 2 /home/pi/Desktop/vision/'+s+'.jpg')
  return Image('/home/pi/Desktop/vision/'+s+'.jpg')


def Motion(channel):
  nowtime=strftime("%Y-%m-%d__%H:%M:%S", gmtime())
  img=getimge(nowtime)
  
GPIO.setmode(GPIO.BCM)
GPIO.setup(15, GPIO.IN)
GPIO.add_event_detect(15,GPIO.FALLING, callback=Motion,bouncetime=1000)

while True:
    for filenames in os.listdir('/home/pi/Desktop/vision'):
          time.sleep(0.01)
          img=Image('/home/pi/Desktop/vision/'+filenames)
          ftime=os.path.splitext(filenames)[0] 
          faces = img.findHaarFeatures('face.xml', min_neighbors=5)
          fullbody = img.findHaarFeatures('fullbody.xml', min_neighbors=5)'
          if faces:
             count+=1
             img=faces.crop()
             firebase.patch('/log/' ,{'curent_count': count})                          
             firebase.patch('/log/'+ ftime,{'state':'Entring','time':ftime,'count': count})
             Blob = bucket.blob(filenames)
             Blob.upload_from_filename(filename='/home/pi/Desktop/vision/'+filenames)
             print('entring')
             os.remove('/home/pi/Desktop/vision/'+filenames)
          elif fullbody:
             count-=1
             img=fullbody.crop()
             firebase.patch('/log/' ,{'curent_count': count})             
             firebase.patch('/log/' +ftime,{'state':'Exiting','time':ftime,'count': count})
             Blob = bucket.blob(filenames)
             Blob.upload_from_filename(filename='/home/pi/Desktop/vision/'+filenames)
             print('exit')
             os.remove('/home/pi/Desktop/vision/'+filenames)
          else:   
             os.remove('/home/pi/Desktop/vision/'+filenames)