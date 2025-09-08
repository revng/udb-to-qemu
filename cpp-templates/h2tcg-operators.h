#pragma once

XReg XRegSet::operator[](size_t i) {
    return xqci_get_gpr(i);
}
