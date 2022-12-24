import cv2
import numpy as np 
import os
import sys
from   PyQt5.Qt                 import Qt
from   PyQt5.QtWidgets          import * 
from   PyQt5.QtCore             import *
from   PyQt5.QtGui              import * 


debug = False


def videoInfo(cap):
	return {
		"fps"        : int(cap.get(cv2.CAP_PROP_FPS)),
		"width"      : int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
		"height"     : int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
		"framecount" : int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
	}

class VideoProcessor(QObject):
	status = pyqtSignal(float)
	def __init__(self, parent=None):
		super(VideoProcessor, self).__init__(parent)
		self.run = True

	def process(self, in_name, flip:bool=False, mirror:bool=False, binary:bool=False, grouping:bool=False):
		cap           = cv2.VideoCapture(in_name) 
		info          = videoInfo(cap)
		outname       = in_name.split(".")[0] + f"{'_flip'if flip else ''}"+ f"{'_mirror'if mirror else ''}"+ f"{'_binary'if binary else ''}"+ f"{'_grouping'if grouping else ''}" + ".mp4"
		fourcc        = cv2.VideoWriter_fourcc(*'mp4v')
		deflate_size  = (int(info["width"]/2), int(info["height"]/2))
		inflate_size  = (info["width"], info["height"])
		out           = cv2.VideoWriter(outname,fourcc, info["fps"], (info["width"], info["height"]))
		framecount    = info["framecount"]
		fps           = info["fps"]
		threshold     = 50
		current_frame = 0

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
					frame  = cv2.flip(frame,-1)

				if mirror:	
					frame = cv2.flip(frame, 1)

				if binary:
					 _, frame = cv2.threshold( frame, threshold, 255, cv2.THRESH_BINARY)

				if grouping:
					frame = cv2.resize( frame, deflate_size, fx=0, fy=0, interpolation = cv2.INTER_NEAREST)
					frame = cv2.resize( frame, inflate_size, fx=0, fy=0, interpolation = cv2.INTER_NEAREST)

				out.write(frame)
				
			else:
				break
		if self.run:
			self.status.emit(100.0)
		cap.release()
		out.release()
		cv2.destroyAllWindows()
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