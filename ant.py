import binascii, re, os, usb.core, glob, serial

def calc_checksum(message):#calulate message checksum
  pattern = re.compile('[\W_]+')
  message=pattern.sub('', message)
  byte = 0
  xor_value = int(message[byte*2:byte*2+2], 16)
  data_length = int(message[byte*2+2:byte*2+4], 16)
  data_length += 3#account for sync byte, length byte and message type byte
  while (byte < data_length):#iterate through message progressively xor'ing
    if byte > 0: 
      xor_value = xor_value ^ int(message[byte*2:byte*2+2], 16)
    byte += 1
  return hex(xor_value)[2:].zfill(2)

def send(stringl, dev_ant, debug):#send message string to dongle
  rtn = {}
  read_val = ""
  for string in stringl:
    i=0
    send=""
    while i<len(string):
      send = send + binascii.unhexlify(string[i:i+2])
      i=i+3
    if debug == True: print ">>",binascii.hexlify(send)#log data to console
    if os.name == 'posix':
      dev_ant.write(send)
      dev_ant.timeout = 0.1
      read_val = binascii.hexlify(dev_ant.read(size=256))
    else:
      try:
        dev_ant.write(0x01,send)
        read_val = binascii.hexlify(dev_ant.read(0x81,64))
      except Exception, e:
        print "USB WRITE ERROR", str(e)
    
    if debug == True: print "<<",read_val
    
    read_val_list = read_val.split("a4")#break reply into list of messsages
    for rv in read_val_list:
      if len(rv)>6:
        if (int(rv[:2],16)+3)*2 == len(rv):
          if calc_checksum("a4"+rv) == rv[-2:]:#valid message
            #a4094f0033ffffffff964ffff7 is gradient message
            if rv[6:8]=="33":
              rtn = {'grade' : int(rv[18:20]+rv[16:18],16) * 0.01 - 200} #7% in zwift = 3.5% grade in ANT+
  return rtn


def calibrate(dev_ant):
  stringl=[
  "a4 02 4d 00 54 bf 00 00",#request max channels
  "a4 01 4a 00 ef 00 00",#reset system
  "a4 02 4d 00 3e d5 00 00",#request ant version
  "a4 09 46 00 b9 a5 21 fb bd 72 c3 45 64 00 00",#set network key b9 a5 21 fb bd 72 c3 45
  ]
  send(stringl,dev_ant, False)
  
def master_channel_config(dev_ant):
  stringl=[
  "a4 03 42 00 10 00 f5 00 00",#[42] assign channel, [00] 0, [10] type 10 bidirectional transmit, [00] network number 0, [f5] extended assignment
  "a4 05 51 00 01 00 11 05 e5 00 00",#[51] set channel ID, [00] number 0 (wildcard search) , [01] device number 1, [00] pairing request (off), [11] device type fec, [05] transmission type  (page 18 and 66 Protocols) 00000101 - 01= independent channel, 1=global data pages used
  "a4 02 45 00 39 da 00 00",#[45] set channel freq, [00] transmit channel on network #0, [39] freq 2400 + 57 x 1 Mhz= 2457 Mhz
  "a4 03 43 00 f6 1f 0d 00 00",#[43] set messaging period, [00] channel #0, [f61f] = 32768/8182(f61f) = 4Hz (The channel messaging period in seconds * 32768. Maximum messaging period is ~2 seconds. )
  "a4 02 60 00 03 c5 00 00",#[60] set transmit power, [00] channel #0, [03] 0 dBm
  "a4 01 4b 00 ee 00 00",#open channel #0
  "a4 09 4e 00 50 ff ff 01 0f 00 85 83 bb 00 00",#broadcast manufacturer's data
  ]
  send(stringl, dev_ant, False)

def second_channel_config(dev_ant):
  stringl=[
  "a4 03 42 01 10 00 f4 00 00",#[42] assign channel, [00] 0, [10] type 10 bidirectional transmit, [00] network number 0, [f4] normal assignment
  "a4 05 51 01 02 00 78 01 8a 00 00",#[51] set channel ID, [01] channel 1 , [02] device number 1, [00] pairing request (off), [78] device type HR sensor, [01] transmission type  (page 18 and 66 Protocols) 00000101 - 01= independent channel, 1=global data pages used
  "a4 02 45 01 39 db 00 00",#[45] set channel freq, [00] transmit channel on network #0, [39] freq 2400 + 57 x 1 Mhz= 2457 Mhz
  "a4 03 43 01 86 1f 7c 00 00",#[43] set messaging period, [00] channel #0, [f61f] = 32768/8182(f61f) = 4Hz (The channel messaging period in seconds * 32768. Maximum messaging period is ~2 seconds. )
  "a4 02 60 01 03 c4 00 00",#[60] set transmit power, [00] channel #0, [03] 0 dBm
  "a4 01 4b 01 ef 00 00",#open channel #0
  "a4 09 4e 01 82 0f 01 00 00 00 00 48 26 00 00",#broadcast manufacturer's data
  ]
  send(stringl, dev_ant, False)

def powerdisplay(dev_ant):
  #calibrate as power display
  stringl=[
  "a4 03 42 00 00 00 e5 00 00", #42 assign channel
  "a4 05 51 00 00 00 0b 00 fb 00 00", #51 set channel id, 0b device=power sensor
  "a4 02 45 00 39 da 00 00", #45 channel freq
  "a4 03 43 00 f6 1f 0d 00 00", #43 msg period
  "a4 02 71 00 00 d7 00 00", #71 Set Proximity Search chann number 0 search threshold 0
  "a4 02 63 00 0a cf 00 00", #63 low priority search channel number 0 timeout 0
  "a4 02 44 00 02 e0 00 00", #44 Host Command/Response 
  "a4 01 4b 00 ee 00 00" #4b ANT_OpenChannel message ID channel = 0 D00001229_Fitness_Modules_ANT+_Application_Note_Rev_3.0.pdf
  ]
  send(stringl, dev_ant, False)

def get_ant():
  ###windows###
  if os.name == 'nt':
    found_available_ant_stick= True
    try:
      dev_ant = usb.core.find(idVendor=0x0fcf, idProduct=0x1009) #get ANT+ stick (garmin)
      dev_ant.set_configuration() #set active configuration
      try:#check if in use
        stringl=["a4 01 4a 00 ef 00 00"]#reset system
        ant.send(stringl, dev_ant, debug)
        msg = "Using Garmin dongle..."
      except usb.core.USBError:
        found_available_ant_stick = False
    except AttributeError:
      #print "No Garmin Device found"
      found_available_ant_stick = False

    if found_available_ant_stick == False:
      found_available_ant_stick = True
      try:
        dev_ant = usb.core.find(idVendor=0x0fcf, idProduct=0x1008) #get ANT+ stick (suunto)
        dev_ant.set_configuration() #set active configuration   
        try:#check if in use
          stringl=["a4 01 4a 00 ef 00 00"]#reset system
          ant.send(stringl, dev_ant, False)
          msg = "Using Suunto dongle..."
        except usb.core.USBError:
          #print "Suunto Device is in use"
          found_available_ant_stick = False
      except AttributeError:  
        #print "No Suunto Device found"
        found_available_ant_stick = False

    if found_available_ant_stick == False:
      dev_ant = False 

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
        msg = "Found ANT Stick"
      else: dev_ant.close()#not correct reply to reset
      if ant_stick_found == True  : break

    if ant_stick_found == False:
      #print 'Could not find ANT+ device. Check output of "lsusb | grep 0fcf" and "ls /dev/ttyUSB*"'
      #sys.exit()
      dev_ant = False
      
    
  else:
    #print "OS not Supported"
    #sys.exit()
    dev_ant = False
  
  
  if not dev_ant: msg = "ANT Stick not found"
  return dev_ant, msg

def get_trainer():
  product=0
  idpl = [0x1932, 0x1942]#iflow, fortius
  for idp in idpl:
    dev = usb.core.find(idVendor=0x3561, idProduct=idp) #find iflow device
    if dev != None:
      product=idp
      break
    
  if product == 0:
    return False
  else:
    return dev
  
def initialise_trainer(dev):
  byte_ints = [2,0,0,0] # will not read cadence until initialisation byte is sent
  byte_str = "".join(chr(n) for n in byte_ints)
  dev.write(0x02,byte_str)