#based on T1932 protocol
import usb.core
import time
import T1932_calibration
import ant
import sys
import binascii
import struct
import platform, glob
import os
from datetime import datetime

if os.name == 'posix':
  import serial

def fromcomp(val,bits):
  if val>>(bits-1) == 1:
    return 0-(val^(2**bits-1))-1
  else: return val

powerfactor = 1
debug = False
simulatetrainer = False
for arga in sys.argv:
  arg = arga.split("=")
  if len(arg)==1: arg.append("")
  if "--simulate-trainer" in arg[0]:
    simulatetrainer = True

  if "--debug" in arg[0]:
    debug = True
    
  if "--power-factor" in arg[0]:
    powerfactor = arg[1]

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
        ant.send(stringl, dev_ant, debug)
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


#find trainer model for Windows and Linux
product=0
if not simulatetrainer:
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

ant.calibrate(dev_ant)#calibrate ANT+ dongle
ant.master_channel_config(dev_ant)#calibrate ANT+ channel FE-C
ant.second_channel_config(dev_ant)#calibrate ANT+ channel HR

resistance=1#set initial resistance level
speed,cadence,power,heart_rate=(0,)*4#initialise values

#initialise TACX USB device
byte_ints = [2,0,0,0] # will not read cadence until initialisation byte is sent
byte_str = "".join(chr(n) for n in byte_ints)
if not simulatetrainer:
  dev.write(0x02,byte_str)
time.sleep(1)

grade = 0
accumulated_power = 0
heart_beat_event_time = time.time() * 1000
heart_beat_event_time_start_cycle = time.time() * 1000
heart_toggle = 0
heart_beat_count = 0

eventcounter = 0
fedata = "a4 09 4e 00 10 19 89 8c 8d 20 00 30 72 00 00" 
#p.44 [10] general fe data, [19] eqpt type trainer, [89] acc value time since start in 0.25s r/over 64s, [8c] acc value time dist travelled in m r/over 256m, 
#[8d] [20] speed lsb msb 0.001m/s, [00] hr, [30] capabilities bit field
accumulated_time = time.time()*1000
distance_travelled = 0
last_dist_time = time.time()*1000

trainerdata = "a4 09 4e 00 19 00 5a b0 47 1b 01 30 6d 00 00" 
#p.60 [19] specific trainer data, [10] counter rollover 256, [5a] inst cadence, [b0] acc power lsb, [47] acc power msb (r/over 65536W), [1b] inst power lsb, 
#[01] bits 0-3 inst power MSB bits 4-7 trainer status bit, [30] flags bit field

try:
  while True:
    reply = {}
    last_measured_time = time.time() * 1000
    if eventcounter >= 256:
      eventcounter = 0
    ####################GET DATA FROM TRAINER####################
    if not simulatetrainer:
      if product==0x1932:#if is a 1932 headunit
        data = dev.read(0x82,64) #get data from device
        if debug == True: print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"TRAINER RX DATA",binascii.hexlify(data)
        #get values reported by trainer
        if len(data)==24:
          print "trainer possibly not powered up"
        if len(data) > 40:
          fs = int(data[33])<<8 | int(data[32])
          speed = round(fs/2.8054/100,1)#speed kph
          force = fromcomp((data[39]<<8)|data[38],16)
          if debug == True: print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"FORCE",force
          try:#try to identify force value from list of possible resistance values
            force = T1932_calibration.possfov.index(force)+1
            if debug == True: print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"FORCE INDEX", force
            power = T1932_calibration.calcpower(speed,force)
            power = int(power * float(powerfactor)) #alter for value passed on command line
          except ValueError:
            pass # do nothing if force value from trainer not recognised
          cadence = int(data[44])
          heart_rate = int(data[12])
    else:
        speed,cadence,power,heart_rate=(30, 90, 283, 72)
        power = int(power * float(powerfactor))
    if debug == True: print speed,cadence,power,heart_rate
    
    ####################SEND DATA TO TRAINER####################
    #send resistance data to trainer   
    if debug == True: print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"GRADE", grade*2,"%"
    if not simulatetrainer:
      if product==0x1932:#if is a 1932 headunit
        level = len(T1932_calibration.grade_resistance)#set resistance level to hardest as default
        for idx, g in enumerate(sorted(T1932_calibration.grade_resistance)):
          if g >= grade*2:#find resistance value immediately above grade set by zwift (Zwift ANT+ grade is half that displayed on screen)
            level = idx
            break
        if debug == True: print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"RESISTANCE LEVEL", T1932_calibration.reslist[level]
        r6=int(T1932_calibration.reslist[level])>>8 & 0xff #byte6
        r5=int(T1932_calibration.reslist[level]) & 0xff #byte 5
        #echo pedal cadence back to trainer
        if len(data) > 40:
          pedecho = data[42]
        else:
          pedecho = 0
        byte_ints = [0x01, 0x08, 0x01, 0x00, r5, r6, pedecho, 0x00 ,0x02, 0x52, 0x10, 0x04]
        if debug == True: print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"TRAINER TX DATA",byte_ints
        byte_str = "".join(chr(n) for n in byte_ints)
        dev.write(0x02,byte_str)#send data to device
    
    ####################BROADCAST AND RECEIVE ANT+ data####################
    if power >= 4094:
      power = 4093
    accumulated_power += power
    if accumulated_power >= 65536:
      accumulated_power = 0

    if (eventcounter + 1) % 66 == 0 or eventcounter % 66 == 0:#send first and second manufacturer's info packet
      newdata = "a4 09 4e 00 50 ff ff 01 0f 00 85 83 bb 00 00"
      
    elif (eventcounter+32) % 66 == 0 or (eventcounter+33) % 66 == 0:#send first and second product info packet
      newdata = "a4 09 4e 00 51 ff ff 01 01 00 00 00 b2 00 00"
    
    elif eventcounter % 3 == 0:#send general fe data every 3 packets
      accumulated_time_counter = int((time.time()*1000 - accumulated_time)/1000/0.25)# time since start in 0.25 seconds
      if accumulated_time_counter >= 256:#rollover at 64 seconds (256 quarter secs)
        accumulated_time_counter = 0
        accumulated_time = time.time()*1000
      newdata = '{0}{1}{2}'.format(fedata[:18], hex(accumulated_time_counter)[2:].zfill(2), fedata[20:]) # set time
      distance_travelled_since_last_loop = (time.time()*1000 - last_dist_time)/1000 * speed
      last_dist_time = time.time()*1000
      distance_travelled += distance_travelled_since_last_loop
      if distance_travelled >= 256:#reset at 256m
        distance_travelled = 0
      newdata = '{0}{1}{2}'.format(newdata[:21], hex(int(distance_travelled))[2:].zfill(2), newdata[23:]) # set distance travelled  
      hexspeed = hex(int(speed*1000))[2:].zfill(4)
      newdata = '{0}{1}{2}{3}{4}'.format(newdata[:24], hexspeed[2:], ' ' , hexspeed[:2], newdata[29:]) # set speed
      newdata = '{0}{1}{2}'.format(newdata[:36], ant.calc_checksum(newdata), newdata[38:])#recalculate checksum
      if debug == True: print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"FE DATA",newdata
    
    else:#send specific trainer data
      newdata = '{0}{1}{2}'.format(trainerdata[:15], hex(eventcounter)[2:].zfill(2), trainerdata[17:]) # increment event count
      if cadence >= 254:
        cadence=253
      newdata = '{0}{1}{2}'.format(newdata[:18], hex(cadence)[2:].zfill(2), newdata[20:])#instant cadence
      hexaccumulated_power = hex(int(accumulated_power))[2:].zfill(4)
      newdata = '{0}{1}{2}{3}{4}'.format(newdata[:21], hexaccumulated_power[2:], ' ' , hexaccumulated_power[:2], newdata[26:]) # set accumulated power
      hexinstant_power = hex(int(power))[2:].zfill(4)
      hexinstant_power_lsb = hexinstant_power[2:]
      newdata = '{0}{1}{2}'.format(newdata[:27], hexinstant_power_lsb, newdata[29:])#set power lsb byte
      hexinstant_power_msb = hexinstant_power[:2]
      bits_0_to_3 = bin(int(hexinstant_power_msb,16))[2:].zfill(4)
      power_msb_trainer_status_byte = '0000' + bits_0_to_3
      newdata = '{0}{1}{2}'.format(newdata[:30], hex(int(power_msb_trainer_status_byte))[2:].zfill(2), newdata[32:])#set mixed trainer data power msb byte
      newdata = '{0}{1}{2}'.format(newdata[:36], ant.calc_checksum(newdata), newdata[38:])#recalculate checksum
      if debug == True: print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"TRAINER DATA",newdata
      reply = ant.send([newdata], dev_ant, debug)
    if "grade" in reply:
      grade = reply['grade']
      
    ####################HR#######################
    #HR format
    #D00000693_-_ANT+_Device_Profile_-_Heart_Rate_Rev_2.1.pdf
    #[00][FF][FF][FF][55][03][01][48]p. 18 [00] bits 0:6 data page no, bit 7 toggle every 4th message, [ff][ff][ff] (reserved for page 0), [55][03] heart beat event time [lsb][ msb] rollover 64s, [01] heart beat count rollover 256, [instant heart rate]max 256
    #[00][FF][FF][FF][55][03][01][48]
    #[00][FF][FF][FF][AA][06][02][48]
    #[00][FF][FF][FF][AA][06][02][48]
    #[80][FF][FF][FF][AA][06][02][48]
    #[80][FF][FF][FF][AA][06][02][48]
    #[80][FF][FF][FF][FF][09][03][48]
    #[80][FF][FF][FF][FF][09][03][48]
    #[00][FF][FF][FF][FF][09][03][48]
    #[00][FF][FF][FF][54][0D][04][48]
    #[00][FF][FF][FF][54][0D][04][48]
    #[00][FF][FF][FF][54][0D][04][48]
    
    #every 65th message send manufacturer and product info -apge 2 and page 3
    #[82][0F][01][00][00][3A][12][48] - [82] page 2 with toggle on (repeat 4 times)
    #[83][01][01][33][4F][3F][13][48] - [83] page 3 with toggle on 
    
    #if eventcounter > 40: heart_rate = 100 #comment out in production
    if heart_rate>0:
      if eventcounter % 4 == 0:#toggle bit every 4 counts
        if heart_toggle == 0: heart_toggle = 128
        else: 
          heart_toggle = 0
      
      #check if heart beat has occurred as tacx only reports instanatenous heart rate data
      #last heart beat is at heart_beat_event_time
      #if now - heart_beat_event_time > time taken for hr to occur, trigger beat. 70 bpm = beat every 60/70 seconds
      if (time.time()*1000 - heart_beat_event_time) > (60 / heart_rate)*1000:
        heart_beat_count += 1#increment heart beat count
        heart_beat_event_time = time.time()*1000#reset last time of heart beat
        
      if heart_beat_event_time - heart_beat_event_time_start_cycle >= 64000:#rollover every 64s
        heart_beat_event_time = time.time()*1000#reset last heart beat event
        heart_beat_event_time_start_cycle = time.time()*1000#reset start of cycle
        
      if heart_beat_count >= 256:
        heart_beat_count = 0
      
      if heart_rate >= 256:
        heart_rate = 255
      
      hex_heart_beat_time = int((heart_beat_event_time - heart_beat_event_time_start_cycle)*1.024) # convert ms to 1/1024 of a second
      hex_heart_beat_time = hex(hex_heart_beat_time)[2:].zfill(4)
      
      hr_byte_4 = hex_heart_beat_time[2:]
      hr_byte_5 = hex_heart_beat_time[:2]
      hr_byte_6 = hex(heart_beat_count)[2:].zfill(2)
      hr_byte_7 = hex(heart_rate)[2:].zfill(2)
      
      
      if (eventcounter + 1) % 66 == 0 or eventcounter % 66 == 0:#send first and second manufacturer's info packet
        hr_byte_0 = hex(2 + heart_toggle)[2:].zfill(2)
        hr_byte_1 = "0f"
        hr_byte_2 = "01"
        hr_byte_3 = "00"
        #[82][0F][01][00][00][3A][12][48]
      elif (eventcounter+32) % 66 == 0 or (eventcounter+33) % 66 == 0:#send first and second product info packet
        hr_byte_0 = hex(3 + heart_toggle)[2:].zfill(2)
        hr_byte_1 = "01"
        hr_byte_2 = "01"
        hr_byte_3 = "33"      
        #[83][01][01][33][4F][3F][13][48]
        
      else:#send page 0
        hr_byte_0 = hex(0 + heart_toggle)[2:].zfill(2)
        hr_byte_1 = "ff"
        hr_byte_2 = "ff"
        hr_byte_3 = "ff"
        
      hrdata = "a4 09 4e 01 "+hr_byte_0+" "+hr_byte_1+" "+hr_byte_2+" "+hr_byte_3+" "+hr_byte_4+" "+hr_byte_5+" "+hr_byte_6+" "+hr_byte_7+" 02 00 00"
      hrdata = "a4 09 4e 01 "+hr_byte_0+" "+hr_byte_1+" "+hr_byte_2+" "+hr_byte_3+" "+hr_byte_4+" "+hr_byte_5+" "+hr_byte_6+" "+hr_byte_7+" "+ant.calc_checksum(hrdata)+" 00 00"
      time.sleep(0.125)# sleep for 120ms
      if debug == True: print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"HEART RATE",hrdata
      ant.send([hrdata], dev_ant, debug)
    ####################wait ####################
    
    #add wait so we only send every 250ms
    time_to_process_loop = time.time() * 1000 - last_measured_time
    sleep_time = 0.25 - (time_to_process_loop)/1000
    if sleep_time < 0: sleep_time = 0
    time.sleep(sleep_time)
    eventcounter += 1
except KeyboardInterrupt: # interrupt power data sending with ctrl c, make sure script continues to reset device
    pass

ant.send(["a4 01 4a 00 ef 00 00"],dev_ant, False)#reset ANT+ dongle

#ser.close()
