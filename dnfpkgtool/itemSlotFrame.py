
import tkinter as tk
import tkinter.ttk as ttk
import pyperclip
import pickle
if not hasattr(ttk,'Spinbox'):
    class Spinbox(ttk.Entry):
        def __init__(self, master=None, **kw):  #from_=0,to=99,
            ttk.Entry.__init__(self, master, "ttk::spinbox", **kw)
        def set(self, value):
            self.tk.call(self._w, "set", value)
    ttk.Spinbox = Spinbox



class ItemslotframeWidget(tk.Frame):
    def __init__(self, master=None, **kw):
        super(ItemslotframeWidget, self).__init__(master, **kw)
        self.invBowserFrame = tk.LabelFrame(self)
        self.invBowserFrame.configure(height=200, text='当前物品列表', width=200)
        frame2 = ttk.Frame(self.invBowserFrame)
        frame2.configure(height=200, width=200)
        self.filterFrame = ttk.Frame(frame2)
        self.filterFrame.configure(height=200, width=200)
        self.showEmptyBtn = ttk.Checkbutton(self.filterFrame)
        self.emptySlotVar = tk.IntVar()
        self.showEmptyBtn.configure(text='显示空槽位', variable=self.emptySlotVar)
        self.showEmptyBtn.pack(padx=5, side="left")
        self.typeBoxE = ttk.Combobox(self.filterFrame)
        self.typeBoxE.configure(width=15)
        self.typeBoxE.pack(padx=5, side="right")
        self.inv_capacityL = ttk.Label(self.filterFrame)
        self.inv_capacityL.configure(text='槽位扩充：')
        self.inv_capacityL.pack(side="left")
        self.inv_capacityE = ttk.Combobox(self.filterFrame)
        self.inv_capacityE.configure(
            state="readonly", values='0 8 16', width=4)
        self.inv_capacityE.pack(side="left")
        self.inv_capacityE.bind(
            "<<ComboboxSelected>>",
            self.set_inv_capacity,
            add="")
        self.filterFrame.pack(fill="x", pady=3, side="top")
        self.treeViewFrame = ttk.Frame(frame2)
        self.treeViewFrame.configure(height=200, width=200)
        self.itemsTreev_now = ttk.Treeview(self.treeViewFrame)
        self.itemsTreev_now.configure(selectmode="extended", show="headings")
        self.itemsTreev_now_cols = [
            'column1',
            'column2',
            'column5',
            'column6',
            'column3']
        self.itemsTreev_now_dcols = [
            'column1', 'column2', 'column5', 'column6', 'column3']
        self.itemsTreev_now.configure(
            columns=self.itemsTreev_now_cols,
            displaycolumns=self.itemsTreev_now_dcols)
        self.itemsTreev_now.column(
            "column1",
            anchor="center",
            stretch=True,
            width=40,
            minwidth=20)
        self.itemsTreev_now.column(
            "column2",
            anchor="center",
            stretch=True,
            width=120,
            minwidth=20)
        self.itemsTreev_now.column(
            "column5",
            anchor="center",
            stretch=True,
            width=60,
            minwidth=20)
        self.itemsTreev_now.column(
            "column6",
            anchor="center",
            stretch=True,
            width=80,
            minwidth=20)
        self.itemsTreev_now.column(
            "column3",
            anchor="center",
            stretch=True,
            width=50,
            minwidth=20)
        self.itemsTreev_now.heading("column1", anchor="center", text=' ')
        self.itemsTreev_now.heading("column2", anchor="center", text='物品名')
        self.itemsTreev_now.heading("column5", anchor="center", text='数量')
        self.itemsTreev_now.heading("column6", anchor="center", text='物品ID')
        self.itemsTreev_now.heading("column3", anchor="center", text='稀有度')
        self.itemsTreev_now.pack(expand=True, fill="both", side="left")
        self.itemsTreev_bar = ttk.Scrollbar(self.treeViewFrame)
        self.itemsTreev_bar.configure(orient="vertical")
        self.itemsTreev_bar.pack(fill="y", side="right")
        self.treeViewFrame.pack(expand=True, fill="both", side="top")
        self.blobFuncFrame = ttk.Frame(frame2)
        self.blobFuncFrame.configure(height=200, width=200)
        self.clearBtn = ttk.Button(self.blobFuncFrame)
        self.clearBtn.configure(text='清空物品')
        self.clearBtn.pack(expand=True, fill="x", side="left")
        self.exportBtn = ttk.Button(self.blobFuncFrame)
        self.exportBtn.configure(text='导出字段')
        self.exportBtn.pack(expand=True, fill="x", side="left")
        self.importBtn = ttk.Button(self.blobFuncFrame)
        self.importBtn.configure(text='导入字段')
        self.importBtn.pack(expand=True, fill="x", side="left")
        self.blobFuncFrame.pack(fill="x", side="top")
        frame2.pack(expand=True, fill="both", side="top")
        self.invBowserFrame.pack(expand=True, fill="both", side="left")
        self.itemEditFrame = tk.LabelFrame(self)
        self.itemEditFrame.configure(height=200, text='物品信息编辑', width=400)
        frame3 = ttk.Frame(self.itemEditFrame)
        frame3.configure(height=200, width=200)
        self.itemBasicInfoFrame = ttk.Frame(frame3)
        self.itemBasicInfoFrame.configure(height=200, width=200)
        self.itemSealBtn = ttk.Checkbutton(self.itemBasicInfoFrame)
        self.itemSealVar = tk.IntVar()
        self.itemSealBtn.configure(text='封装', variable=self.itemSealVar)
        self.itemSealBtn.grid(column=0, pady=1, row=0)
        self.itemNameEntry = ttk.Combobox(self.itemBasicInfoFrame)
        self.itemNameEntry.configure(width=12)
        self.itemNameEntry.grid(
            column=1,
            columnspan=2,
            pady=1,
            row=0,
            sticky="ew")
        self.itemNameEntry.bind(
            "<<ComboboxSelected>>",
            self.readSlotName,
            add="")
        self.itemNameEntry.bind("<Button-1>", self.searchItem, add="")
        self.itemIDEntry = ttk.Entry(self.itemBasicInfoFrame)
        self.itemIDEntry.configure(width=10)
        self.itemIDEntry.grid(
            column=1,
            columnspan=1,
            pady=1,
            row=1,
            sticky="ew")
        self.itemIDEntry.bind("<FocusOut>", self.readSlotID, add="")
        self.numGradeLabel = ttk.Label(self.itemBasicInfoFrame)
        self.numGradeLabel.configure(text='数量：')
        self.numGradeLabel.grid(column=0, pady=1, row=2)
        label2 = ttk.Label(self.itemBasicInfoFrame)
        label2.configure(text='增幅：')
        label2.grid(column=0, pady=1, row=3)
        label3 = ttk.Label(self.itemBasicInfoFrame)
        label3.configure(text='强化：')
        label3.grid(column=0, pady=1, row=4)
        label4 = ttk.Label(self.itemBasicInfoFrame)
        label4.configure(text='锻造：')
        label4.grid(column=2, padx=3, row=4, sticky="w")
        self.numEntry = ttk.Spinbox(self.itemBasicInfoFrame)
        self.numEntry.configure(from_=0, to=999999999999, width=16)
        self.numEntry.grid(column=1, pady=1, row=2, sticky="ew")
        label5 = ttk.Label(self.itemBasicInfoFrame)
        label5.configure(text='耐久：')
        label5.grid(column=2, padx=3, row=2, sticky="w")
        self.durabilityEntry = ttk.Spinbox(self.itemBasicInfoFrame)
        self.durabilityEntry.configure(from_=0, to=9999, width=4)
        self.durabilityEntry.grid(column=2, padx=1, pady=1, row=2, sticky="e")
        self.IncreaseTypeEntry = ttk.Combobox(self.itemBasicInfoFrame)
        self.IncreaseTypeEntry.configure(width=12)
        self.IncreaseTypeEntry.grid(column=1, pady=1, row=3, sticky="ew")
        self.EnhanceEntry = ttk.Spinbox(self.itemBasicInfoFrame)
        self.EnhanceEntry.configure(from_=0, to=999, width=16)
        self.EnhanceEntry.grid(column=1, pady=1, row=4, sticky="ew")
        self.forgingEntry = ttk.Spinbox(self.itemBasicInfoFrame)
        self.forgingEntry.configure(from_=0, to=999, width=4)
        self.forgingEntry.grid(column=2, pady=1, row=4, sticky="e")
        self.IncreaseEntry = ttk.Spinbox(self.itemBasicInfoFrame)
        self.IncreaseEntry.configure(width=12)
        self.IncreaseEntry.grid(column=2, padx=1, pady=1, row=3, sticky="ew")
        self.enableTypeBtn = ttk.Checkbutton(self.itemBasicInfoFrame)
        self.enableTypeChangeVar = tk.IntVar()
        self.enableTypeBtn.configure(
            text='启用种类字段', variable=self.enableTypeChangeVar)
        self.enableTypeBtn.grid(
            column=0,
            columnspan=2,
            padx=3,
            row=6,
            sticky="w")
        self.enableTypeBtn.configure(command=self.enableTestFrame)
        label6 = ttk.Label(self.itemBasicInfoFrame)
        label6.configure(text='种类：')
        label6.grid(column=0, columnspan=2, row=6, sticky="e")
        self.typeEntry = ttk.Combobox(self.itemBasicInfoFrame)
        self.typeEntry.configure(width=8)
        self.typeEntry.grid(column=2, padx=1, row=6, sticky="ew")
        self.typeEntry.bind(
            "<<ComboboxSelected>>",
            self.changeItemSlotType,
            add="")
        self.itemIDLabel = ttk.Label(self.itemBasicInfoFrame)
        self.itemIDLabel.configure(text='ID：')
        self.itemIDLabel.grid(column=0, pady=1, row=1)
        label10 = ttk.Label(self.itemBasicInfoFrame)
        label10.configure(text='封装次数：')
        label10.grid(column=2, padx=3, row=1, sticky="w")
        self.sealCountE = ttk.Spinbox(self.itemBasicInfoFrame)
        self.sealCountE.configure(from_=0, to=7, width=4)
        self.sealCountE.grid(column=2, padx=1, pady=1, row=1, sticky="e")
        self.itemBasicInfoFrame.pack(expand=False, fill="x", side="top")
        self.itemBasicInfoFrame.columnconfigure(0, pad=3)
        self.itemBasicInfoFrame.columnconfigure(1, weight=2)
        self.itemBasicInfoFrame.columnconfigure(2, weight=1)
        self.itemBasicInfoFrame.columnconfigure("all", pad=3)
        self.equipmentExFrame = ttk.Frame(frame3)
        self.equipmentExFrame.configure(height=200, width=200)
        frame9 = ttk.Frame(self.equipmentExFrame)
        frame9.configure(height=200, width=200)
        label7 = ttk.Label(frame9)
        label7.configure(text='异界')
        label7.pack(padx=3, side="left")
        self.otherworldEntry = ttk.Entry(frame9)
        self.otherworldEntry.pack(expand=True, fill="x", padx=1, side="left")
        frame9.pack(fill="x", pady=1, side="top")
        frame10 = ttk.Frame(self.equipmentExFrame)
        frame10.configure(height=200, width=200)
        label8 = ttk.Label(frame10)
        label8.configure(text='宝珠')
        label8.pack(padx=3, side="left")
        self.orbTypeEntry = ttk.Combobox(frame10)
        self.orbTypeEntry.configure(width=8)
        self.orbTypeEntry.pack(expand=True, fill="x", padx=1, side="left")
        self.orbTypeEntry.bind(
            "<<ComboboxSelected>>",
            self.setOrbTypeCom,
            add="")
        self.orbValueEntry = ttk.Combobox(frame10)
        self.orbValueEntry.configure(width=8)
        self.orbValueEntry.pack(expand=True, fill="x", padx=1, side="left")
        self.orbValueEntry.bind(
            "<<ComboboxSelected>>",
            self.setOrbValueCom,
            add="")
        self.orbEntry = ttk.Entry(frame10)
        self.orbEntry.configure(width=8)
        self.orbEntry.pack(expand=False, fill="x", padx=1, side="left")
        self.orbEntry.bind("<FocusOut>", self.changeOrbByID, add="")
        frame10.pack(fill="x", pady=1, side="top")
        frame11 = ttk.Frame(self.equipmentExFrame)
        frame11.configure(height=200, width=200)
        label9 = ttk.Label(frame11)
        label9.configure(text='魔法封印：')
        label9.pack(padx=3, side="left")
        self.forth = ttk.Checkbutton(frame11)
        self.forthSealEnable = tk.IntVar()
        self.forth.configure(text='第四词条', variable=self.forthSealEnable)
        self.forth.pack(padx=3, side="right")
        frame11.pack(fill="x", pady=3, side="top")
        frame12 = ttk.Frame(self.equipmentExFrame)
        frame12.configure(height=200, width=200)
        frame13 = ttk.Frame(frame12)
        frame13.configure(height=200, width=200)
        self.magicSealEntry = ttk.Combobox(frame13)
        self.magicSealEntry.pack(expand=True, fill="x", padx=1, side="left")
        self.magicSealEntry.bind(
            "<<ComboboxSelected>>",
            self.setMagicSeal,
            add="")
        self.magicSealEntry.bind("<Button-1>", self.searchMagicSeal, add="")
        self.magicSealIDEntry = ttk.Entry(frame13)
        self.magicSealIDEntry.configure(width=8)
        self.magicSealIDEntry.pack(padx=1, side="left")
        self.magicSealLevelEntry = ttk.Entry(frame13)
        self.magicSealLevelEntry.configure(width=8)
        self.magicSealLevelEntry.pack(padx=1, side="left")
        frame13.pack(fill="x", pady=1, side="top")
        frame14 = ttk.Frame(frame12)
        frame14.configure(height=200, width=200)
        self.magicSealEntry1 = ttk.Combobox(frame14)
        self.magicSealEntry1.pack(expand=True, fill="x", padx=1, side="left")
        self.magicSealEntry1.bind(
            "<<ComboboxSelected>>",
            self.setMagicSeal,
            add="")
        self.magicSealEntry1.bind("<Button-1>", self.searchMagicSeal, add="")
        self.magicSealIDEntry1 = ttk.Entry(frame14)
        self.magicSealIDEntry1.configure(width=8)
        self.magicSealIDEntry1.pack(padx=1, side="left")
        self.magicSealLevelEntry1 = ttk.Entry(frame14)
        self.magicSealLevelEntry1.configure(width=8)
        self.magicSealLevelEntry1.pack(padx=1, side="left")
        frame14.pack(fill="x", pady=1, side="top")
        frame15 = ttk.Frame(frame12)
        frame15.configure(height=200, width=200)
        self.magicSealEntry2 = ttk.Combobox(frame15)
        self.magicSealEntry2.pack(expand=True, fill="x", padx=1, side="left")
        self.magicSealEntry2.bind(
            "<<ComboboxSelected>>",
            self.setMagicSeal,
            add="")
        self.magicSealEntry2.bind("<Button-1>", self.searchMagicSeal, add="")
        self.magicSealIDEntry2 = ttk.Entry(frame15)
        self.magicSealIDEntry2.configure(width=8)
        self.magicSealIDEntry2.pack(padx=1, side="left")
        self.magicSealLevelEntry2 = ttk.Entry(frame15)
        self.magicSealLevelEntry2.configure(width=8)
        self.magicSealLevelEntry2.pack(padx=1, side="left")
        frame15.pack(fill="x", pady=1, side="top")
        frame16 = ttk.Frame(frame12)
        frame16.configure(height=200, width=200)
        self.magicSealEntry3 = ttk.Combobox(frame16)
        self.magicSealEntry3.pack(expand=True, fill="x", padx=1, side="left")
        self.magicSealEntry3.bind(
            "<<ComboboxSelected>>",
            self.setMagicSeal,
            add="")
        self.magicSealEntry3.bind("<Button-1>", self.searchMagicSeal, add="")
        self.magicSealIDEntry3 = ttk.Entry(frame16)
        self.magicSealIDEntry3.configure(width=8)
        self.magicSealIDEntry3.pack(padx=1, side="left")
        self.magicSealLevelEntry3 = ttk.Entry(frame16)
        self.magicSealLevelEntry3.configure(width=8)
        self.magicSealLevelEntry3.pack(padx=1, side="left")
        frame16.pack(fill="x", pady=1, side="top")
        frame12.pack(fill="x", side="top")
        self.equipmentExFrame.pack(fill="x", padx=2, side="top")
        frame3.pack(expand=True, fill="both", side="top")
        self.btnFrame = ttk.Frame(self.itemEditFrame)
        self.btnFrame.configure(height=200, width=200)
        self.itemSlotBytesE = ttk.Entry(self.btnFrame)
        self.itemSlotBytesE.configure(width=10)
        self.itemSlotBytesE.grid(column=0, padx=3, row=0, sticky="ew")
        self.genBytesBtn = ttk.Button(self.btnFrame)
        self.genBytesBtn.configure(text='生成字节', width=8)
        self.genBytesBtn.grid(column=1, row=0, sticky="ew")
        self.genBytesBtn.configure(command=self.genBytes)
        self.importBytesBtn = ttk.Button(self.btnFrame)
        self.importBytesBtn.configure(text='导入字节', width=8)
        self.importBytesBtn.grid(column=2, row=0, sticky="ew")
        self.importBytesBtn.configure(command=self.readBytes)
        self.delBtn = ttk.Button(self.btnFrame)
        self.delBtn.configure(text='删除')
        self.delBtn.grid(column=0, row=1, sticky="ew")
        self.delBtn.configure(command=self.setDelete)
        self.resetBtn = ttk.Button(self.btnFrame)
        self.resetBtn.configure(text='重置')
        self.resetBtn.grid(column=1, row=1, sticky="ew")
        self.resetBtn.configure(command=self.reset)
        self.commitBtn = ttk.Button(self.btnFrame)
        self.commitBtn.configure(text='提交修改', width=8)
        self.commitBtn.grid(column=2, row=1, sticky="ew")
        self.commitBtn.configure(command=self.ask_commit)
        self.btnFrame.pack(fill="x", side="bottom")
        self.btnFrame.columnconfigure("all", weight=1)
        label1 = ttk.Label(self.itemEditFrame)
        self.currentEditLabelVar = tk.StringVar(value='(0)')
        label1.configure(text='(0)', textvariable=self.currentEditLabelVar)
        label1.place(anchor="se", relx=0.99, x=0, y=0)
        self.itemEditFrame.pack(expand=False, fill="y", side="left")
        self.configure(height=200, width=200)
        self.pack(expand=True, fill="both", side="top")

    def set_inv_capacity(self, event=None):
        pass

    def readSlotName(self, event=None):
        pass

    def searchItem(self, event=None):
        pass

    def readSlotID(self, event=None):
        pass

    def setDelete(self):
        pass

    def reset(self):
        pass

    def enableTestFrame(self):
        pass

    def changeItemSlotType(self, event=None):
        pass

    def setOrbTypeCom(self, event=None):
        pass

    def setOrbValueCom(self, event=None):
        pass

    def changeOrbByID(self, event=None):
        pass

    def setMagicSeal(self, event=None):
        pass

    def searchMagicSeal(self, event=None):
        pass

    def genBytes(self):
        pass

    def readBytes(self):
        pass

    def ask_commit(self):
        pass

if __name__ == "__main__":
    root = tk.Tk()
    import ctypes
    #告诉操作系统使用程序自身的dpi适配
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    #获取屏幕的缩放因子
    ScaleFactor=ctypes.windll.shcore.GetScaleFactorForDevice(0)
    #设置程序缩放
    root.tk.call('tk', 'scaling', ScaleFactor/75)
    widget = ItemslotframeWidget(root)
    widget.pack(expand=True, fill="both")
    root.mainloop()

