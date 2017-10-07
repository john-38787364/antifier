
def calcpower(speed, resistance):
    power=round(factors[resistance][0]*speed + factors[resistance][1])
    if power<0: power=0
    return power
  
# grade passed by zwift will be converted to Tacx resistance value specified by key immediately above it 
# {grade key : resistance value}
# only grade key is editable, do not edit resistance value- these are hard coded by the trainer
# reslist={-3:1900,-2:2030,-1:2150,0:2300,1:2400,2:2550,3:2700,4:2900,5.5:3070,5:3200,6:3350,6.5:3460,7:3600,8:3750}
reslist={ -1:1900, 0:2030,1:2150,1.7:2300,2.5:2400,3.2:2550,4:2700,4.7:2900,  5.4:3070,6.1:3200,6.8:3350,8:3460,9:3600,10:3750}
possfov=[    1039,   1299,  1559,    1819,    2078,    2338,  2598,    2858,      3118,    3378,    3767,  4027,  4287,   4677]#possible force values to be recv from device

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
