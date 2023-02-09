import viewerCMD as viewer
from viewerCMD import config
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename
import threading
import json
import os
import time

VerInfo = 'Ver.0.1.31'
if not os.path.exists('./log'):
    os.mkdir('./log')
tm = time.localtime()
LOGFile = f'./log/{"%02d" % tm.tm_mon}-{"%02d" % tm.tm_mday} {"%02d" % tm.tm_hour}_{"%02d" % tm.tm_min}_{"%02d" % tm.tm_sec}.log'

def log(text):
    tm = time.localtime()
    with open(LOGFile,'a+',encoding='utf-8') as f:
        log = f'[{"%02d" % tm.tm_mon}-{"%02d" % tm.tm_mday} {"%02d" % tm.tm_hour}:{"%02d" % tm.tm_min}:{"%02d" % tm.tm_sec}] {text}\n'
        f.write(log)


globalBlobs_map = {
        '物品栏':'inventory',
        '装备栏':'equipslot',
        '宠物栏':'creature',
        '仓库':'cargo'
    }
globalNonBlobs_map = {'宠物':'creature_items'}


class App():
    def __init__(self):
        w = tk.Tk()
        self.w = w
        self.titleLog = lambda text:[w.title(text),log(text)]
        w.iconbitmap('ico.ico')
        self.buildGUI(self.w)
        self.CONNECT_FLG = False #判断正在连接
        self.PVF_LOAD_FLG = False #判断正在加载pvf
    
    def _buildSqlConn(self,mainFrame):
        #数据库连接
        db_conFrame = tk.Frame(mainFrame)
        tk.Label(db_conFrame,text=' IP').grid(row=0,column=1)
        db_ip = ttk.Entry(db_conFrame,width=15)
        db_ip.grid(row=0,column=2,pady=5)
        db_ip.insert(0,config['DB_IP'])
        tk.Label(db_conFrame,text=' 端口').grid(row=0,column=3)
        db_port = ttk.Entry(db_conFrame,width=8)
        db_port.insert(0,config['DB_PORT'])
        db_port.grid(row=0,column=4)
        tk.Label(db_conFrame,text=' 用户名').grid(row=0,column=5)
        db_user = ttk.Entry(db_conFrame,width=8)
        db_user.insert(0,config['DB_USER'])
        db_user.grid(row=0,column=6)
        tk.Label(db_conFrame,text=' 密码').grid(row=0,column=7)
        db_pwd = ttk.Entry(db_conFrame,width=8,show='*')
        db_pwd.insert(0,config['DB_PWD'])
        db_pwd.grid(row=0,column=8)
        db_conBTN = ttk.Button(db_conFrame,text='连接',command=self.connectSQL)
        db_conBTN.grid(row=0,column=9,padx=10,pady=5)
        db_conFrame.pack()
        ttk.Separator(db_conFrame, orient='horizontal').grid(row=1,column=0,columnspan=10,sticky='we')
        self.db_ip = db_ip
        self.db_port = db_port
        self.db_user = db_user
        self.db_pwd = db_pwd
        self.db_conBTN = db_conBTN


    def _buildtab_main(self,tabView):
        #账号查询功能
        searchFrame = tk.Frame(tabView)
        searchFrame.pack(expand=True)
        tabView.add(searchFrame,text=' 查询 ')
        tabView.pack(expand=True, fill=tk.BOTH,padx=5,pady=5)

        accountSearchFrame = tk.LabelFrame(searchFrame,text='账户查询')
        accountE = ttk.Entry(accountSearchFrame,width=12)
        accountE.pack(padx=5,pady=5)
        accountBtn = ttk.Button(accountSearchFrame,text='查询',command=lambda:self.searchCharac('account'))
        accountBtn.pack(padx=5,pady=5)
        accountSearchFrame.grid(column=1,row=1,padx=5,pady=5,sticky='w')

        characSearchFrame = tk.LabelFrame(searchFrame,text='角色查询')
        characE = ttk.Entry(characSearchFrame,width=12)
        characE.pack(padx=5,pady=5)
        characBtn = ttk.Button(characSearchFrame,text='查询',command=lambda:self.searchCharac('cName'))
        characBtn.pack(padx=5,pady=5)
        characSearchFrame.grid(column=1,row=2,padx=5,pady=5,sticky='w')
        
        #角色选择列表
        characTreev = ttk.Treeview(searchFrame, selectmode ='browse')
        characTreev.grid(row=1,column=2,rowspan=2,sticky='we',padx=5,pady=10)

        characTreev["columns"] = ("1", "2", "3")
        characTreev['show'] = 'headings'
        characTreev.column("1", width = 90, anchor ='c')
        characTreev.column("2", width = 100, anchor ='se')
        characTreev.column("3", width = 90, anchor ='se')

        characTreev.heading("1", text ="全局编号")
        characTreev.heading("2", text ="角色名")
        characTreev.heading("3", text ="等级")
        characTreev.bind('<ButtonRelease-1>',self.selectCharac)

        # 信息显示及logo，物品源选择
        infoFrame = tk.Frame(searchFrame)
        infoFrame.grid(row=1,column=3,rowspan=2,sticky='n')
        PVFSelFrame = tk.LabelFrame(infoFrame,text='物品来源')
        PVFSelFrame.pack(fill='x',padx=5,pady=15)
        itemSourceSel = tk.IntVar()
        def selSource():
            def inner():
                self.setItemSource(itemSourceSel)
            t = threading.Thread(target=inner)
            t.daemon = True
            t.start()
        ttk.Radiobutton(PVFSelFrame,variable=itemSourceSel,value=0,text='CSV文件',command=selSource).pack(anchor='w',padx=15,pady=5)
        ttk.Radiobutton(PVFSelFrame,variable=itemSourceSel,value=1,text='PVF文件',command=selSource).pack(anchor='w',padx=15,pady=5)

        tk.Label(infoFrame,text='\n背包清理工具',font=('TkDefaultFont',12)).pack()
        tk.Label(infoFrame,text=VerInfo,font=('TkDefaultFont',12)).pack()
        tk.Label(infoFrame,text='台服dnf吧',font=('TkDefaultFont',19)).pack(pady=10)
        self.accountE = accountE
        self.characE = characE
        self.characTreev = characTreev
        self.itemSourceSel = itemSourceSel
    
    def _buildtab_itemTab(self,tabView,tabName,treeViewArgs):
        inventoryFrame = tk.Frame(tabView)
        inventoryFrame.pack(expand=True)
        tabView.add(inventoryFrame,text=tabName)
        allInventoryFrame = tk.LabelFrame(inventoryFrame,text='当前物品列表')
        allInventoryFrame.grid(row=1,column=1)
        itemsTreev_now = ttk.Treeview(allInventoryFrame, selectmode ='browse')
        itemsTreev_now.grid(row=1,column=2,rowspan=2,columnspan=2,sticky='we',padx=5)
        self.itemsTreevs_now[tabName] = itemsTreev_now

        delInventoryFrame = tk.LabelFrame(inventoryFrame,text='待删除物品列表')
        delInventoryFrame.grid(row=1,column=2,sticky='ns')
        itemsTreev_del = ttk.Treeview(delInventoryFrame, selectmode ='browse', height=8)
        itemsTreev_del.grid(row=1,column=2,rowspan=2,columnspan=2,sticky='we',padx=5)
        self.itemsTreevs_del[tabName] = itemsTreev_del
        def setTreeViev(itemsTreev,func=lambda e:...):
            itemsTreev['columns'] = treeViewArgs['columns']
            itemsTreev['show'] = treeViewArgs['show']
            for columnID in treeViewArgs['columns']:
                itemsTreev.column(columnID,**treeViewArgs['column'][columnID])
                itemsTreev.heading(columnID,**treeViewArgs['heading'][columnID])
            itemsTreev.bind('<Double-1>',func)

        setTreeViev(itemsTreev_now,lambda e:self.addDel(itemsTreev_now,itemsTreev_del))
        setTreeViev(itemsTreev_del,lambda e:self.removeDel(itemsTreev_del))

        def reselect(tabName):
            itemsTreev_del = self.itemsTreevs_del[tabName] 
            for child in itemsTreev_del.get_children():
                itemsTreev_del.delete(child)
        resetBtn = ttk.Button(delInventoryFrame,text=' 重选 ',command=lambda:reselect(tabName))
        resetBtn.grid(row=3,column=2,pady=5)
        delBtn = ttk.Button(delInventoryFrame,text='确定删除',command=lambda:self.deleteItems(tabName,itemsTreev_del))
        delBtn.grid(row=3,column=3,pady=5)

    def buildGUI(self,w):
        mainFrame = tk.Frame(w)
        mainFrame.pack()
        self.mainFrame = mainFrame
        self._buildSqlConn(mainFrame)

        tabView = ttk.Notebook(mainFrame)
        self.tabView = tabView
        self._buildtab_main(tabView)

        self.itemsTreevs_now = {}
        self.itemsTreevs_del = {}

        treeViewArgs = {
            "columns":['1','2','3'],
            'show':'headings',
            'column':{
                '1':{'width':30, 'anchor':'c'},
                '2':{'width':120, 'anchor':'se'},
                '3':{'width':90, 'anchor':'se'},
                },
            'heading':{
                '1':{'text':'编号'},
                '2':{'text':'物品名'},
                '3':{'text':'物品ID'},
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
                '2':{'width':90, 'anchor':'se'},
                '3':{'width':60, 'anchor':'se'},
                '4':{'width':60, 'anchor':'se'},
                },
            'heading':{
                '1':{'text':'编号'},
                '2':{'text':'宠物名'},
                '3':{'text':'宠物id'},
                '4':{'text':'宠物昵称'},
            }
        }
        for tabName in globalNonBlobs_map.keys():
            self._buildtab_itemTab(tabView,tabName,treeViewArgs)
    
    def connectSQL(self):
        def inner():
            config = {
                'DB_IP' : self.db_ip.get(),
                'DB_PORT' : int(self.db_port.get()),
                'DB_USER' : self.db_user.get(),
                'DB_PWD' : self.db_pwd.get(),
                'PVF_PATH' : viewer.config['PVF_PATH']
            }
            log(str(config))
            viewer.config = config
            if viewer.connect(self.titleLog):  
                self.titleLog('数据库已连接')
                json.dump(config,open(viewer.configPath,'w'))
            else:
                self.titleLog('数据库连接失败，请检查端口配置')
            
            self.db_conBTN.config(text='重新连接',state='normal')
            self.CONNECT_FLG = False
        if self.CONNECT_FLG == False:
            self.db_conBTN.config(state='disable')
            self.CONNECT_FLG = True
            self.titleLog('正在连接数据库...')
            t = threading.Thread(target=inner)
            t.start()
    
    def searchCharac(self,type='account'):   #或者cName
        if type=='account':
            characs = viewer.getCharactorInfo(uid=viewer.getUID(self.accountE.get()))
            
        else:
            characs = viewer.getCharactorInfo(name=self.characE.get())
        log(characs)
        for child in self.characTreev.get_children():
            self.characTreev.delete(child)
        for values in characs:
            self.characTreev.insert('',tk.END,values=values)
    
    def selectCharac(self,show=False):
        #global globalBlobs, globalNonBlobItems, cNo, name, level
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
        if show:
            self.titleLog(f'角色[{name}]物品已加载，双击条目选中删除')
        else:
            log(f'角色[{name}]物品已加载，双击条目选中删除')
        self.enableTabs()
        globalBlobs = {
            '物品栏':inventory,
            '装备栏':equipslot,
            '宠物栏':creature,
            '仓库':cargo
        }
        globalNonBlobItems = {'宠物':creature_items}

        # 物品列表插入新的节点
        for tabName,currentTabBlob in globalBlobs.items():
            itemsTreev_now = self.itemsTreevs_now[tabName]
            itemsTreev_del = self.itemsTreevs_del[tabName]
            for child in itemsTreev_now.get_children():
                itemsTreev_now.delete(child)
            for child in itemsTreev_del.get_children():
                itemsTreev_del.delete(child)

            for values in viewer.showBLOB(currentTabBlob):
                itemsTreev_now.insert('',tk.END,values=values)
        for tabName,currentTabItems in globalNonBlobItems.items():
            itemsTreev_now = self.itemsTreevs_now[tabName]
            itemsTreev_del = self.itemsTreevs_del[tabName]
            for child in itemsTreev_now.get_children():
                itemsTreev_now.delete(child)
            for child in itemsTreev_del.get_children():
                itemsTreev_del.delete(child)

            for values in currentTabItems:
                itemsTreev_now.insert('',tk.END,values=values)
        self.globalBlobs = globalBlobs
        self.globalNonBlobItems = globalNonBlobItems
        self.cNo = cNo
    
    def enableTabs(self):
        '''启用上方tab'''
        for i in range(1,len(globalBlobs_map.keys()) +1 + len(globalNonBlobs_map.keys())):
            self.tabView.tab(i,state='normal')

    def disableTabs(self):
        '''禁用上方tab'''
        for i in range(1,len(globalBlobs_map.keys()) +1 + len(globalNonBlobs_map.keys())):
            self.tabView.tab(i,state='disable')

    def addDel(self,itemsTreev_now,itemsTreev_del:ttk.Treeview):
        '''添加到删除列表'''
        values = itemsTreev_now.item(itemsTreev_now.focus())['values']
        item = itemsTreev_del.insert('',tk.END,values=values)
        #itemsTreev_del.yview_moveto(1)
        itemsTreev_del.see(item)
    def removeDel(self,itemsTreev_del):
        '''从删除列表移除'''
        itemsTreev_del.delete(itemsTreev_del.focus())

    def deleteItems(self,tabName,itemsTreev_del:ttk.Treeview):
        #print('delete',tabName,itemsTreev_del)
        if not messagebox.askokcancel('删除确认',f'确定删除{tabName}所选物品？'):
            return False
        deleteIDs = []
        for child in itemsTreev_del.get_children():
            log(itemsTreev_del.item(child))
            deleteIDs.append(itemsTreev_del.item(child)['values'][0])
        if tabName in globalBlobs_map.keys():
            log('删除BLOB')
            key = globalBlobs_map[tabName]
            blob = self.globalBlobs[tabName]
            InventoryBlob_new = viewer.buildDeletedBlob2(deleteIDs,blob)
            if viewer.setInventory(InventoryBlob_new,self.cNo,key):
                self.titleLog('====删除成功====\n')
            else:
                self.titleLog('====删除失败，请检查数据库连接状况====\n')
        if tabName in globalNonBlobs_map.keys():
            log('删除非BLOB')
            for ui_id in deleteIDs:
                if viewer.delCreatureItem(ui_id):
                    self.titleLog('====删除成功====\n')
                else:
                    self.titleLog('====删除失败，请检查数据库连接状况====\n')
        self.selectCharac()
    
    def setItemSource(self,var:tk.IntVar):
        '''设置物品来源，读取pvf或者csv'''
        source = var.get()
        self.disableTabs()
        if source==1 and not self.PVF_LOAD_FLG:
            PVFPath = askopenfilename(filetypes=[('DNF Script.pvf file','*.pvf')])
            if os.path.exists(PVFPath):
                self.titleLog('加载PVF中...')
                self.PVF_LOAD_FLG = True
                info = viewer.loadItems2(True,PVFPath,self.titleLog)
                self.PVF_LOAD_FLG = False
                if var.get()==1:
                        self.titleLog(info)
                else:
                    viewer.loadItems(False)
                    self.titleLog('PVF加载完成，请选择使用')
                    return True
            else:
                self.titleLog('PVF路径错误，加载CSV')
                time.sleep(1)
                source = 0
                var.set(0)
            self.selectCharac()
        if source==1 and self.PVF_LOAD_FLG:
            self.titleLog('等待PVF加载')
        if source==0:
            info = viewer.loadItems(False)
            self.titleLog(info)
            self.selectCharac()

if __name__=='__main__':
    a = App()
    a.disableTabs()
    
    a.connectSQL()
    a.w.mainloop()
