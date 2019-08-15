import os
from Tkinter import PhotoImage
import xml.etree.ElementTree as ElementTree
import zipfile

MAGIC_GUID = "{6265616e-6f67-616d-6572-206265616e6f}"

def index_to_GUID(index):
    "Takes an int and returns a GUID whose hex digits would represent that integer"
    padded = hex(index)[2:].zfill(32)
    return "{"+padded[:8]+"-"+padded[8:12]+"-"+padded[12:16]+"-"+padded[16:20]+"-"+padded[20:]+"}"

class Vidx():
    def __init__(self,path):
        "Creates a vidx object from the path to an extracted .vidx file"
        self.path=path
        with zipfile.ZipFile(path, "r") as z:
            z.extractall("tmp")
        self.parse_file_meta()
        


    
    def parse_file_meta(self):
        "Parses the magic .xml file based on path attribute, and updates metadata attributes"
        #with open(os.path.join(self.path, self.MAGIC_GUID+".xml"),"r") as f:
        with open("tmp\\"+MAGIC_GUID+".xml") as f:
            t = f.read()

            tree = ElementTree.fromstring(t)
            self.version =tree.find("version").text
            self.frames = int(tree.find("frames").text)
            self.dimensions = (int(tree.find("width").text), int(tree.find("height").text),)
            
    def parse_frame_meta(self,frameIndex):
        """Parses the .xml file for a given frameIndex, and returns a tuple of
        (data GUID, frame duration in ms, subtitle, frame index)"""
        with open("tmp\\"+index_to_GUID(frameIndex)+".xml","r") as f:
            t = f.read()
            
            tree = ElementTree.fromstring(t)
            return (tree.find("frame-info").find("data-guid").text,
                    float(tree.find("frame-info").find("duration").text),
                    tree.find("meta").find("subtitle").text,
                    int(tree.find("frame-info").find("index").text),)
            
class VidxPlayer():
    def __init__(self):
        self.current_frame = 0
        self.passed_frame_time = 0
        self.needed_frame_time = 0
        self.vidx = None
        self.frame_guid = ""
        self.subtitle = ""
        self.state = 0
        
    def load_vidx(self,path):
        self.vidx = Vidx(path)
        self.update_frame_meta()

    def update_frame_meta(self):
        self.frame_guid, self.needed_frame_time, self.subtitle,_ = self.vidx.parse_frame_meta(self.current_frame)
        
    def add_time(self,time):
        self.passed_frame_time = time
        if self.passed_frame_time > self.needed_frame_time:
            self.passed_frame_time -= self.needed_frame_time
            self.add_frame()
    def set_frame(self,frame):
        self.current_frame = frame
        self.current_frame = self.current_frame % self.vidx.frames
        self.update_frame_meta()
    def add_frame(self):
        self.current_frame += 1
        self.current_frame = self.current_frame % self.vidx.frames
        self.update_frame_meta()
    
    def get_frame(self):
        return PhotoImage(file="tmp\\"+self.frame_guid+".gif")
