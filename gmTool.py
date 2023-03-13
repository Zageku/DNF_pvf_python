import sqlManager2 as sqlM
import cacheManager as cacheM
import tkinter as tk
from tkinter import ttk
from toolTip import CreateToolTip
from zhconv import convert
IconPath = './config/ico.ico'
if not hasattr(ttk,'Spinbox'):
    class Spinbox(ttk.Entry):
        def __init__(self, master=None, **kw):  #from_=0,to=99,
            ttk.Entry.__init__(self, master, "ttk::spinbox", **kw)
        def set(self, value):
            self.tk.call(self._w, "set", value)
    ttk.Spinbox = Spinbox

def configFrame(frame:tk.Frame,state='disable'):
    for widget in frame.children.values():
        if type(widget) in [tk.Frame,tk.LabelFrame,ttk.LabelFrame]:
            configFrame(widget,state)
        else:
            try:
                widget.config(state=state)
            except:
                continue

class GMToolWindow(tk.Toplevel):
    def __init__(self,master,title='GM工具测试版',cNo=0,*args,**kw):
        self.cNo = cNo
        self.uid = 0
        if sqlM.connectorUsed is not None:
            self.uid = sqlM.cNo_2_uid(self.cNo)
        self.updateFuncList = []
        self.eventList = []
        tk.Toplevel.__init__(self,master=master,*args,**kw)
        self.title(title)
        self.iconbitmap(IconPath)
        self.tab = ttk.Notebook(self)
        self.tab.pack()
        self.buildTab_usual(self.tab,'常用功能')
        self.buildTab_mail(self.tab,'邮件功能')
        self.buildTab_event(self.tab,'活动管理')
        self.buildTab_server(self.tab,'服务器管理')
        self.update_Info()
        self.resizable(False,False)
    
    def update_Info(self):
        if sqlM.connectorUsed is None:
            return False
        if self.cNo!=0:
            self.uid = sqlM.cNo_2_uid(self.cNo)
        for func in self.updateFuncList:
            func()

    def buildTab_usual(self,tabView:ttk.Notebook,tabName:str):
        def charge(type='cera'):
            cera, cera_point = sqlM.get_cera(self.uid)
            if type=='cera':
                value = int(ceraValueE.get()) + cera 
            elif type=='cera_point':
                value = int(ceraValueE.get()) + cera_point
            sqlM.set_cera(self.uid,value,type)
            self.update_Info()
        def clear_cera(type='cera'):
            sqlM.set_cera(self.uid,0,type)
            self.update_Info()

        def update_cera():
            if self.cNo==0:
                configFrame(usualFrame,'disable')
                return False
            cera, cera_point = sqlM.get_cera(self.uid)
            ceraSVar.set(f'点券：{"%6d" % cera}' if cera<999999 else '点券：100w+')
            ceraPointSVar.set(f'代币：{"%6d" % cera_point}' if cera_point<999999 else '代币：100w+')
            configFrame(usualFrame,'normal')
        
        self.updateFuncList.append(update_cera)
        usualFrame = tk.Frame(tabView)
        tabView.add(usualFrame,text=tabName)
        cfgFrame = {
            'padx':3,
            'pady':3,
            'sticky':'nswe'
        }
        chargeFrame = ttk.LabelFrame(usualFrame,text='充值')
        chargeFrame.grid(row=1,column=1,**cfgFrame)
        if True:
            cfg = {'padx':3,'pady':3}
            ceraSVar = tk.StringVar()
            ceraSVar.set('点券：000000')
            ceraPointSVar = tk.StringVar()
            ceraPointSVar.set('代币：000000')
            tk.Label(chargeFrame,textvariable=ceraPointSVar).grid(row=0,column=1,**cfg)
            tk.Label(chargeFrame,textvariable=ceraSVar).grid(row=0,column=2,**cfg)

            ceraValueE = ttk.Spinbox(chargeFrame,from_=0,to=999999)
            ceraValueE.grid(row=1,column=1,columnspan=2,sticky='we',**cfg)
            ttk.Button(chargeFrame,text='充值代币',command=lambda:charge('cera_point')).grid(row=2,column=1,**cfg)
            ttk.Button(chargeFrame,text='充值点券',command=lambda:charge('cera')).grid(row=2,column=2,**cfg)
            ttk.Button(chargeFrame,text='清空代币',command=lambda:clear_cera('cera_point')).grid(row=3,column=1,**cfg)
            ttk.Button(chargeFrame,text='清空点券',command=lambda:clear_cera('cera')).grid(row=3,column=2,**cfg)
        
        def update_PVP():
            if self.cNo==0:
                return False
            pvp_grade,win,pvp_point,win_point = sqlM.get_PVP(self.cNo)
            PVPgradeE.set(pvp_grade)
            PVPwinNumE.delete(0,tk.END)
            PVPwinNumE.insert(0,win)
            PVPwinPointE.delete(0,tk.END)
            PVPwinPointE.insert(0,win_point)
        
        def set_PVP():
            pvp_grade = int(PVPgradeE.get())
            win = int(PVPwinNumE.get())
            pvp_point = int(PVPwinPointE.get())
            win_point = pvp_point
            sqlM.set_PVP(self.cNo,pvp_grade,win,pvp_point,win_point)
            self.update_Info()
            self.title('提交成功！')
        
        
        self.updateFuncList.append(update_PVP)
        pvpFrame = ttk.LabelFrame(usualFrame,text='PVP数据')
        pvpFrame.grid(row=1,column=2,**cfgFrame)
        if True:
            cfg = {'padx':3,'pady':4}
            PVPgradeE = ttk.Combobox(pvpFrame,width=8,values=list(range(35)))
            PVPgradeE.grid(row=1,column=1,columnspan=2,sticky='we',**cfg)
            PVPwinNumE = ttk.Spinbox(pvpFrame,from_=0,to=999999,width=8)
            PVPwinNumE.grid(row=2,column=1,columnspan=1,sticky='we',**cfg)
            tk.Label(pvpFrame,text='胜场').grid(row=2,column=2,columnspan=1,sticky='we',**cfg)
            PVPwinPointE = ttk.Spinbox(pvpFrame,from_=0,to=999999,width=8)
            PVPwinPointE.grid(row=3,column=1,columnspan=1,sticky='we',**cfg)
            tk.Label(pvpFrame,text='胜点').grid(row=3,column=2,columnspan=1,sticky='we',**cfg)
            ttk.Button(pvpFrame,text='提交',command=set_PVP).grid(row=4,column=1,columnspan=2,sticky='we',**cfg)

        otherFrame = ttk.LabelFrame(usualFrame,text='其他功能')
        otherFrame.grid(row=2,column=1,columnspan=2,**cfgFrame)
        if True:
            cfg = {'padx':4,'pady':4,'sticky':'we'}
            ttk.Button(otherFrame,text='解除账号限制',command=lambda:[sqlM.unlock_register_limit(self.uid),self.title('解除成功')]).grid(row=2,column=1,**cfg)
            ttk.Button(otherFrame,text='开启左右槽',command=lambda:[sqlM.enable_LR_slot(self.cNo),self.title('开启成功')]).grid(row=2,column=2,**cfg)
            ttk.Button(otherFrame,text='开启全图全难度',command=lambda:[sqlM.unlock_all_lev_dungeon(self.uid),self.title('开启成功')]).grid(row=2,column=3,**cfg)
            ttk.Button(otherFrame,text='取消装备等级限制',command=lambda:[sqlM.unlock_ALL_Level_equip(self.cNo),self.title('解除成功')]).grid(row=3,column=1,**cfg)
            ttk.Button(otherFrame,text='清空邮件',command=lambda:[sqlM.delete_all_mail(self.cNo),self.title('清除成功')]).grid(row=3,column=2,**cfg)
            ttk.Button(otherFrame,text='设置副职业满级',command=lambda:[sqlM.maxmize_expert_lev(self.cNo),self.title('设置成功')]).grid(row=3,column=3,**cfg)

    def buildTab_mail(self,tabView:ttk.Notebook,tabName:str):
        def searchItem(e):
            if e.x<100:return
            key = itemNameEntry.get()
            if len(key)>0:
                res = cacheM.searchItem(key)
                itemNameEntry.config(values=[str([item[0]])+' '+item[1] for item in res])
        def readSlotName(name_id):
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
            itemID = int(id_)
            typeid,itemType = cacheM.getStackableTypeMainIdAndZh(itemID)
            
            #print(int(id_),name,typeid,itemType)
            typeZh = sqlM.DnfItemSlot.typeDict.get(typeid)
            if typeid==0:
                typeZh = '未知分类'
            
            fileInDict = cacheM.get_Item_Info_In_Dict(itemID)
            if 'avatar' in str(fileInDict.keys()):
                    typeid = 7
                    typeZh = '时装'
            typeEntry.set(str(typeid)+'-'+typeZh)

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
            if typeZh in ['装备','宠物']:
                numGradeLabel.config(text='品级：')
                for widget in itemEditFrame.children.values():
                    try:
                        widget.config(state='normal')
                    except:
                        pass
                '''if durabilityEntry.get()=='':
                    durabilityEntry.insert(0,10)'''
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
                if numEntry.get()=='':
                    numEntry.insert(0,1)
            typeEntry.config(state='readonly')
            goldE.config(state='normal')
            goldLabel.config(state='normal')

        def get_Item_info()->list:
            id = itemIDEntry.get()
            seal = itemSealVar.get()
            num = numEntry.get()
            durability = 0#durabilityEntry.get()
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

            res = []
            for value in [id,seal,num,durability,IncreaseType,IncreaseValue,enhanceValue,forgeLevel,creature_flag,avatar_flag]:
                try:
                    res.append(int(value))
                except:
                    res.append(0)
            return res

        def send_mail(cNo):
            gold = goldE.get()
            sender = senderE.get()
            message = messageE.get()
            letterID = sqlM.send_message(cNo,sender,message)
            itemID,seal,num,durability,IncreaseType,IncreaseValue,enhanceValue,forgeLevel,creature_flag,avatar_flag = get_Item_info()
            if id==0:
                return True
            sqlM.send_postal(cNo,letterID,sender,itemID,IncreaseType,IncreaseValue,
                             forgeLevel,seal,num,enhanceValue,gold,avatar_flag,creature_flag)
            self.title(f'发送完成-{cNo}')

        def send_mail_all():
            characs = sqlM.get_all_charac()
            print(characs)
            i=1
            for cNo,*_ in characs:
                send_mail(cNo)
                self.title(f'当前发送({i}/{len(characs)})')
                i+=1
            self.title(f'发送完成({len(characs)})!')
        
        def send_mail_VIP(all=False):
            if all==False:
                characs = sqlM.get_VIP_charac()
            else:
                characs = sqlM.get_VIP_charac(True)
            print(characs)
            i=1
            for cNo,*_ in characs:
                send_mail(cNo)
                self.title(f'当前发送({i}/{len(characs)})')
                i+=1
            self.title(f'发送完成({len(characs)})!')

        def send_mail_online():
            onlineCharacList = sqlM.get_online_charac()
            print(onlineCharacList)
            
            i=1
            for cNo,*_ in onlineCharacList:
                send_mail(cNo)
                self.title(f'当前发送({i}/{len(onlineCharacList)})')
                i+=1
            self.title(f'发送完成({len(onlineCharacList)})!')
        mailFrame = tk.Frame(tabView)
        tabView.add(mailFrame,text=tabName)
        itemFrame = ttk.LabelFrame(mailFrame,text='物品信息')
        itemFrame.pack(fill='x',padx=3,pady=3)
        if True:
            itemEditFrame = tk.Frame(itemFrame)
            itemEditFrame.pack()
            cfg = {'padx':3,'pady':2,'sticky':'nswe'}
            # 2
            row = 2
            itemSealVar = tk.IntVar()
            itemSealVar.set(0)
            itemSealBtn = ttk.Checkbutton(itemEditFrame,text='封装',variable=itemSealVar,command=lambda:itemSealVar.get())
            itemSealBtn.grid(column=1,row=row,**cfg)
            CreateToolTip(itemSealBtn,'无法封装的物品勾选会炸角色')
            itemNameEntry = ttk.Combobox(itemEditFrame,width=18,state='normal')
            itemNameEntry.bind('<Button-1>',searchItem)
            itemNameEntry.grid(column=2,row=row,**cfg)
            itemNameEntry.bind("<<ComboboxSelected>>",lambda e:readSlotName('name'))
            CreateToolTip(itemNameEntry,textFunc=getItemPVFInfo)
            itemIDEntry = ttk.Entry(itemEditFrame,width=10)
            itemIDEntry.grid(column=3,row=row,**cfg)
            itemIDEntry.bind('<FocusOut>',lambda e:readSlotName('id'))
            itemIDEntry.bind('<Return>',lambda e:readSlotName('id'))
            # 3
            row = 3
            numGradeLabel = tk.Label(itemEditFrame,text='数量：')
            numGradeLabel.grid(column=1,row=row,**cfg)
            numEntry = ttk.Spinbox(itemEditFrame,width=15,from_=0, to=4294967295)
            numEntry.grid(column=2,row=row,**cfg)
            CreateToolTip(numEntry,'当为装备时，表示为品级\n数值与品级关系较为随机\n(0~4,294,967,295)')
            '''tk.Label(itemEditFrame,text=' 耐久：').grid(column=3,row=row,padx=cfg['padx'],sticky='w')
            durabilityEntry = ttk.Spinbox(itemEditFrame,width=4,from_=0, to=999)
            durabilityEntry.grid(column=3,row=row,padx=cfg['padx'],sticky='e')'''
            # 4
            row = 4
            tk.Label(itemEditFrame,text='增幅：').grid(column=1,row=row,**cfg)
            IncreaseTypeEntry = ttk.Combobox(itemEditFrame,width=14,state='readonly',values=['空-0','异次元体力-1','异次元精神-2','异次元力量-3','异次元智力-4'])
            IncreaseTypeEntry.grid(column=2,row=row,**cfg)
            IncreaseEntry = ttk.Spinbox(itemEditFrame,width=10,from_=0, to=65535)
            IncreaseEntry.grid(column=3,row=row,**cfg)
            
            # 5
            row = 5
            tk.Label(itemEditFrame,text='强化：').grid(column=1,row=row,**cfg)
            EnhanceEntry = ttk.Spinbox(itemEditFrame,width=15,increment=1,from_=0, to=31)
            EnhanceEntry.grid(column=2,row=row,**cfg)
            #tk.Label(itemEditFrame,text='种        类:').grid(column=3,row=row,columnspan=2,**cfg)
            typeEntry = ttk.Combobox(itemEditFrame,width=4,state='readonly',values=['1-装备','2-消耗品','3-材料','4-任务材料','5-宠物','6-宠物装备','7-宠物消耗品','8-时装','10-副职业'])
            typeEntry.grid(column=3,row=row,**cfg)
            typeEntry.bind("<<ComboboxSelected>>",lambda e:changeItemSlotType())
            # 6
            row = 6
            tk.Label(itemEditFrame,text='锻造：').grid(column=1,row=row,**cfg)
            forgingEntry = ttk.Spinbox(itemEditFrame,width=15,increment=1,from_=0, to=31)
            forgingEntry.grid(column=2,row=row,**cfg)
            goldLabel = tk.Label(itemEditFrame,text='金币:')
            goldLabel.grid(column=3,row=row,columnspan=1,padx=cfg['padx'],sticky='w')
            goldE = ttk.Entry(itemEditFrame,width=7)
            goldE.grid(column=3,row=row,padx=cfg['padx'],sticky='e')
            goldE.insert(0,'0')
            
            
        messageFrame = tk.Frame(mailFrame)
        messageFrame.pack()
        #tk.Label(messageFrame,text='发件人').grid(row=2,column=2)
        senderE = ttk.Entry(messageFrame,width=8)
        senderE.insert(0,'背包编辑工具')
        senderE.grid(row=2,column=3)
        CreateToolTip(senderE,textFunc=lambda:'发件人：'+senderE.get())
        messageE = ttk.Entry(messageFrame,width=35)
        messageE.grid(row=2,column=4,**cfg)
        messageE.insert(0,'欢迎使用GM功能，有运行错误请提交issue至GitHub')
        CreateToolTip(messageE,textFunc=lambda:'邮件文本：'+messageE.get())
        btnFrame = tk.Frame(mailFrame)
        btnFrame.pack()
        if True:
            
            ttk.Button(btnFrame,text='发送到当前角色',command=lambda:[send_mail(self.cNo),self.title('发送成功！')]).grid(row=2,column=1,**cfg)
            ttk.Button(btnFrame,text='发送到全服角色',command=send_mail_all).grid(row=2,column=2,**cfg)
            ttk.Button(btnFrame,text='发送到在线角色',command=send_mail_online).grid(row=2,column=3,**cfg)
            ttk.Button(btnFrame,text='发送到VIP账号',command=send_mail_VIP).grid(row=3,column=1,**cfg)
            ttk.Button(btnFrame,text='发送到VIP角色',command=lambda:send_mail_VIP(all)).grid(row=3,column=2,**cfg)
            ttk.Button(btnFrame,text='删除全服邮件',command=lambda:sqlM.delete_all_mail(-1)).grid(row=3,column=3,rowspan=1,**cfg)
        #configFrame(mailFrame)
    def buildTab_event(self,tabView:ttk.Notebook,tabName:str):
        def get_available_event():
            eventList = sqlM.get_event_available()
            self.eventList = [[item[0],item[1],convert(item[2],'zh-cn')] for item in eventList]
            eventList_new = [f'{item[0]}-{item[2]}' for item in self.eventList]
            print(eventList)
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
            print(eventList,runningList)
            for child in eventTreeNow.get_children():
                eventTreeNow.delete(child)
            for item in runningList:
                eventTreeNow.insert('',tk.END,values=item)
            return runningList
        
        self.updateFuncList.append(get_available_event)
        self.updateFuncList.append(get_running_event)
        eventFrame = tk.Frame(tabView)
        tabView.add(eventFrame,text=tabName)
        treeViewFrame = tk.Frame(eventFrame)
        treeViewFrame.pack()
        if True:
            eventTreeNow = ttk.Treeview(treeViewFrame,height=7)
            eventTreeNow.pack(fill='x',side=tk.LEFT)
            if True:
                eventTreeNow["columns"] = ("1", "2", "3",'4')#,'5'
                eventTreeNow['show'] = 'headings'
                eventTreeNow.column("1", width = 60, anchor ='c')
                eventTreeNow.column("2", width = 160, anchor ='c')
                eventTreeNow.column("3", width = 40, anchor ='c')
                eventTreeNow.column("4", width = 40, anchor ='c')
                #eventTreeNow.column("5", width = 80, anchor ='se')

                eventTreeNow.heading("1", text ="活动id")
                eventTreeNow.heading("2", text ="活动描述")
                eventTreeNow.heading("3", text ="参数1")
                eventTreeNow.heading("4", text ="参数2")
                #eventTreeNow.heading("5", text ="结束时间")
                #eventTreeNow.bind('<ButtonRelease-1>',selectCharac)
                eventTreeNow.tag_configure('deleted', background='gray')
            sbar1= tk.Scrollbar(treeViewFrame,bg='gray')
            sbar1.pack(side=tk.RIGHT, fill=tk.Y)
            sbar1.config(command =eventTreeNow.yview)
            eventTreeNow.config(yscrollcommand=sbar1.set,xscrollcommand=sbar1.set)
        def del_event():
            try:
                sel = eventTreeNow.item(eventTreeNow.focus())
                print(sel['values'])
                id = int(sel['values'][0])
            except:
                self.title('未选中活动')
                return False
            sqlM.del_event(id)
            self.update_Info()
            self.title(f'活动已删除，请重启服务器')
        
        def set_event():
            try:
                id = int(eventNameE.get().split('-')[0])
                para1 = eventArg1E.get()
                para2 = eventArg2E.get()
                if para1=='':
                    para1 = 1
                if para2=='':
                    para2 = 0
                sqlM.set_event(id,para1,para2)
            except:
                self.title('活动添加失败')
                return False
            self.title(f'活动已添加，请重启服务器')
            self.update_Info()
        
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

        ttk.Separator(eventFrame, orient='horizontal').pack(fill='x')
        eventEditFrame = tk.Frame(eventFrame)
        eventEditFrame.pack(fill='x',side=tk.TOP)
        if True:
            cfg = {'padx':1,'pady':3, 'sticky':'nswe'}
            tk.Label(eventEditFrame,text='活动名称',fg='blue').grid(row=1,column=2)
            tk.Label(eventEditFrame,text='活动参数1',fg='blue').grid(row=1,column=3)
            tk.Label(eventEditFrame,text='活动参数2',fg='blue').grid(row=1,column=4)
            eventNameE = ttk.Combobox(eventEditFrame,width=23,state='readonly')
            eventNameE.grid(row=2,column=2,**cfg)
            eventNameE.bind('<<ComboboxSelected>>',select_new_event)
            CreateToolTip(eventNameE,textFunc=eventNameE.get)
            eventArg1E = ttk.Entry(eventEditFrame,width=7)
            eventArg1E.grid(row=2,column=3,**cfg)
            eventArg2E = ttk.Entry(eventEditFrame,width=7)
            eventArg2E.grid(row=2,column=4,**cfg)
            ttk.Button(eventEditFrame,text='刷新服务器活动',command=lambda:self.title(f'活动已刷新({len(get_running_event())})')).grid(row=3,column=2,**cfg)
            ttk.Button(eventEditFrame,text='删除选中',width=8,command=del_event).grid(row=3,column=3,**cfg)
            addBtn = ttk.Button(eventEditFrame,text='添加活动',width=8,command=set_event)
            addBtn.grid(row=3,column=4,**cfg)
            CreateToolTip(addBtn,'添加删除后需重启服务器')

    def buildTab_server(self,tabView:ttk.Notebook,tabName:str):
        def connect(show=True):
            def inner():
                ip = db_ip.get()
                port = int(db_port.get())
                user = db_user.get()
                pwd = db_pwd.get()
                try:
                    ssh.connect(ip, username=user, port=port, password=pwd,timeout=3)
                except Exception as e:
                    if show:
                        self.title(f'连接失败 {e}')
                    return False
                cacheM.config['SERVER_IP'] = ip
                cacheM.config['SERVER_PORT'] = port
                cacheM.config['SERVER_USER'] = user
                cacheM.config['SERVER_PWD'] = pwd
                cacheM.save_config()
                configFrame(serverFuncFrame,'normal')
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls /root")
                files = [item.strip() for item in ssh_stdout.readlines()]
                for fileSelE in fileSelEList:
                    fileSelE.config(values=files)
                print(files)
            t = threading.Thread(target = inner)
            t.setDaemon(True)
            t.start()        
        def run_server():
            def inner():
                nonlocal startingFlg
                if startingFlg:
                    self.title('服务器正在启动中！请点击停止服务器')
                    return False
                startingFlg = True
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("sh /root/run")
                self.title('DNF服务器启动中...')
                while True:
                    res = ssh_stdout.readline()
                    print(res)
                    if res == '':
                        break
                    if 'Connect To Guild Server' in str(res):
                        self.title('服务器启动完成')
                        break
                    if 'success' in str(res).lower() or 'error' in str(res).lower():
                        self.title(str(res).strip())
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
            run_file('run1')
        
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
        
        def run_cmd(cmd='ls'):
            def inner():
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
                while True:
                    res = ssh_stdout.readline()
                    if res == '':
                        break
                    time.sleep(0.05)
                    self.title(res)
                self.title(f'指令执行完毕')

            t = threading.Thread(target=inner)
            t.setDaemon(True)
            t.start()
        
        def load_diy():
            diyList = cacheM.config['DIY']
            for i,diy in enumerate(diyList):
                fileSelEList[i].set(diy)
            diyList = cacheM.config['DIY_2']
            for i,diy in enumerate(diyList):
                cmdEList[i].insert(0,diy)
        def save_diy():
            diyList = []
            for selE in fileSelEList:
                diyList.append(selE.get())
            cacheM.config['DIY'] = diyList
            diyList = []
            for selE in cmdEList:
                diyList.append(selE.get())
            cacheM.config['DIY_2'] = diyList
            cacheM.save_config()
        

        import paramiko
        import threading
        import time
        ssh = paramiko.SSHClient()
        # 允许连接不在know_hosts文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        startingFlg = False
        serverFrame = tk.Frame(tabView)
        tabView.add(serverFrame,text=tabName)
        serverConFrame = tk.Frame(serverFrame)
        serverConFrame.pack()
        from cacheManager import config
        if True:
            tk.Label(serverConFrame,text='IP').grid(row=0,column=1,sticky='we')
            db_ip = ttk.Entry(serverConFrame,width=13)
            db_ip.grid(row=0,column=2,pady=5,sticky='we')
            db_ip.insert(0,config['SERVER_IP'])
            tk.Label(serverConFrame,text='端口').grid(row=0,column=3,sticky='we')
            db_port = ttk.Entry(serverConFrame,width=2)
            db_port.insert(0,config['SERVER_PORT'])
            db_port.grid(row=0,column=4,sticky='we')
            tk.Label(serverConFrame,text='用户名').grid(row=1,column=1,sticky='we')
            db_user = ttk.Entry(serverConFrame,width=4)
            db_user.insert(0,config['SERVER_USER'])
            db_user.grid(row=1,column=2,sticky='we')
            tk.Label(serverConFrame,text='密码').grid(row=1,column=3,sticky='we')
            db_pwd = ttk.Entry(serverConFrame,width=7)#,show='*'
            db_pwd.insert(0,config['SERVER_PWD'])
            db_pwd.grid(row=1,column=4,sticky='we')
            db_conBTN = ttk.Button(serverConFrame,text='连接',command=connect)
            db_conBTN.grid(row=0,column=5,rowspan=2,pady=5,padx=5,sticky='nswe')
        
        #ttk.Separator(serverFrame, orient='horizontal').pack(fill='x')
        serverFuncFrame = tk.Frame(serverFrame)
        serverFuncFrame.pack()
        if True:
            cfg = {'padx':1,'pady':3, 'sticky':'nswe'}
            normalFuncFrame = tk.Frame(serverFuncFrame)
            normalFuncFrame.pack()
            ttk.Button(normalFuncFrame,text='启动服务器',command=run_server,width=14).grid(row=3,column=2,**cfg)
            ttk.Button(normalFuncFrame,text='停止服务器',command=stop_server,width=14).grid(row=3,column=3,**cfg)
            ttk.Button(normalFuncFrame,text='重启频道',command=restart_channel,width=14).grid(row=3,column=4,**cfg)

            diyFuncFrame = ttk.LabelFrame(serverFuncFrame,text='自定义功能')
            diyFuncFrame.pack()
            fileSelEList= []
            cmdEList = []
            def diy_func_frame(master,row):
                fileSelE1 = ttk.Combobox(master,width=11)
                fileSelE1.grid(row=row,column=1,**cfg)
                CreateToolTip(fileSelE1,textFunc=lambda:'执行脚本：'+fileSelE1.get())
                ttk.Button(master,text='执行',command=lambda:run_file(fileSelE1.get()),width=7).grid(row=row,column=2,**cfg)
                fileSelE2 = ttk.Combobox(master,width=11)
                fileSelE2.grid(row=row,column=3,**cfg)
                CreateToolTip(fileSelE2,textFunc=lambda:'执行脚本：'+fileSelE2.get())
                ttk.Button(master,text='执行',command=lambda:run_file(fileSelE2.get()),width=7).grid(row=row,column=4,**cfg)
                fileSelEList.extend([fileSelE1,fileSelE2])
                fileSelE1.bind('<<ComboboxSelected>>',lambda e:save_diy())
                fileSelE2.bind('<<ComboboxSelected>>',lambda e:save_diy())
            def diy_func_frame2(master,row):
                cmdE = ttk.Entry(master,width=11)
                cmdE.grid(row=row,column=1,columnspan=3,**cfg)
                ttk.Button(master,text='执行',command=lambda:run_cmd(cmdE.get()),width=7).grid(row=row,column=4,**cfg)
                cmdEList.append(cmdE)
                cmdE.bind('<<FocusOut>>',lambda e:save_diy())
                CreateToolTip(cmdE,textFunc=lambda:'shell指令：'+cmdE.get())
            for i in range(2):
                diy_func_frame(diyFuncFrame,i)

            for i in range(2,4):
                diy_func_frame2(diyFuncFrame,i)

                



        load_diy()
        configFrame(serverFuncFrame,'disable')
        connect(False)
        



            
if __name__=='__main__':
    t = tk.Tk()
    t.geometry('0x0')
    t.overrideredirect(True)
    sqlM.connect()
    gm = GMToolWindow(t,cNo=2)
    gm.protocol('WM_DELETE_WINDOW',t.destroy)
    t.mainloop()





    