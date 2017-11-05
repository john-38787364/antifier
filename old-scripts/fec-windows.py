import usb.core, binascii
import time
import sys,re


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

def send(stringl):#send message string to dongle
  global reply_message, no_bytes_to_find
  rtn = {}
  for string in stringl:
    i=0
    send=""
    while i<len(string):
      send = send + binascii.unhexlify(string[i:i+2])
      i=i+3
    print ">>",binascii.hexlify(send)#log data to console
    #ser.write(send)
    dev.write(0x01,send)

    #ser.timeout = 0.1
    #read_val = binascii.hexlify(ser.read(size=256))
    read_val = binascii.hexlify(dev.read(0x81,64))
    print "read off wire: ",read_val
    
    read_val_list = read_val.split("a4")#break reply into list of messsages
    for rv in read_val_list:
      if len(rv)>6:
        if (int(rv[:2],16)+3)*2 == len(rv):
          if calc_checksum("a4"+rv) == rv[-2:]:#valid message
            #a4094f0033ffffffff964ffff7 is gradient message
            if rv[6:8]=="33":
              rtn = {'grade' : int(rv[18:20]+rv[16:18],16) * 0.01 - 200} #7% in zwift = 3.5% grade in ANT+
  return rtn

found_available_ant_stick= True
try:
  dev = usb.core.find(idVendor=0x0fcf, idProduct=0x1009) #get ANT+ stick (garmin)
  dev.set_configuration() #set active configuration
  try:#check if in use
    stringl=["a4 01 4a 00 ef 00 00"]#reset system
    send(stringl)
  except usb.core.USBError:
    print "Garmin Device is in use"
    found_available_ant_stick = False
except AttributeError:
  print "No Garmin Device found"
  found_available_ant_stick = False

if found_available_ant_stick == False:
  found_available_ant_stick = True
  try:
    dev = usb.core.find(idVendor=0x0fcf, idProduct=0x1008) #get ANT+ stick (suunto)
    dev.set_configuration() #set active configuration   
    try:#check if in use
      stringl=["a4 01 4a 00 ef 00 00"]#reset system
      send(stringl)
    except usb.core.USBError:
      print "Suunto Device is in use"
      found_available_ant_stick = False
  except AttributeError:  
    print "No Suunto Device found"
    found_available_ant_stick = False

if found_available_ant_stick == False:
  print "No available ANT+ device"
  sys.exit()
#print dev.get_active_configuration()
#usb.core.USBError: [Errno None] libusb0-dll:err [claim_interface] could not claim interface 0, win error: The requested resource is in use.       


print "Calibrating..."
stringl=[
"a4 02 4d 00 54 bf 00 00",#request max channels
"a4 01 4a 00 ef 00 00",#reset system
"a4 02 4d 00 3e d5 00 00",#request ant version
"a4 09 46 00 b9 a5 21 fb bd 72 c3 45 64 00 00",#set network key
]
send(stringl)

print "FEC channel config..."
stringl=[
"a4 03 42 00 10 00 f5 00 00",#[42] assign channel, [00] 0, [10] type 10 bidirectional transmit, [00] network number 0, [f5] extended assignment
"a4 05 51 00 01 00 11 05 e5 00 00",#[51] set channel ID, [00] number 0 (wildcard search) , [01] device number 1, [00] pairing request (off), [11] fec, [05] transmission type  (page 18 and 66 Protocols) 00000101 - 01= independent channel, 1=global data pages used
"a4 02 45 00 39 da 00 00",#[45] set channel freq, [00] transmit channel on network #0, [39] freq 2400 + 57 x 1 Mhz= 2457 Mhz
"a4 03 43 00 f6 1f 0d 00 00",#[43] set messaging period, [00] channel #0, [f61f] = 32768/8182(f61f) = 4Hz (The channel messaging period in seconds * 32768. Maximum messaging period is ~2 seconds. )
"a4 02 60 00 03 c5 00 00",#[60] set transmit power, [00] channel #0, [03] 0 dBm
"a4 01 4b 00 ee 00 00",#open channel #0
"a4 09 4e 00 50 ff ff 01 0f 00 85 83 bb 00 00",#broadcast manufacturer's data
]
send(stringl)


accumulated_power = 0
eventcounter=0
fedata = "a4 09 4e 00 10 19 89 8c 8d 20 00 30 72 00 00" 
#p.44 [10] general fe data, [19] eqpt type trainer, [89] acc value time since start in 0.25s r/over 64s, [8c] acc value time dist travelled in m r/over 256m, 
#[8d] [20] speed lsb msb 0.001m/s, [00] hr, [30] capabilities bit field
accumulated_time = time.time()*1000
distance_travelled = 0
last_dist_time = time.time()*1000

data = "a4 09 4e 00 19 00 5a b0 47 1b 01 30 6d 00 00" #p.60 [19] specific trainer data, [10] counter rollover 256, [5a] inst cadence, [b0] acc power lsb, [47] acc power msb (r/over 65536W), [1b] inst power lsb, [01] bits 0-3 inst power MSB bits 4-7 trainer status bit, [30] flags bit field

try:
    while True:
      for eventcounter in range(0,2000): #loop 2000 times sending power 283W cadence 90
        last_measured_time = time.time() * 1000
        
        if (eventcounter + 1) % 66 == 0:#send first manufacturer's info packet
          newdata = "a4 09 4e 00 50 ff ff 01 0f 00 85 83 bb 00 00"
          
        elif eventcounter % 66 == 0:#send second manufacturer's info packet
          newdata = "a4 09 4e 00 50 ff ff 01 0f 00 85 83 bb 00 00"
          
        elif (eventcounter+32) % 66 == 0:#send first product info packet
          newdata = "a4 09 4e 00 51 ff ff 01 01 00 00 00 b2 00 00"
        
        elif (eventcounter+33) % 66 == 0:#send second product info packet
          newdata = "a4 09 4e 00 51 ff ff 01 01 00 00 00 b2 00 00"
        
        elif eventcounter % 3 == 0:#send general fe data every 3 packets
          accumulated_time_counter = int((time.time()*1000 - accumulated_time)/1000/0.25)# time since start in 0.25 seconds
          if accumulated_time_counter >= 256:#rollover at 64 seconds (256 quarter secs)
            accumulated_time_counter = 0
            accumulated_time = time.time()*1000
          newdata = '{0}{1}{2}'.format(fedata[:18], hex(accumulated_time_counter)[2:].zfill(2), fedata[20:]) # set time
          speed = 9# m/s
          distance_travelled_since_last_loop = (time.time()*1000 - last_dist_time)/1000 * speed
          last_dist_time = time.time()*1000
          distance_travelled += distance_travelled_since_last_loop
          if distance_travelled >= 256:#reset at 256m
            distance_travelled = 0
          newdata = '{0}{1}{2}'.format(newdata[:21], hex(int(distance_travelled))[2:].zfill(2), newdata[23:]) # set distance travelled  
          hexspeed = hex(int(speed*1000))[2:].zfill(4)
          newdata = '{0}{1}{2}{3}{4}'.format(newdata[:24], hexspeed[2:], ' ' , hexspeed[:2], newdata[29:]) # set speed
          newdata = '{0}{1}{2}'.format(newdata[:36], calc_checksum(newdata), newdata[38:])#recalculate checksum
          print "FE DATA",newdata
        
        else:#send specific trainer data
          if eventcounter >= 256:
            eventcounter = 0
          newdata = '{0}{1}{2}'.format(data[:15], hex(eventcounter)[2:].zfill(2), data[17:]) # increment event count
          cadence = 90
          if cadence >= 254:
            cadence=253
          newdata = '{0}{1}{2}'.format(newdata[:18], hex(cadence)[2:].zfill(2), newdata[20:])#instant cadence
          power = 280
          if power >= 4094:
            power = 4093
          accumulated_power += power
          if accumulated_power >= 65536:
            accumulated_power = 0
          hexaccumulated_power = hex(int(accumulated_power))[2:].zfill(4)
          newdata = '{0}{1}{2}{3}{4}'.format(newdata[:21], hexaccumulated_power[2:], ' ' , hexaccumulated_power[:2], newdata[26:]) # set accumulated power
          hexinstant_power = hex(int(power))[2:].zfill(4)
          hexinstant_power_lsb = hexinstant_power[2:]
          newdata = '{0}{1}{2}'.format(newdata[:27], hexinstant_power_lsb, newdata[29:])#set power lsb byte
          hexinstant_power_msb = hexinstant_power[:2]
          bits_0_to_3 = bin(int(hexinstant_power_msb,16))[2:].zfill(4)
          power_msb_trainer_status_byte = '0000' + bits_0_to_3
          newdata = '{0}{1}{2}'.format(newdata[:30], hex(int(power_msb_trainer_status_byte))[2:].zfill(2), newdata[32:])#set mixed trainer data power msb byte
          newdata = '{0}{1}{2}'.format(newdata[:36], calc_checksum(newdata), newdata[38:])#recalculate checksum
          print "TRAINER DATA",newdata
          
        reply = send([newdata])
        if "grade" in reply:
          print "Grade set to ",reply['grade'],"%"
        
        
        eventcounter += 1
        
        #add wait so we only send every 250ms
        time_to_send = time.time() * 1000 - last_measured_time
        sleep_time = 0.25 - (time_to_send)/1000
        if sleep_time < 0: sleep_time = 0
        time.sleep(sleep_time)
        
except KeyboardInterrupt: # interrupt power data sending with ctrl c, make sure script continues to reset device
    pass

stringl=["a4 01 4a 00 ef 00 00"]#reset system
send(stringl)



