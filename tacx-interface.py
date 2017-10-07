#based on T1932 protocol
import usb.core
import time
import T1932_calibration
import ant
import sys
import serial, binascii
import struct
import platform, glob
  
def list_serial_ports():
  system_name = platform.system()
  if system_name == "Windows":
    # Scan for available ports.
    available = []
    for i in range(256):
        try:
            s = serial.Serial(i)
            available.append(i)
            s.close()
        except serial.SerialException:
            pass
    return available
  elif system_name == "Darwin":
    # Mac
    return glob.glob('/dev/tty*') + glob.glob('/dev/cu*')
  else:
    # Assume Linux or something else
    return glob.glob('/dev/ttyUSB*')

def fromcomp(val,bits):
  if val>>(bits-1) == 1:
    return 0-(val^(2**bits-1))-1
  else: return val

dev = usb.core.find(idVendor=0x3561, idProduct=0x1932) #find iflow device
try:
  dev.set_configuration() #set active configuration
except AttributeError:
  print "Could not find trainer USB connection"
  #sys.exit()

#Find ANT+ USB stick
ant_stick_found = False
for p in list_serial_ports():
  ser = serial.Serial(p, 19200, rtscts=True,dsrdtr=True)
  ser.timeout = 0.1
  ser.write(binascii.unhexlify("a4014a00ef0000")) #probe with reset command
  reply = binascii.hexlify(ser.read(size=256))
  if reply == "a4016f20ea":#found ANT+ stick
    serial_port=p
    ant_stick_found = True
  else: ser.close()
  if ant_stick_found == True  : break

if ant_stick_found == False:
  print "Could not find serial port"
  sys.exit
  
#try:
  #ser = serial.Serial('/dev/ttyUSB0', 19200, rtscts=True,dsrdtr=True)#set up serial communication with ANT+ dongle
#except serial.serialutil.SerialException:
  #print "Could not find serial port"
  #sys.exit

ant.calibrate(ser)#calibrate ANT+ dongle
ant.master_channel_config(ser)#calibrate ANT+ channels

resistance=1#set initial resistance level
speed,cadence,power,heart_rate=(0,)*4#initialise values

#initialise TACX USB device
byte_ints = [2,0,0,0] # will not read cadence until initialisation byte is sent
byte_str = "".join(chr(n) for n in byte_ints)
dev.write(0x02,byte_str)
time.sleep(1)

grade = 0
accumulated_power = 0
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
    last_measured_time = time.time() * 1000
    ####################GET DATA FROM TRAINER####################
    data = dev.read(0x82,64) #get data from device
    #print data
    
    #get values reported by trainer
    fs = int(data[33])<<8 | int(data[32])
    speed = round(fs/2.8054/100,1)#speed kph
    force = fromcomp((data[39]<<8)|data[38],16)
    try:#try to identify force value from list of possible resistance values
      force = T1932_calibration.possfov.index(force)+1
      power = T1932_calibration.calcpower(speed,force)
    except ValueError:
      pass # do nothing if force value from trainer not recognised
    cadence = int(data[44])
    heart_rate = int(data[12])
    print speed,cadence,power,heart_rate
    
    ####################SEND DATA TO TRAINER####################
    #send resistance data to trainer
    level = list(sorted(T1932_calibration.reslist))[-1] #set resistance level to hardest as default
    for g in sorted(T1932_calibration.reslist):
      if g >= grade*2:#find resistance value immediately above grade set by zwift (Zwift ANT+ grade is half that displayed on screen)
        level = g
        break
    r6=int(T1932_calibration.reslist[level])>>8 & 0xff #byte6
    r5=int(T1932_calibration.reslist[level]) & 0xff #byte 5
    #echo pedal cadence back to trainer
    if len(data) > 40:
      pedecho = data[42]
    else:
      pedecho = 0
    byte_ints = [0x01, 0x08, 0x01, 0x00, r5, r6, pedecho, 0x00 ,0x02, 0x52, 0x10, 0x04]
    
    byte_str = "".join(chr(n) for n in byte_ints)
    dev.write(0x02,byte_str)#send data to device
    
    ####################BROADCAST AND RECEIVE ANT+ data####################
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
      #print "FE DATA",newdata
    
    else:#send specific trainer data
      if eventcounter >= 256:
        eventcounter = 0
      newdata = '{0}{1}{2}'.format(data[:15], hex(eventcounter)[2:].zfill(2), data[17:]) # increment event count
      if cadence >= 254:
        cadence=253
      newdata = '{0}{1}{2}'.format(newdata[:18], hex(cadence)[2:].zfill(2), newdata[20:])#instant cadence
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
      #print "TRAINER DATA",newdata
      
    reply = send([newdata], ser)
    if "grade" in reply:
      grade = reply['grade']
    ####################wait ####################
    
    #add wait so we only send every 250ms
    time_to_process_loop = time.time() * 1000 - last_measured_time
    sleep_time = 0.25 - (time_to_process_loop)/1000
    if sleep_time < 0: sleep_time = 0
    time.sleep(sleep_time)
    eventcounter += 1
except KeyboardInterrupt: # interrupt power data sending with ctrl c, make sure script continues to reset device
    pass

ant.send(["a4 01 4a 00 ef 00 00"],ser)#reset ANT+ dongle

ser.close()