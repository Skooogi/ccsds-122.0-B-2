import numpy as np
import math
import matplotlib.pyplot as plt
import bitstream
import encodeDC

def family(blocks, block_i, data, r, c, index):

    #Children C_i
    blocks[block_i][index+1] = data[2*r][2*c]
    blocks[block_i][index+2] = data[2*r][2*c+1]
    blocks[block_i][index+3] = data[2*r+1][2*c]
    blocks[block_i][index+4] = data[2*r+1][2*c+1]

    #Grandchildren H_i0
    blocks[block_i][index+5] = data[4*r][4*c]
    blocks[block_i][index+6] = data[4*r][4*c+1]
    blocks[block_i][index+7] = data[4*r+1][4*c]
    blocks[block_i][index+8] = data[4*r+1][4*c+1]

    #Grandchildren H_i1
    blocks[block_i][index+9] = data[4*r][4*c+2]
    blocks[block_i][index+10] = data[4*r][4*c+3]
    blocks[block_i][index+11] = data[4*r+1][4*c+2]
    blocks[block_i][index+12] = data[4*r+1][4*c+3]

    #Grandchildren H_i2
    blocks[block_i][index+13] = data[4*r+2][4*c]
    blocks[block_i][index+14] = data[4*r+2][4*c+1]
    blocks[block_i][index+15] = data[4*r+3][4*c]
    blocks[block_i][index+16] = data[4*r+3][4*c+1]

    #Grandchildren H_i3
    blocks[block_i][index+17] = data[4*r+2][4*c+2]
    blocks[block_i][index+18] = data[4*r+2][4*c+3]
    blocks[block_i][index+19] = data[4*r+3][4*c+2]
    blocks[block_i][index+20] = data[4*r+3][4*c+3]


def fill_blocks(blocks, data, width, height):

    #Fill blocks with the families making up the DC coefficients
    for r in range(height):
        for c in range(width):
            block_i = r*width+c

            #DC coefficient
            blocks[block_i][0] = data[r][c]

            #Parents for F0 F1 F2
            blocks[block_i][1] = data[r][2*c] * 8
            blocks[block_i][2] = data[2*r][c] * 8
            blocks[block_i][3] = data[2*r][2*c] * 4
            
            #Families
            family(blocks, block_i, data, r, 2*c, 3)
            family(blocks, block_i, data, 2*r, c, 23)
            family(blocks, block_i, data, 2*r, 2*c, 43)

#As in 4-3
def select_coding(delta, J, N):

    if(64*delta > 23*J*pow(2, N)):
        return -1
    elif(207*J > 128*delta):
        return 0
    elif(J*pow(2,N+5) <= 128*delta + 49*J):
        return N-2
    else:
        k = 1
        while(J*pow(2,k+7) <= 128*delta + 49):
            k += 1
        return k


#Width and Height for the LL3 band
def encode(data, width, height):

    """
    Divide data as follows
    
    [-----------------------coefficients-----------------------] | WIDTH * HEIGHT DWT transformed pixel values
    [ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ] | b = block = 1 DC and 63 AC coefficients
    [    g   ][    g   ][    g   ][    g   ][    g   ][    g   ] | g = gaggle = 16 blocks
    [              s             ][              s             ] | s = segment = n gaggles, 16 <= n <= 2^20


    """
    blocks = np.zeros((int(width/8)*int(height/8), 64))
    print(blocks.shape)
    fill_blocks(blocks, data, int(width/8), int(height/8))

    #Currently partitioned as a single segment
    gaggle_size = 16
    mod = blocks.shape[0] % gaggle_size


    #1. Determine AC and DC bitdepths for the segement

    #Minimum possible values
    bitDC = 1
    bitAC = 0

    for i in range(len(blocks)):
        #DC value
        dc = blocks[i][0]
        print(dc)
        if dc < 0:
            bitDC = max(int(1 + math.log(abs(dc))), bitDC)
        else:
            bitDC = max(int(1 + math.log(dc+1,2)), bitDC)

        #Iterate through AC values
        for j in range(1, 64):
            temp = int(math.log(abs(blocks[i][j])+1,2))
            bitAC = max(temp, bitAC)

    #TODO segment header

    #Determine q (4.3.1.2)
    q = 0
    if(bitDC <= 3):
        q = 0
    elif(bitDC - (1 + bitAC/2) <= 1 and bitDC > 3):
        q = bitDC - 3
    elif(bitDC - (1 + bitAC/2) > 10 and bitDC > 3):
        q = bitDC - 10
    else:
        q = 1 + int(bitAC/2)

    q = max(q, 8)

    #code DC coefficients

    return
    for segment in range(0, blocks.shape[0] - mod, segment_size):



        #Determine q part 4.3.1.2

        #DC coding
        N = max(bitDC - q, 1)
        
        if(N == 1):
            for i in range(0, segment_size):
              print("DC",int(blocks[segment + i][0] / pow(2,q)))  
            
        else:
            #First DC coefficient is uncoded
            last = blocks[segment][0] / pow(2,q)
            blocks[segment][0] /= pow(2,q)
            print(int(blocks[segment][0] / pow(2, q)))
            bitstream.out(int(blocks[segment][0] / pow(2, q)))


            #Rest of the DC coefficients
            for i in range(1, segment_size):
                sigma = blocks[segment+i][0] / pow(2,q) - last
                theta = min(last + pow(2,(N-1)), pow(2,(N-1)) - 1 - last)
                last = blocks[i][0]
                res = 0

                if sigma >= 0 and sigma <= theta:
                    res = 2*sigma
                elif sigma < 0 and sigma >= -theta:
                    res = 2*abs(sigma)-1
                else:
                    res = theta + abs(sigma)

                quantized[i] = int(res)
                print("DC",int(res))

        #AC coding
        N = int(math.log(bitAC + 1, 2))

        if(N == 1):
            for i in range(0, segment_size):
                for j in range(1, 64):
                    print("AC",int(blocks[segment + i][j] / pow(2,q)))  

        else:

            quantized = np.zeros(63)

            #Rest of the AC coefficients
            for i in range(0, segment_size):
                last = blocks[segment + i][1] / pow(2,q)
                for j in range(2, 64):
                    sigma = blocks[segment+i][j] / pow(2,q) - last
                    theta = min(last, pow(2,N) - 1 - last)
                    last = blocks[i][0]
                    res = 0

                    if sigma >= 0 and sigma <= theta:
                        res = 2*sigma
                    elif sigma < 0 and sigma >= -theta:
                        res = 2*abs(sigma)-1
                    else:
                        res = theta + abs(sigma)

                    quantized[i] = int(res)
                    print("AC",int(res))

        print("DC", bitDC, "AC", bitAC, "N", N, "Q", q)
