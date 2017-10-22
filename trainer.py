import usb.core, os
global reslist, trainer_type, possfov, factors, grade_resistance

def fromcomp(val,bits):
  if val>>(bits-1) == 1:
    return 0-(val^(2**bits-1))-1
  else: return val

def send(dev_trainer, grade, pedecho=0, resistance_level_override=False):
  global reslist, grade_resistance  
  if 'reslist' in globals():#if not a simulation
    #get resistance_level from grade
    if resistance_level_override:#if override grade and specify a level
      resistance_level = resistance_level_override
    else:
      resistance_level = len(grade_resistance) - 1 #set resistance level to hardest as default
      for idx, g in enumerate(sorted(grade_resistance)):
        if g >= grade*2:#find resistance value immediately above grade set by zwift (Zwift ANT+ grade is half that displayed on screen)
          resistance_level = idx
          break
    r6=int(reslist[resistance_level])>>8 & 0xff #byte6
    r5=int(reslist[resistance_level]) & 0xff #byte 5
    byte_ints = [0x01, 0x08, 0x01, 0x00, r5, r6, pedecho, 0x00 ,0x02, 0x52, 0x10, 0x04]
    byte_str = "".join(chr(n) for n in byte_ints)
    dev_trainer.write(0x02, byte_str, 30)#send data to device
    return resistance_level
  
def receive(dev_trainer):
  global trainer_type, possfov, factors
  data = dev_trainer.read(0x82, 64, 30)
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
      #print force, possfov, factors
      calc_power=round(factors[possfov.index(force)][0]*speed + factors[possfov.index(force)][1])
      if calc_power<0: calc_power=0
      #print speed, pedecho, heart_rate, calc_power, cadence
      return speed, pedecho, heart_rate, calc_power, cadence
    else:
      return "Not Found", False, False, False, False
  elif trainer_type == 0x1942:#0b17000008010000060080f8000000005902dc03d007d00703130200282b0000000028630000000041f30000000002aa
    if len(data)>80:
      fs = int(data[33])<<8 | int(data[32])
      speed = round(fs/2.8054/100,1)#speed kph
      pedecho = data[42]
      heart_rate = int(data[12])
      cadence = int(data[44])
      force = fromcomp((data[39]<<8)|data[38],16)
      calc_power = 0
      return speed, pedecho, heart_rate, calc_power, cadence
    else:
      return "Not Found", False, False, False, False
    
def get_trainer():
  global trainer_type, reslist, possfov, factors, grade_resistance
  trainer_type = 0
  idpl = [0x1932, 0x1942, 0xe6be]#iflow, fortius, uninitialised fortius
  for idp in idpl:
    dev = usb.core.find(idVendor=0x3561, idProduct=idp) #find trainer USB device
    if dev != None:
      trainer_type = idp
      break
    
  if trainer_type == 0:
    return False
  else:
    if trainer_type == 0x1932:
      print "Found 1932 trainer"
      import T1932_calibration
      reslist = T1932_calibration.reslist
      possfov = T1932_calibration.possfov
      factors = T1932_calibration.factors
      grade_resistance = T1932_calibration.grade_resistance
    elif trainer_type == 0xe6be:#unintialised fortius
      print "Found uninitialised  trainer"
      try:
        os.system("fxload-libusb.exe -I FortiusSWPID1942Renum.hex -t fx -vv")#load firmware
        print "Initialising trainer, please wait 5 seconds"
        time.sleep(5)
        dev = usb.core.find(idVendor=0x3561, idProduct=0x1942)
        if dev != None:
          print "Found 1942 trainer"
          trainer_type = 0x1942
          import T1942_calibration
          reslist = T1942_calibration.reslist
          possfov = T1942_calibration.possfov
          factors = T1942_calibration.factors
          grade_resistance = T1932_calibration.grade_resistance
        else:
          print "Unable to load firmware"
          return False
      except :#not found
        print "Unable to initialise trainer"
        return False
    elif trainer_type == 0x1942:
      print "Found 1942 trainer"
      import T1942_calibration
      reslist = T1942_calibration.reslist
      possfov = T1942_calibration.possfov
      factors = T1942_calibration.factors
      grade_resistance = T1932_calibration.grade_resistance
    
    dev.set_configuration()
    return dev
  
def initialise_trainer(dev):
  byte_ints = [2,0,0,0] # will not read cadence until initialisation byte is sent
  byte_str = "".join(chr(n) for n in byte_ints)
  dev.write(0x02,byte_str)
