import numpy as np

def intify(x):
    if(x < 0 and x != int(x)):
        return int(x-1)
    else:
        return int(x)

def forward_DWT(data, width):

    x = np.copy(data)
    N = int(width/2)
    D = np.zeros(N)

    #D0
    D[0] = x[1] - intify((9/16*(x[0]+x[2]) -1/16*(x[2]+x[4]) + 1/2))

    #Dj for j=1,...,width-3
    for j in range(N-2):
        D[j] = x[2*j+1] - intify((9/16*(x[2*j]+x[2*j+2]) -1/16*(x[2*j-2]+x[2*j+4]) + 1/2))
    
    #D n-2
    D[N-2] = x[2*N-3] - intify((9/16*(x[2*N-4]+x[2*N-2]) -1/16*(x[2*N-6]+x[2*N-2]) + 1/2))
    #D n-1
    D[N-1] = x[2*N-1] - intify(9/8*x[2*N-2] -1/8*x[2*N-4] + 1/2)

    data[0] = x[0] - intify(-D[0]/2 + 1/2)
    for j in range(N):
        data[j] = x[2*j] - intify(-(D[j-1]+D[j])/4 + 1/2)
        data[N+j] = D[j]

def backward_DWT(data, width):
    
    N = int(width/2)
    C = np.copy(data)[:N]
    D = np.copy(data)[N:]

    #x0
    data[0] = C[0] + intify(-D[0]/2 + 1/2)

    #x2j j = 1,...,N-1
    for j in range(N):
        data[2*j] = C[j] + intify(-(D[j-1]+D[j])/4 + 1/2)

    #x1
    data[1] = D[0] + intify(9/16*(data[0] + data[2])-1/16*(data[2] + data[4]) + 1/2)

    #x2j+1 j = 1,...,N-3
    for j in range(N-2):
        data[2*j+1] = D[j] + intify(9/16*(data[2*j] + data[2*j+2]) - 1/16*(data[2*j-2] + data[2*j+4]) + 1/2)
    
    #x2N-3
    data[2*N-3] = D[N-2] + intify(9/16*(data[2*N-4] + data[2*N-2]) - 1/16*(data[2*N-6] + data[2*N-2]) + 1/2)

    #x2N-1
    data[2*N-1] = D[N-1] + intify(9/8*data[2*N-2] - 1/8*data[2*N-4] + 1/2)


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
                backward_DWT(data[i,:int(sub_width)], sub_width)
        return

    for level in range(levels):

        sub_width = int(width/pow(2,level))
        sub_height = int(height/pow(2,level))

        #Horizontal
        for i in range(int(sub_height)):
            forward_DWT(data[i,:int(sub_width)], sub_width)

        #Vertical
        for i in range(int(sub_width)):
            forward_DWT(data[:int(sub_height), i], sub_height)
