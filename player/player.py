# -*- coding: utf-8 -*-
import vidx

from Tkinter import *   
import tkFileDialog,tkMessageBox,tkFont

import time
import os
from io import BytesIO

import zipfile
import uuid
import cv2
from PIL import Image

import json

import webbrowser

import random

PLAYER_VERSION = "v1.0.0"

def get_unique_uuid(used):
    "Get a unique UUID, guaranteed not to be in the list used"
    i = uuid.uuid4()
    while i in used:
        i = uuid.uuid4()
    return i

class App:
    def __init__(self, master):
        "Initialise widgets and some app attributes"
        
        self.root = master
        
        self.create_widgets()
        
        self.player = vidx.VidxPlayer() # Create the VidxPlayer

        self.cancelled_convert = False # Initialise cancelled_convert
        
        self.is_converting = False # Initialise is_converting

        if os.path.isfile("config.json"): # If config.json exists, try to load it
            try:
                with open("config.json","r") as f:
                    self.config = json.loads(f.read())
            except: # It couldn't be opened
                tkMessageBox.showerror("Couldn't load config", "config.json exists but is invalid: repair it, or delete it and a new file will be created.")
                self.root.destroy()
        else: # It needs to be created
            default_config = """
{
    "dialogs": {
        "open": "%UserProfile%",
        "convert-in": "%UserProfile%",
        "convert-out": "%UserProfile%"
        }
}
"""
            self.config = json.loads(default_config)
            self.save_config()
            
                

    def save_config(self):
        "Update the config file with the current application config"
        with open("config.json","w") as f:
            json.dump(self.config, f)

    def create_widgets(self):
        "Create and initialise widgets"
        
        self.root_frame = Frame(self.root, bg="black") # Container frame
        self.root_frame.pack(expand=True, anchor=N,fill=BOTH,side=LEFT)

        self.canvas = Canvas(self.root_frame, width=640, height=480,highlightthickness=0) # Main video playback canvas
        self.canvas.pack()
        
        self.controls = Frame(self.root_frame, height=30, bg="black") # Controls container, including status bar

        self.scrub_bar = Scrollbar(self.controls) # Scrub bar is actually a scrollbar
        self.scrub_bar.config(orient=HORIZONTAL, command=self.scrub_handle, width=25)
        self.scrub_bar.pack(side=TOP,fill=X)

        self.play = Button(self.controls, # Play/pause button
                           text="Play/Pause",
                           command=self.play_pause,
                           height=2)
        
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
        self.root.config(menu=menubar) # Configure the root element to use this as the menu bar

        fileMenu = Menu(menubar,tearoff=False) # Create the file menu
        fileMenu.add_command(label="Open .vidx file", underline=0,command=self.menu_open, accelerator="Ctrl+O")
        self.root.bind_all("<Control-o>", self.menu_open)
        
        fileMenu.add_separator()
        fileMenu.add_command(label="Convert video file", underline=0,command=self.menu_convert)
        fileMenu.add_separator()

        fileMenu.add_command(label="Exit", underline=1, command=self.on_exit, accelerator="Alt+F4")
        
        helpMenu = Menu(menubar,tearoff=False)


        helpMenu.add_command(label="About", underline=0,command=self.menu_about) # Create the about menu
        helpMenu.add_separator()
        helpMenu.add_command(label="Documentation", underline=0,command=self.menu_documentation)
        
        menubar.add_cascade(label="File", underline=0, menu=fileMenu)
        
        menubar.add_cascade(label="Help", underline=0, menu=helpMenu)
        
    def update_image(self):
        "Update the canvas image to be the current vidx file frame image"
        if self.player.vidx != None:
            self.root.image=image =app.player.get_frame()
            app.canvas.create_image(0,0,image=image,anchor=NW)
        else:
            app.canvas.create_rectangle(0,0,app.canvas.cget("width"), app.canvas.cget("height"), fill="black")
            
    def scrub_handle(self,event,pos,*args):
        "Called when the scrub handle is moved"
        actual_pos = float(pos) / (1-app.bar_width) # Calculate how far through the video the handle position represents

        # Necessary to round as otherwise int floors, meaning that low frame count videos would be harder to navigate
        self.player.set_frame(int(round(actual_pos * (self.player.vidx.frames-1))))
        
        self.update_handle()
        
    def update_handle(self):
        "Moves the scrub handle based on video playback position"
        if self.player.vidx:
            progress = (float(self.player.current_frame) / float(self.player.vidx.frames-1)) * (1-self.bar_width) # Update the scrub bar based on video position
            self.scrub_bar.set(progress, progress+self.bar_width)
            self.root.update()
        else:
            self.scrub_bar.set(0,1) # Makes the scrub bar disabled
            self.root.update()  

    def open_vidx(self,path):
        "Load a .vidx file"
        self.path = path
        self.status.config(state="active")
        cancelled = self.player.load_vidx(path, update_callback=self.update_open_progress) # Load the .vidx file, and check if it was cancelled
        if cancelled:
            self.status.config(state="disabled")
            self.cancelled_convert = False # Reset the cancelled_convert flag
            return
        
        self.bar_width = max(0.1, 1.0/self.player.vidx.frames) # Calculate the bar width
        self.scrub_bar.set(0,self.bar_width) # Reset the scrub bar position
        self.player.current_frame = 0
        self.canvas.config(width = self.player.vidx.dimensions[0], height=self.player.vidx.dimensions[1]) # Make the canvas the correct size for the video
        
        self.root.geometry("{0}x{1}".format(self.player.vidx.dimensions[0], self.player.vidx.dimensions[1]+self.controls.winfo_height())) # Make the window the correct size to fit the video and controls
        self.update_image()
        self.root.title("BeanoPlayerⒷ {0} - {1}".format(PLAYER_VERSION,path))
        
    def menu_about(self,*args):
        "When the Help>About menu item is clicked"
        
        t = Toplevel(self.root) # Create the about window
        t.wm_title("About BeanoPlayer")
        t.focus_force() # Bring the window to the top
        t.grab_set() # Force the window to stay on top
        t.iconbitmap('resource\\icon.ico')

        self.root.attributes("-disabled",True) # Disable root to prevent flickery behaviour when attempting to focus main window
        
        t.protocol("WM_DELETE_WINDOW", lambda *args: (self.root.attributes("-disabled",False), t.destroy())) # Re-enable root when the About window closes

        title_font = tkFont.Font(weight="bold", size="16") # Title font
        
        title = Label(t, text="\nBeanoPlayerⒷ {0}".format(PLAYER_VERSION), font=title_font) # Title label
        title.pack(side="top", fill="x", expand=True, padx=50)

        link_font = tkFont.Font(size="12",underline=True) # Link font

        subtitle = Label(t, text="on Github".format(PLAYER_VERSION), fg="blue", cursor="hand2", font=link_font) # Subtitle with link to Discord
        subtitle.pack(side="top", fill="x", expand=True)
        subtitle.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/seagull-pat/beanoplayer"))

        
        lic = Label(t, text="\nLicensed under GNU LGPLv3\n", fg="blue", cursor="hand2", font=link_font) # License text
        lic.bind("<Button-1>", lambda e: webbrowser.open("https://www.gnu.org/licenses/lgpl-3.0.en.html"))
        lic.pack(side="top")

        body_font = tkFont.Font(size="12") # Body font (size=12 is same as default but good to make sure it's the same)
        
        description = Label(t, text="Written by seagull-pat in roughly a week under the influence of sleeplessness and long car journeys.\n", font=body_font, wraplength=250) # Description text
        description.pack(side="top", padx=20)

        # Randomly choose a message for the server link
        discord_link = Label(t, text=random.choice(["And if your day is going just a bit too well, you can always check out the unofficial CyberDiscovery Discord server",
                                                    "Fancy significantly worsening your mood? Have a look at the unofficial CyberDiscovery Discord server",
                                                    "Want to talk to the next generation of lonely computer nerds? Check out the unofficial CyberDiscovery Discord server",
                                                    "Feel like your faith in the UK's cyber defenses could do with taking down a notch? Check out the unofficial CyberDiscovery Discord server",
                                                    "Want to talk to a top Canadian forensicator, but feel like email doesn't have enough screaming children? Join the unofficial CyberDiscovery Discord server"])+"\n",
                             fg="blue",
                             cursor="hand2",
                             font=link_font,
                             wraplength=250)
        
        discord_link.pack(side="top", padx=20)
        discord_link.bind("<Button-1>", lambda e: webbrowser.open("https://discord.gg/Kf8n5rT"))

    def menu_documentation(self,*args):
        "When the Help>Documentation menu item is selected"
        webbrowser.open("https://github.com/seagull-pat/beanoplayer/wiki")

    def menu_open(self, *args):
        "Called when the File>Open .vidx command is selected"
        path = tkFileDialog.askopenfilename(initialdir = self.config["dialogs"]["open"],title = "Select .vidx",filetypes = (("VIDX files","*.vidx"),("All files","*.*"))) # Prompt for a file path

        if path != "": # If a path was actually selected
            self.config["dialogs"]["open"] = os.path.split(path)[0] # Update the last dialog path config
            self.save_config() # Save config
            
            self.status_text.set("Opening {0}".format(path)) # Update status
            self.root.update() # Prevent freezing
            self.open_vidx(path)
            self.status_text.set("Ready") # Reset status when opening finished

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
        self.is_converting = True
        try:
            "Called when the File>Convert video file command is selected"
            inpath = tkFileDialog.askopenfilename(initialdir = self.config["dialogs"]["convert-in"],title = "Select input video file", # Prompt to select input video file
            filetypes = (("Video files","*.mp4 *.mov *.avi"),("All files","*.*")))
            
            if inpath=="": return # If no file selected, return
            self.config["dialogs"]["convert-in"] = os.path.split(inpath)[0]
            self.save_config()
            
            outpath = tkFileDialog.asksaveasfilename(initialdir = self.config["dialogs"]["convert-out"],title = "Select .vidx destination", # Prompt to select .vidx destination
            filetypes = (("VIDX files","*.vidx"),("All files","*.*")))
            
            if outpath=="": return # If no file selected, return
            self.config["dialogs"]["convert-out"] = os.path.split(outpath)[0]
            self.save_config()

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
            
        finally:
            self.is_converting = False

    def on_exit(self):
        self.on_window_close()

    def play_pause(self):
        "Toggle the value of self.player.state"
        self.player.state = 0 if self.player.state == 1 else 1
        
    def on_window_close(self):
        if self.is_converting:
            if tkMessageBox.askokcancel("Quit", "You are currently converting a file, are you sure that you want to quit?"):
                self.root.destroy()
        else:
            self.root.destroy()

root = Tk()
root.title("BeanoPlayerⒷ {0}".format(PLAYER_VERSION))
root.iconbitmap('resource\\icon.ico')


app = App(root)

app.player = vidx.VidxPlayer()
app.update_image()


last_frame=-1 # So that last_frame will always be different when update is first called

last_time = time.time() # The last time update was started

def update():
    global last_frame,last_time
    
    app.update_handle() # Update scrub bar position

    image_start = time.time()
    if last_frame != app.player.current_frame:
        app.update_image()
        last_frame=app.player.current_frame
    image_delta = time.time() - image_start
    
    if app.player.state != 1: # We have paused
        app.fps_text.set("")
        root.after(100,update) # Check again in 0.1s if we have unpaused
        return
    if app.player.vidx:
        app.player.add_frame() # Advance to the next frame

    last_delta = time.time()-last_time
    last_time = time.time()

    app.fps_text.set("{0:.1f} target fps, {1:.1f} actual fps".format(1000.0/app.player.needed_frame_time, 1.0/last_delta))
    
    # Figure out how long we should wait, given that we will already have used some time updating the image
    root.after(max(0, int(app.player.needed_frame_time)-int(image_delta*1000)),update) 


root.protocol("WM_DELETE_WINDOW", app.on_window_close)

root.after(0,update)
root.mainloop()
