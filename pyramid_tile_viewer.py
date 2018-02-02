# import
import os, sys
from basic_values import *
from PyQt4 import QtCore, QtGui
import Queue
import glob
import struct, time
# const value
MAX_LAYER_NUM = 20
TILE_WIDTH = 256
TILE_HEIGHT = 256
# function
def readTile(file_handle):
    layer_index, = struct.unpack('h', file_handle.read(2))
    col_index, = struct.unpack('i', file_handle.read(4))
    row_index, = struct.unpack('i', file_handle.read(4))
    byte_pos, = struct.unpack('q', file_handle.read(8))
    byte_size, = struct.unpack('i', file_handle.read(4))
    return layer_index, col_index, row_index, byte_pos, byte_size
# define classes
class DmPyramidTile(QtGui.QGraphicsPixmapItem):

    """Docstring for DmPyramidTile. """

    def __init__(self, image_filepath = "", \
                 x_index = 0, y_index = 0, pyramid_level = 0, \
                 tl_pos_x = 0., tl_pos_y = 0., \
                 tile_width = 0, tile_height = 0, \
                 byte_pos = 0, byte_size = 0):
        super(DmPyramidTile, self).__init__(parent = None)
        # self.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.setTransformationMode(QtCore.Qt.FastTransformation)
        self.setZValue(DM_Z_VALUE_FOR_PIXMAP)
        self.setPos(tl_pos_x, tl_pos_y)
        # self.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations, True)

        self._path_to_tile = image_filepath
        self._x_index = x_index
        self._y_index = y_index
        self._pyramid_level = pyramid_level
        self._tl_pos_x = tl_pos_x
        self._tl_pos_y = tl_pos_y
        self._tile_width = tile_width
        self._tile_height = tile_height
        self._byte_pos = byte_pos
        self._byte_size = byte_size

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
            temp_level = MAX_PYRAMID_LEVEL
            while temp_level>pyramid_level:
                temp_level/=2.
                pass
            pyramid_level = temp_level
            pass

        # return if pyramid_level does not match
        if(pyramid_level!=self._pyramid_level):
            return
        tile_info = (self._x_index, self._y_index, pyramid_level)
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
            # painter.scale(1/current_lod, 1/current_lod)
            painter.scale(pyramid_level, pyramid_level)
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
        if( ZOOM_IN_FACTOR*(self.view_mag_factor) <= float(self.max_zoom_in_level) ):
            self.view_mag_factor*=ZOOM_IN_FACTOR
            self.signal_mag_factor.emit('%.5fX'%(self.base_mag_factor*self.view_mag_factor))
            self.scale(ZOOM_IN_FACTOR, ZOOM_IN_FACTOR)
            pass
        pass

    def viewZoomOut(self):
        if( ZOOM_OUT_FACTOR*(self.view_mag_factor) >= (1./float(self.max_zoom_out_level)) ):
            self.view_mag_factor*=ZOOM_OUT_FACTOR
            self.signal_mag_factor.emit('%.5fX'%(self.base_mag_factor*self.view_mag_factor))
            self.scale(ZOOM_OUT_FACTOR, ZOOM_OUT_FACTOR)
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

    def createImageReviewTilesFromDM(self):
        # get image filepath
        qstr_image_filename = QtGui.QFileDialog.getOpenFileName( \
                                parent = self, caption = 'Open File', \
                                directory = current_dir, \
                                filter = "dmetrix file (*.dmetrix)")
        str_image_file_name = str(qstr_image_filename);
        if not os.path.exists(str_image_file_name):
            QtGui.QMessageBox.about(self, 'Error', 'Invalid filepath')
            return
        # clear image review tiles
        self.clearImageReviewTiles()
        # open file
        start_t = time.time()
        dm_file = open(str_image_file_name, 'rb')
        # parse info
        company_name = dm_file.read(7)
        print "Company name: "+company_name
        isEncrypted = dm_file.read(1)
        print "Is encrypted? "+isEncrypted
        equipNo = dm_file.read(10)
        print "Equipment NO: "+equipNo
        timeinfo = dm_file.read(8)
        print "Time stamp: "+timeinfo
        total_width, = struct.unpack('i', dm_file.read(4))
        print "Total width:", total_width
        total_height, = struct.unpack('i', dm_file.read(4))
        print "Total height:", total_height
        header_size, = struct.unpack('i', dm_file.read(4))
        print "Header size:", header_size
        file_size, = struct.unpack('q', dm_file.read(8))
        print "File size:", file_size
        max_layer, = struct.unpack('h', dm_file.read(2))
        print "max layer:", max_layer
        umPerPixelX, = struct.unpack('d', dm_file.read(8))
        print "umPerPixelX:", umPerPixelX
        umPerPixelY, = struct.unpack('d', dm_file.read(8))
        print "umPerPixelY:", umPerPixelY
        objMag, = struct.unpack('i', dm_file.read(4))
        print "objMag:", objMag
        layer_info_map = {}
        # layer info
        for layer_index in range(MAX_LAYER_NUM):
            i, = struct.unpack('h', dm_file.read(2))
            col_num, = struct.unpack('i', dm_file.read(4))
            row_num, = struct.unpack('i', dm_file.read(4))
            byte_pos, = struct.unpack('i', dm_file.read(4))
            if col_num >= 0 and row_num >= 0:
                layer_info_map[i] = (i, col_num, row_num, byte_pos)
                pass
            print "layer_index %d, col_num %d, row_num %d, byte_pos %d" % (
                    i, col_num, row_num, byte_pos)
            pass
        print "valid layers: ", layer_info_map.keys()
        # tile info
        label_layer_index, label_col_index, label_row_index, \
            label_byte_pos, label_byte_size = readTile(dm_file)
        print "label tile [%d, %d, %d, %d, %d]" % (
                    label_layer_index, label_col_index,
                    label_row_index, label_byte_pos,
                    label_byte_size)
        thumb_layer_index, thumb_col_index, thumb_row_index, \
            thumb_byte_pos, thumb_byte_size = readTile(dm_file)
        print "thumb tile [%d, %d, %d, %d, %d]" % (
                    thumb_layer_index, thumb_col_index,
                    thumb_row_index, thumb_byte_pos,
                    thumb_byte_size)
        keys_list = layer_info_map.keys()
        keys_list.sort(reverse=True)
        tile_info_map = {}
        pyramid_level = 1
        for layer_index in keys_list:
            layer_info = layer_info_map[layer_index]
            tile_num = (layer_info[1] + 1) * (layer_info[2] + 1)
            dm_file.seek(layer_info[3])
            print "******layer index %d with tile num %d and tile info \
                    starting at %d" % (layer_index, tile_num, layer_info[3])
            for i in range(tile_num):
                i, col_index, row_index, byte_pos, byte_size = \
                        readTile(dm_file)
                tl_pos_x = TILE_WIDTH*pyramid_level*col_index
                tl_pos_y = TILE_HEIGHT*pyramid_level*row_index
                tile_item = DmPyramidTile(
                        image_filepath = str_image_file_name,
                        x_index = col_index, y_index = row_index,
                        pyramid_level = pyramid_level,
                        tl_pos_x = tl_pos_x,
                        tl_pos_y = tl_pos_y,
                        tile_width = TILE_WIDTH,
                        tile_height = TILE_HEIGHT,
                        byte_pos = byte_pos,
                        byte_size = byte_size)
                self._scene.addItem(tile_item)
                self.dm_pixmap_dict[(
                    col_index, row_index, pyramid_level)] = \
                    tile_item
                pass
            pyramid_level *= 2
            pass
        #update objMag
        self.updateBaseMagFactor(objMag)
        # measure time elapsed
        end_t = time.time()
        elapsed_t = end_t - start_t
        print "time elapsed %f sec" % elapsed_t
        pass

    def clearImageReviewTiles(self):
        if not self.dm_pixmap_dict:
            # cleanup cache
            QtGui.QPixmapCache.clear()
            return
        # clear cache
        QtGui.QPixmapCache.clear()
        # remove all items
        for tile_item in self.dm_pixmap_dict.values():
            self._scene.removeItem(tile_item)
        self.dm_pixmap_dict.clear()
        # cleanup cache
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
        self.btn_importTiles_2.clicked.connect(self.image_view_2.createImageReviewTilesFromDM)
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
