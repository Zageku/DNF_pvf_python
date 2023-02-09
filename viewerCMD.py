import zlib
import struct
import os
import csv
from mysql import connector
from mysql.connector.locales.eng import client_error
import json
import datetime
import pvfReader
from zhconv import convert
import hashlib
import pickle
import time
__version__ = '0.1.31'
print(f'物品栏装备删除工具_CMD V{__version__}\n\n')
configPath = './config.json'
pvfCachePath = './pvf.cache'
if os.path.exists(configPath):
    config = json.load(open(configPath,'r'))
else:
    config = {
        'DB_IP' : '192.168.200.131',
        'DB_PORT' : 3306,
        'DB_USER' : 'game',
        'DB_PWD' : '123456',
        'PVF_PATH': 'Script.pvf'
    }
    json.dump(config,open(configPath,'w'))

if os.path.exists(pvfCachePath):
    with open('pvf.cache','rb') as pvfFile:
        PVFs = pickle.load(pvfFile)
else:
    PVFs = {}

def procBlob(fbytes):
    items_bytes = zlib.decompress(fbytes[4:])
    num = len(items_bytes)//61
    result = []
    for i in range(num):
        itemID = struct.unpack('i',items_bytes[i*61:(i+1)*61][2:6])[0]
        if itemID==0:continue
        result.append([i, itemID])
    return result

def showBLOB(fbytes):
    items_bytes = zlib.decompress(fbytes[4:])
    num = len(items_bytes)//61
    result = []
    for i in range(num):
        if items_bytes[i*61:(i+1)*61] == b'\x00'*61:continue
        itemID = struct.unpack('i',items_bytes[i*61:(i+1)*61][2:6])[0]
        result.append([i, ITEMS_dict.get(itemID), itemID])
    return result

def showItemBytes(items_bytes):
    num = len(items_bytes)//61
    result = []
    for i in range(num):
        itemID = struct.unpack('i',items_bytes[i*61:(i+1)*61][2:6])[0]
        if itemID==0:continue
        result.append([i, ITEMS_dict.get(itemID), itemID])
    return result

def buildDeletedBlob(deleteList,items_bytes,prefix):
    '''返回删除物品后的数据库blob字段'''
    items_bytes = bytearray(items_bytes)
    for i in deleteList:
        items_bytes[i*61:i*61+61] = bytearray(b'\x00'*61)
    blob = prefix + zlib.compress(items_bytes)
    return blob

def buildDeletedBlob2(deleteList,originBlob):
    '''返回删除物品后的数据库blob字段'''
    prefix = originBlob[:4]
    items_bytes = bytearray(zlib.decompress(originBlob[4:]))
    for i in deleteList:
        items_bytes[i*61:i*61+61] = bytearray(b'\x00'*61)
    blob = prefix + zlib.compress(items_bytes)
    return blob


ITEMS = []
ITEMS_dict = {}


def loadItems2(usePVF=False,pvfPath='',showFunc=lambda x:print(x)):
    global ITEMS, ITEMS_dict
    ITEMS = []
    ITEMS_dict = {}
    if pvfPath=='':
        pvfPath = config['PVF_PATH']
    if usePVF :
        if  os.path.exists(pvfPath):
            MD5 = hashlib.md5(open(pvfPath,'rb').read()).hexdigest()
            showFunc(pvfPath)
            if PVFs.get(MD5) is not None:
                ITEMS_dict = PVFs.get(MD5)
                info = f'加载pvf缓存获得{len(ITEMS_dict.keys())}条物品信息记录'
            else:
                pvf = pvfReader.FileTree(header=pvfReader.PVFHeader(pvfPath))
                print('加载PVF中...\n',pvf.header)
                pvf.loadLeafs(['stackable','equipment'])
                print('PVF加载文件数：',pvf._fileNum)
                showFunc('PVF加载即将完成...')
                stackable_dict = pvfReader.getItemDict(pvf)
                ITEMS_dict = stackable_dict
                PVFs[pvfPath] = stackable_dict
                PVFs[MD5] = stackable_dict
                info = f'加载pvf文件获得{len(ITEMS_dict.keys())}条物品信息记录'
                del pvf
                pvfFile = open(pvfCachePath,'wb')
                pickle.dump(PVFs,pvfFile)
        else:
            info = 'PVF文件路径错误'
    else:
        csvList = list(filter(lambda item:item[-4:].lower()=='.csv',os.listdir()))
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
    if cNo==0:
        cNo = getCharactorNo(name)[0][0]
    get_all_sql = f'select cargo,jewel,expand_equipslot from charac_inven_expand where charac_no={cNo};'
    inventry_cursor.execute(get_all_sql)
    results = inventry_cursor.fetchall()
    return results

def getInventory(name='',cNo=0):
    if cNo!=0:
        charac_no = cNo
    else:
        charac_no = getCharactorNo(name)[0][0]
    get_all_sql = f'select inventory,equipslot,creature from inventory where charac_no={charac_no};'
    inventry_cursor.execute(get_all_sql)
    results = inventry_cursor.fetchall()
    return results

def getInventoryAll(name='',cNo=0):
    if cNo!=0:
        charac_no = cNo
    else:
        charac_no = getCharactorNo(name)[0][0]
    get_all_sql = f'select inventory,equipslot,creature from inventory where charac_no={charac_no};'
    inventry_cursor.execute(get_all_sql)
    results = inventry_cursor.fetchall()
    return results

def getCreatureItem(name='',cNo=0):
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
    sql_update = f'''update {table} set {key}=%s where charac_no={cNo};'''
    try:
        inventry_cursor.execute(sql_update,(InventoryBlob,))
        inventry_db.commit()
        return True
    except:
        return False

def delCreatureItem(ui_id):
    try:
        deleteDate = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = 'insert into creature_items_del(sdate,ui_id,charac_no,slot,it_id,reg_date,name,stomach,exp,endurance,creature_type,no_charge,stat,item_lock_key,ipg_agency_no,expire_date,delete_date) '+\
            f'select {deleteDate},creature_items.ui_id,creature_items.creature_items.charac_no,creature_items.slot,creature_items.it_id,creature_items.reg_date,creature_items.name,creature_items.stomach,creature_items.exp,creature_items.endurance,creature_items.creature_type,creature_items.no_charge,creature_items.stat,creature_items.item_lock_key,creature_items.ipg_agency_no,creature_items.expire_date,creature_items.delete_date from creature_items '+\
                f'where ui_id={ui_id};'
        sql = f"update creature_items delete_date='{deleteDate}' where ui_id={ui_id};"
        sql = f'delete from creature_items where ui_id={ui_id};'
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
        return True
    except Exception as e:
        account_cursor = None
        inventry_cursor = None
        charactor_cuesor = None
        infoFunc(str(e))
        return False


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
            items = showBLOB(selected_blob)
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
                InventoryBlob_new = buildDeletedBlob(dels,items_bytes,selected_blob[:4])
                print(InventoryBlob_new)
                print(buildDeletedBlob2(dels,selected_blob))
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
                    if delCreatureItem(ui_id):
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
    loadItems2()
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

