from pynput.keyboard import Key, Listener
import argparse
import tempfile
import queue
import sys
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback

#Knappe ting
from signal import pause
from gpiozero import Button
button = Button(2)


assert numpy  # avoid "imported but unused" message (W0611)
import threading

is_recording = False
             
             
             

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    "-l",
    "--list-devices",
    action="store_true",
    help="show list of audio devices and exit",
)
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser],
)
parser.add_argument(
    "filename", nargs="?", metavar="FILENAME", help="audio file to store recording to"
)
parser.add_argument(
    "-d", "--device", type=int_or_str, help="input device (numeric ID or substring)"
)
parser.add_argument("-r", "--samplerate", type=int, help="sampling rate")
parser.add_argument(
    "-c", "--channels", type=int, default=1, help="number of input channels"
)
parser.add_argument(
    "-t", "--subtype", type=str, help='sound file subtype (e.g. "PCM_24")'
)
args = parser.parse_args(remaining)

q = queue.Queue()


def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())


def rec_unlimited():
    try:
        # Filename is set to output plus local time
        named_tuple = time.localtime() # get struct_time
        time_string = time.strftime("%m-%d-%Y %H-%M-%S", named_tuple)
        filename1 = "output"+' '+time_string
        
        device_info = sd.query_devices(args.device, "input")
        # soundfile expects an int, sounddevice provides a float:
        #args.samplerate = int(device_info["default_samplerate"])
        args.samplerate = 44100
        args.filename = tempfile.mktemp(
            prefix=filename1, suffix=".wav", dir=""
        )

        # Make sure the file is opened before recording anything:
        with sf.SoundFile(
            args.filename,
            mode="x",
            samplerate=args.samplerate,
            #channels=args.channels,
            channels=2,
            subtype=args.subtype,
        ) as file:
            with sd.InputStream(
                samplerate=args.samplerate,
                device=args.device,
                #channels=args.channels,
                channels=2,
                callback=callback,
            ):
                print("Starting recording")
                while is_recording:
                    file.write(q.get())
                print("Stopping recording")

    except KeyboardInterrupt:
        print("\nRecording finished: " + repr(args.filename))
        parser.exit(0)
    except Exception as e:
        print(e)
        parser.exit(type(e).__name__ + ": " + str(e))


def on_press(key):
    if key == Key.alt_l:
        print("alt t pressed")
        global is_recording
        is_recording = False
    if key == Key.enter:
        print("Recording: {0}".format(is_recording))


def on_release(key):
    if key == Key.alt_l:
        print("alt t released")
        global is_recording
        is_recording = True
        t = threading.Thread(target=rec_unlimited)
        t.start()
    if key == Key.esc:
        return False


# Button GPIO Shit
def say_hello():
    global is_recording
    is_recording = False

def say_goodbye():
    print("farvel")
    #Afspil introlyd
    filename = "intro.wav"
    data2, fs = sf.read(filename, dtype="float32")
    sd.play(data2,fs)
    status = sd.wait()
    
    #Begin recording
    global is_recording
    is_recording = True
    t = threading.Thread(target=rec_unlimited)
    t.start()

button.when_released = say_goodbye
button.when_pressed = say_hello
while True:
    pause()

with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
    
    
