from pvfEditor import *
import copy
import pvfEditor
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

if not hasattr(ttk,'Spinbox'):
    class Spinbox(ttk.Entry):
        def __init__(self, master=None, **kw):  #from_=0,to=99,
            ttk.Entry.__init__(self, master, "ttk::spinbox", **kw)
        def set(self, value):
            self.tk.call(self._w, "set", value)
    ttk.Spinbox = Spinbox

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
    for i,widget in enumerate(widgets):
        if i >= len(valueInList):
            break
        ins(widget,valueInList[i])



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
    return values

def clearFrame(w:tk.Frame):
    for widget in w.children.values():
        if type(widget) in [tk.Entry,ttk.Entry,ttk.Spinbox,ttk.Combobox]:
            widget.delete(0,tk.END)
        elif type(widget) in [tk.Text]:
            widget.delete("1.0",tk.END)
        elif type(widget) in [ttk.Frame,tk.Frame,tk.LabelFrame,ttk.LabelFrame]:
            clearFrame(widget)


class SkilleditframeWidget(ttk.Frame):
    def __init__(self, master=None, **kw):
        super(SkilleditframeWidget, self).__init__(master, **kw)
        self.editedListFrame = ttk.Labelframe(self)
        self.editedListFrame.configure(height=200, text='已编辑列表', width=200)
        self.treeViewFrame = ttk.Frame(self.editedListFrame)
        self.treeViewFrame.configure(height=200, width=300)
        self.editedTree = ttk.Treeview(self.treeViewFrame)
        self.editedTree.configure(selectmode="browse", show="headings")
        self.editedTree_cols = ['column1', 'column2', 'column3']
        self.editedTree_dcols = ['column1', 'column2', 'column3']
        self.editedTree.configure(
            columns=self.editedTree_cols,
            displaycolumns=self.editedTree_dcols)
        self.editedTree.column(
            "column1",
            anchor="center",
            stretch="true",
            width=60,
            minwidth=20)
        self.editedTree.column(
            "column2",
            anchor="center",
            stretch="true",
            width=60,
            minwidth=20)
        self.editedTree.column(
            "column3",
            anchor="center",
            stretch="true",
            width=60,
            minwidth=20)
        self.editedTree.heading("column1", anchor="center", text='职业')
        self.editedTree.heading("column2", anchor="center", text='技能')
        self.editedTree.heading("column3", anchor="center", text='路径')
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
        self.skillBrowserFrame = ttk.Labelframe(self)
        self.skillBrowserFrame.configure(height=200, text='全部技能列表', width=250)
        self.jobTreeV = ttk.Treeview(self.skillBrowserFrame)
        self.jobTreeV.configure(selectmode="browse", show="headings")
        self.jobTreeV_cols = ['column4', 'column5']
        self.jobTreeV_dcols = ['column4', 'column5']
        self.jobTreeV.configure(
            columns=self.jobTreeV_cols,
            displaycolumns=self.jobTreeV_dcols)
        self.jobTreeV.column(
            "column4",
            anchor="center",
            stretch="true",
            width=40,
            minwidth=20)
        self.jobTreeV.column(
            "column5",
            anchor="center",
            stretch="true",
            width=80,
            minwidth=20)
        self.jobTreeV.heading("column4", anchor="center", text='编号')
        self.jobTreeV.heading("column5", anchor="center", text='职业')
        self.jobTreeV.pack(expand="true", fill="both", side="left")
        self.jobTreeV.bind("<<TreeviewSelect>>", self.select_Job, add="")
        self.skillTreeV = ttk.Treeview(self.skillBrowserFrame)
        self.skillTreeV.configure(selectmode="extended", show="headings")
        self.skillTreeV_cols = ['column6', 'column7', 'column8']
        self.skillTreeV_dcols = ['column6', 'column7', 'column8']
        self.skillTreeV.configure(
            columns=self.skillTreeV_cols,
            displaycolumns=self.skillTreeV_dcols)
        self.skillTreeV.column(
            "column6",
            anchor="center",
            stretch="true",
            width=40,
            minwidth=20)
        self.skillTreeV.column(
            "column7",
            anchor="center",
            stretch="true",
            width=80,
            minwidth=20)
        self.skillTreeV.column(
            "column8",
            anchor="center",
            stretch="true",
            width=60,
            minwidth=20)
        self.skillTreeV.heading("column6", anchor="center", text='编号')
        self.skillTreeV.heading("column7", anchor="center", text='技能')
        self.skillTreeV.heading("column8", anchor="center", text='路径')
        self.skillTreeV.pack(expand="true", fill="both", side="left")
        self.skillTreeV.bind("<<TreeviewSelect>>", self.select_skill, add="")
        self.skillTreeBar = ttk.Scrollbar(self.skillBrowserFrame)
        self.skillTreeBar.configure(orient="vertical")
        self.skillTreeBar.pack(expand="false", fill="y", side="right")
        self.skillBrowserFrame.pack(expand="true", fill="both", side="left")
        self.itemEditFrame = ttk.Labelframe(self)
        self.itemEditFrame.configure(height=200, text='技能数据修改', width=200)
        self.sklBasicF = ttk.Frame(self.itemEditFrame)
        self.sklBasicF.configure(height=200, width=200)
        self.itemInfoFrame = ttk.Frame(self.sklBasicF)
        self.itemInfoFrame.configure(height=200, width=200)
        label1 = ttk.Label(self.itemInfoFrame)
        label1.configure(text='文件路径', width=8)
        label1.pack(side="left")
        self.filePathE = ttk.Entry(self.itemInfoFrame)
        self.filePathE.configure(state="readonly")
        self.filePathE.pack(expand="true", fill="x", side="right")
        self.itemInfoFrame.pack(expand="false", fill="x", pady=3, side="top")
        frame4 = ttk.Frame(self.sklBasicF)
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
        self.frame10 = ttk.Frame(self.sklBasicF)
        self.frame10.configure(height=200, width=200)
        label16 = ttk.Label(self.frame10)
        label16.configure(anchor="center", text='名称', width=8)
        label16.pack(side="left")
        self.nameE = ttk.Entry(self.frame10)
        self.nameE.pack(expand="true", fill="x", side="right")
        self.frame10.pack(fill="x", pady=3, side="top")
        self.frame11 = ttk.Frame(self.sklBasicF)
        self.frame11.configure(height=200, width=200)
        label17 = ttk.Label(self.frame11)
        label17.configure(anchor="center", text='名称2', width=8)
        label17.pack(side="left")
        self.nameE2 = ttk.Entry(self.frame11)
        self.nameE2.pack(expand="true", fill="x", side="right")
        self.frame11.pack(fill="x", pady=3, side="top")
        self.frame12 = ttk.Frame(self.sklBasicF)
        self.frame12.configure(height=200, width=200)
        label18 = ttk.Label(self.frame12)
        label18.configure(anchor="center", text='描述', width=8)
        label18.pack(side="left")
        self.basicExplainE = tk.Text(self.frame12)
        self.basicExplainE.configure(
            height=5,
            highlightbackground="#808080",
            highlightthickness=1,
            relief="flat",
            width=20)
        self.basicExplainE.pack(fill="x", side="top")
        self.frame12.pack(fill="x", pady=3, side="top")
        self.frame13 = ttk.Frame(self.sklBasicF)
        self.frame13.configure(height=200, width=200)
        self.explainE = ttk.Label(self.frame13)
        self.explainE.configure(anchor="center", text='详细描述', width=8)
        self.explainE.pack(side="left")
        self.flavorE = tk.Text(self.frame13)
        self.flavorE.configure(
            height=5,
            highlightbackground="#808080",
            highlightthickness=1,
            relief="flat",
            width=20)
        self.flavorE.pack(fill="x", side="top")
        self.frame13.pack(fill="x", pady=3, side="top")
        self.frame17 = ttk.Frame(self.sklBasicF)
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
        self.frame2 = ttk.Frame(self.sklBasicF)
        self.frame2.configure(height=200, width=200)
        label2 = ttk.Label(self.frame2)
        label2.configure(anchor="center", justify="left", text='等级间隔', width=8)
        label2.pack(side="left")
        self.levRangeE = ttk.Spinbox(self.frame2)
        self.levRangeE.configure(from_=0, to=100)
        self.levRangeE.pack(expand="true", fill="x", side="right")
        self.frame2.pack(fill="x", pady=3, side="top")
        self.frame9 = ttk.Frame(self.sklBasicF)
        self.frame9.configure(height=200, width=200)
        label8 = ttk.Label(self.frame9)
        label8.configure(anchor="center", justify="left", text='可学职业', width=8)
        label8.pack(side="left")
        self.growTypeE1 = ttk.Combobox(self.frame9)
        self.growTypeE1.pack(expand="true", fill="x", side="top")
        self.growTypeE2 = ttk.Combobox(self.frame9)
        self.growTypeE2.pack(expand="true", fill="x", side="top")
        self.growTypeE3 = ttk.Combobox(self.frame9)
        self.growTypeE3.pack(expand="true", fill="x", side="top")
        self.growTypeE4 = ttk.Combobox(self.frame9)
        self.growTypeE4.pack(expand="true", fill="x", side="top")
        self.growTypeE5 = ttk.Combobox(self.frame9)
        self.growTypeE5.pack(expand="true", fill="x", side="top")
        self.frame9.pack(fill="x", pady=3, side="top")
        self.sklBasicF.pack(expand="true", fill="both", side="left")
        self.itemEditFrame.pack(expand="true", fill="both", side="left")
        self.configure(height=400, width=600)
        self.pack(expand="true", fill="both", side="top")

        self._build_other_functions()
    
    def _build_other_functions(self):
        self.leafType = 'skill'
        self.editLeafDict = {}  # path: leaf
        self.lst = None
        self.pvf:TinyPVFEditor = None
        self.currentLeaf = None
        self.editIndex = 0
        self.exFrameObj = None
        self.listBar.config(command=self.editedTree.yview)
        self.editedTree.config(yscrollcommand=self.listBar.set)
        CreateToolTip(self.advanceBtn,'打开浏览器对json文件进行修改\n在浏览器中点击【√】以保存数据')
        CreateToolTip(self.saveFileEditBtn,'保存对该文件的编辑至内存')
        self.entryTagDict = {
            '[name]':[self.nameE,str],
            '[name2]':[self.nameE2,str],
            '[basic explain]':[self.basicExplainE,str],
            '[explain]':[self.explainE,str],
            '[required level]':[self.levE,int],
            '[skill fitness growtype]':[[self.growTypeE1,self.growTypeE2,self.growTypeE3,self.growTypeE4,self.growTypeE5],[int,int,int,int,int,]],
            '[skill fitness second growtype]':[[self.growTypeE1,self.growTypeE2,self.growTypeE3,self.growTypeE4,self.growTypeE5],[int,int,int,int,int,]],
        }

    def get_leaf(self,filePath:str):
        filePath = filePath.lower()
        leaf = self.editLeafDict.get(filePath)
        if leaf is None:
            if self.pvf is None:
                return leaf
            leaf = self.pvf.fileTreeDict.get(filePath)
        itemInDict = leaf.get('itemInDict')
        if itemInDict is None:
            leaf['itemInDict'] = self.pvf.read_File_In_Dict(filePath)
            itemInDict = leaf.get('itemInDict')
        self.editLeafDict[filePath] = leaf
        return leaf

    def on_PVF_load(self):
        for child in self.jobTreeV.get_children():
            self.jobTreeV.delete(child)
        jobList = []
        for jobID,jobDict in cacheM.jobDict.items():
            jobList.append([jobID,jobDict[0]])
            self.jobTreeV.insert('',tk.END,values=jobList[-1])
        for child in self.skillTreeV.get_children():
            self.skillTreeV.delete(child)

    def select_treeview_item_Event(self, event=None):
        selectedItem = self.editedTree.selection()
        filePath = self.editedTree.item(selectedItem)['values'][-1]
        #print(currentEditID)
        currentLeaf = self.get_leaf(filePath)
        if currentLeaf is None:
            return False
        elif currentLeaf!=self.currentLeaf:
            self.read_and_save_file_edit()
            self.currentLeaf = currentLeaf
            self.fillFrameWithItemLeaf(self.currentLeaf)
    
    def fillFrameWithItemLeaf(self,itemLeaf:dict):
        self.filePathE.config(state='normal')
        clearFrame(self.itemEditFrame)
        self.currentLeaf = itemLeaf
        itemInDict = itemLeaf['itemInDict'].copy()
        #print(itemInDict)
        self.filePathE.insert(0,itemLeaf['filePath'])
        self.filePathE.config(state='readonly')
        itemLeaf['skillGrowType'] = '[skill fitness growtype]'
        for tag,entryAndTypes in self.entryTagDict.items():
            if tag == '[skill fitness second growtype]' and itemInDict.get(tag) is not None:
                itemLeaf['skillGrowType'] = '[skill fitness second growtype]'
            insert(entryAndTypes[0],tag,itemInDict)
        
        if itemLeaf.get('jsonEditorServer') is None:
            itemLeaf['jsonEditorServer'] = None
    
    def select_Job(self,e=None):
        selectedItem = self.jobTreeV.selection()
        jobID = self.jobTreeV.item(selectedItem)['values'][0]
        skillPathDict = cacheM.PVFcacheDict['skillPath'].get(jobID)
        skillsDict = cacheM.PVFcacheDict.get('skill').get(jobID)
        values = []

        for child in self.skillTreeV.get_children():
            self.skillTreeV.delete(child)

        for skillID,skillInDict in skillsDict.items():
            skillName = skillInDict.get('[name]')
            skillPath = skillPathDict.get(skillID)
            values.append([skillID,skillName,skillPath])
            self.skillTreeV.insert('',tk.END,values=values[-1])

    
    def select_skill(self,e=None):
        selItem = self.skillTreeV.selection()
        skillPath = self.skillTreeV.item(selItem)['values'][-1]
        skillLeaf = self.get_leaf(skillPath)
        self.fillFrameWithItemLeaf(skillLeaf)
        print('读取技能...\n',skillLeaf)
        
    
    def refill_treeview(self):
        '''用于读取PVF编辑'''
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
        for key,entryAndType in self.entryTagDict.items():
            if key=='[skill fitness growtype]' or '[skill fitness second growtype]':
                if self.currentLeaf.get('skillGrowType')!=key:
                    continue
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
        print(self.currentLeaf)

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
            self.read_and_save_file_edit()
            start_json_thread()
        else:
            jsoneditor.open_browser(self.currentLeaf['jsonEditorServer'].port,False)


if __name__ == "__main__":
    root = tk.Tk()
    widget = SkilleditframeWidget(root)
    widget.pack(expand=True, fill="both")
    root.mainloop()

