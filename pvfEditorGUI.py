from pvfEditor import *
import copy
import pvfEditor
#!/usr/bin/python3
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename,asksaveasfilename
import json
import zlib
import pickle
import jsoneditor
import time
import threading
from toolTip import CreateToolTip
import cacheManager as cacheM
from EtcEditFrame import EtcframeWidget
from skillEditFrame import SkilleditframeWidget
if not hasattr(ttk,'Spinbox'):
    class Spinbox(ttk.Entry):
        def __init__(self, master=None, **kw):  #from_=0,to=99,
            ttk.Entry.__init__(self, master, "ttk::spinbox", **kw)
        def set(self, value):
            self.tk.call(self._w, "set", value)
    ttk.Spinbox = Spinbox
rarityMap = {
    0:'普通',
    1:'高级',
    2:'稀有',
    3:'神器',
    4:'史诗',
    5:'勇者',
    6:'传说',
    7:'神话',
    
}

def insert(widgets,tag='',itemInDict={}):
    def ins(widget,value):
        try:
            if type(widget) in [tk.Entry,ttk.Entry,ttk.Spinbox]:#,ttk.Combobox
                widget.insert(0,value)
            elif type(widget) in [tk.Text]:
                widget.insert(tk.END,value)
            elif type(widget) in [ttk.Combobox]:
                widget.set(value)
        except:
            print(widget,value,type(value))
    valueInList = itemInDict.get(tag)
    if valueInList is None:
        return False
    valueInList = valueInList.copy()
    if not isinstance(widgets,list):
        widgets = [widgets]
    #print(widgets)
    #print(valueInList)
    for i,widget in enumerate(widgets):
        if i >= len(valueInList):
            break
        ins(widget,valueInList[i])
    #print(tag,valueInList)


def get_entrys_values(tag:str,entryAndTypes):
    def read(tag,entry,structType=int):
        try:
            if tag=='[rarity]':
                value = int(entry.get().split('-')[0])
            elif tag=='[skill levelup]':
                if structType==int:
                    value = int(entry.get().split('-')[0])
                elif structType==str:
                    value = entry.get().split('-',1)[-1]
            else:
                if type(entry) in [tk.Text]:
                    value = structType(entry.get("1.0","end"))#.strip()
                else:
                    value = structType(entry.get().strip())
            if isinstance(value,str) and value.strip()=='':
                value = ''
            return value
        except:
            return None
    entrys,structTypes = entryAndTypes
    #print(tag,entrys,structTypes)
    values = []
    if not isinstance(entrys,list):
        entrys = [entrys]
    if not isinstance(structTypes,list):
        structTypes = [structTypes]
    if len(structTypes)<len(entrys) and len(structTypes)==1:
        structTypes = structTypes * len(entrys)
    for i,entry in enumerate(entrys):
        structType = structTypes[i]
        value = read(tag,entry,structType)
        if value is not None and value != '':
            values.append(value)
    #print(f'save-- {tag}-{values}-{entrys}')
    return values

def clearFrame(w:tk.Frame):
    for widget in w.children.values():
        #print(widget,type(widget))
        if type(widget) in [tk.Entry,ttk.Entry,ttk.Spinbox,ttk.Combobox]:
            widget.delete(0,tk.END)
        elif type(widget) in [tk.Text]:
            widget.delete("1.0",tk.END)
        elif type(widget) in [ttk.Frame,tk.Frame,tk.LabelFrame,ttk.LabelFrame]:
            clearFrame(widget)

def bind_command(widget,eventStr,cmd):
    widget.bind(eventStr,cmd)
    if type(widget) in [ttk.Frame,tk.Frame,tk.LabelFrame,ttk.LabelFrame]:
        bind_command(widget,eventStr,cmd)

class WasteframeWidget(ttk.Frame):
    def __init__(self, master=None, **kw):
        super(WasteframeWidget, self).__init__(master, **kw)
        self.hpFrame = ttk.Frame(self)
        self.hpFrame.configure(height=200, width=250)
        label19 = ttk.Label(self.hpFrame)
        label19.configure(anchor="center", text='HP恢复', width=8)
        label19.pack(side="left")
        self.hpHealTypeE = ttk.Combobox(self.hpFrame)
        self.hpHealTypeE.configure(values='% +', width=2)
        self.hpHealTypeE.pack(side="left")
        self.hpE = ttk.Entry(self.hpFrame)
        self.hpE.configure(width=8)
        self.hpE.pack(expand="false", fill="x", side="left")
        self.hptimeUseE = ttk.Entry(self.hpFrame)
        self.hptimeUseE.configure(width=8)
        self.hptimeUseE.pack(expand="true", fill="x", side="left")
        self.hpObjE = ttk.Combobox(self.hpFrame)
        self.hpObjE.configure(values='myself party', width=8)
        self.hpObjE.pack(side="right")
        self.hpFrame.pack(expand="false", fill="x", pady=3, side="top")
        self.mpFrame = ttk.Frame(self)
        self.mpFrame.configure(height=200, width=250)
        label21 = ttk.Label(self.mpFrame)
        label21.configure(anchor="center", text='MP恢复', width=8)
        label21.pack(side="left")
        self.mpHealTypeE = ttk.Combobox(self.mpFrame)
        self.mpHealTypeE.configure(values='% +', width=2)
        self.mpHealTypeE.pack(side="left")
        self.mpE = ttk.Entry(self.mpFrame)
        self.mpE.configure(width=8)
        self.mpE.pack(expand="false", fill="x", side="left")
        self.mptimeUseE = ttk.Entry(self.mpFrame)
        self.mptimeUseE.configure(width=8)
        self.mptimeUseE.pack(expand="true", fill="x", side="left")
        self.mpObjE = ttk.Combobox(self.mpFrame)
        self.mpObjE.configure(values='myself party', width=8)
        self.mpObjE.pack(side="right")
        self.mpFrame.pack(expand="false", fill="x", pady=3, side="top")
        self.statFrame = ttk.Frame(self)
        self.statFrame.configure(height=200, width=250)
        label31 = ttk.Label(self.statFrame)
        label31.configure(anchor="center", text='状态效果', width=8)
        label31.pack(side="left")
        self.statE11 = ttk.Combobox(self.statFrame)
        self.statE11.configure(values='% +', width=2)
        self.statE11.pack(side="left")
        self.statE11.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.statE12 = ttk.Entry(self.statFrame)
        self.statE12.configure(width=8)
        self.statE12.pack(expand="false", fill="x", side="left")
        self.statE13 = ttk.Combobox(self.statFrame)
        self.statE13.configure(values='myself party', width=16)
        self.statE13.pack(expand="true", fill="x", side="right")
        self.statE13.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.statFrame.pack(expand="false", fill="x", pady=3, side="top")
        self.frame2 = ttk.Frame(self)
        self.frame2.configure(height=200, width=250)
        label1 = ttk.Label(self.frame2)
        label1.configure(anchor="center", text='状态效果', width=8)
        label1.pack(side="left")
        self.statE21 = ttk.Combobox(self.frame2)
        self.statE21.configure(values='% +', width=2)
        self.statE21.pack(side="left")
        self.statE21.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.statE22 = ttk.Entry(self.frame2)
        self.statE22.configure(width=8)
        self.statE22.pack(expand="false", fill="x", side="left")
        self.statE23 = ttk.Combobox(self.frame2)
        self.statE23.configure(values='myself party', width=16)
        self.statE23.pack(expand="true", fill="x", side="right")
        self.statE23.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.frame2.pack(expand="false", fill="x", pady=3, side="top")
        self.frame3 = ttk.Frame(self)
        self.frame3.configure(height=200, width=250)
        label2 = ttk.Label(self.frame3)
        label2.configure(anchor="center", text='状态效果', width=8)
        label2.pack(side="left")
        self.statE31 = ttk.Combobox(self.frame3)
        self.statE31.configure(values='% +', width=2)
        self.statE31.pack(side="left")
        self.statE31.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.statE32 = ttk.Entry(self.frame3)
        self.statE32.configure(width=8)
        self.statE32.pack(expand="false", fill="x", side="left")
        self.statE33 = ttk.Combobox(self.frame3)
        self.statE33.configure(values='myself party', width=16)
        self.statE33.pack(expand="true", fill="x", side="right")
        self.statE33.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.frame3.pack(expand="false", fill="x", pady=3, side="top")
        self.frame4 = ttk.Frame(self)
        self.frame4.configure(height=200, width=250)
        label3 = ttk.Label(self.frame4)
        label3.configure(anchor="center", text='状态效果', width=8)
        label3.pack(side="left")
        self.statE41 = ttk.Combobox(self.frame4)
        self.statE41.configure(values='% +', width=2)
        self.statE41.pack(side="left")
        self.statE41.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.statE42 = ttk.Entry(self.frame4)
        self.statE42.configure(width=8)
        self.statE42.pack(expand="false", fill="x", side="left")
        self.statE43 = ttk.Combobox(self.frame4)
        self.statE43.configure(values='myself party', width=16)
        self.statE43.pack(expand="true", fill="x", side="right")
        self.statE43.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.frame4.pack(expand="false", fill="x", pady=3, side="top")
        self.frame5 = ttk.Frame(self)
        self.frame5.configure(height=200, width=250)
        label4 = ttk.Label(self.frame5)
        label4.configure(anchor="center", text='状态效果', width=8)
        label4.pack(side="left")
        self.statE51 = ttk.Combobox(self.frame5)
        self.statE51.configure(values='% +', width=2)
        self.statE51.pack(side="left")
        self.statE51.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.statE52 = ttk.Entry(self.frame5)
        self.statE52.configure(width=8)
        self.statE52.pack(expand="false", fill="x", side="left")
        self.statE53 = ttk.Combobox(self.frame5)
        self.statE53.configure(values='myself party', width=16)
        self.statE53.pack(expand="true", fill="x", side="right")
        self.statE53.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.frame5.pack(expand="false", fill="x", pady=3, side="top")
        self.frame6 = ttk.Frame(self)
        self.frame6.configure(height=200, width=250)
        label5 = ttk.Label(self.frame6)
        label5.configure(anchor="center", text='状态效果', width=8)
        label5.pack(side="left")
        self.statE61 = ttk.Combobox(self.frame6)
        self.statE61.configure(values='% +', width=2)
        self.statE61.pack(side="left")
        self.statE61.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.statE62 = ttk.Entry(self.frame6)
        self.statE62.configure(width=8)
        self.statE62.pack(expand="false", fill="x", side="left")
        self.statE63 = ttk.Combobox(self.frame6)
        self.statE63.configure(values='myself party', width=16)
        self.statE63.pack(expand="true", fill="x", side="right")
        self.statE63.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.frame6.pack(expand="false", fill="x", pady=3, side="top")
        self.frame7 = ttk.Frame(self)
        self.frame7.configure(height=200, width=250)
        label6 = ttk.Label(self.frame7)
        label6.configure(anchor="center", text='状态效果', width=8)
        label6.pack(side="left")
        self.statE71 = ttk.Combobox(self.frame7)
        self.statE71.configure(values='% +', width=2)
        self.statE71.pack(side="left")
        self.statE71.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.statE72 = ttk.Entry(self.frame7)
        self.statE72.configure(width=8)
        self.statE72.pack(expand="false", fill="x", side="left")
        self.statE73 = ttk.Combobox(self.frame7)
        self.statE73.configure(values='myself party', width=16)
        self.statE73.pack(expand="true", fill="x", side="right")
        self.statE73.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.frame7.pack(expand="false", fill="x", pady=3, side="top")
        self.frame8 = ttk.Frame(self)
        self.frame8.configure(height=200, width=250)
        label7 = ttk.Label(self.frame8)
        label7.configure(anchor="center", text='状态效果', width=8)
        label7.pack(side="left")
        self.statE81 = ttk.Combobox(self.frame8)
        self.statE81.configure(values='% +', width=2)
        self.statE81.pack(side="left")
        self.statE81.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.statE82 = ttk.Entry(self.frame8)
        self.statE82.configure(width=8)
        self.statE82.pack(expand="false", fill="x", side="left")
        self.statE83 = ttk.Combobox(self.frame8)
        self.statE83.configure(values='myself party', width=16)
        self.statE83.pack(expand="true", fill="x", side="right")
        self.statE83.bind("<<ComboboxSelected>>", self.selectStat, add="")
        self.frame8.pack(expand="false", fill="x", pady=3, side="top")
        self.durationFrame = ttk.Frame(self)
        self.durationFrame.configure(height=200, width=250)
        label33 = ttk.Label(self.durationFrame)
        label33.configure(anchor="center", text='持续时间', width=8)
        label33.pack(side="left")
        self.durationE = ttk.Spinbox(self.durationFrame)
        self.durationE.configure(from_=0, to=1000000, width=20)
        self.durationE.pack(expand="true", fill="x", side="left")
        self.durationObjE = ttk.Combobox(self.durationFrame)
        self.durationObjE.configure(values='myself party', width=8)
        self.durationObjE.pack(side="right")
        self.durationFrame.pack(expand="false", fill="x", pady=3, side="top")
        self.frame9 = ttk.Frame(self)
        self.frame9.configure(height=200, width=250)
        label8 = ttk.Label(self.frame9)
        label8.configure(anchor="center", text='清除异常', width=8)
        label8.pack(side="left")
        self.activeStatusRecE1 = ttk.Combobox(self.frame9)
        self.activeStatusRecE1.configure(values='any', width=8)
        self.activeStatusRecE1.pack(side="left")
        self.activeStatusRecE2 = ttk.Spinbox(self.frame9)
        self.activeStatusRecE2.configure(from_=0, to=1000000, width=20)
        self.activeStatusRecE2.pack(expand="true", fill="x", side="left")
        self.activeStatusRecE3 = ttk.Combobox(self.frame9)
        self.activeStatusRecE3.configure(values='myself party', width=8)
        self.activeStatusRecE3.pack(side="right")
        self.frame9.pack(expand="false", fill="x", pady=3, side="top")
        self.configure(height=200, width=250)
        self.pack(expand="true", fill="both", side="top")

    
        self._other_build_function()
    def _other_build_function(self):
        self.entryTagDict = {
            '[hp recovery]':[[self.hpHealTypeE,self.hpE,self.hptimeUseE,self.hpObjE],[str,int,int,str]],
            '[mp recovery]':[[self.mpHealTypeE,self.mpE,self.mptimeUseE,self.mpObjE],[str,int,int,str]],
            '[stat change duration]':[[self.durationE,self.durationObjE],[int,str]],
            '[active status recovery]':[[self.activeStatusRecE1,self.activeStatusRecE2,self.activeStatusRecE3],[str,int,str]]
        }
        self.statEntrys = [
            [[self.statE11,self.statE12,self.statE13],[str,int,str]],
            [[self.statE21,self.statE22,self.statE23],[str,int,str]],
            [[self.statE31,self.statE32,self.statE33],[str,int,str]],
            [[self.statE41,self.statE42,self.statE43],[str,int,str]],
            [[self.statE51,self.statE52,self.statE53],[str,int,str]],
            [[self.statE61,self.statE62,self.statE63],[str,int,str]],
            [[self.statE71,self.statE72,self.statE73],[str,int,str]],
            [[self.statE81,self.statE82,self.statE83],[str,int,str]],
        ]
        self.statList = ['stuck', 'physical critical hit rate', 'light resistance', 
                         'magical critical hit rate', 'fire attack', 'water resistance', 'magical defense', 
                         'magical critical hit', 'no breath time change', 'equipment magical attack', 
                         'dark attack', 'mp max', 'light attack', 'move speed', 'fire resistance', 
                         'dark resistance', 'all activestatus resistance', 'curse resistance', 
                         'physical attack', 'hp max', 'freeze resistance', 'equipment physical attack', 
                         'magical attack bonus', 'jump power', 'skill cool time', 'physical critical hit', 
                         'stuck resistance', 'hold resistance', 'cast speed', 'all elemental resistance', 
                         'attack speed', 'physical defense', 'water attack', 'magical attack', 
                         'physical attack bonus', 'separate attack', 'physical equipment defense'
                         ]
        self.statList.sort()
        for elist,typeList in self.statEntrys:
            elist[2].config(values=self.statList)
            CreateToolTip(elist[1],'状态增加值，stuck和cool time时需要填写为负数')

        CreateToolTip(self.hptimeUseE,'恢复所需时间/毫秒')
        CreateToolTip(self.mptimeUseE,'恢复所需时间/毫秒')
        CreateToolTip(self.durationE,'持续时间/毫秒')
    def selectStat(self, event:tk.Event=None):
        #print(event.widget)
        widget = event.widget
        for statEntryList,structTypes in self.statEntrys:
            if event.widget in statEntryList:
                #print(statEntryList)
                widgetIndex = statEntryList.index(event.widget)
                break
        if widget.get()=='+' and 'bonus' in statEntryList[2].get():
            statEntryList[2].set('')
        elif 'bonus' in widget.get():
            statEntryList[0].set('%')
    def fill_values(self,itemLeaf):
        clearFrame(self)
        if itemLeaf is None:
            return False
        itemInDict = itemLeaf.get('itemInDict')
        #print(itemInDict)
        for tag,entryAndTypes in self.entryTagDict.items():
            insert(entryAndTypes[0],tag,itemInDict)
        
        key = '[stat change]'
        entrys = []
        for entryAndTypes in self.statEntrys:
            entrys.extend(entryAndTypes[0])
        insert(entrys,key,itemInDict)
    
    def read_values(self):
        res = {}
        for key,entryAndTypes in self.entryTagDict.items():
            values = get_entrys_values(key,entryAndTypes)
            if values!=[]:
                res[key] = values
        key = '[stat change]'
        statSeg = []
        for entryAndTypes in self.statEntrys:
            values = get_entrys_values(key,entryAndTypes)
            if len(values)==3:
                statSeg.extend(values)
        res[key] = statSeg
        return res


class PvfeditstackableframeWidget(ttk.Frame):
    def __init__(self, master=None, **kw):
        super(PvfeditstackableframeWidget, self).__init__(master, **kw)
        self.editedListFrame = ttk.Labelframe(self)
        self.editedListFrame.configure(height=200, text='已编辑列表', width=300)
        self.searchNameE = ttk.Combobox(self.editedListFrame)
        self.searchNameE.pack(fill="x", side="top")
        self.idE = ttk.Entry(self.editedListFrame)
        self.idE.pack(fill="x", side="top")
        self.addLeafFrame = ttk.Frame(self.editedListFrame)
        self.addLeafFrame.configure(height=23, width=200)
        self.copyThisBtn = ttk.Button(self.addLeafFrame)
        self.copyThisBtn.configure(state="disabled", text='以该物品为模板')
        self.copyThisBtn.pack(expand="true", fill="x", side="left")
        self.copyThisBtn.configure(command=self.btn_edit_with_new_file)
        self.editThisBtn = ttk.Button(self.addLeafFrame)
        self.editThisBtn.configure(state="disabled", text='修改该物品数据')
        self.editThisBtn.pack(expand="true", fill="x", side="right")
        self.editThisBtn.configure(command=self.btn_edit_file)
        self.addLeafFrame.pack(fill="x", side="top")
        self.treeViewFrame = ttk.Frame(self.editedListFrame)
        self.treeViewFrame.configure(height=200, width=300)
        self.editedTree = ttk.Treeview(self.treeViewFrame)
        self.editedTree.configure(selectmode="browse", show="headings")
        self.editedTree.pack(expand="true", fill="both", side="left")
        self.editedTree.bind(
            "<<TreeviewSelect>>",
            self.select_treeview_item_Event,
            add="")
        self.listBar = ttk.Scrollbar(self.treeViewFrame)
        self.listBar.configure(orient="vertical")
        self.listBar.pack(fill="y", side="right")
        self.treeViewFrame.pack(expand="true", fill="both", side="top")
        self.treeViewBtnFrame = ttk.Frame(self.editedListFrame)
        self.treeViewBtnFrame.configure(height=23, width=200)
        self.delLeafBtn = ttk.Button(self.treeViewBtnFrame)
        self.delLeafBtn.configure(text='移除该项编辑')
        self.delLeafBtn.pack(fill="x", side="top")
        self.delLeafBtn.configure(command=self.remove_selected_item)
        self.treeViewBtnFrame.pack(fill="x", side="top")
        self.editedListFrame.pack(expand="true", fill="both", side="left")
        self.itemEditFrame = ttk.Labelframe(self)
        self.itemEditFrame.configure(height=200, text='道具数据修改', width=200)
        self.itemInfoFrame = ttk.Frame(self.itemEditFrame)
        self.itemInfoFrame.configure(height=200, width=200)
        label1 = ttk.Label(self.itemInfoFrame)
        label1.configure(text='文件路径', width=8)
        label1.pack(side="left")
        self.filePathE = ttk.Entry(self.itemInfoFrame)
        self.filePathE.configure(state="readonly", width=30)
        self.filePathE.pack(expand="true", fill="x", side="right")
        self.itemInfoFrame.pack(expand="false", fill="x", pady=3, side="top")
        self.frame2 = ttk.Frame(self.itemEditFrame)
        self.frame2.configure(height=200, width=200)
        label2 = ttk.Label(self.frame2)
        label2.configure(anchor="center", text='种类', width=8)
        label2.pack(side="left")
        self.stkTypeE = ttk.Combobox(self.frame2)
        self.stkTypeE.configure(state="readonly", width=10)
        self.stkTypeE.pack(expand="true", fill="x", side="left")
        self.stkTypeE.bind(
            "<<ComboboxSelected>>",
            self.select_stkType,
            add="+")
        self.stkTypeValueE = ttk.Spinbox(self.frame2)
        self.stkTypeValueE.configure(from_=0, to=100, width=3)
        self.stkTypeValueE.pack(expand="true", fill="x", side="left")
        label37 = ttk.Label(self.frame2)
        label37.configure(text='交易类型')
        label37.pack(side="left")
        self.attachTypeE = ttk.Combobox(self.frame2)
        self.attachTypeE.configure(width=10)
        self.attachTypeE.pack(expand="true", fill="x", side="right")
        self.frame2.pack(expand="false", fill="x", pady=3, side="top")
        self.nameFrame = ttk.Frame(self.itemEditFrame)
        self.nameFrame.configure(height=200, width=200)
        label4 = ttk.Label(self.nameFrame)
        label4.configure(anchor="center", text='名称', width=8)
        label4.pack(side="left")
        self.nameE = ttk.Entry(self.nameFrame)
        self.nameE.pack(expand="true", fill="x", side="right")
        self.nameFrame.pack(expand="false", fill="x", pady=3, side="top")
        self.nameFrame2 = ttk.Frame(self.itemEditFrame)
        self.nameFrame2.configure(height=200, width=200)
        label5 = ttk.Label(self.nameFrame2)
        label5.configure(anchor="center", text='名称2', width=8)
        label5.pack(side="left")
        self.nameE2 = ttk.Entry(self.nameFrame2)
        self.nameE2.pack(expand="true", fill="x", side="right")
        self.nameFrame2.pack(expand="false", fill="x", pady=3, side="top")
        self.explainFrame = ttk.Frame(self.itemEditFrame)
        self.explainFrame.configure(height=200, width=200)
        label7 = ttk.Label(self.explainFrame)
        label7.configure(anchor="center", text='描述', width=8)
        label7.pack(side="left")
        self.explainE = tk.Text(self.explainFrame)
        self.explainE.configure(
            height=5,
            highlightbackground="#808080",
            highlightcolor="#808080",
            highlightthickness=1,
            relief="flat",
            width=20)
        self.explainE.pack(fill="x", side="top")
        self.explainFrame.pack(expand="false", fill="x", pady=3, side="top")
        self.flavorFrame = ttk.Frame(self.itemEditFrame)
        self.flavorFrame.configure(height=200, width=200)
        label9 = ttk.Label(self.flavorFrame)
        label9.configure(anchor="center", text='描述2', width=8)
        label9.pack(side="left")
        self.floavrE = tk.Text(self.flavorFrame)
        self.floavrE.configure(
            height=5,
            highlightbackground="#808080",
            highlightthickness=1,
            relief="flat",
            width=20)
        self.floavrE.pack(fill="x", side="top")
        self.flavorFrame.pack(expand="false", fill="x", pady=3, side="top")
        self.rarityFrame = ttk.Frame(self.itemEditFrame)
        self.rarityFrame.configure(height=200, width=200)
        label11 = ttk.Label(self.rarityFrame)
        label11.configure(anchor="center", text='稀有度', width=8)
        label11.pack(side="left")
        self.rarityE = ttk.Combobox(self.rarityFrame)
        self.rarityE.configure(state="readonly", width=10)
        self.rarityE.pack(expand="true", fill="x", side="right")
        self.rarityFrame.pack(expand="false", fill="x", pady=3, side="top")
        self.weightFrame = ttk.Frame(self.itemEditFrame)
        self.weightFrame.configure(height=200, width=200)
        label13 = ttk.Label(self.weightFrame)
        label13.configure(anchor="center", text='重量', width=8)
        label13.pack(side="left")
        self.weightE = ttk.Entry(self.weightFrame)
        self.weightE.pack(expand="true", fill="x", side="right")
        self.weightFrame.pack(expand="false", fill="x", pady=3, side="top")
        self.limitFrame = ttk.Frame(self.itemEditFrame)
        self.limitFrame.configure(height=200, width=200)
        label15 = ttk.Label(self.limitFrame)
        label15.configure(anchor="center", text='携带上限', width=8)
        label15.pack(side="left")
        self.limitE = ttk.Entry(self.limitFrame)
        self.limitE.pack(expand="true", fill="x", side="right")
        self.limitFrame.pack(expand="false", fill="x", pady=3, side="top")
        self.priceFrame = ttk.Frame(self.itemEditFrame)
        self.priceFrame.configure(height=200, width=200)
        label17 = ttk.Label(self.priceFrame)
        label17.configure(anchor="center", text='购买价格', width=8)
        label17.pack(side="left")
        self.priceE = ttk.Entry(self.priceFrame)
        self.priceE.pack(expand="true", fill="x", side="right")
        self.priceFrame.pack(expand="false", fill="x", pady=3, side="top")
        self.frame3 = ttk.Frame(self.itemEditFrame)
        self.frame3.configure(height=200, width=200)
        label3 = ttk.Label(self.frame3)
        label3.configure(anchor="center", text='出售价格', width=8)
        label3.pack(side="left")
        self.salePriceE = ttk.Entry(self.frame3)
        self.salePriceE.pack(expand="true", fill="x", side="right")
        self.frame3.pack(expand="false", fill="x", pady=3, side="top")
        self.cdTimeF = ttk.Frame(self.itemEditFrame)
        self.cdTimeF.configure(height=200, width=200)
        label27 = ttk.Label(self.cdTimeF)
        label27.configure(anchor="center", text='冷却时间', width=8)
        label27.pack(side="left")
        self.coldTimeE = ttk.Spinbox(self.cdTimeF)
        self.coldTimeE.configure(from_=0, to=100)
        self.coldTimeE.pack(expand="true", fill="x", side="right")
        self.cdTimeF.pack(expand="false", fill="x", pady=3, side="top")
        self.cdGroupF = ttk.Frame(self.itemEditFrame)
        self.cdGroupF.configure(height=200, width=200)
        label29 = ttk.Label(self.cdGroupF)
        label29.configure(anchor="center", text='冷却分组', width=8)
        label29.pack(side="left")
        self.coldGroupE = ttk.Spinbox(self.cdGroupF)
        self.coldGroupE.configure(from_=0, to=100)
        self.coldGroupE.pack(expand="true", fill="x", side="right")
        self.cdGroupF.pack(expand="false", fill="x", pady=3, side="top")
        self.levF = ttk.Frame(self.itemEditFrame)
        self.levF.configure(height=200, width=200)
        label35 = ttk.Label(self.levF)
        label35.configure(
            anchor="center",
            justify="left",
            text='最低等级',
            width=8)
        label35.pack(side="left")
        self.levE = ttk.Spinbox(self.levF)
        self.levE.configure(from_=0, to=100)
        self.levE.pack(expand="true", fill="x", side="right")
        self.levF.pack(expand="false", fill="x", pady=3, side="top")
        frame4 = ttk.Frame(self.itemEditFrame)
        frame4.configure(height=200, width=200)
        self.saveFileEditBtn = ttk.Button(frame4)
        self.saveFileEditBtn.configure(text='保存修改')
        self.saveFileEditBtn.pack(expand="true", fill="x", side="left")
        self.saveFileEditBtn.configure(command=self.save_file_edit)
        self.advanceBtn = ttk.Button(frame4)
        self.advanceBtn.configure(text='高级修改')
        self.advanceBtn.pack(expand="true", fill="x", side="right")
        self.advanceBtn.configure(command=self.open_advance_edit)
        frame4.pack(expand="false", fill="x", pady=3, side="bottom")
        self.itemEditFrame.pack(expand="true", fill="both", side="left")
        self.exEditFrame = ttk.Labelframe(self)
        self.exEditFrame.configure(height=200, text='道具数据修改-附加', width=250)
        self.exEditFrame.pack(expand="true", fill="both", side="left")
        self.configure(height=400, width=600)
        self.pack(expand="true", fill="both", side="top")


        self._build_other_functions()
    
    def _build_other_functions(self):
        self.leafType = 'stackable'
        self.editLeafDict = {}  # eid: leaf
        self.lst = None
        self.pvf:TinyPVFEditor = None
        self.currentLeaf = None
        self.editIndex = 0
        self.exFrameObj = None
        self.listBar.config(command=self.editedTree.yview)
        self.editedTree.config(yscrollcommand=self.listBar.set)
        CreateToolTip(self.advanceBtn,'打开浏览器对json文件进行修改\n在浏览器中点击【√】以保存数据')
        CreateToolTip(self.saveFileEditBtn,'保存对该文件的编辑至内存')
        CreateToolTip(self.searchNameE,textFunc=lambda:self.getItemPVFInfo('输入物品名进行搜索'))
        CreateToolTip(self.idE,textFunc=lambda:self.getItemPVFInfo('输入物品ID进行搜索'))
        self.searchNameE.bind('<Button-1>',self.searchItem)
        self.searchNameE.bind("<<ComboboxSelected>>",lambda e:self.readItemID('name'))
        self.idE.bind('<FocusOut>',lambda e:self.readItemID('id'))
        self.idE.bind('<Return>',lambda e:self.readItemID('id'))
        self.editedTree
        self.editedTree["columns"] = ("1", "2", "3")
        self.editedTree['show'] = 'headings'
        self.editedTree.column("1", width = 20, anchor ='c')
        self.editedTree.column("2", width = 90, anchor ='c')
        self.editedTree.column("3", width = 50, anchor ='c')
        self.editedTree.heading("1", text ="序号")
        self.editedTree.heading("2", text ="物品名")
        self.editedTree.heading("3", text ="物品ID")
        _ = self.editedTree.insert('',tk.END,values=[])
        self.editedTree.delete(_)
        self.stkTypeE.config(values=list(SegKeyDict['stackable'].keys()))
        self.exFramesDict = {
            '[waste]': WasteframeWidget
        }
        WasteframeWidget(self.exEditFrame).pack(expand=True,fill='both')
        self.entryTagDict = {
            '[stackable type]':[[self.stkTypeE,self.stkTypeValueE],[str,int]],
            '[name]':[self.nameE,str],
            '[name2]':[self.nameE2,str],
            '[explain]':[self.explainE,str],
            '[flavor text]':[self.floavrE,str],
            '[rarity]':[self.rarityE,int],
            '[weight]':[self.weightE,int],
            '[stack limit]':[self.limitE,int],
            '[price]':[self.priceE,int],
            '[cool time]':[self.coldTimeE,int],
            '[cooltime group]':[self.coldGroupE,int],
            '[minimum level]':[self.levE,int],
            '[attach type]':[self.attachTypeE,str],
        }
        self.rarityE.config(values=[f'{key}-{value}' for key,value in rarityMap.items()])
    
    def fillFrameWithItemLeaf(self,itemLeaf:dict):
        def ins(widget,value,tag=''):
            if type(widget) in [tk.Entry,ttk.Entry,ttk.Spinbox]:#,ttk.Combobox
                widget.insert(0,value)
            elif type(widget) in [tk.Text]:
                widget.insert(tk.END,value)
            elif type(widget) in [ttk.Combobox]:
                widget.set(value)
        def insert1(entryAndType,tag=''):
            #print(entryAndType)
            entrys,structTypes = entryAndType
            if not isinstance(entrys,list):
                entrys = [entrys]
                structTypes = [structTypes]
            values = itemInDict.get(tag)
            if values is None:
                return False
            if isinstance(values,list):
                for i in range(len(entrys)):
                    e = entrys[i]
                    ins(e,values[i],tag)

        self.filePathE.config(state='normal')
        clearFrame(self.itemEditFrame)
        self.currentLeaf = itemLeaf
        itemInDict = itemLeaf['itemInDict']
        #print('加载文件...',itemInDict)
        self.filePathE.insert(0,itemLeaf['filePath'])
        self.filePathE.config(state='readonly')
        for tag,entryAndTypes in self.entryTagDict.items():
            #entry,structType = entryAndType
            insert(entryAndTypes[0],tag,itemInDict)
        self.select_stkType()
        if itemLeaf.get('jsonEditorServer') is None:
            itemLeaf['jsonEditorServer'] = None
        
        #jsoneditor.editjson(itemInDict,print,options={'mode':'code'},title=itemInDict.get('[name]'))

    def btn_edit_with_new_file(self):
        itemID = int(self.idE.get())
        itemName = cacheM.stackableDict.get(itemID)
        filePath = self.pvf.itemID2itemPath(itemID,self.lst)
        leaf = self.pvf.fileTreeDict.get(filePath).copy()
        leaf['itemInDict'] = self.pvf.read_File_In_Dict(filePath)
        leaf['itemID'] = None
        leaf['filePath'] = 'stackable/'
        leaf['fn'] = None
        leaf['itemInDict']['[name]'] = ['[新]'+itemName]
        self.fillFrameWithItemLeaf(leaf)
        self.select_stkType()
        values = [self.editIndex,'[新]'+itemName,None]
        self.editLeafDict[self.editIndex] = leaf
        node = self.editedTree.insert('',tk.END,values=values)
        leaf['indexInTreeView'] = self.editIndex
        self.editIndex += 1
        self.editedTree.see(node)
        self.editedTree.selection_set(node)

    def enable_Btns(self):
        self.editThisBtn.config(state='normal')
        #self.copyThisBtn.config(state='normal')

    def btn_edit_file(self):
        try:
            itemID = int(self.idE.get())
            itemName = cacheM.stackableDict.get(itemID)
        except:
            self.log('请填充物品ID')
            return False
        if itemName is None:
            self.log('该物品ID不存在')
            return False
        for child in self.editedTree.get_children():
            if itemID == self.editedTree.item(child)["values"][2]:
                self.log('该物品ID已被添加')
                return False
        filePath = self.pvf.itemID2itemPath(itemID,self.lst)
        leaf = self.pvf.fileTreeDict.get(filePath).copy()
        leaf['itemInDict'] = self.pvf.read_File_In_Dict(filePath)
        leaf['itemID'] = itemID
        self.fillFrameWithItemLeaf(leaf)
        #self.select_stkType()
        values = [self.editIndex,itemName,itemID]
        self.editLeafDict[self.editIndex] = leaf
        node = self.editedTree.insert('',tk.END,values=values)
        leaf['indexInTreeView'] = self.editIndex
        self.editIndex += 1
        self.editedTree.see(node)
        self.editedTree.selection_set(node)
        
    def select_treeview_item_Event(self, event=None):
        selectedItem = self.editedTree.selection()
        currentEditID = self.editedTree.item(selectedItem)['values'][0]
        #print(currentEditID)
        currentLeaf = self.editLeafDict.get(currentEditID)
        if currentLeaf is None:
            return False
        elif currentLeaf!=self.currentLeaf:
            self.save_file_edit()
            self.currentLeaf = currentLeaf
            self.fillFrameWithItemLeaf(self.currentLeaf)

    def refill_treeview(self):
        for child in self.editedTree.get_children():
            self.editedTree.delete(child)
        for eid,leaf in self.editLeafDict.items():
            values = [eid,leaf['itemInDict'].get('[name]'),leaf['itemID']]
            item = self.editedTree.insert('',tk.END,values=values)
            print(values)
        if self.editLeafDict=={}:
            return False
        self.editIndex = max(list(self.editLeafDict.keys())) + 1
        self.currentLeaf = None
        self.filePathE.config(state='normal')
        clearFrame(self.itemEditFrame)
        self.filePathE.config(state='readonly')
        #print(self.editLeafDict)

    def remove_selected_item(self):
        selectedItem = self.editedTree.selection()
        editID = self.editedTree.item(selectedItem)['values'][0]
        self.editedTree.delete(selectedItem)
        if self.editLeafDict.get(editID) is not None:
            self.editLeafDict.pop(editID)

    def save_file_edit(self):
        if self.currentLeaf is None:
            return False
        if self.currentLeaf not in self.editLeafDict.values():
            self.log('当前文件已被移除')
        #print(self.currentLeaf['itemInDict'])
        res = {}
        for key,entryAndType in self.entryTagDict.items():
            values = get_entrys_values(key,entryAndType)
            if values!=[]:
                res[key] = values
    
        self.currentLeaf['itemInDict'].update(res)
        if self.exFrameObj is not None:
            res_ex = self.exFrameObj.read_values()
            self.currentLeaf['itemInDict'].update(res_ex)
        #print('保存文件...',self.currentLeaf['itemInDict'])
        if self.currentLeaf.get('jsonEditorServer') is not None and self.currentLeaf['jsonEditorServer'].running:
            self.currentLeaf['jsonEditorServer'].data = self.currentLeaf['itemInDict']

    def open_advance_edit(self):
        def fixJson(fileInDict:dict):
            for key,value in fileInDict.items():
                if isinstance(value,dict):
                    fixJson(value)
                elif not isinstance(value,list):
                    fileInDict[key] = [value]
        def start_json_thread():
            def save(itemInDict_new:dict):
                #print(itemInDict_new)
                fixJson(itemInDict_new)
                localLeaf['itemInDict'] = itemInDict_new
                self.fillFrameWithItemLeaf(localLeaf)
            self.currentLeaf['jsonEditorServer'] = jsoneditor.editjson(self.currentLeaf['itemInDict'],save,options={'mode':'code'},title=self.currentLeaf['itemInDict'].get('[name]'),run_in_thread=True)
            localLeaf = self.currentLeaf
        if self.currentLeaf.get('jsonEditorServer') is None or self.currentLeaf['jsonEditorServer'].running==False:
            self.save_file_edit()
            start_json_thread()
        else:
            jsoneditor.open_browser(self.currentLeaf['jsonEditorServer'].port,False)

    def select_stkType(self,e=None):
        #print(self.stkTypeE.get())
        for child in self.exEditFrame.children.copy().values():
            child.destroy()
        newExFrameClass = self.exFramesDict.get(self.stkTypeE.get())
        if newExFrameClass is not None:
            exFrame = newExFrameClass(self.exEditFrame)
            exFrame.pack(expand=True,fill='both')
            exFrame.fill_values(self.currentLeaf)
            self.exFrameObj = exFrame
        else:
            self.exFrameObj = None
    
    def getItemPVFInfo(self,blankString='')->str:
            if self.idE.get()=='':
                res = blankString
                return res
            try:
                itemID = int(self.idE.get())
            except:
                return '请输入整数ID'
            res = cacheM.get_Item_Info_In_Text(itemID).replace(r'%%',r'%').strip()
            return res
    
    def readItemID(self,name_id='id'):
            if name_id=='id':
                id_ = self.idE.get()
                try:
                    id_ = int(id_)
                except:
                    id_ = 0
                name = str(cacheM.ITEMS_dict.get(int(id_)))
            else:
                id_,name = self.searchNameE.get().split(' ',1)
                id_ = id_[1:-1]
                
            self.idE.delete(0,tk.END)
            self.idE.insert(0,id_)
            self.searchNameE.delete(0,tk.END)
            self.searchNameE.insert(0,name)
            self.searchNameE.config(values=[])
            print(name,id_)

    def searchItem(self,e:tk.Event):
            '''搜索物品名'''
            if e.x<100:return
            key = self.searchNameE.get()
            if len(key)>0:
                res = cacheM.searchItem(key,itemList=cacheM.stackableDict.items())
                self.searchNameE.config(values=[str([item[0]])+' '+item[1] for item in res])

class PvfeditequipmentframeWidget(ttk.Frame):
    def __init__(self, master=None, **kw):
        super(PvfeditequipmentframeWidget, self).__init__(master, **kw)
        self.editedListFrame = ttk.Labelframe(self)
        self.editedListFrame.configure(height=200, text='已编辑列表', width=200)
        self.searchNameE = ttk.Combobox(self.editedListFrame)
        self.searchNameE.pack(fill="x", side="top")
        self.idE = ttk.Entry(self.editedListFrame)
        self.idE.pack(fill="x", side="top")
        self.addLeafFrame = ttk.Frame(self.editedListFrame)
        self.addLeafFrame.configure(height=23, width=200)
        self.copyThisBtn = ttk.Button(self.addLeafFrame)
        self.copyThisBtn.configure(state="disabled", text='以该物品为模板')
        self.copyThisBtn.pack(expand="true", fill="x", side="left")
        self.copyThisBtn.configure(command=self.btn_edit_with_new_file)
        self.editThisBtn = ttk.Button(self.addLeafFrame)
        self.editThisBtn.configure(state="disabled", text='修改该物品数据')
        self.editThisBtn.pack(expand="true", fill="x", side="right")
        self.editThisBtn.configure(command=self.btn_edit_file)
        self.addLeafFrame.pack(fill="x", side="top")
        self.treeViewFrame = ttk.Frame(self.editedListFrame)
        self.treeViewFrame.configure(height=200, width=300)
        self.editedTree = ttk.Treeview(self.treeViewFrame)
        self.editedTree.configure(selectmode="browse", show="headings")
        self.editedTree.pack(expand="true", fill="both", side="left")
        self.editedTree.bind(
            "<<TreeviewSelect>>",
            self.select_treeview_item_Event,
            add="")
        self.listBar = ttk.Scrollbar(self.treeViewFrame)
        self.listBar.configure(orient="vertical")
        self.listBar.pack(fill="y", side="right")
        self.treeViewFrame.pack(expand="true", fill="both", side="top")
        self.treeViewBtnFrame = ttk.Frame(self.editedListFrame)
        self.treeViewBtnFrame.configure(height=23, width=200)
        self.delLeafBtn = ttk.Button(self.treeViewBtnFrame)
        self.delLeafBtn.configure(text='移除该项编辑')
        self.delLeafBtn.pack(fill="x", side="top")
        self.delLeafBtn.configure(command=self.remove_selected_item)
        self.treeViewBtnFrame.pack(fill="x", side="top")
        self.editedListFrame.pack(expand="true", fill="both", side="left")
        self.itemEditFrame = ttk.Labelframe(self)
        self.itemEditFrame.configure(height=200, text='装备数据修改', width=200)
        self.equBasicF = ttk.Frame(self.itemEditFrame)
        self.equBasicF.configure(height=200, width=200)
        self.itemInfoFrame = ttk.Frame(self.equBasicF)
        self.itemInfoFrame.configure(height=200, width=200)
        label1 = ttk.Label(self.itemInfoFrame)
        label1.configure(text='文件路径', width=8)
        label1.pack(side="left")
        self.filePathE = ttk.Entry(self.itemInfoFrame)
        self.filePathE.configure(state="readonly")
        self.filePathE.pack(expand="true", fill="x", side="right")
        self.itemInfoFrame.pack(expand="false", fill="x", pady=3, side="top")
        self.frame2 = ttk.Frame(self.equBasicF)
        self.frame2.configure(height=200, width=200)
        label2 = ttk.Label(self.frame2)
        label2.configure(anchor="center", text='装备种类', width=8)
        label2.pack(side="left")
        self.equTypeE = ttk.Combobox(self.frame2)
        self.equTypeE.configure(width=10)
        self.equTypeE.pack(expand="true", fill="x", side="left")
        self.equTypeValueE = ttk.Spinbox(self.frame2)
        self.equTypeValueE.configure(width=3)
        self.equTypeValueE.pack(expand="true", fill="x", side="left")
        label37 = ttk.Label(self.frame2)
        label37.configure(text='交易类型')
        label37.pack(side="left")
        self.attachTypeE = ttk.Combobox(self.frame2)
        self.attachTypeE.configure(width=10)
        self.attachTypeE.pack(expand="true", fill="x", side="right")
        self.frame2.pack(expand="false", fill="x", pady=3, side="top")
        frame4 = ttk.Frame(self.equBasicF)
        frame4.configure(height=200, width=200)
        self.saveFileEditBtn = ttk.Button(frame4)
        self.saveFileEditBtn.configure(text='保存修改')
        self.saveFileEditBtn.pack(expand="true", fill="x", side="left")
        self.saveFileEditBtn.configure(command=self.read_and_save_file_edit)
        self.advanceBtn = ttk.Button(frame4)
        self.advanceBtn.configure(text='高级修改')
        self.advanceBtn.pack(expand="true", fill="x", side="right")
        self.advanceBtn.configure(command=self.open_advance_edit)
        frame4.pack(expand="false", fill="x", pady=3, side="bottom")
        self.frame10 = ttk.Frame(self.equBasicF)
        self.frame10.configure(height=200, width=200)
        label16 = ttk.Label(self.frame10)
        label16.configure(anchor="center", text='名称', width=8)
        label16.pack(side="left")
        self.nameE = ttk.Entry(self.frame10)
        self.nameE.pack(expand="true", fill="x", side="right")
        self.frame10.pack(fill="x", pady=3, side="top")
        self.frame11 = ttk.Frame(self.equBasicF)
        self.frame11.configure(height=200, width=200)
        label17 = ttk.Label(self.frame11)
        label17.configure(anchor="center", text='名称2', width=8)
        label17.pack(side="left")
        self.nameE2 = ttk.Entry(self.frame11)
        self.nameE2.pack(expand="true", fill="x", side="right")
        self.frame11.pack(fill="x", pady=3, side="top")
        self.frame12 = ttk.Frame(self.equBasicF)
        self.frame12.configure(height=200, width=200)
        label18 = ttk.Label(self.frame12)
        label18.configure(anchor="center", text='描述', width=8)
        label18.pack(side="left")
        self.explainE = tk.Text(self.frame12)
        self.explainE.configure(
            height=3,
            highlightbackground="#808080",
            highlightthickness=1,
            relief="flat",
            width=20)
        self.explainE.pack(fill="x", side="top")
        self.frame12.pack(fill="x", pady=3, side="top")
        self.frame13 = ttk.Frame(self.equBasicF)
        self.frame13.configure(height=200, width=200)
        label19 = ttk.Label(self.frame13)
        label19.configure(anchor="center", text='描述2', width=8)
        label19.pack(side="left")
        self.flavorE = tk.Text(self.frame13)
        self.flavorE.configure(
            height=3,
            highlightbackground="#808080",
            highlightthickness=1,
            relief="flat",
            width=20)
        self.flavorE.pack(fill="x", side="top")
        self.frame13.pack(fill="x", pady=3, side="top")
        self.frame14 = ttk.Frame(self.equBasicF)
        self.frame14.configure(height=200, width=200)
        label20 = ttk.Label(self.frame14)
        label20.configure(anchor="center", text='稀有度', width=8)
        label20.pack(side="left")
        self.rarityE = ttk.Combobox(self.frame14)
        self.rarityE.configure(width=10)
        self.rarityE.pack(expand="true", fill="x", side="right")
        self.frame14.pack(fill="x", pady=3, side="top")
        self.frame15 = ttk.Frame(self.equBasicF)
        self.frame15.configure(height=200, width=200)
        label21 = ttk.Label(self.frame15)
        label21.configure(anchor="center", text='重量', width=8)
        label21.pack(side="left")
        self.weightE = ttk.Entry(self.frame15)
        self.weightE.pack(expand="true", fill="x", side="right")
        self.frame15.pack(fill="x", pady=3, side="top")
        self.frame16 = ttk.Frame(self.equBasicF)
        self.frame16.configure(height=200, width=200)
        label22 = ttk.Label(self.frame16)
        label22.configure(anchor="center", text='价格', width=8)
        label22.pack(side="left")
        self.priceE = ttk.Entry(self.frame16)
        self.priceE.pack(expand="true", fill="x", side="right")
        self.frame16.pack(fill="x", pady=3, side="top")
        self.frame17 = ttk.Frame(self.equBasicF)
        self.frame17.configure(height=200, width=200)
        label23 = ttk.Label(self.frame17)
        label23.configure(
            anchor="center",
            justify="left",
            text='最低等级',
            width=8)
        label23.pack(side="left")
        self.levE = ttk.Spinbox(self.frame17)
        self.levE.configure(from_=0, to=100)
        self.levE.pack(expand="true", fill="x", side="right")
        self.frame17.pack(fill="x", pady=3, side="top")
        self.frame18 = ttk.Frame(self.equBasicF)
        self.frame18.configure(height=200, width=200)
        label24 = ttk.Label(self.frame18)
        label24.configure(anchor="center", justify="left", text='职业', width=8)
        label24.pack(side="left")
        self.jobE3 = ttk.Combobox(self.frame18)
        self.jobE3.configure(width=10)
        self.jobE3.pack(expand="true", fill="x", side="right")
        self.jobE2 = ttk.Combobox(self.frame18)
        self.jobE2.configure(width=10)
        self.jobE2.pack(expand="true", fill="x", side="right")
        self.jobE1 = ttk.Combobox(self.frame18)
        self.jobE1.configure(width=10)
        self.jobE1.pack(expand="true", fill="x", side="right")
        self.frame18.pack(fill="x", pady=3, side="top")
        self.frame19 = ttk.Frame(self.equBasicF)
        self.frame19.configure(height=200, width=200)
        label25 = ttk.Label(self.frame19)
        label25.configure(
            anchor="center",
            justify="left",
            text='要求技能',
            width=8)
        label25.pack(side="left")
        self.reqSkillE = ttk.Combobox(self.frame19)
        self.reqSkillE.configure(width=10)
        self.reqSkillE.pack(expand="true", fill="x", side="left")
        entry1 = ttk.Entry(self.frame19)
        entry1.configure(state="readonly", width=10)
        entry1.pack(expand="true", fill="x", side="right")
        self.frame19.pack(fill="x", ipadx=3, side="top")
        self.frame20 = ttk.Frame(self.equBasicF)
        self.frame20.configure(height=200, width=200)
        label28 = ttk.Label(self.frame20)
        label28.configure(
            anchor="center",
            justify="left",
            text='魔法封印',
            width=8)
        label28.pack(side="left")
        self.randomOptE = ttk.Combobox(self.frame20)
        self.randomOptE.configure(values='0 1', width=10)
        self.randomOptE.pack(expand="true", fill="x", side="right")
        self.frame20.pack(fill="x", ipady=3, side="top")
        self.frame29 = ttk.Frame(self.equBasicF)
        self.frame29.configure(height=200, width=200)
        label38 = ttk.Label(self.frame29)
        label38.configure(anchor="center", justify="left", text='耐久度', width=8)
        label38.pack(side="left")
        self.durabilityE = ttk.Spinbox(self.frame29)
        self.durabilityE.configure(from_=0, to=100)
        self.durabilityE.pack(expand="true", fill="x", side="right")
        self.frame29.pack(fill="x", pady=3, side="top")
        self.equBasicF.pack(expand="true", fill="both", side="left")
        self.itemEditFrame.pack(expand="true", fill="both", side="left")
        self.exEditFrame = ttk.Labelframe(self)
        self.exEditFrame.configure(height=200, text='装备数据修改-附加', width=250)
        self.equPropertyE = ttk.Frame(self.exEditFrame)
        self.equPropertyE.configure(height=200, width=200)
        self.frame35 = ttk.Frame(self.equPropertyE)
        self.frame35.configure(height=200, width=200)
        label42 = ttk.Label(self.frame35)
        label42.configure(
            anchor="center",
            justify="left",
            text='物理攻击',
            width=8)
        label42.pack(side="left")
        self.phyAtkE1 = ttk.Spinbox(self.frame35)
        self.phyAtkE1.configure(from_=0, to=100)
        self.phyAtkE1.pack(expand="true", fill="x", side="right")
        self.phyAtkE2 = ttk.Spinbox(self.frame35)
        self.phyAtkE2.configure(from_=0, to=100)
        self.phyAtkE2.pack(expand="true", fill="x", side="right")
        self.frame35.pack(fill="x", pady=3, side="top")
        self.frame36 = ttk.Frame(self.equPropertyE)
        self.frame36.configure(height=200, width=200)
        label43 = ttk.Label(self.frame36)
        label43.configure(
            anchor="center",
            justify="left",
            text='魔法攻击',
            width=8)
        label43.pack(side="left")
        self.magicAtkE1 = ttk.Spinbox(self.frame36)
        self.magicAtkE1.configure(from_=0, to=100)
        self.magicAtkE1.pack(expand="true", fill="x", side="right")
        self.magicAtkE2 = ttk.Spinbox(self.frame36)
        self.magicAtkE2.configure(from_=0, to=100)
        self.magicAtkE2.pack(expand="true", fill="x", side="right")
        self.frame36.pack(fill="x", pady=3, side="top")
        self.frame37 = ttk.Frame(self.equPropertyE)
        self.frame37.configure(height=200, width=200)
        label44 = ttk.Label(self.frame37)
        label44.configure(
            anchor="center",
            justify="left",
            text='独立攻击',
            width=8)
        label44.pack(side="left")
        self.sepAtkE1 = ttk.Spinbox(self.frame37)
        self.sepAtkE1.configure(from_=0, to=100)
        self.sepAtkE1.pack(expand="true", fill="x", side="right")
        self.sepAtkE2 = ttk.Spinbox(self.frame37)
        self.sepAtkE2.configure(from_=0, to=100)
        self.sepAtkE2.pack(expand="true", fill="x", side="right")
        self.frame37.pack(fill="x", pady=3, side="top")
        self.frame38 = ttk.Frame(self.equPropertyE)
        self.frame38.configure(height=200, width=200)
        label45 = ttk.Label(self.frame38)
        label45.configure(
            anchor="center",
            justify="left",
            text='攻击速度',
            width=8)
        label45.pack(side="left")
        self.atkSpeedE = ttk.Spinbox(self.frame38)
        self.atkSpeedE.configure(from_=0, to=1000, width=8)
        self.atkSpeedE.pack(expand="true", fill="x", side="left")
        self.frame40 = ttk.Frame(self.frame38)
        self.frame40.configure(height=200, width=200)
        label47 = ttk.Label(self.frame40)
        label47.configure(
            anchor="center",
            justify="left",
            text='吟唱速度',
            width=8)
        label47.pack(side="left")
        self.castSpeedE = ttk.Spinbox(self.frame40)
        self.castSpeedE.configure(from_=0, to=100, width=8)
        self.castSpeedE.pack(expand="true", fill="x", side="right")
        self.frame40.pack(expand="true", fill="x", side="right")
        self.frame41 = ttk.Frame(self.frame38)
        self.frame41.configure(height=200, width=200)
        label48 = ttk.Label(self.frame41)
        label48.configure(
            anchor="center",
            justify="left",
            text='移动速度',
            width=8)
        label48.pack(side="left")
        self.moveSpeedE = ttk.Spinbox(self.frame41)
        self.moveSpeedE.configure(from_=0, to=1000, width=8)
        self.moveSpeedE.pack(expand="true", fill="x", side="right")
        self.frame41.pack(expand="true", fill="x", side="right")
        self.frame38.pack(fill="x", pady=3, side="top")
        self.frame23 = ttk.Frame(self.equPropertyE)
        self.frame23.configure(height=200, width=200)
        label31 = ttk.Label(self.frame23)
        label31.configure(
            anchor="center",
            justify="left",
            text='物理防御',
            width=8)
        label31.pack(side="left")
        self.phyDefenseE1 = ttk.Spinbox(self.frame23)
        self.phyDefenseE1.configure(from_=0, to=100)
        self.phyDefenseE1.pack(expand="true", fill="x", side="right")
        self.phyDefenseE2 = ttk.Spinbox(self.frame23)
        self.phyDefenseE2.configure(from_=0, to=100)
        self.phyDefenseE2.pack(expand="true", fill="x", side="right")
        self.frame23.pack(fill="x", pady=3, side="top")
        self.frame25 = ttk.Frame(self.equPropertyE)
        self.frame25.configure(height=200, width=200)
        label33 = ttk.Label(self.frame25)
        label33.configure(
            anchor="center",
            justify="left",
            text='魔法防御',
            width=8)
        label33.pack(side="left")
        self.magicDefenseE1 = ttk.Spinbox(self.frame25)
        self.magicDefenseE1.configure(from_=0, to=100)
        self.magicDefenseE1.pack(expand="true", fill="x", side="right")
        self.magicDefenseE2 = ttk.Spinbox(self.frame25)
        self.magicDefenseE2.configure(from_=0, to=100)
        self.magicDefenseE2.pack(expand="true", fill="x", side="right")
        self.frame25.pack(fill="x", pady=3, side="top")
        self.frame21 = ttk.Frame(self.equPropertyE)
        self.frame21.configure(height=200, width=200)
        label29 = ttk.Label(self.frame21)
        label29.configure(anchor="center", justify="left", text='力量', width=8)
        label29.pack(side="left")
        self.phyAtkE = ttk.Spinbox(self.frame21)
        self.phyAtkE.configure(from_=0, to=100)
        self.phyAtkE.pack(expand="true", fill="x", side="left")
        self.frame22 = ttk.Frame(self.frame21)
        self.frame22.configure(height=200, width=200)
        label30 = ttk.Label(self.frame22)
        label30.configure(anchor="center", justify="left", text='智力', width=8)
        label30.pack(side="left")
        self.magicAtkE = ttk.Spinbox(self.frame22)
        self.magicAtkE.configure(from_=0, to=100)
        self.magicAtkE.pack(expand="true", fill="x", side="right")
        self.frame22.pack(fill="x", side="right")
        self.frame21.pack(fill="x", pady=3, side="top")
        self.frame26 = ttk.Frame(self.equPropertyE)
        self.frame26.configure(height=200, width=200)
        label34 = ttk.Label(self.frame26)
        label34.configure(anchor="center", justify="left", text='体力', width=8)
        label34.pack(side="left")
        self.phyDefenseE = ttk.Spinbox(self.frame26)
        self.phyDefenseE.configure(from_=0, to=100)
        self.phyDefenseE.pack(expand="true", fill="x", side="left")
        self.frame28 = ttk.Frame(self.frame26)
        self.frame28.configure(height=200, width=200)
        label36 = ttk.Label(self.frame28)
        label36.configure(anchor="center", justify="left", text='精神', width=8)
        label36.pack(side="left")
        self.MagicDefenseE = ttk.Spinbox(self.frame28)
        self.MagicDefenseE.configure(from_=0, to=100)
        self.MagicDefenseE.pack(expand="true", fill="x", side="right")
        self.frame28.pack(fill="x", side="right")
        self.frame26.pack(fill="x", pady=3, side="top")
        self.frame3 = ttk.Frame(self.equPropertyE)
        self.frame3.configure(height=200, width=200)
        label3 = ttk.Label(self.frame3)
        label3.configure(anchor="center", justify="left", text='技能等级', width=8)
        label3.pack(side="left")
        self.skillJobE1 = ttk.Combobox(self.frame3)
        self.skillJobE1.configure(width=10)
        self.skillJobE1.pack(expand="true", fill="x", side="left")
        self.skillJobE1.bind(
            "<<ComboboxSelected>>",
            self.select_skill_job,
            add="")
        self.skillE1 = ttk.Combobox(self.frame3)
        self.skillE1.configure(width=10)
        self.skillE1.pack(expand="true", fill="x", side="left")
        self.levE1 = ttk.Spinbox(self.frame3)
        self.levE1.configure(from_=0, to=20, width=10)
        self.levE1.pack(side="right")
        self.frame3.pack(fill="x", pady=3, side="top")
        self.frame5 = ttk.Frame(self.equPropertyE)
        self.frame5.configure(height=200, width=200)
        label4 = ttk.Label(self.frame5)
        label4.configure(anchor="center", justify="left", text='技能等级', width=8)
        label4.pack(side="left")
        self.skillJobE2 = ttk.Combobox(self.frame5)
        self.skillJobE2.configure(width=10)
        self.skillJobE2.pack(expand="true", fill="x", side="left")
        self.skillJobE2.bind(
            "<<ComboboxSelected>>",
            self.select_skill_job,
            add="")
        self.skillE2 = ttk.Combobox(self.frame5)
        self.skillE2.configure(width=10)
        self.skillE2.pack(expand="true", fill="x", side="left")
        self.levE2 = ttk.Spinbox(self.frame5)
        self.levE2.configure(from_=0, to=20, width=10)
        self.levE2.pack(side="right")
        self.frame5.pack(fill="x", pady=3, side="top")
        self.frame7 = ttk.Frame(self.equPropertyE)
        self.frame7.configure(height=200, width=200)
        label6 = ttk.Label(self.frame7)
        label6.configure(anchor="center", justify="left", text='技能等级', width=8)
        label6.pack(side="left")
        self.skillJobE3 = ttk.Combobox(self.frame7)
        self.skillJobE3.configure(width=10)
        self.skillJobE3.pack(expand="true", fill="x", side="left")
        self.skillJobE3.bind(
            "<<ComboboxSelected>>",
            self.select_skill_job,
            add="")
        self.skillE3 = ttk.Combobox(self.frame7)
        self.skillE3.configure(width=10)
        self.skillE3.pack(expand="true", fill="x", side="left")
        self.levE3 = ttk.Spinbox(self.frame7)
        self.levE3.configure(from_=0, to=20, width=10)
        self.levE3.pack(side="right")
        self.frame7.pack(fill="x", pady=3, side="top")
        self.frame8 = ttk.Frame(self.equPropertyE)
        self.frame8.configure(height=200, width=200)
        label7 = ttk.Label(self.frame8)
        label7.configure(anchor="center", justify="left", text='技能等级', width=8)
        label7.pack(side="left")
        self.skillJobE4 = ttk.Combobox(self.frame8)
        self.skillJobE4.configure(width=10)
        self.skillJobE4.pack(expand="true", fill="x", side="left")
        self.skillJobE4.bind(
            "<<ComboboxSelected>>",
            self.select_skill_job,
            add="")
        self.skillE4 = ttk.Combobox(self.frame8)
        self.skillE4.configure(width=10)
        self.skillE4.pack(expand="true", fill="x", side="left")
        self.levE4 = ttk.Spinbox(self.frame8)
        self.levE4.configure(from_=0, to=20, width=10)
        self.levE4.pack(side="right")
        self.frame8.pack(fill="x", pady=3, side="top")
        self.equPropertyE.pack(expand="true", fill="both", side="right")
        self.exEditFrame.pack(expand="true", fill="both", side="left")
        self.configure(height=400, width=600)
        self.pack(expand="true", fill="both", side="top")

        self.root = master
        self._build_other_functions()

    def _build_other_functions(self):
        self.leafType = 'equipment'
        self.editLeafDict = {}  # eid: leaf
        self.lst = None
        self.pvf:TinyPVFEditor = None
        self.currentLeaf = None
        self.editIndex = 0
        self.listBar.config(command=self.editedTree.yview)
        self.editedTree.config(yscrollcommand=self.listBar.set)
        CreateToolTip(self.advanceBtn,'打开浏览器对json文件进行修改\n在浏览器中点击【√】以保存数据')
        CreateToolTip(self.saveFileEditBtn,'保存对该文件的编辑至内存')
        CreateToolTip(self.searchNameE,textFunc=lambda:self.getItemPVFInfo('输入物品名进行搜索'))
        CreateToolTip(self.idE,textFunc=lambda:self.getItemPVFInfo('输入物品ID进行搜索'))
        self.searchNameE.bind('<Button-1>',self.searchItem)
        self.searchNameE.bind("<<ComboboxSelected>>",lambda e:self.readItemID('name'))
        self.idE.bind('<FocusOut>',lambda e:self.readItemID('id'))
        self.idE.bind('<Return>',lambda e:self.readItemID('id'))
        self.editedTree
        self.editedTree["columns"] = ("1", "2", "3")
        self.editedTree['show'] = 'headings'
        self.editedTree.column("1", width = 20, anchor ='c')
        self.editedTree.column("2", width = 90, anchor ='c')
        self.editedTree.column("3", width = 50, anchor ='c')
        self.editedTree.heading("1", text ="序号")
        self.editedTree.heading("2", text ="物品名")
        self.editedTree.heading("3", text ="物品ID")
        _ = self.editedTree.insert('',tk.END,values=[])
        self.editedTree.delete(_)
        self.equTypeE.config(values=list(SegKeyDict['equipment'].keys()))
        useableJobValues = [
            "[all]",
            "[swordman]",
            "[fighter]",
            "[at fighter]",
            "[gunner]",
            "[at gunner]",
            "[mage]",
            "[priest]",
            "[thief]",
            "[at mage]",
            "[demonic swordman]",
            "[creator mage]"
        ]
        self.attachTypeList = [
            "[sealing]",
            "[free]",
            "[trade]",
            "[account]",
            "[trade delete]",
            "[trade]]",
            "[sealing trade]"
        ]
        self.attachTypeE.config(values=self.attachTypeList)
        self.jobEList = [self.jobE1,self.jobE2,self.jobE3]
        for jobE in self.jobEList:
            jobE.config(values=useableJobValues)
        self.entryTagDict = {
            '[equipment type]':[[self.equTypeE,self.equTypeValueE],[str,int]],
            '[name]':[self.nameE,str],
            '[name2]':[self.nameE2,str],
            '[explain]':[self.explainE,str],
            '[flavor text]':[self.flavorE,str],
            '[rarity]':[self.rarityE,int],
            '[weight]':[self.weightE,int],
            '[price]':[self.priceE,int],
            '[minimum level]':[self.levE,int],
            '[usable job]':[self.jobEList,str],
            '[physical attack]':[self.phyAtkE,int],
            '[magical attack]':[self.magicAtkE,int],
            '[attack speed]':[self.atkSpeedE,int],
            '[cast speed]':[self.castSpeedE,int],
            '[equipment physical attack]':[[self.phyAtkE1,self.phyAtkE2],int],
            '[equipment magical attack]':[[self.magicAtkE1,self.magicAtkE2],int],
            '[separate attack]':[[self.sepAtkE1,self.sepAtkE2],int],
            '[random option]':[self.randomOptE,int],
            '[move speed]':[self.moveSpeedE,int],
            '[attach type]':[self.attachTypeE,str],
            '[equipment physical defense]':[[self.phyDefenseE1,self.phyDefenseE2],int],
            '[equipment magical defense]':[[self.magicDefenseE1,self.magicDefenseE2],int],
            '[durability]':[self.durabilityE,int],
            '[required skill]':[self.reqSkillE,int],
            '[magical defense]':[self.MagicDefenseE,int],
            '[physical defense]':[self.phyDefenseE,int],
            
        }
        self.rarityE.config(values=[f'{key}-{value}' for key,value in rarityMap.items()])
        self.randomOptE.config(values=[0,1])

        self.skillEntrys = [
            [[self.skillJobE1,self.skillE1,self.levE1],[str,int,int]],
            [[self.skillJobE2,self.skillE2,self.levE2],[str,int,int]],
            [[self.skillJobE3,self.skillE3,self.levE3],[str,int,int]],
            [[self.skillJobE4,self.skillE4,self.levE4],[str,int,int]],
        ]

    def select_skill_job(self,event:tk.Event=None):
        widget = event.widget
        for skillEntryList,structTypes in self.skillEntrys:
            if event.widget in skillEntryList:
                #print(statEntryList)
                widgetIndex = skillEntryList.index(event.widget)
                break
        jobID,job = widget.get().split('-')
        jobID = int(jobID)
        skillList = cacheM.PVFcacheDict.get('skill').get(jobID)
        values = []
        for skillID,skillDict in skillList.items():
            skillName = skillDict.get('[name]')
            values.append(f'{skillID}-{skillName}')
        skillEntryList[1].config(values=values)
        skillEntryList[1].current(0)

    def fillFrameWithItemLeaf(self,itemLeaf:dict):
        self.filePathE.config(state='normal')
        clearFrame(self.itemEditFrame)
        clearFrame(self.exEditFrame)
        self.currentLeaf = itemLeaf
        itemInDict = itemLeaf['itemInDict'].copy()
        #print(itemInDict)
        self.filePathE.insert(0,itemLeaf['filePath'])
        self.filePathE.config(state='readonly')
        for tag,entryAndTypes in self.entryTagDict.items():
            insert(entryAndTypes[0],tag,itemInDict)
        
        

        tag = '[skill levelup]'
        if itemInDict.get(tag) is not None:
            for i,value in enumerate(itemInDict.get(tag)):
                try:
                    if i%3==0:
                        itemInDict.get(tag)[i] = f'{self.jobTagDictRev.get(value)}-{value}'
                        jobID = self.jobTagDictRev.get(value)
                    elif i%3==1:
                        itemInDict.get(tag)[i] = f'{value}-{cacheM.PVFcacheDict.get("skill").get(jobID).get(value).get("[name]")}'
                except:
                    pass
            #print(itemInDict.get(tag))
            entrys = []
            for entrysAndTypes in self.skillEntrys:
                entrys.extend(entrysAndTypes[0])
            insert(entrys,tag,itemInDict)

        if itemLeaf.get('jsonEditorServer') is None:
            itemLeaf['jsonEditorServer'] = None
        
        
        #jsoneditor.editjson(itemInDict,print,options={'mode':'code'},title=itemInDict.get('[name]'))

    def btn_edit_with_new_file(self):
        itemID = int(self.idE.get())
        itemName = cacheM.equipmentDict.get(itemID)
        filePath = self.pvf.itemID2itemPath(itemID,self.lst)
        leaf = self.pvf.fileTreeDict.get(filePath).copy()
        leaf['itemInDict'] = self.pvf.read_File_In_Dict(filePath)
        leaf['itemID'] = None
        leaf['filePath'] = 'equipment/'
        leaf['fn'] = None
        leaf['itemInDict']['[name]'] = ['[新]'+itemName]
        self.fillFrameWithItemLeaf(leaf)
        values = [self.editIndex,'[新]'+itemName,None]
        self.editLeafDict[self.editIndex] = leaf
        node = self.editedTree.insert('',tk.END,values=values)
        leaf['indexInTreeView'] = self.editIndex
        self.editIndex += 1
        self.editedTree.see(node)
        self.editedTree.selection_set(node)

    def update_with_PVF(self):
        self.enable_Btns()
        print(cacheM.PVFcacheDict.keys())#['jobTagDict'])
        self.jobTagDictRev = {value:key for key,value in cacheM.PVFcacheDict.get('jobTagDict').items()}        
        for skillEntrys in self.skillEntrys:
            skillEntrys[0][0].config(values=[f'{key}-{value}' for key,value in cacheM.PVFcacheDict.get('jobTagDict').items()])
            #skillEntrys[0][0].current(0)

    def enable_Btns(self):
        self.editThisBtn.config(state='normal')
        #self.copyThisBtn.config(state='normal')

    def btn_edit_file(self):
        try:
            itemID = int(self.idE.get())
            itemName = cacheM.equipmentDict.get(itemID)
        except:
            self.log('请填充物品ID')
            return False
        if itemName is None:
            self.log('该物品ID不存在')
            return False
        for child in self.editedTree.get_children():
            if itemID == self.editedTree.item(child)["values"][2]:
                self.log('该物品ID已被添加')
                return False


        filePath = self.pvf.itemID2itemPath(itemID,self.lst)
        leaf = self.pvf.fileTreeDict.get(filePath).copy()
        leaf['itemInDict'] = self.pvf.read_File_In_Dict(filePath)
        leaf['itemID'] = itemID
        self.fillFrameWithItemLeaf(leaf)
        values = [self.editIndex,itemName,itemID]
        self.editLeafDict[self.editIndex] = leaf
        node = self.editedTree.insert('',tk.END,values=values)
        leaf['indexInTreeView'] = self.editIndex
        self.editIndex += 1
        self.editedTree.see(node)
        self.editedTree.selection_set(node)
        
    def select_treeview_item_Event(self, event=None):
        selectedItem = self.editedTree.selection()
        currentEditID = self.editedTree.item(selectedItem)['values'][0]
        print(currentEditID)
        currentLeaf = self.editLeafDict.get(currentEditID)
        if currentLeaf is None:
            return False
        elif currentLeaf!=self.currentLeaf:
            self.read_and_save_file_edit()
            self.currentLeaf = currentLeaf
            self.fillFrameWithItemLeaf(self.currentLeaf)

    def refill_treeview(self):
        for child in self.editedTree.get_children():
            self.editedTree.delete(child)
        for eid,leaf in self.editLeafDict.items():
            values = [eid,leaf['itemInDict'].get('[name]'),leaf['itemID']]
            item = self.editedTree.insert('',tk.END,values=values)
            print(values)
        if self.editLeafDict=={}:
            return False
        self.editIndex = max(list(self.editLeafDict.keys())) + 1
        self.currentLeaf = None
        self.filePathE.config(state='normal')
        clearFrame(self.itemEditFrame)
        self.filePathE.config(state='readonly')
        #print(self.editLeafDict)

    def remove_selected_item(self):
        selectedItem = self.editedTree.selection()
        editID = self.editedTree.item(selectedItem)['values'][0]
        self.editedTree.delete(selectedItem)
        if self.editLeafDict.get(editID) is not None:
            self.editLeafDict.pop(editID)

    def read_and_save_file_edit(self):
        if self.currentLeaf is None:
            return False
        if self.currentLeaf not in self.editLeafDict.values():
            self.log('当前文件已被移除')
        #print(self.currentLeaf['itemInDict'])
        res = {}
        for key,entryAndTypes in self.entryTagDict.items():
            values = get_entrys_values(key,entryAndTypes)
            if values!=[]:
                res[key] = values
        
        key = '[skill levelup]'
        statSeg = []
        for entryAndTypes in self.skillEntrys:
            values = get_entrys_values(key,entryAndTypes)
            if len(values)==3:
                statSeg.extend(values)
        res[key] = statSeg

        #print(res)
        self.currentLeaf['itemInDict'].update(res)
        #print(self.currentLeaf['itemInDict'])
        if self.currentLeaf.get('jsonEditorServer') is not None and self.currentLeaf['jsonEditorServer'].running:
            self.currentLeaf['jsonEditorServer'].data = self.currentLeaf['itemInDict']
        

    def open_advance_edit(self):
        def fixJson(fileInDict:dict):
            for key,value in fileInDict.items():
                if isinstance(value,dict):
                    fixJson(value)
                elif not isinstance(value,list):
                    fileInDict[key] = [value]
        def start_json_thread():
            def save(itemInDict_new:dict):
                #print(itemInDict_new)
                fixJson(itemInDict_new)
                localLeaf['itemInDict'] = itemInDict_new
                self.fillFrameWithItemLeaf(localLeaf)
            self.currentLeaf['jsonEditorServer'] = jsoneditor.editjson(self.currentLeaf['itemInDict'],save,options={'mode':'code'},title=self.currentLeaf['itemInDict'].get('[name]'),run_in_thread=True)
            localLeaf = self.currentLeaf
        if self.currentLeaf['jsonEditorServer'] is None or self.currentLeaf['jsonEditorServer'].running==False:
            self.read_and_save_file_edit()
            start_json_thread()
        else:
            jsoneditor.open_browser(self.currentLeaf['jsonEditorServer'].port,False)
    
    def getItemPVFInfo(self,blankString='')->str:
            if self.idE.get()=='':
                res = blankString
                return res
            try:
                itemID = int(self.idE.get())
            except:
                return '请输入整数ID'
            res = cacheM.get_Item_Info_In_Text(itemID).replace(r'%%',r'%').strip()
            return res
    
    def readItemID(self,name_id='id'):
            if name_id=='id':
                id_ = self.idE.get()
                try:
                    id_ = int(id_)
                except:
                    id_ = 0
                name = str(cacheM.ITEMS_dict.get(int(id_)))
            else:
                id_,name = self.searchNameE.get().split(' ',1)
                id_ = id_[1:-1]
                
            self.idE.delete(0,tk.END)
            self.idE.insert(0,id_)
            self.searchNameE.delete(0,tk.END)
            self.searchNameE.insert(0,name)
            self.searchNameE.config(values=[])
            print(name,id_)

    def searchItem(self,e:tk.Event):
            '''搜索物品名'''
            if e.x<100:return
            key = self.searchNameE.get()
            if len(key)>0:
                res = cacheM.searchItem(key,itemList=cacheM.equipmentDict.items())
                self.searchNameE.config(values=[str([item[0]])+' '+item[1] for item in res])

class PvfeditmainframeApp:
    def __init__(self, master=None):
        # build ui
        frame1 = ttk.Frame(master)
        frame1.configure(height=600, width=800)
        self.menuFrame = tk.Frame(frame1)
        self.menuFrame.configure(height=0, width=600)
        self.menuFrame.pack(fill="x", side="top")
        self.openPVFFrame = ttk.Frame(frame1)
        menubutton1 = ttk.Menubutton(self.openPVFFrame)
        menubutton1.configure(text='文件')
        self.fileMenu = tk.Menu(menubutton1)
        self.fileMenu.configure(tearoff="false")
        self.fileMenu.add("command", command=self.open_PVF_edit, label='打开编辑')
        self.fileMenu.add("command", command=self.save_PVF_edit, label='保存编辑')
        self.fileMenu.add(
            "command",
            command=self.resave_PVF_edit,
            label='另存编辑')
        self.fileMenu.add("separator")
        self.fileMenu.add("command", command=self.open_PVF, label='加载PVF')
        self.fileMenu.add("command", command=self.export_PVF, label='导出PVF')
        menubutton1.configure(menu=self.fileMenu)
        menubutton1.pack(side="left")
        menubutton2 = ttk.Menubutton(self.openPVFFrame)
        menubutton2.configure(state="disabled", text='编辑')
        self.editMenu = tk.Menu(menubutton2)
        menubutton2.configure(menu=self.editMenu)
        menubutton2.pack(side="left")
        label1 = ttk.Label(self.openPVFFrame)
        label1.pack(side="left")
        self.PVFE = ttk.Combobox(self.openPVFFrame)
        self.PVFE.configure(state="readonly")
        self.PVFE.pack(expand="true", fill="x", side="left")
        self.openPVGBtn = ttk.Button(self.openPVFFrame)
        self.openPVGBtn.configure(text='打开PVF')
        self.openPVGBtn.pack(side="left")
        self.openPVGBtn.configure(command=self.open_PVF)
        self.exportPVFBtn = ttk.Button(self.openPVFFrame)
        self.exportPVFBtn.configure(text='导出PVF')
        self.exportPVFBtn.pack(side="left")
        self.exportPVFBtn.configure(command=self.export_PVF)
        self.encodeE = ttk.Combobox(self.openPVFFrame)
        self.encodeE.configure(state="readonly", values='big5 gbk utf-8')
        self.encodeE.pack(side="left")
        self.openPVFFrame.pack(fill="x", side="top")
        separator1 = ttk.Separator(frame1)
        separator1.configure(orient="horizontal")
        separator1.pack(expand="false", fill="x", side="top")
        self.tabView = ttk.Notebook(frame1)
        self.tabView.configure(height=550, width=1000)
        self.tabView.pack(expand="true", fill="both", side="top")
        labelframe1 = ttk.Labelframe(frame1)
        labelframe1.configure(height=200, text='事件日志', width=800)
        self.logBar = ttk.Scrollbar(labelframe1)
        self.logBar.configure(orient="vertical")
        self.logBar.pack(fill="y", side="right")
        self.logE = tk.Text(labelframe1)
        self.logE.configure(height=15, takefocus=False, width=50)
        self.logE.pack(expand="true", fill="both", side="left")
        labelframe1.pack(fill="x", side="top")
        frame1.pack(expand="true", fill="both", side="top")



        # Main widget
        self.mainwindow = frame1
        self.root = master
        self._other_build_functions()

    def run(self):
        
        self.mainwindow.mainloop()
    
    def _other_build_functions(self):
        def _build_stk_tab():
            widget = PvfeditstackableframeWidget(self.tabView)
            widget.pack(expand=True, fill="both")
            self.tabView.add(widget,text=' 道具 ')
            widget.log = self.log
            return widget
        def _build_equ_tab():
            widget = PvfeditequipmentframeWidget(self.tabView)
            widget.pack(expand=True, fill="both")
            self.tabView.add(widget,text=' 装备 ')
            widget.log = self.log
            return widget
        def _build_etc_tab():
            widget = EtcframeWidget(self.tabView)
            widget.pack(expand=True, fill="both")
            self.tabView.add(widget,text='掉落')
            widget.log = self.log
            return widget
        def _build_skill_tab():
            widget = SkilleditframeWidget(self.tabView)
            widget.pack(expand=True, fill="both")
            self.tabView.add(widget,text='技能')
            widget.log = self.log
            return widget
        self.lstDict = {}
        self.editCachePath = ''
        self.pvf = None
        self.stkTab = _build_stk_tab()
        self.equTab = _build_equ_tab()
        self.sklTab = _build_skill_tab()
        self.etcTab = _build_etc_tab()
        self.itemTabList = [self.stkTab, self.equTab, self.etcTab, self.sklTab]
        self.logBar.config(command =self.logE.yview)
        self.logE.config(yscrollcommand=self.logBar.set)
        self.encodeE.set('big5')
        CreateToolTip(self.encodeE,'文件编码，当乱码时切换编码重新加载')
        bind_command(self.root,"<Control_L><o>", lambda e:self.open_PVF_edit())
        bind_command(self.root,"<Control_L><s>", lambda e:self.save_PVF_edit())
        bind_command(self.root,"<Control_R><o>", lambda e:self.open_PVF())
        bind_command(self.root,"<Control_R><s>", lambda e:self.export_PVF())
    
    def open_PVF(self):
        def inner():
            PVF = askopenfilename(filetypes=[('DNF Script.pvf file','*.pvf')])
            p = Path(PVF)
            if PVF!='' and p.exists():
                self.log(PVF)
                cacheM.PVFClass = TinyPVFEditor
                #print(self.encodeE.get())
                pvf:TinyPVFEditor = cacheM.loadItems2(True,PVF,retType='pvf',encode=self.encodeE.get())
                self.pvf = pvf 
                self.PVFE.delete(0,tk.END)
                self.PVFE.insert(0,p)
                stkLstPath = 'stackable/stackable.lst'
                self.lstDict['stackable'] = LstEditor(pvf.read_File_In_Decrypted_Bin(stkLstPath),pvf.stringTable,baseDir='stackable',suffix='.stk')
                self.stkTab.lst = self.lstDict['stackable']
                self.stkTab.pvf = pvf
                self.stkTab.searchNameE.delete(0,tk.END)
                self.stkTab.searchNameE.insert(0,f'输入关键词检索道具({len(cacheM.stackableDict.items())})')
                self.stkTab.enable_Btns()

                equLstPath = 'equipment/equipment.lst'
                self.lstDict['equipment'] = LstEditor(pvf.read_File_In_Decrypted_Bin(equLstPath),pvf.stringTable,baseDir='equipment',suffix='.equ')
                self.equTab.lst = self.lstDict['equipment']
                self.equTab.pvf = pvf
                self.equTab.searchNameE.delete(0,tk.END)
                self.equTab.searchNameE.insert(0,f'输入关键词检索装备({len(cacheM.equipmentDict.items())})')
                self.equTab.update_with_PVF()

                self.etcTab.pvf = pvf
                self.etcTab.on_PVF_load()

                self.sklTab.pvf = pvf
                self.sklTab.on_PVF_load()


                self.log('PVF文件已加载')
        t = threading.Thread(target=inner)
        t.start()

    def open_PVF_edit(self):
        for tab in self.itemTabList:
            if tab.editLeafDict != {}:
                res = messagebox.askokcancel('打开确认','请确认是否已保存编辑！未保存的编辑会丢失。')
                if res==False:
                    self.log('取消文件读取')
                    return False
                break
        
        path = askopenfilename(filetypes=[('DNF PVF编辑缓存.pvfedit file','*.pvfedit')])
        if path=='' or not Path(path).exists():
            self.log(f'文件路径错误，操作取消{path}')
            return False
        with open(path,'rb') as f:
            fileInCompressedJson = f.read()
        editLeafs = pickle.loads(zlib.decompress(fileInCompressedJson))
        self.stkTab.editLeafDict = editLeafs['stackable']
        self.stkTab.refill_treeview()
        self.equTab.editLeafDict = editLeafs['equipment']
        self.equTab.refill_treeview()
        self.etcTab.editLeafDict = editLeafs['etc']
        self.etcTab.update_Edited_Box()
        



    def save_PVF_edit(self):
        editLeafs = {
            'stackable':self.stkTab.editLeafDict,
            'equipment':self.equTab.editLeafDict,
            'etc':self.etcTab.editLeafDict
        }
        for tabName,leafDict in editLeafs.items():
            for leaf in leafDict.values():
                jsonServer_tmp = leaf.get('jsonEditorServer')
                if jsonServer_tmp is not None:
                    jsonServer_tmp.stop()
                leaf['jsonEditorServer'] = None
        if self.editCachePath=='':
            path = asksaveasfilename(title=f'保存文件(.pvfEdit)',filetypes=[('二进制文件',f'*.pvfEdit')],initialfile=f'PVF编辑缓存.pvfEdit')
            if path=='':
                self.log('文件路径错误，操作取消')
                return False
            else:
                if '.pvfEdit' not in path:
                    path += '.pvfEdit'
                self.editCachePath = path
        
        content = zlib.compress(pickle.dumps(editLeafs))
        with open(self.editCachePath,'wb') as f:
            f.write(content)
        self.log(f'文件已保存至 {self.editCachePath}')
    
    def resave_PVF_edit(self):
        editLeafs = {
            'stackable':self.stkTab.editLeafDict
        }
        path = asksaveasfilename(title=f'保存文件(.pvfEdit)',filetypes=[('二进制文件',f'*.pvfEdit')],initialfile=f'PVF编辑缓存.pvfEdit')
        if path=='':
            self.log('文件路径错误，操作取消')
            return False
        else:
            self.editCachePath = path
        content = zlib.compress(pickle.dumps(editLeafs))
        with open(self.editCachePath,'wb') as f:
            f.write(content)
        self.log(f'文件已保存至 {self.editCachePath}')


    def export_PVF(self):
        def inner():
            if self.pvf is None:
                self.log('当前未加载PVF文件，操作取消')
                return False
            editLeafs = {}
            newLeafs = {}
            for tab in self.itemTabList:
                newLeafs[tab.leafType] = {}
                for tmpID,leaf in tab.editLeafDict.items():
                    leaf:dict
                    leaf['content'] = b''
                    jsonServer_tmp = leaf.get('jsonEditorServer')
                    if jsonServer_tmp is not None:
                        jsonServer_tmp.stop()
                    leaf['jsonEditorServer'] = None
                    if leaf.get('fn') is not None:
                        editLeafs[leaf['filePath']] = leaf
                    else:
                        newLeafs[tab.leafType][tmpID] = leaf
            messagebox.askokcancel('注意事项','此工具为测试版本！请在替换PVF前对原始文件进行备份！')
            savePath = asksaveasfilename(title=f'保存文件(.pvf)',filetypes=[('二进制文件',f'*.pvf')],initialfile=f'Script_new.pvf')
            if savePath=='':
                self.log('文件路径错误，操作取消')
                return False
            print('====修改的节点：',editLeafs)
            print('====新增的节点',newLeafs)
            pvf:TinyPVFEditor = self.pvf
            pvf.editedLeafDict = copy.deepcopy(editLeafs)
            pvf.newLeafDict = copy.deepcopy(newLeafs)
            content = pvf.gen_File_chunk()
            try:
                with open(savePath,'wb') as f:
                    f.write(content)
                self.log(f'文件保存成功 {savePath}')
            except Exception as e:
                self.log(f'文件保存失败 {e}')
        t = threading.Thread(target=inner)
        t.setDaemon(True)
        t.start()


    
    



    def log(self,info='',*args):
        tm = time.localtime()
        infos = [info]
        infos.extend(args)
        for info in infos:
            for info in str(info).split('\n'):
                if info.strip()=='':
                    continue
                log = f'[{"%02d" % tm.tm_mon}-{"%02d" % tm.tm_mday} {"%02d" % tm.tm_hour}:{"%02d" % tm.tm_min}:{"%02d" % tm.tm_sec}] {info}\n'
                self.logE.insert(tk.END,log)
                self.logE.see(tk.END)



if __name__ == "__main__":
    IconPath = 'config/ico.ico'
    root = tk.Tk()
    root.iconbitmap(IconPath)
    root.title('PVF编辑器 测试版')
    app = PvfeditmainframeApp(root)
    pvfEditor.print = app.log
    cacheM.print = app.log
    cacheM.pvfReader.print = app.log
    app.run()
    exit()



