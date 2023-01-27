import os
import sys
from   PyQt5.Qt                 import Qt
from   PyQt5.QtWidgets          import QButtonGroup, QLabel, QCheckBox, QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout, QProgressBar, QListWidget, QListWidgetItem, QWidget, QApplication, QAbstractItemView, QSlider, QSpinBox, QDoubleSpinBox, QRadioButton
from   PyQt5.QtCore             import QSize

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
		self.layout.addLayout (self.geometryUISetup())
		self.layout.addLayout (self.miscUISetup())
		self.layout.addLayout (self.colorTuneUISetup())
		self.layout.addLayout (self.executeUISetup())
		self.setLayout(self.layout)
		self.signalSetup()
		self.resize(500,300)

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

	def geometryUISetup(self):
		self.geometry_layout    = QGridLayout()
		self.rotation_0_radio   = QRadioButton("0   deg")
		self.rotation_90_radio  = QRadioButton("90  deg")
		self.rotation_180_radio = QRadioButton("180 deg")
		self.rotation_270_radio = QRadioButton("270 deg")
		self.rotation_group     = QButtonGroup()
		for radio in [self.rotation_0_radio, self.rotation_90_radio, self.rotation_180_radio, self.rotation_270_radio]:
			self.rotation_group.addButton (radio)

		self.rotation_0_radio.setChecked(True)
		self.geometry_layout.addWidget(self.rotation_0_radio,   0, 0, 1, 1)
		self.geometry_layout.addWidget(self.rotation_90_radio,  0, 1, 1, 1)
		self.geometry_layout.addWidget(self.rotation_180_radio, 0, 2, 1, 1)
		self.geometry_layout.addWidget(self.rotation_270_radio, 0, 3, 1, 1)
		return self.geometry_layout

	def miscUISetup(self):
		self.misc_layout        = QGridLayout()
		self.mirrorVideo_check  = QCheckBox("mirrir video")
		self.binaryVideo_check  = QCheckBox("video binary")
		self.groupPixel_check   = QCheckBox("pixel grouping")
		self.colorInvert_check  = QCheckBox("color invert")
		uiFixedHeight           = 35

		for index, widget in enumerate([self.mirrorVideo_check, self.binaryVideo_check, self.groupPixel_check, self.colorInvert_check]):
			self.misc_layout.addWidget (widget,  0, index, 1, 1)
			widget.setFixedHeight(uiFixedHeight)

		self.setWindowTitle("Batch Video Converter")

		return self.misc_layout


	def colorTuneUISetup(self):
		self.colorTune_layout   = QGridLayout()
		self.colorTune_check    = QCheckBox("color tuning")
		self.colorTune_widget   = ColorTuneWidget()
		self.colorTune_layout.addWidget (self.colorTune_check,   0, 0, 1, 5)
		self.colorTune_layout.addWidget (self.colorTune_widget,  1, 0, 1, 5)
		return self.colorTune_layout
		
	def executeUISetup(self):
		self.execute_layout     = QHBoxLayout()
		self.execute_button     = QPushButton("execute")
		self.execute_layout.addStretch()
		self.execute_layout.addWidget (self.execute_button)
		self.execute_layout.addStretch()
		return self.execute_layout

	def signalSetup(self):
		self.colorTune_widget.setVisible(False)
		self.colorTune_check.stateChanged.connect(lambda val : self.colorTune_widget.setVisible(val))
		self.colorTune_check.stateChanged.connect(lambda val : self.colorTune_widget.reset() if val else lambda:None)
		self.execute_button.clicked.connect(self.executeProcess)


	def closeEvent(self, event):
		self.task_listwidget.model().modelReset.disconnect()
		event.accept()

	def executeProcess(self):
		self.setRunState(not(self.runState))
		
		if self.runState:
			rotateVideo = sum([
				int(self.rotation_0_radio.isChecked())   *   0,
				int(self.rotation_90_radio.isChecked())  *  90,
				int(self.rotation_180_radio.isChecked()) * 180,
				int(self.rotation_270_radio.isChecked()) * 270
			])

			mirrorVideo = self.mirrorVideo_check.isChecked()
			binaryVideo = self.binaryVideo_check.isChecked()
			groupPixel  = self.groupPixel_check.isChecked()
			colorInvert = self.colorInvert_check.isChecked()
			colorTune   = self.colorTune_widget.getValue()

			p = Process(target = self.videoProcess(
				rotation = rotateVideo, mirror = mirrorVideo, binary = binaryVideo, grouping = groupPixel, invert = colorInvert,
				brightness_r = colorTune["red_brightness"],   offset_r = colorTune["red_offset"],
				brightness_g = colorTune["green_brightness"], offset_g = colorTune["green_offset"],
				brightness_b = colorTune["blue_brightness"],  offset_b = colorTune["blue_offset"]
			))
			p.start()
			p.join()

			
		else:
			if self.currentProcessor:
				self.currentProcessor.run = False

	def videoProcess(self, *args, **argv):

		for row in range(self.task_listwidget.count()):

			if not(self.runState):
				break


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
				procrssor.status.connect(lambda value : widget.setProgress(int(value)))
				procrssor.process(in_name, *args, **argv)
			else:
				debugPrint("Invalid item %s" % in_name)

		self.currentProcessor = None
		self.setRunState(False)


	def setRunState(self, status):
		self.runState = status
		self.execute_button.setText("cancel" if status else "execute")
		_ = [widget.setEnabled(not(self.runState)) for widget in [
			self.task_listwidget, 
			self.rotation_0_radio, self.rotation_90_radio, self.rotation_180_radio, self.rotation_270_radio,
			self.mirrorVideo_check, self.binaryVideo_check, self.groupPixel_check, self.colorInvert_check, 
			self.colorTune_check, self.colorTune_widget,
			self.delete_button
		]]

class ColorTuneWidget(QWidget):
	red_brightness_changed   = pyqtSignal(float)
	green_brightness_changed = pyqtSignal(float)
	blue_brightness_changed  = pyqtSignal(float)
	red_offset_changed       = pyqtSignal(int)
	green_offset_changed     = pyqtSignal(int)
	blue_offset_changed      = pyqtSignal(int)

	def __init__(self):
		super().__init__()
		self.colorTune_check        = QCheckBox("color tune")
		self.red_brightness_slide   = QSlider()
		self.green_brightness_slide = QSlider()
		self.blue_brightness_slide  = QSlider()

		self.red_offset_slide       = QSlider()
		self.green_offset_slide     = QSlider()
		self.blue_offset_slide      = QSlider()

		self.red_brightness_spin    = QDoubleSpinBox()
		self.green_brightness_spin  = QDoubleSpinBox()
		self.blue_brightness_spin   = QDoubleSpinBox()

		self.red_offset_spin        = QSpinBox()
		self.green_offset_spin      = QSpinBox()
		self.blue_offset_spin       = QSpinBox()

		self.red_brightness_reset   = QPushButton("reset")
		self.green_brightness_reset = QPushButton("reset")
		self.blue_brightness_reset  = QPushButton("reset")

		self.red_offset_reset       = QPushButton("reset")
		self.green_offset_reset     = QPushButton("reset")
		self.blue_offset_reset      = QPushButton("reset")

		self.color_layout           = QGridLayout()


		for index, label_text in enumerate([
			"red amplify", "green amplify", "blue amplify", 
			"red offset",  "green offset",  "blue offset"]):
			label_widget = QLabel(label_text)
			label_widget.setAlignment(Qt.AlignRight)
			label_widget.setFixedWidth(70)
			self.color_layout.addWidget (label_widget,  index,     0, 1, 1)


		for index, widget in enumerate([self.red_brightness_slide, self.green_brightness_slide, self.blue_brightness_slide]):
			widget.setOrientation(Qt.Horizontal)
			widget.setMaximum (20)
			widget.setMinimum  (0)
			widget.setPageStep (1)
			widget.setSliderPosition (10)
			self.color_layout.addWidget (widget,        index,     1, 1, 3)	

		for index, widget in enumerate([self.red_offset_slide,     self.green_offset_slide,     self.blue_offset_slide]):
			widget.setOrientation(Qt.Horizontal)
			widget.setMaximum ( 255)
			widget.setMinimum (-255)
			widget.setPageStep (1)
			widget.setSliderPosition (0)
			self.color_layout.addWidget (widget,        index + 3, 1, 1, 3)

		for index, widget in enumerate([self.red_brightness_spin, self.green_brightness_spin, self.blue_brightness_spin]):
			widget.setMaximum  (2)
			widget.setMinimum  (0)
			widget.setSingleStep (0.1)
			widget.setValue (1)
			widget.setFixedWidth(50)
			widget.setAlignment(Qt.AlignCenter)
			self.color_layout.addWidget (widget,        index,     4, 1, 1)	

		for index, widget in enumerate([self.red_offset_spin,     self.green_offset_spin,     self.blue_offset_spin]):
			widget.setMaximum ( 255)
			widget.setMinimum (-255)
			widget.setSingleStep (1)
			widget.setValue (0)
			widget.setFixedWidth(50)
			widget.setAlignment(Qt.AlignCenter)
			self.color_layout.addWidget (widget,        index + 3, 4, 1, 1)

		for index, widget in enumerate([self.red_offset_spin,     self.green_offset_spin,     self.blue_offset_spin]):
			widget.setMaximum ( 255)
			widget.setMinimum (-255)
			widget.setSingleStep (1)
			widget.setValue (0)
			widget.setFixedWidth(50)
			widget.setAlignment(Qt.AlignCenter)
			self.color_layout.addWidget (widget,        index + 3, 4, 1, 1)

		for index, widget in enumerate([
			self.red_brightness_reset, self.green_brightness_reset, self.blue_brightness_reset,
			self.red_offset_reset,     self.green_offset_reset,     self.blue_offset_reset]):

			widget.setFixedWidth(50)
			self.color_layout.addWidget (widget,        index,    5, 1, 1)
		self.setLayout(self.color_layout)


		self.red_brightness_slide.valueChanged.connect(   lambda val: self.red_brightness_changed.emit(   round(val/10, 1)))
		self.green_brightness_slide.valueChanged.connect( lambda val: self.green_brightness_changed.emit( round(val/10, 1)))
		self.blue_brightness_slide.valueChanged.connect(  lambda val: self.blue_brightness_changed.emit(  round(val/10, 1)))
		self.red_brightness_spin.valueChanged.connect(    lambda val: self.red_brightness_changed.emit(   round(val,    1)))
		self.green_brightness_spin.valueChanged.connect(  lambda val: self.green_brightness_changed.emit( round(val,    1)))
		self.blue_brightness_spin.valueChanged.connect(   lambda val: self.blue_brightness_changed.emit(  round(val,    1)))

		self.red_brightness_changed.connect(  lambda val: self.red_brightness_slide.setValue(  int(val*10)) if not (val * 10 == self.red_brightness_slide.value())   else lambda:None )
		self.green_brightness_changed.connect(lambda val: self.green_brightness_slide.setValue(int(val*10)) if not (val * 10 == self.green_brightness_slide.value()) else lambda:None )
		self.blue_brightness_changed.connect( lambda val: self.blue_brightness_slide.setValue( int(val*10)) if not (val * 10 == self.blue_brightness_slide.value())  else lambda:None )
		self.red_brightness_changed.connect(  lambda val: self.red_brightness_spin.setValue(       val    ) if not (val      == self.red_brightness_spin.value())    else lambda:None )
		self.green_brightness_changed.connect(lambda val: self.green_brightness_spin.setValue(     val    ) if not (val      == self.green_brightness_spin.value())  else lambda:None )
		self.blue_brightness_changed.connect( lambda val: self.blue_brightness_spin.setValue(      val    ) if not (val      == self.blue_brightness_spin.value())   else lambda:None )

		self.red_offset_slide.valueChanged.connect(   lambda val: self.red_offset_changed.emit(val))
		self.green_offset_slide.valueChanged.connect( lambda val: self.green_offset_changed.emit(val))
		self.blue_offset_slide.valueChanged.connect(  lambda val: self.blue_offset_changed.emit(val))
		self.red_offset_spin.valueChanged.connect(    lambda val: self.red_offset_changed.emit(val))
		self.green_offset_spin.valueChanged.connect(  lambda val: self.green_offset_changed.emit(val))
		self.blue_offset_spin.valueChanged.connect(   lambda val: self.blue_offset_changed.emit(val))

		self.red_offset_changed.connect(  lambda val: self.red_offset_slide.setValue(  int(val)) if not (val == self.red_offset_slide.value())   else lambda:None )
		self.green_offset_changed.connect(lambda val: self.green_offset_slide.setValue(int(val)) if not (val == self.green_offset_slide.value()) else lambda:None )
		self.blue_offset_changed.connect( lambda val: self.blue_offset_slide.setValue( int(val)) if not (val == self.blue_offset_slide.value())  else lambda:None )
		self.red_offset_changed.connect(  lambda val: self.red_offset_spin.setValue(   int(val)) if not (val == self.red_offset_spin.value())    else lambda:None )
		self.green_offset_changed.connect(lambda val: self.green_offset_spin.setValue( int(val)) if not (val == self.green_offset_spin.value())  else lambda:None )
		self.blue_offset_changed.connect( lambda val: self.blue_offset_spin.setValue(  int(val)) if not (val == self.blue_offset_spin.value())   else lambda:None )

		self.red_brightness_reset.clicked.connect(lambda   : self.red_brightness_changed.emit(1.0))
		self.green_brightness_reset.clicked.connect(lambda : self.green_brightness_changed.emit(1.0))
		self.blue_brightness_reset.clicked.connect(lambda  : self.blue_brightness_changed.emit(1.0))
		self.red_offset_reset.clicked.connect(lambda       : self.red_offset_changed.emit(0))
		self.green_offset_reset.clicked.connect(lambda     : self.green_offset_changed.emit(0))
		self.blue_offset_reset.clicked.connect(lambda      : self.blue_offset_changed.emit(0))

	def reset(self):
		self.red_brightness_changed.emit(1.0)
		self.green_brightness_changed.emit(1.0)
		self.blue_brightness_changed.emit(1.0)
		self.red_offset_changed.emit(0)
		self.green_offset_changed.emit(0)
		self.blue_offset_changed.emit(0)

	def getValue(self):
		return {
			"red_brightness"   : self.red_brightness_spin.value(),
			"green_brightness" : self.green_brightness_spin.value(),
			"blue_brightness"  : self.blue_brightness_spin.value(),
			"red_offset"       : self.red_offset_spin.value(),
			"green_offset"     : self.green_offset_spin.value(),
			"blue_offset"      : self.blue_offset_spin.value()
		}

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



if __name__ == '__main__':
	app    = QApplication(sys.argv)
	window = VideoConvertWidget()
	# window.setStyleSheet("QWidget{font-size: 11px;}")
	window.show()
	
	sys.exit(app.exec_())