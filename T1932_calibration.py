
def calcpower(speed, resistance):
    power=round(factors[resistance][0]*speed + factors[resistance][1])
    if power<0: power=0
    return power
  
reslist=[1900,2030,2150,2300,2400,2550,2700,2900,3070,3200,3350,3460,3600,3750]#possible resistance values to be sent to device
possfov=[1039,1299,1559,1819,2078,2338,2598,2858,3118,3378,3767,4027,4287,4677]#possible force values to be recv from device

factors={
1:[4.5,-20],
2:[5.3666,-29],
3:[6.0666,-30],
4:[6.8666,-35],
5:[7.7666,-46],
6:[8.5666,-51],
7:[8.9238*1.01,-57],#AFTER 40 MINS
8:[10.1333,-61],
9:[10.8333,-63],
10:[11.8,-77],
11:[12.5333,-80],
12:[13.3,-82],
13:[14.1333,-91],
14:[14.93333,-96]
}
