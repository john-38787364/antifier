#based on T1932 protocol
import usb.core
import time
import T1932_calibration
import ant
import sys
import serial, binascii
import struct

def fromcomp(val,bits):
  if val>>(bits-1) == 1:
    return 0-(val^(2**bits-1))-1
  else: return val

dev = usb.core.find(idVendor=0x3561, idProduct=0x1932) #find iflow device
dev.set_configuration() #set active configuration

ser = serial.Serial('/dev/ttyUSB0', 19200, rtscts=True,dsrdtr=True)#set up serial communication with ANT+ dongle

ant.calibrate(ser)#calibrate ANT+ dongle
ant.master_channel_config(ser)#calibrate ANT+ channels

read_val = binascii.hexlify(ser.read(size=256))
print "read off wire: ",read_val


res=1#set initial resistance level
speed,cadence,power,heart_rate=(0,)*4#initialise values

#initialise TACX USB device
byte_ints = [2,0,0,0] # will not read cadence until initialisation byte is sent
byte_str = "".join(chr(n) for n in byte_ints)
dev.write(0x02,byte_str)
time.sleep(1)

ant_broadcast_count=0 #initialise ANT counter
accumulated_power = "00 00"#initialise ANT+ accumulated power counter
pwrdata = "a4 09 4e 00 10 00 ff 5a 00 00 1b 01 4c 00 00" #[10] Data page number: Standard - Power Only, #[00] Update event count, [FF] Pedal power (not used) #[5A] Instantaneous cadence (not used), [00][00] Accumulated power in watts, 1 watt increments, [1B][01] Instantaneous power
trqdata = "a4 09 4e 00 13 19 47 54 47 54 ff ff e9 00 00" #initialise torque data

try:
  while True:
    last_measured_time = time.time() * 1000
    ####################GET DATA FROM TRAINER####################
    data=dev.read(0x82,64) #get data from device
    #print data
    
    #get values reported by trainer
    fs=int(data[33])<<8 | int(data[32])
    speed=round(fs/2.8054/100,1)#speed kph
    force=fromcomp((data[39]<<8)|data[38],16)
    try:#try to identify force value from list of possible resistance values
      force=T1932_calibration.possfov.index(force)+1
      power=T1932_calibration.calcpower(speed,force)
    except ValueError:
      pass # do nothing if force value from trainer not recognised
    cadence=int(data[44])
    heart_rate=int(data[12])
    print speed,cadence,power,heart_rate
    
    ####################GET DATA FROM ANT+ dongle####################
    read_val = binascii.hexlify(ser.read(size=256))
    print "read",read_val
    
    ####################SEND DATA TO TRAINER####################
    #send resistance data to trainer
    r6=int(T1932_calibration.reslist[res])>>8 & 0xff #byte6
    r5=int(T1932_calibration.reslist[res]) & 0xff #byte 5
    #echo pedal cadence back to trainer
    if len(data)>40:
      pedecho=data[42]
    else:
      pedecho=0
    byte_ints = [0x01, 0x08, 0x01, 0x00, r5, r6, pedecho, 0x00 ,0x02, 0x52, 0x10, 0x04]
    
    byte_str = "".join(chr(n) for n in byte_ints)
    dev.write(0x02,byte_str)#send data to device
    
    ####################BROADCAST ANT+ data####################
    inc=hex(int(pwrdata[15:17])+ant_broadcast_count)[2:].zfill(2)#increment counter
    
    power_hex_little_endian='{0}{1}{2}'.format(binascii.hexlify(struct.pack('<Q',power))[0:2]," ",binascii.hexlify(struct.pack('<Q',power))[2:4])
    print power_hex_little_endian
    if (ant_broadcast_count % 5 == 0):#send torque every 5 packets
      newdata = '{0}{1}{2}'.format(trqdata[:15], inc, trqdata[17:]) # increment event count
      newdata = '{0}{1}{2}'.format(newdata[:36], ant.calc_checksum(newdata), newdata[38:])#recalculate checksum
      print "TORQUE DATA",newdata
      ant.send([newdata],ser)
    else:#send power data
      newdata = '{0}{1}{2}'.format(pwrdata[:15], inc, pwrdata[17:]) # increment event count
      newdata = '{0}{1}{2}'.format(newdata[:30], power_hex_little_endian, newdata[35:])#add new power value
      newdata = '{0}{1}{2}'.format(newdata[:24], accumulated_power, newdata[29:])#recalculate accumulated power
      newdata = '{0}{1}{2}'.format(newdata[:36], ant.calc_checksum(newdata), newdata[38:])#recalculate checksum
      print "POWER DATA",newdata
      ant.send([newdata],ser)#send power data
    accumulated_power = ant.add_little_endian(accumulated_power,power_hex_little_endian)
    
    ant_broadcast_count+=1
    
    #add wait so we only send every 250ms
    time_to_process_loop = time.time() * 1000 - last_measured_time
    sleep_time = 0.25 - (time_to_process_loop)/1000
    if sleep_time < 0: sleep_time = 0
    time.sleep(sleep_time)
  
except KeyboardInterrupt: # interrupt power data sending with ctrl c, make sure script continues to reset device
    pass

ant.send(["a4 01 4a 00 ef 00 00"],ser)#reset ANT+ dongle

ser.close()