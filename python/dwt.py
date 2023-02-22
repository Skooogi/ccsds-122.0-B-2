import numpy as np

def DWT(data, width):

    taps = 7

    #Horizontal
    cache = np.copy(data)
    
    #highpass
    #D0
    highpass_d0 = np.array([-9/16,1,-1/2,0,1/16])
    data[int(width/2)] = sum(cache[:5] * highpass_d0) - 1/2

    #D1 - DN-3
    highpass = np.array([1/16, 0, -9/16, 1, -9/16, 0, 1/16])
    for j in range(1, int(width/2) - 2):
        data[int(width/2)+j] = sum(cache[2*j-2:2*j-2+taps] * highpass) - 1/2

    #DN-2
    highpass_dn_2 = np.array([1/16,0,-9/16,1,-1/2])
    data[int(width)-2] = sum(cache[-6:-1] * highpass_dn_2) - 1/2

    #DN-1
    highpass_dn_1 = np.array([1/8,0,-9/8,1])
    data[int(width)-1] = sum(cache[-5:-1] * highpass_dn_1) - 1/2

    #lowpass
    #C0
    data[0] = cache[0] + data[int(width/2)]/2 - 1/2

    #C1 - CN-1
    for j in range(1, int(width/2)):
        data[j] = cache[2*j] + sum(data[j-1:j])/4 - 1/2

def IDWT(data, width):

    taps = 7

    #IDWT
    cache = np.copy(data[:int(width)])

    #Even values
    #X0
    data[0] = cache[0] - cache[int(width/2)]/2 + 1/2
    #X2 - XN-1
    for j in range(1, int(width/2)):
        data[2*j] = cache[j] - sum(cache[j-1:j])/4 + 1/2

    #Odd values
    #X1
    odd_x1 = np.array([9/16,0,1/2,0,-1/16])
    data[1] = sum(data[:5] * odd_x1) + 1/2 + cache[int(width/2)]

    odd_pass = np.array([-1/16, 0, 9/16, 0, 9/16, 0, -1/16])
    #X3 - XN-3
    for j in range(1, int(width/2) - 2):
        data[2*j+1] = sum(data[2*j-2:2*j-2+taps] * odd_pass) + 1/2 + cache[int(width/2) + j]
    
    #XN-3
    odd_xn_3 = np.array([-1/16,0,9/16,0,1/2])
    data[int(width)-3] = sum(data[-6:-1] * odd_xn_3) + 1/2 + cache[int(width) - 2]

    #XN-1
    data[int(width)-1] = cache[int(width) - 1] + 1/2 + 9/8*data[int(width)-2]-1/8*data[int(width)-4]


def forward_DWT(data, width, height):

    #Horizontal
    for i in range(int(height)):
        DWT(data[i, :int(width)], width)

    #Vertical
    for i in range(int(width)):
        DWT(data[:int(height), i], height)

        
def backward_DWT(data, width, height):

    #Vertical
    for i in range(int(width)):
        IDWT(data[:int(height), i], height)

    #Horizontal
    for i in range(int(height)):
        IDWT(data[i, :int(width)], width)

