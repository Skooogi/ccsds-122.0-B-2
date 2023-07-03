import os
import json
import numpy as np

# benchmark latest version
if __name__ == '__main__':
    bin = "../build/ccsds.bin"

    cases = [
        ["raw/test_image_noise_32.raw", 32],
        ["raw/test_image_noise_64.raw", 64],
        ["raw/test_image_noise_128.raw", 128],
        ["raw/test_image_noise_256.raw", 256],
        ["raw/test_image_noise_512.raw", 512],
        ["raw/test_image_noise_1k.raw", 1024],
        ["raw/test_image_noise_2k.raw", 2048],
        ["raw/test_image_noise_4k.raw", 4096]
    ]

    for case in cases:
        print("testing: "+case[0])
        os.system(f'perf stat -j -d -o {case[1]}.json ./{bin} {case[0]} {case[1]}')

    results = []

    for case in cases:
        with open(f'{case[1]}.json') as file:
            lines = [line.rstrip() for line in file]
            time = float(json.loads(lines[2])["counter-value"])/1000
            cycles = int(float(json.loads(lines[6])["counter-value"]))
            ghz = float(json.loads(lines[6])["metric-value"])
            instr = int(float(json.loads(lines[7])["counter-value"]))
            branches = int(float(json.loads(lines[8])["counter-value"]))
            branch_misses = int(float(json.loads(lines[9])["counter-value"]))

            results.append([time, instr/cycles, branch_misses/branches*100, instr/cycles*ghz])

            #print(f'{time:.10f} s, {instr/cycles:.2f} ins/cyc, {(branch_misses/branches)*100:.2f} %')
        os.remove(f'{case[1]}.json')

    with open("v_latest.res", "wb") as file:
        np.array(results).tofile(file)
    with open("v_latest.txt", "wt") as file:
        file.write(f'{results[-1][0]:.10f} s\n')
        file.write(f'{results[-1][1]:.2f} instr/cycle\n')
        file.write(f'{results[-1][2]:.2f} % branch misses\n')
        file.write(f'{results[-1][3]:.1f} billion operations/s\n')
