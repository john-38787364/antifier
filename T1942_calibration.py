# grade passed by zwift will be converted to Tacx resistance value specified by key immediately above it 
grade_resistance = [
-3,     #up to grade -3% will cause trainer to exert resistance level 1
-2,     #from grade >-3% to <=-2% will cause trainer to exert resistance level 2
-1,     #from grade >-2% to <=-1% will cause trainer to exert resistance level 3 etc.
0,
1,
2,
3,
4,
5,
6,
7,
8,
9,
10
]

#resistance level:[multiplier, additional power]
#You may alter the multiplier and additional power values for each resistance level to more closely match your personal setup
factors={
0: [ 4.5000,-20],#i.e. for resistance level 1, power = speed x 4.5 + (-20) watts = 20kph  x 4.5 - 20 = 70 watts
1: [ 5.3666,-29],
2: [ 6.0666,-30],
3: [ 6.8666,-35],
4: [ 7.7666,-46],
5: [ 8.5666,-51],
6: [ 9.0130,-57],#AFTER 40 MINS
7: [10.1333,-61],
8: [10.8333,-63],
9:[11.8000,-77],
10:[12.5333,-80],
11:[13.3000,-82],
12:[14.1333,-91],
13:[14.9333,-96]
}

#######################################DO NOT ALTER BELOW THIS LINE#######################################
  
def send(dev_trainer, resistance_level, data):
  global reslist
  r6=int(reslist[resistance_level])>>8 & 0xff #byte6
  r5=int(reslist[resistance_level]) & 0xff #byte 5
  #echo pedal cadence back to trainer
  if len(data) > 40:
    pedecho = data[42]
  else:
    pedecho = 0
  byte_ints = [0x01, 0x08, 0x01, 0x00, r5, r6, pedecho, 0x00 ,0x02, 0x52, 0x10, 0x04]
  byte_str = "".join(chr(n) for n in byte_ints)
  dev_trainer.write(0x02,byte_str)#send data to device

possfov=[0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000]#possible force values to be recv from device
reslist=[0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000]#possible resistance value to be transmitted to device
