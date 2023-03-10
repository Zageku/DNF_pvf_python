import cacheManager as cacheM
from titleBar import TitleBarFrame
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename
from toolTip import CreateToolTip
import time
import csv

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
rarityMapRev = {
    '普通':0,
    '高级':1,
    '稀有':2,
    '神器':3,
    '史诗':4,
    '勇者':5,
    '传说':6,
    '神话':7
}
equipmentForamted = {}  #格式化的装备字典
creatureEquipDict = {}  #存储所有宠物装备

class PVFCacheCfgFrame(TitleBarFrame):
    def __init__(self,master,saveFunc=lambda:...,closeFunc=lambda:...,*args,**kw):
        TitleBarFrame.__init__(self,master,master,title='PVF缓存编辑',closeFunc=closeFunc,*args,**kw)
        self.saveFunc = saveFunc    #保存时执行该函数

        frame = self.innerFrame
        #self.root.wm_attributes('-topmost', 1)
        tree = ttk.Treeview(frame, selectmode ='browse',height=3)
        self.tree = tree
        tree.grid(row=1,column=2,rowspan=5,sticky='ns',padx=5,pady=1)

        tree["columns"] = ("1", "2", "3")
        tree['show'] = 'headings'
        tree.column("1", width = 150, anchor ='c')
        tree.column("2", width = 150, anchor ='c')
        tree.column("3", width = 150, anchor ='c')
        tree.heading("1", text ="MD5")
        tree.heading("2", text ="别名")
        tree.heading("3", text ="路径")

        tree.bind('<ButtonRelease-1>',self.showCacheInfo)
        self.fillTree()

        editFrame = tk.Frame(frame)
        editFrame.grid(row=1,column=4,rowspan=5,sticky='nswe')
        row =1 
        kw = {
            'padx':3,
            'pady':3
        }

        tk.Label(editFrame,text='MD5:').grid(row=row,column=1,**kw)
        padFrame = tk.Frame(editFrame,width=200,height=0)
        padFrame.grid(row=row,column=2)
        MD5E = ttk.Entry(editFrame)
        MD5E.grid(row=row,column=2,sticky='we',**kw)
        row += 1
        tk.Label(editFrame,text='别名:').grid(row=row,column=1,**kw)
        nickNameE = ttk.Entry(editFrame)
        nickNameE.grid(row=row,column=2,sticky='we',**kw)
        row += 1
        tk.Label(editFrame,text='路径:').grid(row=row,column=1,**kw)
        pathE = ttk.Entry(editFrame)
        pathE.grid(row=row,column=2,sticky='we',**kw)
        row += 1
        tk.Label(editFrame,text='装备:').grid(row=row,column=1,**kw)
        equE = ttk.Entry(editFrame,width=14)
        equE.grid(row=row,column=2,sticky='w',**kw)
        ttk.Button(editFrame,text='导出',command=self.exportEqu).grid(row=row,column=2,sticky='e',padx=kw['padx'])
        row += 1
        tk.Label(editFrame,text='道具:').grid(row=row,column=1,**kw)
        stkE = ttk.Entry(editFrame,width=14)
        stkE.grid(row=row,column=2,sticky='w',**kw)
        ttk.Button(editFrame,text='导出',command=self.exportStk).grid(row=row,column=2,sticky='e',padx=kw['padx'])
        row +=1
        btnFrame = tk.Frame(editFrame)
        btnFrame.grid(row=row,column=1,columnspan=2)
        ttk.Button(btnFrame,text='保存',command=self.renameCache).grid(row=row,column=1,**kw)
        delBtn = ttk.Button(btnFrame,text='删除',command=self.delCache)
        delBtn.grid(row=row,column=2,**kw)
        CreateToolTip(delBtn,'从列表删除该条记录')

        self.MD5E = MD5E
        self.nickNameE = nickNameE
        self.pathE = pathE
        self.equE = equE
        self.stkE = stkE
    
    def fillTree(self):
        for child in self.tree.get_children():
            self.tree.delete(child)
        for MD5,infoDict in cacheM.cacheManager.tinyCache.items():
            if not isinstance(infoDict,dict):continue
            values = [MD5,infoDict.get('nickName'),infoDict.get('pvfPath')]
            self.tree.insert('',0,values=values)
    
    def renameCache(self):
        nickName = self.nickNameE.get()
        MD5 = self.MD5E.get()
        cacheM.cacheManager.renameCache(MD5,nickName)
        self.fillTree()
        #print('cacheFrame',cacheM.cacheManager.tinyCache)
        self.saveFunc()
    
    def delCache(self):
        if not messagebox.askokcancel('修改确认',f'确定当前所选缓存？'):
            return False
        MD5 = self.MD5E.get()
        cacheM.cacheManager.delCache(MD5)
        self.fillTree()
        self.saveFunc()
    
    def showCacheInfo(self,e:tk.Event):
        tree = self.tree
        try:
            MD5 = tree.item(tree.focus())['values'][0]
        except:
            return False
        #print(len(viewer.cacheManager[MD5]['stackable'].keys()),len(viewer.cacheManager[MD5]['equipment'].keys()))

        self.MD5E.config(state='normal')
        self.pathE.config(state='normal')
        self.equE.config(state='normal')
        self.stkE.config(state='normal')
        self.MD5E.delete(0,tk.END)
        self.nickNameE.delete(0,tk.END)
        self.pathE.delete(0,tk.END)
        self.equE.delete(0,tk.END)
        self.stkE.delete(0,tk.END)

        self.MD5E.insert(0,MD5)
        self.nickNameE.insert(0,str(cacheM.tinyCache[MD5].get('nickName')))
        self.pathE.insert(0,str(cacheM.tinyCache[MD5].get('pvfPath')))
        self.equE.insert(0,f'{cacheM.tinyCache[MD5]["equNum"]} 条记录')
        self.stkE.insert(0,f'{cacheM.tinyCache[MD5]["stkNum"]} 条记录')

        self.MD5E.config(state='readonly')
        self.pathE.config(state='readonly')
        self.equE.config(state='readonly')
        self.stkE.config(state='readonly')

    
    def exportEqu(self):
        MD5 = self.MD5E.get()
        fileType = 'csv'
        filePath = asksaveasfilename(title=f'保存文件(.{fileType})',filetypes=[('二进制文件',f'*.{fileType}')],initialfile=f'{self.nickNameE.get()}-装备.{fileType}')
        if filePath=='':
            return False
        if filePath[-1-len(fileType):]!= f'.{fileType}':
            filePath += f'.{fileType}'
        self.title_label.config(text='导出数据中...')
        time.sleep(0.05)
        self.root.wm_attributes('-topmost', 1)
        self.root.wm_attributes('-topmost', 0)
        equDict = cacheM.cacheManager[MD5]['equipment_formated']
        res = [['名称','ID','大类','小类','子类','等级','稀有度']]
        for type1,type2Dict in equDict.items():
            for type2,type3Dict in type2Dict.items():
                try:
                    tmp_key,tmp_value = type3Dict.popitem()
                except:
                    continue
                type3Dict[tmp_key] = tmp_value
                if not isinstance(tmp_value,dict):
                    type3Dict = {type2:type3Dict}
                for type3,equDictFin in type3Dict.items():
                    for id,name in equDictFin.items():
                        fileInDict = cacheM.get_Item_Info_In_Dict(id)
                        levInList = fileInDict.get('[minimum level]')
                        if levInList is not None:
                            lev = levInList[0]
                        else:
                            lev = 0
                        rarityInList = fileInDict.get('[rarity]')
                        if rarityInList is not None:
                            rarity = rarityMap.get(rarityInList[0])
                        else:
                            rarity = ''
                        if 'avatar' in str(fileInDict.keys()):
                            rarity += '时装'
                        
                        res.append([name,id,type1,type2,type3,lev,rarity])
        self.saveCSV(filePath,res)

    def exportStk(self):
        MD5 = self.MD5E.get()
        fileType = 'csv'
        filePath = asksaveasfilename(title=f'保存文件(.{fileType})',filetypes=[('二进制文件',f'*.{fileType}')],initialfile=f'{self.nickNameE.get()}-道具.{fileType}')
        if filePath=='':
            return False
        if filePath[-1-len(fileType):]!= f'.{fileType}':
            filePath += f'.{fileType}'
        self.title_label.config(text='导出数据中...')
        self.root.wm_attributes('-topmost', 1)
        self.root.wm_attributes('-topmost', 0)
        searchDict = cacheM.cacheManager[MD5].get('stackable')
        searchList = list(searchDict.items())
        res = [['名称','ID','原始种类','种类','使用等级','稀有度']]
        for itemID,name in searchList:
            fileInDict = cacheM.get_Item_Info_In_Dict(itemID)
            levInList = fileInDict.get('[minimum level]')
            if levInList is not None:
                lev = levInList[0]
            else:
                lev = 0
            rarityInList = fileInDict.get('[rarity]')
            if rarityInList is not None:
                rarity = rarityMap.get(rarityInList[0])
            else:
                rarity = ''
            typeInList = fileInDict.get('[stackable type]')
            if typeInList is not None:
                originType = typeInList[0][1:-1]
            else:
                originType = None

            resType = cacheM.typeDict.get(originType)
            if resType is not None:     #转换为中文，没有记录则显示原文
                resType = resType[1]
            else:
                resType = originType

            res.append([name.split('\n')[0],itemID,originType,resType,lev,rarity])
        self.saveCSV(filePath,res)

    def saveCSV(self,filePath,res):
        while True:
            try:
                with open(filePath,"w",errors='ignore',newline="") as csvfile: 
                    writer = csv.writer(csvfile)
                    writer.writerows(res)
                self.title_label.config(text=f'导出完成 {filePath}')
                self.root.wm_attributes('-topmost', 1)
                self.root.wm_attributes('-topmost', 0)
                return True
            except:
                if messagebox.askretrycancel('文件导出失败','请检查文件是否被占用，是否进行重试？'):
                    continue
                self.title_label.config(text=f'导出取消')
                return False

        








if __name__=='__main__':
    t = tk.Tk()
    t.overrideredirect(True)
    PVFCacheCfgFrame(t).pack(fill=tk.X,expand=1,anchor=tk.N)
    t.mainloop()

        