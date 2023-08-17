class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

bmp_images = [
    "../res/noise/test_image_noise_32.bmp",
    "../res/noise/test_image_noise_64.bmp",
    "../res/noise/test_image_noise_128.bmp",
    "../res/noise/test_image_noise_256.bmp",
    "../res/noise/test_image_noise_512.bmp",
	#"../res/noise/test_image_noise_1k.bmp",
	#"../res/noise/test_image_noise_2k.bmp",
	#"../res/noise/test_image_noise_4k.bmp",
    "../res/pattern/test_image_checker_32.bmp",
    "../res/pattern/test_image_gradient_32.bmp",
    "../res/pattern/test_image_black_32.bmp",
    "../res/pattern/test_image_white_32.bmp",
	"../res/pattern/test_image_black_256.bmp",
	"../res/pattern/test_image_white_256.bmp",
	"../res/space/test_image_space_1.bmp",
	"../res/space/test_image_space_2.bmp",
	"../res/space/test_image_space_3.bmp",
	"../res/space/test_image_space_4.bmp",
	"../res/space/test_image_space_5.bmp",
	"../res/space/test_image_space_6.bmp",
	"../res/space/test_image_space_7.bmp",
]

raw_images = [
    ["../res/noise/raw/test_image_noise_32.raw", 32, 32, 8],
    ["../res/noise/raw/test_image_noise_64.raw", 64, 64, 8],
    ["../res/noise/raw/test_image_noise_128.raw", 128, 128, 8],
    ["../res/noise/raw/test_image_noise_256.raw", 256, 256, 8],
    ["../res/noise/raw/test_image_noise_512.raw", 512, 512, 8],
	#["../res/noise/raw/test_image_noise_1k.raw", 1024, 1024, 8],
	#["../res/noise/raw/test_image_noise_2k.raw", 2048, 2048, 8],
	#["../res/noise/raw/test_image_noise_4k.raw", 4096, 4096, 8],
    ["../res/pattern/raw/test_image_checker_32.raw", 32, 32, 8],
    ["../res/pattern/raw/test_image_gradient_32.raw", 32, 32, 8],
    ["../res/pattern/raw/test_image_black_32.raw", 32, 32, 8],
    ["../res/pattern/raw/test_image_white_32.raw", 32, 32, 8],
	["../res/pattern/raw/test_image_black_256.raw", 256, 256, 8],
	["../res/pattern/raw/test_image_white_256.raw", 256, 256, 8],
	["../res/space/raw/test_image_space_1.raw", 786, 604, 8],
	["../res/space/raw/test_image_space_2.raw", 1048, 725, 8],
	["../res/space/raw/test_image_space_3.raw", 2000, 1322, 8],
	["../res/space/raw/test_image_space_4.raw", 1012, 569, 8],
	["../res/space/raw/test_image_space_5.raw", 918, 1087, 8],
	["../res/space/raw/test_image_space_6.raw", 2048, 2048, 8],
	["../res/space/raw/test_image_space_7.raw", 900, 900, 8],
]
