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

TEST_FILE = "../tests/raw/test_image_noise_4k.raw"
TEST_SIZE = 4096
RUN_BIN = ./$(PROJECT).bin $(TEST_FILE) $(TEST_SIZE)

run: all
	@(cd ${BUILD_DIR}; $(RUN_BIN))

debug: all 
	@(cd ${BUILD_DIR}; gdb $(RUN_BIN))

perf: all
	@(cd ${BUILD_DIR}; perf record -F max --call-graph dwarf $(RUN_BIN))

stat: all
	@(cd ${BUILD_DIR}; perf stat -d $(RUN_BIN))

test: all
	@(cd python/cython; python3 compile.py)
	@(cd python; python3 test_compare_dwt.py)

valgrind: all
	@(cd ${BUILD_DIR}; valgrind --leak-check=full --track-origins=yes $(RUN_BIN))

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
