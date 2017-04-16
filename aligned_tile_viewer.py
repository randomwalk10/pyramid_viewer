import os, sys
from basic_values import *
from dm_img_blend_lib import dm_img_blend_lib, ct, DM_IMG_BLEND_RETURN_OK
from PyQt4 import QtCore, QtGui
import Queue
import numpy as np
import glob
import cv2
# define constant values
DM_BACKGROUND_GRID_SIZE = 10

DM_Z_VALUE_FOR_PIXMAP = 1.0
DM_Z_VALUE_FOR_RECT = 2.0

DM_USE_BLENDER = True
DM_PIXMAP_USERTYPE = QtGui.QGraphicsItem.UserType + 1
# define classes
class DmThreadLoadAllImages(QtCore.QThread):
    """docstring for DmThreadLoadAllImages"""
    signal_sendImageToGUI = QtCore.pyqtSignal(tuple, QtGui.QImage)
    def __init__(self, img_load_queue, image_dir):
        super(DmThreadLoadAllImages, self).__init__()
        self.img_load_queue = img_load_queue
        self.image_dir = image_dir
        self.exitFlag = False

    def __del__(self):
        self.wait()

    def run(self):
        while( not self.exitFlag):
            try:
                tile_info = self.img_load_queue.get(False, 0.5)
                path_to_tile = self.returnTilePath(*tile_info)
                if os.path.exists(path_to_tile):
                    tile_image = QtGui.QImage(path_to_tile)
                    self.signal_sendImageToGUI.emit(tile_info, tile_image)
            except Queue.Empty:
                pass

    # def run(self):
    #   while( not self.exitFlag):
    #       try:
    #           tile_info = self.img_load_queue.get(False, 0.5)
    #           path_to_tile = self.returnTilePath(tile_info[0], tile_info[1], 1)
    #           if os.path.exists(path_to_tile):
    #               if(1>=tile_info[2]):
    #                   tile_image = QtGui.QImage(path_to_tile)
    #                   self.signal_sendImageToGUI.emit(tile_info, tile_image)
    #               else:
    #                   # np_array = cv2.imread(path_to_tile, cv2.IMREAD_UNCHANGED)
    #                   # # tile_image = self.generatePyramidImage(np_array, tile_info[2])
    #                   # np_array = self.generatePyramidImage(np_array, tile_info[2])
    #                   # # np_array = cv2.cvtColor(np_array, cv2.COLOR_BGR2RGB)
    #                   # # self.signal_sendImageToGUI.emit(tile_info, np_array)

    #                   # path_to_pyramid_tile = self.returnTilePath(*tile_info)
    #                   # if not os.path.exists(self.image_dir+os.path.sep+'pyramid'):
    #                   #   os.makedirs(self.image_dir+os.path.sep+'pyramid')
    #                   # cv2.imwrite(path_to_pyramid_tile, np_array)
    #                   # tile_image = QtGui.QImage(path_to_pyramid_tile)
    #                   # # print tile_image.size()/2
    #                   # self.signal_sendImageToGUI.emit(tile_info, tile_image)

    #                   # # np_array = cv2.cvtColor(np_array, cv2.COLOR_BGR2RGB)
    #                   # # img_width = np_array.shape[1]
    #                   # # img_height = np_array.shape[0]
    #                   # # tile_image = QtGui.QImage(np_array, img_width, img_height, QtGui.QImage.Format_RGB888)
    #                   # # tile_image_copy = tile_image.copy(tile_image.rect())
    #                   # # self.signal_sendImageToGUI.emit(tile_info, tile_image_copy)

    #                   # check if prev level images is in qpixmapcache
    #                   pyramid_level = tile_info[2]
    #                   temp_level = pyramid_level/2
    #                   pixmap = QtGui.QPixmap()
    #                   while not QtGui.QPixmapCache.find(str((tile_info[0], tile_info[1], temp_level)), pixmap):
    #                       temp_level /= 2
    #                       if(temp_level<1):
    #                           break
    #                   if(temp_level<1):
    #                       tile_image = QtGui.QImage(path_to_tile)
    #                       temp_level = 1
    #                       pass
    #                   else:
    #                       tile_image = pixmap.toImage()
    #                       pass
    #                   while(temp_level<pyramid_level):
    #                       tile_image = tile_image.scaled(tile_image.size()/2)
    #                       temp_level*=2
    #                   self.signal_sendImageToGUI.emit(tile_info, tile_image)
    #       except Queue.Empty:
    #           pass

    def returnTilePath(self, mat_id, x_index, y_index, pyramid_level):
        if(1>=pyramid_level):
            path_to_return = self.image_dir+os.path.sep+'tile_%d_%d_%d.bmp'%(mat_id, x_index, y_index)
        else:
            path_to_return = self.image_dir+os.path.sep+'pyramid'+os.path.sep + \
                                'tile_%d_%d_%d_%d.bmp'%(mat_id, x_index, y_index, pyramid_level)
        return path_to_return

    def generatePyramidImage(self, np_array, pyramid_level):
        temp = 1
        while(temp < pyramid_level):
            np_array = cv2.pyrDown(np_array)
            temp*=2
        # np_array = cv2.cvtColor(np_array, cv2.COLOR_BGR2RGB)
        # img_width = np_array.shape[1]
        # img_height = np_array.shape[0]
        # # print img_width, img_height
        # tile_image = QtGui.QImage(np_array, img_width, img_height, QtGui.QImage.Format_RGB888)
        # return tile_image

        return np_array

    def scheduleStop(self):
        self.exitFlag = True

class DmPixmapItem(QtGui.QGraphicsPixmapItem):
    """docstring for DmPixmapItem"""
    def __init__(self, img_load_queue = None, image_dir = '', mat_id = -1, tile_x_index = 0, tile_y_index = 0, \
                    tile_pos_x = 0., tile_pos_y = 0., tile_width = 0., tile_height = 0.):
        if not img_load_queue:
            raise ValueError('Error: img_load_queue is empty')
        super(DmPixmapItem, self).__init__(parent = None)
        # self.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.setTransformationMode(QtCore.Qt.FastTransformation)
        self.setZValue(DM_Z_VALUE_FOR_PIXMAP)
        self.setPos(tile_pos_x, tile_pos_y)
        # self.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations, True)

        self.img_load_queue = img_load_queue
        self.image_dir = image_dir
        self.mat_id = mat_id
        self.x_index = tile_x_index
        self.y_index = tile_y_index
        self.pos_x = tile_pos_x
        self.pos_y = tile_pos_y
        self.width = tile_width
        self.height = tile_height
        self.offset_x = 0.
        self.offset_y = 0.
        self.IsWaitingForBlending = False
        self.IsBlendingDone = False

    def boundingRect(self):
        return QtCore.QRectF(0., 0., self.width, self.height)
        pass

    def shape(self):
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def setBlendingDoneFlag(self):
        self.IsBlendingDone = True
        pass

    def type(self):
        return DM_PIXMAP_USERTYPE

    def paint(self, painter, option, widget):
        if not isinstance(painter, QtGui.QPainter):
            return
        elif not isinstance(option, QtGui.QStyleOptionGraphicsItem):
            return
        current_lod = option.levelOfDetailFromTransform(painter.worldTransform())
        # find path to tile
        if 1.0<=current_lod:
            # set pyramid level to 1
            pyramid_level = 1
        else:
            # calculate pyramid level
            pyramid_level = int(1/current_lod)
        tile_info = (self.mat_id, self.x_index, self.y_index, pyramid_level)
        # create pixmap
        pixmap = QtGui.QPixmap()
        if(1==pyramid_level) and (True==DM_USE_BLENDER):
            if(False==self.IsWaitingForBlending):
                # set flag
                self.IsWaitingForBlending = True
                # send tile info to img_load_queue
                self.img_load_queue.put( tile_info )
                return
            else:
                # check if blending is done
                if False == self.IsBlendingDone:
                    return
                # reset flags
                self.IsBlendingDone = False
                self.IsWaitingForBlending = False
                # return if no pixmap is found in the cache
                if not QtGui.QPixmapCache.find(str(tile_info), pixmap):
                    return
        elif not QtGui.QPixmapCache.find(str(tile_info), pixmap):
            self.img_load_queue.put( tile_info )
            return
        # set pixmap
        painter.save()
        if 1.0>current_lod:
            painter.scale(1/current_lod, 1/current_lod)
        roi_tl = QtCore.QPoint(self.offset_x, self.offset_y)
        roi_size = QtCore.QSize(self.width, self.height)
        if 1.0<=current_lod:
            painter.drawPixmap(QtCore.QPoint(0,0), pixmap, \
                                QtCore.QRect(roi_tl, roi_size))
        else:
            temp_pyrmid_level = pyramid_level
            while(temp_pyrmid_level>1):
                roi_tl/=2
                roi_size/=2
                temp_pyrmid_level/=2
            painter.drawPixmap(QtCore.QPoint(0,0), pixmap, \
                                QtCore.QRect(roi_tl, roi_size))
        # painter.drawPixmap(0, 0, pixmap)
        painter.restore()
        pass

    def preloadPyramidsIntoCache(self, list_of_pyramid_levels = []):
        if not list_of_pyramid_levels:
            return
        for pyramid_level in list_of_pyramid_levels:
            self.loadPyramidTileIntoCache(pyramid_level)
        pass

    def loadPyramidTileIntoCache(self, pyramid_level = 1):
        path_to_tile = self.returnTilePath(pyramid_level)
        tile_info = (self.mat_id, self.x_index, self.y_index, pyramid_level)
        if not QtGui.QPixmapCache.find(str(tile_info)):
            if os.path.exists(path_to_tile):
                pixmap = QtGui.QPixmap(path_to_tile)
                QtGui.QPixmapCache.insert(str(tile_info), pixmap)
                pass
            pass

    def returnTilePath(self, pyramid_level = 1):
        if(1>=pyramid_level):
            path_to_return = self.image_dir+os.path.sep+'tile_%d_%d_%d.bmp'%(self.mat_id, self.x_index, self.y_index)
        else:
            path_to_return = self.image_dir+os.path.sep+'pyramid'+os.path.sep + \
                                'tile_%d_%d_%d_%d.bmp'%(self.mat_id, self.x_index, self.y_index, pyramid_level)
        return path_to_return

    def setResizeOffset(self, offset_x = 0., offset_y = 0.):
        self.offset_x = offset_x
        self.offset_y = offset_y


class DmReviewGraphicsViewer(QtGui.QGraphicsView):
    """docstring for DmReviewGraphicsViewer"""

    signal_scene_pos = QtCore.pyqtSignal(QtCore.QPointF)
    signal_scene_rect = QtCore.pyqtSignal(QtCore.QRectF)
    signal_mag_factor = QtCore.pyqtSignal(str)
    signal_cursor_pos = QtCore.pyqtSignal(QtCore.QPointF)
    signal_enable_use_rect = QtCore.pyqtSignal(bool)
    signal_stop_thread_loadingPixmap = QtCore.pyqtSignal()

    def __init__(self, scene = None, parent = None, max_zoom_in_level = MaxZoomInLevel, max_zoom_out_level = MaxZoomOutLevel):
        if scene:
            super(DmReviewGraphicsViewer, self).__init__(scene, parent)
        else:
            # super(DmReviewGraphicsViewer, self).__init__(parent)
            raise ValueError('Error: scene is None')
        if (max_zoom_in_level<1) or (max_zoom_out_level<1):
            raise ValueError('Error: wrong input')
        self.enableDragScroll(False)
        self.enableSelectArea(False)
        self.select_on = False
        self.view_mag_factor = 1.0
        self.base_mag_factor = 1.0
        self.max_zoom_in_level = max_zoom_in_level
        self.max_zoom_out_level = max_zoom_out_level
        self._scene = scene
        self.prescan_tile_list = []
        self.dm_pixmap_dict = {}
        self.dm_rect_dict = {}
        self.pf_pt_dict = {}
        self.img_load_queue = Queue.LifoQueue()#size infinite
        # self.semaphore_image_loading = QtCore.QSemaphore(1)
        QtGui.QPixmapCache.setCacheLimit(MaxQPixmapCacheLimitInKB)
        QtGui.QPixmapCache.clear()
        self.blender = dm_img_blend_lib(useOpenCL = 0)
        self.blender.clearAll()
        self.items_to_blend = [] #(mat_id, index_x, index_y)
        pass

    def initializeImageReviewSpace(self):
        # mode
        self.setInteractive(False)
        self.setCacheMode(QtGui.QGraphicsView.CacheBackground)
        # self.setViewportUpdateMode(QtGui.QGraphicsView.MinimalViewportUpdate)
        self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        # self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)
        self.setMouseTracking(True)
        # background
        gridSize = DM_BACKGROUND_GRID_SIZE
        backgroundPixmap = QtGui.QPixmap(gridSize*2, gridSize*2)
        backgroundPixmap.fill(QtGui.QColor("powderblue"))
        painter = QtGui.QPainter(backgroundPixmap)
        backgroundColor = QtGui.QColor("palegoldenrod")
        painter.fillRect(0, 0, gridSize, gridSize, backgroundColor)
        painter.fillRect(gridSize, gridSize, gridSize, gridSize, backgroundColor)
        painter.end()

        self._scene.setBackgroundBrush(QtGui.QBrush(backgroundPixmap))
        # self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        self.setRenderHint(QtGui.QPainter.Antialiasing, False)

        pass

    def mousePressEvent(self, mouseEvent):
        assert isinstance(mouseEvent, QtGui.QMouseEvent)
        if (True==self.selectAreaEnabled) and (mouseEvent.button() == QtCore.Qt.LeftButton):
            self.selectArea_origin = mouseEvent.pos()
            # print 'origin:',self.selectArea_origin
            self.rubber_band = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, self)
            self.rubber_band.setGeometry(QtCore.QRect(self.selectArea_origin, QtCore.QSize()))
            self.rubber_band.show()
            self.select_on = True
            mouseEvent.accept()
        elif mouseEvent.button() == QtCore.Qt.RightButton:
            self.panStartX = mouseEvent.x()
            self.panStartY = mouseEvent.y()
            self.enableDragScroll(True)
            mouseEvent.accept()
        elif (mouseEvent.button() == QtCore.Qt.LeftButton) and (False == self.handDragEnabled):
            pos_in_scene = self.mapToScene(mouseEvent.pos().x(),mouseEvent.pos().y())
            # print 'pos_in_scene:',pos_in_scene, 'pos_in_stage:',PixelSpace2StageSpace(pos_in_scene.x(), pos_in_scene.y())
            # emit to scan engine(convert scene_pos to stage_pos, move to stage_pos, etc.)
            self.signal_scene_pos.emit(pos_in_scene)
            mouseEvent.accept()
        else:
            mouseEvent.ignore()
            super(DmReviewGraphicsViewer, self).mousePressEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        assert isinstance(mouseEvent, QtGui.QMouseEvent)
        if (True==self.selectAreaEnabled) and (mouseEvent.button() == QtCore.Qt.LeftButton):
            self.select_on = False
            self.selectArea_end = mouseEvent.pos()
            view_rect = QtCore.QRect(self.selectArea_origin, self.selectArea_end).normalized()
            # self.printContainedItems(view_rect)
            # convert view_rect to scene_rect, emit to scane engine(create tile matrix, etc.)
            scene_polygon = self.mapToScene(view_rect)
            scene_rect = scene_polygon.boundingRect()
            self.signal_scene_rect.emit(scene_rect)
            self.rubber_band.hide()
            mouseEvent.accept()
        elif mouseEvent.button() == QtCore.Qt.RightButton:
            self.enableDragScroll(False)
            mouseEvent.accept()
        else:
            mouseEvent.ignore()
            super(DmReviewGraphicsViewer, self).mouseReleaseEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        assert isinstance(mouseEvent, QtGui.QMouseEvent)
        if (True==self.select_on):
            self.rubber_band.setGeometry(QtCore.QRect(self.selectArea_origin, mouseEvent.pos()).normalized())
            mouseEvent.accept()
        elif(True == self.handDragEnabled):
            hbar = self.horizontalScrollBar()
            vbar = self.verticalScrollBar()
            hbar.setValue( hbar.value() - (mouseEvent.x()-self.panStartX) )
            vbar.setValue( vbar.value() - (mouseEvent.y()-self.panStartY) )
            self.panStartX = mouseEvent.x()
            self.panStartY = mouseEvent.y()

            mouseEvent.accept()
        else:
            pos_in_scene = self.mapToScene(mouseEvent.pos().x(),mouseEvent.pos().y())
            self.signal_cursor_pos.emit(pos_in_scene)
            mouseEvent.accept()
            # mouseEvent.ignore()
            # super(DmReviewGraphicsViewer, self).mouseMoveEvent(mouseEvent)

    def enableDragScroll(self, isEnabled = False):
        if isEnabled:
            self.handDragEnabled = True
            self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        else:
            self.handDragEnabled = False
            self.setDragMode(QtGui.QGraphicsView.NoDrag)

    def enableSelectArea(self, isEnabled = False):
        self.selectAreaEnabled = isEnabled
        pass

    def printContainedItems(self, view_rect = None):
        if not view_rect:
            raise ValueError('Error: wrong input')
        assert isinstance(view_rect, QtCore.QRect)
        list_of_items = self.items(view_rect, QtCore.Qt.ContainsItemShape)
        if not list_of_items:
            print 'Selected area contains nothing'
        else:
            print 'Selected area contains %d items'%len(list_of_items)
        pass

    def viewZoomIn(self):
        if( 2.*(self.view_mag_factor) <= float(self.max_zoom_in_level) ):
            self.view_mag_factor*=2.
            self.signal_mag_factor.emit('%.2fX'%(self.base_mag_factor*self.view_mag_factor))
            self.scale(2., 2.)
            pass
        pass

    def viewZoomOut(self):
        if( 0.5*(self.view_mag_factor) >= (1./float(self.max_zoom_out_level)) ):
            self.view_mag_factor*=0.5
            self.signal_mag_factor.emit('%.2fX'%(self.base_mag_factor*self.view_mag_factor))
            self.scale(0.5, 0.5)
            pass
        pass

    def updateBaseMagFactor(self, base = 1.0):
        self.base_mag_factor = base
        self.signal_mag_factor.emit('%.2fX'%(self.base_mag_factor*self.view_mag_factor))
        pass

    def updateMaxZoomLevel(self, max_zoom_in_level = 32, max_zoom_out_level = 32):
        if (max_zoom_in_level<1) or (max_zoom_out_level<1):
            raise ValueError('Error: wrong input')
        self.max_zoom_in_level = max_zoom_in_level
        self.max_zoom_out_level = max_zoom_out_level
        pass

    def getCurrentLevelOfDetails(self):
        return self.view_mag_factor

    def createImageReviewTiles(self):
        # get image directory
        qstr_image_dir = QtGui.QFileDialog.getExistingDirectory( parent = self, caption = 'Open Directory', \
                                                                    directory = current_dir )
        if not qstr_image_dir:
            QtGui.QMessageBox.about(self, 'Error', 'Invalid directory')
            return
        # str_crop_image_dir = str(qstr_image_dir)+os.path.sep+'resize'
        str_crop_image_dir = str(qstr_image_dir)
        if not os.path.exists(str_crop_image_dir):
            QtGui.QMessageBox.about(self, 'Error', 'Failed to find cropped tiles')
            return
        # get the list of mat_id
        align_info_filename_list = glob.glob(str_crop_image_dir+os.path.sep+'alignment_info_*.txt')
        mat_id_list = []
        for filename in align_info_filename_list:
            start_index = filename.find('alignment_info_')+len('alignment_info_')
            end_index = filename.find('.txt')
            try:
                mat_id = int(filename[start_index:end_index])
                mat_id_list.append(mat_id)
            except ValueError:
                continue
        if not mat_id_list:
            QtGui.QMessageBox.about(self, 'Error', 'Failed to find alignment info files')
            return
        # get cam calib info
        float_pixel_size = 0.4
        if mat_id_list:
            target_mat_id = mat_id_list[0]
            path_to_scan_info = str_crop_image_dir+os.path.sep+'scan_info_'+str(target_mat_id)+'.txt'
            if not os.path.exists(path_to_scan_info):
                QtGui.QMessageBox.about(self, 'Error', 'Failed to find '+'scan_info_'+str(target_mat_id)+'.txt')
                return
            scan_info_file = open(path_to_scan_info, 'r')
            scan_info_lines = scan_info_file.read().splitlines()
            cam_calib_index = 0
            for i in range(len(scan_info_lines)):
                if '[cam_calib]' == scan_info_lines[i]:
                    cam_calib_index = i + 1
                    break
            if(cam_calib_index==0):
                QtGui.QMessageBox.about(self, 'Error', 'Failed to find [cam_calib]')
                return
            str_cam_angle_x, str_cam_angle_y, str_um_per_pixel_x, str_um_per_pixel_y = scan_info_lines[cam_calib_index].split(',')
            float_pixel_size = float(str_um_per_pixel_x)
        # clear image review tiles
        self.clearImageReviewTiles()
        # get tile_list and create DmPixmapItem
        for mat_id in mat_id_list:
            # parse align info
            path_to_align_info = str_crop_image_dir+os.path.sep+'alignment_info_'+str(mat_id)+'.txt'
            if not os.path.exists(path_to_align_info):
                QtGui.QMessageBox.about(self, 'Error', 'Failed to find '+'alignment_info_'+str(mat_id)+'.txt')
                return
            align_info_file = open(path_to_align_info, 'r')
            align_info_lines = align_info_file.read().splitlines()
            # get tile num
            tile_num_index = 0
            for i in range(len(align_info_lines)):
                if '[tile_num]' == align_info_lines[i]:
                    tile_num_index = i + 1
                    break
            if(tile_num_index==0):
                QtGui.QMessageBox.about(self, 'Error', 'Failed to find [tile_num]')
                return
            str_max_tile_num = align_info_lines[tile_num_index]
            int_max_tile_num = int(str_max_tile_num)
            # get align tiles
            tile_pos_index = 0
            for i in range(len(align_info_lines)):
                if '[align_tile_pos_scene_topleft]' == align_info_lines[i]:
                    tile_pos_index = i + 1
                    break
            if(tile_pos_index==0):
                QtGui.QMessageBox.about(self, 'Error', 'Failed to find [align_tile_pos_scene_topleft]')
                return
            align_tile_dict = {}
            for i in range(tile_pos_index, tile_pos_index+int_max_tile_num):
                str_tile_index_x, str_tile_index_y, str_tile_pos_x, str_tile_pos_y = align_info_lines[i].split(',')
                align_tile_dict[int(str_tile_index_x), int(str_tile_index_y)] = (float(str_tile_pos_x), float(str_tile_pos_y))
            # get resize tile list
            tile_pos_index = 0
            for i in range(len(align_info_lines)):
                if '[resize_tile_pos_scene_topleft]' == align_info_lines[i]:
                    tile_pos_index = i + 1
                    break
            if(tile_pos_index==0):
                QtGui.QMessageBox.about(self, 'Error', 'Failed to find [resize_tile_pos_scene_topleft]')
                return
            tile_list = []
            for i in range(tile_pos_index, tile_pos_index+int_max_tile_num):
                str_tile_index_x, str_tile_index_y, str_tile_pos_x, str_tile_pos_y, str_group_id, str_group_size, \
                            str_tile_width, str_tile_height = align_info_lines[i].split(',')
                tile_list.append( ( int(str_tile_index_x), int(str_tile_index_y), float(str_tile_pos_x), float(str_tile_pos_y), \
                                    int(str_group_id), int(str_group_size), int(str_tile_width), int(str_tile_height) ) )
            # self.semaphore_image_loading.acquire(1)
            tile_loading_progress = QtGui.QProgressDialog('tile loading for mat[%d] is started'%mat_id, 'cancel', 0, len(tile_list), self)
            tile_loading_progress.setWindowTitle('tile loading in progress')
            tile_loading_progress.setFixedSize(400, 150)
            tile_loading_progress.setValue(0)

            # list_of_pyramid_levels = [self.max_zoom_out_level, self.max_zoom_out_level/2, self.max_zoom_out_level/4]
            list_of_pyramid_levels = []
            group_color_dict = {}
            for tile in tile_list:
                # load pixmap
                tile_item = DmPixmapItem(img_load_queue = self.img_load_queue, image_dir = str_crop_image_dir, mat_id = mat_id, \
                                                    tile_x_index = tile[0], tile_y_index = tile[1], \
                                                    tile_pos_x = tile[2], tile_pos_y = tile[3], \
                                                    tile_width = tile[6], tile_height = tile[7])
                tile_offset_x = int(tile[2] - align_tile_dict[tile[0], tile[1]][0])
                tile_offset_y = int(tile[3] - align_tile_dict[tile[0], tile[1]][1])
                tile_item.setResizeOffset(tile_offset_x, tile_offset_y)
                self._scene.addItem(tile_item)
                tile_item.preloadPyramidsIntoCache(list_of_pyramid_levels)
                self.dm_pixmap_dict[(mat_id, tile[0], tile[1])] = tile_item
                # load rect
                group_id = tile[4]
                group_size = tile[5]
                if group_id in group_color_dict.keys():
                    rect_color = group_color_dict[group_id]
                else:
                    if group_size == 1:
                        rect_color = (255,0,0)#red for isolated tile
                    else:
                        rect_color_gb = np.random.randint(0,255,2)
                        rect_color = (0,rect_color_gb[0],rect_color_gb[1])
                        group_color_dict[group_id] = rect_color
                pen = QtGui.QPen(QtGui.QColor(*rect_color))
                pen.setWidth(4)
                rect_item = self._scene.addRect(QtCore.QRectF(tile[2], tile[3], tile[6], tile[7]), pen)
                rect_item.setZValue(DM_Z_VALUE_FOR_RECT)
                rect_item.hide()
                self.dm_rect_dict[(mat_id, tile[0], tile[1])] = rect_item
                # update tile loading progress
                tile_loading_progress.setLabelText( 'tile[%d,%d,%d] is loaded.'%(mat_id, tile[0], tile[1]) )
                tile_loading_progress.setValue( tile_loading_progress.value()+1 )
        # start image loading thread
        self.thread_loadAllImages = DmThreadLoadAllImages(self.img_load_queue, str_crop_image_dir)
        self.thread_loadAllImages.started.connect(self.thread_loadAllImages_started)
        self.thread_loadAllImages.finished.connect(self.thread_loadAllImages_finished)
        self.thread_loadAllImages.signal_sendImageToGUI.connect(self.thread_loadAllImages_addPixmapToCache)
        self.signal_stop_thread_loadingPixmap.connect(self.thread_loadAllImages.scheduleStop)
        self.thread_loadAllImages.start()
        # update base mag factor
        if float_pixel_size<=0.3:
            self.updateBaseMagFactor(40.)
        elif float_pixel_size<0.6:
            self.updateBaseMagFactor(20.)
        elif float_pixel_size<1.2:
            self.updateBaseMagFactor(10.)
        else:
            self.updateBaseMagFactor(4.)
        # update use rect checkbox
        self.signal_enable_use_rect.emit(True)
        pass

    def clearImageReviewTiles(self):
        if not self.dm_pixmap_dict:
            # cleanup queue and cache
            while not self.img_load_queue.empty():
                self.img_load_queue.get(False)
            QtGui.QPixmapCache.clear()
            return
        # stop thread
        # self.thread_loadAllImages.scheduleStop()
        self.signal_stop_thread_loadingPixmap.emit()
        # self.semaphore_image_loading.acquire(1)
        self.thread_loadAllImages.wait()
        QtGui.QPixmapCache.clear()
        # remove all items
        for tile_item in self.dm_pixmap_dict.values():
            self._scene.removeItem(tile_item)
        self.dm_pixmap_dict.clear()
        for rect_item in self.dm_rect_dict.values():
            self._scene.removeItem(rect_item)
        self.dm_rect_dict.clear()
        # cleanup queue and cache
        while not self.img_load_queue.empty():
            self.img_load_queue.get(False)
        QtGui.QPixmapCache.clear()
        # disable enable_use_rect checkbox
        self.signal_enable_use_rect.emit(False)
        pass

    def thread_loadAllImages_started(self):
        pass

    def thread_loadAllImages_finished(self):
        # self.semaphore_image_loading.release(1)
        pass

    def blender_postProcess(self):
        # check if this is the last tile
        items_in_view = self.items(0, 0, \
                    self.viewport().size().width(), \
                    self.viewport().size().height())
        items_to_process = []
        for item in items_in_view:
            if item.type() != DM_PIXMAP_USERTYPE:
                continue # jump to next iteration
            elif (item.mat_id, item.x_index, item.y_index) \
                    not in self.items_to_blend:
                return
            items_to_process.append(item)
            pass
        if not items_to_process:
            return
        # perform blending
        r = self.blender.doBlending(blend_width = 16, use_blender = 1, \
                                try_gpu = 0)
        if DM_IMG_BLEND_RETURN_OK!=r:
            return
        # output images
        for i in range(len(self.items_to_blend)):
            img_index = i # img_index start from zero
            # get image size
            r, out_width, out_height = self.blender.outputDimension(img_index)
            if DM_IMG_BLEND_RETURN_OK!=r:
                return
            # create buffer
            out_img = np.zeros([out_height, out_width, 3], np.ubyte)
            # copy image data from blender
            out_ptr = out_img.ctypes.data_as(ct.POINTER(ct.c_ubyte))
            r = self.blender.outputBlendedImage(out_ptr, img_index)
            if DM_IMG_BLEND_RETURN_OK!=r:
                return
            # insert into cache
            out_qimage = QtGui.QImage(out_img, out_width, out_height, \
                                QtGui.QImage.Format_RGB888)
            out_qpixmap = QtGui.QPixmap.fromImage(out_qimage)
            out_mat_id, out_x_index, out_y_index = \
                self.items_to_blend[i]
            out_tile_info = (out_mat_id, out_x_index, out_y_index, 1)
            QtGui.QPixmapCache.insert(str(out_tile_info), out_qpixmap)
            pass
        # eset flags of blended tile items
        for item in items_to_process:
            item.setBlendingDoneFlag()
            pass
        # clear self.items_to_blend
        while self.items_to_blend:
            self.items_to_blend.pop()
            pass
        # update blended tile items
        for item in items_to_process:
            item.update(item.boundingRect())
            pass
        pass

    def thread_loadAllImages_addPixmapToCache(self, tile_info, tile_image):
        try:
            mat_id, x_index, y_index, pyramid_level = tile_info
        except ValueError:
            return
        if self.dm_pixmap_dict.has_key( (mat_id, x_index, y_index) ):
            tile_item = self.dm_pixmap_dict[ (mat_id, x_index, y_index) ]
            if (1==pyramid_level) and (True==DM_USE_BLENDER):
                # if this is the first tile, clear blender
                if not self.items_to_blend:
                    self.blender.clearAll()
                # register tile image into blender
                tile_image = tile_image.convertToFormat( \
                                    QtGui.QImage.Format_RGB888)
                sip_ptr = tile_image.constBits()
                c_void_pointer = ct.c_void_p(sip_ptr.__int__())
                r = self.blender.addNewImage(data_ptr = c_void_pointer, \
                                         width = tile_image.size().width(), \
                                         height = tile_image.size().height(), \
                                         crop_offset_x = tile_item.offset_x, \
                                         crop_offset_y = tile_item.offset_y, \
                                         tile_pos_x = tile_item.pos_x, \
                                         tile_pos_y = tile_item.pos_y, \
                                         tile_width = tile_item.width, \
                                         tile_height = tile_item.height)
                if DM_IMG_BLEND_RETURN_OK!=r:
                    return
                self.items_to_blend.append( (mat_id, x_index, y_index) )
                # blender post process
                self.blender_postProcess()
                pass
            else:
                # add tile image into cache if necesary
                if not QtGui.QPixmapCache.find(str(tile_info)):
                    pixmap = QtGui.QPixmap.fromImage(tile_image)
                    QtGui.QPixmapCache.insert(str(tile_info), pixmap)
                # update this tile item
                tile_item.update(tile_item.boundingRect())
                pass
            pass

    def setImageReviewTileRectVisible(self, isVisible):
        for rect_item in self.dm_rect_dict.values():
            if isVisible:
                rect_item.show()
            else:
                rect_item.hide()
        pass

    def updateSingleImageTile(self, mat_id, x_index, y_index, pyramid_level):
        if True == self.dm_pixmap_dict.has_key( (mat_id, x_index, y_index) ):
            tile_item = self.dm_pixmap_dict[(mat_id, x_index, y_index)]
            tile_item.loadPyramidTileIntoCache(pyramid_level = pyramid_level)
            tile_item.update(tile_item.boundingRect())
            pass

    def updateGroupImageTiles(self, tile_list, pyramid_level):
        for tile in tile_list:
            mat_id, x_index, y_index = tile
            self.updateSingleImageTile(mat_id, x_index, y_index, pyramid_level)


class dm_large_image_tile_viewer(QtGui.QFrame):
    """docstring for dm_large_image_tile_viewer"""
    def __init__(self):
        super(dm_large_image_tile_viewer, self).__init__()
        self.initUI()
        pass

    def initUI(self):
        # set frame style
        self.setFrameStyle(QtGui.QFrame.NoFrame)
        # init sub module
        self.image_scene_2 = QtGui.QGraphicsScene()
        self.image_view_2 = DmReviewGraphicsViewer(self.image_scene_2)

        self.image_view_2.initializeImageReviewSpace()

        self.btn_zoomIn_2 = QtGui.QPushButton('zoom in')
        self.btn_zoomOut_2 = QtGui.QPushButton('zoom out')
        self.lbl_mag_factor_2 = QtGui.QLabel()
        self.lbl_mag_factor_2.setMaximumHeight(10)
        self.btn_importTiles_2 = QtGui.QPushButton('import tiles')
        self.btn_removeTiles_2 = QtGui.QPushButton('remove tiles')
        self.chb_useRectOnImage_2 = QtGui.QCheckBox('grid on')
        self.chb_useRectOnImage_2.setChecked(False)
        self.chb_useRectOnImage_2.setEnabled(False)
        self.lbl_cursor_pos_x_2 = QtGui.QLabel()
        self.lbl_cursor_pos_x_2.setMaximumHeight(10)
        self.lbl_cursor_pos_y_2 = QtGui.QLabel()
        self.lbl_cursor_pos_y_2.setMaximumHeight(10)
        lbl_indicator_pos_x_2 = QtGui.QLabel('pixel x:')
        lbl_indicator_pos_x_2.setMaximumHeight(10)
        lbl_indicator_pos_y_2 = QtGui.QLabel('pixel y:')
        lbl_indicator_pos_y_2.setMaximumHeight(10)
        # self.lbl_cursor_pos_2.setMaximumHeight(10)
        # connect signals
        self.image_view_2.signal_mag_factor.connect(self.lbl_mag_factor_2.setText)
        self.image_view_2.signal_enable_use_rect.connect(self.setUseRectOnImageEnabled)
        self.image_view_2.signal_cursor_pos.connect(self.displayCursorPosOnScene)
        self.btn_zoomIn_2.clicked.connect(self.image_view_2.viewZoomIn)
        self.btn_zoomOut_2.clicked.connect(self.image_view_2.viewZoomOut)
        self.btn_importTiles_2.clicked.connect(self.image_view_2.createImageReviewTiles)
        self.btn_removeTiles_2.clicked.connect(self.image_view_2.clearImageReviewTiles)
        self.chb_useRectOnImage_2.stateChanged.connect(self.image_review_useRectOnImageChanged)
        # set layout
        hbox_layout = QtGui.QHBoxLayout()
        vbox1_layout = QtGui.QVBoxLayout()
        vbox2_layout = QtGui.QVBoxLayout()

        vbox1_layout.addWidget(self.image_view_2)

        vbox2_layout.addWidget(self.btn_zoomIn_2)
        vbox2_layout.addWidget(self.lbl_mag_factor_2)
        vbox2_layout.addWidget(self.btn_zoomOut_2)
        vbox2_layout.addWidget(self.btn_importTiles_2)
        vbox2_layout.addWidget(self.chb_useRectOnImage_2)
        vbox2_layout.addWidget(self.btn_removeTiles_2)
        vbox2_layout.addWidget(lbl_indicator_pos_x_2)
        vbox2_layout.addWidget(self.lbl_cursor_pos_x_2)
        vbox2_layout.addWidget(lbl_indicator_pos_y_2)
        vbox2_layout.addWidget(self.lbl_cursor_pos_y_2)

        hbox_layout.addLayout(vbox1_layout)
        hbox_layout.addLayout(vbox2_layout)

        self.setLayout(hbox_layout)

        # display
        self.showMaximized()
        if 'nt'==os.name:
            self.setFixedSize(self.geometry().width(), self.geometry().height())
        self.setWindowTitle('Large Image Tile Viewer')
        self.show()
        pass

    def setUseRectOnImageEnabled(self, isEnabled = False):
        if (True==isEnabled):
            self.chb_useRectOnImage_2.setEnabled(True)
        else:
            self.chb_useRectOnImage_2.setChecked(False)
            self.chb_useRectOnImage_2.setEnabled(False)

    def image_review_useRectOnImageChanged(self):
        isVisible =  self.chb_useRectOnImage_2.isChecked()
        self.image_view_2.setImageReviewTileRectVisible(isVisible)

    def displayCursorPosOnScene(self, cursor_position):
        if not isinstance(cursor_position, QtCore.QPointF):
            return
        self.lbl_cursor_pos_x_2.setText('%.2f'%cursor_position.x())
        self.lbl_cursor_pos_y_2.setText('%.2f'%cursor_position.y())

    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'Message', \
                                            'Are you sure to quit?', QtGui.QMessageBox.Yes | \
                                            QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.image_view_2.clearImageReviewTiles()
            event.accept()
        else:
            event.ignore()

def main_tester():
    app = QtGui.QApplication(sys.argv)
    if 'posix'==os.name:
        app.setStyle('cleanlooks')
    test_gui = dm_large_image_tile_viewer()
    sys.exit(app.exec_())
    pass

main_tester()

