#!/bin/sh

clang=$1

print_test_result() {
    local target=$1
    local file=$2
    local pass=$(grep "PASS" $file | wc -l)
    local count=$(cat $file | wc -l)
    echo "${target}: ${pass}/${count}"
}

pushd build/qemu

make build-xqci-asm-tests
make build-xqccmp-asm-tests
make build-smrnmi-asm-tests

make build-xqci-c-tests CC=$clang
make build-xqccmp-c-tests CC=$clang
make build-smrnmi-c-tests CC=$clang

make run-xqci-asm-tests > out-xqci-asm-tests
make run-xqccmp-asm-tests > out-xqccmp-asm-tests
make run-smrnmi-asm-tests > out-smrnmi-asm-tests

make run-xqci-c-tests > out-xqci-c-tests
make run-xqccmp-c-tests > out-xqccmp-c-tests
make run-smrnmi-c-tests > out-smrnmi-c-tests

print_test_result "xqci asm" out-xqci-asm-tests
print_test_result "xqci c" out-xqci-c-tests
print_test_result "xqccmp asm" out-xqccmp-asm-tests
print_test_result "xqccmp c" out-xqccmp-c-tests
print_test_result "smrnmi asm" out-smrnmi-asm-tests
print_test_result "smrnmi c" out-smrnmi-c-tests

popd
