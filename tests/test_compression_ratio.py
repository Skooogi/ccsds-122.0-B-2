import os, sys
sys.path.append(os.path.abspath('../python/cython'))
sys.path.append(os.path.abspath('../python'))
import ccsds_122 as comp
import rccsds_122 as decomp
import file_io
from test_files import *

def test_images(check_python=0):

    file_out = "output.cmp"

    with open("results_compression_ratio.txt", "w") as res_file:

        for i,file in enumerate(raw_images):
            print('Testing image ' + file[0])
            print("C:")
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

        os.system(f'rm {file_out}')

if __name__ == '__main__':
    check_python = 0
    test_images(check_python)
