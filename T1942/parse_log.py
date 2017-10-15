


filepath = 'Downloads/out.log'  
with open(filepath) as fp:  
  line = fp.readline()
  while line:
    if line[32:34]=="TX":
      val = int(line[52:54],16) + int(line[55:57],16)*256
      if val>32000: val = val - 256*256
      #print val
    elif line[32:34]=="RX":
      lines = line[40:]
      print " ".join(lines[i:i+2] for i in range(0, len(lines), 2))
      
      if len(lines)==98:
        #33,34 speed little endian
        #print "speed:", int(lines[64:66],16) + int(lines[66:68],16)*256
        #Bytes 39, 40 is the force on the wheel to compute the power 
        print "force:", int(lines[76:78],16) + int(lines[78:80],16)*256
    line = fp.readline()