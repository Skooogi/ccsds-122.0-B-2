from threading import Thread
import crc8
import numpy as np
import os,sys
import serial
import serial.tools.list_ports
import time

def get_port():
    ports = list(serial.tools.list_ports.comports())
    ser = serial;
    for p in ports:
        if "EDBG" in p[1]:
            return serial.Serial(p[0])
    raise IOError("Board not plugged in!")

def print_banner():
    print(r"""
 ____     ____     ____    ____    ____       
/\  _`\  /\  _`\  /\  _`\ /\  _`\ /\  _`\     
\ \ \/\_\\ \ \/\_\\ \,\L\_\ \ \/\ \ \,\L\_\   
 \ \ \/_/_\ \ \/_/_\/_\__ \\ \ \ \ \/_\__ \   
  \ \ \L\ \\ \ \L\ \ /\ \L\ \ \ \_\ \/\ \L\ \ 
   \ \____/ \ \____/ \ `\____\ \____/\ `\____\
    \/___/   \/___/   \/_____/\/___/  \/_____/
               _      ___       ___           
             /' \   /'___`\   /'___`\         
            /\_, \ /\_\ /\ \ /\_\ /\ \        
            \/_/\ \\/_/// /__\/_/// /__       
               \ \ \  // /_\ \  // /_\ \      
                \ \_\/\______/ /\______/      
                 \/_/\/_____/  \/_____/       
                                              
                                              
          """)

def print_help():
    print(r"""
          clear - clears the screen and prints the banner
          test  - test sending a packet""")

def read_packet(ser):

    retry = 0

    while True:
        byte_data = b''
        time.sleep(0.01)

        while ser.inWaiting() > 0:
            byte_data += ser.read(1)

        if(byte_data == b''):
            ser.write((255).to_bytes(1, 'big'))
            continue

        while(len(byte_data) < byte_data[0]):
            byte_data += ser.read(1)

        packet_length = byte_data[0]
        crc = byte_data[packet_length-1]
        check = crc8.calculate(byte_data[1:packet_length-1])
        
        if(check - crc):
            print("[I]>> requesting resend")
            ser.write((255).to_bytes(1, 'big'))

        else:
            ser.write((1).to_bytes(1, 'big'))
            return byte_data

        retry += 1
        if(retry == 10):
            ser.write((255).to_bytes(1, 'big'))
            print("[I]>> packet transmission failed!")
            return


def send_packet(ser, data):

    crc = crc8.calculate(data)
    
    #Resend the packet max 10 times
    for i in range(10):
        #length + 2 = packet length + data + checksum
        ser.write((len(data)+2).to_bytes(1, 'big'))
        ser.write(data)
        ser.write((crc).to_bytes(1, 'big'))
        time.sleep(0.01)
        out = int.from_bytes(ser.read(1))
        if(out == 1):
            return 0;

        else:
            print(f'[I]>> resending packet')

    return 255;

def time_execution(ser, input_str):
    start = time.time()
    send_packet(ser, input_str.encode());
    while(ser.inWaiting() == 0):
        time.sleep(0.001)
    stop = time.time()
    byte_data = read_packet(ser);
    return (stop-start)*1000

if __name__ == "__main__":
    ser = get_port()
    ser.baudrate = 115200
    ser.timeout = 1
    print_banner()
    print("Connected: yes, port: "+ ser.port + ", baud: " + str(ser.baudrate))

    while 1 :

        input_str = input("[I]>> ")
        if input_str == '':
            continue

        if input_str == 'exit' or input_str == 'q':
            ser.close()
            exit()

        elif input_str == 'clear':
            os.system('clear')
            print_banner()
            print("Connected: yes, port: "+ ser.port + ", baud: " + str(ser.baudrate))

        elif input_str == 'test':
            elapsed = time_execution(ser, input_str)
            print(elapsed, "ms")

        elif input_str == 'file':

            filename = input("[I]>> Input file:")
            width, height, bitdepth = input("[I]>> width, height, bitdepth:").split()

            file = open(filename, "rb")
            data_bytes = file.read()
            
            file_data = "file".encode()
            file_data += len(data_bytes).to_bytes(4, 'little')
            file_data += ((len(data_bytes)+63)//64).to_bytes(4, 'little')
            file_data += int(width).to_bytes(4, 'little')
            file_data += int(height).to_bytes(4, 'little')
            file_data += int(bitdepth).to_bytes(4, 'little')
            send_packet(ser, file_data)
            time.sleep(0.1)
            byte_data = read_packet(ser);

            if(byte_data[1] == 0):
                print("[O]>> Not enough space for file of size", len(data_bytes))
                continue

            print("[I]>> Sending file")
            num_packets = (len(data_bytes)+63)//64
            for i in range(0, len(data_bytes), 64):
                out = send_packet(ser, data_bytes[i:i+64])
                if(out > 0):
                    print(f'[O]>> failed at packet {i//64 + 1}')
                print(f'[O]>> received packet {i//64 + 1}/{num_packets}', end='\r')
            print()

        elif input_str == 'download':

            filename = input("[I]>> Output file:")

            send_packet(ser, input_str.encode())
            time.sleep(0.1)
            byte_data = read_packet(ser);

            if(byte_data[10] == 0):
                print("[O]>> No file to download")
                continue
            print("[O]>> Sending file")

            data_length = int.from_bytes(byte_data[1:5], 'little')
            num_packets = int.from_bytes(byte_data[5:9], 'little')

            fp = open(filename, "wb")

            for i in range(0, len(data_bytes), 64):
                byte_data = read_packet(ser);
                if(byte_data == None):
                    print(f'[O]>> failed at packet {i//64 + 1}')
                print(f'[O]>> received packet {i//64 + 1}/{num_packets}', end='\r')
                fp.write(byte_data[1:-1])

            fp.close()
            print()

        elif input_str == 'compress':
            start = time.time()
            send_packet(ser, input_str.encode());
            while(ser.inWaiting() == 0):
                time.sleep(0.001)
            stop = time.time()
            byte_data = read_packet(ser);
            print(f'[O]>> {(stop-start)*1000} ms')

        elif input_str == "cpu_speed":
            avg = 0
            n = 10
            for i in range(n):
                elapsed = time_execution(ser, input_str)
                print(f'[O]>> {i+1}/{n} took {elapsed} ms')
                avg += elapsed

            avg /= n
            print(f"[O]>> Average time over {n} samples is {avg} ms")
            num = int(0xFFFFFF)
            print(f'{num/(avg/1000)} instructions/s')

        elif input_str == "write_speed":
            avg = 0
            n = 100
            
            #Ignore first because malloc takes time
            time_execution(ser,input_str)

            for i in range(n):
                elapsed = time_execution(ser, input_str)
                print(f'[O]>> {i+1}/{n} took {elapsed} ms')
                avg += elapsed
            avg /= n

            print(f"[O]>> Average time over {n} samples is {avg} ms")
            num_bytes = 87000*4
            speed = num_bytes/(avg/1000) #B/s
            speed /= 1000000 #MB/s
            print(f'[O]>> Write speed of {speed} MB/s')

        elif input_str == "read_speed":
            avg = 0
            n = 100
            for i in range(n):
                elapsed = time_execution(ser, input_str)
                print(f'[O]>> {i+1}/{n} took {elapsed} ms')
                avg += elapsed
            avg /= n

            print(f"[O]>> Average time over {n} samples is {avg} ms")
            num_bytes = 87000*4
            speed = num_bytes/(avg/1000) #B/s
            speed /= 1000000 #MB/s
            print(f'[O]>> Read speed of {speed} MB/s')

        else: 
            send_packet(ser, input_str.encode());
