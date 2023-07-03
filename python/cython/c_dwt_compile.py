from setuptools import setup, Extension
from Cython.Build import cythonize


AIS_REPO_PATH = "../../core"

include_paths = [
    AIS_REPO_PATH+"/src/"
]

source_paths = [
    AIS_REPO_PATH+"/src/discrete_wavelet_transform.c"
]

sourcefiles= ["c_dwt.pyx"]
sourcefiles.extend(source_paths)

compile_args = ["-O3", "-fPIC", "-march=native"]
for icd in include_paths:
	compile_args.append( "-I"+icd )

extensions = [Extension("c_dwt", sourcefiles, extra_compile_args=compile_args)]

setup(
    name='C_DWT',
    ext_modules=cythonize(extensions, compiler_directives={"language_level": "3"}),
    zip_safe=False,
)


