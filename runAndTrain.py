import os
import time

from PIL import ImageGrab, ImageTk
from tkinter import *
from pathlib import Path
from functools import partial

import Link2create as Create
import Link2train as Train
import Link2classit as ClassIt

# arguments
name = "dice"
dicePos = (2850, 700, 2950, 800)  # top-left, bottom-right coordinates
timeToDecide = 10  # sec
boxPos = "under"  # left | right | under | above
numberOfClasses = 2
classNames = ["six", "not six"]
learnAfterThisManySample = 20

# global variable to store the captured image
image = ""


class MyDialog(Toplevel):
    def __init__(self, parent, numberOfClasses, classNames, cl):
        Toplevel.__init__(self, parent)
        Label(self, text=classNames[cl]).grid(row=0, column=0, columnspan=2, padx=50, pady=10)

        for i in range(numberOfClasses):
            b = Button(self, text=classNames[i], command=partial(self.bPress, i), width=8)
            b.grid(row=1, column=i, padx=10, pady=10)

        self.answer = None
        # self.protocol("WM_DELETE_WINDOW", self.no)
        self.title(str(cl))
        self.wm_attributes('-type', 'splash')  # remove title bar, probably just in linux

    def bPress(self, i):
        self.answer = i
        self.destroy()

    def noAnswer(self):
        self.destroy()


def countSamples():
    num = 0
    for i in os.listdir(name + "/classes"):
        num += len(os.listdir(name + "/classes/" + i + "/"))
    return num


def main(argv):
    global image

    # TODO arguments

    width = dicePos[2] - dicePos[0]
    height = dicePos[3] - dicePos[1]

    # Create new CNN if not exist
    if not Path(name).exists():
        Create.main(["", name, numberOfClasses, width, height])

    # get the number of samples
    numberOfSamples = countSamples()

    # Grab the screen region, also save the captured images
    image = ImageGrab.grab(bbox=dicePos)
    image.save('img.png', 'PNG')
    cl = ClassIt.main(["", name, "img.png"])

    # Create the root window with the image in it, place it in to the image's position
    root = Tk()
    root.geometry('%dx%d+%d+%d' % (width, height, dicePos[0], dicePos[1]))
    root.wm_attributes('-type', 'splash')  # remove title bar, probably just in linux
    canvas = Canvas(width=width, height=height, master=root)
    canvas.pack()
    image = ImageTk.PhotoImage(image)
    canvas.create_image(width, height, anchor=SE, image=image)

    # Create the asking dialog, placing it to the desired position
    d = MyDialog(root, numberOfClasses, classNames, cl)
    d.update()  # Have to update to get the width/height, also it blinks for a moment
    dWidth = d.winfo_width()
    dHeight = d.winfo_height()
    if boxPos == "left":
        geom = (dWidth, dHeight, dicePos[0] - dWidth, dicePos[1])
    elif boxPos == "right":
        geom = (dWidth, dHeight, dicePos[0] + width, dicePos[1])
    elif boxPos == "above":
        geom = (dWidth, dHeight, dicePos[0], dicePos[1] - dHeight)
    else:  # boxPos == "under" | default
        geom = (dWidth, dHeight, dicePos[0], dicePos[1] + height)
    d.geometry('%dx%d+%d+%d' % geom)

    # Kill everything after [timeToDecide] sec
    afterID = root.after(1000 * timeToDecide, d.noAnswer)
    root.wait_window(d)
    root.after_cancel(afterID)
    answer = d.answer
    root.destroy()
    if answer is not None:  # If there is answer
        # Move the image into the correct folder, and rename
        newName = str(time.time()) + ".png"
        os.rename("img.png", name + "/classes/" + str(answer) + "/" + newName)

        # If the human answer is not equal to the AI prediction
        ''' 
        if answer != cl:
             Train.main(["", name, newName])  # train only the image
        '''
        # Train.main(["", name])  # train all images once

        numberOfSamples += 1

    print(numberOfSamples)
    # If we reached a set number of samples, we'll train
    if numberOfSamples > 0 and numberOfSamples % learnAfterThisManySample == 0:
        Train.main(["", name, "10"])  # train all images 10 times


if __name__ == '__main__':
    while 1:
        main(sys.argv)
        input("Press Enter to continue...")
