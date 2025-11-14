import numpy as np
import os, sys
import pytest

@pytest.fixture(scope="session", autouse=True)
def compile():
    cmd = f'(cd ..; make clean && make -j3)'
    os.system(cmd)

def generate_random_image(width, height, bitdepth, seed):
    np.random.seed(seed)

    assert width >= 32 and width % 8 == 0, "Width must be a multiple of eight"
    assert height >= 32 and height % 8 == 0, "Height must be a multiple of eight"
    assert bitdepth > 0 and bitdepth <= 25, "Bitdepth must be between 1 and 26"

    data = np.random.rand(height,width)*2**bitdepth
    return data.astype(np.uint32)
