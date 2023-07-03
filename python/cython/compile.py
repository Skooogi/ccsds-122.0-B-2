import os


def compile():
    os.system("python3 c_dwt_compile.py build_ext --inplace")


if __name__ == '__main__':
    compile()
