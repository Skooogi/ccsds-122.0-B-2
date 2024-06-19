import os, sys
sys.path.append(os.path.abspath('../python/cython'))
sys.path.append(os.path.abspath('../python'))
from common_testing import *
from pathlib import Path
import ccsds_122 as comp
import file_io
import rccsds_122 as decomp
import numpy as np

def test_images(check_python=0):

    file_out = "output.cmp"

    root_folder = "../res/opic"
    bmp_files = list(Path(root_folder).rglob("*.[bB][mM][pP]"))
    raw_files = list(Path(root_folder).rglob("*.[rR][aA][wW]"))

    raw_images = []
    
    #Match metadata from bmp to raw file
    for i in range(len(raw_files)):
        filename = os.path.basename(str(raw_files[i]))[:-4]
        bmp_file = next((str(s) for s in bmp_files if filename in str(s)), None)
        #metadata = (os.system(f'identify {bmp_file}'))
        metadata = os.popen(f'identify {bmp_file}').read()[:-1].split(' ')

        width = int(metadata[2].split('x')[0])
        height = int(metadata[2].split('x')[1])
        bitdepth = int(metadata[4].split('-')[0])

        raw_images.append([str(raw_files[i]), width, height, bitdepth*2])

    with open("results.csv", "w") as res_file:

        print("Compression ratio per category", file=res_file)
        print("Filename, Category, width, height, bitdepth, compression ratio", file=res_file)

        for i,file in enumerate(raw_images):
            
            print('Testing image ' + file[0])
            print("C:")
            file_out = file[0][:-3]+'cmp'
            os.system(f'time ../build/ccsds.bin {file[0]} {file_out} {file[1]} {file[2]} {file[3]}')
            file_compressed = os.path.getsize(file_out)
            file_size = file[1]*file[2]*file[3] // 8
            ratio = file_compressed/file_size 
            if(ratio > 0.8):
                print(f'ratio: {bcolors.FAIL}{ratio:.3f}{bcolors.ENDC}')
            elif(ratio > 0.4):
                print(f'ratio: {bcolors.WARNING}{ratio:.3f}{bcolors.ENDC}')
            else:
                print(f'ratio: {bcolors.OKGREEN}{ratio:.3f}{bcolors.ENDC}')

            path = file[0].split('/')
            print(path[-1], path[2], file[1], file[2], file[3], ratio, sep=',', file=res_file)

            if(check_python):
                print("Python:")
                comp.compress(bmp_images[i])
                file_compressed = os.path.getsize(file_out)
                file_size = file[1]*file[2]*file[3] // 8
                ratio = file_compressed/file_size 
                if(ratio > 0.8):
                    print(f'ratio: {bcolors.FAIL}{ratio:.3f}{bcolors.ENDC}')
                elif(ratio > 0.4):
                    print(f'ratio: {bcolors.WARNING}{ratio:.3f}{bcolors.ENDC}')
                else:
                    print(f'ratio: {bcolors.OKGREEN}{ratio:.3f}{bcolors.ENDC}')
                print("*"*20)

        #os.system(f'rm {file_out}')

if __name__ == '__main__':
    check_python = 0
    test_images(check_python)
