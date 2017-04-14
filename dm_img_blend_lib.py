# import modules
import ctypes as ct
# define constant values
# return code
DM_IMG_BLEND_RETURN_OK = 0
DM_IMG_BLEND_RETURN_FAIL = 1
# dm_img_blend_lib


class dm_img_blend_lib(object):
    """docstring for dm_img_blend_lib"""
    def __init__(self, useOpenCL):
        super(dm_img_blend_lib, self).__init__()
        dll_path = unicode("dm_img_blender_c_export.dll")
        self.duiDLL = ct.CDLL(dll_path)
        self.devPtr = ct.c_voidp( self.duiDLL.dm_img_blend_New(ct.c_uint(useOpenCL)) )
        if not self.devPtr:
            print 'dm_img_blend_lib is NOT created'
            pass
        else:
            print 'dm_img_blend_lib IS created'
            pass
        pass
    def __del__(self):
        if not self.devPtr:
            print 'dm_img_blend_lib is already empty'
            pass
        else:
            self.duiDLL.dm_img_blend_Delete(self.devPtr)
            print 'dm_img_blend_lib IS deleted'
            pass
        pass
    # reset
    def clearAll(self):
        self.duiDLL.dm_img_blend_ClearAll(self.devPtr)
        pass
    # register images
    def addNewImage(self, data_ptr, width, height, \
                    crop_offset_x, crop_offset_y, \
                    tile_pos_x, tile_pos_y, \
                    tile_width, tile_height):
        return self.duiDLL.dm_img_blend_AddNewImage(self.devPtr, data_ptr, \
                        ct.c_uint(width), ct.c_uint(height), \
                        ct.c_float(crop_offset_x), ct.c_float(crop_offset_y), \
                        ct.c_float(tile_pos_x), ct.c_float(tile_pos_y), \
                        ct.c_uint(tile_width), ct.c_uint(tile_height))
    # perfomr image blending
    # use_blender: 0-feather, others-multiplication
    # try_gpu: 0-do not use GPU, 1-try to use GPU
    def doBlending(self, blend_width, use_blender, try_gpu):
        return self.duiDLL.dm_img_blend_DoBlending(self.devPtr, ct.c_uint(blend_width), \
                                                    ct.c_uint(use_blender), ct.c_int(try_gpu))
    # output image dimension
    def outputDimension(self, img_index):
        c_width = ct.c_uint()
        c_height = ct.c_uint()
        r = self.duiDLL.dm_img_blend_OutputDimension(self.devPtr, ct.c_int(img_index), \
                                                        ct.byref(c_width), ct.byref(c_height))
        return r, c_width.value, c_height.value
    # output blended images
    def outputBlendedImage(self, data_ptr, img_index):
        return self.duiDLL.dm_img_blend_OutputBlendedImage(self.devPtr, data_ptr, ct.c_int(img_index))
