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
1: [ 4.5000,-20],#i.e. for resistance level 1, power = speed x 4.5 + (-20) watts = 20kph  x 4.5 - 20 = 70 watts
2: [ 5.3666,-29],
3: [ 6.0666,-30],
4: [ 6.8666,-35],
5: [ 7.7666,-46],
6: [ 8.5666,-51],
7: [ 9.0130,-57],#AFTER 40 MINS
8: [10.1333,-61],
9: [10.8333,-63],
10:[11.8000,-77],
11:[12.5333,-80],
12:[13.3000,-82],
13:[14.1333,-91],
14:[14.9333,-96]
}

#######################################DO NOT ALTER BELOW THIS LINE#######################################
def calcpower(speed, resistance):
    power=round(factors[resistance][0]*speed + factors[resistance][1])
    if power<0: power=0
    return power

possfov=[1039, 1299, 1559, 1819, 2078, 2338, 2598, 2858, 3118, 3378, 3767, 4027, 4287, 4677]#possible force values to be recv from device
reslist=[1900, 2030, 2150, 2300, 2400, 2550, 2700, 2900, 3070, 3200, 3350, 3460, 3600, 3750]#possible resistance value to be transmitted to device