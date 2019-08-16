# -*- coding: utf-8 -*-
import vidx

from Tkinter import *   
import tkFileDialog,tkMessageBox

import time
import os
from io import BytesIO

import zipfile
import uuid
import cv2
from PIL import Image



def get_unique_uuid(used):
    i = uuid.uuid4()
    while i in used:
        i = uuid.uuid4()
    return i

class App:

    def __init__(self, master):
        "Initialise widgets and some app attributes"
        
        self.root = master
        
        self.root_frame = Frame(master, bg="black") # Container frame
        self.root_frame.pack(expand=True, anchor=N,fill=BOTH,side=LEFT)

        self.canvas = Canvas(self.root_frame, width=640, height=480,highlightthickness=0) # Main video playback canvas
        self.canvas.pack()
        
        self.controls = Frame(self.root_frame, height=30, bg="black") # Controls container, including status bar

        self.scrub_bar = Scrollbar(self.controls) # Scrub bar is actually a scrollbar
        self.scrub_bar.config(orient=HORIZONTAL, command=self.scrub_handle, width=25)
        self.scrub_bar.pack(side=TOP,fill=X)

        self.play = Button(self.controls, text="Play/Pause", command=self.play_pause, height=2)
        self.play.pack(side=TOP,fill=X)
        
        
        self.status_text = StringVar() # Status bar variable
        self.status = Button(self.controls,
                             state="disabled",
                             text="Ready",
                             bd=1,
                             relief=SUNKEN,
                             anchor=W,
                             textvariable=self.status_text,
                             command = self.cancel_convert) # When clicked (not disabled) cancel_convert is called
        
        self.status.pack(fill=X,side=BOTTOM)
        self.status_text.set("Ready")

        self.fps_text = StringVar() # Status bar variable
        self.status_fps = Label(self.status,
                             text="Ready",
                             bd=1,
                             anchor=W,
                             textvariable=self.fps_text)
        
        self.status_fps.pack(fill=X,side=RIGHT)
        self.fps_text.set("")
        
        self.controls.place(relx=1.0,rely=1.0,x=0,y=0, anchor=SE, relwidth=1) # Places the controls/status container so it stays at the bottom of the window


        menubar = Menu(self.root_frame) # Create the top menu bar
        master.config(menu=menubar) # Configure the root element to use this as the menu bar

        fileMenu = Menu(menubar,tearoff=False) # Create the file menu


        fileMenu.add_command(label="Open .vidx file", command=self.menu_open)
        fileMenu.add_separator()
        fileMenu.add_command(label="Convert video file", command=self.menu_convert)
        fileMenu.add_separator()

        fileMenu.add_command(label="Exit", underline=0, command=self.on_exit)
        
        menubar.add_cascade(label="File", underline=0, menu=fileMenu)

        self.player = vidx.VidxPlayer() # Create the VidxPlayer

        self.cancelled_convert = False # Initialise cancelled_convert

    def update_image(self):
        "Update the canvas image to be the current vidx file frame image"
        if self.player.vidx != None:
            self.root.image=image =app.player.get_frame()
            app.canvas.create_image(0,0,image=image,anchor=NW)
        else:
            app.canvas.create_rectangle(0,0,app.canvas.cget("width"), app.canvas.cget("height"), fill="black")
            
    def scrub_handle(self,event,pos,*args):
        "Called when the scrub handle is moved"
        actual_pos = float(pos) / (1-app.bar_width)
        self.player.set_frame(int(round(actual_pos * (self.player.vidx.frames-1))))
        self.update_handle()
        
    def update_handle(self):
        "Moves the scrub handle based on video playback position"
        if self.player.vidx:
            progress = (float(self.player.current_frame) / float(self.player.vidx.frames-1)) * (1-self.bar_width)
            self.scrub_bar.set(progress, progress+self.bar_width)
            self.root.update()
        else:
            self.scrub_bar.set(0,1)
            self.root.update()  

    def open_vidx(self,path):
        "Load a .vidx file"
        self.path = path
        self.status.config(state="active")
        cancelled = self.player.load_vidx(path, update_callback=self.update_open_progress)
        if cancelled:
            self.status.config(state="disabled")
            self.cancelled_convert = False
            return
        self.bar_width = max(0.1, 1.0/self.player.vidx.frames)
        self.scrub_bar.set(0,self.bar_width)
        self.player.current_frame = 0
        self.canvas.config(width = self.player.vidx.dimensions[0], height=self.player.vidx.dimensions[1])
        self.update_image()
        self.root.title("BeanoPlayerⒷ 11 - {0}".format(path))

    def menu_open(self):
        "Called when the File>Open .vidx command is selected"
        path = tkFileDialog.askopenfilename(initialdir = "/",title = "Select .vidx",filetypes = (("VIDX files","*.vidx"),("All files","*.*")))
        if path != "":
            self.status_text.set("Opening {0}".format(path))
            self.root.update()  
            self.open_vidx(path)
            self.status_text.set("Ready")

    def update_open_progress(self, progress):
        if self.cancelled_convert: # If the cancelled_convert flag was set as a result of the status bar being clicked...
                self.status_text.set("Ready") # update status bar text
                self.status.config(state="disabled") # disable the status bar as a button
                return True
        self.status_text.set("Opening {0}, {1:.2f}% (click to cancel)".format(self.path, progress*100.0))
        self.root.update()
        
    def cancel_convert(self):
        "Called when the status bar is clicked, to cancel the conversion"
        self.cancelled_convert = True
        
    def menu_convert(self):
        "Called when the File>Convert video file command is selected"
        inpath = tkFileDialog.askopenfilename(initialdir = "/",title = "Select input video file", # Prompt to select input video file
        filetypes = (("Video files","*.mp4 *.mov *.avi"),("All files","*.*")))
        if inpath=="": return # If no file selected, return

        outpath = tkFileDialog.asksaveasfilename(initialdir = "/",title = "Select .vidx destination", # Prompt to select .vidx destination
        filetypes = (("VIDX files","*.vidx"),("All files","*.*")))
        if outpath=="": return # If no file selected, return

        capture = cv2.VideoCapture(inpath) # Create the video capture from the input path

        if not os.path.isdir("tmpwrite"): # Create tmpwrite if it doesn't exist
                os.mkdir("tmpwrite")

        # Clear tmpwrite folder, as its entire contents (excluding files beginning with '.') are made into a .vidx
        filelist = [ f for f in os.listdir("tmpwrite") ]
        for f in filelist:
            if not f.startswith("."): # Ignore .gitkeep etc
                os.remove(os.path.join("tmpwrite", f))


        frames = 0 # Number of frames converted so far
        total_frames_estimate = capture.get(cv2.CAP_PROP_FRAME_COUNT) # Estimate for total number of frames
        
        used_guids = [] # GUIDs already used for .gif filenames
        last_timestamp = 0 # The timestamp in ms from the start of the video of the last converted frame, used to calculate duration

        self.status.config(state="active") # Enable the status bar as a cancel button
        
        while True:
            percentage = 100*float(frames)/float(total_frames_estimate) # Calculate and display an estimate of conversion progress
            self.status_text.set("Working {:.2f}% (click to cancel)".format(percentage))
            
            success,image = capture.read() # Capture the next image in the file
            
            frame_duration = int(capture.get(cv2.CAP_PROP_POS_MSEC)-last_timestamp) # Calculate this frame duration
            
            last_timestamp = capture.get(cv2.CAP_PROP_POS_MSEC) # Update last_timestamp
            
            if not success: break # Exit the loop if the image could not be read
            
            pil_image = Image.fromarray(cv2.cvtColor(image,cv2.COLOR_BGR2RGB)) # Convert the image to a PIL image

            image_guid = get_unique_uuid(used_guids) # Generate a GUID for the .gif, and update the list of used GUIDs
            used_guids.append(image_guid)

            image_guid = "{"+str(image_guid)+"}" # Create the full GUID

            
            
            with open("tmpwrite\\"+vidx.index_to_GUID(frames)+".xml", "w") as f: # Create the frame descriptor file
                f.write("""<?xml version="1.0"?>
<frame>
	<meta>
		<subtitle></subtitle>
	</meta>
	<frame-info>
		<duration>{0}</duration>
		<data-guid>{1}</data-guid>
	</frame-info>
</frame>""".format(frame_duration,image_guid))
                
            pil_image.save("tmpwrite\\{0}.gif".format(image_guid), format="gif") # Save the .gif

            self.root.update() # Update the tkinter window to avoid freezing
            
            if self.cancelled_convert: # If the cancelled_convert flag was set, as a result of the status bar being clicked...
                self.cancelled_convert = False # reset it
                self.status_text.set("Ready") # update status bar text
                self.status.config(state="disabled") # disable the status bar as a button
                tkMessageBox.showwarning( # Show the cancellation message
                ".vidx conversion",
                "Cancelled conversion"
                )

                return # Stop conversion
            frames += 1 # Another frame has been converted

        with open("tmpwrite\\"+vidx.MAGIC_GUID+".xml", "w") as f: # Create file descriptor
            f.write("""<?xml version="1.0"?>
<video>
	<version>11</version>
	<width>{0}</width>
	<height>{1}</height>
	<frames>{2}</frames>
</video>""".format(int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                   int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                   int(frames)))

        self.status_text.set("Compressing...")
        zipf = zipfile.ZipFile(outpath, 'w', zipfile.ZIP_DEFLATED)

        for root, dirs, files in os.walk("tmpwrite"):
            for f in files:
                if not f.startswith("."):
                    zipf.write(os.path.join(root,f), f)

        zipf.close()

        self.status_text.set("Ready")
            
        tkMessageBox.showinfo(
            ".vidx conversion",
            "Successfully converted to .vidx"
        )

    def on_exit(self):
        self.quit()

    def play_pause(self):
        "Toggle the value of self.player.state"
        self.player.state = 0 if self.player.state == 1 else 1

root = Tk()
root.title("BeanoPlayerⒷ 11")
root.iconbitmap('resource\\icon.ico')

app = App(root)

app.player = vidx.VidxPlayer()

app.update_image()

last_frame=-1

last_time = time.time()



def update():
    global last_frame,last_time
    
    app.update_handle()

    image_start = time.time()
    if last_frame != app.player.current_frame:
        app.update_image()
        last_frame=app.player.current_frame
    image_delta = time.time() - image_start
    
    if app.player.state != 1:
        app.fps_text.set("")
        root.after(100,update)
        return
    if app.player.vidx:
        app.player.add_frame()

    last_delta = time.time()-last_time
    last_time = time.time()

    app.fps_text.set("{0:.1f} target fps, {1:.1f} actual fps".format(1000.0/app.player.needed_frame_time, 1.0/last_delta))
    
    root.after(max(0, int(app.player.needed_frame_time)-int(image_delta*1000)),update)
    
root.after(0,update)

root.mainloop()
