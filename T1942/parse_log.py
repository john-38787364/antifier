import binascii
reslist=[-3251, -1625, 0, 1625, 3251, 4876, 6502, 8127, 9752, 11378, 13003]#1625/1626 increments
def fromcomp(val,bits):
  if val>>(bits-1) == 1:
    return 0-(val^(2**bits-1))-1
  else: return val

filepath = 'out.log'  
with open(filepath) as fp:  
  line = fp.readline()
  while line:
    if line[32:34]=="TX":
      tline = line[-37:]
      res = int(tline[15:17]+tline[12:14],16)
      if (res & ( 1 << 15 ))!=0: res = res - ( 1 << 16)
    elif line[32:34]=="RX":
      lines = line[40:]
      #print " ".join("%s:%s" % (1+i/2, lines[i:i+2]) for i in range(0, len(lines)-2, 2))
      
      if len(lines)==98:
	#print lines
        #33,34 speed little endian
        speed = int(lines[66:68]+lines[64:66],16)
        if (speed & ( 1 << 15 ))!=0: speed = speed - ( 1 << 16)
	speed = speed/2.8054/100
		
	
        #Bytes 39, 40 is the force on the wheel to compute the power 
        force = int(lines[78:80]+lines[76:78],16)
        if (force & ( 1 << 15 ))!=0: force = force - ( 1 << 16)
        #print "force",force
        
        #byte 13 heart rate?
        heartrate = int(lines[24:26],16)
        
        #cadnce 45,46
        cadence = int(lines[90:92]+lines[88:90],16)
        #print "cadence", cadence
        
        #if res in reslist: print res, force
        if speed >10:
          print "%s,%s" % (res, force)#, speed, heartrate
    line = fp.readline()