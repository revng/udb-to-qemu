#pragma once

XReg &XRegSet::operator[](size_t i) {
    return regs[i];
}
