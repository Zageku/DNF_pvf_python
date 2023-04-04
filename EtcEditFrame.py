#!/usr/bin/python3
import tkinter as tk
import tkinter.ttk as ttk
#from pygubu.widgets.editabletreeview import EditableTreeview
from tkinter.ttk import Treeview as EditableTreeview
from pvfEditor import *

class EtcframeWidget(ttk.Frame):
    def __init__(self, master=None, **kw):
        super(EtcframeWidget, self).__init__(master, **kw)
        frame3 = ttk.Frame(self)
        frame3.configure(height=200, width=200)
        labelframe2 = ttk.Labelframe(frame3)
        labelframe2.configure(height=200, text='金币掉落修改-数值', width=200)
        label6 = ttk.Label(labelframe2)
        label6.configure(text='系数a')
        label6.grid(column=0, row=0)
        label7 = ttk.Label(labelframe2)
        label7.configure(text='系数b')
        label7.grid(column=0, row=1)
        label8 = ttk.Label(labelframe2)
        label8.configure(text='系数c')
        label8.grid(column=0, row=2)
        self.goldaE = ttk.Entry(labelframe2)
        self.goldaE.configure(width=8)
        self.goldaE.grid(column=1, row=0, sticky="ew")
        self.goldbE = ttk.Entry(labelframe2)
        self.goldbE.configure(width=8)
        self.goldbE.grid(column=1, row=1, sticky="ew")
        self.goldcE = ttk.Entry(labelframe2)
        self.goldcE.configure(width=8)
        self.goldcE.grid(column=1, row=2, sticky="ew")
        button2 = ttk.Button(labelframe2)
        button2.configure(text='计算数值')
        button2.grid(column=0, columnspan=2, row=4, sticky="ew")
        button2.configure(command=self.calculate_Gold)
        frame2 = ttk.Frame(labelframe2)
        frame2.configure(height=200, width=200)
        self.goldDropTreeV = EditableTreeview(frame2)
        self.goldDropTreeV.configure(
            height=6, selectmode="extended", show="headings")
        self.goldDropTreeV_cols = ['column1', 'column2', 'column3']
        self.goldDropTreeV_dcols = ['column1', 'column2', 'column3']
        self.goldDropTreeV.configure(
            columns=self.goldDropTreeV_cols,
            displaycolumns=self.goldDropTreeV_dcols)
        self.goldDropTreeV.column(
            "column1",
            anchor="center",
            stretch="true",
            width=40,
            minwidth=20)
        self.goldDropTreeV.column(
            "column2",
            anchor="center",
            stretch="true",
            width=80,
            minwidth=20)
        self.goldDropTreeV.column(
            "column3",
            anchor="center",
            stretch="true",
            width=50,
            minwidth=20)
        self.goldDropTreeV.heading("column1", anchor="center", text='等级')
        self.goldDropTreeV.heading("column2", anchor="center", text='金币数')
        self.goldDropTreeV.heading("column3", anchor="center", text='偏差')
        self.goldDropTreeV.pack(expand="true", fill="both", side="left")
        self.goldTreeBar = ttk.Scrollbar(frame2)
        self.goldTreeBar.configure(orient="vertical")
        self.goldTreeBar.pack(fill="y", side="right")
        frame2.grid(column=2, row=0, rowspan=6, sticky="nsew")
        label9 = ttk.Label(labelframe2)
        label9.configure(text='y=ax²+bx+c')
        label9.grid(column=0, columnspan=2, row=5)
        label15 = ttk.Label(labelframe2)
        label15.configure(text='偏差')
        label15.grid(column=0, row=3)
        self.goldDeltaE = ttk.Entry(labelframe2)
        self.goldDeltaE.configure(width=8)
        self.goldDeltaE.grid(column=1, row=3, sticky="ew")
        labelframe2.pack(expand="true", fill="both", side="left")
        labelframe2.columnconfigure(1, weight=1)
        labelframe2.columnconfigure(2, weight=2)
        self.labelframe3 = ttk.Labelframe(frame3)
        self.labelframe3.configure(height=200, text='副本掉落修改-百分比', width=200)
        label10 = ttk.Label(self.labelframe3)
        label10.configure(
            background="#808080",
            foreground="#ffffff",
            text='普通')
        label10.grid(column=0, row=1)
        label11 = ttk.Label(self.labelframe3)
        label11.configure(
            background="#0080ff",
            foreground="#ffffff",
            text='高级')
        label11.grid(column=0, row=2)
        label12 = ttk.Label(self.labelframe3)
        label12.configure(
            background="#8000ff",
            foreground="#ffffff",
            text='稀有')
        label12.grid(column=0, row=3)
        label13 = ttk.Label(self.labelframe3)
        label13.configure(
            background="#ff80ff",
            foreground="#ffffff",
            text='神器')
        label13.grid(column=0, row=4)
        label14 = ttk.Label(self.labelframe3)
        label14.configure(
            background="#ff8000",
            foreground="#ffffff",
            text='史诗')
        label14.grid(column=0, row=5)
        button3 = ttk.Button(self.labelframe3)
        button3.configure(text='归一化计算')
        button3.grid(column=0, columnspan=3, row=6, sticky="ew")
        button3.configure(command=self.calculate_Drop)
        label16 = ttk.Label(self.labelframe3)
        label16.configure(text='权值')
        label16.grid(column=1, row=0)
        self.dropE1 = ttk.Entry(self.labelframe3)
        self.dropE1.configure(width=8)
        self.dropE1.grid(column=1, row=1)
        self.dropE2 = ttk.Entry(self.labelframe3)
        self.dropE2.configure(width=8)
        self.dropE2.grid(column=1, row=2)
        self.dropE3 = ttk.Entry(self.labelframe3)
        self.dropE3.configure(width=8)
        self.dropE3.grid(column=1, row=3)
        self.dropE4 = ttk.Entry(self.labelframe3)
        self.dropE4.configure(width=8)
        self.dropE4.grid(column=1, row=4)
        self.dropE5 = ttk.Entry(self.labelframe3)
        self.dropE5.configure(width=8)
        self.dropE5.grid(column=1, row=5)
        label17 = ttk.Label(self.labelframe3)
        label17.configure(text='百分比')
        label17.grid(column=2, row=0)
        self.percentE1 = ttk.Entry(self.labelframe3)
        self.percentE1.configure(state="readonly", width=8)
        self.percentE1.grid(column=2, row=1)
        self.percentE2 = ttk.Entry(self.labelframe3)
        self.percentE2.configure(state="readonly", width=8)
        self.percentE2.grid(column=2, row=2)
        self.percentE3 = ttk.Entry(self.labelframe3)
        self.percentE3.configure(state="readonly", width=8)
        self.percentE3.grid(column=2, row=3)
        self.percentE4 = ttk.Entry(self.labelframe3)
        self.percentE4.configure(state="readonly", width=8)
        self.percentE4.grid(column=2, row=4)
        self.percentE5 = ttk.Entry(self.labelframe3)
        self.percentE5.configure(state="readonly", width=8)
        self.percentE5.grid(column=2, row=5)
        self.labelframe3.pack(fill="y", side="left")
        self.labelframe3.rowconfigure("all", weight=1)
        self.labelframe3.columnconfigure("all", weight=1)
        self.labelframe1 = ttk.Labelframe(frame3)
        self.labelframe1.configure(height=200, text='深渊掉落修改-百分比', width=200)
        label19 = ttk.Label(self.labelframe1)
        label19.configure(
            background="#808080",
            foreground="#ffffff",
            text='普通')
        label19.grid(column=0, row=1)
        label20 = ttk.Label(self.labelframe1)
        label20.configure(
            background="#0080ff",
            foreground="#ffffff",
            text='高级')
        label20.grid(column=0, row=2)
        label21 = ttk.Label(self.labelframe1)
        label21.configure(
            background="#8000ff",
            foreground="#ffffff",
            text='稀有')
        label21.grid(column=0, row=3)
        label22 = ttk.Label(self.labelframe1)
        label22.configure(
            background="#ff80ff",
            foreground="#ffffff",
            text='神器')
        label22.grid(column=0, row=4)
        label23 = ttk.Label(self.labelframe1)
        label23.configure(
            background="#ff8000",
            foreground="#ffffff",
            text='史诗')
        label23.grid(column=0, row=5)
        button4 = ttk.Button(self.labelframe1)
        button4.configure(text='归一化计算')
        button4.grid(column=0, columnspan=3, row=6, sticky="ew")
        button4.configure(command=self.calculate_Drop_Hell)
        label24 = ttk.Label(self.labelframe1)
        label24.configure(text='权值')
        label24.grid(column=1, row=0)
        self.dropHellE1 = ttk.Entry(self.labelframe1)
        self.dropHellE1.configure(width=8)
        self.dropHellE1.grid(column=1, row=1)
        self.dropHellE2 = ttk.Entry(self.labelframe1)
        self.dropHellE2.configure(width=8)
        self.dropHellE2.grid(column=1, row=2)
        self.dropHellE3 = ttk.Entry(self.labelframe1)
        self.dropHellE3.configure(width=8)
        self.dropHellE3.grid(column=1, row=3)
        self.dropHellE4 = ttk.Entry(self.labelframe1)
        self.dropHellE4.configure(width=8)
        self.dropHellE4.grid(column=1, row=4)
        self.dropHellE5 = ttk.Entry(self.labelframe1)
        self.dropHellE5.configure(width=8)
        self.dropHellE5.grid(column=1, row=5)
        label25 = ttk.Label(self.labelframe1)
        label25.configure(text='百分比')
        label25.grid(column=2, row=0)
        self.percentHellE1 = ttk.Entry(self.labelframe1)
        self.percentHellE1.configure(state="readonly", width=8)
        self.percentHellE1.grid(column=2, row=1)
        self.percentHellE2 = ttk.Entry(self.labelframe1)
        self.percentHellE2.configure(state="readonly", width=8)
        self.percentHellE2.grid(column=2, row=2)
        self.percentHellE3 = ttk.Entry(self.labelframe1)
        self.percentHellE3.configure(state="readonly", width=8)
        self.percentHellE3.grid(column=2, row=3)
        self.percentHellE4 = ttk.Entry(self.labelframe1)
        self.percentHellE4.configure(state="readonly", width=8)
        self.percentHellE4.grid(column=2, row=4)
        self.percentHellE5 = ttk.Entry(self.labelframe1)
        self.percentHellE5.configure(state="readonly", width=8)
        self.percentHellE5.grid(column=2, row=5)
        self.labelframe1.pack(fill="y", side="left")
        self.labelframe1.rowconfigure("all", weight=1)
        self.labelframe1.columnconfigure("all", weight=1)
        frame3.pack(fill="both", side="top")
        self.etcFileF = ttk.Frame(self)
        self.etcFileF.configure(height=200, width=200)
        self.labelframe6 = ttk.Labelframe(self.etcFileF)
        self.labelframe6.configure(height=200, text='已编辑文件列表', width=200)
        frame7 = ttk.Frame(self.labelframe6)
        frame7.configure(height=200, width=200)
        self.editedList = tk.Listbox(frame7)
        self.editedList.configure(height=15, width=30)
        self.editedList.pack(expand="true", fill="both", side="left")
        self.editedList.bind("<Button>", self.show_json, add="")
        self.editedList.bind("<Double-Button-1>", self.open_Edited_E, add="")
        self.scrollbar4 = ttk.Scrollbar(frame7)
        self.scrollbar4.configure(orient="vertical")
        self.scrollbar4.pack(fill="y", side="right")
        frame7.pack(expand="true", fill="both", side="top")
        frame8 = ttk.Frame(self.labelframe6)
        frame8.configure(height=200, width=200)
        button7 = ttk.Button(frame8)
        button7.configure(text='移除编辑')
        button7.pack(expand="true", fill="x", side="left")
        button7.configure(command=self.remove_Edited)
        frame8.pack(expand="true", fill="x", side="top")
        self.labelframe6.pack(expand="false", fill="both", side="left")
        self.picFrame = ttk.Frame(self.etcFileF)
        self.picFrame.configure(height=200, width=200)
        self.jsonViewE = tk.Text(self.picFrame)
        self.jsonViewE.configure(height=10, width=50)
        self.jsonViewE.pack(expand="true", fill="both", side="top")
        self.picFrame.pack(expand="true", fill="both", side="left")
        self.etcFileF.pack(expand="true", fill="both", side="top")
        self.configure(height=200, width=200)
        self.pack(expand="true", fill="both", side="top")



        self._other_build_function()
    
    def _other_build_function(self):
        self.leafType = 'etc'
        self.editLeafDict = {}
        self.log = print
        self.pvf:TinyPVFEditor = None
        self.goldDropTreeV.config(yscrollcommand=self.goldTreeBar.set)
        self.goldTreeBar.config(command=self.goldDropTreeV.yview)
        #self.etcFileBox.config(yscrollcommand=self.etcFileBar.set)
        #self.etcFileBar.config(command=self.etcFileBox.yview)
        #self.independDropBox.config(yscrollcommand=self.independDropBar.set)
        #self.independDropBar.config(command=self.independDropBox.yview)
        self.goldDropTreeV.insert('',tk.END,values=[1,2,3])
        self.dropEntryList = [
            self.dropE1,self.dropE2,self.dropE3,self.dropE4,self.dropE5
        ]
        self.dropPercentEntryList = [
            self.percentE1,self.percentE2,self.percentE3,self.percentE4,self.percentE5
        ]
        self.hellDropEntryList = [
            self.dropHellE1,self.dropHellE2,self.dropHellE3,self.dropHellE4,self.dropHellE5
        ]
        self.hellDropPercentEntryList = [
            self.percentHellE1,self.percentHellE2,self.percentHellE3,self.percentHellE4,self.percentHellE5
        ]
    
    def on_PVF_load(self):
        def get_etc_files():
            self.etcFileBox.delete(0, tk.END)
            filesList = []
            for filePath in  self.pvf.fileTreeDict.keys():
                if filePath[:4]=='etc/' and len(filePath.split('/'))==2:
                    filesList.append(filePath.split('/')[1])
            filesList.sort()
            for p in filesList:
                self.etcFileBox.insert(tk.END,p)
            return filesList
        def get_independDrop_files():
            self.independDropBox.delete(0, tk.END)
            filesList = []
            for filePath in  self.pvf.fileTreeDict.keys():
                if filePath[:19]=='etc/independentdrop' and len(filePath.split('/'))>2:
                    filesList.append(filePath.split('/',2)[-1])
            filesList.sort()
            for p in filesList:
                self.independDropBox.insert(tk.END,p)
            return filesList
        self.calculate_Gold_abcd()
        #self.etcFiles = get_etc_files()
        #self.independDropFiles = get_independDrop_files()
    
    def open_Edited_E(self,e):
        ...

    def update_Edited_Box(self):
        self.editedList.delete(0,tk.END)
        for filePath,leaf in self.editLeafDict.items():
            self.editedList.insert(tk.END,filePath)
            print(leaf)

    def get_leaf(self,filePath:str):
    
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

    def calculate_Gold_abcd(self):
        filePath = 'etc/itemdropinfo_common.etc'
        leaf = self.get_leaf(filePath)
        if leaf is None:
            return False
        itemInDict = leaf.get('itemInDict')
        goldSeg = itemInDict.get('[gold drop ref table]')
        if goldSeg is None:
            goldSeg = []
            for lev in range(1,201):
                goldSeg.extend([lev,0,0])
        valuesList = []
        for i in range(len(goldSeg)//3):
            valuesList.append(goldSeg[i*3:i*3+3])
        y100 = valuesList[99][1]
        y1 = valuesList[0][1]
        y50 = valuesList[49][1]
        a = ((y100-y1)/99 - (y50-y1)/49)/(101-2499/49)
        b = (y100-y1)/99 - 101*a
        c = y1-a-b
        delta = valuesList[0][2]
        self.goldaE.delete(0,tk.END)
        self.goldbE.delete(0,tk.END)
        self.goldcE.delete(0,tk.END)
        self.goldDeltaE.delete(0,tk.END)
        self.goldaE.insert(0,a)
        self.goldbE.insert(0,b)
        self.goldcE.insert(0,c)
        self.goldDeltaE.insert(0,delta)
        self.update_Gold_Tree(valuesList)

    def update_Gold_Tree(self,goldTable=[]):
        for child in self.goldDropTreeV.get_children():
            self.goldDropTreeV.delete(child)
        
        for values in goldTable:
            self.goldDropTreeV.insert('',tk.END,values=values)

    def calculate_Gold(self):
        a = float(self.goldaE.get())
        b = float(self.goldbE.get())
        c = float(self.goldcE.get())
        d = float(self.goldDeltaE.get())
        valuesList = []
        pvfSeg = []
        for x in range(1,201):
            values = [x,int(a*x*x+b*x+c),int(d)]
            valuesList.append(values)
            pvfSeg.extend(values)
        self.update_Gold_Tree(valuesList)
        filePath = 'etc/itemdropinfo_common.etc'
        leaf = self.get_leaf(filePath)
        leaf['itemInDict']['[gold drop ref table]'] = pvfSeg
        self.update_Edited_Box()

    def calculate_Drop(self):
        weightValues = []
        for entry in self.dropEntryList:
            string = entry.get()
            if string=='':
                string = '0'
            try:
                weightValues.append(float(string))
            except:
                self.log(f'[副本掉落]第{len(weightValues)+1}个参数错误')
                return False
        total = sum(weightValues)
        pvfSeg = []
        value = 0
        for weight in weightValues:
            value += int(weight/total * 100_0001)
            pvfSeg.append(value)
        pvfSeg[-1] = 100_0001
        pvfSeg.append(100_0002)
        #print(pvfSeg)
        pvfSeg = pvfSeg*4
        try:
            filePath_1 = 'etc/itemdropinfo_monseter.etc'
            leaf = self.get_leaf(filePath_1)
            leaf['itemInDict']['[basis of rarity dicision]'] = pvfSeg
            filePath_2 = 'etc/itemdropinfo_monseter_extra.etc'
            leaf = self.get_leaf(filePath_2)
            leaf['itemInDict']['[basis of rarity dicision]'] = pvfSeg
        except:
            self.log('PVF未加载')

        for i,entry in enumerate(self.dropPercentEntryList):
            entry.config(state='normal')
            entry.delete(0,tk.END)
            percent = weightValues[i]/total
            entry.insert(0,'%.4f' % (percent*100))
            entry.config(state='readonly')
        self.update_Edited_Box()
        
        

    def calculate_Drop_Hell(self):
        weightValues = []
        for entry in self.hellDropEntryList:
            string = entry.get()
            if string=='':
                string = '0'
            try:
                weightValues.append(float(string))
            except:
                self.log(f'[深渊掉落]第{len(weightValues)+1}个参数错误')
                return False
        total = sum(weightValues)
        pvfSeg = []
        value = 0
        for weight in weightValues:
            value += int(weight/total * 100_0001)
            pvfSeg.append(value)
        pvfSeg[-1] = 100_0001
        pvfSeg.append(100_0002)
        pvfSeg = [2] + pvfSeg*2
        print(pvfSeg)
        try:
            filePath_1 = 'etc/itemdropinfo_monster_hell.etc'
            leaf = self.get_leaf(filePath_1)
            leaf['itemInDict']['[basis of rarity dicision]'] = pvfSeg
        except:
            self.log('PVF未加载')

        for i,entry in enumerate(self.hellDropPercentEntryList):
            entry.config(state='normal')
            entry.delete(0,tk.END)
            percent = weightValues[i]/total
            entry.insert(0,'%.4f' % (percent*100))
            entry.config(state='readonly')
        
        self.update_Edited_Box()

    def open_ETC(self):
        print(self.etcFileBox.curselection())
        print(self.etcFiles[self.etcFileBox.curselection()])
        pass

    def remove_Edited(self):
        selPath = self.editedList.get(self.editedList.curselection())
        self.log(f'移除节点{selPath}')
        self.editLeafDict.pop(selPath)
        self.update_Edited_Box()

    def show_json(self,e):
        def func():
            selPath = self.editedList.get(self.editedList.curselection())
            leaf = self.get_leaf(selPath)
            #print(selPath,leaf)
            #print(leaf['itemInDict'])
            jsonString = json.dumps(leaf['itemInDict'], sort_keys=True, indent=4, separators=(',',':'))
            self.jsonViewE.delete("1.0",tk.END)
            self.jsonViewE.insert(tk.END,jsonString)
        self.after(100,func)

    def open_ETC_E(self,e):
        self.open_ETC()
        
    def open_IndepentDrop(self):
        pass
    def open_IndepentDrop_E(self,e):
        self.open_IndepentDrop()


if __name__ == "__main__":
    root = tk.Tk()
    widget = EtcframeWidget(root)
    widget.pack(expand=True, fill="both")
    widget.editLeafDict = {'asdas':{'itemInDict':{1:4231}},2:{'itemInDict':{'1':123}}}
    widget.update_Edited_Box()
    root.mainloop()

