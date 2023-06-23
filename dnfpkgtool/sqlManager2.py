import zlib
import struct
#from mysql import connector
import datetime
if __name__=='__main__':
    import sys
    import os
    sys.path.append(os.getcwd())
import pymysql_old as pymysql_old
import pymysql_new 
import json
from dnfpkgtool import cacheManager as cacheM
from zhconv import convert
import time 
import threading
from hashlib import md5
__version__ = ''
#print(f'物品栏装备删除工具_CMD {__version__}\n\n')

ENCODE_AUTO = True  #为True时会在解码后自动修改编码索引，由GUI配置
SQL_ENCODE_LIST = ['混合','windows-1252','latin1','big5','gbk','utf-8']
sqlEncodeUseIndex = 0

SQL_CONNECTOR_LIST = [pymysql_new,pymysql_old,]
SQL_CONNECTOR_IIMEOUT_KW_LIST = [
    {'connect_timeout':2},
    {'connect_timeout':2},
    {'connection_timeout':2},
]
connectorAvailuableList = []
connectorDict = {}  #'DBNAME':pymysql_new.connections.Connection
connectorUsed:pymysql_new.connections.Connection = None

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
    def __init__(self,item_bytes:bytes) -> None:
        if len(item_bytes)<61:
            item_bytes = b'\x00'*61
        self.oriBytes = item_bytes
        self.isSeal = item_bytes[0]
        self.type = item_bytes[1]
        self.id = struct.unpack('I',item_bytes[2:6])[0]
        self.enhancementLevel = item_bytes[6]
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
        item_bytes += struct.pack('B',self.enhancementLevel)
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

def buildBlob(originBlob,editedDnfItemGridList):
    '''传入原始blob字段和需要修改的位置列表[ [1, DnfItemGrid对象], ... ]'''
    prefix = originBlob[:4]
    items_bytes = bytearray(zlib.decompress(originBlob[4:]))
    for i,itemGird in editedDnfItemGridList:
        items_bytes[i*61:i*61+61] = itemGird.build_bytes()
    blob = prefix + zlib.compress(items_bytes)
    return blob

def newConnector(db=''):
    global  connectorDict
    config = cacheM.config
    #print(f'newConnector {db}')
    for _ in range(2):
        for _,connector_ in enumerate(SQL_CONNECTOR_LIST):
            try:
                dbConn = connector_.connect(user=config['DB_USER'], password=config['DB_PWD'], host=config['DB_IP'], port=config['DB_PORT'], database=db,charset='utf8',autocommit=True,connect_timeout=2)
                connectorDict[db] = dbConn
                return True
            except Exception as e:
                pass
                #print(f'连接失败，{str(connector_)}, {e}')
    return False


# 调用exe_and_xxx后，生成一个id，将id和参数放入exec_queue，等待数据返回

execute_queue = []  #[(taskID,args,'fetch'/'commit'/None),...]
resDict = {}    # {id:res}

@inThread
def executor():
    global execute_queue
    while True:
        if len(execute_queue)>0:
            taskID,args,execType = execute_queue.pop(0)
            #print(taskID,args,execType)
            if execType=='fetch':
                resDict[taskID] = execute_fech(*args)
            elif execType=='commit':
                resDict[taskID] = execute_commit(*args)
            else:
                resDict[taskID] = execute(*args)
        else:
            time.sleep(0.01)
executor()
def execute(db,sql,args=None,charset='utf8',reConn=True):
    if connectorDict.get(db) is None:
        if not newConnector(db):
            print(db,sql,args)
            print(f'数据库{db}连接失败')
            return []
    try:
        connector:pymysql_new.connections.Connection = connectorDict[db]
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
        connector:pymysql_new.connections.Connection = connectorDict[db]
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
        connector:pymysql_new.connections.Connection = connectorDict[db]
        connector.set_charset(charset)
        cursor = connector.cursor()
        if args is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql,args)
        connector.commit()
        print(sql)
        return True
    except Exception as e:
        if reConn:
            #print(f'数据库{db}连接失败，尝试重新连接... 错误信息:{e}')
            connectorDict[db] = None
            return execute_commit(db,sql,args,charset,False)
    return False

def execute_and_fech(db,sql,args=None,charset='utf8'):
    taskID = str(time.time())
    #print(taskID)
    execute_queue.append((taskID,[db,sql,args,charset],'fetch'))
    while True:
        if resDict.get(taskID) is not None:
            res = resDict.pop(taskID)
            return res
        else:
            time.sleep(0.005)

def execute_and_commit(db,sql,args=None,charset='utf8'):
    taskID = str(time.time())
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
    res = execute_and_fech('d_taiwan',sql)
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


def getCharacterInfo(cName='',uid=0):
    '''返回 编号，角色名，等级，职业，成长类型，删除状态'''
    if uid>=0 and cName=='':
        sql = f"select m_id, charac_no, charac_name, lev, job, grow_type, delete_flag, expert_job from charac_info where m_id='{uid}';"
        res = execute_and_fech('taiwan_cain',sql)
    elif uid==-1:
        res = get_all_charac()
        return res
    else:
        #print(f'查询{cName}')
        name_new = cName.encode('utf-8','replace')
        sql = f"select m_id, charac_no, charac_name, lev, job, grow_type, delete_flag, expert_job  from charac_info where charac_name=%s;"  
        res = list(execute_and_fech('taiwan_cain',sql,(name_new,),'latin1'))
        res.extend(execute_and_fech('taiwan_cain',sql,(name_new,),'utf-8'))

        name_tw = convert(cName,'zh-tw')
        if cName!=name_tw:
            name_tw_new = name_tw.encode('utf-8','replace')
            sql = f"select m_id, charac_no, charac_name, lev, job, grow_type, delete_flag, expert_job from charac_info where charac_name=%s;"
            res.extend(execute_and_fech('taiwan_cain',sql,(name_tw_new,),'latin1'))
            res.extend(execute_and_fech('taiwan_cain',sql,(name_tw_new,),'utf-8'))
    res = decode_charac_list(res)
    #print(f'角色列表加载完成')
    return res


def getCharactorNo(cName):
    name_new = cName.encode('utf-8').decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
    sql = f"select charac_no from charac_info where charac_name='{name_new}';"
    res = execute_and_fech('taiwan_cain',sql)

    name_tw = convert(cName,'zh-tw')
    if cName!=name_tw:
        name_tw_new = name_tw.encode('utf-8').decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
        sql = f"select charac_no from charac_info where charac_name='{name_tw_new}';"
        res_tmp = execute_and_fech('taiwan_cain',sql)
        res.extend(res_tmp)
    return res

def getCargoAll(cName='',cNo=0):
    '''获取仓库的blob字段'''
    if cNo==0:
        cNo = getCharactorNo(cName)[0][0]
    get_all_sql = f'select cargo,jewel,expand_equipslot from charac_inven_expand where charac_no={cNo};'
    res = execute_and_fech('taiwan_cain_2nd',get_all_sql)

    return res

def get_Account_Cargo(uid=0,cNo=0):
    if uid==0:
        uid = cNo_2_uid(cNo)
    sql = f'select cargo from account_cargo where m_id={uid}'
    cargoBlob = execute_and_fech('taiwan_cain',sql)
    if len(cargoBlob)>0:
        cargoBlob = cargoBlob[0][0]
    return cargoBlob



def getInventoryAll(cName='',cNo=0):
    '''获取背包，穿戴槽，宠物栏的blob字段'''
    if cNo!=0:
        charac_no = cNo
    else:
        charac_no = getCharactorNo(cName)[0][0]

    get_all_sql = f'select inventory,equipslot,creature from inventory where charac_no={charac_no};'
    res = execute_and_fech('taiwan_cain_2nd',get_all_sql)

    return res

def getAvatar(cNo,ability_=False):
    getAvatarSql = f'select ui_id,it_id,hidden_option from user_items where charac_no={cNo};'

    results = execute_and_fech('taiwan_cain_2nd',getAvatarSql)
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
    results = execute_and_fech('taiwan_cain_2nd',get_creatures_sql)

    #print(results)
    res = []
    for ui_id, it_id, cName in results:
        name_new = decode(cName)
        res.append([ui_id,cacheM.ITEMS_dict.get(it_id),it_id,name_new])
    return res

def get_online_charac():


    get_login_account_sql = f'select m_id from login_account_3 where login_status=1'
    res = execute_and_fech('taiwan_login',get_login_account_sql)
    onlineAccounts = [item[0] for item in res]
    result = []
    for uid in onlineAccounts:
        sql = f'select charac_no from event_1306_account_reward where m_id={uid}'
        cNo = execute_and_fech('taiwan_game_event',sql)[0][0]
        #cNo = gameCursor.fetchall()[0][0]
        sql = f"select m_id, charac_no, charac_name, lev, job, grow_type, delete_flag, expert_job  from charac_info where charac_no={cNo};"
        res = execute_and_fech('taiwan_cain',sql)
        res = list(res[0])
        result.append(res)
    return decode_charac_list(result)

VIP_KEY = 'VIP'
def check_VIP_column():
    global VIP_KEY
    
    sql = f'''select column_name,data_type from information_schema.columns where table_schema='d_taiwan' and table_name='accounts';'''
    res = execute_and_fech('d_taiwan',sql)
    for column_name,data_type in res:
        if column_name.lower()=='vip':
            VIP_KEY = column_name
            return
    sql = 'ALTER TABLE accounts ADD VIP INT(1) NOT NULL DEFAULT 0;'
    execute_and_commit('d_taiwan',sql)

def get_VIP_charac(all=False):
    sql = f'select UID from accounts where {VIP_KEY}=1;'
    res = execute_and_fech('d_taiwan',sql)
    characs_list = []
    for uid in res:
        uid = uid[0]
        characs = getCharacterInfo(uid=uid)
        characs = list(filter(lambda x:x[-1]!=1,characs))   #去除删除掉的角色
        if all==False:
            characs_list.append(characs[0])
        else:
            characs_list.extend(characs)
    return characs_list

def get_all_charac():
    sql = f'select UID from accounts;'
    res = execute_and_fech('d_taiwan',sql)
    characs_list = []
    for uid in res:
        uid = uid[0]
        characs = getCharacterInfo(uid=uid)
        characs = list(filter(lambda x:x[-2]!=1,characs))   #去除删除掉的角色
        if len(characs)>0:
            if all==False:
                characs_list.append(characs[0])
            else:
                characs_list.extend(characs)
    return characs_list

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
        uid = execute_and_fech('taiwan_cain',sql)[0][0]
    except:
        uid = 0
    return uid

def set_VIP(cNo,value=1):
    sql = f"select m_id from charac_info where charac_no='{cNo}';"
    uid = execute_and_fech('taiwan_cain',sql)[0][0]
    sql = f'update accounts set {VIP_KEY}={value} where UID={uid};'
    execute_and_commit('d_taiwan',sql)

def read_VIP(cNo):
    sql = f"select m_id from charac_info where charac_no='{cNo}';"
    uid = execute_and_fech('taiwan_cain',sql)[0][0]
    sql = f'select VIP from accounts where UID={uid};'
    VIP = execute_and_fech('d_taiwan',sql)[0][0]
    if VIP == '':
        VIP = 0
    return VIP

def read_return_user(cNo):
    uid = cNo_2_uid(cNo)
    sql = 'select m_id,expire_time from return_user'
    res = execute_and_fech('taiwan_game_event',sql)
    
    for m_id,expire_time in res:
        time_old = time.strptime(str(expire_time), r"%Y-%m-%d %H:%M:%S")
        if m_id==uid and time.localtime()<time_old:
            return True 
    return False

def set_return_user(cNo):
    uid = cNo_2_uid(cNo)
    sql = f'select m_id,expire_time from return_user where m_id={uid}'
    res = execute_and_fech('taiwan_game_event',sql)
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
    res = execute_and_fech('d_taiwan',sql)
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
    res = execute_and_fech('d_taiwan',sql)
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
    res = execute_and_fech('taiwan_login',sql)
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
                    value = value.encode(ENCODE)#.decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
                except:
                    value = convert(value,'zh-tw').encode(ENCODE)#.decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
                charSet = 'latin1'
                #connectorUsed.set_charset('latin1')
            elif key=='lev':
                sql = f"select m_id,lev from charac_info where charac_no='{cNo}';"
                uID,lev = execute_and_fech('taiwan_cain',sql)[0]
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
    res = execute_and_fech('taiwan_cain',sql)
    if len(res)==0:
        return 0
    return res[0][0]

def set_charac_money(cNo,money):
    sql = f'update inventory set money={money} where charac_no={cNo};'
    execute_and_commit('taiwan_cain_2nd',sql)

def get_charac_money(cNo):
    sql = f'select money from inventory where charac_no={cNo};'
    res = execute_and_fech('taiwan_cain_2nd',sql)
    return res[0][0]

def set_pay_coin(cNo,paycoin):
    sql = f'update inventory set pay_coin={paycoin} where charac_no={cNo};'
    execute_and_commit('taiwan_cain_2nd',sql)

def get_pay_coin(cNo):
    sql = f'select pay_coin from inventory where charac_no={cNo};'
    res = execute_and_fech('taiwan_cain_2nd',sql)
    return res[0][0]

def get_skill_sp(cNo):
    '''返回 remain_sp,remain_sp_2nd,remain_sfp_1st,remain_sfp_2nd '''
    sql = f'select remain_sp,remain_sp_2nd,remain_sfp_1st,remain_sfp_2nd from skill where charac_no={cNo};'
    sp = execute_and_fech('taiwan_cain_2nd',sql)
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
    qp = execute_and_fech('taiwan_cain',sql)
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
    cera = execute_and_fech('taiwan_billing',sql)[0][0]
    sql = f'select cera_point from cash_cera_point where account={uid}'
    cera_point = execute_and_fech('taiwan_billing',sql)[0][0]
    return cera,cera_point

def get_PVP(cNo):
    sql = f'select pvp_grade,win,pvp_point,win_point from pvp_result where charac_no={cNo}'
    res = execute_and_fech('taiwan_cain',sql)
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
    res = execute_and_fech('taiwan_cain_2nd',sql)
    return res

def delete_mail_postal(postal_id):
    sql = f'select item_id,avata_flag,creature_flag,add_info,letter_id from postal' +\
        f' where postal_id={postal_id};'
    item_id,avata_flag,creature_flag,add_info,letter_id = execute_and_fech('taiwan_cain_2nd',sql)[0]
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
    res = execute_and_fech('d_taiwan',sql)
    return res

def set_event(event_id,para1,para2=0):
    sql = f'insert into dnf_event_log (occ_time,event_type,parameter1,parameter2,server_id,event_flag,start_time,end_time) values (0,{event_id},{para1},{para2},0,0,0,0)'
    execute_and_commit('d_taiwan',sql)

def del_event(event_log_id):
    sql = f'delete from dnf_event_log where log_id={event_log_id};'
    execute_and_commit('d_taiwan',sql)

def get_event_running():
    sql = 'select log_id,event_type,parameter1,parameter2 from dnf_event_log;'
    res = execute_and_fech('d_taiwan',sql)
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
    letterID = execute_and_fech('taiwan_cain_2nd',sql)
    return letterID[-1][0]

def send_postal(cNo,letterID=0,sender='测试发件人',message='测试邮件',itemID=1000,increaseType=0,increaseValue=0,forgeLev=0,seal=0,totalnum=1,enhanceValue=0,gold=0,avata_flag=0,creature_flag=0,endurance=0):
    def send():
        nonlocal num
        occ_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if avata_flag==1:
            sql = f"insert into taiwan_cain_2nd.user_items (charac_no,it_id,expire_date,obtain_from,reg_date,stat) values ({cNo},{itemID},'9999-12-31 23:59:59',1,'{occ_time}',2)"
            execute_and_commit('taiwan_cain_2nd',sql)
            sql = f"select ui_id from user_items where charac_no={cNo} and it_id={itemID} and reg_date='{occ_time}';"
            ui_id = execute_and_fech('taiwan_cain_2nd',sql)[0][0]
            num = ui_id
        elif creature_flag==1:
            sql = f"insert into taiwan_cain_2nd.creature_items (charac_no,it_id,expire_date,reg_date,stat,item_lock_key,creature_type) values ({cNo},{itemID},'9999-12-31 23:59:59','{occ_time}',1,1,1)"
            execute_and_commit('taiwan_cain_2nd',sql)
            sql = f"select ui_id from creature_items where charac_no={cNo} and it_id={itemID} and reg_date='{occ_time}';"
            ui_id = execute_and_fech('taiwan_cain_2nd',sql)[0][0]
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
    results = execute_and_fech('taiwan_cain_2nd',sql)
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
    results = execute_and_fech('taiwan_cain_2nd',sql)
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

def reset_blood_dungeon(cNo):
    sql = f'update charac_blood_dungeon_reward set enter_count=0 where charac_no={cNo}'
    execute_and_commit('taiwan_cain',sql)


def set_password(uid,password='123456'):
    passwdMD5 = md5(password.encode()).hexdigest()
    sql = f'update accounts set password=%s where UID={uid};'
    execute_and_commit('d_taiwan',sql,(passwdMD5,))

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
    print('连接数据库（sqlmanager）')
    def innerThread():
        for i,connector_ in enumerate(SQL_CONNECTOR_LIST):
            try:
                db = connector_.connect(user=config['DB_USER'], password=config['DB_PWD'], host=config['DB_IP'], port=config['DB_PORT'], database='d_taiwan',charset='utf8',autocommit=True,**SQL_CONNECTOR_IIMEOUT_KW_LIST[i])
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


if __name__=='__main__':
    from cacheManager import loadItems2
    def _test_selectDeleteInventry(cNo):
        while True:
            sel = input('====\n选择以下内容进行处理：\n【1】物品栏 Inventory\n【2】装备栏 Equipslot\n【3】宠物栏 Creature\n【4】宠物 Creature_items\n【5】仓库 Cargo\n【0】返回上一级\n>>>')
            inventory, equipslot, creature = getInventoryAll(cNo=cNo)[0]
            cargo,jewel,expand_equipslot = getCargoAll(cNo=cNo)[0]
            creature_items = getCreatureItem(cNo=cNo)
            if sel=='1': selected_blob = inventory;key = 'inventory'
            elif sel=='2':selected_blob = equipslot;key = 'equipslot'
            elif sel=='3':selected_blob = creature; key = 'creature'
            elif sel=='4':...
            elif sel=='5':selected_blob = cargo; key = 'cargo'
            elif sel=='0':return True
            else: continue
        
            while sel in ['1','2','3','5']:
                items = unpackBLOB_Item(selected_blob)
                print(f'====\n该角色{key}物品信息({len(items)})：\n位置编号，物品名，物品ID')
                for item in items:
                    print(item)
                print('输入需要删除的物品编号，输入非数字时结束输入：')
                dels = []
                while True:
                    try:
                        dels.append(int(input('>>>')))
                    except:
                        break
                print('结束输入，当前待删除列表为：')
                for item in items:
                    if item[0] in dels:
                        print(item)
                    else:
                        continue
            
                delcmd = input('输入选项：\n【1】确定删除\n【2】重新设置删除列表\n【0】返回上一级\n>>>')
                if delcmd=='1':
                    InventoryBlob_new = buildDeletedBlob2(dels,selected_blob)
                    if setInventory(InventoryBlob_new,cNo,key):
                        print('====删除成功====\n')
                    else:
                        print('====删除失败，请检查数据库连接状况====\n')
                    break
                elif delcmd=='2':
                    continue
                elif delcmd=='0':
                    break
        
            while sel in ['4']:
                items = creature_items
                print(f'====\n该角色宠物信息({len(items)})：\n宠物编号，宠物名，宠物ID，宠物昵称')
                for item in items:
                    print(item)
                print('输入需要删除的宠物编号，输入非数字时结束输入：')
                dels = []
                while True:
                    try:
                        dels.append(int(input('>>>')))
                    except:
                        break
                print('结束输入，当前待删除列表为：')
                dels_fix = []
                for item in items:
                    if item[0] in dels:
                        print(item)
                        dels_fix.append(item[0])
                    else:
                        continue
            
                delcmd = input('输入选项：\n【1】确定删除\n【2】重新设置删除列表\n【0】返回上一级\n>>>')
                if delcmd=='1':
                    for ui_id in dels_fix:
                        if delNoneBlobItem(ui_id,tableName='creature_items'):
                            print('====删除成功====\n')
                        else:
                            print('====删除失败====\n')
                    break
                elif delcmd=='2':
                    continue
                elif delcmd=='0':
                    break
    
    def main():
        get_Account_Cargo(8)
        while True:
            cmd = input('====\n输入查询方式：\n【1】账户ID\n【2】角色名\n【0】退出\n>>>')
            if cmd=='1':
                account = input('====\n输入查询的账号名：')
                print('账户UID:',getUID(account))
                cInfos = getCharacterInfo(uid=getUID(account))
                while len(cInfos)>0:
                    print(f'账户{account}拥有角色：\n全局编号，角色名，等级')
                    valid_cNos = [item[0] for item in cInfos]
                    for i in range(len(cInfos)):
                        print(cInfos[i])
                    cNo = input('====\n输入查询角色的全局编号，输入【0】返回上一级：\n>>>')
                    if cNo=='0':
                        break
                    try:
                        cNo = int(cNo)
                    except:
                        continue
                    if cNo not in valid_cNos:
                        print('输入的角色编号错误')
                        continue
                    _test_selectDeleteInventry(cNo)
            elif cmd=='2':
                while True:
                    cName = input('====\n输入查询的角色名，直接输入回车返回上级：\n>>>')
                    if cName=='':break
                    cInfos = getCharacterInfo(cName)
                    if len(cInfos)==0:
                        print('角色查询失败')
                        continue
                    cInfo = cInfos[0]
                    cNo = cInfo[0]
                    print('全局编号，角色名，等级\n',cInfo)
                    _test_selectDeleteInventry(cNo)
            elif cmd=='0':
                break
    cacheM.config['DB_IP'] = '192.168.4.15'

    if '成功' not in connect():
        input('数据库连接失败，请重新配置config.json文件')
        exit()
    loadItems2(True)
    print(f'数据库{cacheM.config["DB_IP"]}:{cacheM.config["DB_PORT"]}已连接')
    res = getCharacterInfo(cName='刀刀刀')
    print(res)
    

