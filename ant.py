import binascii, re

def add_little_endian(val1,val2):#add two strings together in little endian fashion e.g. "1b 01"
  intval = (int(val1[3:],16) * 256 + int(val1[0:2],16)) + (int(val2[3:],16) * 256 + int(val2[0:2],16))
  if intval>= (256 * 256): intval = 0 #rolls over at 65535
  return hex(intval % 256)[2:].zfill(2) +" "+hex((intval - (intval % 256))/256)[2:].zfill(2)

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

def send(stringl,ser):#send message string to dongle
  global reply_message, no_bytes_to_find
  for string in stringl:
    i=0
    send=""
    while i<len(string):
      send = send + binascii.unhexlify(string[i:i+2])
      i=i+3
    print ">>",binascii.hexlify(send)#log data to console
    ser.write(send)

    ser.timeout = 0.1
    read_val = binascii.hexlify(ser.read(size=256))
    #print "read off wire: ",read_val
    
    byte_index = 0
    while byte_index < len(read_val)/2:#iterate along reply to find sync byte
      if no_bytes_to_find > 0:#if bytes still to find
        reply_message += read_val[byte_index*2:2]#add on bytes from previous incomplete message
        no_bytes_to_find = no_bytes_to_find - 1
        if no_bytes_to_find == 0: 
          reply_complete = True
      elif read_val[byte_index*2:2]=="a4":#new reply message
        no_bytes_in_message = int(read_val[byte_index*2+2:byte_index*2+4],16) + 4 #find reported length of message byte , add sync+page+checksum
        if len(read_val[byte_index*2:]) - no_bytes_in_message*2 >= 0: #entire message in reply
          reply_message = read_val[byte_index*2:byte_index*2 + no_bytes_in_message*2]
          reply_complete = True
          byte_index = byte_index*2 + no_bytes_in_message*2
        else:#does not have entire message - get what's available
          reply_message = read_val[b*2:]#get rest of reply to end 
          no_bytes_to_find = no_bytes_in_message - len(read_val[b*2:]) / 2#work out number of bytes still to find
      if reply_complete:
        print "<<",reply_message
        print "-"
      byte_index += 1

def calibrate(ser):
  stringl=[
  "a4 02 4d 00 54 bf 00 00",#request max channels
  "a4 01 4a 00 ef 00 00",#reset system
  "a4 02 4d 00 3e d5 00 00",#request ant version
  "a4 09 46 00 b9 a5 21 fb bd 72 c3 45 64 00 00",#set network key b9 a5 21 fb bd 72 c3 45
  ]
  send(stringl,ser)

def master_channel_config(ser):
  stringl=[
  "a4 03 42 00 10 00 f5 00 00",#[42] assign channel, [00] 0, [10] type 10 bidirectional transmit, [00] network number 0, [f5] extended assignment
  "a4 05 51 00 01 00 0b 05 ff 00 00",#[51] set channel ID, [00] number 0 (wildcard search) , [01] device number 1, [00] pairing request (off), [0b] device type Bike Power meter, [05] transmission type (page 18 and 66 Protocols) 00000101 - 01= independent channel, 1=global data pages used
  "a4 02 45 00 39 da 00 00",#[45] set channel freq, [00] transmit channel on network #0, [39] freq 2400 + 57 x 1 Mhz= 2457 Mhz
  "a4 03 43 00 f6 1f 0d 00 00",#[43] set messaging period, [00] channel #0, [f61f] = 32768/8182 = 4Hz (The channel messaging period in seconds * 32768. Maximum messaging period is ~2 seconds. )
  "a4 02 60 00 03 c5 00 00",#[60] set transmit power, [00] channel #0, [03] 0 dBm
  "a4 01 4b 00 ee 00 00",#open channel #0
  "a4 09 4e 00 50 ff ff 01 0f 00 85 83 bb 00 00",#broadcast manufacturer's data
  ]
  send(stringl,ser)

reply_message = ""
no_bytes_to_find = 0
