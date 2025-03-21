from pickle import LIST
import numpy as np
import matplotlib.pyplot as plt
import glob
import os
from pathlib import Path

input=r"D:\Dropbox\Projects\CometInterceptor\images\EMcampaignOct9to11_2022\2022_10_10-00_55_35*.oraw"#2022_10_10-00_55_35.oraw"

class OPICImage:
    def __init__(self):


        self.defvals=set(dir(self))|set(['defvals','pixels']) 

    def __str__(self):
        printset=set(dir(self))-self.defvals 
        #print(printset)
        return "\n".join([n+":"+str(getattr(self,n)) for n in printset])

    def Load(name):
        
        fin=open(name,"rb")
        data=fin.read(10000000)
        fin.close()

        image=OPICImage()

        image.name=name

        data = np.frombuffer(data,dtype=np.uint8).astype(np.uint16)

        image.packet_length=np.frombuffer(data[0:8:2].copy(order="C"),np.uint32).item()

        image.frame_id=data[5*2:6*2:2][0]
 
        image.frame_tag=np.frombuffer(data[6*2:14*2:2].copy(order="C"),np.uint64).item()

        image.integration_time=data[14*2]+data[15*2]*256+data[16*2]*256*256

        image.fot_len=20
        master_clock_MHz=6.4

        image.integration_time_ms=(image.integration_time+0.43*image.fot_len)*129*0.001/master_clock_MHz
 
        image.temperature=data[17*2]+data[18*2]*256

        image.adc_gain=data[19*2]
 
        image.window_width=data[20*2]+(data[21*2]%8)*256+1

        image.window_height=data[22*2]+(data[23*2]%8)*256+1

        image.size=(image.window_width)*(image.window_height)

        image.offset_x=data[24*2]+(data[25*2]%8)*256

        image.offset_y=data[26*2]+(data[27*2]%8)*256

        image.footer_size=data[28*2]

        image.pixels=np.uint16(data[::2][29:29+image.size]*256+data[1::2][29:29+image.size]-data[1::2][29:29+image.size]%8).reshape((image.window_height,image.window_width))
        return image

    def SavePNG(self,name):
        #cv2.imwrite(name, image.pixels)
        with open(name+"_meta.txt","wt") as fout:
            fout.write(str(self))

if __name__ == '__main__':

    root_folder = "../res/opic/oraw"
    oraws = list(Path(root_folder).rglob("*.[oO][rR][aA][wW]"))

    outdir="../res/opic/raw"

    for imname in oraws:
        image=OPICImage.Load(imname)
        
        print(image.pixels)
        filename = os.path.basename(imname)
        #if(image.window_width == 2048 and image.window_height == 2048):
            #image.pixels = image.pixels - noise
        image.pixels.tofile("../res/opic/raw/"+filename[:-4]+"raw")
