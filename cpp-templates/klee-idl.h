#pragma once

#include <stdint.h>
#include <stddef.h>
#include <initializer_list>
#include <iterator>
#include <type_traits>

#define KLEE_INPUT
#define OP_CHECK_OVERFLOW

#include "base-constants.h"
#include "base-structs.h"
#include "base-functions.h"
#include "base-operators.h"
#include "klee-functions.h"
#include "klee-operators.h"
