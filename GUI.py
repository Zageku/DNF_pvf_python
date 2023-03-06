import viewerCMD as viewer
from viewerCMD import config
import tkinter as tk
from tkinter import ttk, messagebox
if not hasattr(ttk,'Spinbox'):
    class Spinbox(ttk.Entry):
        def __init__(self, master=None, **kw):  #from_=0,to=99,
            ttk.Entry.__init__(self, master, "ttk::spinbox", **kw)
        def set(self, value):
            self.tk.call(self._w, "set", value)
    ttk.Spinbox = Spinbox
from tkinter.filedialog import askopenfilename, asksaveasfilename
import threading
from pathlib import Path
import time
from copy import deepcopy
import struct
from toolTip import CreateToolTip, CreateOnceToolTip, ToolTip
from zhconv import convert
import json
from imageLabel import ImageLabel
import ps
DEBUG = True
VerInfo = viewer.config['VERSION']#'Ver.0.2.23'
logPath = Path('log/')
gifPath_1 = Path('config/gif')
gifPath_2 = Path('config/gif2')
gitHubLogoPath = Path('config/github.png')
IconPath = 'config/ico.ico'
if not logPath.exists():
    logPath.mkdir()
tm = time.localtime()
LOGFile = f'./log/{"%02d" % tm.tm_mon}-{"%02d" % tm.tm_mday} {"%02d" % tm.tm_hour}_{"%02d" % tm.tm_min}_{"%02d" % tm.tm_sec}.log'

def log(text):
    tm = time.localtime()
    with open(LOGFile,'a+',encoding='utf-8') as f:
        log = f'[{"%02d" % tm.tm_mon}-{"%02d" % tm.tm_mday} {"%02d" % tm.tm_hour}:{"%02d" % tm.tm_min}:{"%02d" % tm.tm_sec}] {text}\n'
        f.write(log)

def str2bytes(s)->bytes:
    i = 0
    length = len(s)
    nums = []
    while i<length:
        nums.append(int(s[i:i+2],base=16))
        i+=2
    return struct.pack('B'*len(nums),*nums)

globalBlobs_map = {
        '物品栏':'inventory',
        '穿戴栏':'equipslot',
        '宠物栏':'creature',
        ' 仓库 ':'cargo'
    }
globalNonBlobs_map = {
    ' 宠物 ':'creature_items',
    ' 时装 ':'user_items'
    
    }
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

def openGithub(e=None):
    import webbrowser
    webbrowser.open(viewer.config['GITHUB'])

class GitHubFrame(tk.Frame):
    def __init__(self,*args,**kw):
        tk.Frame.__init__(self,*args,**kw)
        gitHubLogo = ImageLabel(self)
        gitHubLogo.pack()
        gitHubLogo.load(gitHubLogoPath,[150,150])
        CreateToolTip(self,'点击查看作者GitHub更新')
        gitHubLogo.bind('<Button-1>',openGithub)


class App():
    def __init__(self):
        w = tk.Tk()
        def fixed_map(option):
            return [elm for elm in style.map('Treeview', query_opt=option) if
            elm[:2] != ('!disabled', '!selected')]
        style = ttk.Style()
        style.map('Treeview', foreground=fixed_map('foreground'),
        background=fixed_map('background'))
        self.w = w
        self.titleLog = lambda text:[w.title(text),log(text)]
        w.iconbitmap(IconPath)
        
        self.CONNECT_FLG = False #判断正在连接
        self.PVF_LOAD_FLG = False #判断正在加载pvf
        self.Advance_Search_State_FLG = False #判断高级搜索是否打开
        self.Advance_Search_State_FLG_Stackable = False
        self.currentItemDict = {}
        self.editedItemsDict = {}
        self.itemInfoClrFuncs = {}
        self.selectedCharacItemsDict = {}   #使用tabName存储id:ItemSlot
        self.fillTreeFunctions = {}
        self.updateMagicSealFuncs = {}
        self.editFrameUpdateFuncs = {}
        self.globalCharacBlobs = {} #利用标签页名字来存储原始blob
        self.globalCharacNonBlobs = {} #利用标签页名字来存储原始非blob
        self.unknowItemsDict = {}
        self.errorItemsDict = {}
        self.importFlgDict = {} #保存导入过的标签页名

        self.tabViewChangeFuncs = []    #切换tab时执行的function列表
        self.tabNames = []
        self.cNo=0
        self.cName = ''
        self.lev = 0
        self.characInfos = {}
        self.build_GUI(self.w)
    
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
        db_pwd = ttk.Entry(db_conFrame,width=8)#,show='*'
        db_pwd.insert(0,config['DB_PWD'])
        db_pwd.grid(row=0,column=8)
        db_conBTN = ttk.Button(db_conFrame,text='连接',command=self.connectSQL)
        db_conBTN.grid(row=0,column=9,padx=12,pady=5)
        
        
        db_conFrame.pack(fill='x',expand=True)
        ttk.Separator(mainFrame, orient='horizontal').pack(fill='x',expand=True)
        self.db_ip = db_ip
        self.db_port = db_port
        self.db_user = db_user
        self.db_pwd = db_pwd
        self.db_conBTN = db_conBTN

    def _buildtab_main(self,tabView):
        def fill_charac_treeview(charac_list):
            for child in self.characTreev.get_children():
                self.characTreev.delete(child)
            for values in charac_list:
                cNo,name,lev,job,growType,deleteFlag = values
                jobDict = viewer.jobDict.get(job)
                if isinstance(jobDict,dict):
                    jobNew = jobDict.get(growType % 16)
                self.characTreev.insert('',tk.END,values=[cNo,name,lev,jobNew],tags='deleted' if deleteFlag==1 else '')
                self.characInfos[cNo] = {'name':name,'lev':lev,'job':job,'growType':growType} 
            encodeE.set(f'{viewer.sqlEncodeUseIndex}-{viewer.SQL_ENCODE_LIST[viewer.sqlEncodeUseIndex]}')
            self.clear_charac_tab_func()
            self.currentItemDict = {}
            self.selectedCharacItemsDict = {}
            for tabName in self.itemInfoClrFuncs.keys():
                itemsTreev_now = self.itemsTreevs_now[tabName]
                for child in itemsTreev_now.get_children():
                    itemsTreev_now.delete(child)
                try:
                    self.itemInfoClrFuncs[tabName]()    #清除物品信息显示
                    self.fillTreeFunctions[tabName]()   #填充treeview
                except:
                    pass
                try:
                    itemsTreev_del = self.itemsTreevs_del[tabName]
                    for child in itemsTreev_del.get_children():
                        itemsTreev_del.delete(child)
                except:
                    continue
            self.globalCharacBlobs = {}

        def searchCharac(searchType='account'):   #或者cName
            if searchType=='account':
                characs = viewer.getCharactorInfo(uid=viewer.getUID(self.accountE.get()))
                
            else:
                characs = viewer.getCharactorInfo(cName=self.characE.get())
            log(characs)
            fill_charac_treeview(charac_list=characs)

        def selectCharac(showTitle=False):
            sel = self.characTreev.item(self.characTreev.focus())['values']
            try:
                cNo, cName, lev,*_ = sel
            except:
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
                self.titleLog(f'角色[{cName}]物品已加载')
            else:
                log(f'角色[{cName}]物品已加载')
            self.enable_Tabs()
            blobsItemsDict = {}
            for key,value in globalBlobs_map.items():
                blobsItemsDict[key] = locals()[value]
            self.globalCharacBlobs = blobsItemsDict

            nonBlobItemsDict = {}
            for key,value in globalNonBlobs_map.items():
                nonBlobItemsDict[key] = locals()[value]
            self.cNo = cNo
            self.cName = cName
            self.lev = lev
            self.globalCharacNonBlobs = nonBlobItemsDict
            self.importFlgDict = {}
            self.fill_tab_treeviews()
            self.fill_charac_tab_fun()

        def setItemSource(sourceVar:tk.IntVar,pvfPath:str='',pvfMD5=''):
            '''设置物品来源，读取pvf或者csv'''
            if pvfMD5!='':
                sourceVar.set(1)
            source = sourceVar.get()
            self.disable_Tabs()
            print('数据源加载中...PVF：',sourceVar.get(),pvfPath,pvfMD5)
            if source==1 and not self.PVF_LOAD_FLG:
                if pvfMD5!='':
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
                        t1 = time.time()
                        self.titleLog('加载PVF中...')
                        self.PVF_LOAD_FLG = True
                        info = viewer.loadItems2(True,pvfPath,self.titleLog)
                        self.PVF_LOAD_FLG = False
                        if info=='PVF文件路径错误':
                            pvfComboBox.set('pvf路径错误')
                            self.titleLog('pvf读取错误')
                            return False
                        elif '加载pvf缓存' in info:
                            pvfComboBox.set('使用缓存')

                        t = time.time() - t1 
                        info += '  花费时间%.2fs' % t
                        pvfComboBox.set('使用pvf文件')
                        if sourceVar.get()==1:
                            self.titleLog(info)
                        else:
                            viewer.loadItems2(False)
                            self.titleLog('PVF加载完成，请选择使用  花费时间%.2fs' % t)
                            
                    else:
                        self.titleLog('PVF路径错误，加载CSV')
                        time.sleep(1)
                        source = 0
                        sourceVar.set(0)
                    pvfCaches = list(viewer.PVFcacheDicts.keys())
                    pvfCaches.remove('_cacheVersion')
                    pvfComboBox.config(values=pvfCaches)
                selectCharac()
            if source==1 and self.PVF_LOAD_FLG:
                self.titleLog('等待PVF加载')
            if source==0:
                info = viewer.loadItems2(False)
                self.titleLog(info)
                selectCharac()
            if viewer.magicSealDict.get(0) is None:
                viewer.magicSealDict[0] = ''
            [func() for func in self.updateMagicSealFuncs.values()]
            self.hiddenCom.config(values=['0-None']+[f'{i+1}-{value}' for i,value in enumerate(viewer.avatarHiddenList[0])])
            self.jobE.config(values=[f'{item[0]}-{item[1][0]}'  for item in viewer.jobDict.items()])
            self.jobE.set('')

        #账号查询功能
        self.searchCharac = searchCharac
        self.selectCharac = selectCharac
        self.fillCharac = fill_charac_treeview
        self.refreshBtn.config(command=selectCharac)
        searchFrame = tk.Frame(tabView,borderwidth=0)
        searchFrame.pack(expand=True)
        tabView.add(searchFrame,text=' 查询 ')
        #tabView.grid(expand=True, fill=tk.BOTH,padx=5,pady=5)

        
        padx = 0
        pady = 2
        row = 1
        padFrame = tk.Frame(searchFrame)
        padFrame.grid(column=0,row=row,padx=3,sticky='we')
        accountSearchFrame = tk.LabelFrame(searchFrame,text='账户查询')
        accountE = ttk.Entry(accountSearchFrame,width=12)
        accountE.pack(padx=5,pady=pady,fill='x')
        accountBtn = ttk.Button(accountSearchFrame,text='查询',command=lambda:searchCharac('account'),state='disable')
        accountBtn.pack(padx=5,pady=pady,fill='x')
        accountSearchFrame.grid(column=1,row=row,padx=padx,sticky='we')
        row += 1
        characSearchFrame = tk.LabelFrame(searchFrame,text='角色查询')
        characE = ttk.Entry(characSearchFrame,width=12)
        characE.pack(padx=5,pady=pady,fill='x')
        characBtn = ttk.Button(characSearchFrame,text='查询',command=lambda:searchCharac('cName'),state='disable')
        characBtn.pack(padx=5,pady=pady,fill='x')
        characSearchFrame.grid(column=1,row=row,padx=padx,sticky='we')
        row += 1
        connectorFrame = tk.LabelFrame(searchFrame,text='连接器')
        connectorE = ttk.Combobox(connectorFrame,width=10,state='readonly')
        connectorE.pack(padx=5,pady=pady)
        def selConnector(e):
            i = int(connectorE.get().split('-')[0])
            viewer.connectorUsed = viewer.connectorAvailuableDictList[i]
            print(f'当前切换连接器为{viewer.connectorUsed["account_db"]}')
        connectorE.bind('<<ComboboxSelected>>',selConnector)
        connectorFrame.grid(column=1,row=row,padx=padx,sticky='we')
        self.connectorE = connectorE
        self.connectorE.set('----')

        row += 1
        encodeFrame = tk.LabelFrame(searchFrame,text='文字编码')
        encodeE = ttk.Combobox(encodeFrame,width=10,values=[f'{i}-{encode}' for i,encode in enumerate(viewer.SQL_ENCODE_LIST)],state='readonly')
        encodeE.pack(padx=5,pady=pady)
        encodeE.set('----')
        def setEncodeing(e):
            encodeIndex = int(encodeE.get().split('-')[0])
            viewer.sqlEncodeUseIndex = encodeIndex
            viewer.ENCODE_AUTO = False  #关闭自动编码切换
        encodeE.bind('<<ComboboxSelected>>',setEncodeing)
        encodeFrame.grid(column=1,row=row,padx=padx,sticky='we')
        
        # 信息显示及logo，物品源选择
        row += 1
        PVFSelFrame = tk.LabelFrame(searchFrame,text='数据来源')
        PVFSelFrame.grid(row=row,column=1,padx=padx,sticky='we')
        itemSourceSel = tk.IntVar()
        pvfPath = config.get('PVF_PATH')
        if pvfPath is not None and '.pvf' in pvfPath:
            p = Path(pvfPath)
            if p.exists():
                itemSourceSel.set(1)
        def selSource(pvfPath=''):
            def inner():
                if  pvfPath=='':# or '.pvf' in pvfPath.lower()
                    setItemSource(itemSourceSel,pvfPath)
                elif pvfPath in viewer.PVFcacheDicts.keys():
                    setItemSource(itemSourceSel,pvfMD5=pvfPath)
                else:
                    itemSourceSel.set(0)
                    setItemSource(itemSourceSel)
            t = threading.Thread(target=inner)
            t.daemon = True
            t.start()
        
        selSource(config.get('PVF_PATH'))
        ttk.Radiobutton(PVFSelFrame,variable=itemSourceSel,value=0,text='  本地文件',command=selSource).pack(anchor='w',padx=5,pady=5)
        ttk.Radiobutton(PVFSelFrame,variable=itemSourceSel,value=1,text='  PVF文件',command=selSource).pack(anchor='w',padx=5,pady=5)
        pvfCaches = list(viewer.PVFcacheDicts.keys())
        pvfCaches.remove('_cacheVersion')
        pvfComboBox = ttk.Combobox(PVFSelFrame,values=pvfCaches,width=10)
        pvfComboBox.set('请选择PVF缓存')
        pvfComboBox.pack(anchor='w',padx=5,pady=5,fill='x')
        pvfComboBox.bind("<<ComboboxSelected>>",lambda e:selSource(pvfComboBox.get()))
        CreateToolTip(pvfComboBox,'PVF缓存')

        #角色选择列表
        characTreev = ttk.Treeview(searchFrame, selectmode ='browse',height=18)
        characTreev.grid(row=1,column=2,rowspan=5,sticky='we',padx=5,pady=5)

        characTreev["columns"] = ("1", "2", "3",'4')
        characTreev['show'] = 'headings'
        characTreev.column("1", width = 40, anchor ='c')
        characTreev.column("2", width = 115, anchor ='se')
        characTreev.column("3", width = 50, anchor ='se')
        characTreev.column("4", width = 90, anchor ='se')

        characTreev.heading("1", text ="编号")
        characTreev.heading("2", text ="角色名")
        characTreev.heading("3", text ="等级")
        characTreev.heading("4", text ="职业")
        characTreev.bind('<ButtonRelease-1>',selectCharac)
        characTreev.tag_configure('deleted', background='gray')

        infoFrame = tk.Frame(searchFrame,borderwidth=0)
        infoFrame.grid(row=1,column=3,rowspan=10,sticky='nwse')
        infoFrame_ = tk.Frame(searchFrame,width=192,height=5)
        infoFrame_.grid(row=0,column=3,sticky='nwse')
        if len(viewer.config['TITLE'])>0:
            tk.Label(infoFrame,text=viewer.config['TITLE'],font=viewer.config['FONT'][0]).pack(anchor='n',side='top')
        if len(viewer.config['VERSION'])>0:
            tk.Label(infoFrame,text=viewer.config['VERSION'],font=viewer.config['FONT'][1]).pack(anchor='n',side='top')
        if len(viewer.config['INFO'])>0:
            tk.Label(infoFrame,text=viewer.config['INFO'],font=viewer.config['FONT'][2]).pack(anchor='n',side='top')
        gifCanvas = ImageLabel(infoFrame,borderwidth=0)
        gifCanvas.pack(expand=True,pady=5,fill='both')
        def loadPics():
            size = gifCanvas.winfo_width(),gifCanvas.winfo_height()
            if size[0] < 10:
                return self.w.after(100,loadPics)
            gifCanvas.loadDir(gifPath_1,size,root=self.w)
            tabView.update()
        self.w.after(100,loadPics)

        
        
        def changeGif(e):
            if str(searchFrame)==self.tabView.select():
                gifCanvas.randomShow()
        self.tabViewChangeFuncs.append(changeGif)

        self.accountE = accountE
        self.accountBtn = accountBtn
        self.characE = characE
        self.characBtn = characBtn
        self.characTreev = characTreev
        self.itemSourceSel = itemSourceSel
    
    def checkBloblegal(self):
        positionDict = {
            0x00:['快捷栏',[3,9]],
            0x01:['装备',[9,57]],
            0x02:['消耗品',[57,105]],
            0x03:['材料',[105,153]],
            0x04:['任务材料',[153,201]],
            0x05:['宠物',[98,99]],#正在使用的宠物
            0x06:['宠物装备',[0,49],[99,102]],#装备栏和正在使用的装备
            0x07:['宠物消耗品',[49,98],[0,0]],
            0x0a:['副职业',[201,249]]
        }
        if len(viewer.PVFcacheDict.keys())==0:
            return 'PVF未加载'
        for tabName in self.globalCharacBlobs.keys():
            itemDict = self.selectedCharacItemsDict[tabName]
            self.unknowItemsDict[tabName] = []  #保存位置物品的index
            self.errorItemsDict[tabName] = []   #保存错误物品的index
            for index, itemSlot in itemDict.items():
                if itemSlot.id==0:
                    continue
                typeID,typeZh = viewer.getStackableTypeMainIdAndZh(itemSlot.id)
                if typeID!=0 and typeID!=itemSlot.type:
                    self.errorItemsDict[tabName].append(index)
                    #print(index,typeID,'不合法',itemSlot)
                elif typeID==0:
                    self.unknowItemsDict[tabName].append(index)
                    #print(index,typeID,'未知',itemSlot)
                if tabName==' 物品栏 ' and typeID!=0:
                    if index in range(*positionDict[typeID][1]):
                        pass
                        #print(index,'合法')
                    else:
                        self.errorItemsDict[tabName].append(index)
                elif tabName==' 穿戴栏 ':
                    if typeID != 0x01:
                        self.errorItemsDict[tabName].append(index)
                elif tabName==' 宠物栏 ':
                    if index in range(*positionDict[typeID][1]) or index in range(*positionDict[typeID][2]):
                        pass
                    else:
                        self.errorItemsDict[tabName].append(index)
                elif tabName==' 仓库 ':
                    if itemSlot.type not in [1,2,3,0x0a]:
                        self.errorItemsDict[tabName].append(index)
        print('未知物品',self.unknowItemsDict,'\n错误物品',self.errorItemsDict)

    def fill_tab_treeviews(self):
        '''根据当前本地的blob和非blob字段填充数据（不包括角色信息）'''
        self.selectedCharacItemsDict = {}
        for key in self.editedItemsDict.keys():
            self.editedItemsDict[key] = {}    #清空编辑的对象
        
        for tabName,currentTabBlob in self.globalCharacBlobs.items():#替换填充TreeView
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
                CharacItemsDict[index] = dnfItemSlot
            self.selectedCharacItemsDict[tabName] = CharacItemsDict
            
            self.itemInfoClrFuncs[tabName]()    #清除物品信息显示
            self.fillTreeFunctions[tabName]()   #填充treeview
        self.hiddenCom.set('0-None')
        self.checkBloblegal()   #检查物品合法

        for tabName,currentTabItems in self.globalCharacNonBlobs.items():
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
            self.selectedCharacItemsDict[tabName] = CharacNoneBlobItemsDict

    def _buildtab_itemTab(self,tabView,tabName,treeViewArgs):
        def ask_commit():
            if showSelectedItemInfo()!=True or self.cNo==0:
                return False
            if not messagebox.askokcancel('修改确认',f'确定修改{tabName}所选物品？\n请确认账号不在线或正在使用其他角色\n{self.editedItemsDict[tabName]}'):
                return False
            cNo = self.cNo
            key = globalBlobs_map[tabName]
            originblob = self.globalCharacBlobs[tabName]
            viewer.commit_change_blob(originblob,self.editedItemsDict[tabName],cNo,key)
            self.titleLog(f'====修改成功==== {tabName} 角色ID：{self.cNo}')
            return self.selectCharac()
        def config_TreeViev(itemsTreev,doubleFunc=lambda e:...,singleFunc=lambda e:...):
            itemsTreev['columns'] = treeViewArgs['columns']
            itemsTreev['show'] = treeViewArgs['show']
            for columnID in treeViewArgs['columns']:
                itemsTreev.column(columnID,**treeViewArgs['column'][columnID])
                itemsTreev.heading(columnID,**treeViewArgs['heading'][columnID])
            itemsTreev.bind('<Double-1>',doubleFunc)
            itemsTreev.bind("<Button-1>", lambda e:self.w.after(100,singleFunc))
            
        def save_blob(fileType='blob',additionalTag=tabName):
            filePath = asksaveasfilename(title=f'保存文件(.{fileType})',filetypes=[('二进制文件',f'*.{fileType}')],initialfile=f'{self.cName}_lv.{self.lev}_{additionalTag}.{fileType}')
            if filePath=='':
                return False
            if filePath[-1-len(fileType):]!= f'.{fileType}':
                filePath += f'.{fileType}'
            filePath = filePath[:-1-len(fileType)]  +filePath[-1-len(fileType):]#+ f'-{additionalTag}'
            with open(filePath,'wb') as f:
                f.write(self.globalCharacBlobs[tabName])
            self.titleLog(f'文件已保存{filePath}')
        def load_blob(fileType='blob'):
            filePath = askopenfilename(filetypes=[(f'DNF {tabName} file',f'*.{fileType}')])
            if filePath=='':
                return False
            p = Path(filePath)
            if p.exists():
                with open(p,'rb') as f:
                    blob = f.read()
            self.globalCharacBlobs[tabName] = blob
            self.importFlgDict[tabName] = True
            self.fill_tab_treeviews()

        def changeItemSlotType(e=None):
            '''点击修改物品类别或点击新物品时，修改控件可编辑状态'''
            typeZh = typeEntry.get().split('-')[1]

            
            if typeZh in ['装备']:
                numGradeLabel.config(text='品级：')
                for widget in itemEditFrame.children:
                    try:
                        itemEditFrame.children[widget].config(state='normal')
                    except:
                        pass
                for widget in equipmentExFrame.children:
                    #print(widget)
                    try:
                        equipmentExFrame.children[widget].config(state='normal')
                    except:
                        pass

                forth.config(state='normal')

                for magicSealIDEntry in magicSealIDEntrys:
                    magicSealIDEntry.config(state='readonly')
            else:
                forth.config(state='disable')
                for widget in itemEditFrame.children:
                    try:
                        itemEditFrame.children[widget].config(state='disable')
                    except:
                        pass
                for widget in equipmentExFrame.children:
                    try:
                        equipmentExFrame.children[widget].config(state='disable')
                    except:
                        pass
                numGradeLabel.config(state='normal',text='数量：')
                numEntry.config(state='normal')
                itemIDEntry.config(state='normal')
                itemNameEntry.config(state='normal')
                delBtn.config(state='normal')
                resetBtn.config(state='normal')
                typeEntry.config(state='normal')
                enableTestBtn.config(state='normal')
            if typeEntry.get().split('-')[0]=='0':
                typeEntry.config(state='normal')
            else:
                typeEntry.config(state='normal' if viewer.config.get('TYPE_CHANGE_ENABLE') == 1 else 'disable')
                       
        def updateItemEditFrame(itemSlot:viewer.DnfItemSlot):
            '''传入slot对象，更新右侧编辑槽，不触发保存'''
            for widget in itemEditFrame.children:
                try:
                    itemEditFrame.children[widget].config(state='normal')
                except:
                    pass
            for widget in equipmentExFrame.children:
                try:
                    equipmentExFrame.children[widget].config(state='normal')
                except:
                    pass
            clear_item_Edit_Frame(False)


            itemSealVar.set(itemSlot.isSeal)
            itemIDEntry.insert(0,itemSlot.id)
            durabilityEntry.insert(0,itemSlot.durability)
            itemNameEntry.insert(0,str(viewer.ITEMS_dict.get(itemSlot.id)))
            numEntry.insert(0,itemSlot.num_grade)
            EnhanceEntry.insert(0,itemSlot.enhancementLevel)
            forgingEntry.insert(0,itemSlot.forgeLevel)
            otherworldEntry.insert(0,itemSlot.otherworld.hex())
            orbEntry.insert(0,itemSlot.orb_bytes.hex())
            coverMagic,magicSeals = itemSlot.readMagicSeal()
            itemSlotBytesE.insert(0,itemSlot.build_bytes().hex())

            for i in range(4):
                magicSealEntrys[i].set(magicSeals[i][1])
                magicSealIDEntrys[i].config(state='normal')
                magicSealIDEntrys[i].insert(0,magicSeals[i][0])
                magicSealIDEntrys[i].config(state='readonly')
                magicSealLevelEntrys[i].insert(0,magicSeals[i][2])
                

            IncreaseEntry.insert(0,itemSlot.increaseValue)
            IncreaseTypeEntry.set(itemSlot.increaseTypeZh)
            typeEntry.set(str(itemSlot.type)+'-'+itemSlot.typeZh)
            if coverMagic % 4 == 3:
                forthSealEnable.set(1)
            else:
                forthSealEnable.set(0)
            

            changeItemSlotType()
            if itemSlot.id == 0:
                typeEntry.config(state='readonly')
            
        def clear_item_Edit_Frame(clearTitle=True):
            '''清空右侧编辑槽'''
            if clearTitle:
                itemEditFrame.config(text=f'物品信息编辑')
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
            itemSlotBytesE.delete(0,tk.END)
            
            for magicSealIDEntry in magicSealIDEntrys:
                magicSealIDEntry.config(state='normal')
            
            
            
            for magicSealIDEntry in magicSealIDEntrys:
                magicSealIDEntry.delete(0,tk.END)
            for magicSealEntry in magicSealEntrys:
                magicSealEntry.set('')
            for magicSealLevelEntry in magicSealLevelEntrys:
                magicSealLevelEntry.delete(0,tk.END)

            for magicSealIDEntry in magicSealIDEntrys:
                magicSealIDEntry.config(state='readonly')

        def getItemPVFInfo()->str:
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
            
        def set_treeview_color():
            if self.importFlgDict.get(tabName) is not None:
                initTag = 'edited'
            else:
                initTag = ''
            for i_name in itemsTreev_now.get_children():
                try:
                    index,name,num,id_,*_ = itemsTreev_now.item(i_name)['values']
                    tag = initTag
                    if index in self.errorItemsDict[tabName]:
                        tag = 'error'
                    elif index in self.unknowItemsDict[tabName]:
                        tag = 'unknow'
                    itemSlot:viewer.DnfItemSlot = self.editedItemsDict.get(tabName).get(index)
                    if itemSlot  is not None:
                        if itemSlot.id == 0:
                            tag = 'deleted'
                        else:
                            tag = 'edited'
                    itemsTreev_now.item(i_name,tags=tag)
                except:
                    pass

        def showSelectedItemInfo(save=True,reset=False):
            '''显示当前选中物品槽，save:保存当前物品编辑状态，reset：重置当前编辑槽，而不是显示选中的槽'''
            if save:    
                saveState = editSave()
                if self.currentItemDict.get(tabName) is not None and saveState==True:
                    print('物品被编辑保存',self.editedItemsDict)
                elif saveState=='TypeEmptyFalse':
                    return False
                elif saveState=='AvatarItemFalse':
                    return False
            if reset:
                try:
                    index = int(itemEditFrame.cget('text').split('(')[-1].replace(')',''))
                    print(index)
                except:
                    return False
            else:
                values = itemsTreev_now.item(itemsTreev_now.focus())['values']  #数据库index
                if len(values)==0:
                    #未选中任何物品
                    return True
                index = values[0]
                
                set_treeview_color()
            if save and self.editedItemsDict.get(tabName).get(index) is not None:
                itemSlot:viewer.DnfItemSlot = self.editedItemsDict.get(tabName).get(index)
            else:
                itemSlot:viewer.DnfItemSlot = self.selectedCharacItemsDict[tabName][index]
            updateItemEditFrame(itemSlot)
            self.w.title(itemSlot)
            self.currentItemDict[tabName] = [index,itemSlot,itemsTreev_now.focus()]
            itemEditFrame.config(text=f'物品信息编辑({index})')
            return True

        def searchItem(e:tk.Event):
            '''搜索物品名'''
            if e.x<100:return
            key = itemNameEntry.get()
            if len(key)>0:
                res = viewer.searchItem(key)
                itemNameEntry.config(values=[str([item[0]])+' '+item[1] for item in res])
        def searchMagicSeal(com:ttk.Combobox):
            '''输入魔法封印时搜索'''
            key = com.get()
            res = viewer.searchMagicSeal(key)
            res.sort()
            if key!='':
                res_ = list(viewer.magicSealDict.items())
                res_.sort()
                res += res_
            #print(res)
            com.config(values=[item[1].strip()+' '+str([item[0]]) for item in res])
        
        def setMagicSeal(sealNameEntry,sealIDEntry):
            '''选择魔法封印属性时自动填充'''
            name = sealNameEntry.get()
            sealIDEntry.config(state='normal')
            sealIDEntry.delete(0,tk.END)
            sealIDEntry.insert(0,name.split(' [')[1].replace(']',''))
            sealIDEntry.config(state='readonly')
            sealNameEntry.set(name.split(' ')[0])

        def readSlotName(name_id='id'):
            if name_id=='id':
                id_ = itemIDEntry.get()
                try:
                    id_ = int(id_)
                except:
                    id_ = 0
                name = str(viewer.ITEMS_dict.get(int(id_)))
            else:
                id_,name = itemNameEntry.get().split(' ',1)
                id_ = id_[1:-1]
                
            itemIDEntry.delete(0,tk.END)
            itemIDEntry.insert(0,id_)
            itemNameEntry.delete(0,tk.END)
            itemNameEntry.insert(0,name)
            itemNameEntry.config(values=[])
            print(name,id_)

        def reset():
            showSelectedItemInfo(save=False,reset=True)

        def setDelete():
            itemSlot = viewer.DnfItemSlot(b'')
            updateItemEditFrame(itemSlot)

        def editSave(retType='bool'):
            '''保存编辑信息'''
            
            if self.currentItemDict.get(tabName) is None:#没有加载角色数据
                if retType == 'bool':
                    return False
                else:
                    return b'\x00'*61
            #try:
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
            magicSeals = []
            for i in range(4):
                magicSeals.append([int(magicSealIDEntrys[i].get()),magicSealEntrys[i].get(),int(magicSealLevelEntrys[i].get())])
            if forthSealEnable.get()==1:
                coverMagic = 3  
            elif itemSlot.coverMagic==3:
                coverMagic = 0
            else:
                coverMagic = itemSlot.coverMagic
            
            itemSlot.coverMagic = coverMagic
            magicSeal = itemSlot.buildMagicSeal([coverMagic,magicSeals])

            if len(itemSlot.magicSeal)==len(magicSeal):
                itemSlot.magicSeal = magicSeal
            slotBytes = itemSlot.build_bytes()
            itemSlot.oriBytes = slotBytes
            if retType=='bool':
                if slotBytes!= self.selectedCharacItemsDict[tabName][index].oriBytes:
                    
                    if itemSlot.id!=0 and itemSlot.type==0:
                        messagebox.askokcancel('物品状态确认','当前物品种类为空！请清空格子或设置合适种类以继续保存。')
                        #enableTypeChangeVar.set(1)
                        typeEntry.config(state='readonly')
                        return 'TypeEmptyFalse'
                    if 'avatar' in getItemPVFInfo():
                        messagebox.askokcancel('物品状态确认','当前物品种类为时装！时装无法保存至物品栏')
                        return 'AvatarItemFalse'
                    self.editedItemsDict[tabName][index] = itemSlot
                    return True
                else:
                    if index in self.editedItemsDict[tabName].keys():
                        self.editedItemsDict[tabName].pop(index)
                    return False
            else:
                return slotBytes

        def refill_Tree_View(e=tk.Event):
            try:
                typeSel = int(typeBox.get().split('-')[0],16)
            except:
                typeSel = 0xff
            for child in itemsTreev_now.get_children():
                    itemsTreev_now.delete(child)
            viewer.ITEMS_dict[0] = ''
            CharacItemsDict = self.selectedCharacItemsDict[tabName]
            for index, dnfItemSlot in CharacItemsDict.items():
                    name = str(viewer.ITEMS_dict.get(dnfItemSlot.id))
                    if tabName=='物品栏' and index in [0,1,2]:
                        #过滤物品栏前三个。这三个功能未知，会闪退
                        continue
                    if typeSel!=0xff and typeSel!=0x00: #过滤种类
                        if dnfItemSlot.id != 0 and dnfItemSlot.type != typeSel:
                            continue
                        if tabName in ['物品栏','宠物栏']:   #物品栏、宠物栏专属过滤
                            position = viewer.positionDict[typeSel][1]
                            if index not in range(*position) and index not in range(3,9):
                                #不是该位置的index，也不是快捷栏
                                continue
                            if index in range(3,9) and dnfItemSlot.id == 0:
                                #是，但是 id为0
                                continue
                    if typeSel==0x00:   #选择空位，过滤非空
                        emptySlotVar.set(1)
                        if dnfItemSlot.id != 0:
                            continue
                    if emptySlotVar.get()==0 and dnfItemSlot.id==0: #不显示空位，过滤空位
                        continue

                    if dnfItemSlot.typeZh in ['装备'] and dnfItemSlot.enhancementLevel>0:
                        name = f'+{dnfItemSlot.enhancementLevel} ' + name
                    #if dnfItemSlot.typeZh in ['消耗品','材料','任务材料','宠物消耗品','副职业']:
                    num = dnfItemSlot.num_grade
                    if dnfItemSlot.typeZh in ['装备']:
                        num = 1

                    values_unpack = [index,name,num,dnfItemSlot.id]
                    itemsTreev_now.insert('',tk.END,values=values_unpack)
                    CharacItemsDict[index] = dnfItemSlot
            set_treeview_color()
            self.w.after(1000,set_treeview_color)   #延迟1s再次检查，等待物品栏分析结果
        
        self.fillTreeFunctions[tabName] = refill_Tree_View
        self.editedItemsDict[tabName] = {}  #存储每个标签页正在编辑的物品
        self.itemInfoClrFuncs[tabName] = clear_item_Edit_Frame
        self.editFrameUpdateFuncs[tabName] = updateItemEditFrame
        self.tabNames.append(tabName)
        
        inventoryFrame = tk.Frame(tabView)
        inventoryFrame.pack(expand=True)
        tabView.add(inventoryFrame,text=tabName)
        padFrame = tk.Frame(inventoryFrame,width=3)   #控制treeview高度
        padFrame.grid(row=1,column=0,sticky='ns')
        invBowserFrame = tk.LabelFrame(inventoryFrame,text='当前物品列表')
        invBowserFrame.grid(row=1,column=1,sticky='ns',padx=2)
        if True:    #'当前物品列表'
            filterFrame = tk.Frame(invBowserFrame)
            filterFrame.pack(anchor=tk.E,fill=tk.X)
            if True:
                emptySlotVar = tk.IntVar()
                emptySlotVar.set(0)
                ttk.Checkbutton(filterFrame,text='显示空槽位',variable=emptySlotVar,command=refill_Tree_View).pack(side='left',padx=10)

                values = [f'0x{"%02x" % item[0]}-{item[1]}' for item in viewer.DnfItemSlot.typeDict.items()] +['0xff-全部']
                typeBox = ttk.Combobox(filterFrame,values=values,state='readonly',width=14,font=('', 10)) 
                typeBox.set('0xff-全部')
                typeBox.pack(side='right',padx=5)
                typeBox.bind('<<ComboboxSelected>>',refill_Tree_View)         
            treeViewFrame = tk.Frame(invBowserFrame)
            treeViewFrame.pack(anchor=tk.E,fill=tk.X)
            if True:
                #ttk.Separator(treeViewFrame, orient='horizontal').pack(side=tk.TOP,fill='x')
                padFrame = tk.Frame(treeViewFrame,height=324,width=4)   #控制treeview高度
                padFrame.pack(side=tk.LEFT,expand=True,fill='y')
                
                

                itemsTreev_now = ttk.Treeview(treeViewFrame, selectmode ='browse',height=10)
                itemsTreev_now.pack(side=tk.LEFT,fill='both',expand=True)
                if True:
                    itemsTreev_now.tag_configure('edited', background='lightblue')
                    itemsTreev_now.tag_configure('deleted', background='gray')
                    itemsTreev_now.tag_configure('error', background='red')
                    itemsTreev_now.tag_configure('unknow', background='yellow')
                    self.itemsTreevs_now[tabName] = itemsTreev_now
                    sbar1= tk.Scrollbar(treeViewFrame,bg='gray')
                    sbar1.pack(side=tk.RIGHT, fill=tk.Y)
                    sbar1.config(command =itemsTreev_now.yview)
                    itemsTreev_now.config(yscrollcommand=sbar1.set,xscrollcommand=sbar1.set)
                    config_TreeViev(itemsTreev_now,singleFunc=showSelectedItemInfo)

            blobFuncFrame = tk.Frame(inventoryFrame)
            blobFuncFrame.grid(row=2,column=1,sticky='ns')
            if True:
                exportBtn = ttk.Button(blobFuncFrame,text=f'导出字段',command=lambda:save_blob(globalBlobs_map[tabName]),width=15)
                exportBtn.grid(row=1,column=1,padx=5,pady=3)
                CreateToolTip(exportBtn,text='保存当前数据到文件')
                importBtn = ttk.Button(blobFuncFrame,text=f'导入字段',command=lambda:load_blob(globalBlobs_map[tabName]),width=15)
                importBtn.grid(row=1,column=2,padx=5,pady=3)
                CreateToolTip(importBtn,text='从文件导入数据并覆盖')
        
        ttk.Separator(inventoryFrame, orient='vertical').grid(row=1,column=2,rowspan=2,sticky='nswe')

        itemEditFrame = tk.LabelFrame(inventoryFrame,text='物品信息编辑')
        itemEditFrame.grid(row=1,column=3,sticky='nswe',padx=2)

        padx = 3
        pady = 1
        # 2
        row = 2
        itemSealVar = tk.IntVar()
        itemSealVar.set(1)
        itemSealBtn = ttk.Checkbutton(itemEditFrame,text='封装',variable=itemSealVar)
        itemSealBtn.grid(column=1,row=row,padx=padx,pady=pady)
        CreateToolTip(itemSealBtn,'无法封装的物品勾选会炸角色')
        itemNameEntry = ttk.Combobox(itemEditFrame,width=14,state='normal')
        itemNameEntry.bind('<Button-1>',searchItem)
        itemNameEntry.grid(column=2,row=row,sticky='we',padx=padx,pady=pady)
        itemNameEntry.bind("<<ComboboxSelected>>",lambda e:readSlotName('name'))
        CreateToolTip(itemNameEntry,textFunc=getItemPVFInfo)
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
        CreateToolTip(numEntry,'当为装备时，表示为品级\n数值与品级关系较为随机\n(0~4,294,967,295)')
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
        delBtn.grid(row=row,column=3,pady=pady,padx=padx,sticky='we')
        # 6
        row = 6
        tk.Label(itemEditFrame,text='锻造：').grid(column=1,row=row,padx=padx,pady=pady)
        forgingEntry = ttk.Spinbox(itemEditFrame,width=15,increment=1,from_=0, to=31)
        forgingEntry.grid(column=2,row=row,sticky='we',padx=padx,pady=pady)
        resetBtn = ttk.Button(itemEditFrame,text=' 重置 ',command=reset)
        resetBtn.grid(row=row,column=3,pady=pady,padx=padx,sticky='we')
        # 7 
        def enableTestFrame():
            viewer.config['TYPE_CHANGE_ENABLE'] = enableTypeChangeVar.get()
            print(viewer.config)
            json.dump(viewer.config,open(viewer.configPathStr,'w'),ensure_ascii=False)
            typeEntry.config(state='normal' if viewer.config.get('TYPE_CHANGE_ENABLE') == 1 else 'disable')

                
        row = 7
        enableTypeChangeVar = tk.IntVar()
        enableTypeChangeVar.set(viewer.config.get('TYPE_CHANGE_ENABLE'))
        enableTestBtn = ttk.Checkbutton(itemEditFrame,text=' 启用种类字段',variable=enableTypeChangeVar,command=enableTestFrame)
        enableTestBtn.grid(column=1,row=row,columnspan=2,sticky='w',padx=padx,pady=pady)
        tk.Label(itemEditFrame,text='种类:').grid(column=1,row=row,columnspan=2,sticky='e',padx=padx,pady=pady)
        typeEntry = ttk.Combobox(itemEditFrame,width=4,state='readonly',values=['1-装备','2-消耗品','3-材料','4-任务材料','5-宠物','6-宠物装备','7-宠物消耗品','10-副职业'])
        typeEntry.grid(column=3,row=row,sticky='we',padx=padx,pady=pady)
        typeEntry.bind('<<ComboboxSelected>>',changeItemSlotType)
        tip = '物品栏仅3-8可随意修改类型，否则炸角色\n'
        tip += '快捷栏：3 - 8\n' +\
            '装备栏：9 - 56\n' +\
            '消耗品：57 - 104\n' +\
            '材   料：105 - 152\n' +\
            '任务材料：153 - 200\n' +\
            '副职业：201 - 248\n' +\
            '宠物装备：0-48, 99-101\n' +\
            '宠物消耗品：49-97'

    
        CreateToolTip(typeEntry,tip)
        # 8 
        row = 8
        equipmentExFrame = tk.Frame(itemEditFrame)
        equipmentExFrame.grid(column=1,row=row,columnspan=3,sticky='we',padx=padx-1,pady=pady)
        padFrame  = tk.Frame(equipmentExFrame,width=287,height=0,borderwidth=0) #调整整体宽度
        padFrame.grid(row=0,column=1,columnspan=4)
        if True:
            # 8-1
            padx = 1
            row = 1
            tk.Label(equipmentExFrame,text='异界气息：').grid(column=1,row=row,padx=padx,pady=pady)
            otherworldEntry = ttk.Entry(equipmentExFrame,state='readonly',width=29)
            otherworldEntry.grid(column=2,row=row,columnspan=4,sticky='we',padx=padx,pady=pady)
            # 8-2
            row = 2
            tk.Label(equipmentExFrame,text=' 宝  珠：').grid(column=1,row=row,padx=padx,pady=pady)
            orbEntry = ttk.Entry(equipmentExFrame,state='readonly')
            orbEntry.grid(column=2,row=row,columnspan=4,sticky='we',padx=padx,pady=pady)
            # 8-3
            row = 3
            tk.Label(equipmentExFrame,text='魔法封印：').grid(column=1,row=row,padx=padx,pady=pady)
            #magicSealFrame = tk.Frame(testFrame)
            #magicSealFrame.grid(column=2,row=row,columnspan=2,sticky='we',padx=padx,pady=pady)

            forthSealEnable = tk.IntVar()
            forthSealEnable.set(1)
            forth = ttk.Checkbutton(equipmentExFrame,variable=forthSealEnable,text='第四词条',command=lambda:print(forthSealEnable.get()))
            forth.grid(column=2,row=row,columnspan=4,sticky='e')
            CreateToolTip(forth,'启用后无法使用游戏内魔法封印相关修改操作')
        
            magicSealEntrys = []
            magicSealIDEntrys = []
            magicSealLevelEntrys = []
            magicSealEntryWidth = 7
            def build_magic_view(row=4):
                magicSealEntry = ttk.Combobox(equipmentExFrame,state='normal',width=magicSealEntryWidth,values=list(viewer.magicSealDict.values()))
                magicSealIDEntry = ttk.Entry(equipmentExFrame,state='readonly',width=4)
                magicSealIDEntry.grid(column=3,row=row,sticky='we',padx=padx,pady=pady)
                magicSealLevelEntry = ttk.Spinbox(equipmentExFrame,state='normal',width=7,from_=0,to=65535)
                magicSealLevelEntry.grid(column=4,row=row,sticky='we',padx=padx,pady=pady,columnspan=2)
                magicSealEntry.bind('<Button-1>',lambda e:searchMagicSeal(magicSealEntry))
                magicSealEntry.bind('<<ComboboxSelected>>',lambda e:setMagicSeal(magicSealEntry,magicSealIDEntry))
                magicSealEntry.grid(column=1,row=row,sticky='we',padx=padx,pady=pady,columnspan=2)
                magicSealEntrys.append(magicSealEntry)
                magicSealIDEntrys.append(magicSealIDEntry)
                magicSealLevelEntrys.append(magicSealLevelEntry)
                CreateToolTip(magicSealLevelEntry,'词条数值，0-65535')
                self.updateMagicSealFuncs[tabName+str(row)] = lambda: magicSealEntry.config(values=list(viewer.magicSealDict.values()))

            for row in [4,5,6,7]:
                build_magic_view(row)
                
        btnFrame = tk.Frame(inventoryFrame)
        btnFrame.grid(row=2,column=3)
        if True:
            itemSlotBytesE = ttk.Entry(btnFrame,width=10)
            itemSlotBytesE.grid(row=2,column=2,padx=2)
            CreateToolTip(itemSlotBytesE,textFunc=lambda:'物品字节数据：'+itemSlotBytesE.get())
            def genBytes():
                slotBytes = editSave('bytes')
                itemSlotBytesE.delete(0,tk.END)
                itemSlotBytesE.insert(0,slotBytes.hex())
            genBytesBtn = ttk.Button(btnFrame,text='生成字节',command=genBytes,width=8)
            genBytesBtn.grid(row=2,column=1,padx=2)
            CreateToolTip(genBytesBtn,'根据物品槽数据编辑结果生成字节')

            def readBytes():
                itemBytes = str2bytes(itemSlotBytesE.get())
                updateItemEditFrame(viewer.DnfItemSlot(itemBytes))

            importBtn = ttk.Button(btnFrame,text='导入字节',command=readBytes,width=8)
            importBtn.grid(row=2,column=3,padx=2)
            CreateToolTip(importBtn,'读取字节，导入到编辑框\n用于物品复制')
            commitBtn = ttk.Button(btnFrame,text='提交修改',command=ask_commit,width=8)
            commitBtn.grid(row=2,column=4,pady=5)
            CreateToolTip(commitBtn,f'提交当前[{tabName}]页面的所有修改')

    def _buildtab_itemTab_2(self,tabView,tabName,treeViewArgs):
        def addDel(itemsTreev_now:ttk.Treeview,itemsTreev_del:ttk.Treeview):
            '''添加到删除列表'''
            selections = itemsTreev_now.selection()
            for selection in selections:
                values = itemsTreev_now.item(selection)['values']
                item = itemsTreev_del.insert('',tk.END,values=values)
                #itemsTreev_del.yview_moveto(1)
                itemsTreev_del.see(item)
        def removeDel(itemsTreev_del):
            '''从删除列表移除'''
            selections = itemsTreev_del.selection()
            for selection in selections:
                itemsTreev_del.delete(selection)
        
        def deleteItems(tabName,itemsTreev_del:ttk.Treeview):
            if not messagebox.askokcancel('删除确认',f'确定删除{tabName}所选物品？'):
                return False
            deleteIDs = []
            for child in itemsTreev_del.get_children():
                log(itemsTreev_del.item(child))
                deleteIDs.append(itemsTreev_del.item(child)['values'][0])

            if tabName in globalNonBlobs_map.keys():
                log('删除非BLOB')
                tableName = globalNonBlobs_map[tabName]
                for ui_id in deleteIDs:
                    if viewer.delNoneBlobItem(ui_id,tableName):
                        self.titleLog('====删除成功====\n')
                    else:
                        self.titleLog('====删除失败，请检查数据库连接状况====\n')
            self.selectCharac()
        def enableHidden(tabName,itemsTreev_del:ttk.Treeview):
            value =int(hiddenCom.get().split('-')[0])
            if not messagebox.askokcancel('提交确认',f'确定修改{tabName}所选物品？'):
                return False
            editIDS = []
            for child in itemsTreev_del.get_children():
                log(itemsTreev_del.item(child))
                editIDS.append(itemsTreev_del.item(child)['values'][0])
            if tabName in globalNonBlobs_map.keys():
                log('编辑非BLOB')
                tableName = globalNonBlobs_map[tabName]
                for ui_id in editIDS:
                    if viewer.enable_Hidden_Item(ui_id,tableName,value):
                        self.titleLog('====修改成功====\n')
                    else:
                        self.titleLog('====修改失败，请检查数据库连接状况====\n')
            self.selectCharac()
        def set_TreeView_Func(itemsTree_now:ttk.Treeview,itemsTree_edit:ttk.Treeview):
            def press(e,widget='now'):
                nonlocal x,y ,from_
                x = e.x
                y = e.y
                from_ = widget
            def release_Tree_now(e):
                nonlocal x,y 
                if abs(e.x-x)+abs(e.y-y)<10:
                    self.w.title('ctrl多选，shift连选，左右键拖拽或双击添加')
                elif itemsTree_now.winfo_width()*2 > e.x > itemsTree_now.winfo_width()+5 and 0<e.y < itemsTree_now.winfo_height():
                        addDel(itemsTree_now,itemsTree_edit)
            def release_Tree_edit(e):
                nonlocal x,y 
                if abs(e.x-x)+abs(e.y-y)<10:
                    self.w.title('ctrl多选，shift连选，左右键拖拽或双击移除')
                elif 0-itemsTree_edit.winfo_width() < e.x < 0  and 0<e.y < itemsTree_now.winfo_height():
                        removeDel(itemsTree_edit)


            x,y = 0, 0 #记录鼠标点击时的位置，与松开的位置进行判断
            from_ = 'now'   #用于记录拖拽时的源列表
            itemsTree_now.bind('<Double-1>',lambda e:addDel(itemsTree_now,itemsTree_edit))
            itemsTree_now.bind("<ButtonPress-1>",lambda e:press(e,'now'))
            itemsTree_now.bind("<ButtonRelease-1>",release_Tree_now)
            itemsTree_now.bind("<ButtonPress-3>",lambda e:press(e,'now'))
            itemsTree_now.bind("<ButtonRelease-3>",release_Tree_now)
            #itemsTree_now.bind("<B1-Motion>",move_items, add='+')

            itemsTree_edit.bind('<Double-1>',lambda e:removeDel(itemsTree_edit))
            itemsTree_edit.bind("<ButtonPress-1>",lambda e:press(e,'edit'))
            itemsTree_edit.bind("<ButtonRelease-1>",release_Tree_edit)
            itemsTree_edit.bind("<ButtonPress-3>",lambda e:press(e,'edit'))
            itemsTree_edit.bind("<ButtonRelease-3>",release_Tree_edit)
        def config_TreeViev(itemsTreev:ttk.Treeview):
            itemsTreev['columns'] = treeViewArgs['columns']
            itemsTreev['show'] = treeViewArgs['show']
            for columnID in treeViewArgs['columns']:
                itemsTreev.column(columnID,**treeViewArgs['column'][columnID])
                itemsTreev.heading(columnID,**treeViewArgs['heading'][columnID])


        inventoryFrame = tk.Frame(tabView)
        inventoryFrame.pack(expand=True)
        tabView.add(inventoryFrame,text=tabName)
        padFrame = tk.Frame(inventoryFrame,width=3)   #控制treeview高度
        padFrame.grid(row=1,column=0,sticky='ns')
        allInventoryFrame = tk.LabelFrame(inventoryFrame,text='当前物品列表')
        allInventoryFrame.grid(row=1,column=1,padx=2)

        padFrame = tk.Frame(allInventoryFrame,height=380,width=4)
        padFrame.grid(row=1,column=1,sticky='nswe')
        

        itemsTreev_now = ttk.Treeview(allInventoryFrame, height=12)
        itemsTreev_now.grid(row=1,column=2,rowspan=2,columnspan=2,sticky='nswe')
        self.itemsTreevs_now[tabName] = itemsTreev_now
        scrollBar= tk.Scrollbar(allInventoryFrame)
        scrollBar.grid(sticky='nse',column=4,row=1,rowspan=2)
        scrollBar.config(command =itemsTreev_now.yview)
        itemsTreev_now.config(yscrollcommand=scrollBar.set)

        ttk.Separator(inventoryFrame, orient='vertical').grid(row=1,column=2,rowspan=2,sticky='nswe')

        delInventoryFrame = tk.LabelFrame(inventoryFrame,text='待修改物品列表')
        delInventoryFrame.grid(row=1,column=3,sticky='ns',padx=2)
        itemsTreev_del = ttk.Treeview(delInventoryFrame, height=15)   # if tabName==' 宠物 ' else 13
        itemsTreev_del.grid(row=1,column=2,rowspan=2,columnspan=4,sticky='nswe',padx=5,pady=5)
        self.itemsTreevs_del[tabName] = itemsTreev_del

        config_TreeViev(itemsTreev_now)
        config_TreeViev(itemsTreev_del)
        set_TreeView_Func(itemsTreev_now,itemsTreev_del)

        def reselect(tabName):
            itemsTreev_del = self.itemsTreevs_del[tabName] 
            for child in itemsTreev_del.get_children():
                itemsTreev_del.delete(child)
        pady = 5
        resetBtn = ttk.Button(delInventoryFrame,text=' 重选 ',command=lambda:reselect(tabName),width=10 if tabName==' 宠物 ' else 8)
        resetBtn.grid(row=4,column=2,pady=pady)
        if '时装' in tabName:
            hiddenCom = ttk.Combobox(delInventoryFrame,values=['0-None']+[f'{i+1}-{value}' for i,value in enumerate(viewer.avatarHiddenList[0])],width=10)
            hiddenCom.grid(row=4,column=3,pady=pady)
            hiddenCom.set('0-None')
            self.hiddenCom = hiddenCom
            addHiddenBtn = ttk.Button(delInventoryFrame,text='开启潜能',command=lambda:enableHidden(tabName,itemsTreev_del),width=8)
            addHiddenBtn.grid(row=4,column=4,pady=pady)
        delBtn = ttk.Button(delInventoryFrame,text='确定删除',command=lambda:deleteItems(tabName,itemsTreev_del),width=10 if tabName==' 宠物 ' else 8)
        delBtn.grid(row=4,column=5,pady=pady)

    def _buildtab_charac(self,tabView,tabName):
        def clear_tab():
            '''清空角色信息页'''
            nameE.config(state='normal')
            nameE.delete(0,tk.END)
            levE.delete(0,tk.END)
            growTypeE.set('')
            jobE.set('')
            wakeFlgE.set(0)
        def commit():
            if not messagebox.askokcancel('修改确认',f'确定修改角色数据信息？\n请保证账号不在线或正在登陆其他角色'):
                return False
            cName = nameE.get()
            nameLen = len(cName.encode())
            if nameLen>20:
                cName = cName.encode()[:20].decode(errors='ignore')
                CreateOnceToolTip(nameE,'名字超长，自动裁切')
                nameE.delete(0,tk.END)
                nameE.insert(0,cName)
            lev = int(levE.get())
            job = int(jobE.get().split('-')[0])
            growType = int(growTypeE.get().split('-')[0])
            growType += int(wakeFlgE.get()) * 0x10
            kwDict = {
                'charac_name':cName,
                'job':job,
                'lev':lev,
                'grow_type':growType
            }
            viewer.set_charac_info(self.cNo,**kwDict)
            return True

        
        def fill_charac_tab():
            '''根据当前选中的cNo填充角色数据'''
            cName = self.characInfos[self.cNo].get('name')
            lev = self.characInfos[self.cNo].get('lev')
            job = self.characInfos[self.cNo].get('job')
            growType = self.characInfos[self.cNo].get('growType') % 16
            wakeFlg = self.characInfos[self.cNo].get('growType') // 16
            clear_tab()
            
            nameE.insert(0,cName)
            if viewer.ENCODE_ERROR:
                nameE.config(state='readonly')
            levE.insert(0,lev)
            jobE.set(f'{job}-{viewer.jobDict.get(job).get(0)}')
            set_grow_type()
            growTypeE.set(f'{growType}-{viewer.jobDict.get(job).get(growType)}')
            wakeFlgE.set(wakeFlg)


        self.clear_charac_tab_func = clear_tab
        self.fill_charac_tab_fun = fill_charac_tab
        self.cNo
        
        characMainFrame = tk.Frame(tabView)
        characMainFrame.pack(expand=True)
        
        tabView.add(characMainFrame,text=tabName)
        characEntriesAndGitHubFrame = tk.Frame(characMainFrame)
        characEntriesAndGitHubFrame.pack(padx=5,anchor='e',fill='x')
        if True:
            otherFunctionFrame = tk.LabelFrame(characEntriesAndGitHubFrame,text='其他功能')
            otherFunctionFrame.pack(padx=5,pady=5,side='left',expand=True,fill='both')
            btn = ttk.Button(otherFunctionFrame,text='生成一键启动器',command=ps.saveStart)
            btn.pack(expand=True)
            CreateToolTip(btn,'读取正在运行的DNF进程\n生成一键登录exe')

            characEntriesFrame = tk.Frame(characEntriesAndGitHubFrame)
            characEntriesFrame.pack(padx=5,pady=5,side='left')
            if True:
                padx=10
                pady=3
                row = 3
                entryWidth = 10
                tk.Label(characEntriesFrame,text='角色名：',width=entryWidth).grid(row=row,column=3,padx=padx,pady=pady)
                nameE = ttk.Entry(characEntriesFrame)#,state='readonly'
                nameE.grid(row=row,column=4,padx=padx,pady=pady,sticky='we')
                self.nameEditE = nameE
                #CreateToolTip(self.nameEditE,'编码出现错误时无法修改角色名')

                row+=1
                tk.Label(characEntriesFrame,text='角色等级：').grid(row=row,column=3,padx=padx,pady=pady)
                levE = ttk.Spinbox(characEntriesFrame,from_=1,to=999,width=entryWidth)
                levE.grid(row=row,column=4,padx=padx,pady=pady,sticky='we')
                row+=1
                def set_grow_type(e=None):
                    growTypeE.config(values=[f'{item[0]}-{item[1]}' for item in viewer.jobDict.get(int(jobE.get().split('-')[0])).items()])
                tk.Label(characEntriesFrame,text='职业：').grid(row=row,column=3,padx=padx,pady=pady)
                jobE = ttk.Combobox(characEntriesFrame,width=entryWidth,values=[f'{item[0]}-{item[1][0]}'  for item in viewer.jobDict.items()])
                jobE.grid(row=row,column=4,padx=padx,pady=pady,sticky='we')
                jobE.bind('<<ComboboxSelected>>',set_grow_type)
                self.jobE = jobE
                row+=1
                tk.Label(characEntriesFrame,text='成长类型：',width=entryWidth).grid(row=row,column=3,padx=padx,pady=pady)
                growTypeE = ttk.Combobox(characEntriesFrame)
                growTypeE.grid(row=row,column=4,padx=padx,pady=pady,sticky='we')
                row+=1
                tk.Label(characEntriesFrame,text='觉醒标识：',width=entryWidth).grid(row=row,column=3,padx=padx,pady=pady)
                wakeFlgE=ttk.Combobox(characEntriesFrame,state='readonly',values=[0,1])
                wakeFlgE.grid(row=row,column=4,padx=padx,pady=pady,sticky='we')
                row+=1
                ttk.Button(characEntriesFrame,text='提交修改',command=commit).grid(row=row,column=3,columnspan=2,sticky='nswe')
            GitHubFrame(characEntriesAndGitHubFrame).pack(padx=5,pady=5,side='right')

        adLabel = ImageLabel(characMainFrame,borderwidth=0)
        adLabel.pack(expand=True,fill='both',side='bottom')

        def loadPics():
            size = adLabel.winfo_width(), adLabel.winfo_height()
            if size[0] < 10:
                return self.w.after(100,loadPics)
            adLabel.loadDir(gifPath_2,size,root=self.w)
        self.w.after(100,loadPics)
        def reloadGif(e):
            if str(characMainFrame)==self.tabView.select():
                adLabel.randomShow()
        self.tabViewChangeFuncs.append(reloadGif)
                
    def open_advance_search_equipment(self):
        from titleBar import TitleBarFrame
        def start_Search():
            for child in searchResultTreeView.get_children():
                searchResultTreeView.delete(child)
            type1 = typeE.get().split('-')[-1]
            type2 = typeE2.get().split('-')[-1]
            type3 = typeE3.get().split('-')[-1]
            typeDict = {}   #存放搜索时物品的小分类（爪、头肩等）{id:type}
            if type1=='':
                searchDict = viewer.equipmentDict.copy()
            else:
                viewer.equipmentForamted[type1]
                if type1 in ['首饰','特殊装备']:
                    if type2=='':
                        searchDict = {}
                        for typeName,equDict in viewer.equipmentForamted[type1].items():
                            for id in equDict.keys():
                                typeDict[id] = typeName
                            searchDict.update(equDict)
                    else:
                        searchDict = viewer.equipmentForamted[type1][type2]
                        for id in viewer.equipmentForamted[type1][type2].keys():
                            typeDict[id] = type2
                else:
                    if type2=='':
                        searchDict = {}
                        for typeDict_ in viewer.equipmentForamted[type1].values():
                            for typeName,equDict in typeDict_.items():
                                searchDict.update(equDict)
                                for id in equDict.keys():
                                    typeDict[id] = typeName
                    else:
                        if type3=='':
                            searchDict = {}
                            for typeName,equDict in viewer.equipmentForamted[type1][type2].items():
                                searchDict.update(equDict)
                                for id in equDict.keys():
                                    typeDict[id] = typeName
                        else:
                            searchDict = viewer.equipmentForamted[type1][type2][type3]
                            for id in viewer.equipmentForamted[type1][type2][type3].keys():
                                typeDict[id] = type3
            res = []
            nameKey = nameE.get()
            usePVF = usePVFInfoVar.get()
            
            levMin = int(0 if minLevE.get()=='' else minLevE.get())
            levMax = int(999 if maxLevE.get()=='' else maxLevE.get())
            raritykey = rarityE.get()
            if nameKey!='':
                if usePVF:
                    for id in searchDict.keys():
                        searchDict[id] = searchDict[id] + '\n' + convert('\n'.join([str(info) for info in viewer.getItemInfo(id)[1]]),'zh-cn')
                useFuzzy = useFuzzyVar.get()
                searchList = viewer.searchItem(nameKey,list(searchDict.items()),fuzzy=useFuzzy)
            else:
                searchList = list(searchDict.items())
            if levMax==999 and levMin==0 and raritykey=='----':
                searchList = list(searchList)[:10000]

            for itemID,nameAndContent in searchList:
                segType,segments = viewer.getItemInfo(itemID)
                rarity = '' 
                lev = -1 
                for i in range(len(segments)-1):
                    if '时装' not in rarity and isinstance(segments[i],str) and 'avatar' in segments[i]:
                        rarity += '时装'
                    if segments[i] == '[minimum level]':
                        lev = segments[i+1]
                    elif segments[i] == '[rarity]':
                        rarity += rarityMap.get(segments[i+1])

                if lev==-1:
                    lev = 0
                if rarity=='':
                    rarity = '-'
                if typeDict!={}:
                    if raritykey!='----':
                        if raritykey in rarity  and  levMin <= lev <= levMax:
                            res.append([itemID,nameAndContent.split('\n')[0],typeDict.get(itemID),lev,rarity])
                    else:
                        if levMin <= lev <= levMax:
                            res.append([itemID,nameAndContent.split('\n')[0],typeDict.get(itemID),lev,rarity])
                else:
                    if raritykey!='----':
                        if raritykey in rarity and  levMin <= lev <= levMax:
                            res.append([itemID,nameAndContent.split('\n')[0],'',lev,rarity])
                    else:
                        if levMin <= lev <= levMax:
                            res.append([itemID,nameAndContent.split('\n')[0],'',lev,rarity])
            for item in res:
                try:
                    searchResultTreeView.insert('',tk.END,values=item)
                except:
                    break

        

        def apply_Search_result():
            try:
                frame_id = int(self.tabView.select()[-1])-2
            except:#首标签末尾无数字
                return False
            values = searchResultTreeView.item(searchResultTreeView.focus())['values']
            itemID,name,type_,lev,rarity = values
            if '时装' in rarity:
                titleFrame.title_label.config(text='[错误]时装无法放至物品栏！')
                #return False
            if frame_id > len(self.tabNames):
                return False
            itemSlot = viewer.DnfItemSlot(b'\x00'*61)
            itemSlot.id = itemID
            itemSlot.type = 0x01
            itemSlot.durability = 999
            itemSlot.oriBytes = itemSlot.build_bytes()
            self.editFrameUpdateFuncs[self.tabNames[frame_id]](itemSlot)
            self.w.focus_force()

        def quitSearch():
            self.Advance_Search_State_FLG=False

        if self.Advance_Search_State_FLG==True:
            return False
        self.Advance_Search_State_FLG = True
        advanceSearchMainFrame = tk.Toplevel(self.advanceSearchBtn)
        advanceSearchMainFrame.wm_attributes('-topmost', 1)
        advanceSearchMainFrame.wm_overrideredirect(1)
        advanceSearchMainFrame.wm_geometry("+%d+%d" % (self.advanceSearchBtn.winfo_rootx(), self.advanceSearchBtn.winfo_rooty()))
        titleFrame = TitleBarFrame(advanceSearchMainFrame,advanceSearchMainFrame,'装备专用搜索',closeFunc=quitSearch)
        titleFrame.pack(fill=tk.X,expand=1,anchor=tk.N)  
        advanceSearchFrame = titleFrame.innerFrame
        advanceSearchFrame.pack()

        row = 1
        tk.Label(advanceSearchFrame,text='关键词：').grid(row=row,column=3)
        nameE = ttk.Entry(advanceSearchFrame,width=10)
        nameE.grid(row=row,column=4,sticky='we')

        row += 1
        useFuzzyVar = tk.IntVar()
        useFuzzyVar.set(0)
        useFuzzyBtn = ttk.Checkbutton(advanceSearchFrame,text='启用模糊搜索',variable=useFuzzyVar,command=lambda:useFuzzyVar.get())
        useFuzzyBtn.grid(row=row,column=4,sticky='we')
        CreateToolTip(useFuzzyBtn,text='会花费更多时间')

        row += 1
        usePVFInfoVar = tk.IntVar()
        usePVFInfoVar.set(0)
        usePVFInfoBtn = ttk.Checkbutton(advanceSearchFrame,text='搜索PVF文本',variable=usePVFInfoVar,command=lambda:usePVFInfoVar.get())
        usePVFInfoBtn.grid(row=row,column=4,sticky='we')
        CreateToolTip(usePVFInfoBtn,text='同时在PVF文本内搜索关键词')

        row += 1
        def setType2(e):
            type1 = typeE.get()
            if type1!=ALLTYPE:
                typeE2.config(values=[ALLTYPE]+list(viewer.equipmentForamted[type1].keys()),state='readonly')
            else:
                typeE2.config(values=[],state='disable')
                typeE3.config(values=[],state='disable')
            typeE2.set(ALLTYPE)
            typeE3.set(ALLTYPE)
        def setType3(e):
            type1 = typeE.get()
            type2 = typeE2.get()
            if type2!=ALLTYPE and type1 not in ['首饰','特殊装备']:
                typeE3.config(values=[ALLTYPE]+list(viewer.equipmentForamted[type1][type2].keys()),state='readonly')
            else:
                typeE3.config(values=[],state='disable')
            typeE3.set(ALLTYPE)

        tk.Label(advanceSearchFrame,text='大类：').grid(row=row,column=3)
        ALLTYPE = '----'
        typeE = ttk.Combobox(advanceSearchFrame,width=10,values=[ALLTYPE,*viewer.equipmentForamted.keys()],state='readonly')
        typeE.set(ALLTYPE)
        typeE.bind('<<ComboboxSelected>>',setType2)
        typeE.grid(row=row,column=4,sticky='we')
        row += 1
        tk.Label(advanceSearchFrame,text='小类：').grid(row=row,column=3)
        typeE2 = ttk.Combobox(advanceSearchFrame,width=10,state='disable')
        typeE2.bind('<<ComboboxSelected>>',setType3)
        typeE2.grid(row=row,column=4,sticky='we')
        row += 1
        tk.Label(advanceSearchFrame,text='子类：').grid(row=row,column=3)
        typeE3 = ttk.Combobox(advanceSearchFrame,width=10,state='disable')
        typeE3.grid(row=row,column=4,sticky='we')
        row += 1
        tk.Label(advanceSearchFrame,text='稀有度：').grid(row=row,column=3)
        rarityE = ttk.Combobox(advanceSearchFrame,values=['----',*list(rarityMapRev.keys())],width=10,state='readonly')
        rarityE.set('----')
        rarityE.grid(row=row,column=4,sticky='we')
        row += 1
        tk.Label(advanceSearchFrame,text='等级：').grid(row=row,column=3)
        minLevE = ttk.Spinbox(advanceSearchFrame,from_=0,to=999,width=4)
        minLevE.grid(row=row,column=4,sticky='w')
        tk.Label(advanceSearchFrame,text='-').grid(row=row,column=4)
        maxLevE = ttk.Spinbox(advanceSearchFrame,from_=0,to=999,width=4)
        maxLevE.grid(row=row,column=4,sticky='e')
        row += 1
        btnFrame = tk.Frame(advanceSearchFrame)
        btnFrame.grid(row=row,column=3,columnspan=2,sticky='ns',pady=5)
        ttk.Button(btnFrame,text='查询',command=start_Search).grid(row=row,column=3)
        ttk.Button(btnFrame,text='提交',command=apply_Search_result).grid(row=row,column=4)  
        padFrame = tk.Frame(advanceSearchFrame)
        padFrame.grid(row=1,column=2,sticky='nswe',padx=2)
        padFrame = tk.Frame(advanceSearchFrame)
        padFrame.grid(row=1,column=7,sticky='nswe',padx=2)

        treeViewArgs = {
        "columns":['1','2','3','4','5'],
        'show':'headings',
        'column':{
            '1':{'width':50, 'anchor':'c'},
            '2':{'width':200, 'anchor':'c'},
            '3':{'width':50, 'anchor':'c'},
            '4':{'width':40, 'anchor':'c'},
            '5':{'width':60, 'anchor':'c'},
            },
        'heading':{
            '1':{'text':'物品ID'},
            '2':{'text':'物品名'},
            '3':{'text':'种类'},
            '4':{'text':'等级'},
            '5':{'text':'稀有度'},
        }
    }

        searchResultTreeView = ttk.Treeview(advanceSearchFrame)
        searchResultTreeView['columns'] = treeViewArgs['columns']
        searchResultTreeView['show'] = treeViewArgs['show']
        for columnID in treeViewArgs['columns']:
            searchResultTreeView.column(columnID,**treeViewArgs['column'][columnID])
            searchResultTreeView.heading(columnID,**treeViewArgs['heading'][columnID])
        '''searchResultTreeView.bind('<Double-1>',lambda e:...)
        searchResultTreeView.bind("<Button-1>",lambda e:...)'''
        searchResultTreeView.grid(row=1,column=8,rowspan=10)
        scrollBar= tk.Scrollbar(advanceSearchFrame)
        scrollBar.grid(sticky='nse',row=1,column=9,rowspan=10)
        scrollBar.config(command =searchResultTreeView.yview)
        searchResultTreeView.config(yscrollcommand=scrollBar.set)
        def show_overview(e):
            nonlocal overViewTip
            x = searchResultTreeView.winfo_rootx() + e.x + 25
            y = searchResultTreeView.winfo_rooty() + e.y + 5
            overViewTip.hide_tip()
            values = searchResultTreeView.item(searchResultTreeView.focus())['values']
            if len(values)==0: return False
            itemID = int(values[0])
            _,segments = viewer.getItemInfo(itemID)
            res = ' '.join([str(item).strip() for item in segments]).replace('[','\n[').replace(']',']\n    ').replace('     \n','').replace(r'%%',r'%').replace(r'\n\n',r'\n').strip()
            try:
                res = convert(res,'zh-cn')
            except:
                pass
            overViewTip = CreateOnceToolTip(searchResultTreeView,text=res,xy=[x,y])
            titleFrame.title_label.config(text='点击提交将已选结果提交至物品编辑栏')

        searchResultTreeView.bind("<Button-1>",lambda e:self.w.after(100,lambda:show_overview(e)))
        overViewTip:ToolTip = CreateOnceToolTip(searchResultTreeView)
        
    def open_advance_search_stackable(self):
        from titleBar import TitleBarFrame
        def start_Search():
            for child in searchResultTreeView.get_children():
                searchResultTreeView.delete(child)
            typeDict = {}   #存放搜索时物品的小分类（爪、头肩等）{id:type}

            searchDict = viewer.stackableDict.copy()
            
            res = []
            nameKey = nameE.get()
            usePVF = usePVFInfoVar.get()
            type = typeE.get()
            #print(type,viewer.formatedTypeDict.get(type).values())
            levMin = int(0 if minLevE.get()=='' else minLevE.get())
            levMax = int(999 if maxLevE.get()=='' else maxLevE.get())
            raritykey = rarityE.get()
            print(usePVF)
            if nameKey!='':
                if usePVF:
                    for id in searchDict.keys():
                        searchDict[id] = searchDict[id] + '\n' + convert('\n'.join([str(info) for info in viewer.getItemInfo(id)[1]]),'zh-cn')
                useFuzzy = useFuzzyVar.get()
                searchList = viewer.searchItem(nameKey,list(searchDict.items()),fuzzy=useFuzzy)
            else:
                searchList = list(searchDict.items())
            if levMax==999 and levMin==0 and raritykey=='----':
                searchList = list(searchList)[:10000]

            for itemID,nameAndContent in searchList:
                segType,segments = viewer.getItemInfo(itemID)
                rarity = '' 
                lev = -1 
                for i in range(len(segments)-1):
                    if segments[i] == '[minimum level]':
                        lev = segments[i+1]
                    elif segments[i] == '[rarity]':
                        rarity += rarityMap.get(segments[i+1])
                    elif segments[i] == '[stackable type]':
                        typeDict[itemID] = segments[i+1].replace('[','').replace(']','')
                if type!='----' and typeDict[itemID] not in viewer.formatedTypeDict[type].keys():
                    continue

                resType = viewer.typeDict.get(typeDict.get(itemID))
                if resType is not None:     #转换为中文，没有记录则显示原文
                    resType = resType[1]
                else:
                    resType = typeDict[itemID]
                if lev==-1:
                    lev = 0
                if rarity=='':
                    rarity = '-'
                if raritykey!='----':
                    if raritykey in rarity  and  levMin <= lev <= levMax:
                        res.append([itemID,nameAndContent.split('\n')[0],resType,lev,rarity])
                else:
                    if levMin <= lev <= levMax:
                        res.append([itemID,nameAndContent.split('\n')[0],resType,lev,rarity])

            for item in res:
                try:
                    searchResultTreeView.insert('',tk.END,values=item)
                except:
                    break

        def apply_Search_result():
            try:
                frame_id = int(self.tabView.select()[-1])-2
            except:#首标签末尾无数字
                return False
            values = searchResultTreeView.item(searchResultTreeView.focus())['values']
            itemID,name,type_,lev,rarity = values
            typeID,itemTypeZh = viewer.getStackableTypeMainIdAndZh(itemID)
            
            if frame_id > len(self.tabNames):
                return False
            itemSlot = viewer.DnfItemSlot(b'\x00'*61)
            itemSlot.id = itemID
            itemSlot.type = typeID
            itemSlot.durability = 0
            itemSlot.num_grade = 1
            itemSlot.oriBytes = itemSlot.build_bytes()
            self.editFrameUpdateFuncs[self.tabNames[frame_id]](itemSlot)
            self.w.focus_force()
            self.w.title('本地物品信息已修改，请注意种类与位置是否匹配')

        def quitSearch():
            self.Advance_Search_State_FLG_Stackable=False

        if self.Advance_Search_State_FLG_Stackable==True:
            return False
        self.Advance_Search_State_FLG_Stackable = True
        advanceSearchMainFrame = tk.Toplevel(self.advanceSearchBtn)
        advanceSearchMainFrame.wm_attributes('-topmost', 1)
        advanceSearchMainFrame.wm_overrideredirect(1)
        advanceSearchMainFrame.wm_geometry("+%d+%d" % (self.advanceSearchBtn.winfo_rootx(), self.advanceSearchBtn.winfo_rooty()))
        titleFrame = TitleBarFrame(advanceSearchMainFrame,advanceSearchMainFrame,'道具专用搜索',closeFunc=quitSearch)
        titleFrame.pack(fill=tk.X,expand=1,anchor=tk.N)  
        advanceSearchFrame = titleFrame.innerFrame
        advanceSearchFrame.pack()

        row = 1
        tk.Label(advanceSearchFrame,text='关键词：').grid(row=row,column=3)
        nameE = ttk.Entry(advanceSearchFrame,width=10)
        nameE.grid(row=row,column=4,sticky='we')

        row += 1
        useFuzzyVar = tk.IntVar()
        useFuzzyVar.set(0)
        useFuzzyBtn = ttk.Checkbutton(advanceSearchFrame,text='启用模糊搜索',variable=useFuzzyVar,command=lambda:useFuzzyVar.get())
        useFuzzyBtn.grid(row=row,column=4,sticky='we')
        CreateToolTip(useFuzzyBtn,text='会花费更多时间')

        row += 1
        usePVFInfoVar = tk.IntVar()
        usePVFInfoVar.set(0)
        usePVFInfoBtn = ttk.Checkbutton(advanceSearchFrame,text='搜索PVF文本',variable=usePVFInfoVar,command=lambda:usePVFInfoVar.get())
        usePVFInfoBtn.grid(row=row,column=4,sticky='we')
        CreateToolTip(usePVFInfoBtn,text='同时在PVF文本内搜索关键词')

        row += 1
        tk.Label(advanceSearchFrame,text='分类：').grid(row=row,column=3)
        ALLTYPE = '----'
        typeE = ttk.Combobox(advanceSearchFrame,width=10,values=[ALLTYPE,*viewer.formatedTypeDict.keys()],state='readonly')
        typeE.set(ALLTYPE)
        typeE.grid(row=row,column=4,sticky='we')
        

        row += 1
        tk.Label(advanceSearchFrame,text='稀有度：').grid(row=row,column=3)
        rarityE = ttk.Combobox(advanceSearchFrame,values=['----',*list(rarityMapRev.keys())],width=10,state='readonly')
        rarityE.set('----')
        rarityE.grid(row=row,column=4,sticky='we')
        row += 1
        tk.Label(advanceSearchFrame,text='等级：').grid(row=row,column=3)
        minLevE = ttk.Spinbox(advanceSearchFrame,from_=0,to=999,width=4)
        minLevE.grid(row=row,column=4,sticky='w')
        tk.Label(advanceSearchFrame,text='-').grid(row=row,column=4)
        maxLevE = ttk.Spinbox(advanceSearchFrame,from_=0,to=999,width=4)
        maxLevE.grid(row=row,column=4,sticky='e')
        row += 1
        btnFrame = tk.Frame(advanceSearchFrame)
        btnFrame.grid(row=row,column=3,columnspan=2,sticky='ns',pady=5)
        ttk.Button(btnFrame,text='查询',command=start_Search).grid(row=row,column=3)
        ttk.Button(btnFrame,text='提交',command=apply_Search_result).grid(row=row,column=4)  
        padFrame = tk.Frame(advanceSearchFrame)
        padFrame.grid(row=1,column=2,sticky='nswe',padx=2)
        padFrame = tk.Frame(advanceSearchFrame)
        padFrame.grid(row=1,column=7,sticky='nswe',padx=2)

        treeViewArgs = {
        "columns":['1','2','3','4','5'],
        'show':'headings',
        'column':{
            '1':{'width':50, 'anchor':'c'},
            '2':{'width':200, 'anchor':'c'},
            '3':{'width':70, 'anchor':'c'},
            '4':{'width':40, 'anchor':'c'},
            '5':{'width':60, 'anchor':'c'},
            },
        'heading':{
            '1':{'text':'物品ID'},
            '2':{'text':'物品名'},
            '3':{'text':'种类'},
            '4':{'text':'等级'},
            '5':{'text':'稀有度'},
        }
    }

        searchResultTreeView = ttk.Treeview(advanceSearchFrame)
        searchResultTreeView['columns'] = treeViewArgs['columns']
        searchResultTreeView['show'] = treeViewArgs['show']
        for columnID in treeViewArgs['columns']:
            searchResultTreeView.column(columnID,**treeViewArgs['column'][columnID])
            searchResultTreeView.heading(columnID,**treeViewArgs['heading'][columnID])
        '''searchResultTreeView.bind('<Double-1>',lambda e:...)
        searchResultTreeView.bind("<Button-1>",lambda e:...)'''
        searchResultTreeView.grid(row=1,column=8,rowspan=10)
        scrollBar= tk.Scrollbar(advanceSearchFrame)
        scrollBar.grid(sticky='nse',row=1,column=9,rowspan=10)
        scrollBar.config(command =searchResultTreeView.yview)
        searchResultTreeView.config(yscrollcommand=scrollBar.set)
        def show_overview(e):
            nonlocal overViewTip
            x = searchResultTreeView.winfo_rootx() + e.x + 25
            y = searchResultTreeView.winfo_rooty() + e.y + 5
            overViewTip.hide_tip()
            values = searchResultTreeView.item(searchResultTreeView.focus())['values']
            if len(values)==0: return False
            itemID = int(values[0])
            _,segments = viewer.getItemInfo(itemID)
            res = ' '.join([str(item).strip() for item in segments]).replace('[','\n[').replace(']',']\n    ').replace('     \n','').replace(r'%%',r'%').replace(r'\n\n',r'\n').strip()
            try:
                res = convert(res,'zh-cn')
            except:
                pass
            overViewTip = CreateOnceToolTip(searchResultTreeView,text=res,xy=[x,y])
            titleFrame.title_label.config(text='点击提交将已选结果提交至物品编辑栏')

        searchResultTreeView.bind("<Button-1>",lambda e:self.w.after(100,lambda:show_overview(e)))
        overViewTip:ToolTip = CreateOnceToolTip(searchResultTreeView)

    def build_GUI(self,w):  
        def tabView_Chance_Handler(e):
            for func in self.tabViewChangeFuncs:
                func(e)

        mainFrame = tk.Frame(w)
        mainFrame.pack(fill='both')
        self.mainFrame = mainFrame
        self._buildSqlConn(mainFrame)

        tabFrame = tk.Frame(mainFrame,borderwidth=0)
        tabFrame.pack(expand=True,fill='both')
        tabView = ttk.Notebook(tabFrame,padding=[-3,0,-3,-3])
        tabView.grid(row=1,column=1,sticky='nswe')
        tabView.bind('<<NotebookTabChanged>>',tabView_Chance_Handler)
        advanceSearchBtn = tk.Button(tabFrame,text='装备专用搜索', relief=tk.FLAT,font=('', 10, 'underline'),command=self.open_advance_search_equipment)
        self.advanceSearchBtn = advanceSearchBtn
        advanceSearchBtn.grid(row=1,column=1,sticky='ne',padx=5)

        advanceSearchBtn2 = tk.Button(tabFrame,text='道具专用搜索', relief=tk.FLAT,font=('', 10, 'underline'),command=self.open_advance_search_stackable)
        self.advanceSearchBtn2 = advanceSearchBtn2
        advanceSearchBtn2.grid(row=1,column=1,sticky='ne',padx=100)

        self.refreshBtn = tk.Button(tabFrame,text='刷新背包', relief=tk.FLAT,font=('', 10, 'underline'))
        self.refreshBtn.grid(row=1,column=1,sticky='ne',padx=200)
        self.tabView = tabView
        
        self._buildtab_main(tabView)

        self.itemsTreevs_now = {}
        self.itemsTreevs_del = {}

        treeViewArgs = {
            "columns":['1','2','3','4'],
            'show':'headings',
            'column':{
                '1':{'width':30, 'anchor':'c'},
                '2':{'width':138, 'anchor':'se'},
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
                '2':{'width':128, 'anchor':'se'},
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
        tabName = ' 宠物 '
        self._buildtab_itemTab_2(tabView,tabName,treeViewArgs)

        treeViewArgs = {
            "columns":['1','2','3'],
            'show':'headings',
            'column':{
                '1':{'width':60, 'anchor':'c'},
                '2':{'width':128, 'anchor':'se'},
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
        tabName = ' 时装 '
        self._buildtab_itemTab_2(tabView,tabName,treeViewArgs)
        self._buildtab_charac(tabView,' 角色 ')

    def connectSQL(self):
        def inner():
            config = viewer.config
            config['DB_IP'] = self.db_ip.get()
            config['DB_PORT'] = int(self.db_port.get())
            config['DB_USER'] = self.db_user.get()
            config['DB_PWD'] = self.db_pwd.get()
            config['PVF_PATH'] = viewer.config.get('PVF_PATH')
            log(str(config))
            viewer.config = config
            sqlresult = viewer.connect(self.titleLog)
            if '失败' not in sqlresult:  
                self.accountBtn.config(state='normal')
                self.characBtn.config(state='normal')
                self.connectorE.config(values=[f'{i}-'+str(connector['account_db']) for i,connector in enumerate(viewer.connectorAvailuableDictList)])
                self.connectorE.set(f"0-{viewer.connectorAvailuableDictList[0]['account_db']}")
            self.titleLog(sqlresult)
            self.db_conBTN.config(text='重新连接',state='normal')
            CreateToolTip(self.db_conBTN,'重新连接数据库并加载在线角色列表')
            self.CONNECT_FLG = False
            onlineCharacs = viewer.get_online_charac()
            self.fillCharac(onlineCharacs)
            self.titleLog(f'当前在线角色已加载({len(onlineCharacs)})')
        if self.CONNECT_FLG == False:
            self.db_conBTN.config(state='disable')
            self.CONNECT_FLG = True
            self.titleLog('正在连接数据库...')
            t = threading.Thread(target=inner)
            t.start()
    
    def enable_Tabs(self):
        '''启用上方tab'''
        for i in range(1,len(globalBlobs_map.keys()) + 2 + len(globalNonBlobs_map.keys())):
            self.tabView.tab(i,state='normal')

    def disable_Tabs(self):
        '''禁用上方tab'''
        if DEBUG: return False
        for i in range(1,len(globalBlobs_map.keys()) + 2 + len(globalNonBlobs_map.keys())):
            self.tabView.tab(i,state='disable')
    

if __name__=='__main__':
    a = App()    
    a.connectSQL()
    def print2title(*args):
        for arg in args:
            print(arg)
            a.titleLog(str(arg))
    viewer.pvfReader.print = print2title
    viewer.print = print2title
    ps.print = print2title
    a.w.resizable(False,False)
    #a.w.after(3000,viewer.get_online_charac)
    a.w.mainloop()
    for connector in viewer.connectorAvailuableDictList:
        for item in connector.values():
            try:
                item.close()
            except:
                pass
