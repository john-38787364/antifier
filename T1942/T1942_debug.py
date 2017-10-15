import usb.core, time, binascii, sys
from datetime import datetime
import os

##scan for uninitalised 1942
deva = usb.core.find(idVendor=0x3561, idProduct=0xe6be)
try:
  deva.set_configuration()
  os.system("fxload-libusb.exe -I FortiusSWPID1942Renum.hex -t fx -vv")#load firmware
  print "Initialising trainer, please wait 5 seconds"
  time.sleep(5)
except AttributeError:#not found
  print "Uninitialised trainer not found"
  

write = True
if len(sys.argv) > 1:
  if sys.argv[1] == "simulate":
    write = False
if write:
  dev = usb.core.find(idVendor=0x3561, idProduct=0x1942)
  dev.set_configuration()

#possible resistance values to be sent
#-5% (0xf34d or -0x0cb3 or -3251)
#-2.5% (0xf9a7 or -0x659 or -1625), 
#0 (0), 
#2.5% (0x0659 or 1625), 
#5% (0x0cb3 or 3251), 
#7.5% (0x130c or 4876),
#10% (0x1966 or 6502), 
#12.5% (0x1fbf or 8127), 
#15% (0x2618 or 9752), 
#17.5% (0x2c72 or 11378) and 
#20% (0x32cb or 13003).

#speed values to receive
#0x0800 : 5km/h,  int 8
#0x0c00 : 10km/h, int 12
#0x1300 : 15km/h, int 19
#0x1600 : 20km/h, int 22
#0x1c00 : 25 km/h int 30
#0x2200 : 30 km/h int 34

#initialise TACX USB device
byte_ints = [2,0,0,0] # will not read cadence until initialisation byte is sent
byte_str = "".join(chr(n) for n in byte_ints)
if write:
  dev.write(0x02,byte_str)
time.sleep(1)
data=""

eventcounter=1
reslist=[-3251, -1625, 0, 1625, 3251, 4876, 6502, 8127, 9752, 11378, 13003]#1625/1626 increments
resindex = 0

resistance= -3278
try:
  while True:
    last_measured_time = time.time() * 1000
    if write:
      data = dev.read(0x82,64) #get data from device
      print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"TRAINER RX DATA",binascii.hexlify(data)

    #increment resistance
    resistance += 5 #add 27 on each time
    nearest_validated_resistance = min(reslist, key=lambda x:abs(x-resistance))
    if nearest_validated_resistance - resistance < 5 and nearest_validated_resistance - resistance > 0:
      resistance = nearest_validated_resistance
    if resistance == 13004:
      break

    r6=int(resistance)>>8 & 0xff #byte6
    r5=int(resistance) & 0xff #byte 5
    #echo pedal cadence back to trainer
    if len(data) > 40:
      pedecho = data[42]
    else:
      pedecho = 0
    byte_ints = [0x01, 0x08, 0x01, 0x00, r5, r6, pedecho, 0x00 ,0x02, 0x52, 0x10, 0x04]
    print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"TRAINER TX DATA",resistance,'{}'.format(' '.join(hex(x)[2:].zfill(2) for x in byte_ints))
    byte_str = "".join(chr(n) for n in byte_ints)
    if write:
      dev.write(0x02,byte_str)#send data to device
    
    #add wait so we only send every 250ms
    time_to_process_loop = time.time() * 1000 - last_measured_time
    sleep_time = 0.25 - (time_to_process_loop)/1000
    if sleep_time < 0: sleep_time = 0
    time.sleep(sleep_time)
    eventcounter += 1
except KeyboardInterrupt: # interrupt power data sending with ctrl c, make sure script continues to reset device
  pass
