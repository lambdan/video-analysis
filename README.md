Tools to get bitrate and framerate of video, for amusement

# bitrate.py

Converts a video into keyframe interval=1, then splits it into 1 second chunks and gets bitrate of each chunk. Then plots it out on a graph and also creates a video with bitrate overlay, with suitable quality (preset medium, crf 20) for a YouTube upload.

The bitrate number isn't really what you wanna look at, but I use it to see which parts of a video are more bitrate intensive than others (the graph is the most interesting).

https://www.youtube.com/watch?v=4HK5954eDFk

(Please note that the keyframe int=1 transcode I do uses preset ultrafast and crf0, this means it creates a lossless version of your original video, however at probably much, much higher bitrates. This works for my purposes as I wanna see which parts of a video are more intensive, but it should not be used to determine at what bitrate your capture card can capture.)

# framerate.py

Splits a video into 1 second chunks and then takes 60 screenshots (frames) of that second and tries to determine how many unique screenshots (frames) there are, to get framerate per second. Then plots it out on a graph and also creates a video with fps overlay.

https://www.youtube.com/watch?v=CTD1Ja4hMlI

Trying to figure out what framerate a video is much easier if you have a very, very high quality digital/lossless recording. An analog/compressed recording is much harder to analyze.

It is also easier to figure out the framerate if your video has a lot of movement. Something very static like the PS4 Menu or a title screen for a NES game are very hard to get a framerate of.

## How It Works

(This is subject to change, but this is how I'm currently doing it)

- Split video into 60 frames/screenshots per 1 second of video
- Open up n.BMP and n+1.BMP in ImageChops
- Use ImageChops.difference() on the two frames, this generates a picture showing the difference of the two frames
- Use Image.getcolors() on the difference picture, to get colors of the image as RGB components:
	- If the palette is None: It's all black, which means there is no difference between the frames: duped frame
	- If unique colors of palette is < 20: probably just alot of different variants of black (analogue interference, compression artifacts, etc): duped frame
	- If the palette has one color whose component is > 20: there is a pixel that is probably very colorful, maybe a spark: unique frame
	- Count how many pixels there are the in frame in total (pixels), and also count how many of those are blacks (max component of color is 10): if black/pixels >= black_threshold (99.9% need to be some sort of black at the time of writing): duped frame
- Check how many unique frames there were in 60 frames

# Requirements:

- Python 2.7
	- [Matplotlib](http://matplotlib.org/users/installing.html)
	- [Natsort](https://pypi.python.org/pypi/natsort)
	- [Pillow](http://pillow.readthedocs.io/en/3.0.x/installation.html) (framerate.py only)
- ffmpeg (in $PATH)
- mediainfo (in $PATH) (bitrate.py only)

(How to get stuff into your $PATH is very specific for your particular OS setup, so I can't help you. Personally I install Ruby (making sure to select the "Add to PATH"-option) and then put stuff in `C:\Ruby-xx\bin`)

# Usage

- Install the requirements
- Download bitrate.py or framerate.py, put them in a directory
- Go into this directory, open up a CMD or Terminal, and type in `bitrate.py /path/to/video_name.ext` or `framerate.py /path/to/video_name.ext`
- Wait
- After the script is done, it will have created a folder called `Bitrate_video_name` or `Framerate_video_name`, in there is your goods:
	- A MP4 with the framerate/bitrate number overlay. It will also be scaled to 720p so you can get YouTube 60fps for SD content
	- A PNG with a graph of your framerate/bitrate over time
- If you don't plan on analyzing the video again, you can remove the chunks & frames folders, and the eventual transcoded version of your video

Only tested on Windows 10, with an i7 and SSD.
Should work on macOS/Linux. I don't see a reason why it wouldn't.

# Wishlist / TODO

- both: live overlay of graph/plot on top of video
- bitrate.py: detect if video is already compatible (needs to be H264/AVC, and keyframe int=1)
- framerate.py: make solid color screens not go down to 0 fps (maybe look for a significant drop in framerate (60 -> 0) and consider it a fluke)
- framerate.py: make it more accurate