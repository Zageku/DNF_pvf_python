import zlib
import struct
#from mysql import connector
import datetime
import pymysql_old as pymysql_old
import pymysql_new 
import json
import cacheManager as cacheM
from zhconv import convert
import time 
import threading
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
connectorUsed:pymysql_new.connections.Connection = None


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
        return self.increaseTypeDict.get(self.increaseType)

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
    items_bytes = zlib.decompress(fbytes[4:])
    num = len(items_bytes)//61
    result = []
    for i in range(num):
        item = DnfItemSlot(items_bytes[i*61:(i+1)*61])
        result.append([i, item])
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

def execute_and_fech(db,sql,charset='utf8'):
    connectorUsed.select_db(db)
    connectorUsed.set_charset(charset)
    cursor = connectorUsed.cursor()
    cursor.execute(sql)
    res = cursor.fetchall()
    return res
def execute_and_commit(db,sql,args=None,charset='utf8'):
    connectorUsed.select_db(db)
    connectorUsed.set_charset(charset)
    cursor = connectorUsed.cursor()
    if args is None:
        cursor.execute(sql)
    else:
        cursor.execute(sql,args)
    connectorUsed.commit()
    print(sql)

def getUID(username=''):
    if username=='':
        return -1
    sql = f"select UID from accounts where accountname='{username}';"
    res = execute_and_fech('d_taiwan',sql)
    if len(res)==0:
        print('未查询到记录')
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


def getCharactorInfo(cName='',uid=0):
    '''返回 编号，角色名，等级，职业，成长类型，删除状态'''
    connectorUsed.select_db('taiwan_cain')
    connectorUsed.set_charset('utf8')
    cursor = connectorUsed.cursor()

    if uid>=0:
        sql = f"select m_id, charac_no, charac_name, lev, job, grow_type, delete_flag, expert_job from charac_info where m_id='{uid}';"
        cursor.execute(sql)
        res = cursor.fetchall()
    elif uid==-1:
        res = get_all_charac()
        return res
    else:
        print(f'查询{cName}')
        name_new = cName.encode('utf-8','replace')
        sql = f"select m_id, charac_no, charac_name, lev, job, grow_type, delete_flag  from charac_info where charac_name=%s;"
        
        cursor.execute(sql,(name_new,))
        cursor.fetchall()
        name_tw = convert(cName,'zh-tw')
        if cName!=name_tw:
            name_tw_new = name_tw.encode('utf-8','replace')
            sql = f"select m_id, charac_no, charac_name, lev, job, grow_type, delete_flag from charac_info where charac_name=%s;"
            cursor.execute(sql,(name_tw_new,))
            res.extend(cursor.fetchall())
            print('角色名查询错误')
            return []
    res = decode_charac_list(res)
    print(f'角色列表加载完成')
    return res


def getCharactorNo(cName):
    name_new = cName.encode('utf-8').decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
    sql = f"select charac_no from charac_info where charac_name='{name_new}';"
    connectorUsed.select_db('taiwan_cain')
    cursor = connectorUsed.cursor()
    cursor.execute(sql)
    res = cursor.fetchall()

    name_tw = convert(cName,'zh-tw')
    if cName!=name_tw:
        name_tw_new = name_tw.encode('utf-8').decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
        sql = f"select charac_no from charac_info where charac_name='{name_tw_new}';"
        cursor.execute(sql)
        res.extend(cursor.fetchall())
    return res

def getCargoAll(cName='',cNo=0):
    '''获取仓库的blob字段'''
    if cNo==0:
        cNo = getCharactorNo(cName)[0][0]
    connectorUsed.select_db('taiwan_cain_2nd')
    cursor = connectorUsed.cursor()
    get_all_sql = f'select cargo,jewel,expand_equipslot from charac_inven_expand where charac_no={cNo};'
    cursor.execute(get_all_sql)
    results = cursor.fetchall()
    return results

def getInventoryAll(cName='',cNo=0):
    '''获取背包，穿戴槽，宠物栏的blob字段'''
    if cNo!=0:
        charac_no = cNo
    else:
        charac_no = getCharactorNo(cName)[0][0]
    connectorUsed.select_db('taiwan_cain_2nd')
    cursor = connectorUsed.cursor()
    get_all_sql = f'select inventory,equipslot,creature from inventory where charac_no={charac_no};'
    cursor.execute(get_all_sql)
    results = cursor.fetchall()
    return results

def getAvatar(cNo):
    getAvatarSql = f'select ui_id,it_id,ability_no from user_items where charac_no={cNo};'
    connectorUsed.select_db('taiwan_cain_2nd')
    cursor = connectorUsed.cursor()
    cursor.execute(getAvatarSql)
    results = cursor.fetchall()
    res = []
    for ui_id,it_id,ability_no in results:
        res.append([ui_id,cacheM.ITEMS_dict.get(it_id),it_id])
    return res

def getCreatureItem(cName='',cNo=0):
    '''获取宠物'''
    if cNo!=0:
        charac_no = cNo
    else:
        charac_no = getCharactorNo(cName)[0][0]
    get_creatures_sql = f'select ui_id,it_id,name from creature_items where charac_no={charac_no};'
    connectorUsed.select_db('taiwan_cain_2nd')
    cursor = connectorUsed.cursor()
    cursor.execute(get_creatures_sql)
    results = cursor.fetchall()
    #print(results)
    res = []
    for ui_id, it_id, cName in results:
        name_new = decode(cName)
        res.append([ui_id,cacheM.ITEMS_dict.get(it_id),it_id,name_new])
    return res

def get_online_charac():
    #loginCursor = connectorUsed.get('login_cursor')
    connectorUsed.select_db('taiwan_login')
    loginCursor = connectorUsed.cursor()

    get_login_account_sql = f'select m_id from login_account_3 where login_status=1'
    loginCursor.execute(get_login_account_sql)
    onlineAccounts = [item[0] for item in loginCursor.fetchall()]
    #print(onlineAccounts)
    connectorUsed.select_db('taiwan_game_event')
    gameCursor = connectorUsed.cursor()
    #gameCursor = connectorUsed['game_event_cursor']
    result = []
    for uid in onlineAccounts:
        sql = f'select charac_no from event_1306_account_reward where m_id={uid}'
        gameCursor.execute(sql)
        cNo = gameCursor.fetchall()[0][0]
        sql = f"select m_id, charac_no, charac_name, lev, job, grow_type, delete_flag, expert_job  from charac_info where charac_no={cNo};"
        connectorUsed.select_db('taiwan_cain')
        cursor = connectorUsed.cursor()
        cursor.execute(sql)
        res = list(cursor.fetchall()[0])
        result.append(res)
    #print(decode_charac_list(result))
    return decode_charac_list(result)

def get_VIP_charac(all=False):
    sql = f'select UID from accounts where VIP=1;'
    res = execute_and_fech('d_taiwan',sql)
    characs_list = []
    for uid in res:
        uid = uid[0]
        characs = getCharactorInfo(uid=uid)
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
        characs = getCharactorInfo(uid=uid)
        characs = list(filter(lambda x:x[-1]!=1,characs))   #去除删除掉的角色
        if len(characs)>0:
            if all==False:
                characs_list.append(characs[0])
            else:
                characs_list.extend(characs)
    return characs_list

def setInventory(InventoryBlob,cNo,key='inventory'):
    if key in ['inventory','equipslot', 'creature']: table = 'inventory'
    if key in ['cargo','jewel','expand_equipslot']: table = 'charac_inven_expand'
    if key in ['skill_slot']:table = 'skill'
    sql_update = f'''update {table} set {key}=%s where charac_no={cNo};'''
    print(sql_update % InventoryBlob)
    try:
        connectorUsed.select_db('taiwan_cain_2nd')
        cursor = connectorUsed.cursor()
        cursor.execute(sql_update,(InventoryBlob,))
        connectorUsed.commit()
        return True
    except:
        return False

def commit_change_blob(originBlob,editDict:dict,cNo,key):
    '''传入原始blob和修改的物品槽对象列表'''
    editList = list(editDict.items())
    blob_new = buildBlob(originBlob,editList)
    print(f'ID:{cNo}, {key}\n',unpackBLOB_Item(blob_new))
    return setInventory(blob_new,cNo,key)

def delCreatureItem(ui_id):
    try:
        sql = f'delete from creature_items where ui_id={ui_id};'
        print(sql)
        connectorUsed.select_db('taiwan_cain_2nd')
        cursor = connectorUsed.cursor()
        cursor.execute(sql)
        connectorUsed.commit()
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
        connectorUsed.select_db('taiwan_cain_2nd')
        cursor = connectorUsed.cursor()
        cursor.execute(sql)
        connectorUsed.commit()
        return True
    except:
        print(f'{tableName}删除失败')
        return False

def enable_Hidden_Item(ui_id,tableName='user_items',value=1):
    try:
        sql = f'update {tableName} set hidden_option={value} where ui_id={ui_id}'
        print(sql)
        connectorUsed.select_db('taiwan_cain_2nd')
        cursor = connectorUsed.cursor()
        cursor.execute(sql)
        connectorUsed.commit()
        return True
    except:
        return False

def cNo_2_uid(cNo):
    sql = f"select m_id from charac_info where charac_no='{cNo}';"
    connectorUsed.select_db('taiwan_cain')
    charactorCursor = connectorUsed.cursor()
    charactorCursor.execute(sql)
    try:
        uid = charactorCursor.fetchall()[0][0]
    except:
        uid = 0
    return uid

def set_VIP(cNo,value=1):
    sql = f"select m_id from charac_info where charac_no='{cNo}';"
    connectorUsed.select_db('taiwan_cain')
    charactorCursor = connectorUsed.cursor()
    charactorCursor.execute(sql)
    uid = charactorCursor.fetchall()[0][0]
    sql = f'update accounts set VIP={value} where UID={uid};'
    connectorUsed.select_db('d_taiwan')
    account_cursor = connectorUsed.cursor()
    account_cursor.execute(sql)
    print(sql)
    connectorUsed.commit()

def read_VIP(cNo):
    sql = f"select m_id from charac_info where charac_no='{cNo}';"
    connectorUsed.select_db('taiwan_cain')
    charactorCursor = connectorUsed.cursor()
    charactorCursor.execute(sql)
    uid = charactorCursor.fetchall()[0][0]
    sql = f'select VIP from accounts where UID={uid};'
    connectorUsed.select_db('d_taiwan')
    account_cursor = connectorUsed.cursor()
    account_cursor.execute(sql)
    VIP = account_cursor.fetchall()[0][0]
    if VIP == '':
        VIP = 0
    #print(f'uid:{uid},cNo:{cNo},VIP:{VIP}')
    return VIP

def set_charac_info(cNo,*args,**kw):
    for key,value in kw.items():
        try:
            if key=='charac_name':
                try:
                    value = value.encode('utf-8')#.decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
                except:
                    value = convert(value,'zh-tw').encode('utf-8')#.decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
                connectorUsed.set_charset('latin1')
            elif key=='lev':
                sql = f"select m_id,lev from charac_info where charac_no='{cNo}';"
                connectorUsed.select_db('taiwan_cain')
                
                charactorCursor = connectorUsed.cursor()
                charactorCursor.execute(sql)
                uID,lev = charactorCursor.fetchall()[0]
                if lev==value:
                    continue    #未进行等级调整
                sql_exp = f'update charac_stat set exp=%s where charac_no={cNo}'
                expTableList_with_lv0 = [0,0] + cacheM.expTableList
                exp = expTableList_with_lv0[value] + 1
                charactorCursor.execute(sql_exp,(exp,))
                connectorUsed.commit()
                print(sql_exp)
                sql_punish = f'delete from member_punish_info where m_id={uID};'
                connectorUsed.select_db('d_taiwan')
                account_cursor = connectorUsed.cursor()
                account_cursor.execute(sql_punish)
                connectorUsed.commit()
                print(sql_punish)
            elif key=='VIP':
                set_VIP(cNo,value)
                continue

            sql = f'update charac_info set {key}=%s where charac_no={cNo}'
            connectorUsed.select_db('taiwan_cain')
            charactorCursor = connectorUsed.cursor()
            charactorCursor.execute(sql,(value,))
            connectorUsed.commit()
            print(sql)
        except Exception as e:
            print(f'指令{key}-{value}执行失败，{e}')

def get_skill_sp(cNo):
    '''返回 remain_sp,remain_sp_2nd,remain_sfp_1st,remain_sfp_2nd '''
    sql = f'select remain_sp,remain_sp_2nd,remain_sfp_1st,remain_sfp_2nd from skill where charac_no={cNo};'
    sp = execute_and_fech('taiwan_cain_2nd',sql)
    return sp[0]
def set_skill_sp(cNo,sp,sp2,tp,tp2):
    sql = f'update skill set remain_sp={sp},remain_sp_2nd={sp2},remain_sfp_1st={tp},remain_sfp_2nd={tp2} where charac_no={cNo};'
    execute_and_commit('taiwan_cain_2nd',sql)


def get_quest_point(cNo):
    sql = f'select qp from charac_quest_shop where charac_no={cNo};'
    qp = execute_and_fech('taiwan_cain',sql)
    return qp[0][0]

def set_quest_point(cNo,qp):
    sql = f'update charac_quest_shop set qp={qp} where charac_no={cNo};'
    execute_and_commit('taiwan_cain',sql)

def set_cera(uid,value,type='crea'):
    if type=='cera':
        sql = f'update cash_cera set cera={value} where account={uid};'
    elif type=='cera_point':
        sql = f'update cash_cera_point set cera_point={value} where account={uid};'
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

def delete_mail_postal(postal_id):
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
    reg_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = f'insert into letter (charac_no,send_charac_no,send_charac_name,letter_text,reg_date,stat) ' +\
        f"values ({cNo},0,%s,%s,'{reg_time}',1);"
    execute_and_commit('taiwan_cain_2nd',sql,(sender.encode('utf-8'),message.encode('utf-8')),'latin1')
    sql = f"select letter_id from letter where reg_date='{reg_time}'"
    letterID = execute_and_fech('taiwan_cain_2nd',sql)
    return letterID[0][0]

def send_postal(cNo,letterID,sender='测试发件人',itemID=1000,increaseType=0,increaseValue=0,forgeLev=0,seal=0,num=1,enhanceValue=0,gold=1,avata_flag=0,creature_flag=0,endurance=10):
    occ_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = 'insert into postal (occ_time,send_charac_name,receive_charac_no,amplify_option,amplify_value,seperate_upgrade,seal_flag,item_id,add_info,upgrade,gold,letter_id,avata_flag,creature_flag,endurance,unlimit_flag) '+\
          f"values ('{occ_time}',%s,{cNo},{increaseType},{increaseValue},{forgeLev},{seal},{itemID},{num},{enhanceValue},{gold},{letterID},{avata_flag},{creature_flag},{endurance},1)"
    execute_and_commit('taiwan_cain_2nd',sql,(sender.encode(),),'latin1')
    
def get_postal(cNo):
    sql = f'select postal_id,send_charac_name,receive_charac_no,item_id,avata_flag,creature_flag,gold,letter_id from postal' +\
        f' where receive_charac_no={cNo} and delete_flag=0 and item_id!=0;'
    results = execute_and_fech('taiwan_cain_2nd',sql)
    res = []
    for postal_id,send_charac_name,receive_charac_no,item_id,avata_flag,creature_flag,*_ in results:
        if avata_flag==1:
            type = '时装'
        elif creature_flag==1:
            type = '宠物'
        else:
            type = '普通'
        item = cacheM.ITEMS_dict.get(item_id)
        res.append([postal_id,item,decode(send_charac_name), type])
    return res

def connect(infoFunc=lambda x:...): #多线程连接
    global  connectorAvailuableList, connectorUsed
    if len(connectorAvailuableList)>0:
        for connector in connectorAvailuableList:
            connector.close()
        print(f'已关闭旧连接({len(connectorAvailuableList)})')
    connectorAvailuableList = []    #存储连接成功的数据库
    connectorTestedNum = 0  #完成连接测试的数量
    config = cacheM.config
    def innerThread(i,connector_used):
        nonlocal  connectorTestedNum
        try:
            db = connector_used.connect(user=config['DB_USER'], password=config['DB_PWD'], host=config['DB_IP'], port=config['DB_PORT'], database='d_taiwan',charset='utf8',**SQL_CONNECTOR_IIMEOUT_KW_LIST[i])
            '''cursor = db.cursor()
            sql = 'set character_set_server=utf8;'
            cursor.execute(sql)
            sql = 'set character_set_database=utf8;'
            cursor.execute(sql)
            db.commit()'''
            connectorAvailuableList.append(db)
        except Exception as e:
            infoFunc(str(e))
            print(f'连接失败，{str(connector_used)}, {e}')
        finally:
            connectorTestedNum += 1
    for i,connector_ in enumerate(SQL_CONNECTOR_LIST):
        t = threading.Thread(target=innerThread,args=(i,connector_,))
        t.setDaemon(True)
        t.start()
    while connectorTestedNum<len(SQL_CONNECTOR_LIST):
        time.sleep(1)
    if len(connectorAvailuableList)==0:
        print('所有连接器连接失败，详情查看日志')
        return '所有连接器连接失败，详情查看日志'
    else:
        connectorUsed = connectorAvailuableList[0]
        json.dump(config,open(cacheM.configPath,'w'),ensure_ascii=False)
        print(f'数据库连接成功({len(connectorAvailuableList)})')
        return f'数据库连接成功({len(connectorAvailuableList)})'




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
    if not connect():
        input('数据库连接失败，请重新配置config.json文件')
        exit()
    loadItems2(True)
    print(f'数据库{cacheM.config["DB_IP"]}:{cacheM.config["DB_PORT"]}已连接')
    while True:
        cmd = input('====\n输入查询方式：\n【1】账户ID\n【2】角色名\n【0】退出\n>>>')
        if cmd=='1':
            account = input('====\n输入查询的账号名：')
            print('账户UID:',getUID(account))
            cInfos = getCharactorInfo(uid=getUID(account))
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
                cInfos = getCharactorInfo(cName)
                if len(cInfos)==0:
                    print('角色查询失败')
                    continue
                cInfo = cInfos[0]
                cNo = cInfo[0]
                print('全局编号，角色名，等级\n',cInfo)
                _test_selectDeleteInventry(cNo)
        elif cmd=='0':
            break


