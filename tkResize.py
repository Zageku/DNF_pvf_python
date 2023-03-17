import tkinter as tk
from tkinter import ttk, messagebox
if not hasattr(ttk,'Spinbox'):
    class Spinbox(ttk.Entry):
        def __init__(self, master=None, **kw):  #from_=0,to=99,
            ttk.Entry.__init__(self, master, "ttk::spinbox", **kw)
        def set(self, value):
            self.tk.call(self._w, "set", value)
    ttk.Spinbox = Spinbox

def get_tk_size_dict(t:tk.Tk):
    def get_Frame_size(f:tk.Frame,sizeDict:dict):
        for widgetName,widget in f.children.items():
            widget.grid_propagate(False)
            widget.pack_propagate(False)
            sizeDict[widgetName] = {}
            if type(widget) in [tk.Frame,tk.LabelFrame,ttk.LabelFrame,ttk.Notebook]:
                sizeDict[widgetName]['height'] = widget.winfo_height()
                sizeDict[widgetName]['width'] = widget.winfo_width()
                get_Frame_size(widget,sizeDict[widgetName])
            elif type(widget) in [ttk.Entry,ttk.Spinbox]:
                sizeDict[widgetName]['height'] = widget.winfo_height()#有问题
                sizeDict[widgetName]['width'] = widget.cget('width')
            elif type(widget) in [tk.Label,ttk.Button]:
                sizeDict[widgetName]['height'] = widget.winfo_height()#/23
                sizeDict[widgetName]['width'] = widget.winfo_width()/7.3
            else:
                sizeDict.pop(widgetName)
    sizeDict = {}
    get_Frame_size(t,sizeDict)
    return sizeDict

def set_tab_size(tab:ttk.Notebook,sizeDict:dict):
    print(tab.select())

    for frameName,frame in tab.children.items():
        if frameName not in sizeDict.keys():
            continue
        #if str(frame)== tab.select():
        set_tk_size(frame,sizeDict[frameName])
        #    print(frameName)
        
def set_tk_size(t:tk.Tk,sizeDict:dict):
    for widgetName,widget in t.children.items():
        if widgetName not in sizeDict.keys():
            continue
        h = sizeDict[widgetName]['height']
        w = sizeDict[widgetName]['width']
        widget:tk.Frame
        if type(widget) in [tk.Frame,tk.LabelFrame,ttk.LabelFrame]:
            widget.config(height=h,width=w)#
            set_tk_size(widget,sizeDict[widgetName])
        elif type(widget)==ttk.Notebook:
            widget.config(height=h,width=w)
            set_tab_size(widget,sizeDict[widgetName])
        elif type(widget) in [ttk.Entry,ttk.Spinbox,tk.Label]:
            widget.config(width=w)


def regen_size_dict(old_size:dict,multiple=2):
    new_sizeDict = old_size
    for widgetName,subSizeDict in new_sizeDict.items():
        if widgetName=='width':
            new_sizeDict[widgetName] = int(subSizeDict*multiple)
            #print(subSizeDict,int(subSizeDict*multiple),new_sizeDict[widgetName])
        elif isinstance(subSizeDict,dict):
            new_sizeDict[widgetName]=regen_size_dict(subSizeDict,multiple)
            pass
    return new_sizeDict

def print_1(e):
    print(1)
def print_2(e):
    print(2)

def testApp():
    t= tk.Tk()
    f1 = tk.Frame(t)
    f1.pack()
    l11 = tk.Label(f1,text='text11',background='red',name='文本1',width=10)
    l11.grid(row=1,column=2,sticky='nswe',padx=5,pady=5)
    e11 = ttk.Entry(f1,width=8,name='输入1',background='red')
    e11.grid(row=1,column=3,sticky='nswe')
    l12 = tk.Label(f1,text='text33',background='red',name='文本12',width=20)
    l12.grid(row=1,column=4,sticky='nswe')

    l12.bind('<Button-1>',print_1)
    l12.bind('<Button-1>',print_2)

    
    f2 = tk.LabelFrame(t,text='labelFrame')
    f2.pack(fill='x')
    l21 = tk.Label(f2,text='text132312312311',name='文本2',width=10)
    l21.grid(row=1,column=2,sticky='nswe')
    e21 = ttk.Entry(f2,width=8,name='输入2')
    e21.grid(row=1,column=3,sticky='nswe')

    tabFrame = tk.Frame(t)
    tabFrame.pack(expand=True,fill='both')
    tabView = ttk.Notebook(tabFrame)
    tabView.pack(fill='both')

    
    ftab = tk.Frame(tabView,borderwidth=0)
    
    ftab.pack(fill='x')
    tabView.add(ftab,text='tabname')
    etb1 = ttk.Entry(ftab,width=8)
    etb1.pack(expand=True)

    ftab2 = tk.Frame(tabView,borderwidth=0)
    
    ftab2.pack()
    tabView.add(ftab2,text='tabname')
    etb2 = ttk.Entry(ftab2,width=8)
    etb2.pack()
    




    return t

if __name__=='__main__':
    def resize():
        #print('resize...')
        oldsize = get_tk_size_dict(t)
        print('oldsize',oldsize)
        newsize = regen_size_dict(old_size=oldsize.copy(),multiple=2)
        print('newsize',newsize)
        set_tk_size(t,newsize)
        oldsize = get_tk_size_dict(t)
        #print(oldsize)
    t = testApp()
    t.after(1000,resize)
    t.mainloop()