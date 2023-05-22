import numpy as np
import math

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

def encode_ac_magnitudes(blocks, bitAC, q):

    N = int(abs(math.log(1 + bitAC,2)) + 1)
    print("Coding AC coefficients with:\n[bitAC]\t", bitAC, "\n[q]\t", q, "\n[N]\t", N)

    if(N == 1):
        quantized[0] = int(blocks[0])
        temp = int(quantized[0])
        j = 1

        print("AC")
        for i in range(1,len(blocks)):
            if(j == 7):
                print(temp, end='')
                j = 1
                temp = 0
            temp <<= 1
            j += 1
            quantized[i] = int(blocks[i])
            temp |= int(quantized[i])
             
            #print(int(quantized[i]),end='')  
        print()

    else:

        last = abs(blocks[0][63])
        diffs = np.zeros(len(blocks))
        diffs[0] = last
        
        #Rest of the AC coefficients
        for i in range(1, len(blocks)):
            sigma = abs(blocks[i][63]) - last
            theta = min(last, pow(2,N) - 1 - last)
            last = abs(blocks[i][63])
            res = 0

            if sigma >= 0 and sigma <= theta:
                res = 2*sigma
            elif sigma < 0 and sigma >= -theta:
                res = 2*abs(sigma)-1
            else:
                res = theta + abs(sigma)

            diffs[i] = int(res)

        for i in range(0, int(len(blocks)/16)):

            #print("[",int(res),"]",sep='', end='')
            gaggle_sum = 0
            for j in range(16):
                gaggle_sum += diffs[i*16 + j]

            J = 16
            if(i == 0):
                J -= 1

            k = select_coding(gaggle_sum, J, N)
            print("[k=",k,"]",sep='',end='')
            if(i == 0):
                print("[",int(diffs[0]),"]",sep='',end='')

            for j in range(0,16):
                z = int(diffs[i*16+j]/pow(2,k))
                print("0"*z,end='')
                print('1',end='')
            print("|",end='')
            for j in range(16):
                print(int(diffs[i*16+j]) & ((1 << k) - 1),end='')
            print()


        print()

def encode_dc_magnitudes(blocks, bitDC, q):

    #DC coding
    N = max(bitDC - q + 1, 1)
    quantized = np.zeros(len(blocks))

    print("Coding DC coefficients with:\n[bitDC]\t", bitDC, "\n[q]\t", q, "\n[N]\t", N)
    
    if(N == 1):
        quantized[0] = int(blocks[0] / pow(2,q))
        temp = int(quantized[0])
        j = 1

        print("DC")
        for i in range(1,len(blocks)):
            if(j == 7):
                print(temp, end='')
                j = 1
                temp = 0
            temp <<= 1
            j += 1
            quantized[i] = int(blocks[i] / pow(2,q))
            temp |= int(quantized[i])
        print()
        
    else:
        #First DC coefficient is uncoded
        last = int(blocks[0] / pow(2, q))
        print("DC uncoded",int(blocks[0] / pow(2, q)))

        #Rest of the DC coefficients
        for i in range(1, len(blocks)):
            sigma = int(blocks[i] / pow(2, q)) - last
            theta = min(last + pow(2, (N-1)), pow(2, (N-1)) - 1 - last)
            res = 0

            if sigma >= 0 and sigma <= theta:
                res = 2*sigma
            elif sigma < 0 and sigma >= -theta:
                res = -2*sigma-1
            else:
                res = theta + abs(sigma)

            last = int(blocks[i] / pow(2, q))

                
def encode_dc_values(blocks, q, b):
    print("STAGE 0 DC")
    if(b < q and q > 3):
        for i in range(0, len(blocks)):
            print((int(blocks[i][0]) >> b) & 1, end='')
        print()


def subband_lim(j, b):

    if(j == 1 or j == 22 or j == 43) and b <= 3:
        return True
    elif((2 <= j <= 5) or (23 <= j <= 26) or (44 <= j <= 47)) and b <= 2:
        return True
    elif((6 <= j <= 21) or (27 <= j <= 42) or (48 <= j <= 63)) and b <= 2:
        return True
    else:
        return False


def encode_ac_values(status, words, blocks, q, b):


    for i in range(len(status)):
        #STAGE 0
        for j in range(len(status[0])):
            if(subband_lim(j, b)):
                status[i][j] = -1
            elif(abs(blocks[i][j+1]) < pow(2,b)):
                status[i][j] = 0
            elif(pow(2,q) <= abs(blocks[i][j+1]) < pow(2,b+1)):
                status[i][j] = 1
            elif(abs(blocks[i][j+1]) >= pow(2,b+1)):
                status[i][j] = 2

        #STAGE 1
        word = ""
        if(status[i][1] == 1):
            word += str((int(blocks[i][1]) >> b) & 1)
        if(status[i][22] == 1):
            word += str((int(blocks[i][22]) >> b) & 1)
        if(status[i][43] == 1):
            word += str((int(blocks[i][43]) >> b) & 1)

        if(word != ""):
            if(int(word) == 0):
                if(words[i][0] != "1"):
                    words[i][0] = str(int(max(status[i][1], status[i][22], status[i][43])))
                    print(int(words[i][0]),end='') 
            else:
                print(int(word),end='')
    print()


















