import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
if __name__=='__main__':
    import sys
    import os
    sys.path.append(os.getcwd())
import dnfpkgtool.cacheManager as cacheM
import dnfpkgtool.sqlManager2 as sqlM

class QuestframeWidget(ttk.Frame):
    def __init__(self, master=None,app=None, **kw):
        super(QuestframeWidget, self).__init__(master, **kw)
        labelframe1 = ttk.Labelframe(self)
        labelframe1.configure(height=200, text='当前任务列表', width=200)
        frame2 = ttk.Frame(labelframe1)
        frame2.configure(height=200, width=200)
        self.questTree = ttk.Treeview(frame2)
        self.questTree.configure(selectmode="extended", show="headings")
        self.questTree_cols = ['column4', 'column1', 'column2', 'column3']
        self.questTree_dcols = ['column4', 'column1', 'column2', 'column3']
        self.questTree.configure(
            columns=self.questTree_cols,
            displaycolumns=self.questTree_dcols)
        self.questTree.column(
            "column4",
            anchor="center",
            stretch="true",
            width=50,
            minwidth=20)
        self.questTree.column(
            "column1",
            anchor="center",
            stretch="true",
            width=100,
            minwidth=20)
        self.questTree.column(
            "column2",
            anchor="center",
            stretch="true",
            width=200,
            minwidth=20)
        self.questTree.column(
            "column3",
            anchor="center",
            stretch="true",
            width=60,
            minwidth=20)
        self.questTree.heading("column4", anchor="center", text=' ')
        self.questTree.heading("column1", anchor="center", text='任务ID')
        self.questTree.heading("column2", anchor="center", text='任务名')
        self.questTree.heading("column3", anchor="center", text='任务状态')
        self.questTree.pack(fill="both", side="left")
        self.questTree.bind("<<TreeviewSelect>>", self.show_sel_quest, add="")
        self.questBar = ttk.Scrollbar(frame2)
        self.questBar.configure(orient="vertical")
        self.questBar.pack(fill="y", side="right")
        frame2.pack(expand="true", fill="both", side="top")
        frame3 = ttk.Frame(labelframe1)
        frame3.configure(height=200, width=200)
        button2 = ttk.Button(frame3)
        button2.configure(text='放弃选中任务')
        button2.pack(expand="true", fill="x", side="left")
        button2.configure(command=self.give_up_sel_quest)
        button3 = ttk.Button(frame3)
        button3.configure(text='放弃所有任务')
        button3.pack(expand="true", fill="x", side="left")
        button3.configure(command=self.give_up_all_quest)
        button4 = ttk.Button(frame3)
        button4.configure(text='标记状态为完成')
        button4.pack(expand="true", fill="x", side="left")
        button4.configure(command=self.clear_sel_trigger)
        frame3.pack(fill="x", side="top")
        labelframe1.pack(fill="both", side="left")
        labelframe2 = ttk.Labelframe(self)
        labelframe2.configure(height=200, text='任务信息', width=200)
        frame4 = ttk.Frame(labelframe2)
        frame4.configure(height=200, width=200)
        label1 = ttk.Label(frame4)
        label1.configure(text='任务名：')
        label1.grid(column=0, row=0)
        self.questNameE = ttk.Combobox(frame4)
        self.questNameE.grid(column=1, row=0, sticky="ew")
        label2 = ttk.Label(frame4)
        label2.configure(text='ID：')
        label2.grid(column=0, row=1)
        self.questIDE = ttk.Combobox(frame4)
        self.questIDE.grid(column=1, row=1, sticky="ew")
        label3 = ttk.Label(frame4)
        label3.configure(text='任务状态：')
        label3.grid(column=0, row=2)
        self.questTrigerE = ttk.Combobox(frame4)
        self.questTrigerE.configure(values='0 1')
        self.questTrigerE.grid(column=1, row=2, sticky="ew")
        button5 = ttk.Button(frame4)
        button5.configure(text='保存状态')
        button5.grid(column=0, columnspan=2, row=3, sticky="ew")
        button5.configure(command=self.save_current_quest)
        frame4.pack(fill="x", side="top")
        frame4.columnconfigure(1, weight=1)
        self.questPvfE = tk.Text(labelframe2)
        self.questPvfE.configure(height=10, width=30)
        self.questPvfE.pack(expand="true", fill="both", side="top")
        labelframe2.pack(expand="true", fill="both", side="left")
        self.configure(height=200, width=200)
        self.pack(expand="true", fill="both", side="top")

        from dnfpkgtool.__main__ import GuiApp as App
        self.app:App = app

        self._build()

    def _build(self):
        self.questBar.configure(command=self.questTree.yview)
        self.questTree.configure(yscrollcommand=self.questBar.set)
        self.currentIndex = -1
        self.questDict = {}

        self.questNameE.bind('<Button-1>',self.search_Quest)
        self.questNameE.bind('<<ComboboxSelected>>',lambda e:self.readSlotName('name',self.questIDE,self.questNameE))
        self.questIDE.bind('<FocusOut>',lambda e:self.readSlotName('id',self.questIDE,self.questNameE))
        self.questIDE.bind('<Return>',lambda e:self.readSlotName('id',self.questIDE,self.questNameE))


    def search_Quest(self,e:tk.Event):
        '''搜索任务名'''
        if e.x<100:return
        key = self.questNameE.get()
        if len(key)>0:
            questList = [ [questID,questDict.get('[name]',[questID])[0]] for questID,questDict in cacheM.PVFcacheDict.get('quest',{}).items()]
            #print(questList[:10])
            res = cacheM.searchItem(key,questList)
            self.questNameE.config(values=[item[1]+' '+ str([item[0]]) for item in res])

    def readSlotName(self,name_id='id',itemIDEntry=None,itemNameEntry=None):
        if name_id=='id':
            id_ = itemIDEntry.get()
            try:
                id_ = int(id_)
            except:
                id_ = 0
            name = str(cacheM.get_quest_name(int(id_)))
        else:
            name,id_ = itemNameEntry.get().rsplit(' ',1)
            id_ = id_[1:-1]
            
        itemIDEntry.delete(0,tk.END)
        itemIDEntry.insert(0,id_)
        itemNameEntry.delete(0,tk.END)
        itemNameEntry.insert(0,name)
        itemNameEntry.config(values=[])
        questInfo = cacheM.get_Quest_Info_In_Text(int(id_))
        self.questPvfE.delete('1.0', tk.END)
        self.questPvfE.insert('1.0', questInfo)
        # see the end of the text
        self.questPvfE.see(tk.END)

    def load_quest(self):
        self.questTree.delete(*self.questTree.get_children())
        cNo = self.app.cNo
        questDict = sqlM.get_current_quest_dict(cNo)
        if questDict is None:
            return False
        self.questDict = questDict
        self.questTree.delete(*self.questTree.get_children())
        questList = questDict.get('questList', [])
        for i,questTuple in enumerate(questList):
            questID,questTrigger = questTuple
            questName = cacheM.get_quest_name(questID)
            values = [i,questID,questName,questTrigger]
            self.questTree.insert('', i, values=values)

    def show_sel_quest(self, event=None):
        sel = self.questTree.selection()[0]
        questIndex,questID,questName,questTrigger = self.questTree.item(sel, 'values')
        self.questNameE.set(questName)
        self.questIDE.set(questID)
        self.questTrigerE.set(questTrigger)
        self.currentIndex = int(questIndex)
        questInfo = cacheM.get_Quest_Info_In_Text(int(questID))
        self.questPvfE.delete('1.0', tk.END)
        self.questPvfE.insert('1.0', questInfo)
        self.questPvfE.see(tk.END)


    def give_up_sel_quest(self):
        if not messagebox.askokcancel('提示','是否要放弃选中的任务？'):
            return
        sels = self.questTree.selection()
        for sel in sels:
            questIndex,questID,questName,questTrigger = self.questTree.item(sel, 'values')
            self.questDict['questList'][int(questIndex)] = [0,0]
        sqlM.set_quest_dict(self.app.cNo, self.questDict)
        self.load_quest()

    def give_up_all_quest(self):
        if not messagebox.askokcancel('提示','是否要放弃所有任务？'):
            return
        self.questDict['questList'] = [[0,0]]*len(self.questDict['questList'])
        sqlM.set_quest_dict(self.app.cNo, self.questDict)
        self.load_quest()

    def clear_sel_trigger(self):
        if not messagebox.askokcancel('提示','是否要将选中的任务状态标记为完成？\n对于需要物品的任务，请手动发送物品邮件。'):
            return
        sels = self.questTree.selection()
        for sel in sels:
            questIndex,questID,questName,questTrigger = self.questTree.item(sel, 'values')
            self.questDict['questList'][int(questIndex)] = [questID,0]
        sqlM.set_quest_dict(self.app.cNo, self.questDict)
        self.load_quest()

    def save_current_quest(self):
        if self.currentIndex<0:
            return
        questName = self.questNameE.get()
        questID = self.questIDE.get()
        questTrigger = self.questTrigerE.get()
        self.questDict['questList'][self.currentIndex] = [questID,questTrigger]
        sqlM.set_quest_dict(self.app.cNo, self.questDict)
        self.load_quest()


if __name__ == "__main__":
    root = tk.Tk()
    widget = QuestframeWidget(root)
    widget.pack(expand=True, fill="both")
    root.mainloop()

