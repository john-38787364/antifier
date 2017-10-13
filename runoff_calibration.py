import usb.core, time, sys

#find trainer model for Windows and Linux
product=0

idpl = [0x1932, 0x1942]#iflow, fortius
for idp in idpl:
  dev = usb.core.find(idVendor=0x3561, idProduct=idp) #find iflow device
  if dev != None:
    product=idp
    break

if product == 0:
  print "Trainer not found"
  sys.exit()
  
dev.set_configuration() #set active configuration
  
#initialise TACX USB device
byte_ints = [2,0,0,0] # will not read cadence until initialisation byte is sent
byte_str = "".join(chr(n) for n in byte_ints)
dev.write(0x02,byte_str)



print "Tyre pressure 100psi (unloaded), aim for 7.2s rolloff"
print "Warm up 2 mins. Cycle 30kph-40kph for 30s then to above 40kph then stop pedalling and freewheel"
print "Rolldown timer will start automatically when you hit 40kph, so stop pedalling quickly!"

speed = 0
running = True
rolldown = False
rolldown_time = 0
while running == True:
  time.sleep(0.1)
  #get data
  if product==0x1932:#if is an iflow
    data = dev.read(0x82,64) #get data from device
    #get values reported by trainer
    fs = int(data[33])<<8 | int(data[32])
    speed = round(fs/2.8054/100,1)#speed kph
    cadence = int(data[44])
    if len(data) > 40:
      pedecho = data[42]
    else:
      pedecho = 0
    time.sleep(0.1)
    #send data
    #2700 res=6
    r6=int(2700)>>8 & 0xff #byte6
    r5=int(2700) & 0xff #byte 5
    byte_ints = [0x01, 0x08, 0x01, 0x00, r5, r6, pedecho, 0x00 ,0x02, 0x52, 0x10, 0x04]
    byte_str = "".join(chr(n) for n in byte_ints)
    dev.write(0x02,byte_str)#send data to device
  if speed > 40 or rolldown == True:
    sys.stdout.write("Rolldown timer started!")
    sys.stdout.flush()
    rolldown = True
    if rolldown_time == 0:
      rolldown_time = time.time()#set initial rolldown time
    if speed < 0.1:#wheel stopped
      running = False#break loop
      sys.stdout.write("Rolldown time = %s seconds" % (time.time() - rolldown_time))
      sys.stdout.flush()
  else:
    sys.stdout.write("Speed: %s Cadence: %s  \r" % (str(speed).zfill(2),str(cadence)) )
    sys.stdout.flush()
 
    
