// Copyright: Huld Ltd.
// Project: EnVisS ASW (for Comet Interceptor mission)

/// @defgroup ASW_Types ASW Types
/// @brief Common data types used within software.
/// @{

#ifndef ASW_TYPES_H
#define ASW_TYPES_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/// A signed integer of 8 bits
typedef int8_t   Int8_T;

/// A signed integer of 16 bits
typedef int16_t  Int16_T;

/// A signed integer of 32 bits
typedef int32_t  Int32_T;

/// A signed integer of 64 bits
typedef int64_t  Int64_T;

/// An unsigned integer of 8 bits
typedef uint8_t  Octet_T;

/// An unsigned integer of 16 bits
typedef uint16_t Uint16_T;

/// An unsigned integer of 32 bits
typedef uint32_t Uint32_T;

/// An unsigned integer of 64 bits
typedef uint64_t Uint64_T;

/// A count of elements. This is used when a variable represents size, length,
/// number of elements, etc.
typedef size_t Size_T;

/// A count of octets. This is used to define a packet or buffer length.
typedef size_t Octet_Count_T;

/// A count of 16-bit words.
typedef size_t Word_Count_T;

/// A boolean type, which is 1 Octet long. It could be used with "true" and
/// "false" from <stdbool.h>.
typedef uint8_t Bool_T;

/// The maximum possible value of a Uint16_T variable
#define UINT_16_MAX (65535)


/// A macro that forces the compiler to ensure that a variable (or type) will be
/// 32-bit (4 byte) word aligned.
///
#ifndef DOXYGEN
#define COMPILER_WORD_ALIGNED    __attribute__((__aligned__(4)))
#endif

/// A macro that forces the compiler to ensure that a variable (or type) will be
/// 64-bit (8 byte) word aligned.
///
#ifndef DOXYGEN
#define COMPILER_64BIT_ALIGNED    __attribute__((__aligned__(8)))
#endif

// The following two definitions are used to, for the target HW, use a "section"
// attribute to place a given variable into the specified memory. The given
// sections (defined in the linker script) further use NOLOAD to ensure that
// this memory is not overwritten or cleared at start, but rather the values in
// memory when ASW starts running are the ones that are used. (For SDRAM we want
// to avoid unnecessary initialization; for configuration data the section
// already includes the appropriate values when the ASW starts running.)
//
// For the workstation version, the section attribute does not bring any
// problems - it just creates a section with the specified name and puts the
// variable there.

/// A macro used to mark variables to be allocated in the "sdram_data" section
/// by linker.
#ifndef DOXYGEN
#define ALLOCATE_IN_SDRAM  __attribute__((section(".sdram_data")))
#else
#define ALLOCATE_IN_SDRAM
#endif

/// A macro used to mark variables to be allocated in the "sdram_nocache_data"
/// section by linker.
#ifndef DOXYGEN
#define ALLOCATE_IN_SDRAM_NOCACHE  __attribute__((section(".sdram_nocache_data")))
#else
#define ALLOCATE_IN_SDRAM_NOCACHE
#endif

/// A macro used to place the config data in the "config_data" section by
/// linker.
#ifndef DOXYGEN
#define ALLOCATE_CONFIG_DATA  __attribute__((section(".config_data")))
#else
#define ALLOCATE_CONFIG_DATA
#endif

/// A macro used to mark variables to be allocated in the "dtcm" section
/// by linker.
#ifndef DOXYGEN
#define ALLOCATE_IN_DTCM __attribute((section(".dtcm_data")))
#else
#define ALLOCATE_IN_DTCM
#endif

/// A macro used to place variable with 64-bits alignment in the
/// "dtcm" section by linker.
#ifndef DOXYGEN
#define ALLOCATE_IN_DTCM_64_ALIGNED __attribute((section(".dtcm_data"), __aligned__(8)))
#else
#define ALLOCATE_IN_DTCM_64_ALIGNED
#endif

/// A macro used to place variable with 32-bits alignment in the
/// "dtcm" section by linker.
#ifndef DOXYGEN
#define ALLOCATE_IN_DTCM_32_ALIGNED __attribute((section(".dtcm_data"), __aligned__(4)))
#else
#define ALLOCATE_IN_DTCM_32_ALIGNED
#endif

/// A macro used to place the boot report data in the "boot_report_data" section
/// by linker.
#ifndef DOXYGEN
#define ALLOCATE_BOOT_REPORT_DATA __attribute((section(".boot_report_data")))
#else
#define ALLOCATE_BOOT_REPORT_DATA
#endif

/// A macro used to place variable with 64-bits alignment in the
/// "ram_nocache_data" section by linker.
#ifndef DOXYGEN
#define ALLOCATE_IN_NOCACHE_64_ALIGNED __attribute((section(".ram_nocache_data"), __aligned__(8)))
#else
#define ALLOCATE_IN_NOCACHE_64_ALIGNED
#endif

/// A macro used to place variable with 32-bits alignment in the
/// "ram_nocache_data" section by linker.
#ifndef DOXYGEN
#define ALLOCATE_IN_NOCACHE_32_ALIGNED __attribute((section(".ram_nocache_data"), __aligned__(4)))
#else
#define ALLOCATE_IN_NOCACHE_32_ALIGNED
#endif


/// A macro used to tell the compiler that the following function does not
/// return.
#ifndef DOXYGEN
#define NO_RETURN __attribute__((noreturn))
#else
#define NO_RETURN
#endif


/// A macro used to tell the compiler that the following function should not
/// contain a C code but only the Assembly. Also, the compiler does not generate
/// prologue and epilogue sequences for that function.
#ifndef DOXYGEN
#define NAKED __attribute__((naked))
#else
#define NAKED
#endif


/// A macro used to suppress compiler warnings for unused variables.
#define UNUSED(x) ((void)(x))


#endif // ASW_TYPES_H

/// @}
