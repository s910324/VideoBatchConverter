
import os
import sys
import numpy as np
from datetime     import datetime
from cv2          import cvtColor                   as cv2_cvtColor
from cv2          import split                      as cv2_split
from cv2          import merge                      as cv2_merge

from cv2          import imread                     as cv2_imread
from cv2          import imwrite                    as cv2_imwrite
from cv2          import bitwise_not                as cv2_bitwise_not

from cv2          import ROTATE_90_CLOCKWISE        as cv2_ROTATE_90
from cv2          import ROTATE_180                 as cv2_ROTATE_180
from cv2          import ROTATE_90_COUNTERCLOCKWISE as cv2_ROTATE_270

from cv2          import COLOR_BGR2HSV              as cv2_COLOR_BGR2HSV
from cv2          import COLOR_HSV2BGR              as cv2_COLOR_HSV2BGR
from cv2          import IMREAD_COLOR               as cv2_IMREAD_COLOR
from cv2          import VideoCapture               as cv2_VideoCapture
from cv2          import VideoWriter                as cv2_VideoWriter
from cv2          import VideoWriter_fourcc         as cv2_VideoWriter_fourcc

from cv2          import CAP_PROP_FPS               as cv2_CAP_PROP_FPS
from cv2          import CAP_PROP_FRAME_WIDTH       as cv2_CAP_PROP_FRAME_WIDTH
from cv2          import CAP_PROP_FRAME_HEIGHT      as cv2_CAP_PROP_FRAME_HEIGHT
from cv2          import CAP_PROP_FRAME_COUNT       as cv2_CAP_PROP_FRAME_COUNT
from cv2          import THRESH_BINARY              as cv2_THRESH_BINARY
from cv2          import INTER_NEAREST              as cv2_INTER_NEAREST

from cv2          import flip                       as cv2_flip
from cv2          import rotate                     as cv2_rotate
from cv2          import resize                     as cv2_resize
from cv2          import threshold                  as cv2_threshold
from cv2          import destroyAllWindows          as cv2_destroyAllWindows
from cv2          import warpAffine                 as cv2_warpAffine
from PyQt5.QtCore import QObject, pyqtSignal, QCoreApplication

debug = True

def videoInfo(cap):
	return {
		"fps"        : int(cap.get(cv2_CAP_PROP_FPS)),
		"width"      : int(cap.get(cv2_CAP_PROP_FRAME_WIDTH)),
		"height"     : int(cap.get(cv2_CAP_PROP_FRAME_HEIGHT)),
		"framecount" : int(cap.get(cv2_CAP_PROP_FRAME_COUNT))
	}

def imageInfo(img):
	height, width, channels = img.shape
	return {
		"height"     : height,
		"width"      : width, 
		"channels"   : channels
	}


class VideoProcessor(QObject):
	percentage = pyqtSignal(float)
	def __init__(self, parent = None):
		super(VideoProcessor, self).__init__(parent)
		self.run = True

	def process(self, filePath,
		r_flip:bool = False, r_mirror:bool = False, r_invert:bool = False, r_brightness:float = 1, r_offset:float = 0, r_shift_x:int = 0, r_shift_y:int = 0,
		g_flip:bool = False, g_mirror:bool = False, g_invert:bool = False, g_brightness:float = 1, g_offset:float = 0, g_shift_x:int = 0, g_shift_y:int = 0,
		b_flip:bool = False, b_mirror:bool = False, b_invert:bool = False, b_brightness:float = 1, b_offset:float = 0, b_shift_x:int = 0, b_shift_y:int = 0):

		cap              = cv2_VideoCapture(filePath) 
		info             = videoInfo(cap)
		outname          = outFullPath(filePath, "mp4")
		fourcc           = cv2_VideoWriter_fourcc(*'mp4v')
		out              = cv2_VideoWriter(outname, fourcc, info["fps"], (info["width"] , info["height"] ))
		framecount       = info["framecount"]
		fps              = info["fps"]
		current_frame    = 0

		while self.run:
			ret, frame = cap.read()
			fprocessor = FrameProcessor()
			if ret == True:
				QCoreApplication.processEvents()
				current_frame += 1
				if (current_frame%(fps*2)) == 0: 
					progress = current_frame/framecount*100
					debugPrint(f"progress {progress:.1f}% | {filePath}") 
					self.percentage.emit(progress)

				frame = fprocessor.process(frame,
					r_flip, r_mirror, r_invert, r_brightness, r_offset, r_shift_x, r_shift_y,
					g_flip, g_mirror, g_invert, g_brightness, g_offset, g_shift_x, g_shift_y,
					b_flip, b_mirror, b_invert, b_brightness, b_offset, b_shift_x, b_shift_y,
				)
				

				out.write(frame)
				
			else:
				break

		if self.run:
			self.percentage.emit(100.0)
			
		cap.release()
		out.release()
		cv2_destroyAllWindows()
		debugPrint("done")

class ImageProcessor(QObject):
	percentage = pyqtSignal(float)
	def __init__(self, parent = None):
		super(ImageProcessor, self).__init__(parent)
		self.run = True

	def process(self, filePath,
		r_flip:bool = False, r_mirror:bool = False, r_invert:bool = False, r_brightness:float = 1, r_offset:float = 0, r_shift_x:int = 0, r_shift_y:int = 0,
		g_flip:bool = False, g_mirror:bool = False, g_invert:bool = False, g_brightness:float = 1, g_offset:float = 0, g_shift_x:int = 0, g_shift_y:int = 0,
		b_flip:bool = False, b_mirror:bool = False, b_invert:bool = False, b_brightness:float = 1, b_offset:float = 0, b_shift_x:int = 0, b_shift_y:int = 0):
		
		frame      = cv2_imread(filePath, cv2_IMREAD_COLOR)
		outname    = outFullPath(filePath, "png")
		fprocessor = FrameProcessor()
		fprocessor.percentage.connect(self.percentage.emit)

		frame      = fprocessor.process(frame,
			r_flip, r_mirror, r_invert, r_brightness, r_offset, r_shift_x, r_shift_y,
			g_flip, g_mirror, g_invert, g_brightness, g_offset, g_shift_x, g_shift_y,
			b_flip, b_mirror, b_invert, b_brightness, b_offset, b_shift_x, b_shift_y,
		)
		print(outname)
		cv2_imwrite(outname, frame)
		cv2_destroyAllWindows()
		debugPrint("done")

class FrameProcessor(QObject):
	percentage = pyqtSignal(float)

	def __init__(self):
		super(FrameProcessor, self).__init__()
		self.processedSteps = 0
		self.do_counts      = 0

	def process(self, frame, 
		r_flip:bool = False, r_mirror:bool = False, r_invert:bool = False, r_brightness:float = 1, r_offset:float = 0, r_shift_x:int = 0, r_shift_y:int = 0,
		g_flip:bool = False, g_mirror:bool = False, g_invert:bool = False, g_brightness:float = 1, g_offset:float = 0, g_shift_x:int = 0, g_shift_y:int = 0,
		b_flip:bool = False, b_mirror:bool = False, b_invert:bool = False, b_brightness:float = 1, b_offset:float = 0, b_shift_x:int = 0, b_shift_y:int = 0):

		do_flip_mirror = sum([(r_mirror or r_flip), (g_mirror or g_flip), (b_mirror or b_flip)])
		do_color       = sum([1 for c in [(r_brightness, r_offset),  (g_brightness, g_offset),  (b_brightness, b_offset)]  if not(c == (1, 0))])
		do_shift       = sum([1 for s in [(r_shift_x,    r_shift_y), (r_shift_x,    r_shift_y), (r_shift_x,    r_shift_y)] if not(s == (0, 0))])
		do_invert      = sum([r_invert, g_invert, b_invert])
		self.do_counts = sum([do_flip_mirror, do_color, do_shift, do_invert])

		frame_b, frame_g, frame_r = cv2_split(frame)
		rcp     = ChannelProcessor()
		gcp     = ChannelProcessor()
		bcp     = ChannelProcessor()
		rcp.step.connect(self.updateProgress)
		gcp.step.connect(self.updateProgress)
		bcp.step.connect(self.updateProgress)

		frame_r = rcp.process(frame_r, r_flip, r_mirror, r_invert, r_brightness, r_offset, r_shift_x, r_shift_y)
		frame_g = gcp.process(frame_g, g_flip, g_mirror, g_invert, g_brightness, g_offset, g_shift_x, g_shift_y)
		frame_b = bcp.process(frame_b, b_flip, b_mirror, b_invert, b_brightness, b_offset, b_shift_x, b_shift_y)
		frame   = cv2_merge ((frame_b, frame_g, frame_r))
		self.percentage.emit(100.0)
		QCoreApplication.processEvents()
		return frame


	def updateProgress(self):
		self.processedSteps += 1
		if self.do_counts > 0:
			self.percentage.emit(self.processedSteps/self.do_counts*100)
			QCoreApplication.processEvents()

class ChannelProcessor(QObject):
	step = pyqtSignal()
	def __init__(self):
		super(ChannelProcessor, self).__init__()
		
	def process(self, frame, flip:bool = False, mirror:bool = False, invert:bool = False, brightness:float = 1, offset:float = 0, shift_x:int = 0, shift_y:int = 0):

		do_flip_mirror = None
		do_flip_mirror =  1 if [flip, mirror] == [False,  True] else do_flip_mirror
		do_flip_mirror = -1 if [flip, mirror] == [True,   True] else do_flip_mirror
		do_flip_mirror =  0 if [flip, mirror] == [True,  False] else do_flip_mirror
		do_color       =  not((brightness, offset) == (1, 0))
		do_shift       =  not((shift_x,   shift_y) == (0, 0))
		
		if not (do_flip_mirror == None):
			frame = cv2_flip(frame, do_flip_mirror)
			self.step.emit()

		if invert:
			frame = cv2_bitwise_not(frame)
			self.step.emit()

		if do_color:
			frame = np.int16(frame)
			frame = frame * brightness + offset
			frame = np.clip(frame, 0, 255)
			frame = np.uint8(frame)
			self.step.emit()

		if do_shift:
			h, w  = frame.shape[:2]
			trans = np.float32([[1,0,shift_x], [0,1,shift_y]])
			frame = cv2_warpAffine(frame, trans, (w,h))
			self.step.emit()
		return frame

def outFullPath(filePath, ext):
	now      = datetime.now().strftime("%Y%m%d_%H%M%S")
	absPath  = os.path.abspath(filePath)
	dirPath  = os.path.dirname(os.path.realpath(absPath))
	fileName = os.path.splitext(os.path.basename(absPath))[0]
	outname  = f"{dirPath}/{fileName}_{now}.{ext}"
	return outname

def debugPrint(*args, **argv): 
	if debug:
		print(*args, **argv)


if __name__ == '__main__':
	debug = True

	iProcessor = ImageProcessor()
	vProcessor = VideoProcessor()

	# iProcessor.process("./test.png",
	# 	r_flip = True,  r_mirror = False, r_invert = False, r_brightness = 1, r_offset = 0, r_shift_x =  0, r_shift_y =  -15,
	# 	g_flip = False, g_mirror = True,  g_invert = False, g_brightness = 1, g_offset = 0, g_shift_x = -5, g_shift_y =    0,
	# 	b_flip = True,  b_mirror = True,  b_invert = False, b_brightness = 1, b_offset = 0, b_shift_x = -5, b_shift_y =  -15,
	# )
	fs = ["./cross_orig.png", "./Poro_720.png", "./5100_test_inv_edge_VGA.png"]
	vs = ["./PoroTech_light_line_White.mp4"]
	
	# for f in fs:
	# 	iProcessor.process(f,
	# 		r_flip = False,  r_mirror = False,  r_invert = False, r_brightness = 1, r_offset = 0,  r_shift_x =   0, r_shift_y  = 0,
	# 		g_flip = True,   g_mirror = False,  g_invert = False, g_brightness = 1, g_offset = 0, g_shift_x =   -4,  g_shift_y = 0,
	# 		b_flip = False,  b_mirror = False,  b_invert = False, b_brightness = 1, b_offset = 0, b_shift_x =    0,  b_shift_y = 0,
	# 	)
	for f in vs:
		vProcessor.process(f,
			r_flip = False,  r_mirror = False,  r_invert = False, r_brightness = 1, r_offset = 0, r_shift_x =    0, r_shift_y  = 0,
			g_flip = True,   g_mirror = False,  g_invert = False, g_brightness = 1, g_offset = 0, g_shift_x =   -4,  g_shift_y = 0,
			b_flip = False,  b_mirror = False,  b_invert = False, b_brightness = 1, b_offset = 0, b_shift_x =    0,  b_shift_y = 0,
		)