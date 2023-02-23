from glob import glob
from tkinter import *


class TitleBarFrame(Frame):
    def __init__(self,master,root,title='',closeFunc=lambda:...,*args):
        Frame.__init__(self,master=master,highlightthickness=1,highlightcolor='gray',highlightbackground='gray',*args)
        
        self.x, self.y = root.winfo_x(), root.winfo_y()
        self.root = root
        self.title_bar = Frame(self, bg="gray", relief="raised", bd=0)
        self.title_bar.pack(expand=1, fill=X)
        self.title_bar.bind("<B1-Motion>", self.move_app)
        self.title_bar.bind('<Button-1>',self.setxy)

        self.title_label = Label(self.title_bar, text=title, bg="gray", fg="white")
        self.title_label.pack(side=LEFT, pady=4)
        self.title_label.bind("<B1-Motion>", self.move_app)
        self.title_label.bind('<Button-1>',self.setxy)
        self.close_label = Label(self.title_bar, text="[ X ]", bg="gray", fg="white", relief="sunken", bd=0)
        self.close_label.pack(side=RIGHT, pady=4)
        self.close_label.bind("<Button-1>", self.quitter)

        self.innerFrame = Frame(self)
        self.innerFrame.pack(pady=5,anchor=N+W)
        self.closeFunc = closeFunc
    
    def move_app(self,event):
        new_x = (event.x - self.x) + self.root.winfo_x()
        new_y = (event.y - self.y) + self.root.winfo_y()
        s = f'+{new_x}+{new_y}'
        self.root.geometry(s)
    
    def setxy(self,event):
        self.x = event.x
        self.y = event.y
    
    def quitter(self,e):
        self.root.destroy()
        self.closeFunc()


# remove title bar

if __name__ == '__main__':
    root = Tk()
    root.geometry('500x300')
    root.overrideredirect(True)
    
    TitleBarFrame(root,root,'title').pack(fill=X,expand=1,anchor=N)
    root.mainloop()
'''
def move_app(event):
    new_x = (event.x - x) + root.winfo_x()
    new_y = (event.y - y) + root.winfo_y()
    s = f'+{new_x}+{new_y}'
    root.geometry(s)
	#root.geometry(f'+{e.x_root}+{e.y_root}')
def setxy(event):
    global x, y 
    x = event.x
    y = event.y
def quitter(e):
	root.quit()
	#root.destroy()

# Create Fake Title Bar
title_bar = Frame(root, bg="darkgreen", relief="raised", bd=0)
title_bar.pack(expand=1, fill=X)
# Bind the titlebar
title_bar.bind("<B1-Motion>", move_app)
title_bar.bind('<Button-1>',setxy)


# Create title text
title_label = Label(title_bar, text="  My Awesome App!!", bg="darkgreen", fg="white")
title_label.pack(side=LEFT, pady=4)

# Create close button on titlebar
close_label = Label(title_bar, text="  X  ", bg="darkgreen", fg="white", relief="sunken", bd=0)
close_label.pack(side=RIGHT, pady=4)
close_label.bind("<Button-1>", quitter)

my_button = Button(root, text="CLOSE!", font=("Helvetica, 32"), command=root.quit)
my_button.pack(pady=100)



root.mainloop()'''