import numpy as np

def scale(data, width, height):

    #Scaling HL_1 LH_1
    for j in range(0, int(height/2)):
        for i in range(int(width/2), width):
            data[j][i] = int(data[j][i] * 2) 
            data[j + int(height/2)][i - int(width/2)] = int(data[j + int(height/2)][i - int(width/2)] * 2)

    #Scaling HH_2
    for j in range(int(height/4), int(height/2)):
        for i in range(int(width/4), int(width/2)):
            data[j][i] *= 2 

    #Scaling HL_2 LH_2
    for j in range(0, int(height/4)):
        for i in range(int(width/4), int(width/2)):
            data[j][i] = int(data[j][i] * 4) 
            data[j + int(height/4)][i - int(width/4)] = int(data[j + int(height/4)][i - int(width/4)] * 4)

    #Scaling HH_3
    for j in range(int(height/8), int(height/4)):
        for i in range(int(width/8), int(width/4)):
            data[j][i] = int(data[j][i] * 4) 

    #LL_3 HL_3
    for j in range(0, int(height/8)):
        for i in range(0, int(width/4)):
            data[j][i] = int(data[j][i] * 8) 
    #LH_3
    for j in range(int(height/8), int(height/4)):
        for i in range(0, int(width/8)):
            data[j][i] = int(data[j][i] * 8) 
    return data

def rescale(data, width, height):

    #Scaling HL_1 LH_1
    for j in range(0, int(height/2)):
        for i in range(int(width/2), width):
            data[j][i] = int(data[j][i] / 2) 
            data[j + int(height/2)][i - int(width/2)] = int(data[j + int(height/2)][i - int(width/2)] / 2)

    #Scaling HH_2
    for j in range(int(height/4), int(height/2)):
        for i in range(int(width/4), int(width/2)):
            data[j][i] /= 2 

    #Scaling HL_2 LH_2
    for j in range(0, int(height/4)):
        for i in range(int(width/4), int(width/2)):
            data[j][i] = int(data[j][i] / 4) 
            data[j + int(height/4)][i - int(width/4)] = int(data[j + int(height/4)][i - int(width/4)] / 4)

    #Scaling HH_3
    for j in range(int(height/8), int(height/4)):
        for i in range(int(width/8), int(width/4)):
            data[j][i] = int(data[j][i] / 4) 

    #LL_3 HL_3
    for j in range(0, int(height/8)):
        for i in range(0, int(width/4)):
            data[j][i] = int(data[j][i] / 8) 
    #LH_3
    for j in range(int(height/8), int(height/4)):
        for i in range(0, int(width/8)):
            data[j][i] = int(data[j][i] / 8) 
    return data
