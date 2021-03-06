#!/usr/bin/env python

import glob
import os
import tarfile

import wget
from torch.utils.ffi import create_extension

# Download/Extract openfst
dl_path = 'third_party/openfst-1.6.3.tar.gz'
if not os.path.isfile(dl_path):
    wget.download('http://www.openfst.org/twiki/pub/FST/FstDownload/openfst-1.6.3.tar.gz',
                  out=dl_path)
tar = tarfile.open(dl_path)
tar.extractall('third_party/')
tar.close()


# Does gcc compile with this header and library?
def compile_test(header, library):
    dummy_path = os.path.join(os.path.dirname(__file__), "dummy")
    command = "bash -c \"g++ -include " + header + " -l" + library + " -x c++ - <<<'int main() {}' -o " + dummy_path \
              + " >/dev/null 2>/dev/null && rm " + dummy_path + " 2>/dev/null\""
    return os.system(command) == 0


compile_args = ['-O3', '-DNDEBUG', '-DKENLM_MAX_ORDER=6', '-std=c++11', '-fPIC', '-w']
ext_libs = ['stdc++']

if compile_test('zlib.h', 'z'):
    compile_args.append('-DHAVE_ZLIB')
    ext_libs.append('z')

if compile_test('bzlib.h', 'bz2'):
    compile_args.append('-DHAVE_BZLIB')
    ext_libs.append('bz2')

if compile_test('lzma.h', 'lzma'):
    compile_args.append('-DHAVE_XZLIB')
    ext_libs.append('lzma')

third_party_libs = ["kenlm", "openfst-1.6.3/src/include", "ThreadPool"]
compile_args.extend(['-DINCLUDE_KENLM', '-DKENLM_MAX_ORDER=6'])
lib_sources = glob.glob('third_party/kenlm/util/*.cc') + glob.glob('third_party/kenlm/lm/*.cc') + glob.glob(
    'third_party/kenlm/util/double-conversion/*.cc') + glob.glob('third_party/openfst-1.6.3/src/lib/*.cc')
lib_sources = [fn for fn in lib_sources if not (fn.endswith('main.cc') or fn.endswith('test.cc'))]

third_party_includes = ["third_party/" + lib for lib in third_party_libs]
ctc_sources = glob.glob('ctcdecode/src/*.cpp')
ctc_headers = ['ctcdecode/src/binding.h', ]

ffi = create_extension(
    name='ctcdecode._ext.ctc_decode',
    package=True,
    language='c++',
    headers=ctc_headers,
    sources=ctc_sources + lib_sources,
    include_dirs=third_party_includes,
    with_cuda=False,
    libraries=ext_libs,
    extra_compile_args=compile_args
)

if __name__ == '__main__':
    ffi.build()
