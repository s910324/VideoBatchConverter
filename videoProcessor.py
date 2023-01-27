
import os
import sys
import numpy as np
from cv2          import cvtColor               as cv2_cvtColor
from cv2          import split                  as cv2_split
from cv2          import merge                  as cv2_merge

from cv2          import imread                 as cv2_imread
from cv2          import imwrite                as cv2_imwrite
from cv2          import bitwise_not            as cv2_bitwise_not

from cv2          import COLOR_BGR2HSV          as cv2_COLOR_BGR2HSV
from cv2          import COLOR_HSV2BGR          as cv2_COLOR_HSV2BGR
from cv2          import IMREAD_COLOR           as cv2_IMREAD_COLOR
from cv2          import VideoCapture           as cv2_VideoCapture
from cv2          import VideoWriter            as cv2_VideoWriter
from cv2          import VideoWriter_fourcc     as cv2_VideoWriter_fourcc

from cv2          import CAP_PROP_FPS           as cv2_CAP_PROP_FPS
from cv2          import CAP_PROP_FRAME_WIDTH   as cv2_CAP_PROP_FRAME_WIDTH
from cv2          import CAP_PROP_FRAME_HEIGHT  as cv2_CAP_PROP_FRAME_HEIGHT
from cv2          import CAP_PROP_FRAME_COUNT   as cv2_CAP_PROP_FRAME_COUNT
from cv2          import THRESH_BINARY          as cv2_THRESH_BINARY
from cv2          import INTER_NEAREST          as cv2_INTER_NEAREST
from cv2          import flip                   as cv2_flip
from cv2          import resize                 as cv2_resize
from cv2          import threshold              as cv2_threshold
from cv2          import destroyAllWindows      as cv2_destroyAllWindows

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
	status = pyqtSignal(float)
	def __init__(self, parent=None):
		super(VideoProcessor, self).__init__(parent)
		self.run = True

	def process(self, in_name, flip:bool=False, mirror:bool=False, binary:bool=False, grouping:bool=False, invert:bool=False, 
		brightness_r:float = 1, offset_r:float = 0, brightness_g:float = 1, offset_g:float = 0, brightness_b:float = 1, offset_b:float = 0):

		cap              = cv2_VideoCapture(in_name) 
		info             = videoInfo(cap)
		outname          = in_name.split(".")[0] + f"{'_flip'if flip else ''}"+ f"{'_mirror'if mirror else ''}" + \
			f"{'_binary'if binary else ''}"+ f"{'_grouping'if grouping else ''}"+ f"{'_inv'if invert else ''}" + \
			f"{('_bright_r%d' % brightness_r) if brightness_r else ''}" + f"{('_contrast_r%d' % contrast_r) if contrast_r else ''}" + \
			f"{('_bright_g%d' % brightness_g) if brightness_g else ''}" + f"{('_contrast_g%d' % contrast_g) if contrast_g else ''}" + \
			f"{('_bright_b%d' % brightness_b) if brightness_b else ''}" + f"{('_contrast_b%d' % contrast_b) if contrast_b else ''}" + \
			".mp4"
		fourcc           = cv2_VideoWriter_fourcc(*'mp4v')
		deflate_size     = (int(info["width"]/2), int(info["height"]/2))
		inflate_size     = (info["width"], info["height"])
		out              = cv2_VideoWriter(outname,fourcc, info["fps"], (info["width"], info["height"]))
		framecount       = info["framecount"]
		fps              = info["fps"]
		threshold        = 50
		current_frame    = 0

		color_brightness = any( not(i == 1) for i in [brightness_r, brightness_g, brightness_b])
		color_offset     = any( not(i == 0) for i in [offset_r,     offset_g,     offset_b])
		color_process    = color_brightness or color_offset

		while self.run:
			ret, frame = cap.read()
			if ret == True:
				QCoreApplication.processEvents()
				current_frame += 1
				if (current_frame%(fps*2)) == 0: 
					progress = current_frame/framecount*100
					debugPrint(f"progress {progress:.1f}% | {in_name}") 
					self.status.emit(progress)

				if flip:
					frame  = cv2_flip(frame,-1)

				if mirror:	
					frame = cv2_flip(frame, 1)

				if binary:
					 _, frame = cv2_threshold( frame, threshold, 255, cv2_THRESH_BINARY)

				if grouping:
					frame = cv2_resize( frame, deflate_size, fx=0, fy=0, interpolation = cv2_INTER_NEAREST)
					frame = cv2_resize( frame, inflate_size, fx=0, fy=0, interpolation = cv2_INTER_NEAREST)

				if invert:
					frame = cv2_bitwise_not(frame)

				if color_process:
					frame_b, frame_g, frame_r = cv2_split(frame)
					
					if not(brightness_r == 1) or not(offset_r==0):
						frame_r = np.int16(frame_r)
						frame_r = frame_r * brightness_r + offset_r
						frame_r = np.clip(frame_r, 0, 255)
						frame_r = np.uint8(frame_r)

					if not(brightness_g == 1) or not(offset_g==0):
						frame_g = np.int16(frame_g)
						frame_g = frame_g * brightness_g + offset_g
						frame_g = np.clip(frame_g, 0, 255)
						frame_g = np.uint8(frame_g)

					if not(brightness_b == 1) or not(offset_b==0):
						frame_b = np.int16(frame_b)
						frame_b = frame_b * brightness_b + offset_b
						frame_b = np.clip(frame_b, 0, 255)
						frame_b = np.uint8(frame_b)
					frame = cv2_merge ((frame_b, frame_g, frame_r))

				out.write(frame)
				
			else:
				break
		if self.run:
			self.status.emit(100.0)

		cap.release()
		out.release()
		cv2_destroyAllWindows()
		debugPrint("done")


class ImageProcessor(QObject):
	status = pyqtSignal(float)
	def __init__(self, parent=None):
		super(ImageProcessor, self).__init__(parent)
		self.run = True

	def process(self, in_name, flip:bool=False, mirror:bool=False, binary:bool=False, grouping:bool=False, invert:bool=False,
		brightness_r:float = 1, offset_r:float = 0, brightness_g:float = 1, offset_g:float = 0, brightness_b:float = 1, offset_b:float = 0):

		img           = cv2_imread(in_name, cv2_IMREAD_COLOR)
		info          = imageInfo(img)
		outname       = in_name.split(".")[0] + f"{'_flip'if flip else ''}"+ f"{'_mirror'if mirror else ''}"+ f"{'_binary'if binary else ''}"+ f"{'_grouping'if grouping else ''}"+ f"{'_inv'if invert else ''}" + ".jpg"

		deflate_size  = (int(info["width"]/2), int(info["height"]/2))
		inflate_size  = (info["width"], info["height"])

		threshold     = 50
		current_proce = 0


		QCoreApplication.processEvents()
		color_brightness = any( not(i == 1) for i in [brightness_r, brightness_g, brightness_b])
		color_offset     = any( not(i == 0) for i in [offset_r,     offset_g,     offset_b])
		color_process    = color_brightness or color_offset

		total_operation  = sum([flip, mirror, binary, grouping, invert, color_process])

		if flip:
			img  = cv2_flip(img,-1)
			current_proce = current_proce + 1
			self.status.emit(current_proce/total_operation * 100)

		if mirror:	
			img = cv2_flip(img, 1)
			current_proce = current_proce + 1
			self.status.emit(current_proce/total_operation * 100)
			
		if binary:
			_, img = cv2_threshold( img, threshold, 255, cv2_THRESH_BINARY)
			current_proce = current_proce + 1
			self.status.emit(current_proce/total_operation * 100)
			
		if grouping:
			img = cv2_resize( img, deflate_size, fx=0, fy=0, interpolation = cv2_INTER_NEAREST)
			img = cv2_resize( img, inflate_size, fx=0, fy=0, interpolation = cv2_INTER_NEAREST)
			current_proce = current_proce + 1
			self.status.emit(current_proce/total_operation * 100)
			
		if invert:
			img = cv2_bitwise_not(img)
			current_proce = current_proce + 1
			self.status.emit(current_proce/total_operation * 100)

		if color_process:
			img_b, img_g, img_r = cv2_split(img)

			if not(brightness_r == 1) or not(offset_r==0):
				img_r = np.int16(img_r)
				img_r = img_r * brightness_r + offset_r
				img_r = np.clip(img_r, 0, 255)
				img_r = np.uint8(img_r)

			if not(brightness_g == 1) or not(offset_g==0):
				img_g = np.int16(img_g)
				img_g = img_g * brightness_g + offset_g
				img_g = np.clip(img_g, 0, 255)
				img_g = np.uint8(img_g)

			if not(brightness_b == 1) or not(offset_b==0):
				img_b = np.int16(img_b)
				img_b = img_b * brightness_b + offset_b
				img_b = np.clip(img_b, 0, 255)
				img_b = np.uint8(img_b)
			img = cv2_merge ((img_b, img_g, img_r))
			current_proce = current_proce + 1
			self.status.emit(current_proce/total_operation * 100)

		cv2_imwrite(outname, img)
		self.status.emit(100.0)

		cv2_destroyAllWindows()
		debugPrint("done")

def debugPrint(*args, **argv): 
	if debug:
		print(*args, **argv)



if __name__ == '__main__':
	debug = True
	path = "C:\\Users\\scott\\Videos\\"
	files = ["butterfly fly_path_2.mp4", "butterfly_fly_path.mp4", "PoroTech_light_line.mp4"]
	videoProcessor = VideoProcessor()
	for video in files:
		videoProcessor.process(path + video, flip=False, mirror=False, binary=True, grouping=True)