import os
import sys
from   PyQt5.Qt                 import Qt
from   PyQt5.QtWidgets          import QButtonGroup, QLabel, QCheckBox, QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout, QProgressBar, QListWidget, QListWidgetItem, QWidget, QApplication, QAbstractItemView, QSlider, QSpinBox, QDoubleSpinBox, QRadioButton, QFrame
from   PyQt5.QtCore             import QSize, QByteArray
from   PyQt5.QtGui              import QIcon, QPixmap
from   videoProcessor           import *
from   multiprocessing          import Process

video_ext = ["MOV", "WMV", "AVI", "MKV", "MPEG", "MP4"]
image_ext = ["PNG", "JPG", "JPEG"]


class VideoConvertWidget(QWidget):
	def __init__(self):
		super().__init__()
		self.runState          = False
		self.currentProcessor  = None
		self.layout            = QVBoxLayout()

		self.layout.addLayout (self.listUISetup())
		self.layout.addLayout (self.colorTuneUISetup())
		self.layout.addLayout (self.executeUISetup())
		self.setLayout(self.layout)
		self.signalSetup()
		self.resize(500,250)
		self.setWindowTitle ("Video Converter V2")
		self.setWindowIcon(PorotechIcon().icon);

	def listUISetup(self):
		self.float_layout      = QGridLayout()
		self.task_listwidget   = TaskListView()
		self.background_label  = QLabel(f"Drag / Drop media files\n\nVideo: {', '.join([e.lower() for e in video_ext])}\nImage: {', '.join([e.lower() for e in image_ext])}")
		self.delete_button     = QPushButton("clear")

		self.delete_button.setFixedSize(45, 25)
		self.background_label.setAlignment(Qt.AlignCenter)
		self.background_label.setStyleSheet("font-size: 20px; color:#aaa;")
		self.delete_button.clicked.connect(lambda : self.task_listwidget.clear())
		self.task_listwidget.setDragDropMode(QAbstractItemView.DragDrop)
		self.task_listwidget.setMinimumHeight(200)

		self.float_layout.addWidget (self.background_label, 0, 0, 4, 4)
		self.float_layout.addWidget (self.task_listwidget,  0, 0, 4, 4)
		self.float_layout.addWidget (self.delete_button,    3, 3, 1, 1)
		return self.float_layout

	def colorTuneUISetup(self):
		self.colorTune_widget   = RGBTuneWidget()
		self.colorTune_layout   = QGridLayout()
		self.colorTune_layout.addWidget (self.colorTune_widget,   0, 0, 1, 1)
		return self.colorTune_layout
		
	def executeUISetup(self):
		self.execute_layout     = QHBoxLayout()
		self.execute_button     = QPushButton("execute")
		self.execute_layout.addStretch()
		self.execute_layout.addWidget (self.execute_button)
		self.execute_layout.addStretch()
		return self.execute_layout

	def signalSetup(self):
		self.execute_button.clicked.connect(self.executeProcess)

	def closeEvent(self, event):
		self.task_listwidget.model().modelReset.disconnect()
		event.accept()

	def executeProcess(self):
		self.setRunState(not(self.runState))
		
		if self.runState:
			arg = self.colorTune_widget.value()
			p   = Process(target = self.processFile(arg))
			p.start()
			p.join()

		else:
			if self.currentProcessor:
				self.currentProcessor.run = False

	def processFile(self, arg):

		for row in range(self.task_listwidget.count()):
			if not(self.runState):break

			QCoreApplication.processEvents()
			item                  = self.task_listwidget.item(row)
			widget                = self.task_listwidget.itemWidget(item)
			in_name               = widget.filePath
			procrssor             = None 

			if in_name.split(".")[-1].upper() in video_ext:
				procrssor = VideoProcessor(self)
				debugPrint("Process video %s" % in_name)

			if in_name.split(".")[-1].upper() in image_ext:
				procrssor = ImageProcessor(self)
				debugPrint("Process image %s" % in_name)

			if procrssor:
				self.currentProcessor = procrssor
				procrssor.percentage.connect(lambda value : widget.setProgress(int(value)))
				procrssor.process(in_name, **arg)
			else:
				debugPrint("Invalid item %s" % in_name)

		self.currentProcessor = None
		self.setRunState(False)

	def setRunState(self, status):
		self.runState = status
		self.execute_button.setText("cancel" if status else "execute")
		_ = [widget.setEnabled(not(self.runState)) for widget in [
			self.task_listwidget, 
			self.colorTune_widget,
			self.delete_button,
		]]


class TaskListWidget(QWidget):
	remove = pyqtSignal(object)
	def __init__(self, path, item=None, parent=None):
		super(TaskListWidget, self).__init__(parent)
		self.item           = item
		self.fileName_label = QLabel(path.split("/")[-1])
		self.process_label  = QLabel("0%")
		self.progress_bar   = QProgressBar()
		self.delete_button  = QPushButton("x")

		self.filePath       = path
		self.progress       = 0
		self.layout         = QGridLayout()
		self.delete_button.clicked.connect(lambda : self.remove.emit(self.item))

		self.layout.addWidget (self.fileName_label, 0, 0, 1, 3)
		self.layout.addWidget (self.progress_bar,   1, 0, 1, 3)
		self.layout.addWidget (self.process_label,  0, 3, 2, 1)
		self.layout.addWidget (self.delete_button,  0, 4, 2, 1)	
			

		self.process_label.setFixedSize(35,35)
		self.fileName_label.setFixedHeight(15)
		self.progress_bar.setFixedHeight(3)
		self.delete_button.setFixedSize(25,25)

		self.progress_bar.setTextVisible(False)
		self.setLayout(self.layout)

	def setProgress(self, progress:int):
		self.process_label.setText(f"{progress:d}%")
		self.progress_bar.setValue(progress)

class TaskListView(QListWidget):
	def __init__(self, parent=None):
		super(TaskListView, self).__init__(parent)
		self.setAcceptDrops(True)
		self.setIconSize(QSize(72, 72))
		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.viewport().setAutoFillBackground( False )
		self.itemChanged.connect(lambda : self.viewport().setAutoFillBackground( self.count() > 0 ))
		self.model().rowsRemoved.connect(lambda: self.viewport().setAutoFillBackground( self.count() > 0 ))
		self.model().modelReset.connect(lambda: self.viewport().setAutoFillBackground( self.count() > 0 ))


	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls:
			event.accept()
		else:
			event.ignore()

	def dragMoveEvent(self, event):
		if event.mimeData().hasUrls:
			event.setDropAction(Qt.CopyAction)
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, event):
		if event.mimeData().hasUrls:
			event.setDropAction(Qt.CopyAction)
			event.accept()
			links = []
			for url in event.mimeData().urls():
				links.append(str(url.toLocalFile()))
			print (links)
			self.addVideoItems(links)
		else:
			event.ignore()


	def addVideoItems(self, videoPath_list):
		for videoPath in videoPath_list:
			if (videoPath.split(".")[-1].upper() in video_ext) or (videoPath.split(".")[-1].upper() in image_ext):
				debugPrint("add media %s" % videoPath)
				item        = QListWidgetItem(self)
				row         = TaskListWidget(videoPath, item)
				row.remove.connect(lambda  i: self.takeItem (self.row(i)))
				self.addItem(item)
				item.setSizeHint(row.minimumSizeHint())
				self.setItemWidget(item, row)
			else:
				debugPrint("add media error%s" % videoPath)

class RGBTuneWidget(QWidget):
	value_changed = pyqtSignal()
	def __init__(self):
		super().__init__()
		self.r_chtw = ChannelTuneWidget("Red\nChannel")
		self.g_chtw = ChannelTuneWidget("Green\nChannel")
		self.b_chtw = ChannelTuneWidget("Blue\nChannel")
		self.frame  = QVBoxLayout()
		self.frame.addWidget(self.r_chtw)
		self.frame.addWidget(QHLine())
		self.frame.addWidget(self.g_chtw)
		self.frame.addWidget(QHLine())
		self.frame.addWidget(self.b_chtw)
		self.setLayout(self.frame)

	def value(self):
		r_value = self.r_chtw.value()
		g_value = self.g_chtw.value()
		b_value = self.b_chtw.value()
		return dict(
			r_flip       = r_value["flip"],
			r_mirror     = r_value["mirror"],
			r_invert     = r_value["invert"],
			r_brightness = r_value["brightness"],
			r_offset     = r_value["offset"],
			r_shift_x    = r_value["shift_x"],
			r_shift_y    = r_value["shift_y"],
			g_flip       = g_value["flip"],
			g_mirror     = g_value["mirror"],
			g_invert     = g_value["invert"],
			g_brightness = g_value["brightness"],
			g_offset     = g_value["offset"],
			g_shift_x    = g_value["shift_x"],
			g_shift_y    = g_value["shift_y"],
			b_flip       = b_value["flip"],
			b_mirror     = b_value["mirror"],
			b_invert     = b_value["invert"],
			b_brightness = b_value["brightness"],
			b_offset     = b_value["offset"],
			b_shift_x    = b_value["shift_x"],
			b_shift_y    = b_value["shift_y"],
		)

class ChannelTuneWidget(QWidget):
	value_changed = pyqtSignal()

	def __init__(self, title = ""):
		super().__init__()
		self._titleFrame        = QVBoxLayout()
		self._checkFrame        = QVBoxLayout() 
		self._spinComboFrame    = QVBoxLayout() 
		self._frame             = QHBoxLayout()
		self._title             = QLabel(title)
		self._flipCheck         = QCheckBox("Flip Channel")
		self._mirrorCheck       = QCheckBox("Mirror Channel")
		self._invertCheck       = QCheckBox("Invert Channel")
		
		self._channelBrightness = SlideSpinCombo("Brightness",   0, 20, 10, 1, 0)
		self._channelOffest     = SlideSpinCombo("Offest",       0, 20, 10, 1, 0)
		self._channelShiftX     = SlideSpinCombo("Shift X",    -20, 20,  0, 1, 0)
		self._channelShiftY     = SlideSpinCombo("Shift Y",    -20, 20,  0, 1, 0)

		self._titleFrame.addWidget(self._title)
		self._checkFrame.addWidget(self._flipCheck)
		self._checkFrame.addWidget(self._mirrorCheck)
		self._checkFrame.addWidget(self._invertCheck)

		self._spinComboFrame.addWidget(self._channelBrightness)
		self._spinComboFrame.addWidget(self._channelOffest)
		self._spinComboFrame.addWidget(self._channelShiftX)
		self._spinComboFrame.addWidget(self._channelShiftY)

		self._frame.addLayout(self._titleFrame)
		self._frame.addLayout(self._checkFrame)
		self._frame.addLayout(self._spinComboFrame)
		self.setLayout(self._frame)
		self._title.setFixedWidth(60)
		self._spinComboFrame.setContentsMargins (0,0,0,0)
		self._checkFrame.setContentsMargins     (0,0,0,0)
		self._frame.setContentsMargins          (0,0,0,0)

	def value(self):
		return dict(
			flip       = self._flipCheck.isChecked(),
			mirror     = self._mirrorCheck.isChecked(),
			invert     = self._invertCheck.isChecked(),
			brightness = self._channelBrightness.value(),
			offset     = self._channelOffest.value(),
			shift_x    = self._channelShiftX.value(),
			shift_y    = self._channelShiftY.value(),
		)

class SlideSpinCombo(QWidget):
	value_changed = pyqtSignal(float)
	def __init__(self, title:str = "", min_value:float = 0, max_value:float = 100, default_value = 0, step:float = 1 , decimal:int = 2, ):
		super().__init__()
		self._value   = default_value
		self._label   = QLabel(title)
		self._spinbox = QDoubleSpinBox()
		self._slide   = QSlider()
		self._reset   = QPushButton("reset")
		self._grid    = QGridLayout()

		self._slide.setOrientation(Qt.Horizontal)
		self._slide.setMaximum (max_value)
		self._slide.setMinimum  (min_value)
		self._slide.setPageStep (step)
		self._slide.setSliderPosition (default_value)
		self._spinbox.setRange(min_value, max_value)
		self._spinbox.setSingleStep (step)
		self._spinbox.setDecimals (decimal)
		self._spinbox.setValue(default_value)

		self._slide.valueChanged.connect(   lambda val: self.value_changed.emit(round(val, decimal)))
		self._spinbox.valueChanged.connect( lambda val: self.value_changed.emit(round(val, decimal)))
		self._reset.clicked.connect(        lambda    : self.value_changed.emit(default_value))
		self.value_changed.connect(        lambda val : self.setValue(val))
		self._grid.addWidget(self._label,   0, 0, 1, 1)
		self._grid.addWidget(self._slide,   0, 1, 1, 1)
		self._grid.addWidget(self._spinbox, 0, 2, 1, 1)
		self._grid.addWidget(self._reset,   0, 3, 1, 1)
		self._grid.setColumnMinimumWidth (0, 60)
		self._grid.setColumnMinimumWidth (2, 70)
		self._grid.setContentsMargins    (5,0,0,0)
		self.setLayout(self._grid)

	def setValue(self, val):

		self.blockSignals(True)
		self._value = val
		self._slide.setValue(int(val))
		self._spinbox.setValue(val)
		self.blockSignals(False)

	def value(self):
		return self._value
	
class QLine(QFrame):
	def __init__(self):
		super(QLine, self).__init__()
		self.setFrameShape(QFrame.VLine)
		self.setFrameShadow(QFrame.Plain)
		theme = """
			QFrame {
				color: rgba(150, 150, 150, 200);
			}
		"""
		self.setStyleSheet(theme)

class QVLine(QLine):
	def __init__(self):
		super(QVLine, self).__init__()
		self.setFrameShape(QFrame.VLine)

class QHLine(QLine):
	def __init__(self):
		super(QHLine, self).__init__()
		self.setFrameShape(QFrame.HLine)	

class PorotechIcon(object):
	def __init__(self):
		super().__init__()
		self.icon = self.iconFromBase64(b"iVBORw0KGgoAAAANSUhEUgAAABsAAAAbCAYAAACN1PRVAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAA69JREFUSIm1lttPXFUUxn9rnzMzzHCGywwEKNMEG5DpcGs0EsHEWh9Ka7y96Etj4oO26QvR9EG03q2miZWkqUlN9E/QGG+kIVZEglQzWqBAUy8hKFQHGG0bQgszzPIBZsQRa4Dhe9vfWfv8ztrZ59tbVJX1Klz92ZuqPA5MI/p1ypf3KaGqMz92VS/cbJ5ZNwlQEKAEiKDyhJQ7TxnP1cnww98fq390zMkpLEsJ8dlhoERFjyYS18fChy/duzWwAs+3iJSnh+L3/EF5/pnwK5PtOYG58uafw9aQwv0Uej9AmALAMnHdUVSB4kI5mQ2UjWyQbO3Z86U9VVzwtAkHH8Jt3bXqUVIrvPsuHQqezRksrZ0vTrWopZ+gBMVtx7Q6MIFttieW7J0/P8LVXGyQjC6+WjkgmAcJ+vq1NujCNs1AhdtOdkCOO0sr/GHyGZTjq6z4wjU7lNPO0nJm7E7gdwCRuZjb+81oUej9ti3pDKC+q7/Ddo8eEJOoYzkE3tuSzgBcnsHvxCTqV0AArVsGU7HGsqwyu6eq4XVVsdJOYan7hduj0cRmYXZh158mob3psWUkaaMclOVQBSB+JdEJTG8WZlLjQdttdq+yLhtFfvvHFy2mdm0WBGBbVlOW9asR0T4AY5j3FnKuoJKWXMBqJNXsFR0A5lesAemra9znBPRlcdEA+EBnC1Nz26t6xm9sFPTshcZiUZkA/EswF1MGL6vpMMnSwOfiIrQMApCSa8Z5fpONnQD8ABY42wSne9f5fnNPT09SkdPpKrF0omiHtEwcbGjdCKV7pKE1YqSG1ZtMpRNWsvGn+2o88wve8y6HmfxyrRWhDIgb5IHKd4YH1gPCmI+B4KISiy4xnoDkG43DdyuqmbgaP1DfbPulH7DTk/P89OeXS7dvzn2Cl6Lz/8GA4ab8xTw5ci7J3hto5jxTSExbqdbHai9EM52l9cuhhnYRTgIYm+miKrVAgkDc8vOWFBBdEteozzFXrjuJgNFUUypg1VpePQoEFpX4QJKkLq8MIO17I4On0u//VxBPHq5/UlXeLr6FEbG4LVNYJqNiUQcgAXrJYzeAeOiVoGR+3lnVoZEliYAcWQ2CNe4godMj7/pKdb9YlGZMS2JiEVlrBXWRO0AzwVAiEgzZ7M8GrQkDCL428sW8TyOqcgyYweEH/k7vLBo+TcqQwizocbcuRCK3Dp1dq/T/z7NTNZ6FAl9byk61IXInyjYJ6kW8UocSU/jKOPqRp2Suj6qbB8FfcZpVXdo/DbkAAAAASUVORK5CYII=")

	def iconFromBase64(self, base64):
		pixmap = QPixmap()
		pixmap.loadFromData(QByteArray.fromBase64(base64))
		icon = QIcon(pixmap)
		return icon
		
if __name__ == '__main__':
	app    = QApplication(sys.argv)
	window = VideoConvertWidget()
	# window.setStyleSheet("QWidget{font-size: 11px;}")
	window.show()
	sys.exit(app.exec_())