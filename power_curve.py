import ant, os, usb.core, time, binascii

###windows###
if os.name == 'nt':
  found_available_ant_stick= True
  try:
    dev_ant = usb.core.find(idVendor=0x0fcf, idProduct=0x1009) #get ANT+ stick (garmin)
    dev_ant.set_configuration() #set active configuration
    try:#check if in use
      stringl=["a4 01 4a 00 ef 00 00"]#reset system
      ant.send(stringl, dev_ant, debug)
      print "Using Garmin dongle..."
    except usb.core.USBError:
      print "Garmin Device is in use"
      found_available_ant_stick = False
  except AttributeError:
    print "No Garmin Device found"
    found_available_ant_stick = False

  if found_available_ant_stick == False:
    found_available_ant_stick = True
    try:
      dev_ant = usb.core.find(idVendor=0x0fcf, idProduct=0x1008) #get ANT+ stick (suunto)
      dev_ant.set_configuration() #set active configuration   
      try:#check if in use
        stringl=["a4 01 4a 00 ef 00 00"]#reset system
        ant.send(stringl, dev_ant, False)
        print "Using Suunto dongle..."
      except usb.core.USBError:
        print "Suunto Device is in use"
        found_available_ant_stick = False
    except AttributeError:  
      print "No Suunto Device found"
      found_available_ant_stick = False

  if found_available_ant_stick == False:
    print "No available ANT+ device. Retry after quitting Garmin Express or other application that uses ANT+. If still fails then remove dongles for 10s then reinsert"
    sys.exit()
  

###Linux###
elif os.name == 'posix':
  #Find ANT+ USB stick on serial (Linux)
  ant_stick_found = False
  for p in glob.glob('/dev/ttyUSB*'):
    dev_ant = serial.Serial(p, 19200, rtscts=True,dsrdtr=True)
    dev_ant.timeout = 0.1
    dev_ant.write(binascii.unhexlify("a4014a00ef0000")) #probe with reset command
    reply = binascii.hexlify(dev_ant.read(size=256))
    if reply == "a4016f20ea" or reply == "a4016f00ca":#found ANT+ stick
      serial_port=p
      ant_stick_found = True
    else: dev_ant.close()#not correct reply to reset
    if ant_stick_found == True  : break

  if ant_stick_found == False:
    print 'Could not find ANT+ device. Check output of "lsusb | grep 0fcf" and "ls /dev/ttyUSB*"'
    sys.exit()
    
  
else:
  print "OS not Supported"
  sys.exit() 

ant.calibrate(dev_ant)#calibrate ANT+ dongle

#calibrate as power sensor
string=[
"a4 03 42 00 00 00 e5 00 00", #42 assign channel
"a4 05 51 00 00 00 0b 00 fb 00 00", #51 set channel id, 0b device=power sensor
"a4 02 45 00 39 da 00 00", #45 channel freq
"a4 03 43 00 f6 1f 0d 00 00", #43 msg period
"a4 02 71 00 00 d7 00 00", #71 Set Proximity Search chann number 0 search threshold 0
"a4 02 63 00 0a cf 00 00", #63 low priority search channel number 0 timeout 0
"a4 02 44 00 02 e0 00 00", #44 Host Command/Response 
"a4 01 4b 00 ee 00 00" #4b ANT_OpenChannel message ID channel = 0 D00001229_Fitness_Modules_ANT+_Application_Note_Rev_3.0.pdf
]
ant.send(string, dev_ant, True)
print "Do not pedal... calibrating"
ant.send(["a4 09 4f 00 01 aa ff ff ff ff ff ff 49 00 00"], dev_ant, True)
#print binascii.hexlify(dev_ant.read(0x81,64))
try:
  while True:
    reply = {}
    last_measured_time = time.time() * 1000
#a4 02 4d 00 51 ba 00 00 #51 product info #3969 (every 30s)

#a4 09 4f 00 01 aa ff ff ff ff ff ff 49 00 00 #general calibration request

#a4 02 4d 00 51 ba 00 00 #4918

#receives
#a4 09 4e 00 11 ec 98 00 7a 26 21 10 eb #11 wheel torque
#a4 09 4e 00 10 ec ff 00 be 4e 00 00 10 #10 power page be 4e accumulated power 00 00 iunstant power
    #add wait so we only send every 250ms
    try:
      read_val = binascii.hexlify(dev_ant.read(0x81,64))
      if read_val[8:10]=="10":
        print read_val, read_val[20:22], read_val[22:24], int(read_val[22:24],16)*16 + int(read_val[20:22],16)
    except usb.core.USBError:
      print "nothing received"    
     
    time_to_process_loop = time.time() * 1000 - last_measured_time
    sleep_time = 0.25 - (time_to_process_loop)/1000
    if sleep_time < 0: sleep_time = 0
    time.sleep(sleep_time)
except KeyboardInterrupt: # interrupt power data sending with ctrl c, make sure script continues to reset device
    pass

ant.send(["a4 01 4a 00 ef 00 00"],dev_ant, False)#reset ANT+ dongle
