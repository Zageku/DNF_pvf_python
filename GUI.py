import viewerCMD as viewer
from viewerCMD import config
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename
import threading
from pathlib import Path
import time
from copy import deepcopy
import struct
from toolTip import CreateToolTip
from zhconv import convert
import json
DEBUG = True
VerInfo = 'Ver.0.2.16'
logPath = Path('./log')
if not logPath.exists():
    logPath.mkdir()
tm = time.localtime()
LOGFile = f'./log/{"%02d" % tm.tm_mon}-{"%02d" % tm.tm_mday} {"%02d" % tm.tm_hour}_{"%02d" % tm.tm_min}_{"%02d" % tm.tm_sec}.log'

def log(text):
    tm = time.localtime()
    with open(LOGFile,'a+',encoding='utf-8') as f:
        log = f'[{"%02d" % tm.tm_mon}-{"%02d" % tm.tm_mday} {"%02d" % tm.tm_hour}:{"%02d" % tm.tm_min}:{"%02d" % tm.tm_sec}] {text}\n'
        f.write(log)



globalBlobs_map = {
        '物品栏':'inventory',
        '穿戴栏':'equipslot',
        '宠物栏':'creature',
        '仓库':'cargo'
    }
globalNonBlobs_map = {
    '宠物':'creature_items',
    '时装':'user_items'
    
    }


class App():
    def __init__(self):
        w = tk.Tk()
        def fixed_map(option):
            # Fix for setting text colour for Tkinter 8.6.9
            # From: https://core.tcl.tk/tk/info/509cafafae
            #
            # Returns the style map for 'option' with any styles starting with
            # ('!disabled', '!selected', ...) filtered out.

            # style.map() returns an empty list for missing options, so this
            # should be future-safe.
            return [elm for elm in style.map('Treeview', query_opt=option) if
            elm[:2] != ('!disabled', '!selected')]
        style = ttk.Style()
        style.map('Treeview', foreground=fixed_map('foreground'),
        background=fixed_map('background'))

        style = ttk.Style()
        self.w = w
        self.titleLog = lambda text:[w.title(text),log(text)]
        w.iconbitmap('ico.ico')
        
        self.CONNECT_FLG = False #判断正在连接
        self.PVF_LOAD_FLG = False #判断正在加载pvf
        self.currentItemDict = {}
        self.editedItemsDict = {}
        self.itemInfoClrFuncs = {}
        self.buildGUI(self.w)
    
    def _buildSqlConn(self,mainFrame):
        #数据库连接
        db_conFrame = tk.Frame(mainFrame)
        tk.Label(db_conFrame,text='  数据库IP ').grid(row=0,column=1)
        db_ip = ttk.Entry(db_conFrame,width=15)
        db_ip.grid(row=0,column=2,pady=5)
        db_ip.insert(0,config['DB_IP'])
        tk.Label(db_conFrame,text='  端口 ').grid(row=0,column=3)
        db_port = ttk.Entry(db_conFrame,width=8)
        db_port.insert(0,config['DB_PORT'])
        db_port.grid(row=0,column=4)
        tk.Label(db_conFrame,text='  用户名 ').grid(row=0,column=5)
        db_user = ttk.Entry(db_conFrame,width=8)
        db_user.insert(0,config['DB_USER'])
        db_user.grid(row=0,column=6)
        tk.Label(db_conFrame,text='  密码 ').grid(row=0,column=7)
        db_pwd = ttk.Entry(db_conFrame,width=8,show='*')
        db_pwd.insert(0,config['DB_PWD'])
        db_pwd.grid(row=0,column=8)
        db_conBTN = ttk.Button(db_conFrame,text='连接',command=self.connectSQL)
        db_conBTN.grid(row=0,column=9,padx=15,pady=5)
        
        ttk.Separator(db_conFrame, orient='horizontal').grid(row=1,column=0,columnspan=10,sticky='we')
        db_conFrame.pack(fill='x')
        self.db_ip = db_ip
        self.db_port = db_port
        self.db_user = db_user
        self.db_pwd = db_pwd
        self.db_conBTN = db_conBTN


    def _buildtab_main(self,tabView):
        def searchCharac(type='account'):   #或者cName
            if type=='account':
                characs = viewer.getCharactorInfo(uid=viewer.getUID(self.accountE.get()))
                
            else:
                characs = viewer.getCharactorInfo(name=self.characE.get())
            log(characs)
            for child in self.characTreev.get_children():
                self.characTreev.delete(child)
            for values in characs:
                self.characTreev.insert('',tk.END,values=values)

        def selectCharac(showTitle=False):
            sel = self.characTreev.item(self.characTreev.focus())['values']
            try:
                cNo, name, level = sel
            except:
                print(f'选择为空[{sel}]')
                return False
            if self.PVF_LOAD_FLG and self.itemSourceSel.get()==1:
                self.titleLog('等待PVF加载中')
                return False
            if len(viewer.ITEMS_dict.keys())<10:
                self.titleLog(f'请选择物品列表来源')
                return False
            log(f'加载角色物品[{sel}]')
            inventory, equipslot, creature = viewer.getInventoryAll(cNo=cNo)[0]
            cargo,jewel,expand_equipslot = viewer.getCargoAll(cNo=cNo)[0]
            creature_items = viewer.getCreatureItem(cNo=cNo)
            user_items = viewer.getAvatar(cNo=cNo)
            if showTitle:
                self.titleLog(f'角色[{name}]物品已加载')
            else:
                log(f'角色[{name}]物品已加载')
            self.enableTabs()
            globalBlobs = {
                '物品栏':inventory,
                '穿戴栏':equipslot,
                '宠物栏':creature,
                '仓库':cargo
            }
            globalNonBlobItems = {'宠物':creature_items,'时装':user_items}
            globalCharacItemsDict = {}
            for key in self.editedItemsDict.keys():
                self.editedItemsDict[key] = {}    #清空编辑的对象
            # 物品列表插入新的节点
            for tabName,currentTabBlob in globalBlobs.items():
                CharacItemsList = []
                itemsTreev_now = self.itemsTreevs_now[tabName]
                for child in itemsTreev_now.get_children():
                    itemsTreev_now.delete(child)
                
                CharacItemsList = viewer.unpackBLOB_Item(currentTabBlob)
                CharacItemsDict = {}
                self.currentItemDict = {}
                for values in CharacItemsList:
                    index, dnfItemSlot = values
                    name = str(viewer.ITEMS_dict.get(dnfItemSlot.id))
                    if dnfItemSlot.typeZh in ['装备'] and dnfItemSlot.enhancementLevel>0:
                        name = f'+{dnfItemSlot.enhancementLevel} ' + name
                    if dnfItemSlot.typeZh in ['消耗品','材料','任务材料','宠物消耗品','副职业']:
                        num = dnfItemSlot.num_grade
                    else:
                        num = 1
                    values_unpack = [index,name,num,dnfItemSlot.id]
                    itemsTreev_now.insert('',tk.END,values=values_unpack)
                    CharacItemsDict[index] = dnfItemSlot
                globalCharacItemsDict[tabName] = CharacItemsDict
                self.itemInfoClrFuncs[tabName]()    #清除物品信息显示

            for tabName,currentTabItems in globalNonBlobItems.items():
                itemsTreev_now = self.itemsTreevs_now[tabName]
                itemsTreev_del = self.itemsTreevs_del[tabName]
                for child in itemsTreev_now.get_children():
                    itemsTreev_now.delete(child)
                for child in itemsTreev_del.get_children():
                    itemsTreev_del.delete(child)
                CharacNoneBlobItemsDict = {}
                for values in currentTabItems:
                    itemsTreev_now.insert('',tk.END,values=values)
                    CharacNoneBlobItemsDict[values[0]] = values
                globalCharacItemsDict[tabName] = CharacNoneBlobItemsDict
            self.globalCharacBlobs = globalBlobs
            #self.globalNonBlobItems = globalNonBlobItems
            self.cNo = cNo
            self.globalCharacItemsDict = globalCharacItemsDict
        
        def setItemSource(sourceVar:tk.IntVar,pvfPath:str='',pvfMD5=0):
            '''设置物品来源，读取pvf或者csv'''
            if pvfMD5!=0:
                sourceVar.set(1)
            source = sourceVar.get()
            self.disableTabs()
            if source==1 and not self.PVF_LOAD_FLG:
                if pvfMD5!=0:
                    self.titleLog('加载PVF缓存中...')
                    
                    self.PVF_LOAD_FLG = True
                    info = viewer.loadItems2(True,showFunc=self.titleLog,MD5=pvfMD5)
                    self.PVF_LOAD_FLG = False
                    self.titleLog(f'{info}...{pvfMD5}')
                    if '错误' in info:
                        sourceVar.set(0)
                    else:
                        pvfComboBox.set(pvfMD5)
                else:
                    if pvfPath=='':
                        pvfPath = askopenfilename(filetypes=[('DNF Script.pvf file','*.pvf')])
                    p = Path(pvfPath)
                    if p.exists():
                        self.titleLog('加载PVF中...')
                        self.PVF_LOAD_FLG = True
                        info = viewer.loadItems2(True,pvfPath,self.titleLog)
                        self.PVF_LOAD_FLG = False
                        pvfComboBox.set('使用pvf文件')
                        if sourceVar.get()==1:
                            self.titleLog(info)
                        else:
                            viewer.loadItems2(False)
                            self.titleLog('PVF加载完成，请选择使用')
                            
                            
                            return True
                    else:
                        self.titleLog('PVF路径错误，加载CSV')
                        time.sleep(1)
                        source = 0
                        sourceVar.set(0)
                    pvfComboBox.config(values=list(viewer.PVFcacheDicts.keys()))
                selectCharac()
            if source==1 and self.PVF_LOAD_FLG:
                self.titleLog('等待PVF加载')
            if source==0:
                info = viewer.loadItems2(False)
                self.titleLog(info)
                selectCharac()

        #账号查询功能
        self.selectCharac = selectCharac
        searchFrame = tk.Frame(tabView)
        searchFrame.pack(expand=True)
        tabView.add(searchFrame,text=' 查询 ')
        tabView.pack(expand=True, fill=tk.BOTH,padx=5,pady=5)

        accountSearchFrame = tk.LabelFrame(searchFrame,text='账户查询')
        accountE = ttk.Entry(accountSearchFrame,width=12)
        accountE.pack(padx=5,pady=5)
        accountBtn = ttk.Button(accountSearchFrame,text='查询',command=lambda:searchCharac('account'))
        accountBtn.pack(padx=5,pady=5)
        accountSearchFrame.grid(column=1,row=1,padx=5,pady=5,sticky='w')

        characSearchFrame = tk.LabelFrame(searchFrame,text='角色查询')
        characE = ttk.Entry(characSearchFrame,width=12)
        characE.pack(padx=5,pady=5)
        characBtn = ttk.Button(characSearchFrame,text='查询',command=lambda:searchCharac('cName'))
        characBtn.pack(padx=5,pady=5)
        characSearchFrame.grid(column=1,row=2,padx=5,pady=5,sticky='w')
        
        #角色选择列表
        characTreev = ttk.Treeview(searchFrame, selectmode ='browse',height=13)
        characTreev.grid(row=1,column=2,rowspan=2,sticky='we',padx=5,pady=5)

        characTreev["columns"] = ("1", "2", "3")
        characTreev['show'] = 'headings'
        characTreev.column("1", width = 90, anchor ='c')
        characTreev.column("2", width = 120, anchor ='se')
        characTreev.column("3", width = 90, anchor ='se')

        characTreev.heading("1", text ="全局编号")
        characTreev.heading("2", text ="角色名")
        characTreev.heading("3", text ="等级")
        characTreev.bind('<ButtonRelease-1>',selectCharac)

        # 信息显示及logo，物品源选择
        infoFrame = tk.Frame(searchFrame)
        infoFrame.grid(row=1,column=3,rowspan=2,sticky='n')
        PVFSelFrame = tk.LabelFrame(infoFrame,text='物品来源')
        PVFSelFrame.pack(fill='x',padx=5,pady=30)
        itemSourceSel = tk.IntVar()
        p = Path(config['PVF_PATH'])
        if p.exists():
            itemSourceSel.set(1)
        def selSourceThread(pvfPath=''):
            def inner():
                if pvfPath=='' or '.pvf' in pvfPath.lower():
                    setItemSource(itemSourceSel,pvfPath)
                else:
                    setItemSource(itemSourceSel,pvfMD5=pvfPath)
            t = threading.Thread(target=inner)
            t.daemon = True
            t.start()
        def setPVF(e):
            selSourceThread(pvfComboBox.get())

        selSourceThread(config['PVF_PATH'])
        ttk.Radiobutton(PVFSelFrame,variable=itemSourceSel,value=0,text='CSV文件',command=selSourceThread).pack(anchor='w',padx=45,pady=5)
        ttk.Radiobutton(PVFSelFrame,variable=itemSourceSel,value=1,text='PVF文件',command=selSourceThread).pack(anchor='w',padx=45,pady=5)
        pvfComboBox = ttk.Combobox(PVFSelFrame,values=list(viewer.PVFcacheDicts.keys()),width=10)
        pvfComboBox.set('请选择PVF缓存')
        pvfComboBox.pack(anchor='w',padx=20,pady=5,fill='x')
        pvfComboBox.bind("<<ComboboxSelected>>",setPVF)
        CreateToolTip(pvfComboBox,'PVF缓存')

        tk.Label(infoFrame,text='背包编辑工具',font=('TkDefaultFont',17)).pack()
        tk.Label(infoFrame,text=VerInfo,font=('TkDefaultFont',17)).pack()
        tk.Label(infoFrame,text='台服dnf吧',font=('TkDefaultFont',28)).pack(pady=5)
        self.accountE = accountE
        self.characE = characE
        self.characTreev = characTreev
        self.itemSourceSel = itemSourceSel
    
    def _buildtab_itemTab(self,tabView,tabName,treeViewArgs):
        def ask_commit():
            showSelectedItemInfo()
            if not messagebox.askokcancel('修改确认',f'确定修改{tabName}所选物品？\n请确认账号不在线或正在使用其他角色\n{self.editedItemsDict[tabName]}'):
                return False
            cNo = self.cNo
            key = globalBlobs_map[tabName]
            originblob = self.globalCharacBlobs[tabName]
            viewer.commit_change_blob(originblob,self.editedItemsDict[tabName],cNo,key)
            self.titleLog(f'====修改成功==== {tabName} {self.editedItemsDict[tabName]}')
            return self.selectCharac()
        def setTreeViev(itemsTreev,doubleFunc=lambda e:...,singleFunc=lambda e:...):
            itemsTreev['columns'] = treeViewArgs['columns']
            itemsTreev['show'] = treeViewArgs['show']
            for columnID in treeViewArgs['columns']:
                itemsTreev.column(columnID,**treeViewArgs['column'][columnID])
                itemsTreev.heading(columnID,**treeViewArgs['heading'][columnID])
            itemsTreev.bind('<Double-1>',doubleFunc)
            itemsTreev.bind("<Button-1>", lambda e:self.w.after(100,singleFunc))

        def changeItemSlotType(e=None):
            typeZh = typeEntry.get().split('-')[1]
            #print(viewer.config['TEST_ENABLE'])
            if typeZh in ['装备']:
                numGradeLabel.config(text='品级：')
                for widget in itemEditFrame.children:
                    try:
                        itemEditFrame.children[widget].config(state='normal')
                    except:
                        pass
                for widget in testFrame.children:
                    try:
                        testFrame.children[widget].config(state='normal' if viewer.config.get('TEST_ENABLE') == 1 else 'readonly')
                    except:
                        pass
            else:
                
                for widget in itemEditFrame.children:
                    try:
                        itemEditFrame.children[widget].config(state='disable')
                    except:
                        pass
                for widget in testFrame.children:
                    try:
                        testFrame.children[widget].config(state='disable')
                    except:
                        pass
                numGradeLabel.config(state='normal',text='数量：')
                numEntry.config(state='normal')
                itemIDEntry.config(state='normal')
                itemNameEntry.config(state='normal')
                delBtn.config(state='normal')
                resetBtn.config(state='normal')
                typeEntry.config(state='normal')
            
        def updateItemEditFrame(itemSlot:viewer.DnfItemSlot):
            for widget in itemEditFrame.children:
                try:
                    itemEditFrame.children[widget].config(state='normal')
                except:
                    pass
            for widget in testFrame.children:
                try:
                    testFrame.children[widget].config(state='normal')
                except:
                    pass
            itemIDEntry.delete(0,tk.END)
            itemNameEntry.delete(0,tk.END)
            numEntry.delete(0,tk.END)
            durabilityEntry.delete(0,tk.END)
            EnhanceEntry.delete(0,tk.END)
            IncreaseEntry.delete(0,tk.END)
            IncreaseTypeEntry.delete(0,tk.END)
            forgingEntry.delete(0,tk.END)
            otherworldEntry.delete(0,tk.END)
            orbEntry.delete(0,tk.END)
            magicSealEntry.delete(0,tk.END)
            magicSealEntry_1.delete(0,tk.END)
            magicSealEntry_2.delete(0,tk.END)
            magicSealEntry_3.delete(0,tk.END)
            typeEntry.delete(0,tk.END)


            itemSealVar.set(itemSlot.isSeal)
            itemIDEntry.insert(0,itemSlot.id)
            durabilityEntry.insert(0,itemSlot.durability)
            itemNameEntry.insert(0,str(viewer.ITEMS_dict.get(itemSlot.id)))
            numEntry.insert(0,itemSlot.num_grade)
            EnhanceEntry.insert(0,itemSlot.enhancementLevel)
            forgingEntry.insert(0,itemSlot.forgeLevel)
            otherworldEntry.insert(0,itemSlot.otherworld.hex())
            orbEntry.insert(0,itemSlot.orb_bytes.hex())
            magicSealEntry.insert(0,itemSlot.magicSeal.hex()[:6])
            magicSealEntry_1.insert(0,itemSlot.magicSeal.hex()[6:12])
            magicSealEntry_2.insert(0,itemSlot.magicSeal.hex()[12:18])
            magicSealEntry_3.insert(0,itemSlot.magicSeal.hex()[18:])
            IncreaseEntry.insert(0,itemSlot.increaseValue)
            IncreaseTypeEntry.set(itemSlot.increaseTypeZh)
            typeEntry.set(str(itemSlot.type)+'-'+itemSlot.typeZh)
            #enableTestVar.set(0)
            changeItemSlotType()

        def clear_item_Edit_Frame():
            itemIDEntry.delete(0,tk.END)
            itemNameEntry.delete(0,tk.END)
            numEntry.delete(0,tk.END)
            durabilityEntry.delete(0,tk.END)
            EnhanceEntry.delete(0,tk.END)
            IncreaseEntry.delete(0,tk.END)
            IncreaseTypeEntry.delete(0,tk.END)
            forgingEntry.delete(0,tk.END)
            otherworldEntry.delete(0,tk.END)
            orbEntry.delete(0,tk.END)
            magicSealEntry.delete(0,tk.END)
            magicSealEntry_1.delete(0,tk.END)
            magicSealEntry_2.delete(0,tk.END)
            magicSealEntry_3.delete(0,tk.END)

        def showItemInfo():
            try:
                itemID = int(itemIDEntry.get())
            except:
                return None
            segType,segments = viewer.getItemInfo(itemID)
            res = ' '.join([str(item).strip() for item in segments]).replace('[','\n[').replace(']',']\n    ').replace('     \n','').replace(r'%%',r'%').replace(r'\n\n',r'\n').strip()
            try:
                res = convert(res,'zh-cn')
            except:
                pass
            return res
            

        def showSelectedItemInfo(save=True):
            itemsTreev:ttk.Treeview=itemsTreev_now
            if save:    #除重置外均会被保存
                if self.currentItemDict.get(tabName) is not None and editSave()==True:
                    print('物品被编辑保存',self.editedItemsDict)
                    index,*_ = self.currentItemDict.get(tabName)
                    itemSlot:viewer.DnfItemSlot = self.editedItemsDict[tabName][index]
                    if itemSlot.id==0:
                        tag = 'deleted'
                    else: 
                        tag = 'edited'
                    itemsTreev.item(self.currentItemDict[tabName][2],tags=tag)
                elif self.currentItemDict.get(tabName) is not None:
                    itemsTreev.item(self.currentItemDict[tabName][2],tags='')

            
            values = itemsTreev.item(itemsTreev.focus())['values']
            index = values[0]
            if save and self.editedItemsDict.get(tabName).get(values[0]) is not None:
                itemSlot:viewer.DnfItemSlot = self.editedItemsDict.get(tabName).get(values[0])
            else:
                itemSlot:viewer.DnfItemSlot = self.globalCharacItemsDict[tabName][values[0]]
            updateItemEditFrame(itemSlot)
            #print(itemSlot.oriBytes)
            #log(itemSlot)
            self.w.title(itemSlot)
            self.currentItemDict[tabName] = [index,itemSlot,itemsTreev.focus()]
        
        '''FIXME:物品栏编辑'''
        def searchItem(e:tk.Event):
            if e.x<100:return
            key = itemNameEntry.get()
            if len(key)>0:
                res = viewer.searchItem(key)
                itemNameEntry.config(values=[str([item[0]])+' '+item[1] for item in res])
        def readSlotName(name_id='id'):
            if name_id=='id':
                id_ = itemIDEntry.get()
                try:
                    id_ = int(id_)
                except:
                    id_ = 0
                print(id_)
                #itemNameEntry.config(value=viewer.ITEMS_dict.get(id_))
                name = str(viewer.ITEMS_dict.get(int(id_)))
            else:
                id_,name = itemNameEntry.get().split(' ',1)
                id_ = id_[1:-1]
                print(itemNameEntry.get(),id_)
            itemIDEntry.delete(0,tk.END)
            itemIDEntry.insert(0,id_)
            itemNameEntry.delete(0,tk.END)
            itemNameEntry.insert(0,name)
            itemNameEntry.config(values=[])

        def reset():
            showSelectedItemInfo(save=False)

        def setDelete():
            itemSlot = viewer.DnfItemSlot(b'')
            updateItemEditFrame(itemSlot)

        def editSave():
            '''保存编辑信息'''
            def str2bytes(s)->bytes:
                i = 0
                length = len(s)
                nums = []
                while i<length:
                    nums.append(int(s[i:i+2],base=16))
                    i+=2
                return struct.pack('B'*len(nums),*nums)
            if self.currentItemDict.get(tabName) is None:
                return False
            try:
                index,itemSlot_,*_ = self.currentItemDict.get(tabName)
                itemSlot:viewer.DnfItemSlot = deepcopy(itemSlot_)
                itemSlot.id = int(itemIDEntry.get())
                itemSlot.isSeal = itemSealVar.get()
                itemSlot.num_grade = int(numEntry.get())
                itemSlot.durability = int(durabilityEntry.get())
                itemSlot.enhancementLevel= int(EnhanceEntry.get())
                itemSlot.forgeLevel = int(forgingEntry.get())
                itemSlot.increaseType = int(IncreaseTypeEntry.get().split('-')[-1])
                itemSlot.increaseValue = int(IncreaseEntry.get())
                itemSlot.type = int(typeEntry.get().split('-')[0])
                #if enableTestVar.get() == 1:
                orb = str2bytes(orbEntry.get().replace(' ',''))
                if len(itemSlot.orb_bytes) == len(orb):
                    itemSlot.orb_bytes = orb
                otherworld = str2bytes(otherworldEntry.get().replace(' ',''))
                if len(itemSlot.otherworld)==len(otherworld):
                    itemSlot.otherworld = otherworld
                magicNew = magicSealEntry.get() + magicSealEntry_1.get() + magicSealEntry_2.get() + magicSealEntry_3.get()
                magicSeal = str2bytes(magicNew.replace(' ',''))
                if len(itemSlot.magicSeal)==len(magicSeal):
                    itemSlot.magicSeal = magicSeal
                gridBytes = itemSlot.build_bytes()
                if gridBytes!= self.globalCharacItemsDict[tabName][index].oriBytes:
                    self.editedItemsDict[tabName][index] = itemSlot
                    return True
                else:
                    if index in self.editedItemsDict[tabName].keys():
                        self.editedItemsDict[tabName].pop(index)
                    return False
            except Exception as e:
                self.titleLog(e)





        self.editedItemsDict[tabName] = {}
        self.itemInfoClrFuncs[tabName] = clear_item_Edit_Frame
        
        inventoryFrame = tk.Frame(tabView)
        inventoryFrame.pack(expand=True)
        tabView.add(inventoryFrame,text=tabName)
        allInventoryFrame = tk.LabelFrame(inventoryFrame,text='当前物品列表')
        allInventoryFrame.grid(row=1,column=1,rowspan=2,sticky='ns')
        itemsTreev_now = ttk.Treeview(allInventoryFrame, selectmode ='browse',height=12)
        itemsTreev_now.pack(fill='both',padx=5)
        itemsTreev_now.tag_configure('edited', background='lightblue')
        itemsTreev_now.tag_configure('deleted', background='gray')
        self.itemsTreevs_now[tabName] = itemsTreev_now

        

        setTreeViev(itemsTreev_now,singleFunc=showSelectedItemInfo)


        itemEditFrame = tk.LabelFrame(inventoryFrame,text='物品信息编辑')
        itemEditFrame.grid(row=1,column=2,sticky='nswe')
        padx = 3
        pady = 1
        # 2
        row = 2
        itemSealVar = tk.IntVar()
        itemSealVar.set(1)
        itemSealBtn = ttk.Checkbutton(itemEditFrame,text='封装',variable=itemSealVar,command=lambda:print(itemSealVar.get()))
        itemSealBtn.grid(column=1,row=row,padx=padx,pady=pady)
        CreateToolTip(itemSealBtn,'无法封装的物品勾选会炸角色')
        itemNameEntry = ttk.Combobox(itemEditFrame,width=14,state='normal')
        itemNameEntry.bind('<Button-1>',searchItem)
        itemNameEntry.grid(column=2,row=row,sticky='we',padx=padx,pady=pady)
        itemNameEntry.bind("<<ComboboxSelected>>",lambda e:readSlotName('name'))
        CreateToolTip(itemNameEntry,textFunc=showItemInfo)
        itemIDEntry = ttk.Entry(itemEditFrame,width=10)
        itemIDEntry.grid(column=3,row=row,sticky='we',padx=padx,pady=pady)
        itemIDEntry.bind('<FocusOut>',lambda e:readSlotName('id'))
        itemIDEntry.bind('<Return>',lambda e:readSlotName('id'))
        # 3
        row = 3
        numGradeLabel = tk.Label(itemEditFrame,text='数量：')
        numGradeLabel.grid(column=1,row=row,padx=padx,pady=pady)
        numEntry = ttk.Spinbox(itemEditFrame,width=15,from_=0, to=2147483647)
        numEntry.grid(column=2,row=row,sticky='we',padx=padx,pady=pady)
        CreateToolTip(numEntry,'当为装备时，表示为品级\n数值与品级关系较为随机\n(0~2,147,483,647)')
        tk.Label(itemEditFrame,text=' 耐久：').grid(column=3,row=row,sticky='w',padx=padx,pady=pady)
        durabilityEntry = ttk.Spinbox(itemEditFrame,width=4,from_=0, to=999)
        durabilityEntry.grid(column=3,row=row,sticky='e',padx=padx,pady=pady)
        # 4
        row = 4
        tk.Label(itemEditFrame,text='增幅：').grid(column=1,row=row,padx=padx,pady=pady)
        IncreaseTypeEntry = ttk.Combobox(itemEditFrame,width=14,state='readonly',values=['空-0','异次元体力-1','异次元精神-2','异次元力量-3','异次元智力-4'])
        IncreaseTypeEntry.grid(column=2,row=row,sticky='we',padx=padx,pady=pady)
        IncreaseEntry = ttk.Spinbox(itemEditFrame,width=10,from_=0, to=65535)
        IncreaseEntry.grid(column=3,row=row,sticky='we',padx=padx,pady=pady)
        
        # 5
        row = 5
        tk.Label(itemEditFrame,text='强化：').grid(column=1,row=row,padx=padx,pady=pady)
        EnhanceEntry = ttk.Spinbox(itemEditFrame,width=15,increment=1,from_=0, to=31)
        EnhanceEntry.grid(column=2,row=row,sticky='we',padx=padx,pady=pady)
        delBtn = ttk.Button(itemEditFrame,text=' 删除 ',command=setDelete)
        CreateToolTip(delBtn,'标记当前物品为待删除物品')
        delBtn.grid(row=row,column=3,pady=pady)
        # 6
        row = 6
        tk.Label(itemEditFrame,text='锻造：').grid(column=1,row=row,padx=padx,pady=pady)
        forgingEntry = ttk.Spinbox(itemEditFrame,width=15,increment=1,from_=0, to=31)
        forgingEntry.grid(column=2,row=row,sticky='we',padx=padx,pady=pady)
        resetBtn = ttk.Button(itemEditFrame,text=' 重置 ',command=reset)
        resetBtn.grid(row=row,column=3,pady=pady)
        # 7 
        def enableTestFrame():
            viewer.config['TEST_ENABLE'] = enableTestVar.get()
            print(viewer.config)
            json.dump(viewer.config,open(viewer.configPath,'w'))
            for widget in testFrame.children:
                try:
                    testFrame.children[widget].config(state='normal' if enableTestVar.get() == 1 else 'readonly')
                except:
                    pass
                
        row = 7
        enableTestVar = tk.IntVar()
        enableTestVar.set(viewer.config.get('TEST_ENABLE'))
        enableTestBtn = ttk.Checkbutton(itemEditFrame,text=' 启用测试字段',variable=enableTestVar,command=enableTestFrame)
        enableTestBtn.grid(column=1,row=row,columnspan=2,sticky='w',padx=padx,pady=pady)
        tk.Label(itemEditFrame,text='种类:').grid(column=1,row=row,columnspan=2,sticky='e',padx=padx,pady=pady)
        typeEntry = ttk.Combobox(itemEditFrame,width=4,state='readonly',values=['1-装备','2-消耗品','3-材料','4-任务材料','5-宠物','6-宠物装备','7-宠物消耗品','10-副职业'])
        typeEntry.grid(column=3,row=row,sticky='we',padx=padx,pady=pady)
        typeEntry.bind('<<ComboboxSelected>>',changeItemSlotType)
        CreateToolTip(typeEntry,'与物品及位置编号对应，否则炸角色')
        # 8 
        row = 8
        testFrame = tk.Frame(itemEditFrame)
        testFrame.grid(column=1,row=row,columnspan=3,sticky='we',padx=padx,pady=pady)
        # 8-1
        padx = 1
        row = 1
        tk.Label(testFrame,text='异界气息：').grid(column=1,row=row,padx=padx,pady=pady)
        otherworldEntry = ttk.Entry(testFrame,state='readonly',width=30)
        otherworldEntry.grid(column=2,row=row,columnspan=4,sticky='we',padx=padx,pady=pady)
        # 8-2
        row = 2
        tk.Label(testFrame,text=' 宝  珠：').grid(column=1,row=row,padx=padx,pady=pady)
        orbEntry = ttk.Entry(testFrame,state='readonly')
        orbEntry.grid(column=2,row=row,columnspan=4,sticky='we',padx=padx,pady=pady)
        # 8-3
        row = 3
        tk.Label(testFrame,text='魔法封印：').grid(column=1,row=row,padx=padx,pady=pady)
        #magicSealFrame = tk.Frame(testFrame)
        #magicSealFrame.grid(column=2,row=row,columnspan=2,sticky='we',padx=padx,pady=pady)

        magicSealEntryWidth = 7
        magicSealEntry = ttk.Entry(testFrame,state='readonly',width=magicSealEntryWidth)
        magicSealEntry.grid(column=2,row=row,sticky='we',padx=padx,pady=pady)
        magicSealEntry_1 = ttk.Entry(testFrame,state='readonly',width=magicSealEntryWidth)
        magicSealEntry_1.grid(column=3,row=row,sticky='we',padx=padx,pady=pady)
        magicSealEntry_2 = ttk.Entry(testFrame,state='readonly',width=magicSealEntryWidth)
        magicSealEntry_2.grid(column=4,row=row,sticky='we',padx=padx,pady=pady)
        magicSealEntry_3 = ttk.Entry(testFrame,state='readonly',width=8)
        magicSealEntry_3.grid(column=5,row=row,sticky='we',padx=padx,pady=pady)


        
        btnFrame = tk.Frame(inventoryFrame)
        btnFrame.grid(row=2,column=2)
        commitBtn = ttk.Button(btnFrame,text='提交修改',command=ask_commit)
        commitBtn.grid(row=2,column=2,pady=5)
        CreateToolTip(commitBtn,f'提交当前[{tabName}]页面的所有修改')

    def _buildtab_itemTab_2(self,tabView,tabName,treeViewArgs):
        def addDel(itemsTreev_now,itemsTreev_del:ttk.Treeview):
            '''添加到删除列表'''
            values = itemsTreev_now.item(itemsTreev_now.focus())['values']
            item = itemsTreev_del.insert('',tk.END,values=values)
            #itemsTreev_del.yview_moveto(1)
            itemsTreev_del.see(item)
        def removeDel(itemsTreev_del):
            '''从删除列表移除'''
            itemsTreev_del.delete(itemsTreev_del.focus())
        
        def deleteItems(tabName,itemsTreev_del:ttk.Treeview):
            if not messagebox.askokcancel('删除确认',f'确定删除{tabName}所选物品？'):
                return False
            deleteIDs = []
            for child in itemsTreev_del.get_children():
                log(itemsTreev_del.item(child))
                deleteIDs.append(itemsTreev_del.item(child)['values'][0])
            if tabName in globalBlobs_map.keys():
                log('删除BLOB')
                key = globalBlobs_map[tabName]
                blob = self.globalCharacBlobs[tabName]
                InventoryBlob_new = viewer.buildDeletedBlob2(deleteIDs,blob)
                if viewer.setInventory(InventoryBlob_new,self.cNo,key):
                    self.w.title('====删除成功====\n')
                else:
                    self.titleLog('====删除失败，请检查数据库连接状况====\n')
            if tabName in globalNonBlobs_map.keys():
                log('删除非BLOB')
                tableName = globalNonBlobs_map[tabName]
                for ui_id in deleteIDs:
                    if viewer.delNoneBlobItem(ui_id,tableName):
                        self.titleLog('====删除成功====\n')
                    else:
                        self.titleLog('====删除失败，请检查数据库连接状况====\n')
            self.selectCharac()
        def setTreeViev(itemsTreev,doubleFunc=lambda e:...,singleFunc=lambda e:...):
            itemsTreev['columns'] = treeViewArgs['columns']
            itemsTreev['show'] = treeViewArgs['show']
            for columnID in treeViewArgs['columns']:
                itemsTreev.column(columnID,**treeViewArgs['column'][columnID])
                itemsTreev.heading(columnID,**treeViewArgs['heading'][columnID])
            itemsTreev.bind('<Double-1>',doubleFunc)
            itemsTreev.bind("<Button-1>",singleFunc)


        inventoryFrame = tk.Frame(tabView)
        inventoryFrame.pack(expand=True)
        tabView.add(inventoryFrame,text=tabName)
        allInventoryFrame = tk.LabelFrame(inventoryFrame,text='当前物品列表')
        allInventoryFrame.grid(row=1,column=1)
        itemsTreev_now = ttk.Treeview(allInventoryFrame, selectmode ='browse', height=12)
        itemsTreev_now.grid(row=1,column=2,rowspan=2,columnspan=2,sticky='nswe',padx=5)
        self.itemsTreevs_now[tabName] = itemsTreev_now

        delInventoryFrame = tk.LabelFrame(inventoryFrame,text='待删除物品列表')
        delInventoryFrame.grid(row=1,column=2,sticky='ns')
        itemsTreev_del = ttk.Treeview(delInventoryFrame, selectmode ='browse', height=10)
        itemsTreev_del.grid(row=1,column=2,rowspan=2,columnspan=2,sticky='nswe',padx=5)
        self.itemsTreevs_del[tabName] = itemsTreev_del

        setTreeViev(itemsTreev_now,lambda e:addDel(itemsTreev_now,itemsTreev_del),lambda e:self.w.title('双击添加至删除列表'))
        setTreeViev(itemsTreev_del,lambda e:removeDel(itemsTreev_del),lambda e:self.w.title('双击从删除列表移除'))

        def reselect(tabName):
            itemsTreev_del = self.itemsTreevs_del[tabName] 
            for child in itemsTreev_del.get_children():
                itemsTreev_del.delete(child)
        resetBtn = ttk.Button(delInventoryFrame,text=' 重选 ',command=lambda:reselect(tabName))
        resetBtn.grid(row=3,column=2,pady=5)
        delBtn = ttk.Button(delInventoryFrame,text='确定删除',command=lambda:deleteItems(tabName,itemsTreev_del))
        delBtn.grid(row=3,column=3,pady=5)

    def buildGUI(self,w):
        mainFrame = tk.Frame(w)
        mainFrame.pack(fill='both')
        self.mainFrame = mainFrame
        self._buildSqlConn(mainFrame)

        tabView = ttk.Notebook(mainFrame)
        self.tabView = tabView
        self._buildtab_main(tabView)

        self.itemsTreevs_now = {}
        self.itemsTreevs_del = {}

        treeViewArgs = {
            "columns":['1','2','3','4'],
            'show':'headings',
            'column':{
                '1':{'width':30, 'anchor':'c'},
                '2':{'width':130, 'anchor':'se'},
                '3':{'width':40, 'anchor':'se'},
                '4':{'width':70, 'anchor':'se'},
                },
            'heading':{
                '1':{'text':' '},
                '2':{'text':'物品名'},
                '3':{'text':'数量'},
                '4':{'text':'物品ID'},
            }
        }
        tabNames = globalBlobs_map.keys()
        for tabName in tabNames:
            self._buildtab_itemTab(tabView,tabName,treeViewArgs)
        treeViewArgs = {
            "columns":['1','2','3','4'],
            'show':'headings',
            'column':{
                '1':{'width':30, 'anchor':'c'},
                '2':{'width':130, 'anchor':'se'},
                '3':{'width':60, 'anchor':'se'},
                '4':{'width':60, 'anchor':'se'},
                },
            'heading':{
                '1':{'text':' '},
                '2':{'text':'宠物名'},
                '3':{'text':'宠物id'},
                '4':{'text':'宠物昵称'},
            }
        }
        tabName = '宠物'
        self._buildtab_itemTab_2(tabView,tabName,treeViewArgs)

        treeViewArgs = {
            "columns":['1','2','3'],
            'show':'headings',
            'column':{
                '1':{'width':60, 'anchor':'c'},
                '2':{'width':130, 'anchor':'se'},
                '3':{'width':90, 'anchor':'se'},
                '4':{'width':0, 'anchor':'se'},
                },
            'heading':{
                '1':{'text':' '},
                '2':{'text':'装扮名称'},
                '3':{'text':'装扮id'},
                '4':{'text':''},
            }
        }
        tabName = '时装'
        self._buildtab_itemTab_2(tabView,tabName,treeViewArgs)

    def connectSQL(self):
        def inner():
            config = viewer.config
            config['DB_IP'] = self.db_ip.get()
            config['DB_PORT'] = int(self.db_port.get())
            config['DB_USER'] = self.db_user.get()
            config['DB_PWD'] = self.db_pwd.get()
            config['PVF_PATH'] = viewer.config['PVF_PATH']
            log(str(config))
            viewer.config = config
            sql = viewer.connect(self.titleLog)
            if sql==True:  
                self.titleLog('数据库已连接')
            else:
                self.titleLog('数据库连接失败 '+ str(sql))
            
            self.db_conBTN.config(text='重新连接',state='normal')
            self.CONNECT_FLG = False
        if self.CONNECT_FLG == False:
            self.db_conBTN.config(state='disable')
            self.CONNECT_FLG = True
            self.titleLog('正在连接数据库...')
            t = threading.Thread(target=inner)
            t.start()
    
    def enableTabs(self):
        '''启用上方tab'''
        for i in range(1,len(globalBlobs_map.keys()) +1 + len(globalNonBlobs_map.keys())):
            self.tabView.tab(i,state='normal')

    def disableTabs(self):
        '''禁用上方tab'''
        if DEBUG: return False
        for i in range(1,len(globalBlobs_map.keys()) +1 + len(globalNonBlobs_map.keys())):
            self.tabView.tab(i,state='disable')
    

if __name__=='__main__':
    a = App()    
    a.connectSQL()
    a.w.mainloop()
    #viewer.localPipe.send(-1)
    #os.kill(viewer.subPid,signal.SIGINT)