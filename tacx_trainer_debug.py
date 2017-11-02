import usb.core, time, binascii, sys
from datetime import datetime
import os
import trainer

dev_trainer = trainer.get_trainer()
if not dev_trainer:
  print "Could not find trainer"
  sys.exit()
trainer.initialise_trainer(dev_trainer)

eventcounter=1
reslist=[-3251, -1625, 0, 1625, 3251, 4876, 6502, 8127, 9752, 11378, 13003]#1625/1626 increments
log_file=open('tacx_trainer_debug.log','w') 
log_file.write(hex(trainer.trainer_type)+"\n")
resistance= -3278
print "KEEP CYCLING AT A MODERATE PACE UNTIL BLACK WINDOW DISAPPEARS"
try:
  while True:
    last_measured_time = time.time() * 1000
    data = dev_trainer.read(0x82,64) #get data from device
    log_file.write(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]+" TRAINER RX DATA "+binascii.hexlify(data)+"\n")

    #increment resistance
    resistance += 5 #add 5 on each time
    nearest_validated_resistance = min(reslist, key=lambda x:abs(x-resistance))
    if nearest_validated_resistance - resistance < 5 and nearest_validated_resistance - resistance > 0:
      resistance = nearest_validated_resistance
    if resistance >= 13004:
      break
    
    if resistance < 0: r = (256*256) + resistance
    else: r= resistance
    r6=int(r)>>8 & 0xff #byte6
    r5=int(r) & 0xff #byte 5
    #echo pedal cadence back to trainer
    if len(data) > 40:
      pedecho = data[42]
    else:
      pedecho = 0
    byte_ints = [0x01, 0x08, 0x01, 0x00, r5, r6, pedecho, 0x00 ,0x02, 0x52, 0x10, 0x04]
    m=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]+" TRAINER TX DATA "+str(resistance)+' {}'.format(' '.join(hex(x)[2:].zfill(2) for x in byte_ints))
    print m
    log_file.write(m+"\n")
    byte_str = "".join(chr(n) for n in byte_ints)
    dev_trainer.write(0x02,byte_str)#send data to device
    
    #add wait so we only send every 250ms
    time_to_process_loop = time.time() * 1000 - last_measured_time
    sleep_time = 0.25 - (time_to_process_loop)/1000
    if sleep_time < 0: sleep_time = 0
    time.sleep(sleep_time)
    eventcounter += 1
except KeyboardInterrupt: # interrupt power data sending with ctrl c, make sure script continues to reset device
  pass
log_file.close()
print "COMPLETE"
