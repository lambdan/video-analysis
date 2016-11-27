import os
import subprocess
from subprocess import check_output
import sys
import matplotlib.pyplot as plt
from natsort import natsorted
import time
import datetime

runtime = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

def to_hhmmss(sec): # https://thingspython.wordpress.com/2010/09/27/code-golf-converting-seconds-to-hhmmss/
    min,sec = divmod(sec,60)
    hr,min = divmod(min,60)
    return "%d:%02d:%06.3f" % (hr,min,sec)

def screenshot(sec):
	# take a screenshot using ffmpeg
	subprocess.call(['ffmpeg', '-y', '-ss', str(sec), '-i', inputfile, '-loglevel', 'panic', '-vframes', str(1), '-q:v', str(1), inputfile[:-4] + "_peak.jpg"])

if len(sys.argv) < 2:
	print "No input file"
	sys.exit(1)
else:
	inputfile = str(sys.argv[1])
	if not os.path.isfile(inputfile):
		print "That doesnt seem to be a file: " + inputfile
		sys.exit(1)

print "Input file: " + inputfile

extension = ".mp4"
og_video_name = os.path.basename(inputfile)[:-4]
basename = os.path.basename(inputfile)[:-4]
tempdir = "Bitrate_" + basename
chunksdir = os.path.join(tempdir + "/chunks/")
bitratestxt = os.path.abspath(tempdir + "/" + runtime + "-bitrates.txt")
if os.path.exists(tempdir) is False:
	os.makedirs(tempdir)

tempfile = os.path.abspath(tempdir + "/" + basename + '_transcode.mp4')

if os.path.exists(tempfile):
	print "Transcode found. We don't need to do it again."
else:
	print "Transcoding video to H264 with keyframe interval=1" #TODO check if the video is already H264 and keyint 1
	# crf 0 is a bit excessive, crf 15 would probably be enough
	subprocess.call(['ffmpeg', '-i', inputfile, '-g', '1', '-loglevel', 'panic', '-preset', 'ultrafast', '-crf', '0', tempfile])

if os.path.exists(chunksdir) is False:
	os.makedirs(chunksdir)

if os.path.isfile(chunksdir + "0.mp4") is False:
	print "Splitting input into 1 second chunks..."
	subprocess.call(['ffmpeg', '-i', tempfile, '-an', '-c:v', 'copy', '-loglevel', 'panic', '-segment_time', "1", '-map', '0', '-f', 'segment', os.path.join(chunksdir + "%0d" + extension)])
	print "OK!"
else:
	print "Chunks found... skipping step"

# Get names of all the chunks and sort them
allfiles = [f for f in os.listdir(chunksdir) if os.path.isfile(os.path.join(chunksdir + f))]
allfiles = natsorted(allfiles)
chunks = []
for file in allfiles:
	abspathed = os.path.abspath(chunksdir + file)
	chunks.append(abspathed)

print "Getting bitrate of each chunk..."
bitrates = []
for chunk in chunks:
	BITRATE = (int(check_output(["mediainfo", '--Inform=Video;%BitRate%', chunk]))/1000)
	bitrates.append(BITRATE)
print "OK!"

# Convert chunks (seconds) timestamps
timestamps = []
for time in chunks:
	a = os.path.basename(time)[:-4] # remove file ext
	b = int(a) # remvoe chunk_ and convert to int
	#print b
	timestamps.append(b)

# Combine into dictionary, with time as key, and bitrate as value
data = {}
if os.path.isfile(bitratestxt):
	os.remove(bitratestxt)
with open(bitratestxt, 'a') as f:
		f.write("Time(s)\tBitrate(kbps)\n")
for t in timestamps:
	with open(bitratestxt, 'a') as f:
		f.write(str(t) + "\t" + str(bitrates[t]) + "\n")
	data[t] = bitrates[t]

# Get peak bitrate
peakKey = max(data, key=data.get)
#print "peak=" + str(data[peakKey])
#screenshot(peakKey) # take screenshot
#print "Screenshot of peak taken"

# Generate subtitle for ffmpeg
if os.path.exists("subtitle.srt"):
	os.remove("subtitle.srt")
with open("subtitle.srt", 'a') as fi:
	for t in timestamps:
		fi.write(str(t) + "\n")
		fi.write(to_hhmmss(t) + " --> " + to_hhmmss(t+1) + " X1:70 X2:70 Y1:0 Y2:30\n")
		if t == peakKey:
			fi.write("<font color=red>"+ str(bitrates[t]) + " kbps</font>\n\n") # make the peak in red
		else:
			fi.write("<font color=yellow>"+ str(bitrates[t]) + " kbps</font>\n\n")



#print "Plotting..."
#calculate some positions, easier to do here
arrowx = (peakKey+(peakKey/15))
arrowy = (data[peakKey]+(data[peakKey]/200))
textx = (peakKey+(peakKey/3))
texty = (data[peakKey]+(data[peakKey]/20))
max_x = len(timestamps)
max_y = data[peakKey]+(data[peakKey]/10)
#now plot
plt.plot(data.keys(), data.values())
plt.axis([0, max_x, 0, max_y])
plt.title('Video Bitrate of ' + og_video_name, fontweight='bold')
plt.xlabel('Time (seconds)', fontstyle='italic')
plt.ylabel('Video Bitrate (kbps)', fontstyle='italic')
#plt.annotate('peak: ' + str(data[peakKey]) + ' kbps (at ' + to_hhmmss(peakKey) + ')', xy=(arrowx, arrowy), xytext=(textx, texty), arrowprops=dict(facecolor='red', shrink=0.05))
plt.savefig(os.path.abspath(tempdir + "/" + runtime + "_" + og_video_name + '_bitrate_plot.png'),dpi=400)
print "Graph saved"

print "Making video with bitrate overlay..."
subprocess.call(['ffmpeg', '-i', inputfile, '-crf', '20', '-preset', 'medium', '-vf', 'scale=-1:720,subtitles=subtitle.srt', '-loglevel', 'panic', '-flags' ,'+cgop' ,'-bf' ,'2' ,'-pix_fmt' ,'yuv420p' ,'-vprofile' ,'high' ,'-level' ,'4.1' ,'-movflags', 'faststart', '-g', '30', os.path.abspath(tempdir + "/" + runtime + "_" + og_video_name + "_bitrate_overlay.mp4")])

os.remove("subtitle.srt")

print "OK! You can find the goods in: " + os.path.abspath(tempdir)
#TODO: open the folder automatically, but cross-platform yada yada
print "(if you dont plan on analyzing this video again, you should remove the chunks folder and the transcode in there)"