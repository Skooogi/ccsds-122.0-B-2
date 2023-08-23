TARGET = SAMV71

OPT = -g
BUILD_DIR = build

PREFIX = arm-none-eabi-

CC = $(PREFIX)gcc
AS = $(PREFIX)gcc -x assembler-with-cpp
CP = $(PREFIX)objcopy
SZ = $(PREFIX)size
HEX = $(CP) -O ihex
BIN = $(CP) -O binary -S

CPU = -mcpu=cortex-m7
FPU = -mfpu=fpv4-sp-d16
FLOAT-ABI = -mfloat-abi=hard
MCU = $(CPU) -mthumb $(FPU) $(FLOAT-ABI)

C_DEFS = \
-DDEBUG \
-D__SAMV71Q21B__

AS_INCLUDES = 

# List the directories containing header files
C_INCLUDES +=  \
-Icore/src \
-I../core/src \
-Icore/samv71b/include \
-Idrivers/ \
-Idrivers/config \
-Idrivers/hal/include \
-Idrivers/hal/utils/include \
-Idrivers/hpl/core \
-Idrivers/hpl/pio \
-Idrivers/hpl/pmc \
-Idrivers/hpl/usart \
-Idrivers/hpl/xdmac \
-Idrivers/hpl/sdramc \
-Idrivers/hpl/smc \
-Idrivers/hri \
-Idrivers/CMSIS/Core/Include \

SOURCE_DIR = core
CCSDS_DIR = ../core
DRIVER_DIR = drivers

#Pure make. Should work on all platforms
rwildcard=$(wildcard $1$2) $(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2))

# '/' mandatory
C_SOURCES = $(call rwildcard,$(SOURCE_DIR)/,*.c)
C_SOURCES += $(call rwildcard,$(CCSDS_DIR)/,*.c)
C_SOURCES += $(call rwildcard,$(DRIVER_DIR)/,*.c)

ASFLAGS = $(MCU) $(AS_DEFS) $(AS_INCLUDES) $(OPT) -Wall
CFLAGS = $(MCU) $(C_DEFS) $(C_INCLUDES) $(OPT) -Wall -g -std=c99
CFLAGS += -MMD -MP -MF"$(@:%.o=%.d)"

# -lm -lnosys
LIBS = -lnosys
LDSCRIPT = \
	   -T"$(SOURCE_DIR)/samv71b/gcc/gcc/samv71q21b_flash.ld" \
	   -L"$(SOURCE_DIR)/samv71b/gcc/gcc"
LDFLAGS = $(MCU) -specs=nosys.specs $(LDSCRIPT) $(LIBDIR) $(LIBS) -Wl,-Map=$(BUILD_DIR)/$(TARGET).map,--cref -Wl,--gc-sections

all: $(BUILD_DIR)/$(TARGET).elf $(BUILD_DIR)/$(TARGET).bin

OBJECTS = $(addprefix $(BUILD_DIR)/,$(notdir $(C_SOURCES:.c=.o)))
vpath %.c $(sort $(dir $(C_SOURCES)))
# list of ASM program objects
OBJECTS += $(addprefix $(BUILD_DIR)/,$(notdir $(ASM_SOURCES:.s=.o)))
vpath %.s $(sort $(dir $(ASM_SOURCES)))

#Opens the default terminal, flashes the board and launches a gdb with a JLink connection for debugging.
debug: all
	@JLinkExe -commanderscript cmd.jlink
	@JLinkGDBServer -if SWD -Device ATSAMV71Q21B &
	@$(TERM) -e arm-none-eabi-gdb --eval-command="target remote localhost:2331" ./build/SAMV71.elf

flash: all
	@JLinkExe -commanderscript cmd.jlink

$(BUILD_DIR)/%.o: %.c Makefile | $(BUILD_DIR) 
	@$(CC) -c $(CFLAGS) -Wa,-a,-ad,-alms=$(BUILD_DIR)/$(notdir $(<:.c=.lst)) $< -o $@
	$(info [ATSAMV71Q21B] Compiling $@)

$(BUILD_DIR)/%.o: %.s Makefile | $(BUILD_DIR)
	@$(AS) -c $(CFLAGS) $< -o $@

$(BUILD_DIR)/$(TARGET).elf: $(OBJECTS)
	@$(CC) $(OBJECTS) $(LDFLAGS) -Wl,--print-memory-usage -o $@
	$(info [GENERATING] $@)
	$(SZ) $@

$(BUILD_DIR)/%.bin: $(BUILD_DIR)/%.elf
	$(info [GENERATING] $@)
	@$(BIN) $< $@	
	
$(BUILD_DIR):
	mkdir $@		

clean:
	-rm -fR $(BUILD_DIR)

-include $(wildcard $(BUILD_DIR)/*.d)
