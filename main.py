#coding: utf-8
import re
import os
import subprocess
import sys

def echo(string):
    sys.stdout.write(str(string));
    sys.stdout.write('\n')
    sys.stdout.flush()

def error_echo(string):
    sys.stderr.write(str(string));
    sys.stderr.write('\n')
    sys.stderr.flush()

class Code(object):
    def __init__(self, code, result):
        self._code = code
        self._result = result

    def compile(self):
        open('test.cpp', 'w').write(self.code)
        subprocess.check_call([
            '/usr/local/gcc-head/bin/g++',
            '-I/usr/local/gcc-head/include/c++/4.9.0',
            '-L/usr/local/gcc-head/lib64',
            '-Wl,-rpath,/usr/local/gcc-head/lib64',
            '-std=c++11',
            '-otest.exe',
            '-lpthread',
            'test.cpp'])
        #subprocess.check_call(
        #["/usr/local/llvm-3.3/bin/clang++",
        # "-otest.exe",
        # "-std=c++11",
        # "-stdlib=libc++",
        # "-I/usr/local/libcxx-3.3/include/c++/v1",
        # "-L/usr/local/libcxx-3.3/lib",
        # "-Wl,-rpath,/usr/local/libcxx-3.3/lib",
        # "-nostdinc++",
        # "-lpthread",
        # "test.cpp"])

    def run(self):
        return subprocess.check_output(['./test.exe'])

    @property
    def code(self):
        return self._code

    @property
    def result(self):
        return self._result

FENCED_BLOCK_RE = re.compile(
    r'(?P<fence>^(?:~{3,}|`{3,}))[ ]*(\{?\.?(?P<lang>[a-zA-Z0-9_+-]*)\}?)?[ ]*\n(?P<code>.*?)(?<=\n)(?P=fence)[ ]*$',
    re.MULTILINE|re.DOTALL
)

# コードブロックがサンプルコードであるかどうかを判断する
def is_sample_code(code, lang):
    # 最初の5行以内に #include を含んでたらサンプルコードだと判断する
    first_lines = code.split('\n')[:5]
    return any(line.find('#include') >= 0 for line in first_lines)

# コードブロックと出力を探して返す
def get_codes(md):
    codes = []

    class NextFencedBlock(object):

        def __init__(self, md):
            self.md = md

        def __call__(self):
            m = FENCED_BLOCK_RE.search(self.md)
            if m:
                self.md = self.md[:m.start()] + self.md[m.end():]
            return m

    next_fenced_block = NextFencedBlock(md)

    while True:
        m = next_fenced_block()
        if not m:
            break

        code = m.group('code')
        lang = m.group('lang')
        if not is_sample_code(code, lang):
            continue

        m = next_fenced_block()
        if not m:
            result = None
        else:
            result = m.group('code')

        codes.append(Code(code, result))

    return codes

# 全mdファイル列挙
def all_contents():
    for path,dirs,files in os.walk("site"):
        for file in files:
            if (file[-3:] == '.md'):
                yield os.path.join(path, file)

def skip_list():
    return open('ignore_list').read().strip().split('\n')

def main():
    skips = set(skip_list())
    for path in all_contents():
        if path in skips:
            continue

        echo('#' * 32)
        echo('checking {}'.format(path))

        md = open(path).read()
        codes = get_codes(md)
        for code in codes:
            try:
                code.compile()
            except Exception, e:
                echo('COMPILE ERROR: {}'.format(e))
                echo('---- compiled code ----')
                echo(code.code)
                echo('---- expected result ----')
                echo(code.result)
                continue

            try:
                result = code.run()
            except Exception, e:
                echo('RUNTIME ERROR: {}'.format(e))
                echo('---- compiled code ----')
                echo(code.code)
                echo('---- expected result ----')
                echo(code.result)
                continue

            expected = code.result.strip() if code.result is not None else None
            actual = result.strip();
            if expected != actual:
                echo('---- compiled code ----')
                echo(code.code)
                echo('---- expected result ----')
                echo(expected)
                echo('---- actual result ----')
                echo(actual)
            else:
                echo('...OK')

if __name__ == '__main__':
    main()
