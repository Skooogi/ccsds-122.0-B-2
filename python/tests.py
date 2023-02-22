import numpy as np
import math

def MSE(a, b):

    a_height, a_width = np.shape(a)
    #b_height, b_width = np.size(b)
    n = a_height * a_width
    
    error = 0

    for i in range(a_height):
        for j in range(a_width):
            temp = b[i,j] - a[i,j] 
            temp = temp * temp
            error = error + temp

    error = error / n
    return error

def PSNR(a, b):
    mse = MSE(a,b) 
    print("MSE:",mse)
    psnr = 10*math.log((255*255)/mse, 10)
    print("PSNR:", psnr)
    return psnr
