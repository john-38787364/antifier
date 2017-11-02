import pickle,sys
import numpy as np
from scipy.optimize import curve_fit

def fit_func(x, a, b):
      return a*x + b

m="#grade:multiplier,additional\n"
calibration = pickle.load(open('calibration.pickle.jt','rb'))#res,speed,power
for res in range(0,14):
  x=[]
  y=[]
  for val in calibration:
    #if val[0] == 6:
    #  print "%s,%s" % (val[1],val[2])
    if val[0] == res:
      #print res,val[1],val[2]
      x.append(val[1])
      y.append(val[2])
      
  npx = np.array(x)
  npy = np.array(y)
    
  try:
    params = curve_fit(fit_func, npx, npy)
  except:
    pass
  [a, b] = params[0]

  m+="%s:%s,%s\n" % (res-3,a,b)

print m
