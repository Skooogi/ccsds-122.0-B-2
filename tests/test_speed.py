from common_test_functions import *
import time
import matplotlib.pyplot as plt

def mean_execution_time(cmd, n):

    current_time = 0
    for i in range(n):
        start = time.time()
        os.system(cmd)
        end = time.time()
        print(f'{i+1}/{n}', end='\r')
        current_time += end-start
    print()
    return (current_time/n)*1000

@pytest.mark.parametrize('seed', range(1))
@pytest.mark.parametrize('bitdepth', range(12, 13))
def test_speed(bitdepth, seed):
    
    versions = [
        "./previous_versions/v0/ccsds_v0.bin",
        "./previous_versions/v1/ccsds_v1.bin",
        "./previous_versions/v2/ccsds_v2.bin",
    ]
    
    ccsds = "../build/ccsds.bin"

    file_type = np.uint32
    
    data = generate_random_image(1024, 1024, bitdepth, seed).astype(file_type)
    height = data.shape[0]
    width = data.shape[1]

    file_raw = "test.raw" 
    file_compressed = "output.cmp"

    data.tofile(file_raw)
    
    cmd = f' {file_raw} {file_compressed} {width} {height} {bitdepth}'

    n = 10
    speeds = [mean_execution_time(x+cmd, n) for x in versions]
    speeds.append(mean_execution_time(ccsds+cmd, 10)+1)

    for i in range(len(speeds)-1):
        print(f'v{i+1} {(1-speeds[i+1]/speeds[i])*100:.2f} % improvement from v{i}')
        assert speeds[i] > speeds[i+1], f'Version{i+1} is slower than previous'
    print(f'Total {(1-speeds[-1]/speeds[0])*100:.2f} % improvement from v0')

    plt.plot(speeds, '-bo')
    plt.axhline(speeds[0]/3)

    plt.ylabel("Time (ms)")
    plt.ylim([0,300])

    plt.xlabel("Version")
    plt.xticks(range(len(speeds)))

    plt.title("Compression speed")
    plt.grid()
    plt.show()


if __name__=='__main__':
    test_speed(12,0)


