PROJECT = ccsds

BUILD_DIR = build
SOURCE_DIR = core/src

C_INCLUDES = \
-Icore/include \

C_DEFS =
CFLAGS = $(C_DEFS) $(C_INCLUDES) -Wall -g
#Dependency information
CFLAGS+= -MMD -MP -MF"$(@:%.o=%.d)"

LIBS = -lc -lm
LIBDIR = 
LDFLAGS = $(LIBDIR) $(LIBS)

SOURCES := $(wildcard $(SOURCE_DIR)/*.c)
OBJECTS := $(patsubst $(SOURCE_DIR)/%.c, $(BUILD_DIR)/%.o, $(SOURCES))

all: $(BUILD_DIR)/$(PROJECT).bin 

TEST_IN_FILE = "../res/pattern/raw/test_image_gradient_32.raw"
TEST_OUT_FILE = "../python/output.cmp"
TEST_SIZE = 32 32 8
RUN_BIN = ./$(PROJECT).bin $(TEST_IN_FILE) $(TEST_OUT_FILE) $(TEST_SIZE)

run: all
	@(cd ${BUILD_DIR}; $(RUN_BIN))

debug: all 
	@(cd ${BUILD_DIR}; gdb --args $(RUN_BIN))

perf: all
	@(cd ${BUILD_DIR}; perf record -F max --call-graph dwarf $(RUN_BIN))

stat: all
	@(cd ${BUILD_DIR}; perf stat -d $(RUN_BIN))

valgrind: all
	@(cd ${BUILD_DIR}; valgrind --leak-check=full --track-origins=yes $(RUN_BIN))
massig: all
	@(cd ${BUILD_DIR}; valgrind --tool=massif $(RUN_BIN))

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
