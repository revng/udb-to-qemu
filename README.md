## usage

```
$ python yaml-to-cpp.py inst -o out.cpp
$ clang14 out.cpp -O0 -Xclang -disable-O0-optnone -S -emit-llvm
$ helper-to-tcg out.ll
```
