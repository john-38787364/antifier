import binascii, re

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

def send(stringl, dev_ant):#send message string to dongle
  rtn = {}
  for string in stringl:
    i=0
    send=""
    while i<len(string):
      send = send + binascii.unhexlify(string[i:i+2])
      i=i+3
    print ">>",binascii.hexlify(send)#log data to console
    #dev_ant.write(send
    try:
      dev_ant.write(0x01,send)
    except Exception, e:
      print "USB WRITE ERROR", str(e)
    #dev_ant.timeout = 0.1
    #read_val = binascii.hexlify(dev_ant.read(size=256))
    read_val = binascii.hexlify(dev_ant.read(0x81,64))
    print "<<",read_val
    
    read_val_list = read_val.split("a4")#break reply into list of messsages
    for rv in read_val_list:
      if len(rv)>6:
        if (int(rv[:2],16)+3)*2 == len(rv):
          if calc_checksum("a4"+rv) == rv[-2:]:#valid message
            #a4094f0033ffffffff964ffff7 is gradient message
            if rv[6:8]=="33":
              rtn = {'grade' : int(rv[18:20]+rv[16:18],16) * 0.01 - 200} #7% in zwift = 3.5% grade in ANT+
  return rtn


def calibrate(dev_ant):
  stringl=[
  "a4 02 4d 00 54 bf 00 00",#request max channels
  "a4 01 4a 00 ef 00 00",#reset system
  "a4 02 4d 00 3e d5 00 00",#request ant version
  "a4 09 46 00 b9 a5 21 fb bd 72 c3 45 64 00 00",#set network key b9 a5 21 fb bd 72 c3 45
  ]
  send(stringl,dev_ant)
  
def master_channel_config(dev_ant):
  stringl=[
  "a4 03 42 00 10 00 f5 00 00",#[42] assign channel, [00] 0, [10] type 10 bidirectional transmit, [00] network number 0, [f5] extended assignment
  "a4 05 51 00 01 00 11 05 e5 00 00",#[51] set channel ID, [00] number 0 (wildcard search) , [01] device number 1, [00] pairing request (off), [11] device type fec, [05] transmission type  (page 18 and 66 Protocols) 00000101 - 01= independent channel, 1=global data pages used
  "a4 02 45 00 39 da 00 00",#[45] set channel freq, [00] transmit channel on network #0, [39] freq 2400 + 57 x 1 Mhz= 2457 Mhz
  "a4 03 43 00 f6 1f 0d 00 00",#[43] set messaging period, [00] channel #0, [f61f] = 32768/8182(f61f) = 4Hz (The channel messaging period in seconds * 32768. Maximum messaging period is ~2 seconds. )
  "a4 02 60 00 03 c5 00 00",#[60] set transmit power, [00] channel #0, [03] 0 dBm
  "a4 01 4b 00 ee 00 00",#open channel #0
  "a4 09 4e 00 50 ff ff 01 0f 00 85 83 bb 00 00",#broadcast manufacturer's data
  ]
  send(stringl,dev_ant)

def second_channel_config(dev_ant):
  stringl=[
  "a4 03 42 01 10 00 f4 00 00",#[42] assign channel, [00] 0, [10] type 10 bidirectional transmit, [00] network number 0, [f4] normal assignment
  "a4 05 51 01 02 00 78 01 8a 00 00",#[51] set channel ID, [01] channel 1 , [02] device number 1, [00] pairing request (off), [78] device type HR sensor, [01] transmission type  (page 18 and 66 Protocols) 00000101 - 01= independent channel, 1=global data pages used
  "a4 02 45 01 39 db 00 00",#[45] set channel freq, [00] transmit channel on network #0, [39] freq 2400 + 57 x 1 Mhz= 2457 Mhz
  "a4 03 43 01 86 1f 7c 00 00",#[43] set messaging period, [00] channel #0, [f61f] = 32768/8182(f61f) = 4Hz (The channel messaging period in seconds * 32768. Maximum messaging period is ~2 seconds. )
  "a4 02 60 01 03 c4 00 00",#[60] set transmit power, [00] channel #0, [03] 0 dBm
  "a4 01 4b 01 ef 00 00",#open channel #0
  "a4 09 4e 01 82 0f 01 00 00 00 00 48 26 00 00",#broadcast manufacturer's data
  ]
  send(stringl,dev_ant)

