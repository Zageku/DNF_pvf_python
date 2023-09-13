import tkinter as tk
import tkinter.ttk as ttk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename

if __name__=='__main__':
    import os
    import sys 
    sys.path.append(os.getcwd())
    sys.path.append(os.path.join(os.getcwd(),'dnfpkgtool'))
from dnfpkgtool import itemSlotFrame
from dnfpkgtool import creatureFeame
from dnfpkgtool import avatarFrame
from dnfpkgtool import mailFrame
from dnfpkgtool import characFrame
from dnfpkgtool import msgFrame
import threading
from dnfpkgtool import cacheManager as cacheM
from dnfpkgtool import updateManager as updateM
from dnfpkgtool import sqlManager2 as sqlM
from pathlib import Path
import time
from copy import deepcopy
import struct
from dnfpkgtool.widgets.toolTip import CreateToolTip, CreateOnceToolTip, ToolTip
from dnfpkgtool.widgets.imageLabel import ImageLabel
from dnfpkgtool import ps
import webbrowser
from dnfpkgtool.widgets.titleBar import TitleBarFrame
from dnfpkgtool import gmTool_resize as gmToolGUI
from dnfpkgtool import pvfEditorGUI

WIDTH = 1

oldPrint = print
logFunc = [oldPrint]
def print(*args,**kw):
    try:
        if len(args)==1:
            text = str(args[0])
            root.title(text)
        else:
            text = str(args)
    except:
        pass
    logFunc[-1](*args,**kw)

def inThread(func):
    def inner(*args,**kw):
        t = threading.Thread(target=lambda:func(*args,**kw))
        t.setDaemon(True)
        t.start()
        return t
    return inner

VerInfo = cacheM.config['VERSION']#'Ver.0.2.23'
logPath = Path('log/')
gifPath_1 = Path('config/gif')
gifPath_2 = Path('config/gif2')
gitHubLogoPath = Path('config/github.png')
IconPath = 'config/ico.png'
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
        ' 仓库 ':'cargo',
        '账号金库':'account_cargo'
    }
globalNonBlobs_map = {
    ' 宠物 ':'creature_items',
    ' 时装 ':'user_items',
    ' 邮件 ':'user_postals'
    }

tabIDDict = {}

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

def configFrame(frame:tk.Frame,state='disable'):
    for widget in frame.children.values():
        if type(widget) in [tk.Frame,tk.LabelFrame,ttk.LabelFrame,ttk.Frame]:
            configFrame(widget,state)
        else:
            try:
                widget.config(state=state)
            except:
                continue

def openWeb(e=None): 
    webbrowser.open(cacheM.config['TIEBA'])
    webbrowser.open(cacheM.config['GITHUB'])
    webbrowser.open(cacheM.config['QQ'])
    webbrowser.open(cacheM.config['PROVIDER'])

class GitHubFrame(tk.Frame):
    def __init__(self,*args,**kw):
        tk.Frame.__init__(self,*args,**kw)
        gitHubLogo = ImageLabel(self)
        gitHubLogo.pack()
        
        gitHubLogo.load(gitHubLogoPath,[150,150])
        gitHubLogo.bind('<Button-1>',openWeb)
        CreateToolTip(self,f'点击加入群聊查看最新动态')

letter_send_dict = {}
class GuiApp:
    def __init__(self, master=None, check_update=True):
        # build ui
        self.mainFrame = ttk.Frame(master)
        self.mainFrame.configure(height=500, width=700)
        frame2 = ttk.Frame(self.mainFrame)
        frame2.configure(height=200, width=200)
        label1 = ttk.Label(frame2)
        label1.configure(text='数据库IP')
        label1.pack(padx=3, side="left")
        self.db_ipE = ttk.Combobox(frame2)
        self.db_ipE.pack(expand="true", fill="x", side="left")
        self.db_ipE.bind("<<ComboboxSelected>>", self.sel_IP, add="")
        label2 = ttk.Label(frame2)
        label2.configure(text='端口')
        label2.pack(padx=3, side="left")
        self.db_portE = ttk.Entry(frame2)
        self.db_portE.configure(width=8)
        self.db_portE.pack(expand="true", fill="x", side="left")
        label3 = ttk.Label(frame2)
        label3.configure(text='用户名')
        label3.pack(padx=3, side="left")
        self.db_userE = ttk.Entry(frame2)
        self.db_userE.configure(width=10)
        self.db_userE.pack(expand="true", fill="x", side="left")
        label4 = ttk.Label(frame2)
        label4.configure(text='密码')
        label4.pack(padx=3, side="left")
        self.db_pwdE = ttk.Combobox(frame2)
        self.db_pwdE.configure(width=10)
        self.db_pwdE.pack(expand="true", fill="x", side="left")
        self.db_conBTN = ttk.Button(frame2)
        self.db_conBTN.configure(text='连接数据库')
        self.db_conBTN.pack(expand="true", fill="x", padx=3, side="left")
        self.db_conBTN.configure(command=self.connectSQL)
        frame2.pack(fill="x", side="top")
        separator1 = ttk.Separator(self.mainFrame)
        separator1.configure(orient="horizontal")
        separator1.pack(fill="x", pady=3, side="top")
        self.tabFrame = ttk.Frame(self.mainFrame)
        self.tabFrame.configure(height=450, width=200)
        self.tabView = ttk.Notebook(self.tabFrame)
        self.tabView.configure(height=400, width=780)
        self.searchFrame = ttk.Frame(self.tabView)
        self.searchFrame.configure(height=200, width=200)
        frame13 = ttk.Frame(self.searchFrame)
        frame13.configure(height=200, width=200)
        labelframe1 = ttk.Labelframe(frame13)
        labelframe1.configure(height=200, text='账户查询', width=200)
        self.aNameE = ttk.Entry(labelframe1)
        self.aNameE.configure(width=15)
        self.aNameE.pack(expand="false", pady=1, side="top")
        self.accountSearchBtn = ttk.Button(labelframe1)
        self.accountSearchBtn.configure(state="disabled", text='查询/加载所有')
        self.accountSearchBtn.pack(
            expand="false", fill="x", pady=1, side="top")
        self.accountSearchBtn.configure(command=self.search_Account)
        labelframe1.pack(expand="true", fill="both", side="top")
        labelframe4 = ttk.Labelframe(frame13)
        labelframe4.configure(height=200, text='角色查询', width=200)
        self.cNameE = ttk.Entry(labelframe4)
        self.cNameE.configure(width=15)
        self.cNameE.pack(expand="false", pady=1, side="top")
        self.characSearchBtn = ttk.Button(labelframe4)
        self.characSearchBtn.configure(state="disabled", text='查询/加载在线')
        self.characSearchBtn.pack(expand="false", fill="x", pady=1, side="top")
        self.characSearchBtn.configure(command=self.search_Charac)
        labelframe4.pack(expand="true", fill="both", side="top")
        labelframe5 = ttk.Labelframe(frame13)
        labelframe5.configure(height=200, text='连接器及编码', width=200)
        self.connectorE = ttk.Combobox(labelframe5)
        self.connectorE.configure(width=10)
        self.connectorE.pack(expand="false", fill="x", pady=1, side="top")
        self.SqlEncodeE = ttk.Combobox(labelframe5)
        self.SqlEncodeE.configure(width=10)
        self.SqlEncodeE.pack(expand="false", fill="x", pady=1, side="top")
        self.SqlEncodeE.bind(
            "<<ComboboxSelected>>",
            self.sel_Sql_Encode,
            add="")
        labelframe5.pack(expand="true", fill="both", side="top")
        labelframe7 = ttk.Labelframe(frame13)
        labelframe7.configure(height=200, text='PVF数据', width=200)
        self.PVFCacheE = ttk.Combobox(labelframe7)
        self.PVFCacheE.configure(width=10)
        self.PVFCacheE.pack(expand="false", fill="x", pady=1, side="top")
        self.PVFCacheE.bind("<<ComboboxSelected>>", self.sel_PVF_Cache, add="")
        self.PVFEncodeE = ttk.Combobox(labelframe7)
        self.PVFEncodeE.configure(width=10)
        self.PVFEncodeE.pack(expand="false", fill="x", pady=1, side="top")
        self.openPVFBtn = ttk.Button(labelframe7)
        self.openPVFBtn.configure(text='读取PVF文件')
        self.openPVFBtn.pack(expand="false", fill="x", pady=1, side="top")
        self.openPVFBtn.configure(command=self.openPVF)
        labelframe7.pack(expand="true", fill="both", side="top")
        labelframe8 = ttk.Labelframe(frame13)
        labelframe8.configure(height=200, text='GM工具', width=200)
        self.GMtoolBtn = ttk.Button(labelframe8)
        self.GMtoolBtn.configure(text='旧GM工具')
        self.GMtoolBtn.pack(expand="false", fill="x", pady=1, side="top")
        self.GMtoolBtn.configure(command=self._open_GM)
        self.autoGMBtn = ttk.Checkbutton(labelframe8)
        self.autoGMVar = tk.IntVar()
        self.autoGMBtn.configure(text='启动时打开', variable=self.autoGMVar)
        self.autoGMBtn.pack(expand="false", pady=1, side="top")
        self.autoGMBtn.configure(command=self.set_gm_startup)
        labelframe8.pack(expand="true", fill="both", side="top")
        frame13.pack(fill="y", side="left")
        frame14 = ttk.Frame(self.searchFrame)
        frame14.configure(height=200, width=200)
        self.characTreeV = ttk.Treeview(frame14)
        self.characTreeV.configure(selectmode="browse", show="headings")
        self.characTreeV_cols = [
            'column1',
            'column2',
            'column3',
            'column4',
            'column5']
        self.characTreeV_dcols = [
            'column1',
            'column2',
            'column3',
            'column4',
            'column5']
        self.characTreeV.configure(
            columns=self.characTreeV_cols,
            displaycolumns=self.characTreeV_dcols)
        self.characTreeV.column(
            "column1",
            anchor="center",
            stretch="true",
            width=50,
            minwidth=20)
        self.characTreeV.column(
            "column2",
            anchor="center",
            stretch="true",
            width=120,
            minwidth=20)
        self.characTreeV.column(
            "column3",
            anchor="center",
            stretch="true",
            width=40,
            minwidth=20)
        self.characTreeV.column(
            "column4",
            anchor="center",
            stretch="true",
            width=60,
            minwidth=20)
        self.characTreeV.column(
            "column5",
            anchor="center",
            stretch="true",
            width=50,
            minwidth=20)
        self.characTreeV.heading("column1", anchor="center", text='角色ID')
        self.characTreeV.heading("column2", anchor="center", text='角色名')
        self.characTreeV.heading("column3", anchor="center", text='等级')
        self.characTreeV.heading("column4", anchor="center", text='职业')
        self.characTreeV.heading("column5", anchor="center", text='UID')
        self.characTreeV.pack(expand="true", fill="both", side="left")
        self.characTreeV.bind("<<TreeviewSelect>>", self.selectCharac, add="")
        self.characBar = ttk.Scrollbar(frame14)
        self.characBar.configure(orient="vertical")
        self.characBar.pack(fill="y", side="right")
        frame14.pack(expand="true", fill="both", side="left")
        self.imageFrame1 = ttk.Frame(self.searchFrame)
        self.imageFrame1.configure(borderwidth=0, height=200, width=200)
        self.imageFrame1.pack(fill="y", side="left")
        self.searchFrame.pack(side="top")
        self.tabView.add(self.searchFrame, text='查询')
        self.invFrame = ttk.Frame(self.tabView)
        self.invFrame.configure(height=200, width=200)
        self.invFrame.pack(side="top")
        self.tabView.add(self.invFrame, text='物品栏')
        self.equFrame = ttk.Frame(self.tabView)
        self.equFrame.configure(height=200, width=200)
        self.equFrame.pack(side="top")
        self.tabView.add(self.equFrame, text='穿戴栏')
        self.creatureFrame = ttk.Frame(self.tabView)
        self.creatureFrame.configure(height=200, width=200)
        self.creatureFrame.pack(side="top")
        self.tabView.add(self.creatureFrame, text='宠物栏')
        self.cargoFrame = ttk.Frame(self.tabView)
        self.cargoFrame.configure(height=200, width=200)
        self.cargoFrame.pack(side="top")
        self.tabView.add(self.cargoFrame, text=' 仓库 ')
        self.accountCargoFrame = ttk.Frame(self.tabView)
        self.accountCargoFrame.configure(height=200, width=200)
        self.accountCargoFrame.pack(side="top")
        self.tabView.add(self.accountCargoFrame, text='账号金库')
        self.creatureItemFrame = ttk.Frame(self.tabView)
        self.creatureItemFrame.configure(height=200, width=200)
        self.creatureItemFrame.pack(side="top")
        self.tabView.add(self.creatureItemFrame, text=' 宠物 ')
        self.avatarFrame = ttk.Frame(self.tabView)
        self.avatarFrame.configure(height=200, width=200)
        self.avatarFrame.pack(side="top")
        self.tabView.add(self.avatarFrame, text=' 时装 ')
        self.mailF = ttk.Frame(self.tabView)
        self.mailF.configure(height=200, width=200)
        self.mailFrame = ttk.Frame(self.mailF)
        self.mailFrame.configure(height=200, width=200)
        self.mailFrame.pack(expand="true", fill="both", side="left")
        self.sendMailF = ttk.Labelframe(self.mailF)
        self.sendMailF.configure(height=200, text='发送邮件', width=150)
        frame6 = ttk.Frame(self.sendMailF)
        frame6.configure(height=200, width=200)
        self.itemBasicInfoFrame = ttk.Frame(frame6)
        self.itemBasicInfoFrame.configure(height=200, width=200)
        self.itemEditFrame = ttk.Frame(self.itemBasicInfoFrame)
        self.itemEditFrame.configure(height=200, width=200)
        self.itemSealBtn = ttk.Checkbutton(self.itemEditFrame)
        self.itemSealVar = tk.IntVar()
        self.itemSealBtn.configure(text='封装', variable=self.itemSealVar)
        self.itemSealBtn.grid(column=0, row=0)
        self.itemNameEntry = ttk.Combobox(self.itemEditFrame)
        self.itemNameEntry.configure(width=12)
        self.itemNameEntry.grid(column=1, columnspan=2, row=0, sticky="ew")
        self.itemNameEntry.bind(
            "<<ComboboxSelected>>",
            self.readSlotName,
            add="")
        self.itemNameEntry.bind("<Button-1>", self.searchItem, add="")
        self.itemIDEntry = ttk.Entry(self.itemEditFrame)
        self.itemIDEntry.configure(width=10)
        self.itemIDEntry.grid(column=1, columnspan=2, row=2, sticky="ew")
        self.itemIDEntry.bind("<FocusOut>", self.readSlotID, add="")
        self.numGradeLabel = ttk.Label(self.itemEditFrame)
        self.numGradeLabel.configure(text='数量：')
        self.numGradeLabel.grid(column=0, row=3)
        label17 = ttk.Label(self.itemEditFrame)
        label17.configure(text='增幅：')
        label17.grid(column=0, row=4)
        label18 = ttk.Label(self.itemEditFrame)
        label18.configure(text='强化：')
        label18.grid(column=0, row=5)
        label19 = ttk.Label(self.itemEditFrame)
        label19.configure(text='锻造：')
        label19.grid(column=0, row=6)
        self.numEntry = ttk.Spinbox(self.itemEditFrame)
        self.numEntry.configure(from_=0, to=999999999, width=16)
        self.numEntry.grid(column=1, row=3, sticky="nsew")
        label20 = ttk.Label(self.itemEditFrame)
        label20.configure(text='耐久：')
        label20.grid(column=2, padx=3, row=3, sticky="w")
        self.durabilityEntry = ttk.Spinbox(self.itemEditFrame)
        self.durabilityEntry.configure(from_=0, to=9999, width=6)
        self.durabilityEntry.grid(column=2, row=3, sticky="e")
        self.IncreaseTypeEntry = ttk.Combobox(self.itemEditFrame)
        self.IncreaseTypeEntry.configure(width=8)
        self.IncreaseTypeEntry.grid(column=1, row=4, sticky="ew")
        self.EnhanceEntry = ttk.Spinbox(self.itemEditFrame)
        self.EnhanceEntry.configure(from_=0, to=999, width=8)
        self.EnhanceEntry.grid(column=1, pady=0, row=5, sticky="nsew")
        self.forgingEntry = ttk.Spinbox(self.itemEditFrame)
        self.forgingEntry.configure(from_=0, to=999, width=8)
        self.forgingEntry.grid(column=1, pady=0, row=6, sticky="ew")
        self.IncreaseEntry = ttk.Spinbox(self.itemEditFrame)
        self.IncreaseEntry.configure(from_=0, to=99999, width=12)
        self.IncreaseEntry.grid(column=2, row=4, sticky="nsew")
        self.typeEntry = ttk.Combobox(self.itemEditFrame)
        self.typeEntry.configure(width=8)
        self.typeEntry.grid(column=2, row=5, sticky="ew")
        self.typeEntry.bind(
            "<<ComboboxSelected>>",
            self.changeItemSlotType,
            add="")
        self.goldLabel = ttk.Label(self.itemEditFrame)
        self.goldLabel.configure(text='金币：')
        self.goldLabel.grid(column=2, padx=3, row=6, sticky="w")
        self.goldE = ttk.Spinbox(self.itemEditFrame)
        self.goldE.configure(from_=0, to=9999999999999999, width=6)
        self.goldE.grid(column=2, row=6, sticky="e")
        self.itemIDLabel = ttk.Label(self.itemEditFrame)
        self.itemIDLabel.configure(text='ID：')
        self.itemIDLabel.grid(column=0, row=2)
        self.itemEditFrame.grid(column=0, columnspan=3, row=0, sticky="nsew")
        self.itemEditFrame.columnconfigure("all", weight=1)
        label23 = ttk.Label(self.itemBasicInfoFrame)
        label23.configure(text='发件人：')
        label23.grid(column=0, pady=2, row=8)
        self.senderE = ttk.Combobox(self.itemBasicInfoFrame)
        self.senderE.configure(width=20)
        self.senderE.grid(column=1, columnspan=2, row=8, sticky="ew")
        label24 = ttk.Label(self.itemBasicInfoFrame)
        label24.configure(text='内容：')
        label24.grid(column=0, pady=2, row=9)
        self.msgE = ttk.Combobox(self.itemBasicInfoFrame)
        self.msgE.configure(width=12)
        self.msgE.grid(column=1, columnspan=2, row=9, sticky="ew")
        frame8 = ttk.Frame(self.itemBasicInfoFrame)
        frame8.configure(height=200, width=200)
        frame9 = ttk.Frame(frame8)
        frame9.configure(height=200, width=200)
        self.send2currentBtn = ttk.Button(frame9)
        self.send2currentBtn.configure(text='发送到当前角色')
        self.send2currentBtn.grid(column=0, row=0, sticky="ew")
        self.send2allBtn = ttk.Button(frame9)
        self.send2allBtn.configure(text='发送到全服角色')
        self.send2allBtn.grid(column=0, row=1, sticky="ew")
        self.send2VIPaBtn = ttk.Button(frame9)
        self.send2VIPaBtn.configure(text='发送到VIP账号')
        self.send2VIPaBtn.grid(column=0, row=2, sticky="ew")
        self.clearMailBtn = ttk.Button(frame9)
        self.clearMailBtn.configure(text='清空全服邮件')
        self.clearMailBtn.grid(column=1, row=0, sticky="ew")
        self.send2onlineBtn = ttk.Button(frame9)
        self.send2onlineBtn.configure(text='发送到在线角色')
        self.send2onlineBtn.grid(column=1, row=1, sticky="ew")
        self.send2VIPcBtn = ttk.Button(frame9)
        self.send2VIPcBtn.configure(text='发送到VIP角色')
        self.send2VIPcBtn.grid(column=1, row=2, sticky="ew")
        frame9.pack(expand="true", fill="x", side="top")
        frame9.columnconfigure("all", weight=1)
        frame8.grid(column=0, columnspan=3, row=10, sticky="nsew")
        separator6 = ttk.Separator(self.itemBasicInfoFrame)
        separator6.configure(orient="horizontal")
        separator6.grid(columnspan=3, pady=2, row=7, sticky="ew")
        self.itemBasicInfoFrame.pack(expand="true", fill="both", side="right")
        self.itemBasicInfoFrame.columnconfigure(0, pad=3)
        self.itemBasicInfoFrame.columnconfigure(1, weight=2)
        self.itemBasicInfoFrame.columnconfigure(2, weight=1)
        self.itemBasicInfoFrame.columnconfigure("all", pad=3)
        frame6.pack(expand="true", fill="both", side="left")
        self.sendMailF.pack(expand="false", fill="both", side="right")
        self.mailF.pack(side="top")
        self.tabView.add(self.mailF, text=' 邮件 ')
        self.characMainFrame = ttk.Frame(self.tabView)
        self.characMainFrame.configure(height=200, width=200)
        frame3 = ttk.Frame(self.characMainFrame)
        frame3.configure(height=200, width=200)
        self.otherFunctionFrame = ttk.Labelframe(frame3)
        self.otherFunctionFrame.configure(height=200, text='附加功能', width=160)
        frame7 = ttk.Frame(self.otherFunctionFrame)
        frame7.configure(height=100, width=150)
        self.saveStartBtn = ttk.Button(frame7)
        self.saveStartBtn.configure(text='生成一键启动器')
        self.saveStartBtn.pack(fill="x", pady=1, side="top")
        self.saveStartBtn.configure(command=self.saveStart)
        self.pvfCacheMBtn = ttk.Button(frame7)
        self.pvfCacheMBtn.configure(text='PVF缓存管理器')
        self.pvfCacheMBtn.pack(fill="x", pady=1, side="top")
        self.pvfCacheMBtn.configure(command=self.open_PVF_Cache_Edit)
        self.pvfToolBtn = ttk.Button(frame7)
        self.pvfToolBtn.configure(text='PVF工具')
        self.pvfToolBtn.pack(fill="x", pady=1, side="top")
        self.pvfToolBtn.configure(command=self._open_PVF_Editor)
        self.enableAuctionBtn = ttk.Button(frame7)
        self.enableAuctionBtn.configure(text='启用拍卖行')
        self.enableAuctionBtn.pack(fill="x", pady=1, side="top")
        self.enableAuctionBtn.configure(command=self.enable_auction)
        self.checkUpdateBtn = ttk.Checkbutton(frame7)
        self.updateCheckVar = tk.IntVar()
        self.checkUpdateBtn.configure(
            text='自动检查更新', variable=self.updateCheckVar)
        self.checkUpdateBtn.pack(expand="true", side="top")
        self.HDresolutionBtn = ttk.Checkbutton(frame7)
        self.HDResolutionVar = tk.IntVar()
        self.HDresolutionBtn.configure(
            text='高分辨率缩放', variable=self.HDResolutionVar)
        self.HDresolutionBtn.pack(expand="true", side="top")
        frame7.pack(expand="true", fill="both", padx=3, side="top")
        self.otherFunctionFrame.pack(fill="y", side="left")
        self.gitHubFrame = ttk.Frame(frame3)
        self.gitHubFrame.configure(height=160, width=160)
        self.gitHubFrame.pack(side="right")
        labelframe2 = ttk.Labelframe(frame3)
        labelframe2.configure(height=200, text='服务器管理', width=200)
        frame10 = ttk.Frame(labelframe2)
        frame10.configure(height=200, width=200)
        frame11 = ttk.Frame(frame10)
        frame11.configure(height=200, width=200)
        label32 = ttk.Label(frame11)
        label32.configure(text='服务器IP')
        label32.pack(side="left")
        self.ipE2 = ttk.Entry(frame11)
        self.ipE2.configure(width=15)
        self.ipE2.pack(expand="false", fill="x", side="left")
        label33 = ttk.Label(frame11)
        label33.configure(text='端口')
        label33.pack(side="left")
        self.portE2 = ttk.Entry(frame11)
        self.portE2.configure(width=4)
        self.portE2.pack(side="left")
        label34 = ttk.Label(frame11)
        label34.configure(text='用户名')
        label34.pack(side="left")
        self.userE2 = ttk.Entry(frame11)
        self.userE2.configure(width=6)
        self.userE2.pack(side="left")
        label35 = ttk.Label(frame11)
        label35.configure(text='密码')
        label35.pack(side="left")
        self.pwdE2 = ttk.Entry(frame11)
        self.pwdE2.configure(width=10)
        self.pwdE2.pack(expand="true", fill="x", side="top")
        frame11.pack(fill="x", side="top")
        frame12 = ttk.Frame(frame10)
        frame12.configure(height=200, width=200)
        self.sshConBtn = ttk.Button(frame12)
        self.sshConBtn.configure(text='连接服务器', width=8)
        self.sshConBtn.pack(expand="true", fill="x", side="left")
        self.SSHKeyConBtn = ttk.Button(frame12)
        self.SSHKeyConBtn.configure(text='密钥连接', width=8)
        self.SSHKeyConBtn.pack(expand="true", fill="x", side="left")
        self.runServerBtn = ttk.Button(frame12)
        self.runServerBtn.configure(text='启动服务器', width=8)
        self.runServerBtn.pack(expand="true", fill="x", side="left")
        self.stopServerBtn = ttk.Button(frame12)
        self.stopServerBtn.configure(text='停止服务器', width=8)
        self.stopServerBtn.pack(expand="true", fill="x", side="left")
        self.restartChBtn = ttk.Button(frame12)
        self.restartChBtn.configure(text='重启频道', width=8)
        self.restartChBtn.pack(expand="true", fill="x", side="left")
        self.uploadPVFBtn = ttk.Button(frame12)
        self.uploadPVFBtn.configure(text='上传PVF', width=8)
        self.uploadPVFBtn.pack(expand="true", fill="x", side="left")
        frame12.pack(expand="true", fill="both", side="top")
        frame10.pack(fill="x", side="top")
        self.SSHDIYFrame = ttk.Labelframe(labelframe2)
        self.SSHDIYFrame.configure(height=200, text='自定义指令', width=200)
        frame20 = ttk.Frame(self.SSHDIYFrame)
        frame20.configure(height=200, width=200)
        self.cmdE1 = ttk.Combobox(frame20)
        self.cmdE1.grid(column=0, row=0)
        self.cmdE2 = ttk.Combobox(frame20)
        self.cmdE2.grid(column=0, row=1)
        self.cmdE3 = ttk.Combobox(frame20)
        self.cmdE3.grid(column=0, row=2)
        self.cmdE4 = ttk.Combobox(frame20)
        self.cmdE4.grid(column=0, row=3)
        self.runBtn1 = ttk.Button(frame20)
        self.runBtn1.configure(text='执行')
        self.runBtn1.grid(column=1, row=0)
        self.runBtn2 = ttk.Button(frame20)
        self.runBtn2.configure(text='执行')
        self.runBtn2.grid(column=1, row=1)
        self.runBtn3 = ttk.Button(frame20)
        self.runBtn3.configure(text='执行')
        self.runBtn3.grid(column=1, row=2)
        self.runBtn4 = ttk.Button(frame20)
        self.runBtn4.configure(text='执行')
        self.runBtn4.grid(column=1, row=3)
        frame20.pack(side="left")
        frame21 = ttk.Frame(self.SSHDIYFrame)
        frame21.configure(height=200, width=200)
        self.shellLogE = tk.Text(frame21)
        self.shellLogE.configure(height=5, width=50)
        self.shellLogE.pack(expand="true", fill="both", side="top")
        frame21.pack(expand="true", fill="both", side="top")
        self.SSHDIYFrame.pack(expand="true", fill="both", side="top")
        labelframe2.pack(expand="true", fill="both", side="left")
        frame3.pack(fill="x", side="top")
        self.imageFrame = ttk.Frame(self.characMainFrame)
        self.imageFrame.configure(height=200, width=200)
        self.imageFrame.pack(expand="true", fill="both", side="top")
        self.characMainFrame.pack(side="top")
        self.tabView.add(self.characMainFrame, text=' 其它 ')
        self.gmToolFrame = ttk.Frame(self.tabView)
        self.gmToolFrame.configure(height=200, width=200)
        frame26 = ttk.Frame(self.gmToolFrame)
        frame26.configure(height=200, width=200)
        self.chargeFrame = ttk.Labelframe(frame26)
        self.chargeFrame.configure(height=200, text='充值', width=200)
        label26 = ttk.Label(self.chargeFrame)
        label26.configure(text='点券')
        label26.grid(column=0, row=0)
        label27 = ttk.Label(self.chargeFrame)
        label27.configure(text='代币')
        label27.grid(column=0, row=1)
        label28 = ttk.Label(self.chargeFrame)
        label28.configure(text='SP')
        label28.grid(column=0, row=2)
        label29 = ttk.Label(self.chargeFrame)
        label29.configure(text=' QP/TP ')
        label29.grid(column=0, row=3)
        entry1 = ttk.Entry(self.chargeFrame)
        self.ceraSVar = tk.StringVar()
        entry1.configure(state="readonly", textvariable=self.ceraSVar, width=8)
        entry1.grid(column=1, row=0, sticky="ew")
        entry2 = ttk.Entry(self.chargeFrame)
        self.ceraPointSVar = tk.StringVar()
        entry2.configure(
            state="readonly",
            textvariable=self.ceraPointSVar,
            width=8)
        entry2.grid(column=1, row=1, sticky="ew")
        entry3 = ttk.Entry(self.chargeFrame)
        self.spVar = tk.StringVar()
        entry3.configure(state="readonly", textvariable=self.spVar, width=8)
        entry3.grid(column=1, row=2, sticky="ew")
        entry4 = ttk.Entry(self.chargeFrame)
        self.qpTpVar = tk.StringVar()
        entry4.configure(state="readonly", textvariable=self.qpTpVar, width=8)
        entry4.grid(column=1, row=3, sticky="ew")
        self.ceraValueE = ttk.Spinbox(self.chargeFrame)
        self.ceraValueE.configure(from_=0, to=9999999999, width=8)
        self.ceraValueE.grid(column=2, row=0, sticky="ew")
        self.ceraTypeE = ttk.Combobox(self.chargeFrame)
        self.ceraTypeE.configure(
            state="readonly",
            values='点券 代币 SP TP QP',
            width=8)
        self.ceraTypeE.grid(column=2, row=1, sticky="ew")
        self.ceraChargeBtn = ttk.Button(self.chargeFrame)
        self.ceraChargeBtn.configure(text='充值')
        self.ceraChargeBtn.grid(column=2, row=2, sticky="ew")
        self.ceraClearBtn = ttk.Button(self.chargeFrame)
        self.ceraClearBtn.configure(text='清零')
        self.ceraClearBtn.grid(column=2, row=3, sticky="ew")
        self.chargeFrame.pack(expand="true", fill="both", side="left")
        self.chargeFrame.rowconfigure("all", weight=1)
        self.chargeFrame.columnconfigure("all", weight=1)
        self.PVPFrame = ttk.Labelframe(frame26)
        self.PVPFrame.configure(height=200, text='PVP', width=200)
        label5 = ttk.Label(self.PVPFrame)
        label5.configure(text='  段位  ')
        label5.grid(column=0, row=0)
        label30 = ttk.Label(self.PVPFrame)
        label30.configure(text='胜场')
        label30.grid(column=0, row=1)
        label7 = ttk.Label(self.PVPFrame)
        label7.configure(text='胜点')
        label7.grid(column=0, row=2)
        self.PVPwinNumE = ttk.Spinbox(self.PVPFrame)
        self.PVPwinNumE.configure(from_=0, to=9999999, width=8)
        self.PVPwinNumE.grid(column=1, row=1, sticky="ew")
        self.PVPgradeE = ttk.Combobox(self.PVPFrame)
        self.PVPgradeE.configure(
            state="readonly",
            values='点券 代币 SP TP QP',
            width=8)
        self.PVPgradeE.grid(column=1, row=0, sticky="ew")
        self.PVPCommitBtn = ttk.Button(self.PVPFrame)
        self.PVPCommitBtn.configure(text='提交')
        self.PVPCommitBtn.grid(column=0, columnspan=2, row=10, sticky="ew")
        self.PVPwinPointE = ttk.Spinbox(self.PVPFrame)
        self.PVPwinPointE.configure(from_=0, to=99999999, width=8)
        self.PVPwinPointE.grid(column=1, row=2, sticky="ew")
        self.PVPFrame.pack(expand="true", fill="both", side="left")
        self.PVPFrame.rowconfigure("all", weight=1)
        self.PVPFrame.columnconfigure("all", weight=1)
        self.labelframe3 = ttk.Labelframe(frame26)
        self.labelframe3.configure(height=200, text='其他功能', width=200)
        self.liftLimitBtn = ttk.Button(self.labelframe3)
        self.liftLimitBtn.configure(text='解除建号限制')
        self.liftLimitBtn.grid(column=0, row=0, sticky="ew")
        self.liftEquLevLimitBtn = ttk.Button(self.labelframe3)
        self.liftEquLevLimitBtn.configure(text='取消装备等级限制', width=12)
        self.liftEquLevLimitBtn.grid(column=0, row=1, sticky="ew")
        self.enableLRSlotBtn = ttk.Button(self.labelframe3)
        self.enableLRSlotBtn.configure(text='开启左右槽')
        self.enableLRSlotBtn.grid(column=0, row=2, sticky="ew")
        self.resetBloodDungeonBtn = ttk.Button(self.labelframe3)
        self.resetBloodDungeonBtn.configure(text='重置祭坛次数')
        self.resetBloodDungeonBtn.grid(column=1, row=0, sticky="ew")
        self.enableAllLevDungeonBtn = ttk.Button(self.labelframe3)
        self.enableAllLevDungeonBtn.configure(text='开启全图全难度', width=12)
        self.enableAllLevDungeonBtn.grid(column=1, row=1, sticky="ew")
        self.maxLevExpertBtn = ttk.Button(self.labelframe3)
        self.maxLevExpertBtn.configure(text='设置副职业满级')
        self.maxLevExpertBtn.grid(column=1, row=2, sticky="ew")
        self.labelframe3.pack(expand="true", fill="both", side="left")
        self.labelframe3.rowconfigure("all", weight=1)
        self.labelframe3.columnconfigure("all", weight=1)
        frame26.pack(fill="x", side="top")
        self.characInfoFrame = ttk.Frame(self.gmToolFrame)
        self.characInfoFrame.configure(height=200, width=200)
        self.characAndMoneyF = ttk.Frame(self.characInfoFrame)
        self.characAndMoneyF.configure(height=200, width=200)
        self.characInfoF = ttk.Labelframe(self.characAndMoneyF)
        self.characInfoF.configure(height=200, text='角色信息', width=200)
        self.characEntriesFrame = ttk.Frame(self.characInfoF)
        self.characEntriesFrame.configure(height=200, width=200)
        label12 = ttk.Label(self.characEntriesFrame)
        label12.configure(text='角色名：')
        label12.grid(column=0, row=0)
        self.nameE = ttk.Entry(self.characEntriesFrame)
        self.nameE.configure(width=30)
        self.nameE.grid(
            column=1,
            columnspan=2,
            padx=1,
            pady=1,
            row=0,
            sticky="ew")
        label13 = ttk.Label(self.characEntriesFrame)
        label13.configure(text='角色等级：')
        label13.grid(column=0, row=1)
        self.levE = ttk.Spinbox(self.characEntriesFrame)
        self.levE.configure(from_=1, to=999, width=8)
        self.levE.grid(column=1, padx=1, pady=1, row=1, sticky="ew")
        checkbutton2 = ttk.Checkbutton(self.characEntriesFrame)
        self.isVIP = tk.IntVar()
        checkbutton2.configure(text='VIP账户', variable=self.isVIP)
        checkbutton2.grid(column=2, row=1)
        label14 = ttk.Label(self.characEntriesFrame)
        label14.configure(text='职业：')
        label14.grid(column=0, row=2)
        self.jobE = ttk.Combobox(self.characEntriesFrame)
        self.jobE.configure(width=8)
        self.jobE.grid(column=1, padx=1, pady=1, row=2, sticky="ew")
        self.jobE.bind("<<ComboboxSelected>>", self.set_grow_type, add="")
        self.jobE2 = ttk.Combobox(self.characEntriesFrame)
        self.jobE2.configure(width=8)
        self.jobE2.grid(column=2, padx=1, row=2, sticky="ew")
        label15 = ttk.Label(self.characEntriesFrame)
        label15.configure(text='成长类型：')
        label15.grid(column=0, row=3)
        self.growTypeE = ttk.Combobox(self.characEntriesFrame)
        self.growTypeE.configure(width=8)
        self.growTypeE.grid(
            column=1,
            columnspan=1,
            padx=1,
            pady=1,
            row=3,
            sticky="ew")
        label16 = ttk.Label(self.characEntriesFrame)
        label16.configure(text='觉醒标识：')
        label16.grid(column=0, row=4)
        self.wakeFlgE = ttk.Combobox(self.characEntriesFrame)
        self.wakeFlgE.configure(width=8)
        self.wakeFlgE.grid(column=1, padx=1, pady=1, row=4, sticky="ew")
        checkbutton3 = ttk.Checkbutton(self.characEntriesFrame)
        self.isReturnUser = tk.IntVar()
        checkbutton3.configure(text='回归玩家', variable=self.isReturnUser)
        checkbutton3.grid(column=2, row=3)
        self.commitBtn = ttk.Button(self.characEntriesFrame)
        self.commitBtn.configure(text='提交修改')
        self.commitBtn.grid(column=0, columnspan=3, padx=1, row=5, sticky="ew")
        self.commitBtn.configure(command=self.commit)
        self.cInfoSetBanedBtn = ttk.Checkbutton(self.characEntriesFrame)
        self.isBanedUser = tk.IntVar()
        self.cInfoSetBanedBtn.configure(text='封停账号', variable=self.isBanedUser)
        self.cInfoSetBanedBtn.grid(column=2, row=4)
        self.characEntriesFrame.pack(
            anchor="center",
            expand="false",
            fill="x",
            padx=5,
            pady=5,
            side="top")
        self.characEntriesFrame.rowconfigure("all", weight=1)
        self.characEntriesFrame.columnconfigure(1, weight=1)
        self.characInfoF.pack(expand="true", fill="both", side="top")
        self.moneyF = ttk.Labelframe(self.characAndMoneyF)
        self.moneyF.configure(height=200, text='金币复活币', width=200)
        self.pkgMoneyE = ttk.Spinbox(self.moneyF)
        self.pkgMoneyE.configure(from_=0, to=999999999999, width=15)
        self.pkgMoneyE.grid(column=1, row=0, sticky="ew")
        self.pkgMoneyBtn = ttk.Button(self.moneyF)
        self.pkgMoneyBtn.configure(text='提交修改')
        self.pkgMoneyBtn.grid(column=2, row=0, sticky="ew")
        self.accountMoneyE = ttk.Spinbox(self.moneyF)
        self.accountMoneyE.configure(from_=0, to=999999999999, width=15)
        self.accountMoneyE.grid(column=1, row=1, sticky="ew")
        self.accountMoneyBtn = ttk.Button(self.moneyF)
        self.accountMoneyBtn.configure(text='提交修改')
        self.accountMoneyBtn.grid(column=2, row=1, sticky="ew")
        label8 = ttk.Label(self.moneyF)
        label8.configure(text=' 背包 ')
        label8.grid(column=0, row=0)
        label9 = ttk.Label(self.moneyF)
        label9.configure(text=' 金库 ')
        label9.grid(column=0, row=1)
        self.payCoinE = ttk.Spinbox(self.moneyF)
        self.payCoinE.configure(from_=0, to=999999999999)
        self.payCoinE.grid(column=1, row=2, sticky="ew")
        self.payCoinBtn = ttk.Button(self.moneyF)
        self.payCoinBtn.configure(text='提交修改')
        self.payCoinBtn.grid(column=2, row=2, sticky="ew")
        label10 = ttk.Label(self.moneyF)
        label10.configure(text='复活币')
        label10.grid(column=0, row=2)
        self.moneyF.pack(expand="true", fill="both", side="top")
        self.moneyF.columnconfigure("all", weight=1)
        self.characAndMoneyF.pack(expand="false", fill="both", side="left")
        labelframe6 = ttk.Labelframe(self.characInfoFrame)
        labelframe6.configure(height=200, text='活动管理', width=200)
        self.eventTreeNow = ttk.Treeview(labelframe6)
        self.eventTreeNow.configure(
            height=6, selectmode="extended", show="headings")
        self.eventTreeNow_cols = [
            'column25', 'column29', 'column38', 'column39']
        self.eventTreeNow_dcols = ['column25', 'column29', 'column38']
        self.eventTreeNow.configure(
            columns=self.eventTreeNow_cols,
            displaycolumns=self.eventTreeNow_dcols)
        self.eventTreeNow.column(
            "column25",
            anchor="center",
            stretch="true",
            width=50,
            minwidth=20)
        self.eventTreeNow.column(
            "column29",
            anchor="center",
            stretch="true",
            width=100,
            minwidth=20)
        self.eventTreeNow.column(
            "column38",
            anchor="center",
            stretch="true",
            width=50,
            minwidth=20)
        self.eventTreeNow.column(
            "column39",
            anchor="center",
            stretch="true",
            width=50,
            minwidth=20)
        self.eventTreeNow.heading("column25", anchor="center", text='活动ID')
        self.eventTreeNow.heading("column29", anchor="center", text='活动描述')
        self.eventTreeNow.heading("column38", anchor="center", text='参数')
        self.eventTreeNow.heading("column39", anchor="center", text='参数2')
        self.eventTreeNow.pack(expand="true", fill="both", side="top")
        frame18 = ttk.Frame(labelframe6)
        frame18.configure(height=200, width=200)
        self.refreshEventBtn = ttk.Button(frame18)
        self.refreshEventBtn.configure(text='刷新活动')
        self.refreshEventBtn.pack(expand="true", fill="x", side="left")
        self.delEventBtn = ttk.Button(frame18)
        self.delEventBtn.configure(text='删除活动')
        self.delEventBtn.pack(expand="true", fill="x", side="right")
        frame18.pack(fill="x", side="top")
        frame15 = ttk.Frame(labelframe6)
        frame15.configure(height=200, width=200)
        label36 = ttk.Label(frame15)
        label36.configure(foreground="#0080ff", text='活动名称')
        label36.grid(column=0, row=0)
        self.eventNameE = ttk.Combobox(frame15)
        self.eventNameE.configure(width=12)
        self.eventNameE.grid(column=0, row=1, sticky="ew")
        label37 = ttk.Label(frame15)
        label37.configure(foreground="#0080ff", text='参数')
        label37.grid(column=1, row=0)
        self.eventArg1E = ttk.Entry(frame15)
        self.eventArg1E.configure(width=8)
        self.eventArg1E.grid(column=1, row=1, sticky="ew")
        self.addEventBtn = ttk.Button(frame15)
        self.addEventBtn.configure(text='添加活动')
        self.addEventBtn.grid(column=2, row=1, rowspan=1, sticky="ew")
        frame15.pack(fill="x", side="top")
        frame15.columnconfigure("all", weight=1)
        labelframe6.pack(expand="true", fill="both", side="top")
        self.characInfoFrame.pack(expand="true", fill="both", side="top")
        self.gmToolFrame.pack(expand="true", fill="both", side="top")
        self.tabView.add(self.gmToolFrame, text=' GM ')
        self.msgFrame = ttk.Frame(self.tabView)
        self.msgFrame.configure(height=200, width=200)
        self.msgFrame.pack(side="top")
        self.tabView.add(self.msgFrame, text=' 留言 ')
        frame5 = ttk.Frame(self.tabView)
        frame5.configure(height=200, width=200)
        frame17 = ttk.Frame(frame5)
        frame17.configure(height=200, width=200)
        self.banedTreeV = ttk.Treeview(frame17)
        self.banedTreeV.configure(
            height=10,
            selectmode="extended",
            show="headings")
        self.banedTreeV_cols = [
            'column23',
            'column14',
            'column15',
            'column16',
            'column17',
            'column18',
            'column24']
        self.banedTreeV_dcols = [
            'column23',
            'column14',
            'column15',
            'column16',
            'column17',
            'column18',
            'column24']
        self.banedTreeV.configure(
            columns=self.banedTreeV_cols,
            displaycolumns=self.banedTreeV_dcols)
        self.banedTreeV.column(
            "column23",
            anchor="center",
            stretch="true",
            width=40,
            minwidth=20)
        self.banedTreeV.column(
            "column14",
            anchor="center",
            stretch="true",
            width=40,
            minwidth=20)
        self.banedTreeV.column(
            "column15",
            anchor="center",
            stretch="true",
            width=40,
            minwidth=20)
        self.banedTreeV.column(
            "column16",
            anchor="center",
            stretch="true",
            width=20,
            minwidth=20)
        self.banedTreeV.column(
            "column17",
            anchor="center",
            stretch="true",
            width=60,
            minwidth=20)
        self.banedTreeV.column(
            "column18",
            anchor="center",
            stretch="true",
            width=30,
            minwidth=20)
        self.banedTreeV.column(
            "column24",
            anchor="center",
            stretch="true",
            width=50,
            minwidth=20)
        self.banedTreeV.heading("column23", anchor="center", text='账号')
        self.banedTreeV.heading("column14", anchor="center", text='UID')
        self.banedTreeV.heading("column15", anchor="center", text='角色ID')
        self.banedTreeV.heading("column16", anchor="center", text='等级')
        self.banedTreeV.heading("column17", anchor="center", text='角色名')
        self.banedTreeV.heading("column18", anchor="center", text='职业')
        self.banedTreeV.heading("column24", anchor="center", text='IP')
        self.banedTreeV.pack(expand="true", fill="both", side="left")
        self.banedBar = ttk.Scrollbar(frame17)
        self.banedBar.configure(orient="vertical")
        self.banedBar.pack(fill="y", side="right")
        frame17.pack(expand="true", fill="both", side="top")
        frame16 = ttk.Frame(frame5)
        frame16.configure(height=200, width=200)
        self.resumeBanedBtn = ttk.Button(frame16)
        self.resumeBanedBtn.configure(text='解除选中封停')
        self.resumeBanedBtn.pack(expand="true", fill="x", side="left")
        label11 = ttk.Label(frame16)
        label11.configure(text='  账号ID：')
        label11.pack(side="left")
        self.banAnameE = ttk.Entry(frame16)
        self.banAnameE.pack(side="left")
        self.setBanedABtn = ttk.Button(frame16)
        self.setBanedABtn.configure(text='设置封停')
        self.setBanedABtn.pack(expand="true", fill="x", side="left")
        label21 = ttk.Label(frame16)
        label21.configure(text='  角色名：')
        label21.pack(side="left")
        self.banCnameE = ttk.Entry(frame16)
        self.banCnameE.pack(side="left")
        self.setBanedCBtn = ttk.Button(frame16)
        self.setBanedCBtn.configure(text='设置封停')
        self.setBanedCBtn.pack(expand="true", fill="x", side="left")
        frame16.pack(fill="x", side="top")
        frame5.pack(side="top")
        self.tabView.add(frame5, text='封停')
        self.tabView.pack(expand="true", fill="both", side="top")
        self.tabView.bind(
            "<<NotebookTabChanged>>",
            self.change_TabView,
            add="")
        frame1 = ttk.Frame(self.tabFrame)
        frame1.configure(height=20, width=220)
        self.refreshPKGBtn = tk.Button(frame1)
        self.refreshPKGBtn.configure(
            borderwidth=0,
            overrelief="flat",
            relief="flat",
            text='刷新背包')
        self.refreshPKGBtn.pack(padx=3, side="left")
        self.stkSearchBtn = tk.Button(frame1)
        self.stkSearchBtn.configure(
            borderwidth=0,
            overrelief="flat",
            relief="flat",
            text='道具搜索')
        self.stkSearchBtn.pack(padx=3, side="left")
        self.stkSearchBtn.configure(command=self.open_advance_search_stackable)
        self.equSearchBtn = tk.Button(frame1)
        self.equSearchBtn.configure(
            borderwidth=0,
            overrelief="flat",
            relief="flat",
            text='装备搜索')
        self.equSearchBtn.pack(padx=3, side="left")
        self.equSearchBtn.configure(command=self.open_advance_search_equipment)
        frame1.place(anchor="ne", height=23, relx=1.0, y=0)
        self.tabFrame.pack(expand="true", fill="both", side="top")
        separator2 = ttk.Separator(self.mainFrame)
        separator2.configure(orient="horizontal")
        separator2.pack(fill="x", side="top")
        frame4 = tk.Frame(self.mainFrame)
        frame4.configure(height=200, width=200)
        self.infoLabel = ttk.Label(frame4)
        self.infoSvar = tk.StringVar(value=' 欢迎使用背包编辑工具！')
        self.infoLabel.configure(
            borderwidth=1,
            text=' 欢迎使用背包编辑工具！',
            textvariable=self.infoSvar)
        self.infoLabel.pack(anchor="w", expand="true", fill="x", side="left")
        self.label6 = ttk.Label(frame4)
        self.versionSvar = tk.StringVar(value='当前软件版本：230607')
        self.label6.configure(
            anchor="e",
            borderwidth=1,
            text='当前软件版本：230607',
            textvariable=self.versionSvar)
        self.label6.pack(anchor="e", expand="false", fill="x", side="right")
        frame4.pack(fill="x", side="top")
        self.mainFrame.pack(expand="true", fill="both", side="top")

        # Main widget
        self.mainwindow = self.mainFrame


        # Main widget
        self.mainwindow = self.mainFrame
        self.w = master

        self.check_update_flg = check_update
        self.title = self.w.title
        self._build()
    
    def _build(self):
        def treeview_sortColumn(col,tree):
            nonlocal reverseFlag,sortQueue                         # 定义排序标识全局变量
            sortID = len(sortQueue)
            sortQueue.append(sortID)
            lst = [(tree.set(itemStr,col),itemStr)
                    for itemStr in tree.get_children("")]
            lst_int = []
            useInt = True
            for itemStr in tree.get_children(""):
                value = tree.set(itemStr,col).replace(',','')
                try:
                    if value in ['paycoin', 'money','cera','cera_point']:
                        #print(value)
                        value = 0
                    value = int(value)
                    lst_int.append([value,itemStr])
                except:
                    useInt = False
                    break
            if useInt:
                lst = lst_int
            #print(lst)                                 # 打印列表
            lst.sort(key=lambda x:x[0] if isinstance(x[0],int) else x[0].encode('gbk',errors='replace'),reverse=reverseFlag)              # 排序列表
            #print(lst)                                 # 打印列表
            reverseFlag = not reverseFlag              # 更改排序标识
            for index, item in enumerate(lst):         # 重新移动项目内容
                if len(sortQueue)>sortID+1:
                    break
                tree.move(item[1],"",index)
                if index%300==0:
                    self.mainwindow.update()
        
        self.password = ''
        self.CONNECTING_FLG = False #判断正在连接
        self.PVF_LOADING_FLG = False #判断正在加载pvf
        self.Advance_Search_State_FLG = False #判断高级搜索是否打开
        self.Advance_Search_State_FLG_Stackable = False
        self.GM_Tool_Flg = False    #判断GM工具是否打开
        self.sponsorFrame = True
        self.PVF_EDIT_OPEN_FLG = False
        self.fillingFlg = False #填充treeview
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
        self.itemsTreevs_now = {}

        self.loadPkgTaskList = []
        self.currentTreeViews = {}
        self.editFrameShowFuncs = {}
        self.blobCommitExFunc = lambda cNo=0:...
        self.openGMExFunc = lambda GMtool=None:...
        self.quit_GM_Ex_func = lambda:...
        self.tabIDDict = tabIDDict

        self.tabViewChangeFuncs = []    #切换tab时执行的function列表
        self.tabNames = []
        self.cNo = 0
        self.uid = 0
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
        self.w.call('wm', 'iconphoto', self.w._w, tk.PhotoImage(file=IconPath))
        self._buildSqlConn()
        self._buildtab_main()
        self.blobTabNameList = list(globalBlobs_map.keys())
        self.blobFrameList = [self.invFrame,self.equFrame,self.creatureFrame,self.cargoFrame,self.accountCargoFrame]
        
        
        self.nonBlobFrameList = [self.creatureItemFrame,self.avatarFrame,self.mailFrame]
        self.blobFrameWids = []
        for i,frame in enumerate(self.blobFrameList):
            tabName = self.blobTabNameList[i]
            itemEditFrame = itemSlotFrame.ItemslotframeWidget(frame)
            self.blobFrameWids.append(itemEditFrame)
            #self.itemsTreevs_now[self.blobTabNameList[i]] = itemEditFrame.itemsTreev_now
            self._buildtab_itemTab(itemEditFrame,tabName)

        self.mailFrame = mailFrame.MailframeWidget(self.mailFrame)
        self.avatarFrame = avatarFrame.AvatarframeWidget(self.avatarFrame)
        self.creatureItemFrame = creatureFeame.CreatureframeWidget(self.creatureItemFrame)
        #self.characFrame = characFrame.CharacframeWidget(self.characMainFrame)
        self.messageFrame = msgFrame.MessageframeWidget(self.msgFrame)
        
        for tab in self.tabView.tabs():
            tabName = self.tabView.tab(tab,'text')
            tabIDDict[tabName] = tab

        self._buildtab_itemTab_creature(self.creatureItemFrame)
        self._buildtab_itemTab_avatar(self.avatarFrame)
        self._buildtab_itemTab_mail(self.mailFrame)
        self._buildtab_GM()
        self._buildFrame_SSH()
        self._buildTab_Baned()

        
        self._buildtab_charac(self,' 其它 ')

        sortQueue = []
        reverseFlag = True

        for tree in list(self.itemsTreevs_now.values()) + [self.characTreeV,self.messageFrame.msgListTree,self.banedTreeV]:
            for colIndex in range(20):
                try:
                    col = tree.column(colIndex)['id']
                    tree.heading(f"#{colIndex+1}", command=lambda c=col,t=tree:treeview_sortColumn(c,t))
                    #print(colIndex,col)
                except:
                    break
        
        boxs = [self.characTreeV,self.creatureItemFrame.itemsTreev_now,self.avatarFrame.itemsTreev_now,self.mailFrame.itemsTreev_now,self.banedTreeV]
        bars = [self.characBar,self.creatureItemFrame.itemsTreev_bar,self.avatarFrame.itemsTreev_bar,self.mailFrame.itemsTreev_bar,self.banedBar]

        for i in range(len(boxs)):
            box:tk.Listbox = boxs[i]
            bar = bars[i]
            bar.config(command=box.yview)
            box.config(yscrollcommand=bar.set)
        
        self.db_ipE.config(values=list(cacheM.config.get('DB_CONFIGS').keys()))
        self.db_pwdE.config(values=['123456','uu5!^%jg'])
        VERSION = updateM.versionDict.get('VERSION')
        self.versionSvar.set(f'当前软件版本：{VERSION}  ')

    def _buildSqlConn(self):
        #数据库连接
        db_ip = self.db_ipE
        db_ip.insert(0,cacheM.config['DB_IP'])
        db_port = self.db_portE
        db_port.insert(0,cacheM.config['DB_PORT'])
        db_user = self.db_userE
        db_user.insert(0,cacheM.config['DB_USER'])
        db_pwd = self.db_pwdE
        self.password = cacheM.config['DB_PWD']
        db_pwd.insert(0,'******')


    def _buildtab_main(self):
        def fill_charac_treeview(charac_list):
            self.characTreeV.delete(*self.characTreeV.get_children())
            for values in charac_list:
                uid,cNo,name,lev,job,growType,deleteFlag,expert_job = values
                jobDict = cacheM.jobDict.get(job)
                if isinstance(jobDict,dict):
                    jobNew = jobDict.get(growType % 16)
                else:
                    jobNew = growType % 16
                self.characTreeV.insert('',tk.END,values=[cNo,name,lev,jobNew,uid],tags='deleted' if deleteFlag==1 else '')
                self.characInfos[cNo] = {'uid':uid,'name':name,'lev':lev,'job':job,'growType':growType,'expert_job':expert_job} 
            self.SqlEncodeE.set(f'{sqlM.sqlEncodeUseIndex}-{sqlM.SQL_ENCODE_LIST[sqlM.sqlEncodeUseIndex]}')
            self.clear_charac_tab_func()
            self.currentItemDict = {}
            self.selectedCharacItemsDict = {}
            for tabName in self.itemInfoClrFuncs.keys():
                itemsTreev_now = self.itemsTreevs_now[tabName]
                itemsTreev_now.delete(*itemsTreev_now.get_children())
                try:
                    self.itemInfoClrFuncs[tabName]()    #清除物品信息显示
                    self.fillTreeFunctions[tabName]()   #填充treeview
                except:
                    pass
                try:
                    itemsTreev_del = self.itemsTreevs_del[tabName]
                    itemsTreev_del.delete(*itemsTreev_del.get_children())
                except:
                    continue
            self.globalCharacBlobs = {}

        def searchCharac(searchType='account'):   #或者cName
            if searchType=='account':
                characs = sqlM.getCharacterInfo(uid=sqlM.getUID(self.aNameE.get()))
                try:
                    uid = int(self.aNameE.get())
                    characs_uid = sqlM.getCharacterInfo(uid=uid)
                    characs += characs_uid
                except:
                    pass
                
            else:
                if self.cNameE.get()=='':
                    characs = sqlM.get_online_charac()
                else:
                    characs = sqlM.getCharacterInfo(cName=self.cNameE.get())
            print('加载角色列表',characs)
            fill_charac_treeview(charac_list=characs)

        @inThread
        def selectCharac(showTitle=False):
            
            if len(self.characTreeV.selection())==0:return
            taskID = len(self.loadPkgTaskList)
            self.loadPkgTaskList.append(taskID)
            self.fillingFlg = True
            sel = self.characTreeV.item(self.characTreeV.selection()[0])['values']
            try:
                cNo, cName, lev, job, uid = sel
            except:
                print('未选择角色')
                return False
            if self.PVF_LOADING_FLG:
                print('等待PVF加载中')
                return False
            if len(cacheM.ITEMS_dict.keys())<10:
                print(f'请选择物品列表来源')
                return False
            log(f'加载角色物品[{sel}]')
            inventory, equipslot, creature = sqlM.getInventoryAll(cNo=cNo)[0]
            cargo,jewel,expand_equipslot = sqlM.getCargoAll(cNo=cNo)[0]
            creature_items = sqlM.getCreatureItem(cNo=cNo)
            user_items = sqlM.getAvatar(cNo=cNo,ability_=True)
            account_cargo = sqlM.get_Account_Cargo(cNo=cNo)
            user_postals = sqlM.get_postal_new(cNo=cNo)
            #print(user_postals)
            if showTitle:
                print(f'角色[{cName}]物品已加载')
            else:
                log(f'角色[{cName}]物品已加载')
            #self.enable_Tabs()
            blobsItemsDict = {}
            for key,name in globalBlobs_map.items():
                blobsItemsDict[key] = locals()[name]
            self.globalCharacBlobs = blobsItemsDict

            nonBlobItemsDict = {}
            for key,name in globalNonBlobs_map.items():
                nonBlobItemsDict[key] = locals().get(name)
            self.cNo = cNo
            self.cName = cName
            #self.job = job
            self.uid = uid
            self.lev = lev
            self.globalCharacNonBlobs = nonBlobItemsDict
            self.importFlgDict = {}
            #print('填充treev')
            self.w.after(1,lambda:self.fill_tab_treeviews(taskID))
            self.fill_charac_tab_fun()
            while self.fillingFlg and len(self.loadPkgTaskList)==taskID+1:
                time.sleep(0.01)
                #print(self.fillingFlg)
            self.update_GM()
            if self.GM_Tool_Flg:    #同步修改角色
                self.GMTool.cNo = cNo
                self.GMTool.update_Info()
                self.GMTool.title(self.cName)

        def loadPVF(pvfPath:str=''):
            '''设置物品来源，读取pvf或者csv'''
            def inner():
                nonlocal pvfPath
                print('数据源加载中...PVF：',pvfPath)
                if cacheM.config.get('PVF_PATH')== '':
                    messagebox.askokcancel('这是一个初次运行的广告','全服背包管理工具赞助即可获得！详情请点击其它->Github图标。')
                if self.PVF_LOADING_FLG:
                    print('等待PVF加载')
                    return False
                if pvfPath=='':
                    pvfPath = askopenfilename(filetypes=[('DNF Script.pvf file','*.pvf')])
                if pvfPath!='':
                    cacheM.pvfReader.LOAD_FUNC = cacheM.pvfReader.get_Item_Dict
                    t1 = time.time()
                    print('加载PVF中...')
                    self.PVF_LOADING_FLG = True
                    info = cacheM.loadItems2(True,pvfPath,encode=self.PVFEncodeE.get())
                    self.PVF_LOADING_FLG = False
                    t = time.time() - t1 
                    MD5 = cacheM.PVFcacheDict.get("MD5")
                    if MD5 is None:
                        return False
                    info += '  花费时间%.2fs' % t
                    self.PVFCacheE.set(f'{cacheM.tinyCache[MD5].get("nickName")}-{MD5}')
                    self.PVFEncodeE.set(cacheM.tinyCache[MD5].get("encode"))

                    # 更新魔法封印框、时装潜能框和职业框
                    if cacheM.magicSealDict.get(0) is None:
                        cacheM.magicSealDict[0] = ''
                    [func() for func in self.updateMagicSealFuncs.values()]
                    self.hiddenCom.config(values=['0-None']+[f'{i+1}-{value}' for i,value in enumerate(cacheM.avatarHiddenList[0])])
                    self.jobE.config(values=[f'{item[0]}-{item[1][0]}'  for item in cacheM.jobDict.items()])
                    self.jobE.set('')

                    PVFres = []
                    for MD5,infoDict in list(cacheM.cacheManager.tinyCache.items()):
                        if not isinstance(infoDict,dict):continue
                        PVFres.append(f'{cacheM.cacheManager.tinyCache[MD5]["nickName"]}-{MD5}')
                    self.PVFCacheE.config(values=PVFres)
                    enhanceTypes = list(cacheM.enhanceDict_zh.keys())
                    for orbTypeE in self.orbTypeEList:
                        orbTypeE.config(values=enhanceTypes)

                    if self.PVF_CACHE_EDIT_OPEN_FLG:
                        self.PVFEditWinFrame.fillTree()
                    print(info)
                else:
                    print('PVF路径为空，加载CSV')
                    cacheM.loadItems2(False)
                    self.PVFCacheE.set('使用CSV')
                selectCharac()
            t = threading.Thread(target=inner)
            t.setDaemon(True)
            t.start()
            
        self.load_PVF = loadPVF

        #账号查询功能
        self.search_Account_ = lambda e=None:searchCharac('account')
        self.search_Charac_ = lambda e=None:searchCharac('cName')
        self.selectCharac_ = selectCharac
        self.fillCharac = fill_charac_treeview
        self.refreshPKGBtn.config(command=self.selectCharac_)
        searchFrame = self.searchFrame
        

        self.connectorE.set('----')
        self.SqlEncodeE.config(values=[f'{i}-{encode}' for i,encode in enumerate(sqlM.SQL_ENCODE_LIST)],state='readonly')
        self.SqlEncodeE.set('----')
        def setEncodeing(e=None):
            encodeIndex = int(self.SqlEncodeE.get().split('-')[0])
            sqlM.sqlEncodeUseIndex = encodeIndex
            sqlM.ENCODE_AUTO = False  #关闭自动编码切换
        self.sel_Sql_Encode_ = setEncodeing


        res = []
        for MD5,infoDict in list(cacheM.cacheManager.tinyCache.items()):
            if not isinstance(infoDict,dict):continue
            res.append(f'{cacheM.cacheManager.tinyCache[MD5]["nickName"]}-{MD5}')
        self.PVFCacheE.config(values=res,state='readonly')

        self.PVFCacheE.set('PVF缓存')
        self.PVFEncodeE.config(values=['big5','gbk','utf-8'],state='readonly')
        self.PVFEncodeE.set('big5')

        CreateToolTip(self.PVFEncodeE,'PVF编码，加载乱码请尝试修改后重新加载')

        characTreev = self.characTreeV
        characTreev.tag_configure('deleted', background='gray')

        self.autoGMVar.set(cacheM.config.get('GMTOOL_STARTUP'))
        if cacheM.config.get('GMTOOL_STARTUP'):
            self.w.after(10,self._open_GM)

        gifCanvas = None
        def loadPics():
            nonlocal gifCanvas
            
            size = self.imageFrame1.winfo_width(),self.imageFrame1.winfo_height()
            if size[0] < 10:
                return self.w.after(100,loadPics)
            size = size[0]+50,size[1]+50
            gifCanvas = ImageLabel(self.imageFrame1,borderwidth=0)
            gifCanvas.pack(expand=True,fill='both')
            gifCanvas.loadDir(gifPath_1,size,root=self.w)
            self.mainFrame.update()
        self.w.after(100,loadPics)
        
        def changeGif(e):
            if str(searchFrame)==self.tabView.select() and gifCanvas is not None:
                gifCanvas.randomShow()
        self.tabViewChangeFuncs.append(changeGif)

    def _buildtab_itemTab(self,itemEditFrame:itemSlotFrame.ItemslotframeWidget,tabName):
        def ask_commit():
            if showSelectedItemInfo()!=True or self.cNo==0:
                return False
            if not messagebox.askokcancel('修改确认',f'确定修改{tabName}所选物品？\n请确认账号不在线或正在使用其他角色\n{self.editedItemsDict[tabName]}'):
                return False
            cNo = self.cNo
            key = globalBlobs_map[tabName]
            originblob = self.globalCharacBlobs[tabName]
            #print(originblob,self.editedItemsDict[tabName],cNo,key)
            sqlM.commit_change_blob(originblob,self.editedItemsDict[tabName],cNo,key)
            print(f'修改列表{tabName}-{self.editedItemsDict[tabName]}')
            self.blobCommitExFunc(self.cNo)
            print(f'====修改成功==== {tabName} 角色ID：{self.cNo}')
            return self.selectCharac()
            
        def save_blob(fileType='blob',additionalTag=tabName):
            filePath = asksaveasfilename(title=f'保存文件(.{fileType})',filetypes=[('二进制文件',f'*.{fileType}')],initialfile=f'{self.cName}_lv.{self.lev}_{additionalTag}.{fileType}')
            if filePath=='':
                return False
            if filePath[-1-len(fileType):]!= f'.{fileType}':
                filePath += f'.{fileType}'
            filePath = filePath[:-1-len(fileType)]  +filePath[-1-len(fileType):]#+ f'-{additionalTag}'
            with open(filePath,'wb') as f:
                f.write(self.globalCharacBlobs[tabName])
            print(f'文件已保存{filePath}')

        def load_blob(fileType='blob'):
            #print('load')
            filePath = askopenfilename(filetypes=[(f'DNF {tabName} file',f'*.{fileType}')])
            if filePath=='':
                return False
            p = Path(filePath)
            if p.exists():
                with open(p,'rb') as f:
                    blob = f.read()
            self.globalCharacBlobs[tabName] = blob
            self.importFlgDict[tabName] = True

            #clear_item_Edit_Frame()
            #refill_Tree_View()
            taskID=len(self.loadPkgTaskList)
            self.loadPkgTaskList.append((taskID,tabName))
            self.fill_tab_treeviews(taskID=taskID)

        def changeItemSlotType(e=None):
            '''点击修改物品类别或点击新物品时，修改控件可编辑状态'''
            typeZh = typeEntry.get().split('-')[1]
            #print(typeZh)
            if typeZh in ['装备']:
                numGradeLabel.config(text='品级：')
                configFrame(equipmentExFrame,'normal')
                configFrame(itemEditFrame.itemBasicInfoFrame,'normal')
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
                configFrame(equipmentExFrame,'disabled')
                for widget in itemEditFrame.itemBasicInfoFrame.children:
                    try:
                        itemEditFrame.itemBasicInfoFrame.children[widget].config(state='disable')
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
        
        def clear_item_Edit_Frame(clearTitle=True):
            '''清空右侧编辑槽'''
            #if clearTitle:
            #    itemSlotEditFrame.config(text=f'物品信息编辑')
            itemEditFrame.currentEditLabelVar.set(f'(0)')
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

        def updateItemEditFrame(itemSlot:sqlM.DnfItemSlot):
            '''传入slot对象，更新右侧编辑槽，不触发保存'''
            configFrame(itemEditFrame.itemEditFrame,'normal')

            clear_item_Edit_Frame(False)


            itemSealVar.set(itemSlot.isSeal)
            itemIDEntry.insert(0,itemSlot.id)
            durabilityEntry.insert(0,itemSlot.durability)
            try:
                itemNameEntry.insert(0,str(cacheM.ITEMS_dict.get(itemSlot.id)))
            except:
                itemNameNew = ''
                for c in str(cacheM.ITEMS_dict.get(itemSlot.id)):
                    itemNameNew += c if ord(c) < 0xffff else ''
                    cacheM.ITEMS_dict[itemSlot.id] = itemNameNew
                itemNameEntry.insert(0,itemNameNew)

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
                    print(f'宝珠加载失败，{itemSlot.orb}')
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
                    if len(cacheM.PVFcacheDict.keys())!=0:
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
            #print(slotBytes)
            #print(self.selectedCharacItemsDict[tabName][index].oriBytes)
            if retType=='bool':
                if slotBytes!= self.selectedCharacItemsDict[tabName][index].oriBytes:
                    
                    if itemSlot.id!=0 and itemSlot.type==0:
                        messagebox.askokcancel('物品状态确认','当前物品种类为空！请清空格子或设置合适种类以继续保存。')
                        #enableTypeChangeVar.set(1)
                        typeEntry.config(state='readonly')
                        return 'TypeEmptyFalse'
                    if '时装' in cacheM.getStackableTypeMainIdAndZh(itemSlot.id):
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
                    index = int(itemEditFrame.currentEditLabelVar.get().split('(')[-1].replace(')',''))
                    print(index)
                except:
                    return False
            else:
                sels = itemsTreev_now.selection()
                if len(sels)==0:#未选中任何物品
                    return True
                values = itemsTreev_now.item(itemsTreev_now.selection()[0])['values']  #数据库index
                index = values[0]
                
                set_treeview_color()
            if save and self.editedItemsDict.get(tabName).get(index) is not None:
                itemSlot:sqlM.DnfItemSlot = self.editedItemsDict.get(tabName).get(index)
            else:
                itemSlot:sqlM.DnfItemSlot = self.selectedCharacItemsDict[tabName][index]
            updateItemEditFrame(itemSlot)
            log(f'{tabName}-{index}-{itemSlot}')
            self.w.title(itemSlot)
            self.currentItemDict[tabName] = [index,itemSlot,itemsTreev_now.focus()]
            #itemSlotEditFrame.config(text=f'物品信息编辑({index})')
            itemEditFrame.currentEditLabelVar.set(f'({index})')
            if len(cacheM.PVFcacheDict.keys())!=0 and self.errorInfoDict.get(tabName) is not None:
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
                itemNameEntry.config(values=[item[1]+' '+ str([item[0]]) for item in res])
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
                name,id_ = itemNameEntry.get().rsplit(' ',1)
                id_ = id_[1:-1]
                
            itemIDEntry.delete(0,tk.END)
            itemIDEntry.insert(0,id_)
            itemNameEntry.delete(0,tk.END)
            itemNameEntry.insert(0,name)
            itemNameEntry.config(values=[])
            #print(name,id_)

        def reset():
            showSelectedItemInfo(save=False,reset=True)

        def setDelete():
            itemSlot = sqlM.DnfItemSlot(b'')
            updateItemEditFrame(itemSlot)

        

        def refill_Tree_View(e=tk.Event):
            try:
                typeSel = int(typeBox.get().split('-')[0],16)
            except:
                typeSel = 0xff
            itemsTreev_now.delete(*itemsTreev_now.get_children())
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
                    rarity = cacheM.get_Item_Info_In_Dict(dnfItemSlot.id).get('[rarity]')
                    if rarity is not None:
                        rarity = f'[{rarity[0]}]-{rarityMap.get(rarity[0])}'
                    values_unpack = [index,name,num,dnfItemSlot.id,rarity]
                    try:
                        itemsTreev_now.insert('',tk.END,values=values_unpack)
                    except:
                        name_new = ''
                        for c in name:
                            name_new += c if ord(c)<0xffff else ''

                        values_unpack = [index,name_new,num,dnfItemSlot.id]
                        itemsTreev_now.insert('',tk.END,values=values_unpack)

                    CharacItemsDict[index] = dnfItemSlot
            set_treeview_color()
            self.w.after(1000,set_treeview_color)   #延迟1s再次检查，等待物品栏分析结果
        
        self.fillTreeFunctions[tabName] = refill_Tree_View
        self.editedItemsDict[tabName] = {}  #存储每个标签页正在编辑的物品
        self.itemInfoClrFuncs[tabName] = clear_item_Edit_Frame
        self.editFrameUpdateFuncs[tabName] = updateItemEditFrame
        self.tabNames.append(tabName)
        
        inventoryFrame = itemEditFrame
        inventoryFrame.pack(expand=True)

        invBowserFrame = itemEditFrame.invBowserFrame


        emptySlotVar = itemEditFrame.emptySlotVar
        emptySlotVar.set(0)
        itemEditFrame.showEmptyBtn.config(command=refill_Tree_View)

        values = [f'0x{"%02x" % item[0]}-{item[1]}' for item in sqlM.DnfItemSlot.typeDict.items()] +['0xff-全部']
        typeBox = itemEditFrame.typeBoxE
        typeBox.config(values=values,state='readonly') 
        typeBox.set('0xff-全部')
        typeBox.bind('<<ComboboxSelected>>',refill_Tree_View)         

            
            

        itemsTreev_now = itemEditFrame.itemsTreev_now
        itemsTreev_now.pack(side=tk.LEFT,fill='both',expand=True)

        itemsTreev_now.tag_configure('edited', background='lightblue')
        itemsTreev_now.tag_configure('deleted', background='gray')
        itemsTreev_now.tag_configure('error', background='red')
        itemsTreev_now.tag_configure('unknow', background='yellow')
        self.itemsTreevs_now[tabName] = itemsTreev_now
        sbar1= itemEditFrame.itemsTreev_bar

        sbar1.config(command =itemsTreev_now.yview)
        itemsTreev_now.config(yscrollcommand=sbar1.set,xscrollcommand=sbar1.set)
        itemsTreev_now.bind('<<TreeviewSelect>>',lambda e:showSelectedItemInfo())
        self.currentTreeViews[tabName] = itemsTreev_now
        self.editFrameShowFuncs[tabName] = showSelectedItemInfo

        
        exportBtn = itemEditFrame.exportBtn
        exportBtn.config(command=lambda:save_blob(globalBlobs_map[tabName]))
        CreateToolTip(exportBtn,text='保存当前数据到文件')
        importBtn = itemEditFrame.importBtn
        importBtn.config(command=lambda:load_blob(globalBlobs_map[tabName]))
        CreateToolTip(importBtn,text='从文件导入数据并覆盖')

        itemSlotEditFrame = itemEditFrame.itemEditFrame
        itemSealVar = itemEditFrame.itemSealVar
        itemSealBtn = itemEditFrame.itemSealBtn
        CreateToolTip(itemSealBtn,'无法封装的物品勾选会炸角色')
        itemNameEntry = itemEditFrame.itemNameEntry
        itemNameEntry.bind("<<ComboboxSelected>>",lambda e:readSlotName('name'))
        itemNameEntry.bind('<Button-1>',searchItem)
        CreateToolTip(itemNameEntry,textFunc=getItemPVFInfo)
        itemIDEntry = itemEditFrame.itemIDEntry
        itemIDEntry.bind('<FocusOut>',lambda e:readSlotName('id'))
        itemIDEntry.bind('<Return>',lambda e:readSlotName('id'))
        # 3

        numGradeLabel = itemEditFrame.numGradeLabel
        numEntry = itemEditFrame.numEntry
        numEntry.config(from_=0, to=4294967295)
        CreateToolTip(numEntry,'当为装备时，表示为品级\n数值与品级关系较为随机\n(0~4,294,967,295)')
        durabilityEntry = itemEditFrame.durabilityEntry

        # 4
        IncreaseTypeEntry = itemEditFrame.IncreaseTypeEntry
        IncreaseTypeEntry.config(values=['空-0','异次元体力-1','异次元精神-2','异次元力量-3','异次元智力-4'])
        IncreaseEntry = itemEditFrame.IncreaseEntry
        IncreaseEntry.config(from_=0, to=65535)

        # 5
        EnhanceEntry = itemEditFrame.EnhanceEntry
        EnhanceEntry.config(from_=0, to=31)
        delBtn = itemEditFrame.delBtn
        delBtn.config(command=setDelete)
        CreateToolTip(delBtn,'标记当前物品为待删除物品')
        # 6
        row = 6
        forgingEntry = itemEditFrame.forgingEntry
        forgingEntry.config(from_=0, to=31)
        resetBtn = itemEditFrame.resetBtn
        resetBtn.config(command=reset)
        # 7 
        def enableTestFrame():
            #print(itemEditFrame.enableTypeChangeVar.get())
            typeEntry.config(state='readonly' if itemEditFrame.enableTypeChangeVar.get() == 1 else 'disable')

        #itemEditFrame.enableTestFrame = enableTestFrame
        enableTestBtn = itemEditFrame.enableTypeBtn
        enableTestBtn.config(command=enableTestFrame)
        row = 7

        typeEntry = itemEditFrame.typeEntry
        typeEntry.config(state='readonly',values=['1-装备','2-消耗品','3-材料','4-任务材料','5-宠物','6-宠物装备','7-宠物消耗品','10-副职业'])
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
        equipmentExFrame = itemEditFrame.equipmentExFrame
        # 8-1
        otherworldEntry = itemEditFrame.otherworldEntry
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

        orbTypeEntry = itemEditFrame.orbTypeEntry
        orbValueEntry = itemEditFrame.orbValueEntry
        orbEntry = itemEditFrame.orbEntry
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

        forthSealEnable = itemEditFrame.forthSealEnable
        forth = itemEditFrame.forth
        CreateToolTip(forth,'启用后无法使用游戏内魔法封印相关修改操作')
    
        magicSealEntrys = [itemEditFrame.magicSealEntry,itemEditFrame.magicSealEntry1,itemEditFrame.magicSealEntry2,itemEditFrame.magicSealEntry3]
        magicSealIDEntrys = [itemEditFrame.magicSealIDEntry,itemEditFrame.magicSealIDEntry1,itemEditFrame.magicSealIDEntry2,itemEditFrame.magicSealIDEntry3]
        magicSealLevelEntrys = [itemEditFrame.magicSealLevelEntry,itemEditFrame.magicSealLevelEntry1,itemEditFrame.magicSealLevelEntry2,itemEditFrame.magicSealLevelEntry3]

        def build_magic_view(i):
            magicSealEntry = magicSealEntrys[i]
            magicSealIDEntry = magicSealIDEntrys[i]
            magicSealLevelEntry = magicSealLevelEntrys[i]
            magicSealEntry.config(values=list(cacheM.magicSealDict.values()))
            magicSealIDEntry.config(state='readonly')
           #magicSealLevelEntry.config(from_=0,to=65535)
            
            magicSealEntry.bind('<Button-1>',lambda e:searchMagicSeal(magicSealEntry))
            magicSealEntry.bind('<<ComboboxSelected>>',lambda e:setMagicSeal(magicSealEntry,magicSealIDEntry))

            CreateToolTip(magicSealLevelEntry,'词条数值，0-65535')
            self.updateMagicSealFuncs[tabName+str(row)] = lambda: magicSealEntry.config(values=list(cacheM.magicSealDict.values()))

        for i in range(4):
            build_magic_view(i)
                
        if True:
            itemSlotBytesE = itemEditFrame.itemSlotBytesE
            CreateToolTip(itemSlotBytesE,textFunc=lambda:'物品字节数据：'+itemSlotBytesE.get())
            def genBytes():
                slotBytes = editSave('bytes')
                itemSlotBytesE.delete(0,tk.END)
                itemSlotBytesE.insert(0,slotBytes.hex())
            genBytesBtn = itemEditFrame.genBytesBtn
            genBytesBtn.config(command=genBytes)
            CreateToolTip(genBytesBtn,'根据物品槽数据编辑结果生成字节')

            def readBytes():
                itemBytes = str2bytes(itemSlotBytesE.get())
                updateItemEditFrame(sqlM.DnfItemSlot(itemBytes))
            importBtn = itemEditFrame.importBytesBtn
            importBtn.config(command=readBytes)
            CreateToolTip(importBtn,'读取字节，导入到编辑框\n用于物品复制')
            commitBtn = itemEditFrame.commitBtn
            commitBtn.config(command=ask_commit)
            CreateToolTip(commitBtn,f'提交当前[{tabName}]页面的所有修改')

    def _buildtab_itemTab_creature(self,creatureF:creatureFeame.CreatureframeWidget,tabName=' 宠物 '):
        def deleteItems():
            if not messagebox.askokcancel('删除确认',f'确定删除{tabName}所选物品？'):
                return False
            deleteIDs = []
            for sel in itemsTree_now.selection():
                delID = itemsTree_now.item(sel)['values'][0]
                deleteIDs.append(delID)
            
            print(f'删除{deleteIDs}')
            tableName = globalNonBlobs_map[tabName]
            for ui_id in deleteIDs:
                if sqlM.delNoneBlobItem(ui_id,tableName):
                    print('====删除成功====\n')
                else:
                    print('====删除失败，请检查数据库连接状况====\n')
            self.blobCommitExFunc(self.cNo)
            self.selectCharac()


        itemsTree_now = creatureF.itemsTreev_now
        self.currentTreeViews[tabName] = itemsTree_now
        self.itemsTreevs_now[tabName] = itemsTree_now
        delBtn = creatureF.deleteBtn
        delBtn.config(command=deleteItems)

    def _buildtab_itemTab_avatar(self,avatarF:avatarFrame.AvatarframeWidget,tabName=' 时装 '):
        def deleteItems():
            if not messagebox.askokcancel('删除确认',f'确定删除{tabName}所选物品？'):
                return False
            deleteIDs = []
            for sel in itemsTree_now.selection():
                delID = itemsTree_now.item(sel)['values'][0]
                deleteIDs.append(delID)
            
            print(f'删除{deleteIDs}')

            tableName = globalNonBlobs_map[tabName]
            for ui_id in deleteIDs:
                if sqlM.delNoneBlobItem(ui_id,tableName):
                    print('====删除成功====\n')
                else:
                    print('====删除失败，请检查数据库连接状况====\n')
            self.blobCommitExFunc(self.cNo)
            self.selectCharac()

        def enableHidden():
            value =int(hiddenCom.get().split('-')[0])
            if not messagebox.askokcancel('提交确认',f'确定修改{tabName}所选物品？'):
                return False
            editIDS = []
            for sel in itemsTree_now.selection():
                delID = itemsTree_now.item(sel)['values'][0]
                editIDS.append(delID)
            log('编辑非BLOB')
            tableName = globalNonBlobs_map[tabName]
            for ui_id in editIDS:
                if sqlM.enable_Hidden_Item(ui_id,tableName,value):
                    print('====修改成功====\n')
                else:
                    print('====修改失败，请检查数据库连接状况====\n')
            self.selectCharac()


        itemsTree_now = avatarF.itemsTreev_now
        self.currentTreeViews[tabName] = itemsTree_now
        itemsTreev_now = itemsTree_now
        self.itemsTreevs_now[tabName] = itemsTreev_now

        hiddenCom = avatarF.avatarHiddenE
        hiddenCom.config(values=['0-None']+[f'{i+1}-{value}' for i,value in enumerate(cacheM.avatarHiddenList[0])],width=int(WIDTH*10))

        hiddenCom.set('0-None')
        self.hiddenCom = hiddenCom
        addHiddenBtn = avatarF.addHiddenBtn
        addHiddenBtn.config(command=enableHidden)
        delBtn = avatarF.deleteBtn
        delBtn.config(command=deleteItems)

    def _buildtab_itemTab_mail(self,mailF:mailFrame.MailframeWidget,tabName=' 邮件 '):
        def deleteItems():
            if not messagebox.askokcancel('删除确认',f'确定删除{tabName}所选物品？'):
                return False
            deleteIDs = []
            for sel in itemsTree_now.selection():
                delID = itemsTree_now.item(sel)['values'][0]
                deleteIDs.append(delID)
            print(f'删除{deleteIDs}')
            tableName = globalNonBlobs_map[tabName]
            for ui_id in deleteIDs:
                if sqlM.delNoneBlobItem(ui_id,tableName):
                    print('====删除成功====\n')
                else:
                    print('====删除失败，请检查数据库连接状况====\n')
            self.blobCommitExFunc(self.cNo)
            self.selectCharac()
    
        itemsTree_now = mailF.itemsTreev_now
        self.currentTreeViews[tabName] = itemsTree_now
        itemsTreev_now = mailF.itemsTreev_now
        self.itemsTreevs_now[tabName] = itemsTreev_now
        delBtn = mailF.deleteBtn
        delBtn.config(command=deleteItems)

    def _buildtab_charac(self,characF:characFrame.CharacframeWidget,tabName):
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
            if cName==self.cName:
                kwDict.pop('charac_name')

            sqlM.set_charac_info(self.cNo,**kwDict)
            if isReturnUser.get()==1:
                sqlM.set_return_user(self.cNo)
            else:
                sqlM.clear_return_user(self.cNo)
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
            isReturnUser.set(sqlM.read_return_user(self.cNo))
            if self.cNo in self.banedDictCno.keys():
                self.isBanedUser.set(1)
            else:
                self.isBanedUser.set(0)

            clear_tab()
            
            nameE.insert(0,cName)
            levE.insert(0,lev)
            jobE.set(f'{job}-{cacheM.jobDict.get(job).get(0)}')
            jobE2.set(f'{expert_job}-{expert_jobMap.get(expert_job)}')
            set_grow_type()
            growTypeE.set(f'{growType}-{cacheM.jobDict.get(job).get(growType)}')
            wakeFlgE.set(wakeFlg)
        
        @inThread
        def set_ban_var(e:tk.Event=None):
            time.sleep(0.3)
            if self.isBanedUser.get()==1:
                sqlM.set_baned(self.uid)
                messagebox.showinfo('提示','已封禁该账号')
            else:
                sqlM.resume_baned(self.uid)
                messagebox.showinfo('提示','已解封该账号')
            self.refill_baned_tree()
        
        def enable_auction(y=None,m=None):
            if y==None:
                y = time.strftime("%Y", time.localtime())
            if m==None:
                m = time.strftime("%m", time.localtime())
            table = f"auction_history_{y}{m}"
            db = sqlM.connectorUsed
            db.select_db('taiwan_cain_auction_gold')
            sql = f'''CREATE TABLE IF NOT EXISTS `{table}`(
                    `auction_id` bigint(20) unsigned NOT NULL DEFAULT '0',
                    `start_time` datetime DEFAULT NULL,
                    `occ_time` datetime DEFAULT NULL,
                    `event_type` tinyint(4) DEFAULT NULL,
                    `owner_id` int(11) DEFAULT NULL,
                    `buyer_id` int(11) DEFAULT NULL,
                    `price` int(11) DEFAULT NULL,
                    `seal_flag` tinyint(4) DEFAULT NULL,
                    `item_id` int(10) unsigned DEFAULT NULL,
                    `add_info` int(11) DEFAULT NULL,
                    `upgrade` tinyint(3) unsigned DEFAULT NULL,
                    `amplify_option` tinyint(3) unsigned NOT NULL DEFAULT '0',
                    `amplify_value` mediumint(8) unsigned NOT NULL DEFAULT '0',
                    `seal_cnt` tinyint(3) unsigned DEFAULT NULL,
                    `endurance` smallint(5) unsigned DEFAULT NULL,
                    `extend_info` int(10) unsigned DEFAULT NULL,
                    `owner_postal_id` int(10) unsigned DEFAULT NULL,
                    `buyer_postal_id` int(10) unsigned DEFAULT NULL,
                    `expire_time` int(10) unsigned NOT NULL DEFAULT '0',
                    `unit_price` int(10) unsigned NOT NULL DEFAULT '0',
                    `random_option` varchar(14) NOT NULL DEFAULT '',
                    `roi_high_key` bigint(20) NOT NULL DEFAULT '0',
                    `roi_low_key` int(11) NOT NULL DEFAULT '0',
                    `seperate_upgrade` tinyint(3) unsigned NOT NULL DEFAULT '0',
                    `commission` int(11) unsigned NOT NULL DEFAULT '0',
                    `owner_type` tinyint(3) unsigned NOT NULL DEFAULT '0',
                    `item_guid` varbinary(10) NOT NULL DEFAULT '',
                    PRIMARY KEY (`auction_id`),
                    KEY `idx_buyer_id` (`buyer_id`) USING BTREE,
                    KEY `idx_occ_time` (`occ_time`) USING BTREE,
                    KEY `idx_owner_id` (`owner_id`) USING BTREE
                    ) ENGINE=MyISAM DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT;'''
            cur = db.cursor()
            cur.execute(sql)

            sql = f'''CREATE TABLE IF NOT EXISTS `auction_history_buyer_{y}{m}` (
                    `auction_id` bigint(20) unsigned DEFAULT NULL,
                    `occ_time` datetime DEFAULT NULL,
                    `pre_buyer_id` int(11) DEFAULT NULL,
                    `buyer_id` int(11) DEFAULT NULL,
                    `pre_price` int(11) DEFAULT NULL,
                    `price` int(11) DEFAULT NULL,
                    `pre_buyer_postal_id` int(10) unsigned DEFAULT NULL,
                    KEY `idx_auction_id` (`auction_id`) USING BTREE,
                    KEY `idx_buyer_id` (`buyer_id`) USING BTREE
                    ) ENGINE=MyISAM DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT;'''
            cur.execute(sql)
            db.commit()
            messagebox.showinfo('提示','已在数据库中添加拍卖行表格，请重启服务端程序。\n如拍卖行无法启动请尝试清空taiwan_cain_auction_gold数据库中的auction_main数据表')
            return True
        self.clear_charac_tab_func = clear_tab
        self.fill_charac_tab_fun = fill_charac_Info_tab
        self.cNo
        
        characMainFrame = characF
        


        characF.saveStartBtn.config(command=ps.saveStart)
        CreateToolTip(characF.saveStartBtn,'读取正在运行的DNF进程\n生成一键登录exe')
        self.PVF_CACHE_EDIT_OPEN_FLG = False

        btn = characF.pvfCacheMBtn
        btn.config(command=self.open_PVF_Cache_Edit)
        CreateToolTip(btn,'修改缓存数据\n导出装备道具列表为CSV')

        btn = characF.pvfToolBtn
        btn.config(command=self._open_PVF_Editor)
        CreateToolTip(btn,'开启PVF编辑工具（测试）')

        auctionBtn = characF.enableAuctionBtn
        auctionBtn.config(command=enable_auction)
        CreateToolTip(auctionBtn,'开启拍卖行，需要手动重启服务端\n当PVF装备锻造可以超过7时，拍卖行无法搜索物品')


        updateCheckVar = characF.updateCheckVar
        updateCheckVar.set(1 if cacheM.config.get('UPDATE_CHECK') is None or cacheM.config.get('UPDATE_CHECK')==1 else 0)
        def setUpdate():
            cacheM.config['UPDATE_CHECK'] = updateCheckVar.get()
            cacheM.save_config()
            if updateCheckVar.get()==1:
                self.check_Update()
        if self.check_update_flg:
            checkUpdateBtn = characF.checkUpdateBtn
            checkUpdateBtn.config(command=setUpdate)
            if updateCheckVar.get()==1:
                self.check_Update()
        HDVar = characF.HDResolutionVar
        HDVar.set(cacheM.config.get('HD_RESOLUTION',0))
        
        def setHD():
            cacheM.config['HD_RESOLUTION'] = HDVar.get()
            cacheM.save_config()
        HDBtn = characF.HDresolutionBtn#HDResolutionBtn
        
        HDBtn.config(command=setHD)
        CreateToolTip(HDBtn,'开启高清分辨率，重启程序后生效')


        nameE = characF.nameE
        self.nameEditE = nameE
        levE = characF.levE
        levE.config(to=999,from_=1)
        isVIP = characF.isVIP
        def set_grow_type(e=None):
            growTypeE.config(values=[f'{item[0]}-{item[1]}' for item in cacheM.jobDict.get(int(jobE.get().split('-')[0])).items()])

        jobE2 = characF.jobE2
        jobE2.config(values=[f'{key}-{value}' for key,value in expert_jobMap.items()])
        jobE = characF.jobE
        jobE.config(values=[f'{item[0]}-{item[1][0]}'  for item in cacheM.jobDict.items()])
        jobE.bind('<<ComboboxSelected>>',set_grow_type)
        self.jobE = jobE

        growTypeE = characF.growTypeE
        wakeFlgE = characF.wakeFlgE
        wakeFlgE.config(state='readonly',values=[0,1])

        isReturnUser = characF.isReturnUser
        commitBtn = characF.commitBtn
        commitBtn.config(command=commit)
        GitHubFrame(characF.gitHubFrame).pack()

        self.cInfoSetBanedBtn.bind('<Button-1>',set_ban_var)

        adLabel = ImageLabel(characF.imageFrame,borderwidth=0)
        adLabel.pack(expand=True,fill='both',side='bottom')

        def loadPics():
            size = adLabel.winfo_width(), adLabel.winfo_height()
            if size[0] < 10:
                return self.w.after(100,loadPics)
            size = size[0]+50,size[1]+50
            adLabel.loadDir(gifPath_2,size,root=self.w)
        self.w.after(100,loadPics)
        def changeGif(e):
            if str(characMainFrame)==self.tabView.select():
                adLabel.randomShow()
        self.tabViewChangeFuncs.append(changeGif)
    
    def _buildtab_GM(self):
        PVPMap_tmp = [f'{i}级' for i in range(1,11)]
        PVPMap_tmp.reverse()
        PVPMap_tmp2 = [f'{i}段' for i in range(1,11)]
        PVPMap_tmp3 = [f'至尊{i}' for i in range(1,11)]
        PVPMap_tmp4 = ['达人','名人','小霸王','霸王','斗神']
        PVPRankList = PVPMap_tmp+PVPMap_tmp2+PVPMap_tmp3+PVPMap_tmp4

        self.get_group_account_characs = lambda:...
        self.get_group_all_characs = lambda:...
        self.get_group_all_uids = lambda:...
        self.delete_mail_group = lambda:...
        self.localEventList = None
        self.blobCommitExFunc = lambda cNo=0:...
        self.updateFuncList = []
        self.eventList = []


        def update_Info():
            for func in self.updateFuncList:
                func()
        self.update_GM = update_Info
        def buildTab_usual():
            def charge(type='cera'):
                if not messagebox.askokcancel('充值确认',f'确定充值？\n将充值到当前角色[{self.cNo}][{self.cName}]'):
                    return False
                #update_cera_and_SP()
                type = ceraTypeE.get()
                value = int(ceraValueE.get())
                if type =='点券':
                    oldValue = cNoInfoDict['cera']
                    #sqlM.set_cera(self.uid,value+cNoInfoDict['cera'],'cera')
                    sqlM.charge_crea(self.uid,value,'cera')
                elif type =='代币':
                    oldValue = cNoInfoDict['cera_point']
                    #sqlM.set_cera(self.uid,value+cNoInfoDict['cera_point'],'cera_point')
                    sqlM.charge_crea(self.uid,value,'cera_point')
                elif type=='SP':
                    oldValue = cNoInfoDict['sp']
                    sqlM.charge_sp(self.cNo,value,'remain_sp')
                    #sqlM.set_skill_sp(self.cNo,value+cNoInfoDict['sp'],value+cNoInfoDict['sp2'],cNoInfoDict['tp'],cNoInfoDict['tp2'])
                elif type=='TP':
                    oldValue = cNoInfoDict['tp']
                    sqlM.charge_sp(self.cNo,value,'remain_sfp_1st')
                    #sqlM.set_skill_sp(self.cNo,cNoInfoDict['sp'],cNoInfoDict['sp2'],value+cNoInfoDict['tp'],value+cNoInfoDict['tp2'])
                elif type=='QP':
                    oldValue = cNoInfoDict['qp']
                    sqlM.charge_quest_point(self.cNo,value)
                    #sqlM.set_quest_point(self.cNo,value+cNoInfoDict['qp'])
                update_Info()
                print(f'角色[{self.cNo}][{self.cName}]-[{type}]充值完成 [{oldValue}]->[{oldValue+value}]')
                self.blobCommitExFunc(self.cNo)
            

            def clear_cera():
                update_cera_and_SP()
                type = ceraTypeE.get()
                if type =='点券':
                    sqlM.set_cera(self.uid,0,'cera')
                elif type =='代币':
                    sqlM.set_cera(self.uid,0,'cera_point')
                elif type=='SP':
                    sqlM.set_skill_sp(self.cNo,0,0,cNoInfoDict['tp'],cNoInfoDict['tp2'])
                elif type=='TP':
                    sqlM.set_skill_sp(self.cNo,cNoInfoDict['sp'],cNoInfoDict['sp2'],0,0)
                elif type=='QP':
                    sqlM.set_quest_point(self.cNo,0)
                update_Info()
                print('清空成功！')
                self.blobCommitExFunc(self.cNo)
            def update_cera_and_SP():
                if 'uid' not in dir(self):
                    return False
                cera, cera_point = sqlM.get_cera(self.uid)
                cNoInfoDict['cera'] = cera
                cNoInfoDict['cera_point'] = cera_point

                sp,sp2,tp,tp2 = sqlM.get_skill_sp(self.cNo)
                cNoInfoDict['sp'] = sp
                cNoInfoDict['sp2'] = sp2
                cNoInfoDict['tp'] = tp
                cNoInfoDict['tp2'] = tp2
                qp = sqlM.get_quest_point(self.cNo)
                cNoInfoDict['qp'] = qp
                ceraSVar.set(cera)#f'{"%6d" % cera}' if cera<999999 else '100w+')
                ceraPointSVar.set(cera_point)#f'{"%6d" % cera_point}' if cera_point<999999 else '100w+')
                spVar.set(sp)#f'{"%6d" % sp}' if sp<999999 else '100w+')
                qpStr = f'{qp}'# if qp<999 else '1k+'
                tpStr = f'{tp}'# if tp<999 else '1k+'
                qpTpVar.set(qpStr+'/'+tpStr)

            
            self.updateFuncList.append(update_cera_and_SP)
            cNoInfoDict = {}
            readOnlyWidgets = []

            ceraSVar = self.ceraSVar
            ceraSVar.set('000000')
            ceraPointSVar = self.ceraPointSVar
            ceraPointSVar.set('000000')
            spVar = self.spVar
            spVar.set('000000')
            qpTpVar = self.qpTpVar
            qpTpVar.set('00/00')

            ceraValueE = self.ceraValueE
            ceraValueE.set(0)
            ceraTypeE = self.ceraTypeE
            ceraTypeE.set('点券')
            readOnlyWidgets.append(ceraTypeE)
            self.ceraChargeBtn.config(command=charge)
            self.ceraClearBtn.config(command=clear_cera)


            def update_PVP():
                if self.cNo==0:
                    return False
                pvp_grade,win,pvp_point,win_point = sqlM.get_PVP(self.cNo)
                PVPgradeE.set(f'{PVPRankList[pvp_grade]}')
                PVPwinNumE.delete(0,tk.END)
                PVPwinNumE.insert(0,win)
                PVPwinPointE.delete(0,tk.END)
                PVPwinPointE.insert(0,win_point)
            
            def set_PVP():
                if not messagebox.askyesno('确认提交','确认提交PVP信息？'):
                    return False
                pvp_grade = PVPRankList.index(PVPgradeE.get())
                win = int(PVPwinNumE.get())
                pvp_point = int(PVPwinPointE.get())
                win_point = pvp_point
                sqlM.set_PVP(self.cNo,pvp_grade,win,pvp_point,win_point)
                update_Info()
                print('PVP数据提交完成')
            
            
            self.updateFuncList.append(update_PVP)

            PVPgradeE = self.PVPgradeE
            PVPgradeE.config(values=[f'{name}' for i,name in enumerate(PVPRankList)])
            readOnlyWidgets.append(PVPgradeE)

            PVPwinNumE = self.PVPwinNumE

            PVPwinPointE = self.PVPwinPointE
            self.PVPCommitBtn.config(command=set_PVP)

            def unlock_dungeon():
                if not messagebox.askyesno('确认提交','确认解锁副本难度？'):
                    return False
                dungeonList = list(cacheM.dungeonDict.keys())
                
                if dungeonList!=[]:
                    dungeons = ''
                    for i in dungeonList:
                        dungeons += f'{i}|3,'
                    dungeons = dungeons[:-1]
                else:
                    dungeons = '1|3,2|3,3|3,4|3,5|3,6|3,7|3,8|3,9|3,11|3,12|3,13|3,14|3,15|3,16|1,17|3,21|3,22|3,23|3,24|3,25|3,26|3,27|3,31|3,32|3,33|3,34|3,35|3,36|3,37|3,40|3,41|2,42|3,43|3,44|3,45|3,50|3,51|3,52|3,53|3,60|3,61|3,62|2,63|3,64|3,65|3,67|3,70|3,71|3,72|3,73|3,74|3,75|3,76|3,77|3,80|3,81|3,82|3,83|3,84|3,85|3,86|3,87|3,88|3,89|3,90|3,91|2,92|3,93|3,100|3,101|3,102|3,103|3,104|3,110|3,111|3,112|3,140|3,141|3,502|3,511|3,515|1,518|1,521|3,1000|3,1500|3,1501|3,1502|3,1507|1,3506|3,10000|3'
                #print(dungeons)
                sqlM.unlock_all_lev_dungeon(self.uid,dungeons)
                print('解锁副本难度指令执行完成')

            def reset_blood_dungeon():
                if not messagebox.askyesno('确认提交','确认重置祭坛次数？'):
                    return False
                sqlM.reset_blood_dungeon(self.cNo)
                print('重置祭坛次数指令执行完成')
            
            def unlock_ALL_Level_equip():
                if not messagebox.askyesno('确认提交','确认解锁装备等级限制？'):
                    return False
                sqlM.unlock_ALL_Level_equip(self.cNo)
                print('解锁装备等级限制指令执行完成')

            def enable_LR_slot():
                if not messagebox.askyesno('确认提交','确认解锁左右槽位？'):
                    return False
                sqlM.enable_LR_slot(self.cNo)
                print('解锁左右槽位指令执行完成')
            
            def maxmize_expert_lev():
                if not messagebox.askyesno('确认提交','确认提升副职业至满级？'):
                    return False
                sqlM.maxmize_expert_lev(self.cNo)
                print('提升副职业至满级指令执行完成')
            
            def unlock_register_limit():
                if not messagebox.askyesno('确认提交','确认解除账号限制？'):
                    return False
                sqlM.unlock_register_limit(self.uid)
                print('解除账号限制指令执行完成')

            unlockBtn = self.liftLimitBtn
            unlockBtn.config(command=unlock_register_limit)
            CreateToolTip(unlockBtn,'解除建号限制、限制交易、封号等账号异常状态')
            self.enableLRSlotBtn.config(command=enable_LR_slot)
            self.liftEquLevLimitBtn.config(command=unlock_ALL_Level_equip)
            self.enableAllLevDungeonBtn.config(command=unlock_dungeon)
            self.resetBloodDungeonBtn.config(command=reset_blood_dungeon)
            self.maxLevExpertBtn.config(command=maxmize_expert_lev)

        def build_Tab_Money():
            pkgMoneyE = self.pkgMoneyE
            pkgMoneyBtn = self.pkgMoneyBtn
            accountMoneyE = self.accountMoneyE
            accountMoneyBtn = self.accountMoneyBtn
            payCoinE = self.payCoinE
            payCoinBtn = self.payCoinBtn
            def get_money():
                if self.cNo==0:
                    return False
                money = sqlM.get_charac_money(self.cNo)
                pkgMoneyE.delete(0,tk.END)
                pkgMoneyE.insert(0,money)
                return money
            def set_money():
                if not messagebox.askokcancel('确认提交','确认提交金币修改？'):
                    return False
                if self.cNo==0:
                    return False
                money = int(pkgMoneyE.get())
                sqlM.set_charac_money(self.cNo,money)
                print(f'角色[{self.cNo}][{self.cName}]金币修改完成[{money}]，请手动重载数据')
            def get_account_money():
                if self.uid==0:
                    return False
                money = sqlM.get_account_money(self.uid)
                accountMoneyE.delete(0,tk.END)
                accountMoneyE.insert(0,money)
                return money
            def set_account_money():
                if not messagebox.askokcancel('确认提交','确认提交账号金币修改？'):
                    return False
                if self.uid==0:
                    return False
                money = int(accountMoneyE.get())
                sqlM.set_account_money(self.uid,money)
                print(f'账号[{self.uid}]金币修改完成[{money}]，请手动重载数据')
                #app.blobCommitExFunc(app.cNo)
            def get_pay_coin():
                if self.cNo==0:
                    return False
                paycoin = sqlM.get_pay_coin(self.cNo)
                payCoinE.delete(0,tk.END)
                payCoinE.insert(0,paycoin)
                return paycoin
            def set_pay_coin():
                if not messagebox.askokcancel('确认提交','确认提交复活币修改？'):
                    return False
                if self.cNo==0:
                    return False
                paycoin = int(payCoinE.get())
                sqlM.set_pay_coin(self.cNo,paycoin)
                print(f'角色[{self.cNo}][{self.cName}]复活币修改完成[{paycoin}]，请手动重载数据')
            
            self.updateFuncList.append(get_money)
            self.updateFuncList.append(get_account_money)
            self.updateFuncList.append(get_pay_coin)

            pkgMoneyBtn.config(command=set_money)
            accountMoneyBtn.config(command=set_account_money)
            payCoinBtn.config(command=set_pay_coin)

        def buildTab_mail():
            def searchItem(e):
                if e.x<100:return
                key = itemNameEntry.get()
                if len(key)>0:
                    res = cacheM.searchItem(key)
                    itemNameEntry.config(values=[item[1] +' '+ str([item[0]]) for item in res])
            def readSlotName(name_id='id'):
                if name_id=='id':
                    id_ = itemIDEntry.get()
                    try:
                        id_ = int(id_)
                    except:
                        id_ = 0
                    name = str(cacheM.ITEMS_dict.get(int(id_)))
                else:
                    name,id_ = itemNameEntry.get().rsplit(' ',1)
                    id_ = id_[1:-1]
                    
                itemIDEntry.delete(0,tk.END)
                itemIDEntry.insert(0,id_)
                itemNameEntry.delete(0,tk.END)
                itemNameEntry.insert(0,name)
                itemNameEntry.config(values=[])
                itemID = int(id_)
                typeid,itemType = cacheM.getStackableTypeMainIdAndZh(itemID)
                
                #print(int(id_),name,typeid,itemType)
                typeEntry.set(str(typeid)+'-'+itemType)

                changeItemSlotType()         
            def getItemPVFInfo():
                try:
                    itemID = int(itemIDEntry.get())
                except:
                    return None
                res = cacheM.get_Item_Info_In_Text(itemID).replace(r'%%',r'%').strip()
                return res
            def changeItemSlotType():
                typeZh = typeEntry.get().split('-')[1] 
                if typeZh in ['装备','宠物','时装']:
                    numGradeLabel.config(text='品级：')
                    for widget in itemEditFrame.children.values():
                        try:
                            widget.config(state='normal')
                        except:
                            pass
                    if enduranceEntry.get()=='':
                        enduranceEntry.insert(0,0)
                    if numEntry.get()=='':
                        numEntry.insert(0,0)
                    if IncreaseTypeEntry.get()=='':
                        IncreaseTypeEntry.set('空-0')
                    if IncreaseEntry.get()=='':
                        IncreaseEntry.insert(0,'0')
                    if EnhanceEntry.get()=='':
                        EnhanceEntry.insert(0,'0')
                    if forgingEntry.get()=='':
                        forgingEntry.insert(0,'0')
                    
                else:
                    for widget in itemEditFrame.children.values():
                        try:
                            widget.config(state='disable')
                        except:
                            pass
                    numGradeLabel.config(state='normal',text='数量：')
                    numEntry.config(state='normal')
                    itemIDEntry.config(state='normal')
                    itemNameEntry.config(state='normal')
                    self.itemIDLabel.config(state='normal')
                    if numEntry.get()=='':
                        numEntry.insert(0,1)
                typeEntry.config(state='readonly')
                goldE.config(state='normal')
                goldLabel.config(state='normal')
            def get_Item_info()->list:
                id = itemIDEntry.get()
                seal = itemSealVar.get()
                num = numEntry.get()
                endurance = enduranceEntry.get()
                IncreaseType = IncreaseTypeEntry.get().split('-')[-1]
                IncreaseValue = IncreaseEntry.get()
                enhanceValue = EnhanceEntry.get()
                forgeLevel = forgingEntry.get()
                itemType = typeEntry.get().split('-')[-1]
                avatar_flag = 0
                creature_flag = 0
                if itemType=='宠物':
                    creature_flag = 1
                elif itemType=='时装':
                    avatar_flag = 1
                    endurance = 1
                    num = 773

                res = []
                for value in [id,seal,num,endurance,IncreaseType,IncreaseValue,enhanceValue,forgeLevel,creature_flag,avatar_flag]:
                    try:
                        res.append(int(value))
                    except:
                        res.append(0)
                return res
            def send_mail(cNo,confirm=False):
                if confirm:
                    if not messagebox.askokcancel('发送确认',f'确定发送邮件到当前角色[{self.cName}][{cNo}]？'):
                        return False
                if cNo==0:
                    messagebox.showerror('错误','请先选择角色')
                    return False
                gold = int(goldE.get())
                sender = senderE.get()
                message = messageE.get()
                letterID = sqlM.send_message(cNo,sender,message)
                messages = cacheM.config.get('MESSAGES',['欢迎使用GM功能，有运行错误请提交issue至GitHub'])
                if messages.index(message)!=0:
                    messages.remove(message)
                    messages.insert(0,message)
                    cacheM.save_config()
                messageE.config(values=messages)
                senders = cacheM.config.get('SENDERS',['背包编辑工具'])
                if senders.index(sender)!=0:
                    senders.remove(sender)
                    senders.insert(0,sender)
                    cacheM.save_config()
                senderE.config(values=senders)
                itemID,seal,num,endurance,IncreaseType,IncreaseValue,enhanceValue,forgeLevel,creature_flag,avatar_flag = get_Item_info()
                if itemID==0 and gold==0:
                    print(f'发送文本完成-{cNo}')
                    return True
                sqlM.send_postal(cNo,letterID,sender,message,itemID,IncreaseType,IncreaseValue,
                                forgeLevel,seal,num,enhanceValue,gold,avatar_flag,creature_flag,endurance)
                if cacheM.stackableDict.get(itemID) is None:
                    num = 1
                print(f'发送完成-角色[{cNo}]-物品[{cacheM.ITEMS_dict.get(itemID)}][{itemID}]-数量[{num}]-金币[{gold}]')
                self.blobCommitExFunc(cNo)
                letter_send_dict[letterID] = {
                    'cNo':cNo, 'itemID':itemID,'gold':gold,'num':num
                }
                if cNo==self.cNo:
                    self.selectCharac()
                
            def send_mail_all():
                characs = sqlM.get_all_charac()
                #print(characs)
                if not messagebox.askokcancel('发送确认',f'确定发送邮件到当前所有的{len(characs)}个角色？'):
                    return False
                i=1
                for cNo,*_ in characs:
                    send_mail(cNo)
                    print(f'当前发送({i}/{len(characs)}/{characs[i]})')
                    i+=1
            def send_mail_VIP(all=False):
                if all==False:
                    characs = sqlM.get_VIP_charac()
                else:
                    characs = sqlM.get_VIP_charac(True)
                print(characs)
                if not messagebox.askokcancel('发送确认',f'确定发送邮件到当前VIP的{len(characs)}个角色？'):
                    return False
                i=1
                for cNo,*_ in characs:
                    send_mail(cNo)
                    print(f'当前发送({i}/{len(characs)})')
                    i+=1
                print(f'发送完成({len(characs)})!')

            def send_mail_online():
                onlineCharacList = sqlM.get_online_charac()
                print(onlineCharacList)
                if not messagebox.askokcancel('发送确认',f'确定发送邮件到当前在线的{len(onlineCharacList)}个角色？'):
                    return False
                
                i=1
                for cNo,*_ in onlineCharacList:
                    send_mail(cNo)
                    print(f'当前发送({i}/{len(onlineCharacList)})')
                    i+=1
                print(f'发送完成({len(onlineCharacList)})!')
            
            @inThread
            def clearAllMail():
                allPostalID = sqlM.get_all_postalID()
                if not messagebox.askokcancel('发送确认',f'确定清空当前所有的{len(allPostalID)}封邮件？'):
                    return False
                i = 1
                for postalID in allPostalID:
                    sqlM.delete_mail_postal(postalID[0])
                    print(f'删除邮件{postalID} {i}/{len(allPostalID)}')
                    i+=1
                

            self.readSlotID = readSlotName
            itemEditFrame = self.itemEditFrame
            itemSealVar = self.itemSealVar
            itemSealVar.set(0)
            itemSealBtn = self.itemSealBtn
            CreateToolTip(itemSealBtn,'无法封装的物品勾选会炸角色')
            itemNameEntry = self.itemNameEntry
            itemNameEntry.bind('<Button-1>',searchItem)
            itemNameEntry.bind("<<ComboboxSelected>>",lambda e:readSlotName('name'))
            CreateToolTip(itemNameEntry,textFunc=getItemPVFInfo)
            itemIDEntry = self.itemIDEntry
            itemIDEntry.bind('<FocusOut>',lambda e:readSlotName('id'))
            itemIDEntry.bind('<Return>',lambda e:readSlotName('id'))
            self.mailItemIDEntry = itemIDEntry
            self.setMailItemIDFun = lambda :readSlotName('id')

            numGradeLabel = self.numGradeLabel

            numEntry = self.numEntry
            CreateToolTip(numEntry,'当为装备时，表示为品级\n数值与品级关系较为随机\n(0~4,294,967,295)')
            enduranceEntry = self.durabilityEntry
            IncreaseTypeEntry = self.IncreaseTypeEntry
            IncreaseTypeEntry.config(state='readonly',values=['空-0','异次元体力-1','异次元精神-2','异次元力量-3','异次元智力-4'])
            IncreaseEntry = self.IncreaseEntry
            
            EnhanceEntry = self.EnhanceEntry

            typeEntry = self.typeEntry
            typeEntry.config(state='readonly',values=['1-装备','2-消耗品','3-材料','4-任务材料','5-宠物','6-宠物装备','7-宠物消耗品','8-时装','10-副职业'])
            typeEntry.bind("<<ComboboxSelected>>",lambda e:changeItemSlotType())
            forgingEntry = self.forgingEntry
            goldLabel = self.goldLabel
            goldE = self.goldE
            goldE.insert(0,'0')
                
            senderE = self.senderE
            senders = cacheM.config.get('SENDERS',['背包编辑工具'])
            senderE.config(values=senders)
            senderE.set(senders[0])
            CreateToolTip(senderE,textFunc=lambda:'发件人：'+senderE.get())
            messageE = self.msgE
            messages = cacheM.config.get('MESSAGES',['欢迎使用GM功能，有运行错误请提交issue至GitHub'])
            messageE.config(values=messages)
            messageE.set(messages[0])
            #messageE.insert(0,'欢迎使用GM功能，有运行错误请提交issue至GitHub')
            CreateToolTip(messageE,textFunc=lambda:'邮件文本：'+messageE.get())

            if True:
                self.send2allBtn.config(command=send_mail_all)
                self.send2onlineBtn.config(command=send_mail_online)
                self.send2VIPaBtn.config(command=send_mail_VIP)
                self.send2VIPcBtn.config(command=lambda:send_mail_VIP(True))
                self.clearMailBtn.config(command=clearAllMail)
                self.send2currentBtn.config(command=lambda:send_mail(self.cNo,True))
        
        def buildTab_event():
            def get_available_event():
                eventList = sqlM.get_event_available()
                from zhconv import convert
                self.eventList = [[item[0],item[1],convert(item[2],'zh-cn')] for item in eventList]
                self.localEventList = None
                import json,pathlib
                EventPath = './config/eventList.json'
                if self.localEventList is None and pathlib.Path(EventPath).exists():
                    self.localEventList = json.load(open(EventPath,'r'))
                if self.localEventList!= self.eventList:
                    if str(self.eventList).count('?')<30:
                        json.dump(self.eventList,open(EventPath,'w'),ensure_ascii=False)
                    elif  self.localEventList is not None:
                        self.eventList = self.localEventList
                eventList_new = [f'{item[0]}-{item[2]}' for item in self.eventList]
                #print(eventList)
                eventNameE.set(f'选择活动({len(eventList_new)})')
                eventNameE.config(values=eventList_new)
            
            def get_running_event():
                eventList = sqlM.get_event_running()
                runningList = []
                for log_id,eventid,para1,para2 in eventList:
                    flg = False
                    for Eid,name,explain in self.eventList:
                        if eventid==Eid:
                            runningList.append([log_id,explain,para1,para2])
                            flg = True
                            break
                    if flg:continue
                    runningList.append([log_id,'explain',para1,para2])
                #print(eventList,runningList)
                for child in eventTreeNow.get_children():
                    eventTreeNow.delete(child)
                for item in runningList:
                    eventTreeNow.insert('',tk.END,values=item)
                return runningList
            update_event_list_func = lambda:[get_available_event(),get_running_event()]
            eventTreeNow = self.eventTreeNow
            eventTreeNow.tag_configure('deleted', background='gray')

            def del_event():
                try:
                    sel = eventTreeNow.item(eventTreeNow.focus())
                    print(sel['values'])
                    id = int(sel['values'][0])
                except:
                    print('未选中活动')
                    return False
                sqlM.del_event(id)
                update_event_list_func()
                print(f'活动已删除，请重启服务器')
            
            def set_event():
                try:
                    id = int(eventNameE.get().split('-')[0])
                    para1 = eventArg1E.get()
                    if para1=='':
                        para1 = 1
                    para2 = 0
                    sqlM.set_event(id,para1,para2)
                except:
                    print('活动添加失败')
                    return False
                print(f'活动已添加，请重启服务器')
                update_event_list_func()
            
            def select_new_event(e):
                eventExplain = eventNameE.get()
                if '百分比' in eventExplain:
                    value = 200
                elif '倍数' in eventExplain:
                    value = 2
                else:
                    value = 1
                eventArg1E.delete(0,tk.END)
                eventArg1E.insert(0,value)
            eventNameE = self.eventNameE
            eventNameE.bind('<<ComboboxSelected>>',select_new_event)
            CreateToolTip(eventNameE,textFunc=eventNameE.get)
            eventArg1E = self.eventArg1E

            refreshBtn = self.refreshEventBtn
            refreshBtn.config(command=lambda:print(f'活动已刷新({len(get_running_event())})'))

            deleteBtn = self.delEventBtn
            deleteBtn.config(command=del_event)
            
            addBtn = self.addEventBtn
            addBtn.config(command=set_event)
            CreateToolTip(addBtn,'添加删除后需重启服务器')
            
            return update_event_list_func
        
        buildTab_usual()
        build_Tab_Money()
        buildTab_mail()
        self.update_event_list_func = buildTab_event()

    def _buildFrame_SSH(self):
        def connect(show=True,key=False):
            def inner():
                if self.connectedFlg:
                    try:
                        ssh.close()
                        self.transPort.close()
                    except:
                        pass
                ip = ipE.get()
                port = int(portE.get())
                user = userE.get()
                self.connectingFlg = True
                if key:
                    keyPath = askopenfilename(filetypes=[('密钥文件','*.pub'),('所有文件','*.*')])
                    if not keyPath:
                        return False
                    
                    try:
                        private_key  = paramiko.RSAKey.from_private_key_file(keyPath)
                    except Exception as e:
                        messagebox.showerror('错误',f'密钥文件错误{e}')
                        return False
                    try:
                        ssh.connect(ip, username=user, port=port, pkey=private_key,timeout=3)
                        self.transPort = paramiko.Transport((ip,port))
                        self.transPort.connect(username=user, pkey=private_key)
                    except Exception as e:
                        if show:
                            print(f'连接失败 {e}')
                            self.title(f'连接失败 {e}')
                        self.connectedFlg = False
                        self.connectingFlg = False
                        return False
                    cacheM.config['SERVER_PWD'] = ''
                else:
                    pwd = pwdE.get()
                    try:
                        ssh.connect(ip, username=user, port=port, password=pwd,timeout=3)
                        self.transPort = paramiko.Transport((ip,port))
                        self.transPort.connect(username=user, password=pwd)
                        
                    except Exception as e:
                        if show:
                            print(f'连接失败 {e}')
                            self.title(f'连接失败 {e}')
                        self.connectedFlg = False
                        self.connectingFlg = False
                        return False
                    cacheM.config['SERVER_PWD'] = pwd
                cacheM.config['SERVER_IP'] = ip
                cacheM.config['SERVER_PORT'] = port
                cacheM.config['SERVER_USER'] = user
                cacheM.config['SERVER_CONFIGS'][ip] = {'port':port,'pwd':pwd,'user':user}
                cacheM.save_config()
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls /root")
                files = ['sh '+item.strip() for item in ssh_stdout.readlines()]
                for fileSelE in fileSelEList:
                    fileSelE.config(values=files)
                self.connectedFlg = True
                #self.ip = ip
                self.title('服务器已连接！')
                self.connectingFlg = False
                configFrame(self.SSHDIYFrame,'normal')
            t = threading.Thread(target = inner)
            t.setDaemon(True)
            t.start()        
        def run_server():
            def inner():
                nonlocal startingFlg
                if startingFlg:
                    print('服务器正在启动中！请点击停止服务器')
                    return False
                startingFlg = True
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("sh /root/run")
                print('DNF服务器启动中...')
                while True:
                    res = ssh_stdout.readline()
                    print(res)
                    if res == '':
                        break
                    if 'Connect To Guild Server' in str(res):
                        print('服务器启动完成')
                        break
                    if 'success' in str(res).lower() or 'error' in str(res).lower():
                        print(str(res).strip())
                        insert2cmdLog(res)
                startingFlg = False
                
            t = threading.Thread(target=inner)
            t.setDaemon(True)
            t.start()
        def stop_server():
            def inner():
                nonlocal startingFlg
                startingFlg = False
                self.title('指令执行中...')
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("sh /root/stop")
                ssh_stdout.readlines()
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("sh /root/stop")
                ssh_stdout.readlines()
                print('服务器已停止')
                self.title('服务器已停止')
            t = threading.Thread(target=inner)
            t.setDaemon(True)
            t.start()

        def restart_channel():
            run_cmd('sh /root/run1')

        def insert2cmdLog(s:str):
            #self.shellLogE.config(state='normal')
            s = s+ '\n' if s[-1]!='\n' else s
            self.shellLogE.insert(tk.END,s)
            #self.shellLogE.config(state='disable')
            self.shellLogE.see(tk.END)

        def run_file(fileName):
            def inner():
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(f'sh "/root/{fileName}"')
                while True:
                    res = ssh_stdout.readline()
                    if res == '':
                        break
                    time.sleep(0.05)
                    self.title(res)
                self.title(f'{fileName}执行完毕')

            t = threading.Thread(target=inner)
            t.setDaemon(True)
            t.start()

        def run_cmd(cmd='ls',endStr=None):
            def inner():
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
                save_diy()
                t = 0
                while True:
                    try:
                        res = ssh_stdout.readline()
                        if res.replace('\n','') == '':
                            t += 1
                            if t==10: break
                        else:
                            t = 0
                            if endStr is not None and endStr in res:
                                break
                            insert2cmdLog(res)
                            print(res.replace('\n',''))
                        time.sleep(0.02)
                    except:
                        break
                #self.title(f'指令执行完毕')
                print(f'指令执行完毕')
                #time.sleep(60)

            t = threading.Thread(target=inner)
            t.setDaemon(True)
            t.start()
            return t

        def load_diy():
            '''diyList = cacheM.config['DIY']
            for i,diy in enumerate(diyList):
                try:
                    fileSelEList[i].set(diy)
                except:
                    pass'''
            diyList = cacheM.config['DIY_2']
            for i,diy in enumerate(diyList):
                try:
                    cmdEList[i].insert(0,diy)
                except:
                    pass
        def save_diy():
            '''diyList = []
            for selE in fileSelEList:
                diyList.append(selE.get())
            cacheM.config['DIY'] = diyList'''
            diyList = []
            for selE in cmdEList:
                diyList.append(selE.get())
            cacheM.config['DIY_2'] = diyList
            cacheM.save_config()
        
        def uploadFile():
            def inner():
                def printTotals(transferred, toBeTransferred):
                    nonlocal time_now
                    if time.time() - time_now>1:
                        print("Transferred: {0}\tOut of: {1}".format(transferred, toBeTransferred))
                        self.title("%.3fM/%.3fM" % (transferred/1e6, toBeTransferred/1e6))
                        time_now += 1

                pvfPath = askopenfilename(filetypes=[('DNF Script.pvf file','*.pvf')])                
                if pvfPath=='' or not Path(pvfPath).exists():
                    self.title('文件错误')
                    return False
                print(pvfPath)
                sftp = paramiko.SFTPClient.from_transport(self.transPort)
                remote_path = r'/home/neople/game/Script.pvf'
                cmd = r'ls /home/neople/game/'
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
                res = ssh_stdout.readlines()
                #print(res)
                if len(res)<5:
                    self.title('目标文件夹异常')
                    return False
                time_now = time.time()
                sftp.put(pvfPath,remote_path,callback=printTotals)
                self.title('上传完成！')
                upPatch = messagebox.askokcancel('上传完成，是否上传等级补丁？')
                if upPatch:
                    remote_path = r'/home/neople/game/df_game_r'
                    patchPath = askopenfilename()    
                    if patchPath=='':
                        self.title('补丁文件错误')
                        return False
                    sftp.put(patchPath,remote_path,callback=printTotals)
            t = threading.Thread(target=inner)
            t.start()
    
        def lsDir(dirPath='/'):
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(f"ls {dirPath}")
            files = [item.strip() for item in ssh_stdout.readlines()]
            return files

        def downloadFile(filePath='',targetPath='',progressBarPos=[200,200],progressBarMaster=None):
            def showProgress(transferred, toBeTransferred):
                #print(transferred,toBeTransferred)
                nonlocal time_now
                if time.time() - time_now>1:
                    progressBar['maximum'] = toBeTransferred
                    # 进度值初始值
                    progressBar['value'] = transferred
                    progressBar.update()
                    time_now += 0.1

            # 使用paramiko下载文件到本机
            if progressBarMaster is None:
                progressBarMaster = self.master
            progressWin = tk.Toplevel(progressBarMaster)
            progressWin.geometry(f"+{progressBarPos[0]}+{progressBarPos[1]}")
            progressWin.overrideredirect(True)
            progressWin.wm_attributes('-topmost', 1)
            progressBar = ttk.Progressbar(progressWin)
            progressBar.pack()
            time_now = time.time()
            try:
                sftp = paramiko.SFTPClient.from_transport(self.transPort)
                sftp.get(filePath, targetPath,callback=showProgress)
            except:
                progressWin.destroy()
                return False
            progressWin.destroy()
            return True
            
        self.run_cmd = run_cmd
        self.lsDir = lsDir
        self.downloadFile = downloadFile
        self.connectingFlg = False
        self.connectedFlg = False
        import paramiko
        ssh = paramiko.SSHClient()
        self.ssh = ssh
        self.transPort:paramiko.Transport = None
        # 允许连接不在know_hosts文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        startingFlg = False
        config = cacheM.config
        if True:
            ipE = self.ipE2
            ipE.insert(0,config['SERVER_IP'])
            portE = self.portE2
            portE.insert(0,config['SERVER_PORT'])
            userE = self.userE2
            userE.insert(0,config['SERVER_USER'])
            pwdE = self.pwdE2
            pwdE.insert(0,config['SERVER_PWD'])
            SSHconBtn = self.sshConBtn
            SSHconBtn.config(command=connect)

            SSHKeyConBtn = self.SSHKeyConBtn
            SSHKeyConBtn.config(command=lambda:connect(key=True))

        #ttk.Separator(serverFrame, orient='horizontal').pack(fill='x')

        runBtn = self.runServerBtn
        runBtn.config(command=run_server)
        CreateToolTip(runBtn,'执行/root/run文件')
        stopBtn = self.stopServerBtn
        stopBtn.config(command=stop_server)
        CreateToolTip(stopBtn,'执行/root/stop文件')
        run1Btn = self.restartChBtn
        run1Btn.config(command=restart_channel)

        CreateToolTip(run1Btn,'执行/root/run1文件')
        uploadBtn = self.uploadPVFBtn
        uploadBtn.config(command=uploadFile)
        CreateToolTip(uploadBtn,'上传到/home/neople/game/Script.pvf并将原文件覆盖')

        cmdEList = [self.cmdE1,self.cmdE2,self.cmdE3,self.cmdE4]
        fileSelEList = cmdEList
        cmdRunBtnList = [self.runBtn1,self.runBtn2,self.runBtn3,self.runBtn4]
        for cmdRunBtn in cmdRunBtnList:
            cmdRunBtn.config(command=lambda:run_cmd(cmdEList[cmdRunBtnList.index(cmdRunBtn)].get()))
        
        configFrame(self.SSHDIYFrame,'disabled')

        load_diy()

    def _buildTab_Baned(self):
        @inThread
        def refill_baned_tree():
            self.banedTreeV.delete(*self.banedTreeV.get_children())
            banedDict = sqlM.get_baned_Dict_detail()
            banedDictCno = {}
            for uid,BanInfo in banedDict.items():
                characs = sqlM.getCharacterInfo(uid=uid)
                for uid_,cNo,name,lev,job,growType,deleteFlag,expert_job in characs:
                    if deleteFlag==1:continue
                    jobDict = cacheM.jobDict.get(job)
                    if isinstance(jobDict,dict):
                        jobNew = jobDict.get(growType % 16)
                    else:
                        jobNew = growType % 16
                    values = [BanInfo['accountName'],uid,cNo,lev,name,jobNew,BanInfo['ip']]
                    banedDictCno[cNo] = {
                        'uid':uid,'name':name,'job':jobNew,'lev':lev,'ip':BanInfo['ip']
                    }
                    self.banedTreeV.insert('',tk.END,values=values)
            self.banedDictCno = banedDictCno
        
        def set_baned_a():
            aName = self.banAnameE.get()
            try:
                uidINT = int(aName)
            except:
                uidINT = 0
            try:
                uidSTR = int(sqlM.getUID(aName))
            except:
                uidSTR = 0
            if uidINT==0 and uidSTR==0:
                messagebox.askokcancel('未查询到账号','请检查输入的账号是否正确')
                return False
            elif uidINT!=0 and uidSTR!=0:
                res = messagebox.askyesnocancel('查询到UID和用户名','选择是封禁UID，选择否封禁用户名')
                if res==True:
                    uid = uidINT
                elif res==False:
                    uid = uidSTR
                else:
                    return False
            else:
                uid = max(uidINT,uidSTR)
            if not messagebox.askokcancel('封禁确认',f'确定封禁账号[{uid}]？'):
                return False
            sqlM.set_baned(uid)
            print(f'封禁完成-{uid}')
            self.refill_baned_tree()

        
        def set_baned_c():
            cName = self.banCnameE.get()
            characs = sqlM.getCharacterInfo(cName=cName)
            if len(characs)>1:
                messagebox.askokcancel('查询到多个角色','请在首页进行查询后，在GM页面设置封禁')
                return False
            elif len(characs)==1:
                if not messagebox.askokcancel('封禁确认',f'确定封禁角色{characs[0]}？'):
                    return False
                uid = characs[0][0]
                sqlM.set_baned(uid)
                print(f'封禁完成-{uid}')
                self.refill_baned_tree()
            else:
                messagebox.askokcancel('未查询到角色','请检查输入的角色名是否正确')
                return False

        def set_resume():
            if not messagebox.askokcancel('解封确认','确定解封当前选中的角色？'):
                return False
            sels = self.banedTreeV.selection()
            for sel in sels:
                uid = self.banedTreeV.item(sel)['values'][1]
                sqlM.resume_baned(uid)
                print(f'解封账号-{uid}')
            self.refill_baned_tree()

        self.setBanedABtn.config(command=set_baned_a)
        self.setBanedCBtn.config(command=set_baned_c)
        self.resumeBanedBtn.config(command=set_resume)
            
        
        self.refill_baned_tree = refill_baned_tree
        self.banedDictCno = {}




    def fill_tab_treeviews(self,taskID=0):
        '''根据当前本地的blob和非blob字段填充数据（不包括角色信息）'''
        self.selectedCharacItemsDict = {}
        for key in self.editedItemsDict.keys():
            self.editedItemsDict[key] = {}    #清空编辑的对象
        
        # 填充blob字段
        #print(self.globalCharacBlobs.keys())
        #print(len(self.globalCharacBlobs.keys()))
        for tabName,currentTabBlob in self.globalCharacBlobs.items():#替换填充TreeView
            #print(tabName)
            CharacItemsList = []
            itemsTreev_now = self.itemsTreevs_now[tabName]
            itemsTreev_now.delete(*itemsTreev_now.get_children())
            
            CharacItemsList = sqlM.unpackBLOB_Item(currentTabBlob)
            #print(len(CharacItemsList))
            if len(CharacItemsList)==0:
                print(f'{tabName}字段解压错误或不存在')
            CharacItemsDict = {}
            self.currentItemDict = {}
            for values in CharacItemsList:
                index, dnfItemSlot = values
                name = str(cacheM.ITEMS_dict.get(dnfItemSlot.id))
                CharacItemsDict[index] = dnfItemSlot
            self.selectedCharacItemsDict[tabName] = CharacItemsDict
            #print('字段处理完成')
            if len(self.loadPkgTaskList)>taskID+1: return
            self.itemInfoClrFuncs[tabName]()    #清除物品信息显示
            self.fillTreeFunctions[tabName]()   #填充treeview
            #print(tabName,'填充完毕')
        #print('blob字段填充完毕')
        self.hiddenCom.set('0-None')
        self.checkBloblegal()   #检查物品合法

        tabName = ' 宠物 '
        currentTabItems = self.globalCharacNonBlobs.get(tabName)
        try:
            itemsTreev_now = self.itemsTreevs_now[tabName]
            itemsTreev_now.delete(*itemsTreev_now.get_children())
            CharacNoneBlobItemsDict = {}
            for values in currentTabItems:
                if len(self.loadPkgTaskList)>taskID+1: return
                itemsTreev_now.insert('',tk.END,values=values)
                CharacNoneBlobItemsDict[values[0]] = values
            self.selectedCharacItemsDict[tabName] = CharacNoneBlobItemsDict
        except:
            print(f'{tabName}加载失败')
        
        tabName = ' 时装 '
        currentTabItems = self.globalCharacNonBlobs.get(tabName)
        try:
            itemsTreev_now = self.itemsTreevs_now[tabName]
            itemsTreev_now.delete(*itemsTreev_now.get_children())
            CharacNoneBlobItemsDict = {}
            for values in currentTabItems:
                if len(self.loadPkgTaskList)>taskID+1: return
                try:
                    values[3] = cacheM.avatarHiddenList[0][values[3]-1] if values[3]>0 else '---'
                except:
                    pass
                itemsTreev_now.insert('',tk.END,values=values)
                CharacNoneBlobItemsDict[values[0]] = values
            self.selectedCharacItemsDict[tabName] = CharacNoneBlobItemsDict
        except:
            print(f'{tabName}加载失败')
        
        tabName = ' 邮件 '
        currentTabItems = self.globalCharacNonBlobs.get(tabName)
        try:
            itemsTreev_now = self.itemsTreevs_now[tabName]
            itemsTreev_now.delete(*itemsTreev_now.get_children())
            CharacNoneBlobItemsDict = {}
            for values in currentTabItems:
                if len(self.loadPkgTaskList)>taskID+1: return
                #print(values)
                try:
                    itemID = values[2]
                    values[1] = cacheM.ITEMS_dict.get(itemID)
                    if cacheM.equipmentDict.get(itemID) is not None:
                        values[4] = 1 
                except:
                    pass
                itemsTreev_now.insert('',tk.END,values=values)
                CharacNoneBlobItemsDict[values[0]] = values
            self.selectedCharacItemsDict[tabName] = CharacNoneBlobItemsDict
        except:
            print(f'{tabName}加载失败')
        if len(self.loadPkgTaskList)>taskID+1: return
        self.infoSvar.set(f' 加载角色：{self.cName}({self.cNo})')
        self.fillingFlg = False

    def run(self):
        self.mainwindow.mainloop()

    def readSlotName(self):
        ...
    
    def searchItem(self):
        ...
    
    def readSlotID(self):
        ...
    
    def changeItemSlotType(self):
        ...
    
    def saveStart(self):
        ...
    
    def enable_auction(self):
        ...
    
    def set_grow_type(self,e=None):
        ...
    
    def commit(self):
        ...

    def connectSQL(self,dbConn=None):
        def inner():
            config = cacheM.config
            config['DB_IP'] = self.db_ipE.get()
            config['DB_PORT'] = int(self.db_portE.get())
            config['DB_USER'] = self.db_userE.get()
            config['PVF_PATH'] = cacheM.config.get('PVF_PATH')
            self.mainwindow.update()
            pwd = self.db_pwdE.get()
            if pwd!='******':
                config['DB_PWD'] = pwd
            else:
                pwd = config['DB_PWD']
            #log(str(config))
            cacheM.config = config
            sqlresult = sqlM.connect(print,conn=dbConn)
            if '失败' not in sqlresult:  
                self.accountSearchBtn.config(state='normal')
                self.characSearchBtn.config(state='normal')
                #self.connectorE.config(values=[f'{i}-'+str(connector['account_db']) for i,connector in enumerate(sqlM.connectorAvailuableDictList)])
                self.connectorE.config(values=[f'{i}-'+str(connector) for i,connector in enumerate(sqlM.connectorAvailuableList)])
                #self.connectorE.set(f"0-{sqlM.connectorAvailuableDictList[0]['account_db']}")
                self.connectorE.set(f"0-{sqlM.connectorAvailuableList[0]}")
                onlineCharacs = sqlM.get_online_charac()
                self.fillCharac(onlineCharacs)
                print(f'当前在线角色已加载({len(onlineCharacs)})')
                if self.GM_Tool_Flg:
                    self.GMTool.update_Info()
            print(sqlresult)
            self.password = pwd
            self.db_conBTN.config(text='重新连接',state='normal')
            self.db_pwdE.delete(0,tk.END)
            
            self.db_pwdE.insert(0,'******')
            CreateToolTip(self.db_conBTN,'重新连接数据库并加载在线角色列表')
            self.update_event_list_func()
            self.refill_baned_tree()
            self.CONNECTING_FLG = False
            
        if self.CONNECTING_FLG == False:
            self.db_conBTN.config(state='disable')
            self.CONNECTING_FLG = True
            print('正在连接数据库...')
            t = threading.Thread(target=inner)
            t.start()

    def open_PVF_Cache_Edit(self):
        def quit_edit():
            pvfEditMainWin.destroy()
            self.PVF_CACHE_EDIT_OPEN_FLG = False
        def update_pvf_cache_sel():
            res = []
            for MD5,infoDict in cacheM.cacheManager.tinyCache.items():
                if not isinstance(infoDict,dict):continue
                res.append(f'{infoDict["nickName"]}-{MD5}')
            self.PVFCacheE.config(values=res)
            pvfMD5 = self.PVFCacheE.get().split('-')[-1]
            if len(pvfMD5)>0:
                if cacheM.cacheManager.tinyCache.get(pvfMD5) is None:
                    self.PVFCacheE.set(f'请选择PVF缓存')
                else:
                    self.PVFCacheE.set(f'{cacheM.cacheManager.tinyCache[pvfMD5].get("nickName")}-{pvfMD5}')
            print('PVF缓存已保存')
        from pvfCacheFrame import PVFCacheCfgFrame
        if self.PVF_CACHE_EDIT_OPEN_FLG:
            self.pvfEditWin.state('normal')
            self.pvfEditWin.wm_attributes('-topmost', 1)
            self.pvfEditWin.wm_attributes('-topmost', 0)
            self.cacheEditFrame.fillTree()
            return False
        self.PVF_CACHE_EDIT_OPEN_FLG = True
        pvfEditMainWin = tk.Toplevel(self.tabView)
        #pvfEditMainFrame.wm_attributes('-topmost', 1)
        #pvfEditMainFrame.wm_attributes('-topmost', 0)
        #pvfEditMainFrame.wm_overrideredirect(1)
        pvfEditMainWin.wm_geometry("+%d+%d" % (self.characFrame.pvfCacheMBtn.winfo_rootx(), self.characFrame.pvfCacheMBtn.winfo_rooty()))
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

    def _open_GM(self,sshAutoFlg=True):
        #self._open_PVF_Editor()
        
        if self.GM_Tool_Flg:
            self.GMTool.state('normal')
            self.GMTool.wm_attributes('-topmost', 1)
            self.GMTool.wm_attributes('-topmost', 0)
            return False
        self.GMTool = gmToolGUI.GMToolWindow(self.tabView,cNo=self.cNo,sponsorFrame=self.sponsorFrame,sshAutoConnect=sshAutoFlg)
        self.GMTool.blobCommitExFunc = self.blobCommitExFunc
        self.GM_Tool_Flg = True
        def quit():
            if self.quit_GM_Ex_func()!=False:
                self.GM_Tool_Flg=False
                self.GMTool.destroy()
                self.GMTool = None
            else:
                self.GMTool.state('icon')
        self.GMTool.protocol('WM_DELETE_WINDOW',quit)
        self.openGMExFunc(self.GMTool)

    def _open_PVF_Editor(self):
        def quit():
            self.PVF_EDIT_OPEN_FLG=False
            self.PVFToolWin.destroy()
        
        if self.PVF_EDIT_OPEN_FLG:
            self.PVFToolWin.state('normal')
            self.PVFToolWin.wm_attributes('-topmost', 1)
            self.PVFToolWin.wm_attributes('-topmost', 0)
            return False
        PVFToolMainWin = tk.Toplevel(self.stkSearchBtn)
        
        #advanceSearchMainFrame.wm_attributes('-topmost', 1)
        #advanceSearchMainFrame.wm_overrideredirect(1)
        #PVFToolMainWin.wm_geometry("+%d+%d" % (self.advanceSearchBtn.winfo_rootx(), self.advanceSearchBtn.winfo_rooty()))
        self.PVFToolWin = PVFToolMainWin
        self.PVFTool = pvfEditorGUI.PvfeditmainframeApp(self.PVFToolWin)
        self.PVF_EDIT_OPEN_FLG = True
        PVFToolMainWin.title('PVF编辑器 测试版')
        PVFToolMainWin.iconbitmap(IconPath)
        PVFToolMainWin.protocol('WM_DELETE_WINDOW',quit)

    def open_advance_search_equipment(self):
        
        def start_Search():
            searchResultTreeView.delete(*searchResultTreeView.get_children())
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
                searchList = list(searchList)[:100000]

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

        def apply_Search_result_mail():
            values = searchResultTreeView.item(searchResultTreeView.focus())['values']
            itemID,name,type_,lev,rarity = values
            self.itemIDEntry.delete(0,tk.END)
            self.itemIDEntry.insert(0,itemID)
            self.readSlotID()
            self.tabView.select(self.tabIDDict.get(' 邮件 '))
            #self._open_GM()
            if self.GM_Tool_Flg:
                self.GMTool.tab.select(self.GMTool.mailTabID)
                self.GMTool.mailItemIDEntry.delete(0,tk.END)
                self.GMTool.mailItemIDEntry.insert(0,itemID)
                self.GMTool.setMailItemIDFun()
            
        if self.Advance_Search_State_FLG==True:
            self.advanceEquSearchMainFrame.state('normal')
            self.advanceEquSearchMainFrame.wm_attributes('-topmost', 1)
            self.advanceEquSearchMainFrame.wm_attributes('-topmost', 0)
            return False
        self.Advance_Search_State_FLG = True
        advanceSearchMainWin = tk.Toplevel(self.equSearchBtn)
        
        #advanceSearchMainFrame.wm_attributes('-topmost', 1)
        #advanceSearchMainFrame.wm_overrideredirect(1)
        advanceSearchMainWin.wm_geometry("+%d+%d" % (self.equSearchBtn.winfo_rootx(), self.equSearchBtn.winfo_rooty()))
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
        btnFrame.grid(row=row,column=3,columnspan=2,sticky='ns',pady=5)
        ttk.Button(btnFrame,text='查询',command=start_Search,width=8).grid(row=row,column=3)
        commitBtn = ttk.Button(btnFrame,text='提交编辑',command=apply_Search_result,width=8)
        commitBtn.grid(row=row,column=4)  
        CreateToolTip(commitBtn,'提交至物品编辑框')
        commitBtn2 = ttk.Button(btnFrame,text='提交邮件',command=apply_Search_result_mail,width=8)
        commitBtn2.grid(row=row,column=5)  
        CreateToolTip(commitBtn2,'提交至邮件')
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
        scrollBar= ttk.Scrollbar(advanceSearchFrame)
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
        
        def start_Search():
            searchResultTreeView.delete(*searchResultTreeView.get_children())
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
                    for i,id in enumerate(searchDict.keys()):
                        searchDict[id] = searchDict[id] + '\n' + cacheM.get_Item_Info_In_Text(id).strip()
                        #print(i)
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

        def apply_Search_result_mail():
            values = searchResultTreeView.item(searchResultTreeView.focus())['values']
            itemID,name,type_,lev,rarity = values
            self.itemIDEntry.delete(0,tk.END)
            self.itemIDEntry.insert(0,itemID)
            self.readSlotID()
            self.tabView.select(self.tabIDDict.get(' 邮件 '))
            #self._open_GM()
            if self.GM_Tool_Flg:
                self.GMTool.tab.select(self.GMTool.mailTabID)
                self.GMTool.mailItemIDEntry.delete(0,tk.END)
                self.GMTool.mailItemIDEntry.insert(0,itemID)
                self.GMTool.setMailItemIDFun()

        if self.Advance_Search_State_FLG_Stackable==True:
            self.advanceStkSearchMainFrame.state('normal')
            self.advanceStkSearchMainFrame.wm_attributes('-topmost', 1)
            self.advanceStkSearchMainFrame.wm_attributes('-topmost', 0)
            return False
        self.Advance_Search_State_FLG_Stackable = True
        advanceSearchMainWin = tk.Toplevel(self.stkSearchBtn)
        #advanceSearchMainFrame.wm_attributes('-topmost', 1)
        #advanceSearchMainWin.wm_overrideredirect(1)
        advanceSearchMainWin.iconbitmap(IconPath)
        advanceSearchMainWin.wm_geometry("+%d+%d" % (self.stkSearchBtn.winfo_rootx(), self.stkSearchBtn.winfo_rooty()))
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
        btnFrame.grid(row=row,column=3,columnspan=2,sticky='ns',pady=5)
        ttk.Button(btnFrame,text='查询',command=start_Search,width=8).grid(row=row,column=3)
        commitBtn = ttk.Button(btnFrame,text='提交',command=apply_Search_result,width=8)
        commitBtn.grid(row=row,column=4)  
        CreateToolTip(commitBtn,'提交至物品编辑框')

        commitBtn2 = ttk.Button(btnFrame,text='提交邮件',command=apply_Search_result_mail,width=8)
        commitBtn2.grid(row=row,column=5)  
        CreateToolTip(commitBtn2,'提交至邮件')

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

        searchResultTreeView.grid(row=1,column=8,rowspan=10)
        scrollBar= ttk.Scrollbar(advanceSearchFrame)
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

    def check_Update(self):
        import subprocess, os
        def update_fin():
            openACK = messagebox.askyesno('下载完成','是否打开文件位置？')
            if openACK:
                openDirCMD = f'explorer.exe /select,{updateM.targetPath}'
                subprocess.Popen(openDirCMD,shell=False)
        def inner():
            if not self.check_update_flg:
                return 
            print('检查更新中...')
            updateState = updateM.check_Update()
            #print(f'更新状态：{updateState}')
            if updateState:
                
                print(f'有文件更新 {updateM.versionDict_remote["URL"]}')
                fileName = updateM.versionDict_remote.get("URL").rsplit("/",1)[-1]
                print('文件名：',fileName,updateM.versionDict_remote.get("URL"))
                updateACK = messagebox.askyesno('有软件更新！',f'是否下载最新版本？也可点击其他页面GitHub图标手动下载\n最新版本号：{updateM.versionDict_remote.get("VERSION")} {fileName}\n{updateM.versionDict_remote.get("INFO")}')
                if updateACK and updateM.targetPath.exists():
                    updateACK = messagebox.askyesno('目标文件已存在！','是否覆盖已下载版本？')
                if updateACK:
                    updateM.get_Update2(update_fin)
                    print(f'正在下载最新版本...{updateM.versionDict_remote["VERSION"]}')
        t = threading.Thread(target=inner)
        t.setDaemon(True)
        t.start()

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
                self.errorInfoDict[tabName][index] = ''
                if itemSlot.isSeal==1 and cacheM.PVFcacheDict['stackable_detail'].get(itemSlot.id) is None:
                    attach_type = cacheM.get_Item_Info_In_Dict(itemSlot.id).get('[attach type]')
                    if attach_type is not None and attach_type[0]!='[sealing]':
                        self.errorItemsListDict[tabName].append(index)
                        self.errorInfoDict[tabName][index] += f'物品封装状态冲突-当前为封装 \n'
                typeID,typeZh = cacheM.getStackableTypeMainIdAndZh(itemSlot.id)
                #print(typeID,typeZh,cacheM.ITEMS_dict.get(itemSlot.id))
                #常规判断，标记种类是否与实际种类冲突
                
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


    def sel_IP(self, event=None):
        ip = self.db_ipE.get()
        if cacheM.config.get('DB_CONFIGS').get(ip) is not None:
            port = cacheM.config.get('DB_CONFIGS').get(ip)['port']
            pwd = cacheM.config.get('DB_CONFIGS').get(ip)['pwd']
            user = cacheM.config.get('DB_CONFIGS').get(ip)['user']
            self.db_portE.delete(0,tk.END)
            self.db_portE.insert(0,port)
            self.db_pwdE.set(pwd)
            self.db_userE.delete(0,tk.END)
            self.db_userE.insert(0,user)


    def search_Account(self):
        self.search_Account_()


    def search_Charac(self):
        self.search_Charac_()


    def sel_Sql_Encode(self, event=None):
        self.sel_Sql_Encode_()


    def sel_PVF_Cache(self, event=None):
        self.load_PVF(self.PVFCacheE.get().split('-')[-1])


    def openPVF(self):
        self.load_PVF('')

    @inThread
    def selectCharac(self, event=None):
        t = self.selectCharac_(True)
        t.join()

    def set_gm_startup(self):
        cacheM.config['GMTOOL_STARTUP'] = self.autoGMVar.get()
        cacheM.save_config()

    def change_TabView(self, e=None):
        for func in self.tabViewChangeFuncs:
            func(e)
        ...

def run():
    #from ttkthemes import themed_tk
    root = tk.Tk()
    #root = themed_tk.ThemedTk(theme='yaru')
    root.title('背包编辑工具')
    W = 730
    H = 500
    try:
        import ctypes
        #获取屏幕的缩放因子
        ScaleFactor=ctypes.windll.shcore.GetScaleFactorForDevice(0)
        #设置程序缩放
        if cacheM.config.get('HD_RESOLUTION')==1:
            #告诉操作系统使用程序自身的dpi适配
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            root.tk.call('tk', 'scaling', ScaleFactor/75)
            W = W*ScaleFactor//100
            H = H*ScaleFactor//100
            s=ttk.Style()
            #s.theme_use('classic')

            # Add the rowheight
            s.configure('Treeview', rowheight=20*ScaleFactor//100)
    except:
        print('高清缩放失败')
    root.geometry(f'{W}x{H}')
    def fixed_map(option):
        return [elm for elm in style.map('Treeview', query_opt=option) if
        elm[:2] != ('!disabled', '!selected')]
    style = ttk.Style()
    style.map('Treeview', foreground=fixed_map('foreground'),
    background=fixed_map('background'))
    app = GuiApp(root)
    if cacheM.config.get('PVF_PATH')!='':
        app.w.after(2000,lambda:app.load_PVF(cacheM.config.get('PVF_PATH')))
    
    app.w.after(200,app.connectSQL)
    #print(ScaleFactor)
    

    app.run()
    for localVar,localValue in locals().items():
        globals()[localVar] = localValue
    


if __name__ == "__main__":
    run()
    

