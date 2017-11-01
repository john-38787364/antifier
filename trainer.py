import usb.core, os
global reslist, trainer_type, possfov

def fromcomp(val,bits):
  if val>>(bits-1) == 1:
    return 0-(val^(2**bits-1))-1
  else: return val

def send(dev_trainer, resistance_level, pedecho=0):
  global reslist  
  if 'reslist' in globals():#if not a simulation   
    r6=int(reslist[resistance_level])>>8 & 0xff #byte6
    r5=int(reslist[resistance_level]) & 0xff #byte 5
    byte_ints = [0x01, 0x08, 0x01, 0x00, r5, r6, pedecho, 0x00 ,0x02, 0x52, 0x10, 0x04]
    byte_str = "".join(chr(n) for n in byte_ints)
    try:
      dev_trainer.write(0x02, byte_str, 30)#send data to device
    except Exception, e:
      print "TRAINER WRITE ERROR", str(e)
    return resistance_level
  
def receive(dev_trainer):
  global trainer_type, possfov
  try:
    data = dev_trainer.read(0x82, 64, 30)
  except Exception, e:
    if "timeout error" in str(e):#trainer did not return any data
      pass
    else:
      print "TRAINER READ ERROR", str(e)
    return "Not Found", False, False, False, False
  if trainer_type == 0x1932:
    if len(data)>40:
      fs = int(data[33])<<8 | int(data[32])
      speed = round(fs/2.8054/100,1)#speed kph
      pedecho = data[42]
      heart_rate = int(data[12])
      cadence = int(data[44])
      force = fromcomp((data[39]<<8)|data[38],16)
      if force == 0:
        force = 1039
      force_index = possfov.index(force)
      return speed, pedecho, heart_rate, force_index, cadence
    else:
      return "Not Found", False, False, False, False
  elif trainer_type == 0x1942:#[0x0b,0x17,0x00,0x00,0x08,0x01,0x00,0x00,0x06,0x00,0x80,0xf8,0x00,0x00,0x00,0x00,0x59,0x02,0xdc,0x03,0xd0,0x07,0xd0,0x07,0x03,0x13,0x02,0x00,0x28,0x2b,0x00,0x00,0x00,0x00,0x28,0x63,0x00,0x00,0x00,0x00,0x41,0xf3,0x00,0x00,0x00,0x00,0x02,0xaa]
    if len(data)>40:
      fs = int(data[33])<<8 | int(data[32])
      speed = round(fs/2.8054/100,1)#speed kph
      pedecho = data[42]
      heart_rate = int(data[12])
      cadence = int(data[44])
      force = fromcomp((data[39]<<8)|data[38],16)
      force_index = possfov.index(force)
      return speed, pedecho, heart_rate, force_index, cadence
    else:
      return "Not Found", False, False, False, False
    
def get_trainer():
  global trainer_type, reslist, possfov
  trainer_type = 0
  idpl = [0x1932, 0x1942, 0xe6be]#iflow, fortius, uninitialised fortius
  for idp in idpl:
    dev = usb.core.find(idVendor=0x3561, idProduct=idp) #find trainer USB device
    if dev != None:
      trainer_type = idp
      break
    
  if trainer_type == 0:
    return False
  else:#found trainer
    if trainer_type == 0xe6be:#unintialised 1942
      print "Found uninitialised 1942 head unit"
      try:
        os.system("fxload-libusb.exe -I FortiusSWPID1942Renum.hex -t fx -vv")#load firmware
        print "Initialising head unit, please wait 5 seconds"
        time.sleep(5)
        dev = usb.core.find(idVendor=0x3561, idProduct=0x1942)
        if dev != None:
          print "1942 head unit initialised"
          trainer_type = 0x1942
        else:
          print "Unable to load firmware"
          return False
      except :#not found
        print "Unable to initialise trainer"
        return False
      
    if trainer_type == 0x1932:
      print "Found 1932 head unit"
      possfov=[1039, 1299, 1559, 1819, 2078, 2338, 2598, 2858, 3118, 3378, 3767, 4027, 4287, 4677]#possible force values to be recv from device
      reslist=[1900, 2030, 2150, 2300, 2400, 2550, 2700, 2900, 3070, 3200, 3350, 3460, 3600, 3750]#possible resistance value to be transmitted to device
    elif trainer_type == 0x1942:
      print "Found initialised 1942 head unit"
      possfov=[0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000]#possible force values to be recv from device
      reslist=[0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000]#possible resistance value to be transmitted to device
    
    dev.set_configuration()
    return dev
  
def initialise_trainer(dev):
  byte_ints = [2,0,0,0] # will not read cadence until initialisation byte is sent
  byte_str = "".join(chr(n) for n in byte_ints)
  dev.write(0x02,byte_str)
  
def parse_factors(filename):
  temp = open(filename,'r').read().split('\n')
  rtn ={}
  for l in temp:
    l=l.split("#")#get rid of comments
    l=l[0].split(":")
    if len(l)==2:
      vals = l[1].split(",")
      if len(vals)==2:
        rtn[float(l[0])]=[float(vals[0]), float(vals[1])]
  return rtn
