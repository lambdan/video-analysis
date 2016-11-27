import os
import subprocess
import sys
import matplotlib.pyplot as plt
from natsort import natsorted
import time
import PIL
from PIL import Image, ImageChops, ImageEnhance
import datetime
import shutil

black_threshold = float(0.999) # if the diff is >= 99.9% black, its a dupe frame
pic_ext = ".bmp" # all the frames will be in this format. jpg is alot faster but less accurate


version = 1


if len(sys.argv) < 2:
	print "No input file"
	sys.exit(1)
else:
	inputfile = str(sys.argv[1])
	if not os.path.isfile(inputfile):
		print "That doesnt seem to be a file: " + inputfile
		sys.exit(1)

print "Input file: " + inputfile


runtime = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
basename = os.path.basename(inputfile)[:-4]
tempdir = "Framerate_" + basename
if os.path.exists(tempdir) is False:
	os.makedirs(tempdir)
framesdir = os.path.join(tempdir + '/frames/')
diffsfile = os.path.join(tempdir, 'diffs_human.txt')
tempoverlay = "overlay.srt" # ffmpeg is cranky, easiest to have the temp in the same working dir

def to_hhmmss(sec): # https://thingspython.wordpress.com/2010/09/27/code-golf-converting-seconds-to-hhmmss/
    min,sec = divmod(sec,60)
    hr,min = divmod(min,60)
    return "%d:%02d:%06.3f" % (hr,min,sec)

def ask_if_black(im1, im2):
	# (was) used for calibration
	tempdiff = os.path.join(tempdir + 'diff_' + im1[:-4] + "-" + im2[:-4] + ".bmp")
	image1 = Image.open(os.path.join(framesdir + im1)) # current frame
	image2 = Image.open(os.path.join(framesdir + im2)) # next frame
	diff = ImageChops.difference(image1, image2).save(tempdiff)
	a = Image.open(tempdiff)
	contrast = ImageEnhance.Contrast(a)
	contrast.enhance(10).show()
	option = raw_input("Is this image just black? (enter y if so)")
	a.close()
	if option == "y":
		return True
	else:
		return False

def generate_diff(im1, im2):
	image1 = Image.open(os.path.join(framesdir + im1)) # current frame
	image2 = Image.open(os.path.join(framesdir + im2)) # next frame
	diff = ImageChops.difference(image1, image2)
	palette = diff.getcolors(8192)
	return palette

def unique_frame(im1, im2, palette):
	global black_threshold
	# takes a palette (from generate_diff) and tries to determine if it is just black (sounds easy, i know)
	# currently this works for very very high quality (lossless) DIGITAL video. it will not work well with compressed or analogue video
	# (we need to calibrate what is just black and what is just interference etc for that to work)

	if palette is None:
		#print "none"
		return False # solid black, probably duped frame
	if len(palette) < 20:
		#print "less than 20 colors in palette"
		return False # less than 15 different colors, probably just alot of blacks (duped frame)

	pixels = 0
	black = 0
	for color in palette:
		pixels += color[0] # 100x100 is gonna be 10000
		combined_color = 0
		if (min(color[1])) > 20:
			return True # some tiny little pixel is very colorful, probably unique frame then
		if (max(color[1])) <= 10: # color[1] = rgb values, (5,5,5) is probably just black/interference
			black += color[0]

	part_black = float(black) / float(pixels)
	#print str(black) + "/" + str(pixels) + " = " + str(part_black)

	if part_black >= black_threshold:
		#print " == over threshold (duped frame)"
		return False
	else:
		#print " == unique frame!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
		return True

if os.path.exists(framesdir) is False:
	print ("Separating video into 60 screenshots (frames) per 1 second of video... "),
	os.makedirs(framesdir)
	start_time = time.time() # statistics are fun
	# 100x100 is enough, i think we get memoryerrors if we do any bigger, not to mention something like a 1920x1080 BMP frame takes alot of HDD space
	subprocess.call(['ffmpeg', '-i', inputfile, '-loglevel', 'panic', '-vf', 'scale=100:100', '-r', '60/1', os.path.join(framesdir + '%d' + pic_ext)]) # take 60 screenshots per 1 second
	timetook = time.time() - start_time
	files = []
	for file in os.listdir(framesdir):
		if file.endswith(pic_ext):
			files.append(file)
	files = natsorted(files)
	print "created " + str(len(files)) + " frames in " + str(timetook) + " seconds"
else:
	print "Frames found at: " + framesdir + "... skipping step"
	files = []
	for file in os.listdir(framesdir):
		if file.endswith(pic_ext):
			files.append(file)
	files = natsorted(files)

diffs = {}

start_time = time.time() # statistics are fun
print ("Calculating difference in colors between frames... might take a while... "), 
for f in files:
	curr_frame = f[:-4] # remove .bmp
	next_frame = str(int(curr_frame)+1) + pic_ext
	if os.path.isfile(os.path.join(framesdir + next_frame)) is False: # gone through all frames
		if not os.path.isfile(diffsfile):
			print "Saving human readable palettes..."
			with open(diffsfile, 'wb') as f: # write human readable file diffs tho, useful for debugging black level
				for key, value in diffs.iteritems():
					f.write(value[0] + "-" + value[1] + ": " + str(value[2]) + "\n")
	else:
		diffs[int(curr_frame)] = [f, next_frame, generate_diff(f, next_frame)]

timetook = time.time() - start_time
print "OK, took " + str(timetook) + " seconds"

framerate = {}
i = 0
unique_frames = 0
secs = 0
print ("Figuring out framerate..."),
for frame, values in diffs.iteritems():
	frame1 = values[0] # 1.bmp
	frame2 = values[1] # 2.bmp
	palette = values[2] # [(4, 4, 4), (8, 4, 4), (8, 4, 4), (8, 4, 4), (8, 4, 4), (8, 4, 4)...]
	if unique_frame(frame1, frame2, palette) is True:
		unique_frames += 1
	i += 1
	if i == 60: # 60 frames processed == 1 second processed
		framerate[secs] = unique_frames
		print (str(unique_frames)),
		unique_frames = 0
		i = 0
		secs += 1

print "OK"

# Generate subtitle for ffmpeg
if os.path.exists(tempoverlay):
	os.remove(tempoverlay)
with open(tempoverlay, 'a') as fi:
	for sec, fps in framerate.iteritems():
		fi.write(str(sec+1) + "\n")
		fi.write(to_hhmmss(sec) + " --> " + to_hhmmss(sec+1) + " X1:35 X2:35 Y1:0 Y2:30\n")
		fi.write("<font color=yellow>"+ str(fps) + " fps</font>\n\n")

max_x = len(framerate)
max_y = 61
plt.plot(framerate.keys(), framerate.values())
plt.axis([0, max_x, 0, max_y])
plt.title('Framerate of ' + basename, fontweight='bold')
plt.xlabel('Video Time (seconds)', fontstyle='italic')
plt.ylabel('FPS', fontstyle='italic')
plt.savefig(os.path.abspath(tempdir + "/" + runtime + "_" + basename + '_fps_graph.png'),dpi=400)
print "Graph saved"


#TODO: ask if you wanna make video with overlay
print "Making video with fps overlay..." # bad crappy quality for quickness
subprocess.call(['ffmpeg', '-i', inputfile, '-crf', '20', '-preset', 'medium', '-vf', 'scale=-1:720,subtitles=overlay.srt', '-loglevel', 'panic', '-flags' ,'+cgop' ,'-bf' ,'2' ,'-pix_fmt' ,'yuv420p' ,'-vprofile' ,'high' ,'-level' ,'4.1' ,'-movflags', 'faststart', '-g', '30', os.path.abspath(tempdir + "/" + runtime + "_" + basename + "_fps_overlay.mp4")])

#shutil.rmtree(tempdir)
os.remove(tempoverlay)

print "OK, All done!"