import tkinter as tk
from PIL import Image, ImageTk
from itertools import count, cycle

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
    factor = min([f1, f2])  
    #print(f1, f2, factor) # test  
    # use best down-sizing filter  
    width = int(w*factor)  
    height = int(h*factor)  
    return pil_image.resize((width, height), Image.ANTIALIAS) 

class ImageLabel(tk.Label):
    """
    A Label that displays images, and plays them if they are gifs
    :im: A PIL Image instance or a string filename
    """
    def load(self, im,size=[100,100]):
        if isinstance(im, str):
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
 
        if len(frames) == 1:
            self.config(image=next(self.frames))
        else:
            self.next_frame()
 
    def unload(self):
        self.config(image=None)
        self.frames = None
 
    def next_frame(self):
        if self.frames:
            self.config(image=next(self.frames))
            self.after(self.delay, self.next_frame)

if __name__ == '__main__':
    root = tk.Tk()
    lbl = ImageLabel(root)
    lbl.pack()
    lbl.load('gif.gif')
    root.mainloop()