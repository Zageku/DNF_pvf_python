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
        frame8 = ttk.Frame(self)
        frame8.configure(height=200, width=200)
        self.skillBrowserFrame = ttk.Labelframe(frame8)
        self.skillBrowserFrame.configure(height=200, text='全部技能列表', width=250)
        frame2 = ttk.Frame(self.skillBrowserFrame)
        frame2.configure(height=200, width=200)
        self.jobTreeV = ttk.Treeview(frame2)
        self.jobTreeV.configure(
            height=11,
            selectmode="browse",
            show="headings")
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
        self.jobTreeV.pack(expand="false", fill="both", side="left")
        self.jobTreeV.bind("<<TreeviewSelect>>", self.select_Job, add="")
        self.skillTreeV = ttk.Treeview(frame2)
        self.skillTreeV.configure(selectmode="extended", show="headings")
        self.skillTreeV_cols = ['column6', 'column7', 'column8']
        self.skillTreeV_dcols = ['column6', 'column7']
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
            width=120,
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
        self.skillTreeBar = ttk.Scrollbar(frame2)
        self.skillTreeBar.configure(orient="vertical")
        self.skillTreeBar.pack(expand="false", fill="y", side="right")
        frame2.pack(expand="true", fill="both", side="top")
        frame5 = ttk.Frame(self.skillBrowserFrame)
        frame5.configure(height=200, width=200)
        self.addSkill = ttk.Button(frame5)
        self.addSkill.configure(text='将选中技能添加至当前转职')
        self.addSkill.pack(side="top")
        self.addSkill.configure(command=self.add_skill)
        frame5.pack(side="top")
        self.skillBrowserFrame.pack(expand="true", fill="both", side="left")
        self.labelframe1 = ttk.Labelframe(frame8)
        self.labelframe1.configure(height=200, text='转职技能列表', width=250)
        frame3 = ttk.Frame(self.labelframe1)
        frame3.configure(height=200, width=200)
        self.growTypeTreeV = ttk.Treeview(frame3)
        self.growTypeTreeV.configure(selectmode="browse", show="headings")
        self.growTypeTreeV_cols = ['column9', 'column10', 'column14']
        self.growTypeTreeV_dcols = ['column9', 'column10']
        self.growTypeTreeV.configure(
            columns=self.growTypeTreeV_cols,
            displaycolumns=self.growTypeTreeV_dcols)
        self.growTypeTreeV.column(
            "column9",
            anchor="center",
            stretch="true",
            width=40,
            minwidth=20)
        self.growTypeTreeV.column(
            "column10",
            anchor="center",
            stretch="true",
            width=80,
            minwidth=20)
        self.growTypeTreeV.column(
            "column14",
            anchor="w",
            stretch="true",
            width=200,
            minwidth=20)
        self.growTypeTreeV.heading("column9", anchor="center", text='编号')
        self.growTypeTreeV.heading("column10", anchor="center", text='职业')
        self.growTypeTreeV.heading("column14", anchor="w", text='sp路径')
        self.growTypeTreeV.pack(expand="false", fill="both", side="left")
        self.growTypeTreeV.bind(
            "<<TreeviewSelect>>",
            self.select_growType,
            add="")
        self.growTypeSkillTreeV = ttk.Treeview(frame3)
        self.growTypeSkillTreeV.configure(
            selectmode="extended", show="headings")
        self.growTypeSkillTreeV_cols = ['column11', 'column12', 'column13']
        self.growTypeSkillTreeV_dcols = ['column11', 'column12']
        self.growTypeSkillTreeV.configure(
            columns=self.growTypeSkillTreeV_cols,
            displaycolumns=self.growTypeSkillTreeV_dcols)
        self.growTypeSkillTreeV.column(
            "column11",
            anchor="center",
            stretch="true",
            width=40,
            minwidth=20)
        self.growTypeSkillTreeV.column(
            "column12",
            anchor="center",
            stretch="true",
            width=120,
            minwidth=20)
        self.growTypeSkillTreeV.column(
            "column13",
            anchor="center",
            stretch="true",
            width=60,
            minwidth=20)
        self.growTypeSkillTreeV.heading("column11", anchor="center", text='编号')
        self.growTypeSkillTreeV.heading("column12", anchor="center", text='技能')
        self.growTypeSkillTreeV.heading("column13", anchor="center", text='路径')
        self.growTypeSkillTreeV.pack(expand="true", fill="both", side="left")
        self.growTypeSkillTreeV.bind(
            "<<TreeviewSelect>>",
            self.select_skill_growType,
            add="")
        self.growTypeSkillTreeBar = ttk.Scrollbar(frame3)
        self.growTypeSkillTreeBar.configure(orient="vertical")
        self.growTypeSkillTreeBar.pack(expand="false", fill="y", side="right")
        frame3.pack(expand="true", fill="both", side="top")
        frame4 = ttk.Frame(self.labelframe1)
        frame4.configure(height=200, width=200)
        self.removeSkill = ttk.Button(frame4)
        self.removeSkill.configure(text='移除选中技能')
        self.removeSkill.pack(side="top")
        self.removeSkill.configure(command=self.remove_skill)
        frame4.pack(side="top")
        self.labelframe1.pack(expand="true", fill="both", side="left")
        frame8.pack(expand="true", fill="both", side="top")
        frame9 = ttk.Frame(self)
        frame9.configure(height=200, width=200)
        self.editedListFrame = ttk.Labelframe(frame9)
        self.editedListFrame.configure(height=200, text='已编辑列表', width=200)
        self.treeViewFrame = ttk.Frame(self.editedListFrame)
        self.treeViewFrame.configure(height=200, width=300)
        self.listBar = ttk.Scrollbar(self.treeViewFrame)
        self.listBar.configure(orient="vertical")
        self.listBar.pack(fill="y", side="right")
        self.editedBox = tk.Listbox(self.treeViewFrame)
        self.editedBox.pack(expand="true", fill="both", side="top")
        self.treeViewFrame.pack(expand="true", fill="both", side="top")
        self.treeViewBtnFrame = ttk.Frame(self.editedListFrame)
        self.treeViewBtnFrame.configure(height=23, width=200)
        self.delLeafBtn = ttk.Button(self.treeViewBtnFrame)
        self.delLeafBtn.configure(text='移除该项编辑')
        self.delLeafBtn.pack(fill="x", side="top")
        self.delLeafBtn.configure(command=self.remove_selected_item)
        self.treeViewBtnFrame.pack(fill="x", side="top")
        self.editedListFrame.pack(expand="true", fill="both", side="left")
        self.itemEditFrame = ttk.Labelframe(frame9)
        self.itemEditFrame.configure(height=200, text='技能数据预览', width=200)
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
        self.labelExplain = ttk.Label(self.frame13)
        self.labelExplain.configure(anchor="center", text='详细描述', width=8)
        self.labelExplain.pack(side="left")
        self.explainE = tk.Text(self.frame13)
        self.explainE.configure(
            height=8,
            highlightbackground="#808080",
            highlightthickness=1,
            relief="flat",
            width=20)
        self.explainE.pack(fill="x", side="top")
        self.frame13.pack(fill="x", pady=3, side="top")
        self.sklBasicF.pack(expand="true", fill="both", side="left")
        self.itemEditFrame.pack(expand="true", fill="both", side="left")
        frame9.pack(expand="true", fill="both", side="top")
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
        
        self.entryTagDict = {
            '[name]':[self.nameE,str],
            '[name2]':[self.nameE2,str],
            '[basic explain]':[self.basicExplainE,str],
            '[explain]':[self.explainE,str],
        }

        self.listBar.config(command=self.editedBox.yview)
        self.editedBox.config(yscrollcommand=self.listBar.set)

        self.skillTreeBar.config(command=self.skillTreeV.yview)
        self.skillTreeV.config(yscrollcommand=self.skillTreeBar.set)

        self.growTypeSkillTreeBar.config(command=self.growTypeSkillTreeV.yview)
        self.growTypeSkillTreeV.config(yscrollcommand=self.growTypeSkillTreeBar.set)

    def get_leaf(self,filePath:str,dataFormat=dict):
        filePath = filePath.lower()
        leaf = self.editLeafDict.get(filePath)
        if leaf is None:
            if self.pvf is None:
                return leaf
            leaf = self.pvf.fileTreeDict.get(filePath)
        if dataFormat == dict:
            itemInDict = leaf.get('itemInDict')
            if itemInDict is None:
                leaf['itemInDict'] = self.pvf.read_File_In_Dict(filePath)
        elif dataFormat == list:
            itemInList = leaf.get('itemInList')
            if itemInList is None:
                leaf['itemInList'] = self.pvf.read_File_In_Structed_List(filePath)
        self.editLeafDict[filePath] = leaf
        return leaf

    def load_pos(self):
        skillPosDict = {}
        nextSkillDict = {}
        for jobID,jobTag in cacheM.PVFcacheDict.get('jobTagDict').items():
            skillPosDict[jobID] = {}
            nextSkillDict[jobID] = {}
            spPath = cacheM.PVFcacheDict.get('spPath').get(jobTag)
            skillSpLeaf = self.get_leaf(spPath,list)
            print(f'加载技能图标坐标...{jobID}-{jobTag}')
            for characJobSegDict in skillSpLeaf.get('itemInList'):
                if not isinstance(characJobSegDict,dict):continue
                skillInfoSegs = characJobSegDict.get('[character job]')
                if skillInfoSegs is None: continue
                skillInfoSegs = skillInfoSegs[2:]
                for skillInfoSeg in skillInfoSegs:
                    if not isinstance(skillInfoSeg,dict):continue
                    #print(skillInfoSeg)
                    skillID = self.pvf.get_seg(skillInfoSeg.get('[skill info]'),'[index]')[0]
                    skillPos = self.pvf.get_seg(skillInfoSeg.get('[skill info]'),'[icon pos]')
                    oldPos = skillPosDict[jobID].get(skillID)
                    if oldPos is not None:
                        if oldPos[1]>skillPos[1]:
                            skillPosDict[jobID][skillID] = skillPos
                        elif oldPos[1]==skillPos[1] and oldPos[0]>skillPos[0]:
                            skillPosDict[jobID][skillID] = skillPos
                    else:
                        skillPosDict[jobID][skillID] = skillPos
        self.posDict = skillPosDict
        print(skillPosDict)

    def on_PVF_load(self):
        for child in self.jobTreeV.get_children():
            self.jobTreeV.delete(child)
        jobList = []
        for jobID,jobDict in cacheM.jobDict.items():
            jobName = jobDict[0]
            if 'at' in cacheM.PVFcacheDict.get('jobTagDict').get(jobID):
                jobName = 'AT '+jobName
            jobList.append([jobID,jobName])
            self.jobTreeV.insert('',tk.END,values=jobList[-1])
        for child in self.skillTreeV.get_children():
            self.skillTreeV.delete(child)
        self.load_pos()
    
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
        
        for child in self.growTypeTreeV.get_children():
            self.growTypeTreeV.delete(child)
        
        jobTag = cacheM.PVFcacheDict.get('jobTagDict').get(jobID)
        spPath = cacheM.PVFcacheDict.get('spPath').get(jobTag)
        skillSpLeaf = self.get_leaf(spPath,list)
        growTypes = []
        for characJobSegDict in skillSpLeaf.get('itemInList'):
            growTypes.append(characJobSegDict.get('[character job]')[1])
        for i,growType in enumerate(growTypes):
            values = [i,growType,spPath]
            self.growTypeTreeV.insert('',tk.END,values=values)

    def select_growType(self,e):
        def get_Skill_List(itemInList:list)->list:
            skillDict = {}
            skillInfoDict = cacheM.PVFcacheDict.get('skill').get(jobID)
            skillPathDict = cacheM.PVFcacheDict['skillPath'].get(jobID)
            for characJobSegDict in itemInList:
                if characJobSegDict.get('[character job]')[1]==growTypeName:
                    for skillSeg in characJobSegDict.get('[character job]')[2:]:
                        if not isinstance(skillSeg,dict): continue
                        skillInfo = skillSeg.get('[skill info]')
                        if skillInfo is None:
                            continue
                        skillID = self.pvf.get_seg(skillInfo,'[index]')[0]
                        skillName = skillInfoDict.get(skillID)
                        skillPath = skillPathDict.get(skillID)
                        if skillName is not None:
                            skillName = skillName.get('[name]')
                        skillIconPos = self.pvf.get_seg(skillInfo,'[icon pos]')
                        skillDict[skillID] = [skillName,skillPath,skillIconPos]
            skillList = [[skillID,item[0],item[1]] for skillID,item in skillDict.items()]
            skillList.sort()
            return skillList
        
        for child in self.growTypeSkillTreeV.get_children():
            self.growTypeSkillTreeV.delete(child)

        selectedItem = self.growTypeTreeV.selection()
        growTypeNo,growTypeName,spPath = self.growTypeTreeV.item(selectedItem)['values']
        selectedItem = self.jobTreeV.selection()
        jobID = self.jobTreeV.item(selectedItem)['values'][0]
        if spPath is not None:
            skillLeaf = self.get_leaf(spPath,list)
            skillList = get_Skill_List(skillLeaf.get('itemInList'))
            for values in skillList:
                self.growTypeSkillTreeV.insert('',tk.END,values=values)
    
    def select_skill(self,e=None):
        selItem = self.skillTreeV.selection()[-1]
        skillPath = self.skillTreeV.item(selItem)['values'][-1]
        skillLeaf = self.get_leaf(skillPath)
        self.fillFrameWithItemLeaf(skillLeaf)
        #print('读取技能...\n',skillLeaf)
    
    def select_skill_growType(self,e=None):
        selItem = self.growTypeSkillTreeV.selection()[-1]
        skillPath = self.growTypeSkillTreeV.item(selItem)['values'][-1]
        skillLeaf = self.get_leaf(skillPath)
        self.fillFrameWithItemLeaf(skillLeaf)
        #print('读取技能...\n',skillLeaf)

    def update_Edited_Box(self):
        self.editedBox.delete(0,tk.END)
        for filePath,leaf in self.editLeafDict.items():
            self.editedBox.insert(tk.END,filePath)
            #print(leaf)
        
    def save_growtype_skill(self):
        selectedItem = self.growTypeTreeV.selection()
        growTypeNo,growTypeName,spPath = self.growTypeTreeV.item(selectedItem)['values']
        selectedItem = self.jobTreeV.selection()
        jobID = self.jobTreeV.item(selectedItem)['values'][0]
        
        pos_dy = 67
        pos_dx = 47
        if spPath is not None:
            character_job_seg_tmp = []
            skillPosUsed = []
            skillIDList = []    #存放已经保存过的技能id
            skillTreeLeaf = self.get_leaf(spPath,list)
            character_job_seg_old = skillTreeLeaf.get('itemInList')[growTypeNo]
            for child in  self.growTypeSkillTreeV.get_children():
                skillID,skillName,skillPath = self.growTypeSkillTreeV.item(child)['values']
                if skillID in skillIDList:
                    continue
                skillIDList.append(skillID)
                skillLeaf = self.get_leaf(skillPath)
                skillInDict = skillLeaf.get('itemInDict')

                # 修正等级
                levtag = '[growtype maximum level]'
                growtype_maximum_level = skillInDict.get(levtag)
                growtype_maximum_level[growTypeNo] = max(growtype_maximum_level)
                skillInDict[levtag] = growtype_maximum_level

                levtag2 = '[second growtype maximum level]'
                growtype_maximum_level_2 = skillInDict.get(levtag2)
                if growtype_maximum_level_2 is not None:
                    growtype_maximum_level_2 = [max(growtype_maximum_level_2)] * len(growtype_maximum_level_2)
                    skillInDict[levtag2] = growtype_maximum_level_2
                # 去除前置
                reqTag = '[pre required skill]'
                if skillInDict.get(reqTag) is not None:
                    skillInDict.pop(reqTag)

                skillPos = self.posDict.get(jobID).get(skillID)
                while skillPos in skillPosUsed:
                    skillPos = [skillPos[0]+pos_dx,skillPos[1]]
                    if skillPos[0] > 470:
                        skillPos = [0,skillPos[1]+pos_dy]
                skillPosUsed.append(skillPos)
                skillInfoSeg = {'[skill info]':[{'[index]':[skillID]},{'[icon pos]':skillPos},True]}
                character_job_seg_tmp.append(skillInfoSeg)
                print(skillInfoSeg)
            character_job_seg = {'[character job]':character_job_seg_old.get('[character job]')[:2] + character_job_seg_tmp +[True]}
            skillTreeLeaf.get('itemInList')[growTypeNo] = character_job_seg
        
        self.update_Edited_Box()

        ...
    
    def add_skill(self,e=None):
        selectedItems = self.skillTreeV.selection()
        for selection in selectedItems:
            values = self.skillTreeV.item(selection)['values']
            item = self.growTypeSkillTreeV.insert('',tk.END,values=values)
            self.growTypeSkillTreeV.see(item)
        self.save_growtype_skill()


    def remove_skill(self,e=None):
        selectedItems = self.growTypeSkillTreeV.selection()
        for selection in selectedItems:
            self.growTypeSkillTreeV.delete(selection)
        self.save_growtype_skill()
        ...
    



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



if __name__ == "__main__":
    root = tk.Tk()
    widget = SkilleditframeWidget(root)
    widget.pack(expand=True, fill="both")
    root.mainloop()

