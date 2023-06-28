This project contains contains an implementation of image compression as 
described in the ccsds_122_B-2 standard as well as some tests for the 
discrete wavelet transform and run length encoder.

Usage:
python3 ccsds_122.py filein fileout #Takes a bmp image as input and outputs a *.cmp file and out_1.bmp
python3 pytest #Runs tests for the discrete wavelet transform and run length encoder
python3 rccsds_122.py #Uncompresses output.cmp in same folder to a file named out_2.bmp and measures MSE and PSNR compared to out_1.bmp

Third party:
numpy
Image PIL
struct

pytest

