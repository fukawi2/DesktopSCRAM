#!/usr/bin/python2
import getopt   # for parsing command line options
import fcntl
import serial
import termios
import time
import os
import sys
from stat import *

def main():
  ### this attempts to set 'defaults' based on the OS
  uname = os.uname()[0]
  if uname == 'Linux':
    ### Linux OS
    cmd_start_screensaver = 'xflock4'
    cmd_pause_music = 'pgrep mpd > /dev/null && mpc pause'
  elif uname == 'Darwin':
    ### Apple OS X
    # pause iTunes (note that this always pauses; if it's not playing, it has
    # no effect). it's kinda ugly; if iTunes isn't already running, osascript
    # will start it, then dutifully tell it to pause. Gee, thanks. This should
    # stop that.
    cmd_pause_music = '[[ -n `ps -ef | grep iTunes | grep -v grep | grep -v iTunesHelper` ]] && osascript -e \'tell application "iTunes" to pause\''
    # lock screen (which is really just "start screensaver"; you need to
    # configure screen saver to lock the screen when it starts).
    cmd_start_screensaver = '/System/Library/Frameworks/ScreenSaver.framework/Resources/ScreenSaverEngine.app/Contents/MacOS/ScreenSaverEngine'
  else:
    # Uhoh, unknown OS.
    print 'Unable to determine OS (Linux or Darwin). Aborting.'
    sys.exit(1)

  ### override defaults with command line input?
  # -d = device to use
  # -S = signal to wait for
  # -l = lock command
  # -p = pause command
  try:
    opts, args = getopt.getopt(sys.argv[1:], "hd:S:l:p:", ["help", "device=", "signal=", "lock=", "pause="])
  except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)

  device = None
  signal = 'dsr'; # default
  cmd_pause = cmd_pause_music
  cmd_lock = cmd_start_screensaver
  for opt, arg in opts:
      if opt in ("-h", "--help"):
          usage()
          sys.exit()
      elif opt in ("-d", "--device"):
          device = arg
      elif opt in ("-S", "--signal"):
          signal = arg
      elif opt in ("-l;", "--lock"):
          cmd_lock = arg
      elif opt in ("-p", "--pause"):
          cmd_pause = arg
      else:
          assert False, "unhandled option"

  ### validate our options
  if signal:
    if signal.lower() == 'cts':
      signal = termios.TIOCM_CTS;
    elif signal.lower() == 'dsr':
      signal = termios.TIOCM_DSR;

  if device:
    if not os.path.exists(device):
      print "Device not found: %s" % device
      sys.exit(3)
    mode = os.stat(device).st_mode
    if not S_ISCHR(mode):
      print "Invalid device: %s" % device
      sys.exit(3)
    if not os.access(device, os.R_OK):
      print "Permission denied: %s" % device
      sys.exit(3)
  else:
    print "No device specified"
    sys.exit(3)

  last_event = time.time()

  # Main
  while True:
    try:
      print "Trying to open a connection..."
      # Open the serial device; this is the specific USB/Serial adapter model I'm using
      s = serial.Serial(device)
      print "Got!"
      while True:
        print "Waiting for DTR change..."
        fcntl.ioctl(s.fd, termios.TIOCMIWAIT, (signal))
        # Debounce.
        # (Also ignores events in the first 2s of runtime)
        if time.time() - last_event < 2:
          print "DTR changed, but ignored as a bounce"
          continue
        # Do useful stuff
        print "DTR changed, activating!"
        os.system(cmd_pause)
        os.system(cmd_lock)
        last_event = time.time();
    except:
      # Something died. Wait and try again.
      print "Failed. Will try again in a bit."
      print sys.exc_info()[0]
      time.sleep(30)
      pass

def usage():
  print "-d = device to use"
  print "-S = signal to wait for"
  print "-l = lock command"
  print "-p = pause command"

# apparently main() isn't good enough for python, you have to explicitly
# start it. what a princess.
if __name__ == "__main__":
  main()
