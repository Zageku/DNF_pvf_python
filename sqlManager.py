import zlib
import struct
from mysql import connector
import pymysql_old as pymysql_old
import pymysql_new 
import json
import cacheManager as cacheM
from zhconv import convert
import time 
import threading
__version__ = ''
print(f'物品栏装备删除工具_CMD {__version__}\n\n')

ENCODE_AUTO = True  #为True时会在解码后自动修改编码索引，由GUI配置
ENCODE_ERROR = False #当解码名称出错时，该位置为True，否则为False 自动配置
DECODE_ERROR = False #用于将本地文字编码发送时的错误标志
SQL_ENCODE_LIST = ['latin1','windows-1252','big5','gbk','utf-8']
SQL_CONNECTOR_LIST = [pymysql_new,pymysql_old,connector,]
SQL_CONNECTOR_IIMEOUT_KW_LIST = [
    {'connect_timeout':2},
    {'connect_timeout':2},
    {'connection_timeout':2},
]
connectorAvailuableDictList = []
connectorUsed = {}
sqlEncodeUseIndex = 0

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

def getUID(username=''):
    sql = f"select UID from accounts where accountname='{username}';"
    connectorUsed['account_cursor'].execute(sql)
    res = connectorUsed['account_cursor'].fetchall()
    if len(res)==0:
        print('未查询到记录')
        return None
    return res[0][0]

def decode_charac_list(characList:list):
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
                        record[1] = record[1].encode(SQL_ENCODE_LIST[sqlEncodeUseIndex],errors='ignore').decode('utf-8',errors='ignore')
                        res_new.append(record)
            if len(res_new) == len(characList):
                break
    else:
        for i in characList:
            record = list(i)
            record[1] = record[1].encode(SQL_ENCODE_LIST[sqlEncodeUseIndex],errors='ignore').decode('utf-8',errors='ignore')
            res_new.append(record)
    
    return res_new


def getCharactorInfo(cName='',uid=0):
    '''返回 编号，角色名，等级，职业，成长类型，删除状态'''
    global  DECODE_ERROR
    if uid!=0:
        sql = f"select charac_no, charac_name, lev, job, grow_type, delete_flag from charac_info where m_id='{uid}';"
        connectorUsed['charactor_cursor'].execute(sql)
        res = connectorUsed['charactor_cursor'].fetchall()
    else:
        print(f'查询{cName}')
        name_new = cName.encode('utf-8')
        sql = f"select charac_no, charac_name, lev, job, grow_type, delete_flag  from charac_info where charac_name=%s;"
        
        connectorUsed['charactor_cursor'].execute(sql,(name_new,))
        res = list(connectorUsed['charactor_cursor'].fetchall())
        name_tw = convert(cName,'zh-tw')
        if cName!=name_tw:
            name_tw_new = name_tw.encode('utf-8')
            sql = f"select charac_no, charac_name, lev, job, grow_type, delete_flag from charac_info where charac_name=%s;"
            connectorUsed['charactor_cursor'].execute(sql,(name_tw_new,))
            res.extend(connectorUsed['charactor_cursor'].fetchall())
        try:
            DECODE_ERROR = False
        except:
            DECODE_ERROR = True
            print('角色名查询错误')
            return []
    res = decode_charac_list(res)
    print(f'角色列表加载完成')
    return res


def getCharactorNo(cName):
    name_new = cName.encode('utf-8').decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
    sql = f"select charac_no from charac_info where charac_name='{name_new}';"
    connectorUsed['charactor_cursor'].execute(sql)
    res = connectorUsed['charactor_cursor'].fetchall()

    name_tw = convert(cName,'zh-tw')
    if cName!=name_tw:
        name_tw_new = name_tw.encode('utf-8').decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
        sql = f"select charac_no from charac_info where charac_name='{name_tw_new}';"
        connectorUsed['charactor_cursor'].execute(sql)
        res.extend(connectorUsed['charactor_cursor'].fetchall())
    return res

def getCargoAll(cName='',cNo=0):
    '''获取仓库的blob字段'''
    if cNo==0:
        cNo = getCharactorNo(cName)[0][0]
    get_all_sql = f'select cargo,jewel,expand_equipslot from charac_inven_expand where charac_no={cNo};'
    connectorUsed['inventry_cursor'].execute(get_all_sql)
    results = connectorUsed['inventry_cursor'].fetchall()
    return results

def getInventoryAll(cName='',cNo=0):
    '''获取背包，穿戴槽，宠物栏的blob字段'''
    if cNo!=0:
        charac_no = cNo
    else:
        charac_no = getCharactorNo(cName)[0][0]
    get_all_sql = f'select inventory,equipslot,creature from inventory where charac_no={charac_no};'
    connectorUsed['inventry_cursor'].execute(get_all_sql)
    results = connectorUsed['inventry_cursor'].fetchall()
    return results

def getAvatar(cNo):
    getAvatarSql = f'select ui_id,it_id,ability_no from user_items where charac_no={cNo};'
    connectorUsed['inventry_cursor'].execute(getAvatarSql)
    results = connectorUsed['inventry_cursor'].fetchall()
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
    connectorUsed['inventry_cursor'].execute(get_creatures_sql)
    results = connectorUsed['inventry_cursor'].fetchall()
    #print(results)
    res = []
    for ui_id, it_id, cName in results:
        name_new = cName.encode('windows-1252',errors='ignore').decode(errors='ignore')
        res.append([ui_id,cacheM.ITEMS_dict.get(it_id),it_id,name_new])
    return res

def get_online_charac():
    loginCursor = connectorUsed.get('login_cursor')
    if loginCursor is None:
        return []

    get_login_account_sql = f'select m_id from login_account_3 where login_status=1'
    loginCursor.execute(get_login_account_sql)
    onlineAccounts = [item[0] for item in loginCursor.fetchall()]
    #print(onlineAccounts)
    gameCursor = connectorUsed['game_event_cursor']
    result = []
    for uid in onlineAccounts:
        sql = f'select charac_no from event_1306_account_reward where m_id={uid}'
        gameCursor.execute(sql)
        cNo = gameCursor.fetchall()[0][0]
        sql = f"select charac_no, charac_name, lev, job, grow_type, delete_flag  from charac_info where charac_no={cNo};"
        
        connectorUsed['charactor_cursor'].execute(sql)
        res = list(connectorUsed['charactor_cursor'].fetchall()[0])
        result.append(res)
    #print(decode_charac_list(result))
    return decode_charac_list(result)





def setInventory(InventoryBlob,cNo,key='inventory'):
    if key in ['inventory','equipslot', 'creature']: table = 'inventory'
    if key in ['cargo','jewel','expand_equipslot']: table = 'charac_inven_expand'
    if key in ['skill_slot']:table = 'skill'
    sql_update = f'''update {table} set {key}=%s where charac_no={cNo};'''
    print(sql_update % InventoryBlob)
    try:
        connectorUsed['inventry_cursor'].execute(sql_update,(InventoryBlob,))
        connectorUsed['inventry_db'].commit()
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
        connectorUsed['inventry_cursor'].execute(sql)
        connectorUsed['inventry_db'].commit()
        return True
    except:
        return False
    
def delNoneBlobItem(ui_id,tableName='creature_items'):
    try:
        sql = f'delete from {tableName} where ui_id={ui_id};'
        print(sql)
        connectorUsed['inventry_cursor'].execute(sql)
        connectorUsed['inventry_db'].commit()
        return True
    except:
        return False

def enable_Hidden_Item(ui_id,tableName='user_items',value=1):
    try:
        sql = f'update {tableName} set hidden_option={value} where ui_id={ui_id}'
        print(sql)
        connectorUsed['inventry_cursor'].execute(sql)
        connectorUsed['inventry_db'].commit()
        return True
    except:
        return False

def set_charac_info(cNo,*args,**kw):
    for key,value in kw.items():
        try:
            if key=='charac_name':
                try:
                    value = value.encode('utf-8')#.decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
                except:
                    value = convert(value,'zh-tw').encode('utf-8')#.decode(SQL_ENCODE_LIST[sqlEncodeUseIndex])
            if key=='lev':
                sql = f"select m_id,lev from charac_info where charac_no='{cNo}';"
                connectorUsed['charactor_cursor'].execute(sql)
                uID,lev = connectorUsed['charactor_cursor'].fetchall()[0]
                if lev==value:
                    continue    #未进行等级调整
                sql_exp = f'update charac_stat set exp=%s where charac_no={cNo}'
                expTableList_with_lv0 = [0,0] + cacheM.expTableList
                exp = expTableList_with_lv0[value] + 1
                connectorUsed['charactor_cursor'].execute(sql_exp,(exp,))
                connectorUsed['charactor_db'].commit()
                print(sql_exp)
                sql_punish = f'delete from member_punish_info where m_id={uID};'
                connectorUsed['account_cursor'].execute(sql_punish)
                connectorUsed['account_db'].commit()
                print(sql_punish)


            sql = f'update charac_info set {key}=%s where charac_no={cNo}'
            connectorUsed['charactor_cursor'].execute(sql,(value,))
            connectorUsed['charactor_db'].commit()
            print(sql)
        except Exception as e:
            print(f'指令{key}-{value}执行失败，{e}')


def connect(infoFunc=lambda x:...): #多线程连接
    global  connectorAvailuableDictList, connectorUsed
    if len(connectorAvailuableDictList)>0:
        for connector in connectorAvailuableDictList:
            for item in connector.values():
                item.close()
        print(f'已关闭旧连接({len(connectorAvailuableDictList)})')
    connectorAvailuableDictList = []    #存储连接成功的数据库dict
    connectorTestedNum = 0  #完成连接测试的数量
    config = cacheM.config
    def innerThread(i,connector_used):
        nonlocal  connectorTestedNum
        try:
            account_db = connector_used.connect(user=config['DB_USER'], password=config['DB_PWD'], host=config['DB_IP'], port=config['DB_PORT'], database='d_taiwan',**SQL_CONNECTOR_IIMEOUT_KW_LIST[i])
            account_cursor = account_db.cursor()
            inventry_db = connector_used.connect(user=config['DB_USER'], password=config['DB_PWD'], host=config['DB_IP'], port=config['DB_PORT'], database='taiwan_cain_2nd')
            inventry_cursor = inventry_db.cursor()
            charactor_db = connector_used.connect(user=config['DB_USER'], password=config['DB_PWD'], host=config['DB_IP'], port=config['DB_PORT'], database='taiwan_cain',charset='latin1')#
            charactor_cursor = charactor_db.cursor()
            login_db = connector_used.connect(user=config['DB_USER'], password=config['DB_PWD'], host=config['DB_IP'], port=config['DB_PORT'], database='taiwan_login')
            login_cursor = login_db.cursor()
            game_event_db = connector_used.connect(user=config['DB_USER'], password=config['DB_PWD'], host=config['DB_IP'], port=config['DB_PORT'], database='taiwan_game_event')
            game_event_cursor = game_event_db.cursor()
            sqlConnect = {
                'account_db':account_db,
                'account_cursor':account_cursor,
                'inventry_db':inventry_db,
                'inventry_cursor':inventry_cursor,
                'charactor_db':charactor_db,
                'charactor_cursor':charactor_cursor,
                'login_db':login_db,
                'login_cursor':login_cursor,
                'game_event_db':game_event_db,
                'game_event_cursor':game_event_cursor
            }
            connectorAvailuableDictList.append(sqlConnect)
            
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
    if len(connectorAvailuableDictList)==0:
        print('所有连接器连接失败，详情查看日志')
        return '所有连接器连接失败，详情查看日志'
    else:
        connectorUsed = connectorAvailuableDictList[0]
        json.dump(config,open(cacheM.configPath,'w'),ensure_ascii=False)
        print(f'数据库连接成功({len(connectorAvailuableDictList)})')
        return f'数据库连接成功({len(connectorAvailuableDictList)})'




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


