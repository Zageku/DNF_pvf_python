from tkinter import *
class ToolTip(object):
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def show_tip(self, text, xy=None):
        "Display text in tooltip window"
        def processWheel(event):
            a= int(-(event.delta)/60)
            c.yview_scroll(a,'units')
        self.text = text
        if self.tipwindow or not self.text:
            return
        if xy==None:
            x, y, cx, cy = self.widget.bbox("insert")
            x = x + self.widget.winfo_rootx() + 7
            y = y + cy + self.widget.winfo_rooty() +22
        else:
            x,y = xy
        #print('tip xy:',x,y)
        self.tipwindow = tw = Toplevel(self.widget)
        self.tipwindow.wm_attributes('-topmost', 1)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        c= Canvas(tw,background = "#D2D2D2",height=300,highlightthickness=0, borderwidth=1)
        f = Frame(c)
        c.create_window(0,0,window=f, anchor='nw')
        c.pack(side="left", fill="both", expand=True)

        label = Label(f, text=self.text, justify=LEFT,wraplength=300,
                      background="#ffffe0", relief=SOLID, borderwidth=0,
                      )#font=("yahei","10","normal")
        label.pack(ipadx=1)
        tw.update()
        try:
            c.config(scrollregion=c.bbox("all"))
        except:
            return False
        if self.widget is not None:
            self.widget.bind("<MouseWheel>", processWheel)
        f.bind("<MouseWheel>", processWheel)
        c.config(width=f.winfo_width(),height=f.winfo_height() if f.winfo_height()<500 else 500)

    def hide_tip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()
    


def CreateToolTip(widget, text='', textFunc=None,xy=None):
    toolTip = ToolTip(widget)
    def enter(event):
        nonlocal text
        x = widget.winfo_rootx()+20
        y = widget.winfo_rooty()+27
        xy_ = x,y
        if textFunc is not None:
            text = textFunc()
        toolTip.show_tip(text,xy=xy_)
    def leave(event):
        toolTip.hide_tip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)
    return toolTip

if __name__=='__main__':
    t = Tk()
    #t.after(1000,lambda:showTooltip('tip测试'))
    CreateToolTip(t,'tip test'*10)
    t.mainloop()
    
    