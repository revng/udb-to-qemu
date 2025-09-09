#pragma once

#include <stddef.h>

#include "base-structs.h"

XReg XRegSet::operator[](size_t i) { return xqci_get_gpr(i); }
