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

def read_message(ser):
    time.sleep(0.1)
    out = ''
    while ser.inWaiting() > 0:
        out += ser.read(1).decode("utf-8")
    if out != '':
        print("[O]>> " + out)
    return out

if __name__ == "__main__":
    ser = get_port()
    ser.baudrate = 115200
    ser.timeout = 1
    print_banner()
    print("Connected: yes, port: "+ ser.port + ", baud: " + str(ser.baudrate))

    while 1 :
        # get keyboard input
        # Python 3 users
        input_str = input("[I]>> ")
        if input_str == 'exit' or input_str == 'q':
            ser.close()
            exit()

        elif input_str == 'clear':
            os.system('clear')
            print_banner()
            print("Connected: yes, port: "+ ser.port + ", baud: " + str(ser.baudrate))

        else:
            # send the character to the device
            ser.write((input_str+'\n').encode())
            # let's wait one second before reading output (let's give device time to answer)
            out = read_message(ser);

            if out == 'Downloading file!':
                data = np.array(range(128), dtype=np.uint8)
                crc = crc8.calculate(data)

                data_bytes = (len(data).to_bytes(1, 'big'))
                data_bytes += data.tobytes()
                data_bytes += (crc).to_bytes(1, 'big')
                ser.write(data_bytes)
                out = read_message(ser)
