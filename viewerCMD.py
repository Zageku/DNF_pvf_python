import zlib
import struct
from pathlib import Path
import csv
from mysql import connector
from mysql.connector.locales.eng import client_error
import json
import pvfReader
from zhconv import convert
import hashlib
import pickle
import re
__version__ = '0.2.16'
print(f'物品栏装备删除工具_CMD V{__version__}\n\n')
configPath = './config.json'
pvfCachePath = './pvf.cache'
fcgPath = Path(configPath)
cache = Path(pvfCachePath)
if fcgPath.exists():
    config = json.load(open(configPath,'r'))
else:
    config = {
        'DB_IP' : '192.168.200.131',
        'DB_PORT' : 3306,
        'DB_USER' : 'game',
        'DB_PWD' : '123456',
        'PVF_PATH': 'Script.pvf',
        'TEST_ENABLE': 1
    }
    json.dump(config,open(configPath,'w'))

PVFcacheDicts = {}
if cache.exists():
    try:
        with open(pvfCachePath,'rb') as pvfFile:
            cacheCompressed = pvfFile.read()
            PVFcacheDicts:dict = pickle.loads(zlib.decompress(cacheCompressed))
    except:
        pass

positionDict = {
    0x00:['快捷栏',[3,9]],
    0x01:['装备栏',[9,57]],
    0x02:['消耗品',[57,105]],
    0x03:['材料',[105,153]],
    0x04:['任务材料',[153,]],
    0x05:['宠物',[98,99]],#正在使用的宠物
    0x06:['宠物装备',[0,49],[99,102]],#装备栏和正在使用的装备
    0x07:['宠物消耗品',[49,98]],
    0x0a:['副职业',[201,249]]
}

class DnfItemSlot():
    '''物品格子对象，存储格子信息'''
    typeDict ={
        0x00:'已删除',
        0x01:'装备',
        0x02:'消耗品',
        0x03:'材料',
        0x04:'任务材料',
        0x05:'宠物',
        0x06:'宠物装备',
        0x07:'宠物消耗品',
        0x0a:'副职业'
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
        #self.typeZh = self.typeDict.get(self.type)
        self.id = struct.unpack('I',item_bytes[2:6])[0]
        self.enhancementLevel = item_bytes[6]
        self.num_grade = struct.unpack('i',item_bytes[7:11])[0]
        self.durability = struct.unpack('H',item_bytes[11:13])[0]
        self.orb_bytes = item_bytes[13:17]
        self.increaseType = item_bytes[17]
        #self.increaseTypeZh = self.increaseTypeDict.get(self.increaseType)
        self.increaseValue = struct.unpack('H',item_bytes[18:20])[0]
        self._others20_30 = item_bytes[20:31]
        self.otherworld = item_bytes[31:33]#struct.unpack('H',item_bytes[31:33])[0]
        self._others32_36 = item_bytes[33:37]
        self.magicSeal = item_bytes[37:51]
        self.forgeLevel = item_bytes[51]
        self._others = item_bytes[52:]
    
    @property
    def typeZh(self):
        return self.typeDict.get(self.type)
    
    @property
    def increaseTypeZh(self):
        return self.increaseTypeDict.get(self.increaseType)

    def build_bytes(self):
        item_bytes = b''
        if self.id==0:
            item_bytes = b'\x00'*61
            return item_bytes
        item_bytes += struct.pack('B',self.isSeal)
        item_bytes += struct.pack('B',self.type)
        item_bytes += struct.pack('I',self.id)
        item_bytes += struct.pack('B',self.enhancementLevel)
        #print(self.num_grade)
        item_bytes += struct.pack('i',self.num_grade)
        item_bytes += struct.pack('H',self.durability)
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
        s = f'[{self.typeDict.get(self.type)}]{ITEMS_dict.get(self.id)} '
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



def __unpackBlob_skill(fbytes):
    items_bytes = zlib.decompress(fbytes[4:])
    num = len(items_bytes)//2
    result = []
    for i in range(num):
        skillID,skilllevel = struct.unpack('BB',items_bytes[i*2:(i+1)*2])
        result.append([skillID,skilllevel])
    return result


def unpackBLOB_Item(fbytes):
    '''返回[index, DnfItemGrid对象]'''
    items_bytes = zlib.decompress(fbytes[4:])
    num = len(items_bytes)//61
    result = []
    for i in range(num):
        if items_bytes[i*61:(i+1)*61] == b'\x00'*61:continue
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

ITEMS = []
ITEMS_dict = {}
PVFcacheDict = {}

PVFOKflg = False

def getItemInfo(itemID:int):
    if PVFOKflg == True:
        stringtable = PVFcacheDict['stringtable']
        nString = PVFcacheDict['nstring']
        idPathContentDict = PVFcacheDict['idPathContentDict']
        try:
            res = pvfReader.TinyPVF.content2List(idPathContentDict[itemID],stringtable,nString)
        except:
            res = '','无此id记录'
    else:
        res =  'type',['']
    return res

def loadItems2(usePVF=False,pvfPath='',showFunc=lambda x:print(x),MD5='0'):        
    global ITEMS, ITEMS_dict, PVFOKflg, PVFcacheDict
    ITEMS = []
    ITEMS_dict = {}
    if pvfPath=='':
        pvfPath = config['PVF_PATH']
    
    if usePVF :
        p = Path(pvfPath)
        if  MD5 in PVFcacheDicts.keys():
            if PVFcacheDicts.get(MD5) is not None:
                PVFcacheDict = PVFcacheDicts.get(MD5)
                ITEMS_dict = PVFcacheDict['ITEMS_dict']
                info = f'加载pvf缓存获得{len(ITEMS_dict.keys())}条物品信息记录 {pvfPath}'   #{len(ITEMS_dict.keys())}
                #loadPvfTree_Thread()
                config['PVF_PATH'] = MD5
                PVFOKflg = True

        elif  p.exists():#os.path.exists(pvfPath):
            MD5 = hashlib.md5(open(pvfPath,'rb').read()).hexdigest().upper()
            if MD5 not in PVFcacheDicts.keys():
                pvf = pvfReader.FileTree(pvfHeader=pvfReader.PVFHeader(pvfPath))
                print('加载PVF中...\n',pvf.pvfHeader)
                pvf.loadLeafs(['stackable','equipment'])
                print('PVF加载文件数：',pvf._fileNum)
                showFunc('PVF加载即将完成...')
                stackable_dict = pvfReader.getItemDict(pvf)
                PVFcacheDict = {}
                PVFcacheDict['stringtable'] = pvf.stringtable
                PVFcacheDict['nstring'] = pvf.nStringTableLite
                PVFcacheDict['idPathContentDict'] = stackable_dict.pop('idPathContentDict')
                PVFcacheDict['ITEMS_dict'] = stackable_dict
                
                ITEMS_dict = stackable_dict
                info = f'加载pvf文件获得{len(ITEMS_dict.keys())}条物品信息记录'
                PVFcacheDicts[MD5] = PVFcacheDict
                pvfFile = open(pvfCachePath,'wb')
                cacheCompressed = zlib.compress(pickle.dumps(PVFcacheDicts))
                pvfFile.write(cacheCompressed)
                pvfFile.close()
                #loadPvfTree_Thread()
                print(f'pvf cache saved. {PVFcacheDict.keys()}')
                PVFOKflg = True
                
            else:
                PVFcacheDict = PVFcacheDicts.get(MD5)
                ITEMS_dict = PVFcacheDict['ITEMS_dict']
                info = f'加载pvf缓存获得{len(ITEMS_dict.keys())}条物品信息记录 {pvfPath}'   #{len(ITEMS_dict.keys())}
                #loadPvfTree_Thread()
                PVFOKflg = True
            config['PVF_PATH'] = MD5
        else:
            info = 'PVF文件路径错误'
    else:
        csvList = list(filter(lambda item:item[-4:].lower()=='.csv',[item.name for item in Path('./').iterdir()]))
        print(f'物品文件列表:',csvList)
        for fcsv in csvList:
            csv_reader = list(csv.reader(open(fcsv,encoding='utf-8',errors='ignore')))[1:]
            ITEMS.extend(csv_reader)
        for item in ITEMS:
            if len(item)!=2:
                print(item)
            else:
                try:
                    ITEMS_dict[int(item[1])] = item[0]
                except:
                    print(item, '该条记录处理错误。')
        info = f'加载csv文件获得{len(ITEMS)}条物品信息记录'
    print(info)
    for key,value in ITEMS_dict.items():
        try:
            ITEMS_dict[key] = convert(value,'zh-cn')
        except:
            ITEMS_dict[key] = value
    ITEMS = list(ITEMS_dict.items())
    json.dump(config,open(configPath,'w'))
    return info

def getUID(username=''):
    sql = f"select UID from accounts where accountname='{username}';"
    account_cursor.execute(sql)
    res = account_cursor.fetchall()
    if len(res)==0:
        print('未查询到记录')
        return None
    return res[0][0]

def getCharactorInfo(name='',uid=0):
    '''返回 编号，角色名，等级'''
    if uid!=0:
        sql = f"select * from charac_info where m_id='{uid}';"
        charactor_cuesor.execute(sql)
        res = charactor_cuesor.fetchall()
    else:
        name_new = name.encode('utf-8').decode('latin1')
        sql = f"select * from charac_info where charac_name='{name_new}';"
        charactor_cuesor.execute(sql)
        res = charactor_cuesor.fetchall()
        name_tw = convert(name,'zh-tw')
        if name!=name_tw:
            name_tw_new = name_tw.encode('utf-8').decode('latin1')
            sql = f"select * from charac_info where charac_name='{name_tw_new}';"
            charactor_cuesor.execute(sql)
            res.extend(charactor_cuesor.fetchall())
    res_new = []
    for i in res:
        record = list(i)
        record[2] = record[2].encode('latin1').decode('utf-8')
        res_new.append(record[1:3]+record[5:6])
    return res_new

def getCharactorNo(name):
    name_new = name.encode('utf-8').decode('latin1')
    sql = f"select charac_no from charac_info where charac_name='{name_new}';"
    charactor_cuesor.execute(sql)
    res = charactor_cuesor.fetchall()

    name_tw = convert(name,'zh-tw')
    if name!=name_tw:
        name_tw_new = name_tw.encode('utf-8').decode('latin1')
        sql = f"select charac_no from charac_info where charac_name='{name_tw_new}';"
        charactor_cuesor.execute(sql)
        res.extend(charactor_cuesor.fetchall())
    return res

def getCargoAll(name='',cNo=0):
    '''获取仓库的blob字段'''
    if cNo==0:
        cNo = getCharactorNo(name)[0][0]
    get_all_sql = f'select cargo,jewel,expand_equipslot from charac_inven_expand where charac_no={cNo};'
    inventry_cursor.execute(get_all_sql)
    results = inventry_cursor.fetchall()
    return results

def getInventoryAll(name='',cNo=0):
    '''获取背包，穿戴槽，宠物栏的blob字段'''
    if cNo!=0:
        charac_no = cNo
    else:
        charac_no = getCharactorNo(name)[0][0]
    get_all_sql = f'select inventory,equipslot,creature from inventory where charac_no={charac_no};'
    inventry_cursor.execute(get_all_sql)
    results = inventry_cursor.fetchall()
    return results

def getAvatar(cNo):
    getAvatarSql = f'select ui_id,it_id,ability_no from user_items where charac_no={cNo};'
    inventry_cursor.execute(getAvatarSql)
    results = inventry_cursor.fetchall()
    res = []
    for ui_id,it_id,ability_no in results:
        res.append([ui_id,ITEMS_dict.get(it_id),it_id])
    return res

def getCreatureItem(name='',cNo=0):
    '''获取宠物'''
    if cNo!=0:
        charac_no = cNo
    else:
        charac_no = getCharactorNo(name)[0][0]
    get_creatures_sql = f'select ui_id,it_id,name from creature_items where charac_no={charac_no};'
    inventry_cursor.execute(get_creatures_sql)
    results = inventry_cursor.fetchall()
    #print(results)
    res = []
    for ui_id, it_id, name in results:
        name_new = name.encode('windows-1252',errors='ignore').decode(errors='ignore')
        res.append([ui_id,ITEMS_dict.get(it_id),it_id,name_new])
    return res

def setInventory(InventoryBlob,cNo,key='inventory'):
    if key in ['inventory','equipslot', 'creature']: table = 'inventory'
    if key in ['cargo','jewel','expand_equipslot']: table = 'charac_inven_expand'
    if key in ['skill_slot']:table = 'skill'
    sql_update = f'''update {table} set {key}=%s where charac_no={cNo};'''
    try:
        inventry_cursor.execute(sql_update,(InventoryBlob,))
        inventry_db.commit()
        return True
    except:
        return False

def commit_change_blob(originBlob,editDict:dict,cNo,key):
    '''传入原始blob和修改的物品槽对象列表'''
    editList = list(editDict.items())
    blob_new = buildBlob(originBlob,editList)
    print(cNo,key,unpackBLOB_Item(blob_new))
    return setInventory(blob_new,cNo,key)

def delCreatureItem(ui_id):
    try:
        sql = f'delete from creature_items where ui_id={ui_id};'
        print(sql)
        inventry_cursor.execute(sql)
        inventry_db.commit()
        return True
    except:
        return False
    
def delNoneBlobItem(ui_id,tableName='creature_items'):
    try:
        sql = f'delete from {tableName} where ui_id={ui_id};'
        print(sql)
        inventry_cursor.execute(sql)
        inventry_db.commit()
        return True
    except:
        return False

def connect(infoFunc=lambda x:...):
    global account_db,account_cursor,inventry_db,inventry_cursor,charactor_db,charactor_cuesor
    try:
        account_db = connector.connect(user=config['DB_USER'], password=config['DB_PWD'], host=config['DB_IP'], port=config['DB_PORT'], database='d_taiwan', connection_timeout=4)
        account_cursor = account_db.cursor()
        infoFunc('账号表连接成功')
        inventry_db = connector.connect(user=config['DB_USER'], password=config['DB_PWD'], host=config['DB_IP'], port=config['DB_PORT'], database='taiwan_cain_2nd')
        inventry_cursor = inventry_db.cursor()
        infoFunc('背包表连接成功')
        charactor_db = connector.connect(user=config['DB_USER'], password=config['DB_PWD'], host=config['DB_IP'], port=config['DB_PORT'], database='taiwan_cain', charset='latin1')
        charactor_cuesor = charactor_db.cursor()
        infoFunc('角色表连接成功')
        json.dump(config,open(configPath,'w'))
        return True
    except Exception as e:
        account_cursor = None
        inventry_cursor = None
        charactor_cuesor = None
        infoFunc(str(e))
        return e

def searchItem(key):
    res = []
    pattern = '.*?'.join(key)
    regex = re.compile(pattern)
    for id_,name in ITEMS:
        try:
            match = regex.search(name)
            if match:
                res.append([id_,name])
        except:
            pass
    
    return sorted(res,key=lambda x:len(x[1]))

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
                items_bytes = zlib.decompress(selected_blob[4:])
                #InventoryBlob_new = buildDeletedBlob(dels,items_bytes,selected_blob[:4])
                #print(InventoryBlob_new)
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
if __name__=='__main__':
    if not connect():
        input('数据库连接失败，请重新配置config.json文件')
        exit()
    loadItems2(True)
    print(f'数据库{config["DB_IP"]}:{config["DB_PORT"]}已连接')
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
    #os.kill(subPid,signal.SIGINT)

