import socket,time,subprocess,sys

subprocess.Popen(["python", "./backend/tacx_iflow.py","runoff"])

time.sleep(1)
s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host="localhost"
port=8169
s.connect(( host, port ))
print "Tyre pressure 100psi (unloaded), aim for 7.2s rolloff"
print "Warm up 2 mins. Cycle 30-40 for 30s then to above 40 then stop"


while 1:
    data=""
    speeds=[]
    times=[]
    revtimes=[]

    triggered=False
    running = True
    #time.sleep(1)
    while running:
        #loop every 200ms
        time.sleep(0.2)
        data=s.recv(4096)
        times.append(time.time())
        hr = int(data[36:40],16)
        speed = round(float(int(data[20:26],16))/100,1)
        cadence = int(data[32:36],16)
        resistance = int(data[26:32],16)
        power = int(data[40:48],16)
        sys.stdout.write("Speed: "+str(speed)+"   \r" )
        sys.stdout.flush()
        speeds.append(speed)
        if speed>40: triggered=True
        if speed==0 and triggered:
            break

    i=0
    revtimes=list(reversed(times))
    finishtime=revtimes[0]
    for sp in reversed(speeds):
        #print s,finishtime-revtimes[i]
        i+=1
        if sp>30: break;
        
    print "Rolloff: "+str(round(finishtime-revtimes[i-1],1))
