# -*- coding: utf-8 -*-
from Tkinter import *   
import time
import os
import vidx
import tkFileDialog,tkMessageBox
import uuid
import cv2
import zipfile

from PIL import Image

from io import BytesIO

def get_unique_uuid(used):
    i = uuid.uuid4()

    while i in used:
        i = uuid.uuid4()
    return i

class App:

    def __init__(self, master):

        self.root = master

        self.root_frame = Frame(master, bg="black")
        self.root_frame.pack(expand=True, anchor=N,fill=BOTH,side=LEFT)
  
        for i in range(10):
            self.root_frame.rowconfigure(i, weight=1)

        for i in range(10):
            self.root_frame.columnconfigure(i, weight=1)

        self.canvas = Canvas(self.root_frame, width=640, height=480,highlightthickness=0)
        self.canvas.pack()
        
        self.controls = Frame(self.root_frame, height=20,bg="black")
        
        
        for i in range(10):
            self.controls.rowconfigure(i, weight=1)

        for i in range(10):
            self.controls.columnconfigure(i, weight=1)

        self.scrub_bar = Scrollbar(self.controls)
        self.scrub_bar.config(orient=HORIZONTAL, command=self.scrub_handle, width=25)
        self.scrub_bar.pack(side=TOP,fill=X)

        self.play = Button(self.controls, text="Play/Pause", command=self.play_pause, height=2)
        self.play.pack(side=TOP,fill=X)

        
        
        self.status_text = StringVar()
        self.status = Label(self.root_frame, text="Ready", bd=1, relief=SUNKEN, anchor=W, textvariable=self.status_text)
        self.status.pack(fill=X,side=BOTTOM)
        self.status_text.set("Ready")
        
        self.controls.pack(side=BOTTOM,fill=X)

        menubar = Menu(self.root_frame)
        master.config(menu=menubar)

        fileMenu = Menu(menubar,tearoff=False)


        fileMenu.add_command(label="Open .vidx file", command=self.menu_open)
        fileMenu.add_separator()
        fileMenu.add_command(label="Convert video file", command=self.menu_convert)
       


        fileMenu.add_separator()

        fileMenu.add_command(label="Exit", underline=0, command=self.on_exit)
        menubar.add_cascade(label="File", underline=0, menu=fileMenu)

        self.player = vidx.VidxPlayer()

    def update_image(self):
        if self.player.vidx != None:
            self.root.image=image =app.player.get_frame()
            app.canvas.create_image(0,0,image=image,anchor=NW)
        else:
            app.canvas.create_rectangle(0,0,app.canvas.cget("width"), app.canvas.cget("height"), fill="black")
    def scrub_handle(self,event,pos,*args):
        actual_pos = float(pos) / (1-app.bar_width)
        self.player.set_frame(int(round(actual_pos * (self.player.vidx.frames-1))))
        self.update_handle()
        
    def update_handle(self):
        if self.player.vidx:
            progress = (float(self.player.current_frame) / float(self.player.vidx.frames-1)) * (1-self.bar_width)
            self.scrub_bar.set(progress, progress+self.bar_width)
            self.root.update()
        else:
            self.scrub_bar.set(0,1)
            self.root.update()  

    def open_vidx(self,path):
        self.player.load_vidx(path)
        self.bar_width = max(0.1, 1.0/self.player.vidx.frames)
        self.scrub_bar.set(0,self.bar_width)
        self.player.current_frame = 0
        print("Set canvas size to {0}".format(self.player.vidx.dimensions))
        self.canvas.config(width = self.player.vidx.dimensions[0], height=self.player.vidx.dimensions[1])
        self.update_image()
        self.root.title("BeanoPlayerⒷ 11 - {0}".format(path))

    def menu_open(self):
        path = tkFileDialog.askopenfilename(initialdir = "/",title = "Select .vidx",filetypes = (("VIDX files","*.vidx"),("All files","*.*")))
        if path != None:
            self.status_text.set("Opening {0}".format(path))
            self.root.update()  
            self.open_vidx(path)
            self.status_text.set("Ready")
            
    def menu_convert(self):
        inpath = tkFileDialog.askopenfilename(initialdir = "/",title = "Select input video file",
        filetypes = (("Video files","*.mp4 *.mov *.avi"),("All files","*.*")))
        if inpath==None: return

        outpath = tkFileDialog.asksaveasfilename(initialdir = "/",title = "Select .vidx destination",
        filetypes = (("VIDX files","*.vidx"),("All files","*.*")))
        if outpath==None: return

        capture = cv2.VideoCapture(inpath)

        # Clear tmpwrite

        filelist = [ f for f in os.listdir("tmpwrite") ]
        for f in filelist:
            os.remove(os.path.join("tmpwrite", f))


        frames = 0
        total_frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        print(type(total_frames))
        print(total_frames)
        
        with open("tmpwrite\\"+vidx.MAGIC_GUID+".xml", "w") as f:
            f.write("""<?xml version="1.0"?>
<video>
	<version>11</version>
	<width>{0}</width>
	<height>{1}</height>
	<frames>{2}</frames>
</video>""".format(int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                   int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                   int(total_frames)))
        used_guids = []
        last_timestamp = 0
        while True:
            percentage = 100*float(frames)/float(total_frames)
            self.status_text.set("Working {:.2f}%".format(percentage))
            success,image = capture.read()
            print(int(capture.get(cv2.CAP_PROP_POS_MSEC))-last_timestamp)
            last_timestamp = capture.get(cv2.CAP_PROP_POS_MSEC)
            if not success: break
            
            #cv2.imwrite("tmpwrite\\piajffpsaijpisajg.gif",image)
            pil_image = Image.fromarray(cv2.cvtColor(image,cv2.COLOR_BGR2RGB))

            image_guid = get_unique_uuid(used_guids)
            used_guids.append(image_guid)

            image_guid = "{"+str(image_guid)+"}"
            print("turned {0} to {1}".format(frames,vidx.index_to_GUID(frames)))
            with open("tmpwrite\\"+vidx.index_to_GUID(frames)+".xml", "w") as f:
                f.write("""<?xml version="1.0"?>
<frame>
	<meta>
		<subtitle></subtitle>
	</meta>
	<frame-info>
		<index>{0}</index>
		<duration>{1}</duration>
		<data-guid>{2}</data-guid>
	</frame-info>
</frame>""".format(frames,100,image_guid))
            pil_image.save("tmpwrite\\{0}.gif".format(image_guid), format="gif")
            print(frames)
            self.root.update()
            frames += 1

        zipf = zipfile.ZipFile(outpath, 'w', zipfile.ZIP_DEFLATED)

        for root, dirs, files in os.walk("tmpwrite"):
            for f in files:
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
        self.player.state = 0 if self.player.state == 1 else 1

root = Tk()
root.title("BeanoPlayerⒷ 11")
root.iconbitmap('resource\\icon.ico')

app = App(root)

app.player = vidx.VidxPlayer()

app.update_image()

last_frame=-1

def update():
    global last_frame
    
    app.update_handle()
    if last_frame != app.player.current_frame:
        app.update_image()
        last_frame=app.player.current_frame
    
    
    if app.player.state != 1:
        root.after(100,update)
        return
    app.player.add_frame()
    print("Waiting for {0}".format(app.player.needed_frame_time))
    root.after(app.player.needed_frame_time,update)
root.after(0,update)

root.mainloop()
