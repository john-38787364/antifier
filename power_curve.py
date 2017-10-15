#calibrate as power sensor
a4 03 42 00 00 00 e5 00 00 #42 assign channel
a4 05 51 00 00 00 0b 00 fb 00 00 #51 set channel id, 0b device=power sensor
a4 02 45 00 39 da 00 00 #45 channel freq
a4 03 43 00 f6 1f 0d 00 00 #43 msg period
a4 02 71 00 00 d7 00 00 #71 Set Proximity Search chann number 0 search threshold 0
a4 02 63 00 0a cf 00 00 #63 low priority search channel number 0 timeout 0
a4 02 44 00 02 e0 00 00 #44 Host Command/Response 
a4 01 4b 00 ee 00 00 #4b ANT_OpenChannel message ID channel = 0 D00001229_Fitness_Modules_ANT+_Application_Note_Rev_3.0.pdf

a4 02 4d 00 51 ba 00 00 #51 product info #3969 (every 30s)

a4 09 4f 00 01 aa ff ff ff ff ff ff 49 00 00 #general calibration request

a4 02 4d 00 51 ba 00 00 #4918

receives
a4 09 4e 00 11 ec 98 00 7a 26 21 10 eb #11 
a4 09 4e 00 10 ec ff 00 be 4e 00 00 10 #10 power page
