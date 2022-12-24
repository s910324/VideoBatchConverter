import os
import sys
from   PyQt5.Qt                 import Qt
from   PyQt5.QtWidgets          import * 
from   PyQt5.QtCore             import *
from   PyQt5.QtGui              import * 
from   videoProcessor           import *
from   multiprocessing          import Process

class VideoConvertWidget(QWidget):
	def __init__(self):
		super().__init__()

		self.runState          = False
		self.currentProcessor  = None
		self.task_listwidget   = TestListView()
		self.background_label  = QLabel("Drag / Drop video")
		self.flipVideo_check   = QCheckBox("flip video")
		self.mirrorVideo_check = QCheckBox("mirrir video")
		self.binaryVideo_check = QCheckBox("video binary")
		self.groupPixel_check  = QCheckBox("pixel grouping")
		self.execute_button    = QPushButton("execute")
		self.delete_button     = QPushButton("clear")
		self.float_layout      = QGridLayout()
		self.layout            = QGridLayout()

		self.background_label.setAlignment(Qt.AlignCenter)
		self.background_label.setStyleSheet("font-size: 20px; color:#777777;")
		self.setWindowTitle("Batch Video Converter")
		self.delete_button.clicked.connect(lambda : self.task_listwidget.clear())
		self.task_listwidget.setDragDropMode(QAbstractItemView.DragDrop)
		uiFixedHeight = 35

		self.float_layout.addWidget (self.background_label,  0, 0, 4, 4)
		self.float_layout.addWidget (self.task_listwidget,  0, 0, 4, 4)
		self.float_layout.addWidget (self.delete_button,    3, 3, 1, 1)

		self.layout.addLayout(self.float_layout, 0, 0, 1, 4)
		for index, widget in enumerate([self.flipVideo_check, self.mirrorVideo_check, self.binaryVideo_check, self.groupPixel_check]):
			self.layout.addWidget (widget,  1, index, 1, 1)
			widget.setFixedHeight(uiFixedHeight)
		self.layout.addWidget (self.execute_button,  2, 1, 1, 2)
		self.delete_button.setFixedSize(45, 25)
		self.setLayout(self.layout)


		self.execute_button.clicked.connect(self.executeProcess)
		self.resize(500,300)

	def executeProcess(self):
		self.setRunState(not(self.runState))
		
		if self.runState:
			flipVideo   = self.flipVideo_check.isChecked()
			mirrorVideo = self.mirrorVideo_check.isChecked()
			binaryVideo = self.binaryVideo_check.isChecked()
			groupPixel  = self.groupPixel_check.isChecked()

			p = Process(target = self.videoProcess(flipVideo, mirrorVideo, binaryVideo, groupPixel))
			p.start()
			p.join()

			
		else:
			if self.currentProcessor:
				self.currentProcessor.run = False

	def videoProcess(self, flipVideo, mirrorVideo, binaryVideo, groupPixel):

		for row in range(self.task_listwidget.count()):

			if not(self.runState):
				break

			QCoreApplication.processEvents()
			item                  = self.task_listwidget.item(row)
			widget                = self.task_listwidget.itemWidget(item)
			in_name               = widget.filePath
			procrssor             = VideoProcessor(self)
			self.currentProcessor = procrssor
			procrssor.status.connect(lambda value : widget.setProgress(int(value)))
			procrssor.process(in_name, flip = flipVideo, mirror = mirrorVideo, binary = binaryVideo, grouping = groupPixel)
		self.currentProcessor = None
		self.setRunState(False)


	def setRunState(self, status):
		self.runState = status
		self.execute_button.setText("cancel" if status else "execute")
		_ = [widget.setEnabled(not(self.runState)) for widget in [self.task_listwidget, self.flipVideo_check, self.binaryVideo_check, self.mirrorVideo_check, self.binaryVideo_check, self.groupPixel_check, self.delete_button]]

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

class TestListView(QListWidget):
	def __init__(self, parent=None):
		super(TestListView, self).__init__(parent)
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
			if videoPath.split(".")[-1].upper() in ["MOV", "WMV", "AVI", "MKV", "MPEG", "MP4"]:
				item        = QListWidgetItem(self)
				row         = TaskListWidget(videoPath, item)
				row.remove.connect(lambda  i: self.takeItem (self.row(i)))
				self.addItem(item)
				item.setSizeHint(row.minimumSizeHint())
				self.setItemWidget(item, row)


if __name__ == '__main__':
	app    = QApplication(sys.argv)
	window = VideoConvertWidget()
	# window.setStyleSheet("QWidget{font-size: 11px;}")
	window.show()
	
	sys.exit(app.exec_())