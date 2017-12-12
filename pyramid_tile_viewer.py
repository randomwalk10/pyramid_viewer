import os, sys
from basic_values import *
from PyQt4 import QtCore, QtGui
import Queue
import glob
# define constant values
DM_BACKGROUND_GRID_SIZE = 10

DM_Z_VALUE_FOR_PIXMAP = 1.0

CYCLE_LEN = (1<<30)
# define classes
class DmPyramidTile(QtGui.QGraphicsPixmapItem):

    """Docstring for DmPyramidTile. """

    def __init__(self, img_load_queue = None, \
                 image_dir = "", mat_id = -1, \
                 x_index = 0, y_index = 0, pyramid_level = 0, \
                 tl_pos_x = 0., tl_pos_y = 0., \
                 tile_width = 0, tile_height = 0, \
                 byte_pos = 0, byte_size = 0):
        if not img_load_queue:
            raise ValueError('Error, img_load_queue is empty')
        super(DmPyramidTile, self).__init__(parent = None)
        # self.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.setTransformationMode(QtCore.Qt.FastTransformation)
        self.setZValue(DM_Z_VALUE_FOR_PIXMAP)
        self.setPos(tl_pos_x, tl_pos_y)
        # self.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations, True)

        self._img_load_queue = img_load_queue
        self._image_dir = image_dir
        self._mat_id = mat_id
        self._x_index = x_index
        self._y_index = y_index
        self._pyramid_level = pyramid_level
        self._tl_pos_x = tl_pos_x
        self._tl_pos_y = tl_pos_y
        self._tile_width = tile_width
        self._tile_height = tile_height
        self._byte_pos = byte_pos
        self._byte_size = byte_size
        self._path_to_tile = self._image_dir+os.path.sep+ \
                'pyramid_data_%d.bin'%(self._mat_id)

    def boundingRect(self):
        return QtCore.QRectF(0., 0., \
                             self._pyramid_level*self._tile_width, \
                             self._pyramid_level*self._tile_height)
        pass

    def paint(self, painter, option, widget):
        current_lod = option.levelOfDetailFromTransform( \
                                    painter.worldTransform() )
        # find path to tile
        if 1.0<=current_lod:
            # set pyramid level to 1
            pyramid_level = 1
        else:
            # calculate pyramid level
            pyramid_level = int(1/current_lod)
        # return if pyramid_level does not match
        if(pyramid_level!=self._pyramid_level):
            return
        tile_info = (self._mat_id, self._x_index, \
                            self._y_index, pyramid_level)
        # create pixmap
        pixmap = QtGui.QPixmap()
        if not QtGui.QPixmapCache.find(str(tile_info), pixmap):
            images_file = open(self._path_to_tile, "rb")
            images_file.seek(self._byte_pos)
            jpg_data = images_file.read(self._byte_size)
            tile_image = QtGui.QImage.fromData(jpg_data)
            pixmap = QtGui.QPixmap.fromImage(tile_image)
            QtGui.QPixmapCache.insert(str(tile_info), pixmap)
            images_file.close()
        # set pixmap
        painter.save()
        if 1.0>current_lod:
            painter.scale(1/current_lod, 1/current_lod)
        painter.drawPixmap(0, 0, pixmap)
        painter.restore()
        pass

class DmReviewGraphicsViewer(QtGui.QGraphicsView):
    """docstring for DmReviewGraphicsViewer"""

    signal_scene_pos = QtCore.pyqtSignal(QtCore.QPointF)
    signal_scene_rect = QtCore.pyqtSignal(QtCore.QRectF)
    signal_mag_factor = QtCore.pyqtSignal(str)
    signal_cursor_pos = QtCore.pyqtSignal(QtCore.QPointF)

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
        self.pf_pt_dict = {}
        self.img_load_queue = Queue.LifoQueue()#size infinite
        QtGui.QPixmapCache.setCacheLimit(MaxQPixmapCacheLimitInKB)
        QtGui.QPixmapCache.clear()
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
        qstr_image_dir = QtGui.QFileDialog.getExistingDirectory( \
                                parent = self, caption = 'Open Directory', \
                                directory = current_dir )
        if not qstr_image_dir:
            QtGui.QMessageBox.about(self, 'Error', 'Invalid directory')
            return
        str_pr_image_dir = str(qstr_image_dir)
        if not os.path.exists(str_pr_image_dir):
            QtGui.QMessageBox.about(self, 'Error', \
                                    'Failed to find pyramid tiles')
            return
        # get the list of mat_id
        pr_info_filename_list = glob.glob( \
                        str_pr_image_dir+os.path.sep+'pyramid_info_*.txt')
        mat_id_list = []
        for filename in pr_info_filename_list:
            start_index = filename.find('pyramid_info_')+len('pyramid_info_')
            end_index = filename.find('.txt')
            try:
                mat_id = int(filename[start_index:end_index])
                mat_id_list.append(mat_id)
            except ValueError:
                continue
        if not mat_id_list:
            QtGui.QMessageBox.about(self, 'Error', \
                                    'Failed to find pyramid info files')
            return
        # clear image review tiles
        self.clearImageReviewTiles()
        # get tile_list and create DmPixmapItem
        for mat_id in mat_id_list:
            # parse align info
            path_to_pyramid_info = str_pr_image_dir+os.path.sep+ \
                'pyramid_info_'+str(mat_id)+'.txt'
            if not os.path.exists(path_to_pyramid_info):
                QtGui.QMessageBox.about(self, 'Error', \
                                        'Failed to find '+ \
                                        'pyramid_info_'+ \
                                        str(mat_id)+'.txt')
                return
            pyramid_info_file = open(path_to_pyramid_info, 'r')
            pyramid_info_lines = pyramid_info_file.read().splitlines()
            # get tile num
            tile_num_index = 0
            for i in range(len(pyramid_info_lines)):
                if '[tile_num]' == pyramid_info_lines[i]:
                    tile_num_index = i + 1
                    break
            if(tile_num_index==0):
                QtGui.QMessageBox.about(self, 'Error', \
                                        'Failed to find [tile_num]')
                return
            str_max_tile_num = pyramid_info_lines[tile_num_index]
            int_max_tile_num = int(str_max_tile_num)
            # get data size list
            tile_pos_index = 0
            for i in range(len(pyramid_info_lines)):
                if '[tile_data_size]' == \
                        pyramid_info_lines[i]:
                    tile_pos_index = i + 1
                    break
            if(tile_pos_index==0):
                QtGui.QMessageBox.about(self, 'Error', \
                        'Failed to find [tile_data_size]')
                return
            tile_map = {}
            for i in range(tile_pos_index, tile_pos_index+int_max_tile_num):
                str_tile_index_x, str_tile_index_y, str_tile_pyramid_level, \
                    str_tile_data_pos_cycle, str_tile_data_pos_mod, \
                    str_tile_data_size = pyramid_info_lines[i].split(',')
                int_tile_data_pos = int(str_tile_data_pos_cycle)*CYCLE_LEN+ \
                                        int(str_tile_data_pos_mod)
                tile_map[ ( \
                                int(str_tile_index_x), \
                                int(str_tile_index_y), \
                                int(str_tile_pyramid_level) \
                                    ) ] = \
                                    ( 0,0,0,0, \
                                     int_tile_data_pos, \
                                     int(str_tile_data_size) )
            # get pyramid tile list
            tile_pos_index = 0
            for i in range(len(pyramid_info_lines)):
                if '[pyramid_tile_pos_scene_topleft]' == \
                        pyramid_info_lines[i]:
                    tile_pos_index = i + 1
                    break
            if(tile_pos_index==0):
                QtGui.QMessageBox.about(self, 'Error', \
                        'Failed to find [pyramid_tile_pos_scene_topleft]')
                return
            for i in range(tile_pos_index, tile_pos_index+int_max_tile_num):
                str_tile_index_x, str_tile_index_y, str_tile_pyramid_level, \
                    str_tile_pos_x, str_tile_pos_y, \
                    str_tile_width, str_tile_height = \
                    pyramid_info_lines[i].split(',')
                tile_info = tile_map[( \
                                      int(str_tile_index_x), \
                                      int(str_tile_index_y), \
                                      int(str_tile_pyramid_level) )]
                tile_map[ ( \
                                int(str_tile_index_x), \
                                int(str_tile_index_y), \
                                int(str_tile_pyramid_level) \
                                    ) ] = \
                                    ( \
                                     float(str_tile_pos_x), \
                                     float(str_tile_pos_y), \
                                     int(str_tile_width), \
                                     int(str_tile_height), \
                                     tile_info[4], \
                                     tile_info[5] )
            tile_loading_progress = QtGui.QProgressDialog( \
                'tile loading for mat[%d] is started'%mat_id, \
                'cancel', 0, len(tile_map), self)
            tile_loading_progress.setWindowTitle('tile loading in progress')
            tile_loading_progress.setFixedSize(400, 150)
            tile_loading_progress.setValue(0)

            for tile in tile_map.keys():
                # load pixmap
                tile_info = tile_map[tile]
                tile_item = DmPyramidTile( \
                        img_load_queue = self.img_load_queue, \
                        image_dir = str_pr_image_dir, \
                        mat_id = mat_id, x_index = tile[0], \
                        y_index = tile[1], pyramid_level = tile[2], \
                        tl_pos_x = tile_info[0], tl_pos_y = tile_info[1], \
                        tile_width = tile_info[2], \
                        tile_height = tile_info[3], \
                        byte_pos = tile_info[4], \
                        byte_size = tile_info[5]
                                          )
                self._scene.addItem(tile_item)
                self.dm_pixmap_dict[ \
                            (mat_id, tile[0], tile[1], tile[2]) \
                                    ] = tile_item
                # update tile loading progress
                tile_loading_progress.setLabelText( \
                        'tile[%d,%d,%d,%d] is loaded.'%(mat_id, tile[0], \
                                                     tile[1], tile[2]) )
                tile_loading_progress.setValue( \
                        tile_loading_progress.value()+1 )
        pass

    def clearImageReviewTiles(self):
        if not self.dm_pixmap_dict:
            # cleanup queue and cache
            while not self.img_load_queue.empty():
                self.img_load_queue.get(False)
            QtGui.QPixmapCache.clear()
            return
        # clear cache
        QtGui.QPixmapCache.clear()
        # remove all items
        for tile_item in self.dm_pixmap_dict.values():
            self._scene.removeItem(tile_item)
        self.dm_pixmap_dict.clear()
        # cleanup queue and cache
        while not self.img_load_queue.empty():
            self.img_load_queue.get(False)
        QtGui.QPixmapCache.clear()
        pass

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
        self.image_view_2.signal_cursor_pos.connect(self.displayCursorPosOnScene)
        self.btn_zoomIn_2.clicked.connect(self.image_view_2.viewZoomIn)
        self.btn_zoomOut_2.clicked.connect(self.image_view_2.viewZoomOut)
        self.btn_importTiles_2.clicked.connect(self.image_view_2.createImageReviewTiles)
        self.btn_removeTiles_2.clicked.connect(self.image_view_2.clearImageReviewTiles)
        # set layout
        hbox_layout = QtGui.QHBoxLayout()
        vbox1_layout = QtGui.QVBoxLayout()
        vbox2_layout = QtGui.QVBoxLayout()

        vbox1_layout.addWidget(self.image_view_2)

        vbox2_layout.addWidget(self.btn_zoomIn_2)
        vbox2_layout.addWidget(self.lbl_mag_factor_2)
        vbox2_layout.addWidget(self.btn_zoomOut_2)
        vbox2_layout.addWidget(self.btn_importTiles_2)
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

if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    if 'posix'==os.name:
        app.setStyle('cleanlooks')
    test_gui = dm_large_image_tile_viewer()
    sys.exit(app.exec_())
    pass
