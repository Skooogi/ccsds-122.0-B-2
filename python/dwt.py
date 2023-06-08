import numpy as np

def intify(x):
    if(x < 0 and x != int(x)):
        return int(x-1)
    else:
        return int(x)

def forward_DWT(data, width):

    taps = 7

    #Horizontal
    cache = np.copy(data)
    
    #highpass
    #D0
    highpass_d0 = np.array([9/16,0,1/2,0,-1/16])
    data[int(width/2)] = cache[1] - intify(sum(cache[:5] * highpass_d0) + 1/2)

    #D1 - DN-3
    highpass = np.array([-1/16, 0, 9/16, 0, 9/16, 0, -1/16])
    for j in range(1, int(width/2) - 2):
        data[int(width/2)+j] = cache[2*j] - intify(sum(cache[2*j-2:2*j-2+taps] * highpass) + 1/2)

    #DN-2
    highpass_dn_2 = np.array([-1/16,0,9/16,0,1/2])
    data[int(width)-2] = cache[-3] - intify(sum(cache[-6:-1] * highpass_dn_2) + 1/2)

    #DN-1
    highpass_dn_1 = np.array([-1/8,0,9/8,0])
    data[int(width)-1] = cache[-1] - intify(sum(cache[-5:-1] * highpass_dn_1) + 1/2)

    #lowpass
    #C0
    data[0] = cache[0] - intify(-data[int(width/2)]/2 + 1/2)

    #C1 - CN-1
    for j in range(1, int(width/2)):
        data[j] = cache[2*j] - intify(-sum(data[j-1:j])/4 + 1/2)

def backward_DWT(data, width):

    taps = 7

    #IDWT
    cache = np.copy(data[:int(width)])

    #Even values
    #X0
    data[0] = cache[0] + intify(-cache[int(width/2)]/2 + 1/2)
    #X2 - XN-1
    for j in range(1, int(width/2)):
        data[2*j] = cache[j] + intify(-sum(cache[j-1:j])/4 + 1/2)

    #Odd values
    #X1
    odd_x1 = np.array([9/16,0,1/2,0,-1/16])
    data[1] = cache[int(width/2)] + intify(sum(data[:5] * odd_x1) + 1/2)

    odd_pass = np.array([-1/16, 0, 9/16, 0, 9/16, 0, -1/16])
    #X3 - XN-3
    for j in range(1, int(width/2) - 2):
        data[2*j+1] = cache[int(width/2) + j] + intify(sum(data[2*j-2:2*j-2+taps] * odd_pass) + 1/2)
    
    #XN-3
    odd_xn_3 = np.array([-1/16,0,9/16,0,1/2])
    data[int(width)-3] = cache[int(width) - 2] + intify(sum(data[-6:-1] * odd_xn_3) + 1/2)

    #XN-1
    data[int(width)-1] = cache[int(width) - 1] + intify(9/8*data[int(width)-2]-1/8*data[int(width)-4] + 1/2)

def discrete_wavelet_transform_2D(data, width, height, levels = 3, backward = False) -> None:

    if(backward):
        for level in reversed(range(levels)):

            sub_width = int(width/pow(2,level))
            sub_height = int(height/pow(2,level))

            #Vertical
            for i in range(int(sub_width)):
                backward_DWT(data[:int(sub_height), i], sub_height)

            #Horizontal
            for i in range(int(sub_height)):
                backward_DWT(data[i, :int(sub_width)], sub_width)
        return

    for level in range(levels):

        sub_width = int(width/pow(2,level))
        sub_height = int(height/pow(2,level))

        #Horizontal
        for i in range(int(sub_height)):
            forward_DWT(data[i, :int(sub_width)], sub_width)

        #Vertical
        for i in range(int(sub_width)):
            forward_DWT(data[:int(sub_height), i], sub_height)
