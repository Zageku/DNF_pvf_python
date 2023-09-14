from dnfpkgtool import sqlManager2 as sqlM
from dnfpkgtool import cacheManager as cacheM
import tkinter as tk
from tkinter import ttk
from dnfpkgtool.widgets.toolTip import CreateToolTip
from zhconv import convert
import dnfpkgtool.serverProtocol as server
from dnfpkgtool.widgets.imageLabel import ImageLabel
IconPath = './config/ico.ico'
if not hasattr(ttk,'Spinbox'):
    class Spinbox(ttk.Entry):
        def __init__(self, master=None, **kw):  #from_=0,to=99,
            ttk.Entry.__init__(self, master, "ttk::spinbox", **kw)
        def set(self, value):
            self.tk.call(self._w, "set", value)
    ttk.Spinbox = Spinbox

oldPrint = print
logFunc = [oldPrint]
def print(*args,**kw):
    logFunc[-1](*args,**kw)
    
def configFrame(frame:tk.Frame,state='disable'):
    for widget in frame.children.values():
        if type(widget) in [tk.Frame,tk.LabelFrame,ttk.LabelFrame]:
            configFrame(widget,state)
        else:
            try:
                widget.config(state=state)
            except:
                continue

PVPMap_tmp = [f'{i}级' for i in range(1,11)]
PVPMap_tmp.reverse()
PVPMap_tmp2 = [f'{i}段' for i in range(1,11)]
PVPMap_tmp3 = [f'至尊{i}' for i in range(1,11)]
PVPMap_tmp4 = ['达人','名人','小霸王','霸王','斗神']
PVPRankList = PVPMap_tmp+PVPMap_tmp2+PVPMap_tmp3+PVPMap_tmp4

WIDTH,HEIGHT = cacheM.config['SIZE']

letter_send_dict = {}

class GMToolWindow(tk.Toplevel):
    def __init__(self,master,title='GM工具',cNo=0,sponsorFrame=True,sshAutoConnect=True,*args,**kw):
        self.cNo = cNo
        self.uid = 0
        self.uids = []
        self.cNos = []
        self.get_group_account_characs = lambda:...
        self.get_group_all_characs = lambda:...
        self.get_group_all_uids = lambda:...
        self.delete_mail_group = lambda:...
        self.localEventList = None
        self.sshAutoConnect = sshAutoConnect
        self.blobCommitExFunc = lambda cNo=0:...
        #self.chargeCeraExFunc = lambda cNo=0,uid=0:...
        if sqlM.connectorUsed is not None:
            self.uid = sqlM.cNo_2_uid(self.cNo)
        self.updateFuncList = []
        self.eventList = []
        tk.Toplevel.__init__(self,master=master,*args,**kw)
        self.title(title)
        self.iconbitmap(IconPath)
        self.tab = ttk.Notebook(self)
        self.tab.pack()
        self.tabIDDict = {}
        self.buildTab_usual(self.tab,'常用功能')
        self.buildTab_mail(self.tab,'邮件功能')
        self.mailTabID = self.tab.tabs()[-1]
        self.buildTab_GroupMail(self.tab,'群体功能')
        self.groupTabID = self.tab.tabs()[-1]
        self.buildTab_event(self.tab,'活动管理')
        self.buildTab_server(self.tab,'服务器')
        self.serverTabID = self.tab.tabs()[-1]
        if sponsorFrame:
            self.buildTab_sponsor(self.tab,'联系我们')
        self.update_Info()
        self.resizable(False,False)
    
    def update_Info(self):
        if sqlM.connectorUsed is None:
            return False
        #print(sqlM.connectorUsed)
        if self.cNo!=0:
            self.uid = sqlM.cNo_2_uid(self.cNo)
            self.characChargeFrame.config(text=f'充值-角色{self.cNo}')
            self.mailItemFrame.config(text=f'物品信息-角色{self.cNo}')
        for func in self.updateFuncList:
            func()

    def buildTab_usual(self,tabView:ttk.Notebook,tabName:str):
        def charge(type='cera'):
            update_cera_and_SP()
            type = ceraTypeE.get()
            value = int(ceraValueE.get())
            if type =='点券':
                sqlM.set_cera(self.uid,value+cNoInfoDict['cera'],'cera')
            elif type =='代币':
                sqlM.set_cera(self.uid,value+cNoInfoDict['cera_point'],'cera_point')
            elif type=='SP':
                sqlM.set_skill_sp(self.cNo,value+cNoInfoDict['sp'],value+cNoInfoDict['sp2'],cNoInfoDict['tp'],cNoInfoDict['tp2'])
            elif type=='TP':
                sqlM.set_skill_sp(self.cNo,cNoInfoDict['sp'],cNoInfoDict['sp2'],value+cNoInfoDict['tp'],value+cNoInfoDict['tp2'])
            elif type=='QP':
                sqlM.set_quest_point(self.cNo,value+cNoInfoDict['qp'])
            self.update_Info()
            self.title('充值成功！')
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
            self.update_Info()
            self.title('清除成功！')
            self.blobCommitExFunc(self.cNo)
        def update_cera_and_SP():
            if self.cNo==0:
                configFrame(usualFrame,'disable')
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
            configFrame(usualFrame,'normal')
            for widget in readOnlyWidgets:
                widget.config(state='readonly')
        
        self.updateFuncList.append(update_cera_and_SP)
        cNoInfoDict = {}
        readOnlyWidgets = []
        usualFrame = tk.Frame(tabView)
        tabView.add(usualFrame,text=tabName)
        usualFrame = tk.Frame(usualFrame)
        usualFrame.pack()
        cfgFrame = {
            'padx':3,
            'pady':3,
            'sticky':'nswe'
        }
        chargeFrame = ttk.LabelFrame(usualFrame,text='充值')
        self.characChargeFrame = chargeFrame
        chargeFrame.grid(row=1,column=1,**cfgFrame)
        chargeFrame = tk.Frame(chargeFrame)
        chargeFrame.pack()
        if True:
            cfg = {'padx':3,'pady':3}
            ceraSVar = tk.StringVar()
            ceraSVar.set('000000')
            ceraPointSVar = tk.StringVar()
            ceraPointSVar.set('000000')
            spVar = tk.StringVar()
            spVar.set('000000')
            qpTpVar = tk.StringVar()
            qpTpVar.set('00/00')
            tk.Label(chargeFrame,text='点券').grid(row=0,column=0,sticky='we',**cfg)
            tk.Label(chargeFrame,text='代币').grid(row=1,column=0,sticky='we',**cfg)
            tk.Label(chargeFrame,text='SP').grid(row=2,column=0,sticky='we',**cfg)
            tk.Label(chargeFrame,text='QP/TP').grid(row=3,column=0,sticky='we',**cfg)
            #tk.Label(chargeFrame,text='',width=int(WIDTH*14)).grid(row=0,column=1,sticky='w',**cfg)
            width = 8
            
            readOnlyWidgets.append(ttk.Entry(chargeFrame,textvariable=ceraSVar,state='readonly',width=int(WIDTH*width)))
            readOnlyWidgets[-1].grid(row=0,column=1,sticky='we',**cfg)
            readOnlyWidgets.append(ttk.Entry(chargeFrame,textvariable=ceraPointSVar,state='readonly',width=int(WIDTH*width)))
            readOnlyWidgets[-1].grid(row=1,column=1,sticky='we',**cfg)
            readOnlyWidgets.append(ttk.Entry(chargeFrame,textvariable=spVar,state='readonly',width=int(WIDTH*width)))
            readOnlyWidgets[-1].grid(row=2,column=1,sticky='we',**cfg)
            readOnlyWidgets.append(ttk.Entry(chargeFrame,textvariable=qpTpVar,state='readonly',width=int(WIDTH*width)))
            readOnlyWidgets[-1].grid(row=3,column=1,sticky='we',**cfg)

            ceraValueE = ttk.Spinbox(chargeFrame,from_=0,to=999999,width=int(WIDTH*7))
            ceraValueE.grid(row=0,column=2,columnspan=1,sticky='we',**cfg)
            ceraValueE.set(0)
            ceraTypeE = ttk.Combobox(chargeFrame,width=int(WIDTH*5),values=['点券','代币','SP','TP','QP'],state='readonly')
            ceraTypeE.set('点券')
            readOnlyWidgets.append(ceraTypeE)
            ceraTypeE.grid(row=1,column=2,columnspan=1,sticky='we',**cfg)
            #ttk.Button(chargeFrame,text='充值代币',command=lambda:charge('cera_point')).grid(row=2,column=1,**cfg)
            ttk.Button(chargeFrame,text='充值',command=charge,width=int(WIDTH*9)).grid(row=2,column=2,sticky='we',**cfg)
            #ttk.Button(chargeFrame,text='清空代币',command=lambda:clear_cera('cera_point')).grid(row=3,column=1,**cfg)
            ttk.Button(chargeFrame,text='清空',command=clear_cera,width=int(WIDTH*9)).grid(row=3,column=2,sticky='we',**cfg)
            #chargeFrame.update()
            #chargeFrame.pack_propagate(False)
            #chargeFrame.grid_propagate(False)
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
            pvp_grade = PVPRankList.index(PVPgradeE.get())
            win = int(PVPwinNumE.get())
            pvp_point = int(PVPwinPointE.get())
            win_point = pvp_point
            sqlM.set_PVP(self.cNo,pvp_grade,win,pvp_point,win_point)
            self.update_Info()
            self.title('提交成功！')
        
        
        self.updateFuncList.append(update_PVP)
        pvpFrame = ttk.LabelFrame(usualFrame,text='PVP数据')
        pvpFrame.grid(row=1,column=2,**cfgFrame)
        pvpFrame = ttk.Frame(pvpFrame)
        pvpFrame.pack()
        if True:
            cfg = {'padx':3,'pady':4}
            PVPgradeE = ttk.Combobox(pvpFrame,width=int(WIDTH*7),values=[f'{name}' for i,name in enumerate(PVPRankList)])
            PVPgradeE.grid(row=1,column=1,columnspan=1,sticky='we',**cfg)
            readOnlyWidgets.append(PVPgradeE)
            tk.Label(pvpFrame,text='段位').grid(row=1,column=2,columnspan=1,sticky='we',**cfg)
            PVPwinNumE = ttk.Spinbox(pvpFrame,from_=0,to=999999,width=int(WIDTH*7))
            PVPwinNumE.grid(row=2,column=1,columnspan=1,sticky='we',**cfg)
            tk.Label(pvpFrame,text='胜场').grid(row=2,column=2,columnspan=1,sticky='we',**cfg)
            PVPwinPointE = ttk.Spinbox(pvpFrame,from_=0,to=999999,width=int(WIDTH*7))
            PVPwinPointE.grid(row=3,column=1,columnspan=1,sticky='we',**cfg)
            tk.Label(pvpFrame,text='胜点').grid(row=3,column=2,columnspan=1,sticky='we',**cfg)
            ttk.Button(pvpFrame,text='提交',command=set_PVP).grid(row=4,column=1,columnspan=2,sticky='we',**cfg)

        def unlock_dungeon():
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


        otherFrame = ttk.LabelFrame(usualFrame,text='其他功能')
        otherFrame.grid(row=2,column=1,columnspan=2,**cfgFrame)
        if True:
            cfg = {'padx':3,'pady':4,'sticky':'nswe'}
            padFrame = tk.Frame(otherFrame,height=int(HEIGHT*48+(HEIGHT-1)*48))
            padFrame.grid(row=2,column=0,rowspan=2)
            unlockBtn = ttk.Button(otherFrame,text='解除账号限制',command=lambda:[sqlM.unlock_register_limit(self.uid),self.title('解除成功')])
            unlockBtn.grid(row=2,column=1,**cfg)
            CreateToolTip(unlockBtn,'解除建号限制、限制交易、封号等账号异常状态')
            ttk.Button(otherFrame,text='开启左右槽',command=lambda:[sqlM.enable_LR_slot(self.cNo),self.title('开启成功')],width=int(WIDTH*13)).grid(row=2,column=2,**cfg)
            ttk.Button(otherFrame,text='开启全图全难度',command=lambda:[unlock_dungeon(),self.title('开启成功')]).grid(row=2,column=3,**cfg)
            ttk.Button(otherFrame,text='取消装备等级限制',command=lambda:[sqlM.unlock_ALL_Level_equip(self.cNo),self.title('解除成功')],width=int(WIDTH*14)).grid(row=3,column=1,**cfg)
            ttk.Button(otherFrame,text='重置祭坛次数',command=lambda:[sqlM.reset_blood_dungeon(self.cNo),self.title('重置成功')]).grid(row=3,column=2,**cfg)
            ttk.Button(otherFrame,text='设置副职业满级',command=lambda:[sqlM.maxmize_expert_lev(self.cNo),self.title('设置成功')],width=int(WIDTH*13)).grid(row=3,column=3,**cfg)

    def buildTab_mail(self,tabView:ttk.Notebook,tabName:str):
        def searchItem(e):
            if e.x<100:return
            key = itemNameEntry.get()
            if len(key)>0:
                res = cacheM.searchItem(key)
                itemNameEntry.config(values=[item[1] +' '+ str([item[0]]) for item in res])
        def readSlotName(name_id):
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

        def send_mail(cNo):
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
                return True
            sqlM.send_postal(cNo,letterID,sender,message,itemID,IncreaseType,IncreaseValue,
                             forgeLevel,seal,num,enhanceValue,gold,avatar_flag,creature_flag,endurance)
            print(f'发送完成-{cNo}')
            self.title(f'发送完成-{cNo}')
            self.blobCommitExFunc(cNo)
            letter_send_dict[letterID] = {
                'cNo':cNo, 'itemID':itemID,'gold':gold,'num':num
            }
            

        def send_mail_all():
            characs = sqlM.get_all_charac()
            #print(characs)
            i=1
            for cNo,*_ in characs:
                send_mail(cNo)
                self.title(f'当前发送({i}/{len(characs)}/{characs[i]})')
                i+=1
        
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
        self.mailItemFrame = itemFrame
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
            itemNameEntry = ttk.Combobox(itemEditFrame,width=int(WIDTH*18),state='normal')
            itemNameEntry.bind('<Button-1>',searchItem)
            itemNameEntry.grid(column=2,row=row,**cfg)
            itemNameEntry.bind("<<ComboboxSelected>>",lambda e:readSlotName('name'))
            CreateToolTip(itemNameEntry,textFunc=getItemPVFInfo)
            itemIDEntry = ttk.Entry(itemEditFrame,width=int(WIDTH*10))
            itemIDEntry.grid(column=3,row=row,**cfg)
            itemIDEntry.bind('<FocusOut>',lambda e:readSlotName('id'))
            itemIDEntry.bind('<Return>',lambda e:readSlotName('id'))
            self.mailItemIDEntry = itemIDEntry
            self.setMailItemIDFun = lambda :readSlotName('id')
            # 3
            row = 3
            numGradeLabel = tk.Label(itemEditFrame,text='数量：')
            numGradeLabel.grid(column=1,row=row,**cfg)
            numEntry = ttk.Spinbox(itemEditFrame,width=int(WIDTH*15),from_=0, to=4294967295)
            numEntry.grid(column=2,row=row,**cfg)
            CreateToolTip(numEntry,'当为装备时，表示为品级\n数值与品级关系较为随机\n(0~4,294,967,295)')
            tk.Label(itemEditFrame,text=' 耐久：').grid(column=3,row=row,padx=cfg['padx'],sticky='w')
            enduranceEntry = ttk.Spinbox(itemEditFrame,width=int(WIDTH*4),from_=0, to=999)
            enduranceEntry.grid(column=3,row=row,padx=cfg['padx'],sticky='e')
            # 4
            row = 4
            tk.Label(itemEditFrame,text='增幅：').grid(column=1,row=row,**cfg)
            IncreaseTypeEntry = ttk.Combobox(itemEditFrame,width=int(WIDTH*14),state='readonly',values=['空-0','异次元体力-1','异次元精神-2','异次元力量-3','异次元智力-4'])
            IncreaseTypeEntry.grid(column=2,row=row,**cfg)
            IncreaseEntry = ttk.Spinbox(itemEditFrame,width=int(WIDTH*10),from_=0, to=65535)
            IncreaseEntry.grid(column=3,row=row,**cfg)
            
            # 5
            row = 5
            tk.Label(itemEditFrame,text='强化：').grid(column=1,row=row,**cfg)
            EnhanceEntry = ttk.Spinbox(itemEditFrame,width=int(WIDTH*15),increment=1,from_=0, to=31)
            EnhanceEntry.grid(column=2,row=row,**cfg)
            #tk.Label(itemEditFrame,text='种        类:').grid(column=3,row=row,columnspan=2,**cfg)
            typeEntry = ttk.Combobox(itemEditFrame,width=int(WIDTH*4),state='readonly',values=['1-装备','2-消耗品','3-材料','4-任务材料','5-宠物','6-宠物装备','7-宠物消耗品','8-时装','10-副职业'])
            typeEntry.grid(column=3,row=row,**cfg)
            typeEntry.bind("<<ComboboxSelected>>",lambda e:changeItemSlotType())
            # 6
            row = 6
            tk.Label(itemEditFrame,text='锻造：').grid(column=1,row=row,**cfg)
            forgingEntry = ttk.Spinbox(itemEditFrame,width=int(WIDTH*15),increment=1,from_=0, to=31)
            forgingEntry.grid(column=2,row=row,**cfg)
            goldLabel = tk.Label(itemEditFrame,text='金币:')
            goldLabel.grid(column=3,row=row,columnspan=1,padx=cfg['padx'],sticky='w')
            goldE = ttk.Entry(itemEditFrame,width=int(WIDTH*7))
            goldE.grid(column=3,row=row,padx=cfg['padx'],sticky='e')
            goldE.insert(0,'0')
            
            
        messageFrame = tk.Frame(mailFrame)
        messageFrame.pack()
        #tk.Label(messageFrame,text='发件人').grid(row=2,column=2)
        senderE = ttk.Combobox(messageFrame,width=int(WIDTH*8))
        senders = cacheM.config.get('SENDERS',['背包编辑工具'])
        senderE.config(values=senders)
        senderE.set(senders[0])
        senderE.grid(row=2,column=3)
        CreateToolTip(senderE,textFunc=lambda:'发件人：'+senderE.get())
        messageE = ttk.Combobox(messageFrame,width=int(WIDTH*35))
        messageE.grid(row=2,column=4,**cfg)
        messages = cacheM.config.get('MESSAGES',['欢迎使用GM功能，有运行错误请提交issue至GitHub'])
        messageE.config(values=messages)
        messageE.set(messages[0])
        #messageE.insert(0,'欢迎使用GM功能，有运行错误请提交issue至GitHub')
        CreateToolTip(messageE,textFunc=lambda:'邮件文本：'+messageE.get())
        btnFrame = tk.Frame(mailFrame)
        btnFrame.pack()
        if True:
            padFrame = tk.Frame(btnFrame,height=int(HEIGHT*48+(HEIGHT-1)*48))
            padFrame.grid(row=2,column=0,rowspan=2)
            ttk.Button(btnFrame,text='发送到当前角色',command=lambda:send_mail(self.cNo),width=int(WIDTH*13)).grid(row=2,column=1,**cfg)
            ttk.Button(btnFrame,text='发送到全服角色',command=send_mail_all,width=int(WIDTH*13)).grid(row=2,column=2,**cfg)
            ttk.Button(btnFrame,text='发送到在线角色',command=send_mail_online,width=int(WIDTH*13)).grid(row=2,column=3,**cfg)
            ttk.Button(btnFrame,text='发送到VIP账号',command=send_mail_VIP).grid(row=3,column=1,**cfg)
            ttk.Button(btnFrame,text='发送到VIP角色',command=lambda:send_mail_VIP(all)).grid(row=3,column=2,**cfg)
            ttk.Button(btnFrame,text='删除全服邮件',command=lambda:sqlM.delete_all_mail_cNo(-1)).grid(row=3,column=3,rowspan=1,**cfg)
        #configFrame(mailFrame)
    
    
    def buildTab_GroupMail(self,tabView:ttk.Notebook,tabName:str):
        from tkinter import messagebox
        def searchItem(e):
            if e.x<100:return
            key = itemNameEntry.get()
            if len(key)>0:
                res = cacheM.searchItem(key)
                itemNameEntry.config(values=[item[1] +' '+ str([item[0]]) for item in res])
        def readSlotName(name_id):
            if name_id=='id':
                id_ = itemIDEntry.get()
                try:
                    id_ = int(id_)
                except:
                    id_ = 0
                name = str(cacheM.ITEMS_dict.get(int(id_)))
            else:
                name,id_ = itemNameEntry.get().split(' ',1)
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

        def send_mail(cNo):
            gold = goldE.get()
            sender = senderE.get()
            message = messageE.get()
            letterID = sqlM.send_message(cNo,sender,message)
            itemID,seal,num,endurance,IncreaseType,IncreaseValue,enhanceValue,forgeLevel,creature_flag,avatar_flag = get_Item_info()
            sqlM.send_postal(cNo,letterID,sender,message,itemID,IncreaseType,IncreaseValue,
                             forgeLevel,seal,num,enhanceValue,gold,avatar_flag,creature_flag,endurance)
            print(f'发送完成-{cNo}-{itemID}-{gold}')
            
            letter_send_dict[letterID] = {
                'cNo':cNo, 'itemID':itemID,'gold':gold,'num':num
            }

        def send_mail_group_a():
            if not messagebox.askokcancel('发送确认',f'确定发送到所有账号？\n将发送到当前分组每个账号最高等级角色的邮箱'):
                return False
            self.focus_force()
            characs = self.get_group_account_characs()
            print(f'发送目标角色ID：{characs}')
            i=1
            for cNo in characs:
                send_mail(cNo)
                self.title(f'当前发送({i}/{len(characs)}-{characs[i-1]})')
                i+=1
            self.title(f'发送完成({len(characs)})!')
            self.blobCommitExFunc(characs)
            messages = cacheM.config.get('MESSAGES',['欢迎使用GM功能，有运行错误请提交issue至GitHub'])
            messageE.config(values=messages)
            senders = cacheM.config.get('SENDERS',['背包编辑工具'])
            senderE.config(values=senders)
            

        
        def send_mail_group_c():
            if not messagebox.askokcancel('发送确认',f'确定发送到分组所有角色？\n将发送到当前分组每个角色的邮箱'):
                return False
            self.focus_force()
            characs = self.get_group_all_characs()
            print(f'发送目标角色ID：{characs}')
            i=1
            for cNo in characs:
                send_mail(cNo)
                self.title(f'当前发送({i}/{len(characs)}-{characs[i-1]})')
                i+=1
            self.title(f'发送完成({len(characs)})!')
            self.blobCommitExFunc(characs)
            messages = cacheM.config.get('MESSAGES',['欢迎使用GM功能，有运行错误请提交issue至GitHub'])
            messageE.config(values=messages)
            senders = cacheM.config.get('SENDERS',['背包编辑工具'])
            senderE.config(values=senders)
            
        
        def send_mail_group_online():
            if not messagebox.askokcancel('发送确认',f'确定发送到分组所有在线？\n将发送到当前分组每个在线角色的邮箱'):
                return False
            self.focus_force()
            characs = self.get_group_all_characs()
            onlineCharacList = sqlM.get_online_charac()
            cNos = list(filter(lambda x:x in onlineCharacList,characs))
            f'发送目标角色ID：{cNos}'
            i=1
            for cNo in cNos:
                send_mail(cNo)
                self.title(f'当前发送({i}/{len(cNos)}-{cNos[i-1]})')
                i+=1
            self.title(f'发送完成({len(cNos)})!')
            self.blobCommitExFunc(cNos)
            messages = cacheM.config.get('MESSAGES',['欢迎使用GM功能，有运行错误请提交issue至GitHub'])
            messageE.config(values=messages)
            senders = cacheM.config.get('SENDERS',['背包编辑工具'])
            senderE.config(values=senders)
        
        def get_cera_and_SP(uid):
            cera, cera_point = sqlM.get_cera(uid)
            cNoInfoDict = {}
            cNoInfoDict['cera'] = cera
            cNoInfoDict['cera_point'] = cera_point

            sp,sp2,tp,tp2 = sqlM.get_skill_sp(self.cNo)
            cNoInfoDict['sp'] = sp
            cNoInfoDict['sp2'] = sp2
            cNoInfoDict['tp'] = tp
            cNoInfoDict['tp2'] = tp2
            qp = sqlM.get_quest_point(self.cNo)
            cNoInfoDict['qp'] = qp
            return cNoInfoDict

        
        def groupCharge():
            if not messagebox.askokcancel('充值确认',f'确定充值？\n将充值到当前分组每个账号'):
                return False
            self.focus_force()
            uids = self.get_group_all_uids()
            for i,uid in enumerate(uids):
                cNoInfoDict = get_cera_and_SP(uid)
                type = chargeTypeE.get()
                value = int(chargeValueE.get())
                if type =='点券':
                    valueNew = value+cNoInfoDict['cera']
                    sqlM.set_cera(uid,value+cNoInfoDict['cera'],'cera')
                elif type =='代币':
                    valueNew = value+cNoInfoDict['cera_point']
                    sqlM.set_cera(uid,value+cNoInfoDict['cera_point'],'cera_point')
                
                self.title(f'充值{type}-{value} 账号{uid} [{valueNew-value}]->[{valueNew}]]')
            self.update_Info()


        mailFrame = tk.Frame(tabView)
        tabView.add(mailFrame,text=tabName)
        groupMailFrame = ttk.LabelFrame(mailFrame,text='群体邮件')
        groupMailFrame.pack(fill='x',padx=3,pady=3)
        if True:
            itemEditFrame = tk.Frame(groupMailFrame)
            itemEditFrame.pack()
            cfg = {'padx':3,'pady':1,'sticky':'we'}
            # 2
            row = 2
            itemSealVar = tk.IntVar()
            itemSealVar.set(0)
            itemSealBtn = ttk.Checkbutton(itemEditFrame,text='封装',variable=itemSealVar,command=lambda:itemSealVar.get())
            itemSealBtn.grid(column=1,row=row,**cfg)
            CreateToolTip(itemSealBtn,'无法封装的物品勾选会炸角色')
            itemNameEntry = ttk.Combobox(itemEditFrame,width=int(WIDTH*18),state='normal')
            itemNameEntry.bind('<Button-1>',searchItem)
            itemNameEntry.grid(column=2,row=row,**cfg)
            itemNameEntry.bind("<<ComboboxSelected>>",lambda e:readSlotName('name'))
            CreateToolTip(itemNameEntry,textFunc=getItemPVFInfo)
            itemIDEntry = ttk.Entry(itemEditFrame,width=int(WIDTH*14))
            itemIDEntry.grid(column=3,row=row,**cfg)
            itemIDEntry.bind('<FocusOut>',lambda e:readSlotName('id'))
            itemIDEntry.bind('<Return>',lambda e:readSlotName('id'))
            # 3
            row = 3
            numGradeLabel = tk.Label(itemEditFrame,text='数量：')
            numGradeLabel.grid(column=1,row=row,**cfg)
            numEntry = ttk.Spinbox(itemEditFrame,width=int(WIDTH*15),from_=0, to=4294967295)
            numEntry.grid(column=2,row=row,**cfg)
            CreateToolTip(numEntry,'当为装备时，表示为品级\n数值与品级关系较为随机\n(0~4,294,967,295)')
            tk.Label(itemEditFrame,text=' 耐久：').grid(column=3,row=row,padx=cfg['padx'],sticky='w')
            enduranceEntry = ttk.Spinbox(itemEditFrame,width=int(WIDTH*4),from_=0, to=999)
            enduranceEntry.grid(column=3,row=row,padx=cfg['padx'],sticky='e')
            # 4
            row = 4
            tk.Label(itemEditFrame,text='增幅：').grid(column=1,row=row,**cfg)
            IncreaseTypeEntry = ttk.Combobox(itemEditFrame,width=int(WIDTH*14),state='readonly',values=['空-0','异次元体力-1','异次元精神-2','异次元力量-3','异次元智力-4'])
            IncreaseTypeEntry.grid(column=2,row=row,**cfg)
            IncreaseEntry = ttk.Spinbox(itemEditFrame,width=int(WIDTH*10),from_=0, to=65535)
            IncreaseEntry.grid(column=3,row=row,**cfg)
            
            # 5
            row = 5
            tk.Label(itemEditFrame,text='强化：').grid(column=1,row=row,**cfg)
            EnhanceEntry = ttk.Spinbox(itemEditFrame,width=int(WIDTH*15),increment=1,from_=0, to=31)
            EnhanceEntry.grid(column=2,row=row,**cfg)
            #tk.Label(itemEditFrame,text='种        类:').grid(column=3,row=row,columnspan=2,**cfg)
            typeEntry = ttk.Combobox(itemEditFrame,width=int(WIDTH*4),state='readonly',values=['1-装备','2-消耗品','3-材料','4-任务材料','5-宠物','6-宠物装备','7-宠物消耗品','8-时装','10-副职业'])
            typeEntry.grid(column=3,row=row,**cfg)
            typeEntry.bind("<<ComboboxSelected>>",lambda e:changeItemSlotType())
            # 6
            row = 6
            tk.Label(itemEditFrame,text='锻造：').grid(column=1,row=row,**cfg)
            forgingEntry = ttk.Spinbox(itemEditFrame,width=int(WIDTH*15),increment=1,from_=0, to=31)
            forgingEntry.grid(column=2,row=row,**cfg)
            goldLabel = tk.Label(itemEditFrame,text='金币:')
            goldLabel.grid(column=3,row=row,columnspan=1,padx=cfg['padx'],sticky='w')
            goldE = ttk.Entry(itemEditFrame,width=int(WIDTH*7))
            goldE.grid(column=3,row=row,padx=cfg['padx'],sticky='e')
            goldE.insert(0,'0')

            row = 7
            
        messageFrame = tk.Frame(groupMailFrame)
        messageFrame.pack()
        #tk.Label(messageFrame,text='发件人').grid(row=2,column=2)
        senderE = ttk.Combobox(messageFrame,width=int(WIDTH*8))
        senders = cacheM.config.get('SENDERS',['背包编辑工具'])
        senderE.config(values=senders)
        senderE.set(senders[0])
        senderE.grid(row=2,column=3)
        CreateToolTip(senderE,textFunc=lambda:'发件人：'+senderE.get())
        messageE = ttk.Combobox(messageFrame,width=int(WIDTH*35))
        messageE.grid(row=2,column=4,**cfg)
        messages = cacheM.config.get('MESSAGES',['欢迎使用GM功能，有运行错误请提交issue至GitHub'])
        messageE.config(values=messages)
        messageE.set(messages[0])
        CreateToolTip(messageE,textFunc=lambda:'邮件文本：'+messageE.get())
        btnFrame = tk.Frame(groupMailFrame)
        btnFrame.pack()
        if True:
            ttk.Button(btnFrame,text='发送到分组账号',command=send_mail_group_a,width=int(WIDTH*13)).grid(row=2,column=1,**cfg)
            ttk.Button(btnFrame,text='发送到分组角色',command=send_mail_group_c,width=int(WIDTH*13)).grid(row=2,column=2,**cfg)
            ttk.Button(btnFrame,text='发送到分组在线',command=send_mail_group_online,width=int(WIDTH*15)).grid(row=2,column=3,rowspan=1,**cfg)
        
        
        groupChargeFrame = ttk.LabelFrame(mailFrame,text='群体充值')
        groupChargeFrame.pack(expand=True,fill='x',padx=3)
        chargeValueE = ttk.Spinbox(groupChargeFrame,from_=0,to=9e9)
        chargeValueE.pack(side='left',expand=True,fill='x')
        chargeTypeE = ttk.Combobox(groupChargeFrame,values=['点券','代币'],width=6)
        chargeTypeE.pack(side='left',expand=True,fill='x')
        chargeTypeE.set('点券')
        chargeBtn = ttk.Button(groupChargeFrame,text='群体充值',command=groupCharge)
        chargeBtn.pack(side='left',expand=True,fill='x')

        self.groupChargeLF = groupChargeFrame
        self.groupMailLF = groupMailFrame

        configFrame(mailFrame,'disable')

    def buildTab_event(self,tabView:ttk.Notebook,tabName:str):
        def get_available_event():
            eventList = sqlM.get_event_available()
            self.eventList = [[item[0],item[1],convert(item[2],'zh-cn')] for item in eventList]
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
        self.update_event_list_func = lambda:[get_available_event(),get_running_event()]
        try:
            if sqlM.connectorUsed is not None:
                self.update_event_list_func()
        except:
            pass
        #self.updateFuncList.append(get_available_event)
        #self.updateFuncList.append(get_running_event)
        eventFrame = tk.Frame(tabView)
        tabView.add(eventFrame,text=tabName)
        treeViewFrame = tk.Frame(eventFrame)
        treeViewFrame.pack(expand=True,fill='both')
        if True:
            eventTreeNow = ttk.Treeview(treeViewFrame,height=3)
            eventTreeNow.pack(expand=True,fill='both',side=tk.LEFT)
            if True:
                eventTreeNow["columns"] = ("1", "2", "3",'4')#,'5'
                eventTreeNow['show'] = 'headings'
                eventTreeNow.column("1", width = int(WIDTH*60), anchor ='c')
                eventTreeNow.column("2", width = int(WIDTH*160), anchor ='c')
                eventTreeNow.column("3", width = int(WIDTH*40), anchor ='c')
                eventTreeNow.column("4", width = int(WIDTH*40), anchor ='c')
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
        eventEditFrame.pack(side=tk.TOP)
        if True:
            cfg = {'padx':1,'pady':3, 'sticky':'nswe'}
            tk.Label(eventEditFrame,text='活动名称',fg='blue').grid(row=1,column=2)
            tk.Label(eventEditFrame,text='活动参数1',fg='blue').grid(row=1,column=3)
            tk.Label(eventEditFrame,text='活动参数2',fg='blue').grid(row=1,column=4)
            eventNameE = ttk.Combobox(eventEditFrame,width=int(WIDTH*23),state='readonly')
            eventNameE.grid(row=2,column=2,**cfg)
            eventNameE.bind('<<ComboboxSelected>>',select_new_event)
            CreateToolTip(eventNameE,textFunc=eventNameE.get)
            eventArg1E = ttk.Entry(eventEditFrame,width=int(WIDTH*7))
            eventArg1E.grid(row=2,column=3,**cfg)
            eventArg2E = ttk.Entry(eventEditFrame,width=int(WIDTH*7))
            eventArg2E.grid(row=2,column=4,**cfg)
            ttk.Button(eventEditFrame,text='刷新服务器活动',command=lambda:self.title(f'活动已刷新({len(get_running_event())})')).grid(row=3,column=2,**cfg)
            ttk.Button(eventEditFrame,text='删除选中',width=int(WIDTH*8),command=del_event).grid(row=3,column=3,**cfg)
            addBtn = ttk.Button(eventEditFrame,text='添加活动',width=int(WIDTH*8),command=set_event)
            addBtn.grid(row=3,column=4,**cfg)
            CreateToolTip(addBtn,'添加删除后需重启服务器')

    def buildTab_server(self,tabView:ttk.Notebook,tabName:str):
        self.serverApp = server.ServerCtrlFrame(tabView,titlefunc=self.title,autoConnect=self.sshAutoConnect)

    def buildTab_sponsor(self,tabView:ttk.Notebook,tabName:str):
        def loadPics():
            size = adLabel.winfo_width(), adLabel.winfo_height()
            if size[0] < 10:
                return self.after(100,loadPics)
            adLabel.load(r'config\sponsor.jpg',size,root=self)
        sponsorFrame = tk.Frame(tabView)
        tabView.add(sponsorFrame,text=tabName)
        #tk.Label(sponsorFrame,text='GM管理工具激活密钥获取详情请加群709527238。').pack()
        adLabel = ImageLabel(sponsorFrame,borderwidth=0)
        adLabel.pack(fill='both',expand=True)
        self.after(100,loadPics)
        CreateToolTip(sponsorFrame,'感谢支持，GM管理工具激活密钥请扫码加群，量大从优')
        



            
if __name__=='__main__':
    t = tk.Tk()
    t.geometry('0x0')
    t.overrideredirect(True)
    sqlM.connect()
    gm = GMToolWindow(t,cNo=2)
    gm.protocol('WM_DELETE_WINDOW',t.destroy)
    t.mainloop()





    