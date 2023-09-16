import zlib
import struct
#from mysql import connector
import datetime
import os
if __name__=='__main__':
    import sys
    sys.path.append(os.getcwd())
import pymysql 
from pymysql.constants import CLIENT
import json
from dnfpkgtool import cacheManager as cacheM
from zhconv import convert
import time 
import threading
from hashlib import md5
import pickle
import random
__version__ = ''
#print(f'物品栏装备删除工具_CMD {__version__}\n\n')

ENCODE_AUTO = True  #为True时会在解码后自动修改编码索引，由GUI配置
SQL_ENCODE_LIST = ['混合','windows-1252','latin1','big5','gbk','utf-8']
sqlEncodeUseIndex = 0

SQL_CONNECTOR_LIST = [pymysql]
SQL_CONNECTOR_IIMEOUT_KW_LIST = [
    {'connect_timeout':2},
    {'connect_timeout':2},
    {'connection_timeout':2},
]
connectorAvailuableList = []
connectorDict = {}  #'DBNAME':pymysql.connections.Connection
connectorUsed:pymysql.connections.Connection = None

CONNECTOR_NUM = 2

oldPrint = print
logFunc = [oldPrint]
def print(*args,**kw):
    logFunc[-1](*args,**kw)

def inThread(func):
    def inner(*args,**kw):
        t = threading.Thread(target=lambda:func(*args,**kw))
        t.setDaemon(True)
        t.start()
        return t
    return inner

class DnfItemSlot():
    '''物品格子对象，存储格子信息'''
    typeDict ={
        0x00:'已删除/空槽位',
        0x01:'装备',
        0x02:'消耗品',
        0x03:'材料',
        0x04:'任务材料',
        0x05:'宠物',
        0x06:'宠物装备',
        0x07:'宠物消耗品',
        0x0a:'副职业'
    }
    typeDictRev ={
        '已删除/空槽位':0x00,
        '装备':0x01,
        '消耗品':0x02,
        '材料':0x03,
        '任务材料':0x04,
        '宠物':0x05,
        '宠物装备':0x06,
        '宠物消耗品':0x07,
        '副职业':0x0a
    }
    increaseTypeDict = {
        0x00:'空-0',
        0x01:'异次元体力-1',
        0x02:'异次元精神-2',
        0x03:'异次元力量-3',
        0x04:'异次元智力-4'
    }
    def __init__(self,item_bytes:bytes=b'') -> None:
        if len(item_bytes)<61:
            item_bytes = b'\x00'*61
        self.oriBytes = item_bytes
        self.isSeal = item_bytes[0]
        self.type = item_bytes[1]
        self.id = struct.unpack('I',item_bytes[2:6])[0]
        self.enhancementLevel = item_bytes[6]&0x1f
        self.sealCnt = item_bytes[6]>>5
        if self.typeZh == '装备':
            self.num_grade = struct.unpack('!I',item_bytes[7:11])[0]
        else:
            self.num_grade = struct.unpack('I',item_bytes[7:11])[0]
        self.durability = struct.unpack('H',item_bytes[11:13])[0]
        self.orb_bytes = item_bytes[13:17]
        self.orb = struct.unpack('I',self.orb_bytes)[0]
        self.increaseType = item_bytes[17]
        self.increaseValue = struct.unpack('H',item_bytes[18:20])[0]
        self._others20_30 = item_bytes[20:31]
        self.otherworld = item_bytes[31:33]#struct.unpack('H',item_bytes[31:33])[0]
        self._others32_36 = item_bytes[33:37]
        self.magicSeal = item_bytes[37:51]
        self.coverMagic = self.magicSeal[-1]   #表示被替换的魔法封印，当第四属性存在的时候有效

        self.forgeLevel = item_bytes[51]
        self._others = item_bytes[52:]
    
    def readMagicSeal(self):
        def read3Bytes(seal:bytes=b'\x00\x00\x00'):
            sealID = seal[0]
            sealType = cacheM.magicSealDict.get(sealID)
            if sealType is None: sealType = ''
            sealLevel = int.from_bytes(seal[1:],'big')
            return sealID,sealType.strip(), sealLevel  #ID，type，level
        seal_1 = read3Bytes(self.magicSeal[:3])
        seal_2 = read3Bytes(self.magicSeal[3:6])
        seal_3 = read3Bytes(self.magicSeal[6:9])
        seal_4 = read3Bytes(self.magicSeal[10:13])
        return [self.coverMagic,[seal_1,seal_2,seal_3,seal_4]]
    
    def buildMagicSeal(self,sealTuple:tuple=(0,[[1,'name',1]*4])):
        coverMagic,seals = sealTuple
        magicSeal = b''
        for i in range(3):
            sealID, sealType, sealLevel = seals[i]
            if sealID==0:
                magicSeal += b'\x00\x00\x00'
                continue
            magicSeal += sealID.to_bytes(1,'big')
            magicSeal += sealLevel.to_bytes(2,'big')
        magicSeal += self.magicSeal[9:10]
        sealID, sealType, sealLevel = seals[3]
        if sealID==0:
            magicSeal += b'\x00\x00\x00'
        else:
            magicSeal += sealID.to_bytes(1,'big')
            magicSeal += sealLevel.to_bytes(2,'big')
        magicSeal += coverMagic.to_bytes(1,'big')
        return magicSeal
        #self.magicSeal = magicSeal


    @property
    def typeZh(self):
        return self.typeDict.get(self.type)
    
    @property
    def increaseTypeZh(self):
        typeZh = self.increaseTypeDict.get(self.increaseType)
        
        return typeZh if typeZh is not None else f'None-{self.increaseType}'

    def build_bytes(self):
        item_bytes = b''
        item_bytes += struct.pack('B',self.isSeal)
        item_bytes += struct.pack('B',self.type)
        item_bytes += struct.pack('I',self.id)
        enhanceAndSeal = self.enhancementLevel | (self.sealCnt<<5)
        item_bytes += struct.pack('B',enhanceAndSeal)
        #print(self.num_grade)
        if self.typeZh == '装备':
            item_bytes += struct.pack('!I',self.num_grade)
        else:
            item_bytes += struct.pack('I',self.num_grade)
        item_bytes += struct.pack('H',self.durability)
        self.orb_bytes = struct.pack('I',self.orb)
        item_bytes += self.orb_bytes
        item_bytes += struct.pack('B',self.increaseType)
        item_bytes += struct.pack('H',self.increaseValue)
        item_bytes += self._others20_30
        item_bytes += self.otherworld#struct.pack('H',self.otherworld)
        item_bytes += self._others32_36
        item_bytes += self.magicSeal
        item_bytes += struct.pack('B',self.forgeLevel)
        item_bytes += self._others
        return item_bytes


    def __repr__(self) -> str:
        s = f'[{self.typeDict.get(self.type)}]{cacheM.ITEMS_dict.get(self.id)} '
        if self.typeDict.get(self.type) in ['消耗品','材料','任务材料','副职业','宠物','宠物消耗品']:
            s += f'数量:{self.num_grade}'
        elif self.typeDict.get(self.type) in ['装备']:
            if self.isSeal!=0:
                s+=f'[封装]'
            if self.enhancementLevel>0:
                s+=f' 强化:+{self.enhancementLevel}'
            s += f' 耐久:{self.durability}'
            if self.increaseType!=0:
                s += f' 增幅:{self.increaseTypeZh}+{self.increaseValue}'#self.increaseTypeDict.get(self.increaseType)
            if  self.forgeLevel>0:
                s += f' 锻造:+{self.forgeLevel}'
        return s
    __str__ = __repr__

def unpackBLOB_Item(fbytes):
    '''返回[index, DnfItemGrid对象]'''
    try:
        items_bytes = zlib.decompress(fbytes[4:])
        num = len(items_bytes)//61
        result = []
        for i in range(num):
            item = DnfItemSlot(items_bytes[i*61:(i+1)*61])
            result.append([i, item])
    except:
        #print('背包字节解压错误...')
        result = []
    return result

def buildDeletedBlob2(deleteList,originBlob):
    '''返回删除物品后的数据库blob字段'''
    prefix = originBlob[:4]
    items_bytes = bytearray(zlib.decompress(originBlob[4:]))
    for i in deleteList:
        items_bytes[i*61:i*61+61] = bytearray(b'\x00'*61)
    blob = prefix + zlib.compress(items_bytes)
    return blob

def buildBlob(originBlob,editedDnfItemSlotList):
    '''传入原始blob字段和需要修改的位置列表[ [1, DnfItemGrid对象], ... ]'''
    prefix = originBlob[:4]
    items_bytes = bytearray(zlib.decompress(originBlob[4:]))
    for i,itemGird in editedDnfItemSlotList:
        items_bytes[i*61:i*61+61] = itemGird.build_bytes()
    blob = prefix + zlib.compress(items_bytes)
    return blob

def newConnector(db=''):
    global  connectorDict
    config = cacheM.config
    for _ in range(2):
        for _,connector_ in enumerate(SQL_CONNECTOR_LIST):
            try:
                dbConn = connector_.connect(user=config['DB_USER'], password=config['DB_PWD'], host=config['DB_IP'], port=config['DB_PORT'],charset='utf8',
                                            autocommit=True,connect_timeout=2,client_flag=CLIENT.MULTI_STATEMENTS)
                connectorDict[db] = dbConn
                sql = f'create database if not exists {db};'
                dbConn.cursor().execute(sql)
                dbConn.select_db(db)

                return True
            except Exception as e:
                pass
    return False


# 调用exe_and_xxx后，生成一个id，将id和参数放入exec_queue，等待数据返回

execute_queue_Dict = {}  #[(taskID,args,'fetch'/'commit'/None),...]
resDict = {}    # {id:res}


taskNum = 0
def gen_task_id():
    global taskNum
    taskNum += 1
    taskID =  str(time.time())+str(taskNum) + str(random.randint(0,1000))
    return taskID

#executorList = []
@inThread
def executor(db):
    global execute_queue_Dict
    ID = str(time.time())
    #executorList.append(ID)
    execute_queue = execute_queue_Dict[db]
    while True:
        if len(execute_queue)>0:# and executorList[-1]==ID:
            taskID,args,execType = execute_queue.pop(0)
            #print(taskID,args,execType)
            if execType=='fetch':
                resDict[taskID] = execute_fech(*args)
            elif execType=='commit':
                resDict[taskID] = execute_commit(*args)
            else:
                resDict[taskID] = execute(*args)
        else:
            time.sleep(0.0005)

def execute(db,sql,args=None,charset='utf8',reConn=True):
    if connectorDict.get(db) is None:
        if not newConnector(db):
            print(db,sql,args)
            print(f'数据库{db}连接失败')
            return []
    try:
        connector:pymysql.connections.Connection = connectorDict[db]
        connector.set_charset(charset)
        cursor = connector.cursor()
        if args is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql,args)
        print(sql)
        return True
    except Exception as e:
        if reConn:
            #print(f'数据库{db}连接失败，尝试重新连接... 错误信息:{e}')
            connectorDict[db] = None
            return execute(db,sql,args,charset,False)

def execute_fech(db,sql,args=None,charset='utf8',reConn=True):
    if connectorDict.get(db) is None:
        if not newConnector(db):
            print(db,sql,args)
            print(f'数据库{db}连接失败')
            return []
    try:
        #print(db,sql,args)
        connector:pymysql.connections.Connection = connectorDict[db]
        connector.set_charset(charset)
        cursor = connector.cursor()
        if args is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql,args)
        res = cursor.fetchall()
        return res
    except Exception as e:
        if reConn:
            #print(f'数据库{db}连接失败，尝试重新连接... 错误信息:{e}')
            connectorDict[db] = None
            return execute_fech(db,sql,args,charset,False)
        return []

def execute_commit(db,sql,args=None,charset='utf8',reConn=True):
    if connectorDict.get(db) is None:
        if not newConnector(db):
            print(db,sql,args)
            print(f'数据库{db}连接失败')
            return False
    try:
        connector:pymysql.connections.Connection = connectorDict[db]
        connector.set_charset(charset)
        cursor = connector.cursor()
        if args is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql,args)
        #connector.commit()
        #print(sql)
        return True
    except Exception as e:
        print(e)
        if args is None:
            print(sql[:500])
        else:
            print(sql[:500],args[:100])
        if reConn:
            #print(f'数据库{db}连接失败，尝试重新连接... 错误信息:{e}')
            connectorDict[db] = None
            return execute_commit(db,sql,args,charset,False)
    return False

def execute_and_fetch(db,sql,args=None,charset='utf8'):
    taskID = gen_task_id()
    execute_queue = execute_queue_Dict.get(db)
    if execute_queue is None:
        execute_queue = []
        execute_queue_Dict[db] = execute_queue
        executor(db)
    execute_queue.append((taskID,[db,sql,args,charset],'fetch'))
    #timeStart = time.time()
    while True:
        if resDict.get(taskID) is not None:
            res = resDict.pop(taskID)
            return res
        else:
            time.sleep(0.005)
            

def execute_and_commit(db,sql,args=None,charset='utf8'):
    taskID = gen_task_id()
    execute_queue = execute_queue_Dict.get(db)
    if execute_queue is None:
        execute_queue = []
        execute_queue_Dict[db] = execute_queue
        executor(db)
    execute_queue.append((taskID,[db,sql,args,charset],'commit'))
    while True:
        if resDict.get(taskID) is not None:
            res = resDict.pop(taskID)
            return res
        else:
            time.sleep(0.005)

def getUID(username=''):
    if username=='':
        return -1
    sql = f"select UID from accounts where accountname='{username}';"
    res = execute_and_fetch('d_taiwan',sql)
    if len(res)==0:
        #print('未查询到记录')
        return 0
    return res[0][0]



def decode_charac_list_old(characList:list):
    global sqlEncodeUseIndex
    res_new = []
    if ENCODE_AUTO==True:
        sqlEncodeUseIndex = 0
        while sqlEncodeUseIndex < len(SQL_ENCODE_LIST):
            res_new = []
            #print(f'当前编码：{SQL_ENCODE_LIST[sqlEncodeUseIndex]}')
            for i in characList:
                record = list(i)
                try:
                    record[1] = record[1].encode(SQL_ENCODE_LIST[sqlEncodeUseIndex]).decode('utf-8')
                    res_new.append(record)
                except:
                    
                    if sqlEncodeUseIndex +1 < len(SQL_ENCODE_LIST):
                        sqlEncodeUseIndex += 1
                        
                        break
                    else:
                        record[1] = record[1].encode(SQL_ENCODE_LIST[sqlEncodeUseIndex],errors='replace').decode('utf-8',errors='replace')
                        res_new.append(record)
            if len(res_new) == len(characList):
                break
    else:
        for i in characList:
            record = list(i)
            print(record)
            record[1] = record[1].encode(SQL_ENCODE_LIST[sqlEncodeUseIndex],errors='replace').decode('utf-8',errors='replace')
            res_new.append(record)
    print(SQL_ENCODE_LIST[sqlEncodeUseIndex])
    return res_new
def decode(string:str):
    s1 = string.encode('latin1','replace')
    s2 = string.encode('cp1252','replace')
    s3 = b''
    for i in range(len(s1)):
        if s1[i:i+1] == b'?':
            s3 += s2[i:i+1]
        else:
            s3 += s1[i:i+1]
    return s3.decode(errors='replace')
def decode_charac_list(characList:list):
    
    global sqlEncodeUseIndex
    res_new = []
    if SQL_ENCODE_LIST[sqlEncodeUseIndex]=='混合':
        for i in characList:
            record = list(i)
            #print(record)
            record[2] = decode(record[2])
            res_new.append(record)
    else:
        for i in characList:
            record = list(i)
            #print(record)
            record[2] = record[2].encode(SQL_ENCODE_LIST[sqlEncodeUseIndex],errors='replace').decode('utf-8',errors='replace')
            res_new.append(record)
    #print(SQL_ENCODE_LIST[sqlEncodeUseIndex])
    return res_new


def getCharacterInfo(cName='',uid=0,cNo=0):
    '''返回 m_id, charac_no, charac_name, lev, job, grow_type, delete_flag, expert_job'''
    if uid>0 and cName=='':
        sql = f"select m_id, charac_no, charac_name, lev, job, grow_type, delete_flag, expert_job from charac_info where m_id='{uid}';"
        res = execute_and_fetch('taiwan_cain',sql)
    elif uid==-1:
        res = get_all_charac()
        return res
    elif cNo!=0:
        sql = f"select m_id, charac_no, charac_name, lev, job, grow_type, delete_flag, expert_job from charac_info where charac_no='{cNo}';"
        res = execute_and_fetch('taiwan_cain',sql)
    else:
        #print(f'查询{cName}')
        name_new = cName.encode('utf-8','replace')
        sql = f"select m_id, charac_no, charac_name, lev, job, grow_type, delete_flag, expert_job  from charac_info where charac_name=%s;"  
        res = list(execute_and_fetch('taiwan_cain',sql,(name_new,),'latin1'))
        res.extend(execute_and_fetch('taiwan_cain',sql,(name_new,),'utf-8'))

        name_tw = convert(cName,'zh-tw')
        if cName!=name_tw:
            name_tw_new = name_tw.encode('utf-8','replace')
            sql = f"select m_id, charac_no, charac_name, lev, job, grow_type, delete_flag, expert_job from charac_info where charac_name=%s;"
            res.extend(execute_and_fetch('taiwan_cain',sql,(name_tw_new,),'latin1'))
            res.extend(execute_and_fetch('taiwan_cain',sql,(name_tw_new,),'utf-8'))
    res = decode_charac_list(res)
    #print(f'角色列表加载完成')
    return res


def getCharactorNo(cName):
    name_new = cName.encode('utf-8').decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
    sql = f"select charac_no from charac_info where charac_name='{name_new}';"
    res = execute_and_fetch('taiwan_cain',sql)

    name_tw = convert(cName,'zh-tw')
    if cName!=name_tw:
        name_tw_new = name_tw.encode('utf-8').decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
        sql = f"select charac_no from charac_info where charac_name='{name_tw_new}';"
        res_tmp = execute_and_fetch('taiwan_cain',sql)
        res.extend(res_tmp)
    return res

def getCargoAll(cName='',cNo=0):
    '''获取仓库的blob字段'''
    if cNo==0:
        cNo = getCharactorNo(cName)[0][0]
    get_all_sql = f'select cargo,jewel,expand_equipslot from charac_inven_expand where charac_no={cNo};'
    res = execute_and_fetch('taiwan_cain_2nd',get_all_sql)
    if len(res)==0:
        return [[[],[],[]]]
    return res

def get_Account_Cargo(uid=0,cNo=0):
    if uid==0:
        uid = cNo_2_uid(cNo)
    sql = f'select cargo from account_cargo where m_id={uid}'
    cargoBlob = execute_and_fetch('taiwan_cain',sql)
    if len(cargoBlob)>0:
        cargoBlob = cargoBlob[0][0]
    return cargoBlob



def getInventoryAll(cName='',cNo=0):
    '''获取背包，穿戴槽，宠物栏的blob字段 以及 物品槽数量'''
    if cNo!=0:
        charac_no = cNo
    else:
        charac_no = getCharactorNo(cName)[0][0]

    get_all_sql = f'select inventory,equipslot,creature,inventory_capacity from inventory where charac_no={charac_no};'
    res = execute_and_fetch('taiwan_cain_2nd',get_all_sql)
    if len(res)==0:
        return [[[],[],[],[]]]
    return res

def getAvatar(cNo,ability_=False):
    getAvatarSql = f'select ui_id,it_id,hidden_option from user_items where charac_no={cNo};'

    results = execute_and_fetch('taiwan_cain_2nd',getAvatarSql)
    #results = cursor.fetchall()
    res = []
    for ui_id,it_id,hidden_option in results:
        if ability_:
            res.append([ui_id,cacheM.ITEMS_dict.get(it_id),it_id,hidden_option])
        else:
            res.append([ui_id,cacheM.ITEMS_dict.get(it_id),it_id])
    return res

def getCreatureItem(cName='',cNo=0):
    '''获取宠物'''
    if cNo!=0:
        charac_no = cNo
    else:
        charac_no = getCharactorNo(cName)[0][0]
    get_creatures_sql = f'select ui_id,it_id,name from creature_items where charac_no={charac_no};'
    results = execute_and_fetch('taiwan_cain_2nd',get_creatures_sql)

    #print(results)
    res = []
    for ui_id, it_id, cName in results:
        name_new = decode(cName)
        res.append([ui_id,cacheM.ITEMS_dict.get(it_id),it_id,name_new])
    return res

def get_online_uid():
    get_login_account_sql = f'select m_id,login_ip from login_account_3 where login_status=1'
    onlineAccounts = execute_and_fetch('taiwan_login',get_login_account_sql)
    onlineAccountIPDict = {item[0]:item[1] for item in onlineAccounts}
    return onlineAccountIPDict

def get_online_charac():
    get_login_account_sql = f'select m_id from login_account_3 where login_status=1'
    res = execute_and_fetch('taiwan_login',get_login_account_sql)
    onlineAccounts = [item[0] for item in res]
    result = []
    for uid in onlineAccounts:
        sql = f'select charac_no from event_1306_account_reward where m_id={uid}'
        cNo = execute_and_fetch('taiwan_game_event',sql)[0][0]
        #cNo = gameCursor.fetchall()[0][0]
        sql = f"select m_id, charac_no, charac_name, lev, job, grow_type, delete_flag, expert_job  from charac_info where charac_no={cNo};"
        res = execute_and_fetch('taiwan_cain',sql)
        res = list(res[0])
        result.append(res)
    return decode_charac_list(result)

def get_online_charac_3():
    '''[[uid,cNo,ip]...]'''
    get_login_account_sql = f'select m_id,login_ip from login_account_3 where login_status=1'
    res = execute_and_fetch('taiwan_login',get_login_account_sql)
    uid_ip_dict = {item[0]:item[1] for item in res}
    onlineAccounts = [item[0] for item in res]
    if len(onlineAccounts)==0:
        return []
    sql = f'select m_id,charac_no from event_1306_account_reward where '
    for uid in onlineAccounts:
        sql += f' m_id={uid} or'
    sql = sql[:-2]
    res = execute_and_fetch('taiwan_game_event',sql)
    res = [[item[0],item[1],uid_ip_dict.get(item[0],'')] for item in res]
    return res

VIP_KEY = 'VIP'
def check_VIP_column():
    global VIP_KEY
    
    sql = f'''select column_name,data_type from information_schema.columns where table_schema='d_taiwan' and table_name='accounts';'''
    res = execute_and_fetch('d_taiwan',sql)
    for column_name,data_type in res:
        if column_name.lower()=='vip':
            VIP_KEY = column_name
            return
    sql = 'ALTER TABLE accounts ADD VIP INT(1) NOT NULL DEFAULT 0;'
    execute_and_commit('d_taiwan',sql)

def get_VIP_charac(all=False):
    sql = f'select UID from accounts where {VIP_KEY}=1;'
    res = execute_and_fetch('d_taiwan',sql)
    characs_list = []
    for uid in res:
        uid = uid[0]
        characs = getCharacterInfo(uid=uid)
        characs = list(filter(lambda x:x[-2]!=1,characs))   #去除删除掉的角色
        if all==False:
            characs_list.append(characs[0])
        else:
            characs_list.extend(characs)
    return characs_list

def get_all_charac():
    sql = f'select UID from accounts;'
    res = execute_and_fetch('d_taiwan',sql)
    sql = f"select m_id, charac_no, charac_name, lev, job, grow_type, delete_flag, expert_job from charac_info;"
    res = execute_and_fetch('taiwan_cain',sql)
    characs = decode_charac_list(res)
    characs = list(filter(lambda x:x[-2]!=1,characs))
    return characs

def setInventory(InventoryBlob,cNo,key='inventory'):
    if key in ['account_cargo']:
        uid = cNo_2_uid(cNo)
        sql_update = f'''update account_cargo set cargo=%s where m_id={uid};'''
        execute_and_commit('taiwan_cain',sql_update,(InventoryBlob,))
        return True

    if key in ['inventory','equipslot', 'creature']: table = 'inventory'
    if key in ['cargo','jewel','expand_equipslot']: table = 'charac_inven_expand'
    if key in ['skill_slot']:table = 'skill'
    sql_update = f'''update {table} set {key}=%s where charac_no={cNo};'''
    print(sql_update % InventoryBlob)
    try:
        execute_and_commit('taiwan_cain_2nd',sql_update,(InventoryBlob,))
        return True
    except:
        return False

def commit_change_blob(originBlob,editDict:dict,cNo,key):
    '''传入原始blob和修改的物品槽对象列表'''
    editList = [[keyy,value] for keyy,value in editDict.items()]
    print(editList)
    blob_new = buildBlob(originBlob,editList)
    print(f'ID:{cNo}, {key}\n',unpackBLOB_Item(blob_new))
    return setInventory(blob_new,cNo,key)

def delCreatureItem(ui_id):
    try:
        sql = f'delete from creature_items where ui_id={ui_id};'
        print(sql)
        execute_and_commit('taiwan_cain_2nd',sql)
        return True
    except:
        return False
    
def delNoneBlobItem(ui_id,tableName='creature_items'):
    try:
        print(f'{ui_id},{tableName}')
        if tableName=='user_postals':   #删除邮件
            delete_mail_postal(ui_id)
            return True
        sql = f'delete from {tableName} where ui_id={ui_id};'
        print(sql)
        execute_and_commit('taiwan_cain_2nd',sql)
        return True
    except:
        print(f'{tableName}删除失败')
        return False

def enable_Hidden_Item(ui_id,tableName='user_items',value=1):
    try:
        sql = f'update {tableName} set hidden_option={value} where ui_id={ui_id}'
        print(sql)
        execute_and_commit('taiwan_cain_2nd',sql)
        return True
    except:
        return False

def cNo_2_uid(cNo):
    sql = f"select m_id from charac_info where charac_no='{cNo}';"
    try:
        uid = execute_and_fetch('taiwan_cain',sql)[0][0]
    except:
        uid = 0
    return uid

def set_VIP(cNo,value=1):
    sql = f"select m_id from charac_info where charac_no='{cNo}';"
    uid = execute_and_fetch('taiwan_cain',sql)[0][0]
    sql = f'update accounts set {VIP_KEY}={value} where UID={uid};'
    execute_and_commit('d_taiwan',sql)

def read_VIP(cNo):
    sql = f"select m_id from charac_info where charac_no='{cNo}';"
    uid = execute_and_fetch('taiwan_cain',sql)[0][0]
    sql = f'select VIP from accounts where UID={uid};'
    VIP = execute_and_fetch('d_taiwan',sql)[0][0]
    if VIP == '':
        VIP = 0
    return VIP

def read_return_user(cNo):
    uid = cNo_2_uid(cNo)
    sql = 'select m_id,expire_time from return_user'
    res = execute_and_fetch('taiwan_game_event',sql)
    
    for m_id,expire_time in res:
        time_old = time.strptime(str(expire_time), r"%Y-%m-%d %H:%M:%S")
        if m_id==uid and time.localtime()<time_old:
            return True 
    return False

def set_return_user(cNo):
    uid = cNo_2_uid(cNo)
    sql = f'select m_id,expire_time from return_user where m_id={uid}'
    res = execute_and_fetch('taiwan_game_event',sql)
    if len(res)>0:
        sql = f'''update return_user set expire_time='2023-12-31 00:00:00';'''
    else:
        sql = f'''insert into return_user (m_id,expire_time) values ({uid},'2023-12-31 00:00:00');'''
    execute_and_commit('taiwan_game_event',sql)

def clear_return_user(cNo):
    uid = cNo_2_uid(cNo)
    sql = f'''delete from return_user where m_id={uid};'''
    execute_and_commit('taiwan_game_event',sql)

def get_baned_Dict():
    sql = 'select m_id, punish_type, occ_time, punish_value, apply_flag, start_time, end_time, reason from member_punish_info where apply_flag!=0'
    res = execute_and_fetch('d_taiwan',sql)
    banedDict = {}
    timeNow = datetime.datetime.now()
    for m_id, punish_type, occ_time, punish_value, apply_flag, start_time, end_time, reason in res:
        #print(m_id, punish_type, occ_time, punish_value, apply_flag, start_time, end_time, reason)
        if end_time<timeNow:continue
        banedDict[m_id] = {
            'punish_type':punish_type,'start_time':start_time,'end_time':end_time,'reason':reason
        }
    return banedDict

def get_all_accountName_and_uid():
    sql = 'select UID,accountname from accounts'
    res = execute_and_fetch('d_taiwan',sql)
    ACCOUNT_DICT = {item[0]:item[1] for item in res}
    return ACCOUNT_DICT

def resume_baned(uid):
    sql = f'delete from member_punish_info where m_id={uid};'
    execute_and_commit('d_taiwan',sql)
    
def set_baned(uid,days=365,punish_type=1,punishValue=101,reason=''):
    occ_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    end_time = (datetime.datetime.now()+datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    sql = f'''REPLACE INTO `member_punish_info` (m_id, punish_type, occ_time, punish_value, apply_flag, start_time, end_time, reason) VALUES({uid}, {punish_type}, "{occ_time}",{punishValue},2,"{start_time}","{end_time}",%s);'''
    execute_and_commit('d_taiwan',sql,(reason,))

def get_baned_Dict_detail():
    banedDict = get_baned_Dict()
    sql = 'SELECT m_id,login_ip FROM `taiwan_login`.`login_account_3` where '
    if len(banedDict.keys())==0:
        return {}
    ACCOUNT_DICT = get_all_accountName_and_uid()
    for uid in banedDict.keys():
        sql += f' m_id={uid} or'
    sql = sql[:-2]
    res = execute_and_fetch('taiwan_login',sql)
    uid_ip_dict = {item[0]:item[1] for item in res}
    for uid,uInfoDict in banedDict.items():
        ip = uid_ip_dict.get(uid,'')
        accountName = ACCOUNT_DICT.get(uid,'')
        banedDict[uid]['ip'] = ip
        banedDict[uid]['accountName'] = accountName
    return banedDict

def set_charac_info(cNo,*args,**kw):
    for key,value in kw.items():
        try:
            charSet = 'utf8'
            if key=='charac_name':
                ENCODE = 'utf-8'
                try:
                    value = value.encode(ENCODE,errors='replace')#.decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
                except:
                    value = convert(value,'zh-tw').encode(ENCODE,errors='replace')#.decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
                charSet = 'latin1'
                #connectorUsed.set_charset('latin1')
            elif key=='lev':
                sql = f"select m_id,lev from charac_info where charac_no='{cNo}';"
                uID,lev = execute_and_fetch('taiwan_cain',sql)[0]
                if lev==value:
                    continue    #未进行等级调整
                sql_exp = f'update charac_stat set exp=%s where charac_no={cNo}'
                expTableList_with_lv0 = [0,0] + cacheM.expTableList
                exp = expTableList_with_lv0[value] + 1
                execute_and_commit('taiwan_cain',sql_exp,(exp,))
                sql_punish = f'delete from member_punish_info where m_id={uID};'
                execute_and_commit('d_taiwan',sql_punish)
                print(sql_punish)
            elif key=='VIP':
                set_VIP(cNo,value)
                continue

            sql = f'update charac_info set {key}=%s where charac_no={cNo}'
            execute_and_commit('taiwan_cain',sql,(value,),charSet)
        except Exception as e:
            print(f'指令{key}-{value}执行失败，{e}')

def set_account_money(uid,money):
        sql = f'update account_cargo set money={money} where m_id={uid};'
        execute_and_commit('taiwan_cain',sql)
    
def get_account_money(uid):
    sql = f'select money from account_cargo where m_id={uid};'
    res = execute_and_fetch('taiwan_cain',sql)
    if len(res)==0:
        return 0
    return res[0][0]

def set_charac_money(cNo,money):
    sql = f'update inventory set money={money} where charac_no={cNo};'
    execute_and_commit('taiwan_cain_2nd',sql)

def get_charac_money(cNo):
    sql = f'select money from inventory where charac_no={cNo};'
    res = execute_and_fetch('taiwan_cain_2nd',sql)
    if len(res)==0:
        return 0
    return res[0][0]

def set_pay_coin(cNo,paycoin):
    sql = f'update inventory set pay_coin={paycoin} where charac_no={cNo};'
    execute_and_commit('taiwan_cain_2nd',sql)

def get_pay_coin(cNo):
    sql = f'select pay_coin from inventory where charac_no={cNo};'
    res = execute_and_fetch('taiwan_cain_2nd',sql)
    if len(res)==0:
        return 0
    return res[0][0]

def get_skill_sp(cNo):
    '''返回 remain_sp,remain_sp_2nd,remain_sfp_1st,remain_sfp_2nd '''
    sql = f'select remain_sp,remain_sp_2nd,remain_sfp_1st,remain_sfp_2nd from skill where charac_no={cNo};'
    sp = execute_and_fetch('taiwan_cain_2nd',sql)
    if len(sp)==0:
        return 0,0,0,0
    return sp[0]
def set_skill_sp(cNo,sp,sp2,tp,tp2):
    sql = f'update skill set remain_sp={sp},remain_sp_2nd={sp2},remain_sfp_1st={tp},remain_sfp_2nd={tp2} where charac_no={cNo};'
    execute_and_commit('taiwan_cain_2nd',sql)

def charge_sp(cNo,value,key='remain_sp'):
    key2 = 'remain_sp_2nd' if key=='remain_sp' else 'remain_sfp_2nd'
    sql = f'update skill set {key}={key}+{value},{key2}={key2}+{value} where charac_no={cNo};'
    execute_and_commit('taiwan_cain_2nd',sql)

def get_quest_point(cNo):
    sql = f'select qp from charac_quest_shop where charac_no={cNo};'
    qp = execute_and_fetch('taiwan_cain',sql)
    if len(qp)==0:
        return 0
    return qp[0][0]

def set_quest_point(cNo,qp):
    sql = f'update charac_quest_shop set qp={qp} where charac_no={cNo};'
    execute_and_commit('taiwan_cain',sql)

def charge_quest_point(cNo,value):
    sql = f'update charac_quest_shop set qp=qp+{value} where charac_no={cNo};'
    execute_and_commit('taiwan_cain',sql)

def set_cera(uid,value,type='crea'):
    if type=='cera':
        sql = f'update cash_cera set cera={value} where account={uid};'
    elif type=='cera_point':
        sql = f'update cash_cera_point set cera_point={value} where account={uid};'
    execute_and_commit('taiwan_billing',sql)

def charge_crea(uid,value,type='crea'):
    if type=='cera':
        sql = f'update cash_cera set cera=cera+{value} where account={uid};'
    elif type=='cera_point':
        sql = f'update cash_cera_point set cera_point=cera_point+{value} where account={uid};'
    execute_and_commit('taiwan_billing',sql)

def get_cera(uid):
    sql = f'select cera from cash_cera where account={uid}'
    cera = execute_and_fetch('taiwan_billing',sql)[0][0]
    sql = f'select cera_point from cash_cera_point where account={uid}'
    cera_point = execute_and_fetch('taiwan_billing',sql)[0][0]
    return cera,cera_point

def get_cera_point(uid):
    sql = f'select cera_point from cash_cera_point where account={uid}'
    cera_point = execute_and_fetch('taiwan_billing',sql)[0][0]
    return cera_point

def get_PVP(cNo):
    sql = f'select pvp_grade,win,pvp_point,win_point from pvp_result where charac_no={cNo}'
    res = execute_and_fetch('taiwan_cain',sql)
    if len(res)==0:
        return 0,0,0,0
    return res[0]

def set_PVP(cNo,pvp_grade,win,pvp_point,win_point):
    sql = f'update pvp_result set pvp_grade={pvp_grade},win={win},pvp_point={pvp_point},win_point={win_point} where charac_no={cNo}'
    execute_and_commit('taiwan_cain',sql)

def enable_LR_slot(cNo):
    sql = f'update charac_stat set add_slot_flag=3 where charac_no={cNo};'
    execute_and_commit('taiwan_cain',sql)

def unlock_ALL_Level_equip(cNo):
    sql = f'delete from charac_manage_info where charac_no={cNo};'
    execute_and_commit('taiwan_cain',sql)
    sql = f'insert into charac_manage_info (charac_no,max_equip_level) values ({cNo},999);'
    execute_and_commit('taiwan_cain',sql)

def delete_all_mail_cNo(cNo):
    '''传入-1删除所有邮件'''
    sql = f'update postal set delete_flag=1 where receive_charac_no={cNo};'
    if cNo==-1: #
        sql = f'update postal set delete_flag=1;'
    execute_and_commit('taiwan_cain_2nd',sql)

def get_all_postalID():
    sql = f'select postal_id from postal where delete_flag=0;'
    res = execute_and_fetch('taiwan_cain_2nd',sql)
    return res

def delete_mail_postal(postal_id):
    sql = f'select item_id,avata_flag,creature_flag,add_info,letter_id from postal' +\
        f' where postal_id={postal_id};'
    item_id,avata_flag,creature_flag,add_info,letter_id = execute_and_fetch('taiwan_cain_2nd',sql)[0]
    try:
        if avata_flag==1:
            delNoneBlobItem(add_info,'user_items')
        elif creature_flag==1:
            delNoneBlobItem(add_info,'creature_items')
    except:
        pass
    sql = f'update postal set delete_flag=1 where postal_id={postal_id};'
    execute_and_commit('taiwan_cain_2nd',sql)

def unlock_all_lev_dungeon(uid,dungeon=''):
    #dungeon = '1|3,2|3,3|3,4|3,5|3,6|3,7|3,8|3,9|3,11|3,12|3,13|3,14|3,15|3,16|1,17|3,21|3,22|3,23|3,24|3,25|3,26|3,27|3,31|3,32|3,33|3,34|3,35|3,36|3,37|3,40|3,41|2,42|3,43|3,44|3,45|3,50|3,51|3,52|3,53|3,60|3,61|3,62|2,63|3,64|3,65|3,67|3,70|3,71|3,72|3,73|3,74|3,75|3,76|3,77|3,80|3,81|3,82|3,83|3,84|3,85|3,86|3,87|3,88|3,89|3,90|3,91|2,92|3,93|3,100|3,101|3,102|3,103|3,104|3,110|3,111|3,112|3,140|3,141|3,502|3,511|3,515|1,518|1,521|3,1000|3,1500|3,1501|3,1502|3,1507|1,3506|3,10000|3'
    sql = f"update member_dungeon set dungeon='{dungeon}' where m_id={uid};"
    execute_and_commit('taiwan_cain',sql)

def unlock_register_limit(uid):
    sql = f'update limit_create_character set count=0 where m_id={uid};'
    execute_and_commit('d_taiwan',sql)
    sql_punish = f'delete from member_punish_info where m_id={uid};'
    execute_and_commit('d_taiwan',sql_punish)

def maxmize_expert_lev(cNo):
    sql = f'update charac_stat set expert_job_exp=2054 where charac_no={cNo}'
    execute_and_commit('taiwan_cain',sql)

def get_event_available():
    sql = 'select event_id,event_name,event_explain from dnf_event_info;'
    res = execute_and_fetch('d_taiwan',sql)
    return res

def set_event(event_id,para1,para2=0):
    sql = f'insert into dnf_event_log (occ_time,event_type,parameter1,parameter2,server_id,event_flag,start_time,end_time) values (0,{event_id},{para1},{para2},0,0,0,0)'
    execute_and_commit('d_taiwan',sql)

def del_event(event_log_id):
    sql = f'delete from dnf_event_log where log_id={event_log_id};'
    execute_and_commit('d_taiwan',sql)

def get_event_running():
    sql = 'select log_id,event_type,parameter1,parameter2 from dnf_event_log;'
    res = execute_and_fetch('d_taiwan',sql)
    return res

def set_unlimited_inveWeight(cNo):
    sql = f'update charac_info set inven_weight=99999999 where charac_no={cNo}'
    execute_and_commit('taiwan_cain',sql)

def send_message(cNo,sender='测试发件人',message='测试邮件')->int:
    senders = cacheM.config.get('SENDERS',[])
    if sender not in senders:
        senders.append(sender)
        cacheM.config['SENDERS'] = senders
        cacheM.save_config()
    messages = cacheM.config.get('MESSAGES',[])
    if message not in messages:
        messages.append(message)
        cacheM.config['MESSAGES'] = messages
        cacheM.save_config()
    
    reg_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = f'insert into letter (charac_no,send_charac_no,send_charac_name,letter_text,reg_date,stat) ' +\
        f"values ({cNo},0,%s,%s,'{reg_time}',1);"
    execute_and_commit('taiwan_cain_2nd',sql,(sender.encode('utf-8'),message.encode('utf-8')),'latin1')
    sql = f"select letter_id from letter where reg_date='{reg_time}'"
    letterID = execute_and_fetch('taiwan_cain_2nd',sql)
    return letterID[-1][0]

def send_postal(cNo,letterID=0,sender='测试发件人',message='测试邮件',itemID=1000,increaseType=0,increaseValue=0,forgeLev=0,seal=0,totalnum=1,enhanceValue=0,gold=0,avata_flag=0,creature_flag=0,endurance=0):
    def send():
        nonlocal num
        occ_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if avata_flag==1:
            sql = f"insert into taiwan_cain_2nd.user_items (charac_no,it_id,expire_date,obtain_from,reg_date,stat) values ({cNo},{itemID},'9999-12-31 23:59:59',1,'{occ_time}',2)"
            execute_and_commit('taiwan_cain_2nd',sql)
            sql = f"select ui_id from user_items where charac_no={cNo} and it_id={itemID} and reg_date='{occ_time}';"
            ui_id = execute_and_fetch('taiwan_cain_2nd',sql)[0][0]
            num = ui_id
        elif creature_flag==1:
            itemDict = cacheM.get_Item_Info_In_Dict(itemID)
            if itemDict.get('[output index]') is not None:
                creatureType = 0
            else:
                creatureType = 1
            sql = f"insert into taiwan_cain_2nd.creature_items (charac_no,it_id,expire_date,reg_date,stat,item_lock_key,creature_type,stomach) values ({cNo},{itemID},'9999-12-31 23:59:59','{occ_time}',0,0,{creatureType},100)"
            execute_and_commit('taiwan_cain_2nd',sql)
            sql = f"select ui_id from creature_items where charac_no={cNo} and it_id={itemID} and reg_date='{occ_time}';"
            ui_id = execute_and_fetch('taiwan_cain_2nd',sql)[0][0]
            num = ui_id
        sql = 'insert into postal (occ_time,send_charac_name,receive_charac_no,amplify_option,amplify_value,seperate_upgrade,seal_flag,item_id,add_info,upgrade,gold,letter_id,avata_flag,creature_flag,endurance,unlimit_flag) '+\
            f"values ('{occ_time}',%s,{cNo},{increaseType},{increaseValue},{forgeLev},{seal},{itemID},{num},{enhanceValue},{gold},{letterID},{avata_flag},{creature_flag},{endurance},1)"
        execute_and_commit('taiwan_cain_2nd',sql,(sender.encode(),),'latin1')
    if letterID==0:
        letterID = send_message(cNo,sender='测试发件人',message='测试邮件')
    stkLimit = cacheM.get_Item_Info_In_Dict(itemID).get('[stack limit]')
    if stkLimit is not None:
        stkLimit = stkLimit[0]
    else:
        stkLimit = 1e19
    numSend = 0
    subNum = 0  #邮件内附件数量

    while numSend<totalnum or totalnum<=0:
        if subNum>9:
            letterID = send_message(cNo,sender,message)
            subNum = 0
        num_tmp = min(stkLimit,totalnum-numSend)
        num = num_tmp
        send()
        gold = 0
        subNum += 1
        numSend += num_tmp
        if totalnum<=0:
            break
    
def get_postal(cNo,ret='name'):
    sql = f'select postal_id,send_charac_name,receive_charac_no,item_id,avata_flag,creature_flag,add_info,gold,letter_id from postal' +\
        f' where receive_charac_no={cNo} and delete_flag=0 and item_id!=0;'
    results = execute_and_fetch('taiwan_cain_2nd',sql)
    res = []
    for postal_id,send_charac_name,receive_charac_no,item_id,avata_flag,creature_flag,num,*_ in results:
        if avata_flag==1:
            type = '时装'
        elif creature_flag==1:
            type = '宠物'
        else:
            type = '普通'
        item = cacheM.ITEMS_dict.get(item_id)
        if ret=='name':
            res.append([postal_id,item,decode(send_charac_name), type])
        elif ret=='id':
            res.append([postal_id,item_id,decode(send_charac_name), num])
    return res

def get_postal_new(cNo):
    sql = f'select postal_id,send_charac_name,receive_charac_no,item_id,avata_flag,creature_flag,add_info,gold,letter_id from postal' +\
        f' where receive_charac_no={cNo} and delete_flag=0 and item_id!=0;'
    results = execute_and_fetch('taiwan_cain_2nd',sql)
    res = []
    for postal_id,send_charac_name,receive_charac_no,item_id,avata_flag,creature_flag,num,*_ in results:
        if avata_flag==1:
            type = '时装'
        elif creature_flag==1:
            type = '宠物'
        else:
            type = '普通'
        item = cacheM.ITEMS_dict.get(item_id)
        res.append([postal_id,'itemName',item_id,decode(send_charac_name), num,type])
    return res


def get_current_quest_dict(cNo):
    sql = f'select * from new_charac_quest where charac_no={cNo};'
    res = execute_and_fetch('taiwan_cain',sql)
    if len(res)==0:
        return None
    cNo, clear_quest, quest_notify, *questList = res[0]
    i=0
    questList_ = []
    while i+2<len(questList):
        if i==20:
            i+=1
        questList_.append(questList[i:i+2])
        i+=2
    questDict = {
        'clear_quest':clear_quest, 'quest_notify':quest_notify, 'questList':questList_
    }
    
    return questDict

def set_quest_dict(cNo,questDict):
    clear_quest = questDict['clear_quest']
    quest_notify = questDict['quest_notify']
    questList = questDict['questList']
    questList_ = []
    for questID,trigger in questList:
        questList_.append(questID)
        questList_.append(trigger)
    questList = questList_
    sql = f'''update new_charac_quest set play_1={questList[0]}, play_1_trigger={questList[1]}, play_2={questList[2]}, play_2_trigger={questList[3]}, play_3={questList[4]}, play_3_trigger={questList[5]}, play_4={questList[6]}, play_4_trigger={questList[7]}, play_5={questList[8]}, play_5_trigger={questList[9]}, play_6={questList[10]}, play_6_trigger={questList[11]}, play_7={questList[12]}, play_7_trigger={questList[13]}, play_8={questList[14]}, play_8_trigger={questList[15]}, play_9={questList[16]}, play_9_trigger={questList[17]}, play_10={questList[18]}, play_10_trigger={questList[19]}, play_11={questList[20]}, play_11_trigger={questList[21]}, play_12={questList[22]}, play_12_trigger={questList[23]}, play_13={questList[24]}, play_13_trigger={questList[25]}, play_14={questList[26]}, play_14_trigger={questList[27]}, play_15={questList[28]}, play_15_trigger={questList[29]}, play_16={questList[30]}, play_16_trigger={questList[31]}, play_17={questList[32]}, play_17_trigger={questList[33]}, play_18={questList[34]}, play_18_trigger={questList[35]}, play_19={questList[36]}, play_19_trigger={questList[37]}, play_20={questList[38]}, play_20_trigger={questList[39]} where charac_no={cNo};'''

    execute_and_commit('taiwan_cain',sql)


def reset_dimension(cNo):
    sql = f'UPDATE `taiwan_cain`.`charac_dimension_inout` SET `dungeon1` = 6, `dungeon2` = 6, `dungeon3` = 6, `dungeon4` = 6, `dungeon5` = 6, `dungeon6` = 6, `dungeon7` = 6, `dungeon8` = 6, `dungeon9` = 6, `dungeon10` = 6 WHERE `charac_no` = {cNo};'
    execute_and_commit('taiwan_cain',sql)



def reset_blood_dungeon(cNo):
    sql = f'update charac_blood_dungeon_reward set enter_count=0 where charac_no={cNo}'
    execute_and_commit('taiwan_cain',sql)


def set_password(uid,password='123456'):
    passwdMD5 = md5(password.encode()).hexdigest()
    sql = f'update accounts set password=%s where UID={uid};'
    execute_and_commit('d_taiwan',sql,(passwdMD5,))


def del_cNos(cNos):
    for cNo in cNos:
        sql = f'update charac_info set delete_flag=1 where charac_no={cNo};'
        execute_and_commit('taiwan_cain',sql)

def recover_cNos(cNos):
    for cNo in cNos:
        sql = f'update charac_info set delete_flag=0 where charac_no={cNo};'
        execute_and_commit('taiwan_cain',sql)

def merge_dicts(dict1:dict, dict2:dict):
    '''递归合并字典到dict1'''
    for k,v in dict2.items():
        if isinstance(v,dict):
            if type(dict1.get(k))!=type(v):
                continue    #类型不同不合并
            dict1[k] = merge_dicts(dict1.get(k,{}),v)
        else:
            if k in dict1:
                if not isinstance(dict1[k],type(v)):
                    continue    #类型不同不合并
                if isinstance(v,list):
                    dict1[k] += v
            else:
                dict1[k] = v
            
                
from tkinter import messagebox

backup_batch_num = 3000
bak_db_num = 0
total_bak_db_num = 0
db_bak_stat = {}# db:{'bak':[...],'total':[...]} 表示备份进度

@inThread
def backup_db(db,bakPath):
    db_bak_dict = {}
    print(f'---{db}备份开始')
    tables = execute_and_fetch(db,'show tables;')
    db_bak_stat[db] = {'bak':[],'total':[table[0] for table in tables]}
    for table in tables:
        table = table[0]
        try:
            totalNum = execute_and_fetch(db,f'select count(*) from `{table}`;')[0][0]
            current_num = 0
            res = []
            while True:
                sql = f'select * from `{table}` limit {current_num},{backup_batch_num}'
                res_tmp = execute_and_fetch(db,sql)
                if len(res_tmp)==0:
                    break
                res += res_tmp
                current_num += backup_batch_num
                if current_num>=totalNum:
                    break
                print(f'    大型表单 {db} {table}备份进度 {current_num}/{totalNum}')
            tableDDL = execute_and_fetch(db,f'show create table `{table}`;')[0][1]
            db_bak_dict[table] = {'data':res,'DDL':tableDDL}
        except Exception as e:
            print(e)
            print(f'    {db} {table}备份失败')
        print(f'    {db} {table}备份完成')
        db_bak_stat[db]['bak'].append(table)
    db_bytes = zlib.compress(pickle.dumps(db_bak_dict))
    if os.path.exists(bakPath)==False:
        os.mkdir(bakPath)
    with open(os.path.join(bakPath,f'{db}.sqlbak'),'wb') as f:
        f.write(db_bytes)
    global bak_db_num,total_bak_db_num
    bak_db_num+=1
    print(f'==={db}备份完成 {bak_db_num}/{total_bak_db_num}')
    if bak_db_num==total_bak_db_num:
        print('全部备份完成')

db_restore_stat = {}# db:{'restored':[...],'total':[...]}
restore_db_num = 0
total_restore_db_num = 0
filedTableDict = {}
@inThread
def restore_db(db,bakPath='sql_backup'):
    def recover(dataPart,checkLen=False):
        #nonlocal recoveredNum
        #sql = ''
        sql = f'insert into `{table}` values '
        args = []
        for record in dataPart:
            sql += '('+','.join(['%s']*len(record))+'),'
            args.extend(record)
            if checkLen:
                if len(sql)>1000:
                    sql = sql[:-1]
                    execute_and_commit(db,sql,args)
                    sql = f'insert into `{table}` values '
                    args = []
        if sql[-1]==',':
            sql = sql[:-1]
            execute_and_commit(db,sql,args)

    fileName = f'{bakPath}/{db}.sqlbak'
    if os.path.exists(fileName)==False:
        print(f'{db}备份文件不存在')
        return
    with open(fileName,'rb') as f:
        db_bytes = f.read()
    db_bak_dict:dict = pickle.loads(zlib.decompress(db_bytes))
    errorTables = []
    for table,table_bak_dict in db_bak_dict.copy().items():
        if table_bak_dict.get('DDL')=='':
            errorTables.append(table)
            db_bak_dict.pop(table)
    if errorTables!=[]:
        print(f'{db}备份文件损坏，以下表无法恢复')
        print(errorTables)
        if not messagebox.askokcancel('提示',f'{db}备份文件不完整，该数据库以下表无法恢复，是否继续？\n{errorTables}'):
            return
    print(f'---{db}恢复开始')
    #print(db_bytes,db_all_dict)
    db_restore_stat[db] = {'restored':[],'total':list(db_bak_dict.keys())}

    sql = f'drop database if exists {db};'
    execute_and_commit('taiwan_cain',sql)
    sql = f'create database  IF NOT EXISTS {db};'
    execute_and_commit('taiwan_cain',sql)

    sql = "SET GLOBAL sql_mode='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'" # 允许0000-00-00 00:00:00
    execute_and_commit(db,sql)

    while len(db_bak_dict)>0:
        recovered_db_num = 0
        for table,table_bak_dict in db_bak_dict.copy().items():
            
            structList = table_bak_dict.get('struct',[])
            keyList = [struct[0] for struct in structList]
            del_key = 'delete_flag'
            if del_key in keyList:
                flag_index = keyList.index(del_key)
            else:
                flag_index = -1
            
            DDL:str = table_bak_dict.get('DDL')
            if DDL=='':
                print(f'{db}-{table} DDL为空')
                continue
            t = time.time()

            DDL = DDL.replace('CREATE TABLE','CREATE TABLE IF NOT EXISTS')
            DDL = DDL.replace("enum('m','f')","enum('m','f','')")
            execute_and_commit(db,DDL)

            sql = f'delete from `{table}`;'
            execute_and_commit(db,sql)

            # check if table is created
            sql = f'show tables;'
            res = execute_and_fetch(db,sql)
            tableList = [table[0] for table in res]
            if table not in tableList:
                continue    # 表因为外键创建失败，等待其他表创建完成后再次尝试

            if table in ['p2p_statistics','log_num_occupations','log_query_stat','log_game_channel',
                         'channel_lev_status','dnf_old_equip_info','dnf_item_info','random_option_ref'
                         ] or 'prod_sale_entry_' in table:
                pass  
            else:
                data = table_bak_dict.get('data',[])
                index = 0
                for i in range(0,len(data),backup_batch_num):
                    recover(data[i:i+backup_batch_num])
                    index += 1
            sql = f'select count(*) from `{table}`;'
            res = execute_and_fetch(db,sql)
            recoveredNum = res[0][0]
            print(f'    {db} {table} 恢复完成 {recoveredNum}')
            db_restore_stat[db]['restored'].append(table)
            db_bak_dict.pop(table)
            recovered_db_num += 1
        if recovered_db_num==0:
            print(f'\n\n\n\n\t\t\t\t{db}恢复失败,以下表未恢复')
            for table in db_bak_dict:
                print(db,table)
            filedTableDict[db] = list(db_bak_dict.keys())
            break
    global restore_db_num,total_restore_db_num
    restore_db_num+=1
    print(f'---{db}恢复完成 {restore_db_num}/{total_restore_db_num}')
    if restore_db_num==total_restore_db_num:
        print('全部恢复完成')
        if filedTableDict!={}:
            print('以下表未恢复')
            for db,tables in filedTableDict.items():
                print(db,tables)


def restore_all_db(bakPath='sql_backup'):
    files = os.listdir(bakPath)
    bakFiles = []
    for file in files:
        if file.endswith('.sqlbak'):
            bakFiles.append(file)
    global total_restore_db_num,restore_db_num
    total_restore_db_num = len(bakFiles)
    restore_db_num = 0
    for file in bakFiles:
        db = file[:-7]
        restore_db(db,bakPath)


def clear_all_table():
    db_list = ['taiwan_cain','taiwan_cain_2nd','taiwan_billing','d_taiwan','d_channel','d_guild','d_taiwan_secu','d_technical_report',
               'taiwan_cain_auction_gold','taiwan_cain_auction_cera','taiwan_cain_log','taiwan_cain_web','taiwan_game_event',
               'taiwan_mng_manager','taiwan_prod','taiwan_pvp','taiwan_se_event',]
    db_list = ['taiwan_siroco']
    allDB = execute_and_fetch('taiwan_cain','show databases;')
    allDB = [db[0] for db in allDB]
    db_avaliable = []
    for db in db_list:
        if db in allDB:
            db_avaliable.append(db)
    for db in db_avaliable:
        sql = f'show tables;'
        res = execute_and_fetch(db,sql)
        for table in res:
            table = table[0]
            sql = f'delete from {table};'
            execute_and_commit(db,sql)
            print(f'{db} {table}清空完成')
               





def connect(infoFunc=lambda x:...,conn=None): #多线程连接
    global  connectorAvailuableList, connectorUsed, connectorDict
    if len(connectorAvailuableList)>0:
        for connector in connectorAvailuableList:
            connector.close()
        for connector in connectorDict.values():
            connector.close()

        print(f'已关闭旧连接({len(connectorAvailuableList)})')
    connectorDict = {}
    connectorAvailuableList = []    #存储连接成功的数据库
    if conn is not None:
        connectorUsed = conn
        connectorAvailuableList.append(conn)
        return f'数据库连接成功({len(connectorAvailuableList)})'
    config = cacheM.config
    print(f'连接数据库（sqlmanager）')
    def innerThread():
        for i,connector_ in enumerate(SQL_CONNECTOR_LIST):
            try:
                db = connector_.connect(user=config['DB_USER'], password=config['DB_PWD'], host=config['DB_IP'], port=config['DB_PORT'],charset='utf8',autocommit=True,**SQL_CONNECTOR_IIMEOUT_KW_LIST[i])
                connectorAvailuableList.append(db)
                check_VIP_column()
                return True
            except Exception as e:
                infoFunc(str(e))
                print(f'连接失败，{str(connector_)}, {e}')

    t = threading.Thread(target=innerThread)
    t.setDaemon(True)
    t.start()
    t.join()
    if len(connectorAvailuableList)==0:
        print('所有连接器连接失败，详情查看日志')
        return '所有连接器连接失败，详情查看日志'
    else:
        connectorUsed = connectorAvailuableList[0]
        cacheM.config['DB_CONFIGS'][config['DB_IP']] ={
            'user':config['DB_USER'],
            'port':config['DB_PORT'],
            'pwd':config['DB_PWD']
        }
        cacheM.save_config()
        return f'数据库连接成功'


