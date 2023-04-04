import tkinter as tk
from PIL import Image, ImageTk
from itertools import count, cycle
from pathlib import Path
from random import choice
import threading
def resize(pil_image,size=[100,100]):  
    ''' 
    resize a pil_image object so it will fit into 
    a box of size w_box times h_box, but retain aspect ratio 
    对一个pil_image对象进行缩放，让它在一个矩形框内，还能保持比例 
    '''  
    w_box, h_box = size
    w, h= pil_image.size
    f1 = 1.0*w_box/w # 1.0 forces float division in Python2  
    f2 = 1.0*h_box/h  
    factor = max([f1, f2])  

    width = int(w*factor)  
    height = int(h*factor)  
    
    box = ((width-min(w_box,width))//2, (height-min(h_box,height))//2, (width+min(w_box,width))//2, (height+min(h_box,height))//2)
    res = pil_image.resize((width, height), Image.ANTIALIAS).crop(box)

    return res #

class ImageLabel(tk.Label):
    """
    A Label that displays images, and plays them if they are gifs
    :im: A PIL Image instance or a string filename
    """

    def loadDir(self, imDir:Path,size=[100,100],root=None):
        if root is not None:
            self.x, self.y = root.winfo_x(), root.winfo_y()
            self.root = root
            self.bind("<B1-Motion>", self.move_app)
            self.bind('<Button-1>',self.setxy)
        def inner():
            self.unload()
            if not hasattr(self,'framesList'):
                self.framesList = []
            if not imDir.exists():
                imDir.mkdir()
            for im in imDir.iterdir():
                if isinstance(im, Path):
                    im = Image.open(im)
                frames = []
                try:
                    for i in count(1):
                        frames.append(ImageTk.PhotoImage(resize(im.copy(),size)))
                        im.seek(i)
                        if not hasattr(self,'firstLoad') and not hasattr(self,'picShow'):
                            self.config(image=frames[0])
                            self.picShow = True
                except EOFError:
                    pass
                frames = cycle(frames)
                
        
                try:
                    delay = im.info['duration']
                except:
                    delay = 100
                self.framesList.append([delay,frames])
                if not hasattr(self,'firstLoad'):
                    setattr(self,'firstLoad',True)
                    self.randomShow()
                    self.next_frame()
                
            print(str(imDir)+'图片加载完成')
        t = threading.Thread(target=inner)
        t.setDaemon(True)
        t.start()

    def randomShow(self):
        if not hasattr(self,'framesList'):
            return False
        if len(self.framesList)>0:
            self.delay,self.frames = choice(self.framesList)

    def load(self, im:str,size=[100,100],root=None):
        if root is not None:
            self.x, self.y = root.winfo_x(), root.winfo_y()
            self.root = root
            self.bind("<B1-Motion>", self.move_app)
            self.bind('<Button-1>',self.setxy)
        self.unload()
        if not hasattr(self,'framesList'):
            self.framesList = []
        #self.config(height=size[1],width=size[0])
        if isinstance(im, str) or isinstance(im, Path):
            im = Image.open(im)
        frames = []
 
        try:
            for i in count(1):
                frames.append(ImageTk.PhotoImage(resize(im.copy(),size)))
                im.seek(i)
        except EOFError:
            pass
        self.frames = cycle(frames)
        
        try:
            self.delay = im.info['duration']
        except:
            self.delay = 100
        self.framesList.append([self.delay,self.frames])
        if len(frames) == 1:
            self.config(image=next(self.frames))
        else:
            if not hasattr(self,'firstLoad'):
                setattr(self,'firstLoad',True)
                self.next_frame()
 
    def unload(self):
        self.config(image=None)
        self.frames = None
 
    def next_frame(self):
        if self.frames:
            self.config(image=next(self.frames))
            self.after(self.delay, self.next_frame)
    
    def move_app(self,event):
        new_x = (event.x - self.x) + self.root.winfo_x()
        new_y = (event.y - self.y) + self.root.winfo_y()
        s = f'+{new_x}+{new_y}'
        self.root.geometry(s)
    
    def setxy(self,event):
        self.x = event.x
        self.y = event.y

if __name__ == '__main__':
    root = tk.Tk()
    lbl = ImageLabel(root)
    lbl.pack()
    lbl.load('./config/gif/gif.gif')
    print(type(lbl))
    root.mainloop()