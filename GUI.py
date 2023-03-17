import cacheManager as cacheM
from cacheManager import config
import updateManager as updateM
import sqlManager2 as sqlM
import tkinter as tk
from tkResize import get_tk_size_dict,regen_size_dict,set_tk_size
from tkinter import ttk, messagebox, font
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
from titleBar import TitleBarFrame
import ps
DEBUG = True
VerInfo = cacheM.config['VERSION']#'Ver.0.2.23'
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

expert_jobMap={
    0:'无职业',
    1:'附魔师',
    2:'炼金术师',
    3:'分解师',
    4:'控偶师'
}

globalBlobs_map = {
        '物品栏':'inventory',
        '穿戴栏':'equipslot',
        '宠物栏':'creature',
        ' 仓库 ':'cargo'
    }
globalNonBlobs_map = {
    ' 宠物 ':'creature_items',
    ' 时装 ':'user_items',
    ' 邮件 ':'user_postals'
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

def openWeb(e=None):
    import webbrowser
    webbrowser.open(cacheM.config['NET_DISK'])
    webbrowser.open(cacheM.config['GITHUB'])

class GitHubFrame(tk.Frame):
    def __init__(self,*args,**kw):
        tk.Frame.__init__(self,*args,**kw)
        gitHubLogo = ImageLabel(self)
        gitHubLogo.pack()
        para = min(WIDTH,HEIGHT)
        gitHubLogo.load(gitHubLogoPath,[int(150*para),int(150*para)])
        CreateToolTip(self,f'点击查看更新，当前版本：{updateM.local_version}')
        gitHubLogo.bind('<Button-1>',openWeb)

PADX = 1
PADY = 1
WIDTH,HEIGHT = cacheM.config['SIZE']

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
        if HEIGHT!=1:
            w.defaultFont = font.nametofont("TkDefaultFont")
            w.defaultFont.configure(family="黑体",size=int(3*(HEIGHT-1.3)+11.5),)#
            ttk.Style().configure("TEntry", padding=6, relief="flat",background="#ccc",font=("黑体",int(3*(HEIGHT-1.3)+11.5)))
            ttk.Style().configure("TCombobox", padding=6, relief="flat",background="#ccc",font=("黑体",int(3*(HEIGHT-1.3)+11.5)))
            ttk.Style().configure("TSpinbox", padding=6, relief="flat",background="#ccc",font=("黑体",int(3*(HEIGHT-1.3)+11.5)))
                                               
                                   
        self.titleLog = lambda text:[w.title(text),log(text)]
        w.iconbitmap(IconPath)
        
        self.CONNECT_FLG = False #判断正在连接
        self.PVF_LOAD_FLG = False #判断正在加载pvf
        self.Advance_Search_State_FLG = False #判断高级搜索是否打开
        self.Advance_Search_State_FLG_Stackable = False
        self.GM_Tool_Flg = False    #判断GM工具是否打开
        self.currentItemDict = {}
        self.editedItemsDict = {}
        self.itemInfoClrFuncs = {}
        self.selectedCharacItemsDict = {}   #使用tabName存储id:ItemSlot
        self.fillTreeFunctions = {}
        self.updateMagicSealFuncs = {}
        self.editFrameUpdateFuncs = {}
        self.globalCharacBlobs = {} #利用标签页名字来存储原始blob
        self.globalCharacNonBlobs = {} #利用标签页名字来存储原始非blob
        self.unknowItemsListDict = {}
        self.errorItemsListDict = {}
        self.errorInfoDict = {}
        self.importFlgDict = {} #保存导入过的标签页名
        self.orbTypeEList = []

        self.tabViewChangeFuncs = []    #切换tab时执行的function列表
        self.tabNames = []
        self.cNo=0
        self.cName = ''
        self.lev = 0
        self.characInfos = {}
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
        self.positionDict = positionDict
        self.pool = None
        self.build_GUI(self.w)
        
    def _buildSqlConn(self,mainFrame):
        #数据库连接
        db_conFrame = tk.Frame(mainFrame)
        tk.Label(db_conFrame,text='  数据库IP ').grid(row=0,column=1)
        db_ip = ttk.Entry(db_conFrame,width=int(WIDTH*15))
        db_ip.grid(row=0,column=2,pady=PADY*5)
        db_ip.insert(0,config['DB_IP'])
        tk.Label(db_conFrame,text='  端口 ').grid(row=0,column=3)
        db_port = ttk.Entry(db_conFrame,width=int(WIDTH*8))
        db_port.insert(0,config['DB_PORT'])
        db_port.grid(row=0,column=4)
        tk.Label(db_conFrame,text='  用户名 ').grid(row=0,column=5)
        db_user = ttk.Entry(db_conFrame,width=int(WIDTH*8))
        db_user.insert(0,config['DB_USER'])
        db_user.grid(row=0,column=6)
        tk.Label(db_conFrame,text='  密码 ').grid(row=0,column=7)
        db_pwd = ttk.Entry(db_conFrame,width=int(WIDTH*8))#,show='*'
        db_pwd.insert(0,config['DB_PWD'])
        db_pwd.grid(row=0,column=8)
        db_conBTN = ttk.Button(db_conFrame,text='连接',command=self.connectSQL)
        db_conBTN.grid(row=0,column=9,padx=PADX*12,pady=PADY*5)
        
        
        db_conFrame.pack()
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
                uid,cNo,name,lev,job,growType,deleteFlag,expert_job = values
                jobDict = cacheM.jobDict.get(job)
                if isinstance(jobDict,dict):
                    jobNew = jobDict.get(growType % 16)
                else:
                    jobNew = growType % 16
                self.characTreev.insert('',tk.END,values=[cNo,name,lev,jobNew,uid],tags='deleted' if deleteFlag==1 else '')
                self.characInfos[cNo] = {'uid':uid,'name':name,'lev':lev,'job':job,'growType':growType,'expert_job':expert_job} 
            encodeE.set(f'{sqlM.sqlEncodeUseIndex}-{sqlM.SQL_ENCODE_LIST[sqlM.sqlEncodeUseIndex]}')
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
                characs = sqlM.getCharactorInfo(uid=sqlM.getUID(self.accountE.get()))
                try:
                    uid = int(self.accountE.get())
                    characs_uid = sqlM.getCharactorInfo(uid=uid)
                    characs += characs_uid
                except:
                    pass
                
            else:
                if self.characE.get()=='':
                    characs = sqlM.get_online_charac()
                else:
                    characs = sqlM.getCharactorInfo(cName=self.characE.get())
            print(characs)
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
            if len(cacheM.ITEMS_dict.keys())<10:
                self.titleLog(f'请选择物品列表来源')
                return False
            log(f'加载角色物品[{sel}]')
            inventory, equipslot, creature = sqlM.getInventoryAll(cNo=cNo)[0]
            cargo,jewel,expand_equipslot = sqlM.getCargoAll(cNo=cNo)[0]
            creature_items = sqlM.getCreatureItem(cNo=cNo)
            user_items = sqlM.getAvatar(cNo=cNo)
            user_postals = sqlM.get_postal(cNo=cNo)
            print(user_postals)
            if showTitle:
                self.titleLog(f'角色[{cName}]物品已加载')
            else:
                log(f'角色[{cName}]物品已加载')
            self.enable_Tabs()
            blobsItemsDict = {}
            for key,name in globalBlobs_map.items():
                blobsItemsDict[key] = locals()[name]
            self.globalCharacBlobs = blobsItemsDict

            nonBlobItemsDict = {}
            for key,name in globalNonBlobs_map.items():
                nonBlobItemsDict[key] = locals().get(name)
            self.cNo = cNo
            self.cName = cName
            self.lev = lev
            self.globalCharacNonBlobs = nonBlobItemsDict
            self.importFlgDict = {}
            self.fill_tab_treeviews()
            self.fill_charac_tab_fun()
            if self.GM_Tool_Flg:    #同步修改角色
                self.GMTool.cNo = cNo
                self.GMTool.update_Info()
                self.GMTool.title(self.cName)

        def setItemSource(sourceVar:tk.IntVar,pvfPath:str='',pvfMD5=''):
            '''设置物品来源，读取pvf或者csv'''
            if pvfMD5!='':
                sourceVar.set(1)
            source = sourceVar.get()
            #self.disable_Tabs()
            print('数据源加载中...PVF：',sourceVar.get(),pvfPath,pvfMD5)
            if source==1 and not self.PVF_LOAD_FLG:
                if pvfMD5!='':
                    self.titleLog('加载PVF缓存中...')
                    
                    self.PVF_LOAD_FLG = True
                    info = cacheM.loadItems2(True,MD5=pvfMD5)
                    self.PVF_LOAD_FLG = False
                    self.titleLog(f'{info}... {cacheM.tinyCache[pvfMD5].get("nickName")}')
                    if '错误' in info:
                        sourceVar.set(0)
                    else:
                        pvfComboBox.set(f'{cacheM.tinyCache[pvfMD5].get("nickName")}-{pvfMD5}')
                else:
                    if pvfPath=='':
                        pvfPath = askopenfilename(filetypes=[('DNF Script.pvf file','*.pvf')])
                    p = Path(pvfPath)
                    if p.exists():
                        multiCoreFlg = False#messagebox.askyesno('多核加载','是否开启多核心加载PVF？')
                        if multiCoreFlg:
                            cacheM.pvfReader.LOAD_FUNC = cacheM.pvfReader.get_Item_Dict_Multi
                            #cacheM.pvfReader.TinyPVF.loadLeafFunc = cacheM.pvfReader.TinyPVF.load_Leafs_multi
                        else:
                            cacheM.pvfReader.LOAD_FUNC = cacheM.pvfReader.get_Item_Dict
                            #cacheM.pvfReader.TinyPVF.loadLeafFunc = cacheM.pvfReader.TinyPVF.load_Leafs
                        t1 = time.time()
                        self.titleLog('加载PVF中...')
                        self.PVF_LOAD_FLG = True
                        info = cacheM.loadItems2(True,pvfPath,self.titleLog,pool=pool)
                        self.PVF_LOAD_FLG = False
                        if info=='PVF文件路径错误':
                            pvfComboBox.set('pvf路径错误')
                            self.titleLog('pvf读取错误')
                            return False
                        t = time.time() - t1 
                        info += '  花费时间%.2fs' % t
                        MD5 = cacheM.PVFcacheDict.get("MD5")
                        pvfComboBox.set(f'{cacheM.tinyCache[MD5].get("nickName")}-{MD5}')
                        if self.PVF_EDIT_OPEN_FLG:
                            self.PVFEditWinFrame.fillTree()

                        if sourceVar.get()==1:
                            self.titleLog(info)
                        else:
                            cacheM.loadItems2(False)
                            self.titleLog('PVF加载完成，请选择使用  花费时间%.2fs' % t)
                        #get_pool()
                    else:
                        self.titleLog('PVF路径错误，加载CSV')
                        time.sleep(1)
                        source = 0
                        sourceVar.set(0)
                    res = []
                    for MD5,infoDict in list(cacheM.cacheManager.tinyCache.items()):
                        if not isinstance(infoDict,dict):continue
                        res.append(f'{cacheM.cacheManager.tinyCache[MD5]["nickName"]}-{MD5}')
                    pvfComboBox.config(values=res)
                enhanceTypes = list(cacheM.enhanceDict_zh.keys())
                for orbTypeE in self.orbTypeEList:
                    orbTypeE.config(values=enhanceTypes)
                selectCharac()
            if source==1 and self.PVF_LOAD_FLG:
                self.titleLog('等待PVF加载')
            if source==0:
                info = cacheM.loadItems2(False)
                self.titleLog(info)
                selectCharac()
            if cacheM.magicSealDict.get(0) is None:
                cacheM.magicSealDict[0] = ''
            [func() for func in self.updateMagicSealFuncs.values()]
            self.hiddenCom.config(values=['0-None']+[f'{i+1}-{value}' for i,value in enumerate(cacheM.avatarHiddenList[0])])
            self.jobE.config(values=[f'{item[0]}-{item[1][0]}'  for item in cacheM.jobDict.items()])
            self.jobE.set('')

        #账号查询功能
        self.searchCharac = searchCharac
        self.selectCharac = selectCharac
        self.fillCharac = fill_charac_treeview
        self.refreshBtn.config(command=selectCharac)
        searchFrame = tk.Frame(tabView,borderwidth=0)
        searchFrame.pack(expand=True)
        tabView.add(searchFrame,text=' 查询 ')
        #tabView.grid(expand=True, fill=tk.BOTH,padx=PADX*5,pady=PADY*5)

        
        padx = 0
        pady = 2
        row = 1
        padFrame = tk.Frame(searchFrame)
        padFrame.grid(column=0,row=row,padx=PADX*3,sticky='nswe')
        if True:
            fill = 'x' if HEIGHT==1 else 'both'
            accountSearchFrame = tk.LabelFrame(searchFrame,text='账户查询')

            accountE = ttk.Entry(accountSearchFrame,width=int(WIDTH*12))
            accountE.pack(padx=PADX*5,pady=PADY*pady,fill=fill,expand=True)
            accountBtn = ttk.Button(accountSearchFrame,text='查询/加载所有',command=lambda:searchCharac('account'),state='disable')
            accountBtn.pack(padx=PADX*5,pady=PADY*pady,fill=fill,expand=True)
            CreateToolTip(accountBtn,'输入账号名或账号ID\n输入为空时加载所有角色')
            accountSearchFrame.grid(column=1,row=row,padx=PADX*padx,sticky='nswe')
            row += 1
            characSearchFrame = tk.LabelFrame(searchFrame,text='角色查询')
            characE = ttk.Entry(characSearchFrame,width=int(WIDTH*12))
            characE.pack(padx=PADX*5,pady=PADY*pady,fill=fill,expand=True)
            characBtn = ttk.Button(characSearchFrame,text='查询/加载在线',command=lambda:searchCharac('cName'),state='disable')
            characBtn.pack(padx=PADX*5,pady=PADY*pady,fill=fill,expand=True)
            CreateToolTip(characBtn,'输入为空时加载在线角色')
            characSearchFrame.grid(column=1,row=row,padx=PADX*padx,sticky='nswe')
            row += 1
            connectorFrame = tk.LabelFrame(searchFrame,text='连接器')
            connectorE = ttk.Combobox(connectorFrame,width=int(WIDTH*10),state='readonly')
            connectorE.pack(padx=PADX*5,pady=PADY*pady,fill=fill,expand=True)
            def selConnector(e):
                i = int(connectorE.get().split('-')[0])
                sqlM.connectorUsed = sqlM.connectorAvailuableList[i]
                print(f'当前切换连接器为{sqlM.connectorUsed}')
            connectorE.bind('<<ComboboxSelected>>',selConnector)
            connectorFrame.grid(column=1,row=row,padx=PADX*padx,sticky='nswe')
            self.connectorE = connectorE
            self.connectorE.set('----')

            row += 1
            encodeFrame = tk.LabelFrame(searchFrame,text='文字编码')
            encodeE = ttk.Combobox(encodeFrame,width=int(WIDTH*10),values=[f'{i}-{encode}' for i,encode in enumerate(sqlM.SQL_ENCODE_LIST)],state='readonly')
            encodeE.pack(padx=PADX*5,pady=PADY*pady,fill=fill,expand=True)
            encodeE.set('----')
            def setEncodeing(e):
                encodeIndex = int(encodeE.get().split('-')[0])
                sqlM.sqlEncodeUseIndex = encodeIndex
                sqlM.ENCODE_AUTO = False  #关闭自动编码切换
            encodeE.bind('<<ComboboxSelected>>',setEncodeing)
            encodeFrame.grid(column=1,row=row,padx=PADX*padx,sticky='nswe')
            
            # 信息显示及logo，物品源选择
            row += 1
            PVFSelFrame = tk.LabelFrame(searchFrame,text='数据来源')
            PVFSelFrame.grid(row=row,column=1,padx=PADX*padx,sticky='nswe')
            itemSourceSel = tk.IntVar()
            pvfPath = config.get('PVF_PATH')
            if pvfPath is not None and '.pvf' in pvfPath:
                p = Path(pvfPath)
                if p.exists():
                    itemSourceSel.set(1)
            def selSource(pvfPath=''):
                def inner():
                    if  pvfPath=='':# 加载PVF
                        setItemSource(itemSourceSel,pvfPath)
                    elif pvfPath.split('-')[-1] in cacheM.cacheManager.allMD5(): #PVF缓存
                        setItemSource(itemSourceSel,pvfMD5=pvfPath.split('-')[-1])
                    else:
                        itemSourceSel.set(0)    #读取CSV
                        setItemSource(itemSourceSel)
                t = threading.Thread(target=inner)
                t.daemon = True
                t.start()
            
            selSource(config.get('PVF_PATH'))
            ttk.Radiobutton(PVFSelFrame,variable=itemSourceSel,value=0,text='  本地文件',command=selSource).pack(anchor='w',padx=PADX*5,pady=PADY*3,fill='both',expand=True)
            ttk.Radiobutton(PVFSelFrame,variable=itemSourceSel,value=1,text='  PVF文件',command=selSource).pack(anchor='w',padx=PADX*5,pady=PADY*3,fill='both',expand=True)
            res = []
            for MD5,infoDict in list(cacheM.cacheManager.tinyCache.items()):
                if not isinstance(infoDict,dict):continue
                res.append(f'{cacheM.cacheManager.tinyCache[MD5]["nickName"]}-{MD5}')
            pvfComboBox = ttk.Combobox(PVFSelFrame,values=res,width=int(WIDTH*10))
            pvfComboBox.set('请选择PVF缓存')
            pvfComboBox.pack(anchor='w',padx=PADX*5,pady=PADY*5,fill=fill,expand=True)
            pvfComboBox.bind("<<ComboboxSelected>>",lambda e:selSource(pvfComboBox.get()))
            self.pvfComboBox = pvfComboBox
            CreateToolTip(pvfComboBox,'PVF缓存')

        #角色选择列表
        padFrame = tk.Frame(searchFrame,height=int(HEIGHT*390))
        padFrame.grid(row=1,column=2,rowspan=5,sticky='ns',padx=PADX*5,pady=PADY*5)
        characTreev = ttk.Treeview(searchFrame, selectmode ='browse',height=int(HEIGHT*18))
        characTreev.grid(row=1,column=2,rowspan=5,sticky='nswe',padx=PADX*5,pady=PADY*5)

        characTreev["columns"] = ("1", "2", "3",'4','5')
        characTreev['show'] = 'headings'
        characTreev.column("5", width = int(40*WIDTH), anchor ='c')
        characTreev.column("1", width = int(40*WIDTH), anchor ='c')
        characTreev.column("2", width = int(95*WIDTH), anchor ='se')
        characTreev.column("3", width = int(50*WIDTH), anchor ='se')
        characTreev.column("4", width = int(70*WIDTH), anchor ='se')
        characTreev.heading("5", text ="账号")
        characTreev.heading("1", text ="编号")
        characTreev.heading("2", text ="角色名")
        characTreev.heading("3", text ="等级")
        characTreev.heading("4", text ="职业")
        characTreev.bind('<ButtonRelease-1>',selectCharac)
        characTreev.tag_configure('deleted', background='gray')

        infoFrame = tk.Frame(searchFrame,borderwidth=0)
        infoFrame.grid(row=1,column=3,rowspan=10,sticky='nwse')
        infoFrame_ = tk.Frame(searchFrame,width=int(WIDTH*192),height=int(HEIGHT*5))
        infoFrame_.grid(row=0,column=3,sticky='nwse')
        if len(cacheM.config['TITLE'])>0:
            tk.Label(infoFrame,text=cacheM.config['TITLE'],font=cacheM.config['FONT'][0]).pack(anchor='n',side='top')
        if len(cacheM.config['VERSION'])>0:
            tk.Label(infoFrame,text=cacheM.config['VERSION'],font=cacheM.config['FONT'][1]).pack(anchor='n',side='top')
        if len(cacheM.config['INFO'])>0:
            tk.Label(infoFrame,text=cacheM.config['INFO'],font=cacheM.config['FONT'][2]).pack(anchor='n',side='top')
        gifCanvas = ImageLabel(infoFrame,borderwidth=0)
        gifCanvas.pack(expand=True,pady=PADY*5,fill='both')
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
        positionDict = self.positionDict
        if len(cacheM.PVFcacheDict.keys())==0:
            return 'PVF未加载'
        for tabName in self.globalCharacBlobs.keys():
            itemDict = self.selectedCharacItemsDict[tabName]
            self.unknowItemsListDict[tabName] = []  #保存位置物品的index
            self.errorItemsListDict[tabName] = []   #保存错误物品的index
            self.errorInfoDict[tabName] = {}    #保存错误信息
            for index, itemSlot in itemDict.items():
                itemSlot:sqlM.DnfItemSlot
                if itemSlot.id==0:
                    continue
                typeID,typeZh = cacheM.getStackableTypeMainIdAndZh(itemSlot.id)
                #print(typeID,typeZh,cacheM.ITEMS_dict.get(itemSlot.id))
                #常规判断，标记种类是否与实际种类冲突
                self.errorInfoDict[tabName][index] = ''
                if typeID not in [0,1,2,3,4,5,6,7,0x0a]:
                    self.errorItemsListDict[tabName].append(index)
                    self.errorInfoDict[tabName][index] += f'物品种类冲突-当前{typeID,typeZh}-不属于此列表分类 \n'
                if typeID!=0 and typeID!=itemSlot.type:
                    self.errorItemsListDict[tabName].append(index)
                    self.errorInfoDict[tabName][index] += f'物品种类冲突-当前{itemSlot.type}-{typeID} \n'
                elif typeID==0:
                    self.unknowItemsListDict[tabName].append(index)
                stkLimit = None
                pvfInfoDict = cacheM.get_Item_Info_In_Dict(itemSlot.id)
                if pvfInfoDict is not None:
                    stkLimit = pvfInfoDict.get('[stack limit]')
                    if stkLimit is not None:
                        stkLimit = stkLimit[0]
                if stkLimit is not None and stkLimit<itemSlot.num_grade:
                    self.errorItemsListDict[tabName].append(index)
                    self.errorInfoDict[tabName][index] += f'物品数量错误-当前{itemSlot.num_grade}-{stkLimit} \n'

                if tabName=='物品栏' and typeID!=0:
                    if index in range(*positionDict[typeID][1]) or index in [3,4,5,6,7,8]:
                        pass
                    else:
                        self.errorItemsListDict[tabName].append(index)
                        self.errorInfoDict[tabName][index] += f'物品位置错误-当前{index}-{positionDict[typeID][1]} \n'
                elif tabName=='穿戴栏':
                    if typeID != 0x01:
                        self.errorItemsListDict[tabName].append(index)
                        self.errorInfoDict[tabName][index] += f'物品种类错误-当前{typeID}-0x01 \n'
                    if itemSlot.isSeal==1:
                        self.errorItemsListDict[tabName].append(index)
                        self.errorInfoDict[tabName][index] += f'物品封装错误-当前{itemSlot.isSeal}-0x00 \n'
                elif tabName=='宠物栏':
                    try:
                        if index in range(*positionDict[typeID][1]) or index in range(*positionDict[typeID][2]):
                            pass
                        else:
                            self.errorItemsListDict[tabName].append(index)
                            self.errorInfoDict[tabName][index] += f'物品位置错误-当前{index}-{positionDict[typeID][1],positionDict[typeID][2]} \n'
                    except:
                        print('宠物栏',index,typeID)
                elif tabName==' 仓库 ':
                    if itemSlot.type not in [1,2,3,0x0a]:
                        self.errorItemsListDict[tabName].append(index)
                        self.errorInfoDict[tabName][index] += f'物品类型错误-当前{itemSlot.type}-{[1,2,3,0x0a]} '
        print('未知物品',self.unknowItemsListDict,'\n错误物品',self.errorItemsListDict)

    def fill_tab_treeviews(self):
        '''根据当前本地的blob和非blob字段填充数据（不包括角色信息）'''
        self.selectedCharacItemsDict = {}
        for key in self.editedItemsDict.keys():
            self.editedItemsDict[key] = {}    #清空编辑的对象
        
        # 填充blob字段
        for tabName,currentTabBlob in self.globalCharacBlobs.items():#替换填充TreeView
            CharacItemsList = []
            itemsTreev_now = self.itemsTreevs_now[tabName]
            for child in itemsTreev_now.get_children():
                itemsTreev_now.delete(child)
            
            CharacItemsList = sqlM.unpackBLOB_Item(currentTabBlob)
            CharacItemsDict = {}
            self.currentItemDict = {}
            for values in CharacItemsList:
                index, dnfItemSlot = values
                name = str(cacheM.ITEMS_dict.get(dnfItemSlot.id))
                CharacItemsDict[index] = dnfItemSlot
            self.selectedCharacItemsDict[tabName] = CharacItemsDict
            
            self.itemInfoClrFuncs[tabName]()    #清除物品信息显示
            self.fillTreeFunctions[tabName]()   #填充treeview
        self.hiddenCom.set('0-None')
        self.checkBloblegal()   #检查物品合法

        #填充非blob字段
        for tabName,currentTabItems in self.globalCharacNonBlobs.items():
            try:
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
            except:
                print(f'{tabName}加载失败')

    def _buildtab_itemTab(self,tabView,tabName,treeViewArgs):
        def ask_commit():
            if showSelectedItemInfo()!=True or self.cNo==0:
                return False
            if not messagebox.askokcancel('修改确认',f'确定修改{tabName}所选物品？\n请确认账号不在线或正在使用其他角色\n{self.editedItemsDict[tabName]}'):
                return False
            cNo = self.cNo
            key = globalBlobs_map[tabName]
            originblob = self.globalCharacBlobs[tabName]
            sqlM.commit_change_blob(originblob,self.editedItemsDict[tabName],cNo,key)
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
                orbTypeEntry.config(state='readonly')
                orbValueEntry.config(state='readonly')
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
                typeEntry.config(state='normal' if cacheM.config.get('TYPE_CHANGE_ENABLE') == 1 else 'disable')
                       
        def updateItemEditFrame(itemSlot:sqlM.DnfItemSlot):
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
            itemNameEntry.insert(0,str(cacheM.ITEMS_dict.get(itemSlot.id)))
            numEntry.insert(0,itemSlot.num_grade)
            EnhanceEntry.insert(0,itemSlot.enhancementLevel)
            forgingEntry.insert(0,itemSlot.forgeLevel)
            otherworldEntry.insert(0,itemSlot.otherworld.hex())
            orbEntry.insert(0,itemSlot.orb)
            enhance:dict = cacheM.cardDict_zh.get(itemSlot.orb)
            if enhance is not None:
                try:
                    enhanceType,value = enhance.copy().popitem()
                    orbTypeEntry.set(enhanceType)
                    setOrbTypeCom(1)
                    orbValueEntry.set(value)
                except:
                    self.titleLog(f'宝珠加载失败，{itemSlot.orb}')
                    pass
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
            orbTypeEntry.set('')
            orbValueEntry.set('')
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
            res = cacheM.get_Item_Info_In_Text(itemID).replace(r'%%',r'%').strip()
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
                    if index in self.errorItemsListDict[tabName]:
                        tag = 'error'
                    elif index in self.unknowItemsListDict[tabName]:
                        tag = 'unknow'
                    itemSlot:sqlM.DnfItemSlot = self.editedItemsDict.get(tabName).get(index)
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
                itemSlot:sqlM.DnfItemSlot = self.editedItemsDict.get(tabName).get(index)
            else:
                itemSlot:sqlM.DnfItemSlot = self.selectedCharacItemsDict[tabName][index]
            updateItemEditFrame(itemSlot)
            self.w.title(itemSlot)
            self.currentItemDict[tabName] = [index,itemSlot,itemsTreev_now.focus()]
            itemEditFrame.config(text=f'物品信息编辑({index})')
            errorInfo = self.errorInfoDict[tabName].get(index)
            if errorInfo is not None:
                CreateOnceToolTip(itemsTreev_now,text=errorInfo)
            return True

        def searchItem(e:tk.Event):
            '''搜索物品名'''
            if e.x<100:return
            key = itemNameEntry.get()
            if len(key)>0:
                res = cacheM.searchItem(key)
                itemNameEntry.config(values=[str([item[0]])+' '+item[1] for item in res])
        def searchMagicSeal(com:ttk.Combobox):
            '''输入魔法封印时搜索'''
            key = com.get()
            res = cacheM.searchMagicSeal(key)
            res.sort()
            if key!='':
                res_ = list(cacheM.magicSealDict.items())
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
                name = str(cacheM.ITEMS_dict.get(int(id_)))
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
            itemSlot = sqlM.DnfItemSlot(b'')
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
            itemSlot:sqlM.DnfItemSlot = deepcopy(itemSlot_)
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
            orb = int(orbEntry.get().replace(' ',''))
            itemSlot.orb = orb
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
            cacheM.ITEMS_dict[0] = ''
            CharacItemsDict = self.selectedCharacItemsDict[tabName]
            for index, dnfItemSlot in CharacItemsDict.items():
                    name = str(cacheM.ITEMS_dict.get(dnfItemSlot.id))
                    if tabName=='物品栏' and index in [0,1,2]:
                        #过滤物品栏前三个。这三个功能未知，会闪退
                        continue
                    if typeSel!=0xff and typeSel!=0x00: #过滤种类
                        if dnfItemSlot.id != 0 and dnfItemSlot.type != typeSel:
                            continue
                        if tabName in ['物品栏','宠物栏']:   #物品栏、宠物栏专属过滤
                            position = self.positionDict[typeSel][1]
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
        padFrame = tk.Frame(inventoryFrame,width=int(3))#WIDTH*
        padFrame.grid(row=1,column=0,sticky='nswe')
        invBowserFrame = tk.LabelFrame(inventoryFrame,text='当前物品列表',width=int(WIDTH*306))
        invBowserFrame.grid(row=1,column=1,sticky='nswe',padx=PADX*2)
        #self.w.after(5000,lambda:print(invBowserFrame.winfo_width()))
        if True:    #'当前物品列表'
            filterFrame = tk.Frame(invBowserFrame)
            filterFrame.pack(anchor=tk.E,fill=tk.X)
            if True:
                emptySlotVar = tk.IntVar()
                emptySlotVar.set(0)
                ttk.Checkbutton(filterFrame,text='显示空槽位',variable=emptySlotVar,command=refill_Tree_View).pack(side='left',padx=PADX*10)

                values = [f'0x{"%02x" % item[0]}-{item[1]}' for item in sqlM.DnfItemSlot.typeDict.items()] +['0xff-全部']
                typeBox = ttk.Combobox(filterFrame,values=values,state='readonly',width=int(WIDTH*14),font=('', 10)) 
                typeBox.set('0xff-全部')
                typeBox.pack(side='right',padx=PADX*5)
                typeBox.bind('<<ComboboxSelected>>',refill_Tree_View)         
            treeViewFrame = tk.Frame(invBowserFrame)
            treeViewFrame.pack(anchor=tk.E,fill=tk.X)
            if True:
                #ttk.Separator(treeViewFrame, orient='horizontal').pack(side=tk.TOP,fill='x')
                padFrame = tk.Frame(treeViewFrame,height=int(HEIGHT*324+(HEIGHT-1)*80),width=4)   #控制treeview高度int(WIDTH*4),bg='red'
                padFrame.pack(side=tk.LEFT,fill='y')
                
                

                itemsTreev_now = ttk.Treeview(treeViewFrame, selectmode ='browse',height=int(HEIGHT*10))
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
            blobFuncFrame.grid(row=2,column=1,sticky='nswe')
            #blobFuncFrame = tk.Frame(blobFuncFrame)
            #blobFuncFrame.pack(fill='both',expand=True)
            if True:
                exportBtn = ttk.Button(blobFuncFrame,text=f'导出字段',command=lambda:save_blob(globalBlobs_map[tabName]),width=int(WIDTH*15))
                exportBtn.pack(side='left',fill='both',expand=True,padx=PADX*5,pady=PADY*3)
                CreateToolTip(exportBtn,text='保存当前数据到文件')
                importBtn = ttk.Button(blobFuncFrame,text=f'导入字段',command=lambda:load_blob(globalBlobs_map[tabName]),width=int(WIDTH*15))
                importBtn.pack(side='right',fill='both',expand=True,padx=PADX*5,pady=PADY*3)
                CreateToolTip(importBtn,text='从文件导入数据并覆盖')
        #return False
        ttk.Separator(inventoryFrame, orient='vertical').grid(row=1,column=2,rowspan=2,sticky='nswe')

        itemEditFrame = tk.LabelFrame(inventoryFrame,text='物品信息编辑',width=int(WIDTH*296))
        #self.w.after(5000,lambda:print(itemEditFrame.winfo_width()))
        itemEditFrame.grid(row=1,column=3,sticky='nswe',padx=PADX*2)

        padFrame = tk.Frame(itemEditFrame,height=int(HEIGHT*340+(HEIGHT-1)*80))
        padFrame.grid(column=0,row=0,rowspan=9)
        padx = 3
        pady = 1
        # 2
        row = 2
        itemSealVar = tk.IntVar()
        itemSealVar.set(1)
        itemSealBtn = ttk.Checkbutton(itemEditFrame,text='封装',variable=itemSealVar)
        itemSealBtn.grid(column=1,row=row,padx=PADX*padx,pady=PADY*pady)
        CreateToolTip(itemSealBtn,'无法封装的物品勾选会炸角色')
        itemNameEntry = ttk.Combobox(itemEditFrame,width=int(WIDTH*14),state='normal')
        itemNameEntry.bind('<Button-1>',searchItem)
        itemNameEntry.grid(column=2,row=row,sticky='nswe',padx=PADX*padx,pady=PADY*pady)
        itemNameEntry.bind("<<ComboboxSelected>>",lambda e:readSlotName('name'))
        CreateToolTip(itemNameEntry,textFunc=getItemPVFInfo)
        itemIDEntry = ttk.Entry(itemEditFrame,width=int(WIDTH*10))
        itemIDEntry.grid(column=3,row=row,sticky='nswe',padx=PADX*padx,pady=PADY*pady)
        itemIDEntry.bind('<FocusOut>',lambda e:readSlotName('id'))
        itemIDEntry.bind('<Return>',lambda e:readSlotName('id'))
        # 3
        row = 3
        numGradeLabel = tk.Label(itemEditFrame,text='数量：')
        numGradeLabel.grid(column=1,row=row,padx=PADX*padx,pady=PADY*pady)
        numEntry = ttk.Spinbox(itemEditFrame,width=int(WIDTH*15),from_=0, to=4294967295)
        numEntry.grid(column=2,row=row,sticky='nswe',padx=PADX*padx,pady=PADY*pady)
        CreateToolTip(numEntry,'当为装备时，表示为品级\n数值与品级关系较为随机\n(0~4,294,967,295)')
        tk.Label(itemEditFrame,text=' 耐久：').grid(column=3,row=row,sticky='nsw',padx=PADX*padx,pady=PADY*pady)
        durabilityEntry = ttk.Spinbox(itemEditFrame,width=int(WIDTH*4),from_=0, to=999)
        durabilityEntry.grid(column=3,row=row,sticky='nse',padx=PADX*padx,pady=PADY*pady)
        # 4
        row = 4
        tk.Label(itemEditFrame,text='增幅：').grid(column=1,row=row,padx=PADX*padx,pady=PADY*pady)
        IncreaseTypeEntry = ttk.Combobox(itemEditFrame,width=int(WIDTH*14),state='readonly',values=['空-0','异次元体力-1','异次元精神-2','异次元力量-3','异次元智力-4'])
        IncreaseTypeEntry.grid(column=2,row=row,sticky='nswe',padx=PADX*padx,pady=PADY*pady)
        IncreaseEntry = ttk.Spinbox(itemEditFrame,width=int(WIDTH*10),from_=0, to=65535)
        IncreaseEntry.grid(column=3,row=row,sticky='nswe',padx=PADX*padx,pady=PADY*pady)
        
        # 5
        row = 5
        tk.Label(itemEditFrame,text='强化：').grid(column=1,row=row,padx=PADX*padx,pady=PADY*pady)
        EnhanceEntry = ttk.Spinbox(itemEditFrame,width=int(WIDTH*15),increment=1,from_=0, to=31)
        EnhanceEntry.grid(column=2,row=row,sticky='nswe',padx=PADX*padx,pady=PADY*pady)
        delBtn = ttk.Button(itemEditFrame,text=' 删除 ',command=setDelete)
        CreateToolTip(delBtn,'标记当前物品为待删除物品')
        delBtn.grid(row=row,column=3,pady=PADY*pady,padx=PADX*padx,sticky='nswe')
        # 6
        row = 6
        tk.Label(itemEditFrame,text='锻造：').grid(column=1,row=row,padx=PADX*padx,pady=PADY*pady)
        forgingEntry = ttk.Spinbox(itemEditFrame,width=int(WIDTH*15),increment=1,from_=0, to=31)
        forgingEntry.grid(column=2,row=row,sticky='nswe',padx=PADX*padx,pady=PADY*pady)
        resetBtn = ttk.Button(itemEditFrame,text=' 重置 ',command=reset)
        resetBtn.grid(row=row,column=3,pady=PADY*pady,padx=PADX*padx,sticky='nswe')
        # 7 
        def enableTestFrame():
            cacheM.config['TYPE_CHANGE_ENABLE'] = enableTypeChangeVar.get()
            print(cacheM.config)
            json.dump(cacheM.config,open(cacheM.configPath,'w'),ensure_ascii=False)
            typeEntry.config(state='normal' if cacheM.config.get('TYPE_CHANGE_ENABLE') == 1 else 'disable')

                
        row = 7
        enableTypeChangeVar = tk.IntVar()
        enableTypeChangeVar.set(cacheM.config.get('TYPE_CHANGE_ENABLE'))
        enableTestBtn = ttk.Checkbutton(itemEditFrame,text=' 启用种类字段',variable=enableTypeChangeVar,command=enableTestFrame)
        enableTestBtn.grid(column=1,row=row,columnspan=2,sticky='w',padx=PADX*padx,pady=PADY*pady)
        tk.Label(itemEditFrame,text='种类:').grid(column=1,row=row,columnspan=2,sticky='e',padx=PADX*padx,pady=PADY*pady)
        typeEntry = ttk.Combobox(itemEditFrame,width=int(WIDTH*4),state='readonly',values=['1-装备','2-消耗品','3-材料','4-任务材料','5-宠物','6-宠物装备','7-宠物消耗品','10-副职业'])
        typeEntry.grid(column=3,row=row,sticky='nswe',padx=PADX*padx,pady=PADY*pady)
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
        equipmentExFrame.grid(column=1,row=row,columnspan=3,sticky='nswe',padx=PADX*padx-1,pady=PADY*pady)
        padFrame  = tk.Frame(equipmentExFrame,width=int(WIDTH*287),height=int(HEIGHT*180),borderwidth=0) #调整整体宽度
        padFrame.grid(row=1,column=1,columnspan=6,rowspan=7)
        if True:
            # 8-1
            padx = 1
            row = 1
            tk.Label(equipmentExFrame,text='异界').grid(column=1,row=row,padx=PADX*padx,pady=PADY*pady)
            otherworldEntry = ttk.Entry(equipmentExFrame,state='readonly',width=int(WIDTH*29))
            otherworldEntry.grid(column=2,row=row,columnspan=5,sticky='nswe',padx=PADX*padx,pady=PADY*pady)
            # 8-2
            def setOrbTypeCom(e:tk.Event):
                enhanceKeyZh = orbTypeEntry.get()
                enhanceItems = cacheM.enhanceDict_zh.get(enhanceKeyZh)
                enhanceItemsList = list(enhanceItems.items())
                #print(items)
                try:
                    enhanceItemsList.sort(key=lambda x:x[1][0],reverse=True)
                except:
                    pass
                items_str = []
                for item in enhanceItemsList:
                    if isinstance(item,list):
                        item_str = '|'.join([str(value) for value in item[1]]) +' '*20 +f'-{item[0]}'
                    else:
                        item_str = str(item[1]) + ' '*20 +f'-{item[0]}'
                    items_str.append(item_str)
                orbValueEntry.config(values=items_str)    
                orbValueEntry.set(f'属性值({len(items_str)})')
            
            def setOrbValueCom(e:tk.Event):
                itemID = orbValueEntry.get().split('-')[-1]
                orbEntry.delete(0,tk.END)
                orbEntry.insert(0,itemID)
                
            row = 2
            tk.Label(equipmentExFrame,text='宝珠').grid(column=1,row=row,padx=PADX*padx,pady=PADY*pady)
            orbTypeEntry = ttk.Combobox(equipmentExFrame,state='readonly',width=int(WIDTH*10))
            orbValueEntry = ttk.Combobox(equipmentExFrame,state='readonly',width=int(WIDTH*11))
            orbEntry = ttk.Entry(equipmentExFrame,state='readonly',width=int(WIDTH*7))#
            orbTypeEntry.grid(column=2,row=row,padx=PADX*padx,pady=PADY*pady,sticky='nswe')
            orbValueEntry.grid(column=3,row=row,columnspan=3,sticky='nswe',padx=PADX*padx,pady=PADY*pady)
            orbEntry.grid(column=6,row=row,columnspan=1,sticky='nswe',padx=PADX*padx,pady=PADY*pady)
            orbTypeEntry.bind('<<ComboboxSelected>>',setOrbTypeCom)
            orbValueEntry.bind('<<ComboboxSelected>>',setOrbValueCom)
            self.orbTypeEList.append(orbTypeEntry)
            def showOrb(e=tk.Event):
                try:
                    return cacheM.get_Item_Info_In_Text(int(orbEntry.get())) if int(orbEntry.get())!=0 else ''
                except:
                    return ''
            
            def changeOrbByID(e):
                try:
                    enhance:dict = cacheM.cardDict_zh.get(int(orbEntry.get()))
                    if enhance is not None:
                        enhanceType,value = enhance.copy().popitem()
                        orbTypeEntry.set(enhanceType)
                        setOrbTypeCom(1)
                        orbValueEntry.set(value)
                except:
                    pass
            orbEntry.bind('<FocusOut>',changeOrbByID)
            orbEntry.bind('<Return>',changeOrbByID)
            CreateToolTip(orbEntry,textFunc=showOrb)
            # 8-3
            row = 3
            tk.Label(equipmentExFrame,text='魔法封印：').grid(column=1,row=row,columnspan=2,sticky='w',padx=PADX*padx,pady=PADY*pady)

            forthSealEnable = tk.IntVar()
            forthSealEnable.set(1)
            forth = ttk.Checkbutton(equipmentExFrame,variable=forthSealEnable,text='第四词条',command=lambda:print(forthSealEnable.get()))
            forth.grid(column=2,row=row,columnspan=5,sticky='e')
            CreateToolTip(forth,'启用后无法使用游戏内魔法封印相关修改操作')
        
            magicSealEntrys = []
            magicSealIDEntrys = []
            magicSealLevelEntrys = []
            magicSealEntryWidth = 7
            def build_magic_view(row=4):
                magicSealEntry = ttk.Combobox(equipmentExFrame,state='normal',width=int(WIDTH*magicSealEntryWidth),values=list(cacheM.magicSealDict.values()))
                magicSealIDEntry = ttk.Entry(equipmentExFrame,state='readonly',width=int(WIDTH*4))
                magicSealLevelEntry = ttk.Spinbox(equipmentExFrame,state='normal',width=int(WIDTH*7),from_=0,to=65535)
                
                magicSealEntry.bind('<Button-1>',lambda e:searchMagicSeal(magicSealEntry))
                magicSealEntry.bind('<<ComboboxSelected>>',lambda e:setMagicSeal(magicSealEntry,magicSealIDEntry))
                magicSealEntry.grid(column=1,row=row,sticky='nswe',padx=PADX*padx,pady=PADY*pady,columnspan=3)
                magicSealIDEntry.grid(column=4,row=row,sticky='nswe',padx=PADX*padx,pady=PADY*pady)
                magicSealLevelEntry.grid(column=5,row=row,sticky='nswe',padx=PADX*padx,pady=PADY*pady,columnspan=2)
                magicSealEntrys.append(magicSealEntry)
                magicSealIDEntrys.append(magicSealIDEntry)
                magicSealLevelEntrys.append(magicSealLevelEntry)
                CreateToolTip(magicSealLevelEntry,'词条数值，0-65535')
                self.updateMagicSealFuncs[tabName+str(row)] = lambda: magicSealEntry.config(values=list(cacheM.magicSealDict.values()))

            for row in [4,5,6,7]:
                build_magic_view(row)
                
        btnFrame = tk.Frame(inventoryFrame,width=int(WIDTH*296))
        btnFrame.grid(row=2,column=3,sticky='nswe')
        if True:
            itemSlotBytesE = ttk.Entry(btnFrame,width=int(WIDTH*10))
            itemSlotBytesE.pack(side='left',fill='both',expand=True,padx=PADX*2,pady=PADY*3)#grid(row=2,column=2,padx=PADX*2)
            CreateToolTip(itemSlotBytesE,textFunc=lambda:'物品字节数据：'+itemSlotBytesE.get())
            def genBytes():
                slotBytes = editSave('bytes')
                itemSlotBytesE.delete(0,tk.END)
                itemSlotBytesE.insert(0,slotBytes.hex())
            genBytesBtn = ttk.Button(btnFrame,text='生成字节',command=genBytes,width=int(WIDTH*7))
            genBytesBtn.pack(side='left',fill='both',expand=True,padx=PADX*2,pady=PADY*3)#.grid(row=2,column=1,padx=PADX*2)
            CreateToolTip(genBytesBtn,'根据物品槽数据编辑结果生成字节')

            def readBytes():
                itemBytes = str2bytes(itemSlotBytesE.get())
                updateItemEditFrame(sqlM.DnfItemSlot(itemBytes))

            importBtn = ttk.Button(btnFrame,text='导入字节',command=readBytes,width=int(WIDTH*7))
            importBtn.pack(side='left',fill='both',expand=True,padx=PADX*2,pady=PADY*3)#.grid(row=2,column=3,padx=PADX*2)
            CreateToolTip(importBtn,'读取字节，导入到编辑框\n用于物品复制')
            commitBtn = ttk.Button(btnFrame,text='提交修改',command=ask_commit,width=int(WIDTH*7))
            commitBtn.pack(side='left',fill='both',expand=True,padx=PADX*2,pady=PADY*3)#.grid(row=2,column=4,pady=PADY*5)
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
            print(f'删除{deleteIDs}')
            if tabName in globalNonBlobs_map.keys():
                log('删除非BLOB')
                tableName = globalNonBlobs_map[tabName]
                for ui_id in deleteIDs:
                    if sqlM.delNoneBlobItem(ui_id,tableName):
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
                    if sqlM.enable_Hidden_Item(ui_id,tableName,value):
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
        padFrame = tk.Frame(inventoryFrame,width=int(WIDTH*3))   #控制treeview高度
        padFrame.grid(row=1,column=0,sticky='ns')
        allInventoryFrame = tk.LabelFrame(inventoryFrame,text='当前物品列表',width=int(WIDTH*306))
        allInventoryFrame.grid(row=1,column=1,padx=PADX*2,sticky='nswe')
        #self.w.after(5000,lambda:print(allInventoryFrame.winfo_width()))

        padFrame = tk.Frame(allInventoryFrame,height=int(HEIGHT*380),width=int(WIDTH*4))
        padFrame.grid(row=1,column=1,sticky='nswe')
        

        itemsTreev_now = ttk.Treeview(allInventoryFrame, height=int(HEIGHT*12))
        itemsTreev_now.grid(row=1,column=2,rowspan=2,columnspan=2,sticky='nswe')
        self.itemsTreevs_now[tabName] = itemsTreev_now
        scrollBar= tk.Scrollbar(allInventoryFrame)
        scrollBar.grid(sticky='nse',column=4,row=1,rowspan=2)
        scrollBar.config(command =itemsTreev_now.yview)
        itemsTreev_now.config(yscrollcommand=scrollBar.set)

        ttk.Separator(inventoryFrame, orient='vertical').grid(row=1,column=2,rowspan=2,sticky='nswe')

        delInventoryFrame = tk.LabelFrame(inventoryFrame,text='待修改物品列表',width=int(WIDTH*295))
        delInventoryFrame.grid(row=1,column=3,padx=PADX*2,sticky='nswe')
        #self.w.after(5000,lambda:print(delInventoryFrame.winfo_width()))
        itemsTreev_del = ttk.Treeview(delInventoryFrame, height=int(HEIGHT*15+(HEIGHT-1)*5))   # if tabName==' 宠物 ' else 13
        itemsTreev_del.grid(row=1,column=2,rowspan=2,columnspan=4,sticky='nswe',padx=PADX*5,pady=PADY*5)
        self.itemsTreevs_del[tabName] = itemsTreev_del

        config_TreeViev(itemsTreev_now)
        config_TreeViev(itemsTreev_del)
        set_TreeView_Func(itemsTreev_now,itemsTreev_del)

        def reselect(tabName):
            itemsTreev_del = self.itemsTreevs_del[tabName] 
            for child in itemsTreev_del.get_children():
                itemsTreev_del.delete(child)
        pady = 5
        resetBtn = ttk.Button(delInventoryFrame,text=' 重选 ',command=lambda:reselect(tabName),width=int(WIDTH*10) if tabName==' 宠物 ' else 8)
        resetBtn.grid(row=4,column=2,pady=PADY*pady)
        if '时装' in tabName:
            hiddenCom = ttk.Combobox(delInventoryFrame,values=['0-None']+[f'{i+1}-{value}' for i,value in enumerate(cacheM.avatarHiddenList[0])],width=int(WIDTH*10))
            hiddenCom.grid(row=4,column=3,pady=PADY*pady)
            hiddenCom.set('0-None')
            self.hiddenCom = hiddenCom
            addHiddenBtn = ttk.Button(delInventoryFrame,text='开启潜能',command=lambda:enableHidden(tabName,itemsTreev_del),width=int(WIDTH*8))
            addHiddenBtn.grid(row=4,column=4,pady=PADY*pady)
        delBtn = ttk.Button(delInventoryFrame,text='确定删除',command=lambda:deleteItems(tabName,itemsTreev_del),width=int(WIDTH*10) if tabName==' 宠物 ' else 8)
        delBtn.grid(row=4,column=5,pady=PADY*pady)

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
            expert_job = int(jobE2.get().split('-')[0])
            kwDict = {
                'charac_name':cName,
                'job':job,
                'lev':lev,
                'grow_type':growType,
                'VIP':isVIP.get(),
                'expert_job':expert_job
            }
            sqlM.set_charac_info(self.cNo,**kwDict)
            return True
      
        def fill_charac_Info_tab():
            '''根据当前选中的cNo填充角色数据'''
            cName = self.characInfos[self.cNo].get('name')
            lev = self.characInfos[self.cNo].get('lev')
            job = self.characInfos[self.cNo].get('job')
            growType = self.characInfos[self.cNo].get('growType') % 16
            wakeFlg = self.characInfos[self.cNo].get('growType') // 16
            expert_job = self.characInfos[self.cNo].get('expert_job')
            #VIP = 
            isVIP.set(sqlM.read_VIP(self.cNo))
            clear_tab()
            
            nameE.insert(0,cName)
            levE.insert(0,lev)
            jobE.set(f'{job}-{cacheM.jobDict.get(job).get(0)}')
            jobE2.set(f'{expert_job}-{expert_jobMap.get(expert_job)}')
            set_grow_type()
            growTypeE.set(f'{growType}-{cacheM.jobDict.get(job).get(growType)}')
            wakeFlgE.set(wakeFlg)

        self.clear_charac_tab_func = clear_tab
        self.fill_charac_tab_fun = fill_charac_Info_tab
        self.cNo
        
        characMainFrame = tk.Frame(tabView)
        characMainFrame.pack(expand=True)
        
        tabView.add(characMainFrame,text=tabName)
        characEntriesAndGitHubFrame = tk.Frame(characMainFrame)
        characEntriesAndGitHubFrame.pack(padx=PADX*5,anchor='e',fill='x')
        if True:
            fill = 'x' if HEIGHT==1 else 'both'
            otherFunctionFrame = tk.LabelFrame(characEntriesAndGitHubFrame,text='附加功能')
            otherFunctionFrame.pack(padx=PADX*5,pady=PADY*5,side='left',fill='both',expand=True)
            btn = ttk.Button(otherFunctionFrame,text='生成一键启动器',command=ps.saveStart)
            btn.pack(expand=True,fill=fill,padx=PADX*5)
            CreateToolTip(btn,'读取正在运行的DNF进程\n生成一键登录exe')
            self.PVF_EDIT_OPEN_FLG = False
            btn = ttk.Button(otherFunctionFrame,text='PVF缓存管理器',command=self.open_PVF_Cache_Edit)
            btn.pack(expand=True,fill=fill,padx=PADX*5)
            CreateToolTip(btn,'修改缓存数据\n导出装备道具列表为CSV')

            btn = ttk.Button(otherFunctionFrame,text='GM工具',command=self._open_GM)
            btn.pack(expand=True,fill=fill,padx=PADX*5)
            CreateToolTip(btn,'开启GM工具（测试）')
            def set_Size(e):
                W = float(sizeE_W.get())
                H = float(sizeE_H.get())
                cacheM.config['SIZE'] = [W,H]
                cacheM.save_config()
            sizeFrame = tk.Frame(otherFunctionFrame)
            sizeFrame.pack(expand=True,fill=fill,padx=PADX*4)
            sizeE_W = ttk.Combobox(sizeFrame,values=[1,1.3,1.5,1.8,2,2.5],width=int(WIDTH*3))
            sizeE_W.set(WIDTH)
            sizeE_W.pack(expand=True,fill=fill,padx=PADX*1,side='left')
            sizeE_W.bind('<<ComboboxSelected>>',set_Size)
            CreateToolTip(sizeE_W,'设置窗口尺寸宽度倍数，下次启动后生效（测试）')
            sizeE_H = ttk.Combobox(sizeFrame,values=[1,1.3,1.5,1.8,2,2.5],width=int(WIDTH*3))
            sizeE_H.set(HEIGHT)
            sizeE_H.pack(expand=True,fill=fill,padx=PADX*1,side='right')
            sizeE_H.bind('<<ComboboxSelected>>',set_Size)
            CreateToolTip(sizeE_H,'设置窗口尺寸高度倍数，下次启动后生效（测试）')
            updateCheckVar = tk.IntVar()
            updateCheckVar.set(1 if cacheM.config.get('UPDATE_SUTO') is None or cacheM.config.get('UPDATE_SUTO')==1 else 0)
            def setUpdate():
                cacheM.config['UPDATE_SUTO'] = updateCheckVar.get()
                cacheM.save_config()
                if updateCheckVar.get()==1:
                    self.check_Update()
            ttk.Checkbutton(otherFunctionFrame,text='自动检查更新',variable=updateCheckVar,command=setUpdate).pack(padx=PADX*5)
            if updateCheckVar.get()==1:
                self.check_Update()
            
            

            characEntriesFrame = tk.Frame(characEntriesAndGitHubFrame)
            characEntriesFrame.pack(padx=PADX*5,pady=PADY*5,side='left',fill='both',expand=True)
            if True:
                padx = 10
                pady = 3
                row = 3
                entryWidth = 25
                padFrame = tk.Frame(characEntriesFrame,height=int(HEIGHT*150))
                padFrame.grid(row=row,column=4,columnspan=2,rowspan=6,sticky='nswe')
                tk.Label(characEntriesFrame,text='角色名：').grid(row=row,column=3,padx=PADX*padx,pady=PADY*pady)
                nameE = ttk.Entry(characEntriesFrame,width=int(WIDTH*entryWidth))#,state='readonly'
                nameE.grid(row=row,column=4,padx=PADX*padx,pady=PADY*pady,sticky='nswe')
                self.nameEditE = nameE
                #CreateToolTip(self.nameEditE,'编码出现错误时无法修改角色名')

                row+=1
                tk.Label(characEntriesFrame,text='角色等级：').grid(row=row,column=3,padx=PADX*padx,pady=PADY*pady)
                levE = ttk.Spinbox(characEntriesFrame,from_=1,to=999,width=int(WIDTH*entryWidth/1.5))
                levE.grid(row=row,column=4,padx=PADX*padx,pady=PADY*pady,sticky='nsw')
                isVIP = tk.IntVar()
                ttk.Checkbutton(characEntriesFrame,text='VIP账户',variable=isVIP,command=lambda:isVIP.get()).grid(row=row,column=4,padx=PADX*padx,pady=PADY*pady,sticky='nse')
                row+=1
                def set_grow_type(e=None):
                    growTypeE.config(values=[f'{item[0]}-{item[1]}' for item in cacheM.jobDict.get(int(jobE.get().split('-')[0])).items()])
                tk.Label(characEntriesFrame,text='职业：').grid(row=row,column=3,padx=PADX*padx,pady=PADY*pady)
                jobE2 = ttk.Combobox(characEntriesFrame,width=int(WIDTH*entryWidth/3),values=[f'{key}-{value}' for key,value in expert_jobMap.items()])
                jobE2.grid(row=row,column=4,padx=PADX*padx,pady=PADY*pady,sticky='nse')
                jobE = ttk.Combobox(characEntriesFrame,width=int(WIDTH*entryWidth/1.75),values=[f'{item[0]}-{item[1][0]}'  for item in cacheM.jobDict.items()])
                jobE.grid(row=row,column=4,padx=PADX*padx,pady=PADY*pady,sticky='nsw')
                jobE.bind('<<ComboboxSelected>>',set_grow_type)
                self.jobE = jobE
                row+=1
                tk.Label(characEntriesFrame,text='成长类型：').grid(row=row,column=3,padx=PADX*padx,pady=PADY*pady)
                growTypeE = ttk.Combobox(characEntriesFrame,width=int(WIDTH*entryWidth))
                growTypeE.grid(row=row,column=4,padx=PADX*padx,pady=PADY*pady,sticky='nswe')
                row+=1
                tk.Label(characEntriesFrame,text='觉醒标识：').grid(row=row,column=3,padx=PADX*padx,pady=PADY*pady)
                wakeFlgE=ttk.Combobox(characEntriesFrame,state='readonly',values=[0,1],width=int(WIDTH*entryWidth))
                wakeFlgE.grid(row=row,column=4,padx=PADX*padx,pady=PADY*pady,sticky='nswe')
                row+=1
                ttk.Button(characEntriesFrame,text='提交修改',command=commit).grid(row=row,column=3,columnspan=2,sticky='nswe')
            GitHubFrame(characEntriesAndGitHubFrame).pack(padx=PADX*5,pady=PADY*5,side='right')

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

    def _open_GM(self):
        import gmTool_resize as gmTool
        if self.GM_Tool_Flg:
            self.GMTool.wm_attributes('-topmost', 1)
            self.GMTool.wm_attributes('-topmost', 0)
            return False
        self.GMTool = gmTool.GMToolWindow(self.tabView,cNo=self.cNo)
        self.GM_Tool_Flg = True
        def quit():
            self.GM_Tool_Flg=False
            self.GMTool.destroy()
        self.GMTool.protocol('WM_DELETE_WINDOW',quit)

    def open_advance_search_equipment(self):
        
        def start_Search():
            for child in searchResultTreeView.get_children():
                searchResultTreeView.delete(child)
            type1 = typeE.get().split('-')[-1]
            type2 = typeE2.get().split('-')[-1]
            type3 = typeE3.get().split('-')[-1]
            typeDict = {}   #存放搜索时物品的小分类（爪、头肩等）{id:type}
            if type1=='':
                searchDict = cacheM.equipmentDict.copy()
            else:
                cacheM.equipmentForamted[type1]
                if type1 in ['首饰','特殊装备']:
                    if type2=='':
                        searchDict = {}
                        for typeName,equDict in cacheM.equipmentForamted[type1].items():
                            for id in equDict.keys():
                                typeDict[id] = typeName
                            searchDict.update(equDict)
                    else:
                        searchDict = cacheM.equipmentForamted[type1][type2]
                        for id in cacheM.equipmentForamted[type1][type2].keys():
                            typeDict[id] = type2
                else:
                    if type2=='':
                        searchDict = {}
                        for typeDict_ in cacheM.equipmentForamted[type1].values():
                            for typeName,equDict in typeDict_.items():
                                searchDict.update(equDict)
                                for id in equDict.keys():
                                    typeDict[id] = typeName
                    else:
                        if type3=='':
                            searchDict = {}
                            for typeName,equDict in cacheM.equipmentForamted[type1][type2].items():
                                searchDict.update(equDict)
                                for id in equDict.keys():
                                    typeDict[id] = typeName
                        else:
                            searchDict = cacheM.equipmentForamted[type1][type2][type3]
                            for id in cacheM.equipmentForamted[type1][type2][type3].keys():
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
                        searchDict[id] = searchDict[id] + '\n' + cacheM.get_Item_Info_In_Text(id).replace(r'%%',r'%').strip()
                useFuzzy = useFuzzyVar.get()
                searchList = cacheM.searchItem(nameKey,list(searchDict.items()),fuzzy=useFuzzy)
            else:
                searchList = list(searchDict.items())
            if levMax==999 and levMin==0 and raritykey=='----':
                searchList = list(searchList)[:10000]

            for itemID,nameAndContent in searchList:
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
                equipment_type = fileInDict.get('[equipment type]')
                if 'avatar' in str(equipment_type) or ('avatar' in str(fileInDict.keys()) and '[stackable type]'):
                    rarity += '时装'
                '''if 'avatar' in str(fileInDict.keys()):
                    rarity += '时装'''

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
            itemSlot = sqlM.DnfItemSlot(b'\x00'*61)
            itemSlot.id = itemID
            itemSlot.type = 0x01
            itemSlot.durability = 999
            itemSlot.oriBytes = itemSlot.build_bytes()
            self.editFrameUpdateFuncs[self.tabNames[frame_id]](itemSlot)
            self.w.focus_force()

        def quitSearch():
            advanceSearchMainWin.destroy()
            self.Advance_Search_State_FLG=False

        if self.Advance_Search_State_FLG==True:
            self.advanceEquSearchMainFrame.wm_attributes('-topmost', 1)
            self.advanceEquSearchMainFrame.wm_attributes('-topmost', 0)
            return False
        self.Advance_Search_State_FLG = True
        advanceSearchMainWin = tk.Toplevel(self.advanceSearchBtn)
        
        #advanceSearchMainFrame.wm_attributes('-topmost', 1)
        #advanceSearchMainFrame.wm_overrideredirect(1)
        advanceSearchMainWin.wm_geometry("+%d+%d" % (self.advanceSearchBtn.winfo_rootx(), self.advanceSearchBtn.winfo_rooty()))
        self.advanceEquSearchMainFrame = advanceSearchMainWin
        titleFrame = TitleBarFrame(advanceSearchMainWin,advanceSearchMainWin,'装备专用搜索')
        titleFrame.pack(fill=tk.X,expand=1,anchor=tk.N)  
        advanceSearchFrame = titleFrame.innerFrame
        advanceSearchFrame.pack()
        advanceSearchMainWin.iconbitmap(IconPath)
        advanceSearchMainWin.bind('<Escape>',titleFrame.quitter)
        advanceSearchMainWin.bind('<Return>',lambda e:start_Search())
        advanceSearchMainWin.protocol('WM_DELETE_WINDOW',quitSearch)
        advanceSearchMainWin.title('装备专用搜索')
        advanceSearchMainWin.resizable(False,False)

        row = 1
        tk.Label(advanceSearchFrame,text='关键词：').grid(row=row,column=3)
        nameE = ttk.Entry(advanceSearchFrame,width=int(WIDTH*10))
        nameE.grid(row=row,column=4,sticky='nswe')

        row += 1
        useFuzzyVar = tk.IntVar()
        useFuzzyVar.set(0)
        useFuzzyBtn = ttk.Checkbutton(advanceSearchFrame,text='启用模糊搜索',variable=useFuzzyVar,command=lambda:useFuzzyVar.get())
        useFuzzyBtn.grid(row=row,column=4,sticky='nswe')
        CreateToolTip(useFuzzyBtn,text='会花费更多时间')

        row += 1
        usePVFInfoVar = tk.IntVar()
        usePVFInfoVar.set(0)
        usePVFInfoBtn = ttk.Checkbutton(advanceSearchFrame,text='搜索PVF文本',variable=usePVFInfoVar,command=lambda:usePVFInfoVar.get())
        usePVFInfoBtn.grid(row=row,column=4,sticky='nswe')
        CreateToolTip(usePVFInfoBtn,text='同时在PVF文本内搜索关键词')

        row += 1
        def setType2(e):
            type1 = typeE.get()
            if type1!=ALLTYPE:
                typeE2.config(values=[ALLTYPE]+list(cacheM.equipmentForamted[type1].keys()),state='readonly')
            else:
                typeE2.config(values=[],state='disable')
                typeE3.config(values=[],state='disable')
            typeE2.set(ALLTYPE)
            typeE3.set(ALLTYPE)
        def setType3(e):
            type1 = typeE.get()
            type2 = typeE2.get()
            if type2!=ALLTYPE and type1 not in ['首饰','特殊装备']:
                typeE3.config(values=[ALLTYPE]+list(cacheM.equipmentForamted[type1][type2].keys()),state='readonly')
            else:
                typeE3.config(values=[],state='disable')
            typeE3.set(ALLTYPE)

        tk.Label(advanceSearchFrame,text='大类：').grid(row=row,column=3)
        ALLTYPE = '----'
        typeE = ttk.Combobox(advanceSearchFrame,width=int(WIDTH*10),values=[ALLTYPE,*cacheM.equipmentForamted.keys()],state='readonly')
        typeE.set(ALLTYPE)
        typeE.bind('<<ComboboxSelected>>',setType2)
        typeE.grid(row=row,column=4,sticky='nswe')
        row += 1
        tk.Label(advanceSearchFrame,text='小类：').grid(row=row,column=3)
        typeE2 = ttk.Combobox(advanceSearchFrame,width=int(WIDTH*10),state='disable')
        typeE2.bind('<<ComboboxSelected>>',setType3)
        typeE2.grid(row=row,column=4,sticky='nswe')
        row += 1
        tk.Label(advanceSearchFrame,text='子类：').grid(row=row,column=3)
        typeE3 = ttk.Combobox(advanceSearchFrame,width=int(WIDTH*10),state='disable')
        typeE3.grid(row=row,column=4,sticky='nswe')
        row += 1
        tk.Label(advanceSearchFrame,text='稀有度：').grid(row=row,column=3)
        rarityE = ttk.Combobox(advanceSearchFrame,values=['----',*list(rarityMapRev.keys())],width=int(WIDTH*10),state='readonly')
        rarityE.set('----')
        rarityE.grid(row=row,column=4,sticky='nswe')
        row += 1
        tk.Label(advanceSearchFrame,text='等级：').grid(row=row,column=3)
        minLevE = ttk.Spinbox(advanceSearchFrame,from_=0,to=999,width=int(WIDTH*4))
        minLevE.grid(row=row,column=4,sticky='w')
        tk.Label(advanceSearchFrame,text='-').grid(row=row,column=4)
        maxLevE = ttk.Spinbox(advanceSearchFrame,from_=0,to=999,width=int(WIDTH*4))
        maxLevE.grid(row=row,column=4,sticky='e')
        row += 1
        btnFrame = tk.Frame(advanceSearchFrame)
        btnFrame.grid(row=row,column=3,columnspan=2,sticky='ns',pady=PADY*5)
        ttk.Button(btnFrame,text='查询',command=start_Search).grid(row=row,column=3)
        commitBtn = ttk.Button(btnFrame,text='提交',command=apply_Search_result)
        commitBtn.grid(row=row,column=4)  
        CreateToolTip(commitBtn,'提交至物品编辑框')
        padFrame = tk.Frame(advanceSearchFrame)
        padFrame.grid(row=1,column=2,sticky='nswe',padx=PADX*2)
        padFrame = tk.Frame(advanceSearchFrame)
        padFrame.grid(row=1,column=7,sticky='nswe',padx=PADX*2)

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
            res = cacheM.get_Item_Info_In_Text(itemID).replace(r'%%',r'%').strip()
            overViewTip = CreateOnceToolTip(searchResultTreeView,text=res,xy=[x,y])
            titleFrame.title_label.config(text='点击提交将已选结果提交至物品编辑栏')

        searchResultTreeView.bind("<Button-1>",lambda e:self.w.after(100,lambda:show_overview(e)))
        overViewTip:ToolTip = CreateOnceToolTip(searchResultTreeView)
        
    def open_advance_search_stackable(self):
        from titleBar import TitleBarFrame
        def start_Search():
            for child in searchResultTreeView.get_children():
                searchResultTreeView.delete(child)
            searchDict = cacheM.stackableDict.copy()
            
            res = []
            nameKey = nameE.get()
            usePVF = usePVFInfoVar.get()
            type = typeE.get()
            levMin = int(0 if minLevE.get()=='' else minLevE.get())
            levMax = int(999 if maxLevE.get()=='' else maxLevE.get())
            raritykey = rarityE.get()
            if nameKey!='':
                if usePVF:
                    for id in searchDict.keys():
                        searchDict[id] = searchDict[id] + '\n' + cacheM.get_Item_Info_In_Text(id).replace(r'%%',r'%').strip()
                useFuzzy = useFuzzyVar.get()
                searchList = cacheM.searchItem(nameKey,list(searchDict.items()),fuzzy=useFuzzy)
            else:
                searchList = list(searchDict.items())
            if levMax==999 and levMin==0 and raritykey=='----':
                searchList = list(searchList)[:10000]

            for itemID,nameAndContent in searchList:
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
                    itemType = typeInList[0][1:-1]
                else:
                    itemType = None
                
                if type!='----' and itemType not in cacheM.formatedTypeDict[type].keys():
                    continue

                resType = cacheM.typeDict.get(itemType)
                if resType is not None:     #转换为中文，没有记录则显示原文
                    resType = resType[1]
                else:
                    resType = itemType
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
            typeID,itemTypeZh = cacheM.getStackableTypeMainIdAndZh(itemID)
            
            if frame_id > len(self.tabNames):
                return False
            itemSlot = sqlM.DnfItemSlot(b'\x00'*61)
            itemSlot.id = itemID
            itemSlot.type = typeID
            itemSlot.durability = 0
            itemSlot.num_grade = 1
            itemSlot.oriBytes = itemSlot.build_bytes()
            self.editFrameUpdateFuncs[self.tabNames[frame_id]](itemSlot)
            self.w.focus_force()
            self.w.title('本地物品信息已修改，请注意种类与位置是否匹配')

        def quitSearch():
            advanceSearchMainWin.destroy()
            self.Advance_Search_State_FLG_Stackable=False

        if self.Advance_Search_State_FLG_Stackable==True:
            self.advanceStkSearchMainFrame.wm_attributes('-topmost', 1)
            self.advanceStkSearchMainFrame.wm_attributes('-topmost', 0)
            return False
        self.Advance_Search_State_FLG_Stackable = True
        advanceSearchMainWin = tk.Toplevel(self.advanceSearchBtn)
        #advanceSearchMainFrame.wm_attributes('-topmost', 1)
        #advanceSearchMainWin.wm_overrideredirect(1)
        advanceSearchMainWin.iconbitmap(IconPath)
        advanceSearchMainWin.wm_geometry("+%d+%d" % (self.advanceSearchBtn.winfo_rootx(), self.advanceSearchBtn.winfo_rooty()))
        self.advanceStkSearchMainFrame = advanceSearchMainWin
        titleFrame = TitleBarFrame(advanceSearchMainWin,advanceSearchMainWin,'道具专用搜索')
        titleFrame.pack(fill=tk.X,expand=1,anchor=tk.N)  
        advanceSearchFrame = titleFrame.innerFrame
        advanceSearchFrame.pack()
        advanceSearchMainWin.bind('<Escape>',titleFrame.quitter)
        advanceSearchMainWin.bind('<Return>',lambda e:start_Search())
        advanceSearchMainWin.protocol('WM_DELETE_WINDOW',quitSearch)
        advanceSearchMainWin.title('道具专用搜索')
        advanceSearchMainWin.resizable(False,False)

        row = 1
        tk.Label(advanceSearchFrame,text='关键词：').grid(row=row,column=3)
        nameE = ttk.Entry(advanceSearchFrame,width=int(WIDTH*10))
        nameE.grid(row=row,column=4,sticky='nswe')

        row += 1
        useFuzzyVar = tk.IntVar()
        useFuzzyVar.set(0)
        useFuzzyBtn = ttk.Checkbutton(advanceSearchFrame,text='启用模糊搜索',variable=useFuzzyVar,command=lambda:useFuzzyVar.get())
        useFuzzyBtn.grid(row=row,column=4,sticky='nswe')
        CreateToolTip(useFuzzyBtn,text='会花费更多时间')

        row += 1
        usePVFInfoVar = tk.IntVar()
        usePVFInfoVar.set(0)
        usePVFInfoBtn = ttk.Checkbutton(advanceSearchFrame,text='搜索PVF文本',variable=usePVFInfoVar,command=lambda:usePVFInfoVar.get())
        usePVFInfoBtn.grid(row=row,column=4,sticky='nswe')
        CreateToolTip(usePVFInfoBtn,text='同时在PVF文本内搜索关键词')

        row += 1
        tk.Label(advanceSearchFrame,text='分类：').grid(row=row,column=3)
        ALLTYPE = '----'
        typeE = ttk.Combobox(advanceSearchFrame,width=int(WIDTH*10),values=[ALLTYPE,*cacheM.formatedTypeDict.keys()],state='readonly')
        typeE.set(ALLTYPE)
        typeE.grid(row=row,column=4,sticky='nswe')
        

        row += 1
        tk.Label(advanceSearchFrame,text='稀有度：').grid(row=row,column=3)
        rarityE = ttk.Combobox(advanceSearchFrame,values=['----',*list(rarityMapRev.keys())],width=int(WIDTH*10),state='readonly')
        rarityE.set('----')
        rarityE.grid(row=row,column=4,sticky='nswe')
        row += 1
        tk.Label(advanceSearchFrame,text='等级：').grid(row=row,column=3)
        minLevE = ttk.Spinbox(advanceSearchFrame,from_=0,to=999,width=int(WIDTH*4))
        minLevE.grid(row=row,column=4,sticky='w')
        tk.Label(advanceSearchFrame,text='-').grid(row=row,column=4)
        maxLevE = ttk.Spinbox(advanceSearchFrame,from_=0,to=999,width=int(WIDTH*4))
        maxLevE.grid(row=row,column=4,sticky='e')
        row += 1
        btnFrame = tk.Frame(advanceSearchFrame)
        btnFrame.grid(row=row,column=3,columnspan=2,sticky='ns',pady=PADY*5)
        ttk.Button(btnFrame,text='查询',command=start_Search).grid(row=row,column=3)
        commitBtn = ttk.Button(btnFrame,text='提交',command=apply_Search_result)
        commitBtn.grid(row=row,column=4)  
        CreateToolTip(commitBtn,'提交至物品编辑框')
        padFrame = tk.Frame(advanceSearchFrame)
        padFrame.grid(row=1,column=2,sticky='nswe',padx=PADX*2)
        padFrame = tk.Frame(advanceSearchFrame)
        padFrame.grid(row=1,column=7,sticky='nswe',padx=PADX*2)

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
            res = cacheM.get_Item_Info_In_Text(itemID).replace(r'%%',r'%').strip()
            overViewTip = CreateOnceToolTip(searchResultTreeView,text=res,xy=[x,y])
            titleFrame.title_label.config(text='点击提交将已选结果提交至物品编辑栏')

        searchResultTreeView.bind("<Button-1>",lambda e:self.w.after(100,lambda:show_overview(e)))
        overViewTip:ToolTip = CreateOnceToolTip(searchResultTreeView)

    def open_PVF_Cache_Edit(self):
        def quit_edit():
            pvfEditMainWin.destroy()
            self.PVF_EDIT_OPEN_FLG = False
        def update_pvf_cache_sel():
            res = []
            for MD5,infoDict in cacheM.cacheManager.tinyCache.items():
                if not isinstance(infoDict,dict):continue
                res.append(f'{infoDict["nickName"]}-{MD5}')
            self.pvfComboBox.config(values=res)
            pvfMD5 = self.pvfComboBox.get().split('-')[-1]
            if len(pvfMD5)>0:
                if cacheM.cacheManager.tinyCache.get(pvfMD5) is None:
                    self.pvfComboBox.set(f'请选择PVF缓存')
                else:
                    self.pvfComboBox.set(f'{cacheM.cacheManager.tinyCache[pvfMD5].get("nickName")}-{pvfMD5}')
            self.titleLog('PVF缓存已保存')
        from pvfCacheFrame import PVFCacheCfgFrame
        if self.PVF_EDIT_OPEN_FLG:
            self.pvfEditWin.wm_attributes('-topmost', 1)
            self.pvfEditWin.wm_attributes('-topmost', 0)
            self.cacheEditFrame.fillTree()
            return False
        self.PVF_EDIT_OPEN_FLG = True
        pvfEditMainWin = tk.Toplevel(self.tabView)
        #pvfEditMainFrame.wm_attributes('-topmost', 1)
        #pvfEditMainFrame.wm_attributes('-topmost', 0)
        #pvfEditMainFrame.wm_overrideredirect(1)
        pvfEditMainWin.wm_geometry("+%d+%d" % (self.advanceSearchBtn.winfo_rootx(), self.advanceSearchBtn.winfo_rooty()))
        self.pvfEditWin = pvfEditMainWin
        pvfEditMainWin.iconbitmap(IconPath)
        pvfEditFrame = PVFCacheCfgFrame(pvfEditMainWin,closeFunc=quit_edit,saveFunc=update_pvf_cache_sel)
        pvfEditFrame.pack(fill=tk.BOTH,expand=True,anchor=tk.N)
        pvfEditMainWin.bind('<Escape>',pvfEditFrame.quitter)
        self.cacheEditFrame = pvfEditFrame
        pvfEditMainWin.protocol('WM_DELETE_WINDOW',quit_edit)
        pvfEditMainWin.title('PVF缓存管理')
        pvfEditMainWin.resizable(False,True)
        self.PVFEditWinFrame = pvfEditFrame
        
    def build_GUI(self,w):  
        def tabView_Chance_Handler(e):
            for func in self.tabViewChangeFuncs:
                func(e)

        mainFrame = tk.Frame(w)
        mainFrame.pack(fill='both')
        self.mainFrame = mainFrame
        self._buildSqlConn(mainFrame)
        tabFrame = tk.Frame(mainFrame,borderwidth=0,width=613*WIDTH)
        #self.w.after(5000,lambda:print(tabFrame.winfo_width()))
        tabFrame.pack(expand=True,fill='both')
        tabView = ttk.Notebook(tabFrame,padding=[-3,0,-3,-3])
        tabView.grid(row=1,column=1,sticky='nswe')
        tabView.bind('<<NotebookTabChanged>>',tabView_Chance_Handler)
        advanceSearchBtn = tk.Button(tabFrame,text='装备搜索', relief=tk.FLAT,font=('', 10, 'underline'),command=self.open_advance_search_equipment)
        self.advanceSearchBtn = advanceSearchBtn
        advanceSearchBtn.grid(row=1,column=1,sticky='ne',padx=PADX*5)

        advanceSearchBtn2 = tk.Button(tabFrame,text='道具搜索', relief=tk.FLAT,font=('', 10, 'underline'),command=self.open_advance_search_stackable)
        self.advanceSearchBtn2 = advanceSearchBtn2
        advanceSearchBtn2.grid(row=1,column=1,sticky='ne',padx=PADX*80)

        self.refreshBtn = tk.Button(tabFrame,text='刷新背包', relief=tk.FLAT,font=('', 10, 'underline'))
        self.refreshBtn.grid(row=1,column=1,sticky='ne',padx=PADX*155)
        self.tabView = tabView
        
        self._buildtab_main(tabView)
        
        self.itemsTreevs_now = {}
        self.itemsTreevs_del = {}

        treeViewArgs = {
            "columns":['1','2','3','4'],
            'show':'headings',
            'column':{
                '1':{'width':int(30*WIDTH), 'anchor':'c'},
                '2':{'width':int(138*WIDTH), 'anchor':'se'},
                '3':{'width':int(40*WIDTH), 'anchor':'se'},
                '4':{'width':int(70*WIDTH), 'anchor':'se'},
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
        #return False
        treeViewArgs = {
            "columns":['1','2','3','4'],
            'show':'headings',
            'column':{
                '1':{'width':int(30*WIDTH), 'anchor':'c'},
                '2':{'width':int(128*WIDTH), 'anchor':'se'},
                '3':{'width':int(60*WIDTH), 'anchor':'se'},
                '4':{'width':int(60*WIDTH), 'anchor':'se'},
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
                '1':{'width':int(60*WIDTH), 'anchor':'c'},
                '2':{'width':int(128*WIDTH), 'anchor':'se'},
                '3':{'width':int(90*WIDTH), 'anchor':'se'},
                },
            'heading':{
                '1':{'text':' '},
                '2':{'text':'装扮名称'},
                '3':{'text':'装扮id'},
            }
        }
        tabName = ' 时装 '
        self._buildtab_itemTab_2(tabView,tabName,treeViewArgs)

        treeViewArgs = {
            "columns":['1','2','3','4'],
            'show':'headings',
            'column':{
                '1':{'width':int(38*WIDTH), 'anchor':'c'},
                '2':{'width':int(110*WIDTH), 'anchor':'se'},
                '3':{'width':int(90*WIDTH), 'anchor':'se'},
                '4':{'width':int(40*WIDTH), 'anchor':'se'},
                },
            'heading':{
                '1':{'text':' '},
                '2':{'text':'物品名'},
                '3':{'text':'发件人'},
                '4':{'text':'类型'},
            }
        }
        tabName = ' 邮件 '
        self._buildtab_itemTab_2(tabView,tabName,treeViewArgs)
        self._buildtab_charac(tabView,' 其它 ')

    def connectSQL(self):
        def inner():
            config = cacheM.config
            config['DB_IP'] = self.db_ip.get()
            config['DB_PORT'] = int(self.db_port.get())
            config['DB_USER'] = self.db_user.get()
            config['DB_PWD'] = self.db_pwd.get()
            config['PVF_PATH'] = cacheM.config.get('PVF_PATH')
            log(str(config))
            cacheM.config = config
            sqlresult = sqlM.connect(self.titleLog)
            if '失败' not in sqlresult:  
                self.accountBtn.config(state='normal')
                self.characBtn.config(state='normal')
                #self.connectorE.config(values=[f'{i}-'+str(connector['account_db']) for i,connector in enumerate(sqlM.connectorAvailuableDictList)])
                self.connectorE.config(values=[f'{i}-'+str(connector) for i,connector in enumerate(sqlM.connectorAvailuableList)])
                #self.connectorE.set(f"0-{sqlM.connectorAvailuableDictList[0]['account_db']}")
                self.connectorE.set(f"0-{sqlM.connectorAvailuableList[0]}")
                onlineCharacs = sqlM.get_online_charac()
                self.fillCharac(onlineCharacs)
                self.titleLog(f'当前在线角色已加载({len(onlineCharacs)})')
                if self.GM_Tool_Flg:
                    self.GMTool.update_Info()
            self.titleLog(sqlresult)
            self.db_conBTN.config(text='重新连接',state='normal')
            CreateToolTip(self.db_conBTN,'重新连接数据库并加载在线角色列表')
            self.CONNECT_FLG = False
            
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
        for i in range(1,len(globalBlobs_map.keys()) + 2 + len(globalNonBlobs_map.keys())):
            self.tabView.tab(i,state='disable')
    
    def check_Update(self):
        import subprocess, os
        def update_fin():
            openACK = messagebox.askyesno('下载完成','是否打开文件位置？')
            if openACK:
                openDirCMD = f'explorer.exe /select,{updateM.targetPath}'
                subprocess.Popen(openDirCMD,shell=False)
        def inner():
            self.titleLog('检查更新中...')
            updateState = updateM.check_Update()
            #self.titleLog(f'更新状态：{updateState}')
            if updateState:
                
                self.titleLog(f'有文件更新 {updateM.versionDict_remote["URL"]}')
                fileName = updateM.versionDict_remote.get("URL").rsplit("/",1)[-1]
                print('文件名：',fileName,updateM.versionDict_remote.get("URL"))
                updateACK = messagebox.askyesno('有软件更新！',f'是否下载最新版本？也可点击其他页面GitHub图标手动下载\n最新版本号：{updateM.versionDict_remote.get("VERSION")} {fileName}\n{updateM.versionDict_remote.get("INFO")}')
                if updateACK and updateM.targetPath.exists():
                    updateACK = messagebox.askyesno('目标文件已存在！','是否覆盖已下载版本？')
                if updateACK:
                    updateM.get_Update2(update_fin)
                    self.titleLog(f'正在下载最新版本...{updateM.versionDict_remote["VERSION"]}')
        t = threading.Thread(target=inner)
        t.setDaemon(True)
        t.start()
def get_pool():
    import multiprocessing
    def inner():
        global pool
        try:
            pool.close()
        except:
            pass
        cores = multiprocessing.cpu_count()
        taskNum = 6
        processNum = min(cores,taskNum)
        pool = multiprocessing.Pool(processes=processNum)
        print(f'进程池已启动({processNum})')
        return pool
    t = threading.Thread(target=inner)
    t.start()

if __name__=='__main__':
    a = App()    
    a.w.after(2000,a.connectSQL)
    def print2title(*args):
        for arg in args:
            print(arg)
            a.titleLog(str(arg))
    cacheM.pvfReader.print = print2title
    cacheM.print = print2title
    updateM.print = print2title
    ps.print = print2title
    a.w.resizable(False,False)
    pool = None
    #get_pool()
    a._open_GM()
    #a.check_Update()
    def resize():
        oldsize = get_tk_size_dict(a.w)
    a.w.after(2000,resize)
    a.w.mainloop()
    
    for connector in sqlM.connectorAvailuableList:
        try:
            connector.close()
        except:
            pass
    if pool is not None:
        pool.close()
