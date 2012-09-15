#!/usr/bin/python2
import fcntl
import serial
import termios
import time
import os
import sys

# Config
# am I on OSX or Linux?
uname = os.uname()[0]
if uname == 'Linux':
	cmd_start_screensaver = 'xflock4'
	cmd_pause_music = 'pgrep mpd > /dev/null && mpc pause'
elif uname == 'Darwin':
	# pause iTunes (note that this always pauses; if it's not playing, it has no effect).
	# it's kinda ugly; if iTunes isn't already running, osascript will start it, then dutifully
	# tell it to pause. Gee, thanks. This should stop that.
	cmd_pause_music = '[[ -n `ps -ef | grep iTunes | grep -v grep | grep -v iTunesHelper` ]] && osascript -e \'tell application "iTunes" to pause\''
	# lock screen (which is really just "start screensaver"; you need to configure screen saver to lock the screen when it starts).
	cmd_start_screensaver = '/System/Library/Frameworks/ScreenSaver.framework/Resources/ScreenSaverEngine.app/Contents/MacOS/ScreenSaverEngine'
else:
	# do nothing.
	print 'Unable to determine OS (Linux or Darwin). Aborting.'
	sys.exit(1)

last_event = time.time()

# Main
while True:
	try:
		print "Trying to open a connection..."
		# Open the serial device; this is the specific USB/Serial adapter model I'm using
		s = serial.Serial('/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A400C1SY-if00-port0')
		print "Got!"
		while True:
			print "Waiting for DTR change..."
			fcntl.ioctl(s.fd, termios.TIOCMIWAIT, (termios.TIOCM_CTS))
			# Debounce.
			# (Also ignores events in the first 2s of runtime)
			if time.time() - last_event < 2:
				print "DTR changed, but ignored as a bounce"
				continue
			# Do useful stuff
			print "DTR changed, activating!"
			os.system(cmd_pause_music)
			os.system(cmd_start_screensaver)
			last_event = time.time();
	except:
		# Something died. Wait and try again.
		print "Failed. Will try again in a bit."
		print sys.exc_info()[0]
		time.sleep(30)
		pass
