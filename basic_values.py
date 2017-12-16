import os, sys
# define constant values
current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

MAX_PYRAMID_LEVEL = (1<<19)
MaxZoomOutLevel = MAX_PYRAMID_LEVEL
MaxZoomInLevel = 32
MaxQPixmapCacheLimitInKB = 1024*500 #500MB

DM_BACKGROUND_GRID_SIZE = 10

DM_Z_VALUE_FOR_PIXMAP = 1.0

CYCLE_LEN = (1<<30)

ZOOM_IN_FACTOR = 2.
ZOOM_OUT_FACTOR = 0.5
