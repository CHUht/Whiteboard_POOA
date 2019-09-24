from tkinter import *

def hello(event):
    print("Single Click, Button-1" )

def quit(event):
    print("Double Click, stopping")
    sys.exit()

widget = Button(None, text = "Mouse Clicks")
widget.pack()
widget.bind('<Motion>', hello)
widget.bind('<Double-1>', quit)
widget.mainloop()