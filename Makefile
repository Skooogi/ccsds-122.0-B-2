PROJECT = ccsds

BUILD_DIR = build
SOURCE_DIR = core/src

C_INCLUDES = \
-Icore/include \

C_DEFS =
CFLAGS = $(C_DEFS) $(C_INCLUDES) -Wall -g -O3
#Dependency information
CFLAGS+= -MMD -MP -MF"$(@:%.o=%.d)"

LIBS = -lc -lm
LIBDIR = 
LDFLAGS = $(LIBDIR) $(LIBS)

SOURCES := $(wildcard $(SOURCE_DIR)/*.c)
OBJECTS := $(patsubst $(SOURCE_DIR)/%.c, $(BUILD_DIR)/%.o, $(SOURCES))

all: $(BUILD_DIR)/$(PROJECT).bin 

run: all
	@(cd ${BUILD_DIR}; ./$(PROJECT).bin)

debug: all 
	@(cd ${BUILD_DIR}; gdb ./$(PROJECT).bin)

perf: all
	@(cd ${BUILD_DIR}; perf record -F max --call-graph dwarf ./$(PROJECT).bin)

stat: all
	@(cd ${BUILD_DIR}; perf stat -d ./$(PROJECT).bin)

valgrind: all
	@(cd ${BUILD_DIR}; valgrind --leak-check=full --track-origins=yes ./$(PROJECT).bin)

$(BUILD_DIR)/$(PROJECT).bin: $(OBJECTS)
	@$(CC) $^ $(LDFLAGS) -o $@
	$(info [GENERATING] $@)

$(BUILD_DIR)/%.o: $(SOURCE_DIR)/%.c
	@mkdir -p $(@D)
	@$(CC) -c $(CFLAGS) $< -o $@
	$(info [COMPILING] $<)

clean:
	@rm -fR $(BUILD_DIR)
	@rm -fR $(BINARY_DIR)
	@echo Project cleaned!
