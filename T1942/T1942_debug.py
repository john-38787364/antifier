import usb.core, time, binascii
from datetime import datetime

dev = usb.core.find(idVendor=0x3561, idProduct=0x1942)
dev.set_configuration()

#initialise TACX USB device
byte_ints = [2,0,0,0] # will not read cadence until initialisation byte is sent
byte_str = "".join(chr(n) for n in byte_ints)
if not simulatetrainer:
 dev.write(0x02,byte_str)
time.sleep(1)
data=""
try:
  while True:
    last_measured_time = time.time() * 1000
    data = dev.read(0x82,64) #get data from device
    print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"TRAINER RX DATA",binascii.hexlify(data)
    r6=int(4876)>>8 & 0xff #byte6
    r5=int(4876) & 0xff #byte 5
    #echo pedal cadence back to trainer
    if len(data) > 40:
      pedecho = data[42]
    else:
      pedecho = 0
    byte_ints = [0x01, 0x08, 0x01, 0x00, r5, r6, pedecho, 0x00 ,0x02, 0x52, 0x10, 0x04]
    print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"TRAINER TX DATA",byte_ints
    byte_str = "".join(chr(n) for n in byte_ints)
    dev.write(0x02,byte_str)#send data to device
    
    #add wait so we only send every 250ms
    time_to_process_loop = time.time() * 1000 - last_measured_time
    sleep_time = 0.25 - (time_to_process_loop)/1000
    if sleep_time < 0: sleep_time = 0
    time.sleep(sleep_time)
except KeyboardInterrupt: # interrupt power data sending with ctrl c, make sure script continues to reset device
  pass