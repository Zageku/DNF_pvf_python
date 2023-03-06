import zlib
import struct
from pathlib import Path
import csv
from mysql import connector
import pymysql_old as pymysql_old
import pymysql_new 
import encodings.idna
from mysql.connector.locales.eng import client_error
import json
import pvfReader
from zhconv import convert
import copy
import hashlib
import pickle
import re
import time 
import threading
__version__ = ''

print(f'物品栏装备删除工具_CMD {__version__}\n\n')
configPathStr = 'config/config.json'
pvfCachePathStr = 'config/pvf.cache'
magicSealDictPathStr = 'config/magicSealDict.json'
jobDictPathStr = 'config/jobDict.json'
avatarHiddenPathStr = 'config/avatarHidden.json'
expTablePathStr = 'config/expTable.json'
csvPathStr = 'config/'
csvPath = Path(csvPathStr)
fcgPath = Path(configPathStr)
cachePath = Path(pvfCachePathStr)
magicDictPath = Path(magicSealDictPathStr)
jobPath = Path(jobDictPathStr)
avatarPath = Path(avatarHiddenPathStr)
expTablePath = Path(expTablePathStr)

PVF_CACHE_VERSION = '230303'
CONFIG_VERSION = '230227'
PVFcacheDicts = {'_cacheVersion':PVF_CACHE_VERSION}

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

ITEMS_dict = {}
stackableDict = {}
equipmentDict = {}
equipmentDetailDict = {}    #根据种类保存的物品列表
equipmentForamted = {}  #格式化的装备字典
creatureEquipDict = {}  #存储所有宠物装备
PVFcacheDict = {}
magicSealDict = {}
expTableList = []
avatarHiddenList = [[],[]]
jobDict = {}

typeDict = {
    'waste':[2,'消耗品'],
    'recipe':[2,'制作图'],
    'material expert job':[10,'副职业'],
    'enchant waste':[5,'宝珠'],
    'avatar emblem':[6,'徽章'],
    'feed':[7,'宠物饲料'],
    'etc':[8,'etc'],
    'creature':[7,'宠物消耗品'],
    'booster':[11,'礼包1'],
    'material':[3,'材料'],
    'quest':[4,'任务材料'],
    'throw':[2,'投掷品'],
    'upgradable legacy':[2,'礼包2'],
    'disguise':[2,'变装道具'],
    'disguise random':[2,'变装道具2'],
    'only effect':[2,'城镇特效'],
    'booster selection':[11,'礼包3'],
    'usable cera package':[11,'时装礼包'],
    'dye':[2,'染色剂'],
    'set':[2,'陷阱'],
    'cera booster':[11,'其它礼包1'],
    'cera package':[11,'其它礼包2'],
    'unlimited waste':[2,'无限道具'],
    'expert town potion':[2,'城镇药剂'],
    'quest receive':[9,'悬赏令'],
    'legacy':[13,'旧物品'],
    'stackable legacy':[13,'旧物品2'],
    'global effect':[2,'全局光环'],
    'booster random':[11,'随机礼包'],
    'upgrade limit cube':[2,'升级盒子'],
    'multi upgradable legacy':[11,'礼包4'],
    'creature expitem':[7,'宠物经验道具'],
    'teleport potion':[2,'传送药剂'],
    'town and dungeon':[2,'城镇/副本道具'],
    'unlimited town and dungeon':[2,'无限城镇/副本道具'],
    'contract':[12,'契约'],
    'multi upgradable legacy bonus cera':[11,'多重奖励包'],
}
formatedTypeMap = {
    2:'消耗品',
    3:'材料',
    10:'副职业',
    4:'任务材料',
    5:'宝珠',
    6:'时装徽章',
    7:'宠物',
    8:'etc',
    9:'悬赏令',
    13:'旧物品',
    11:'礼包',
    12:'契约'
}

formatedTypeDict = {}
for pvfType, typeZh in typeDict.items():
    if formatedTypeDict.get(formatedTypeMap[typeZh[0]]) is None:
        formatedTypeDict[formatedTypeMap[typeZh[0]]] = {}
    formatedTypeDict[formatedTypeMap[typeZh[0]]][pvfType] = typeZh[1]
print(formatedTypeDict)




config_template = {
        'DB_IP' : '192.168.200.131',
        'DB_PORT' : 3306,
        'DB_USER' : 'game',
        'DB_PWD' : '123456',
        'PVF_PATH': '',
        'TEST_ENABLE': 1,
        'TYPE_CHANGE_ENABLE':0,
        'CONFIG_VERSION':CONFIG_VERSION,
        'GITHUB':'https://github.com/Zageku/DNF_pvf_python',
        'INFO':'',
        'FONT':[['',17],['',17],['',20]],
        'VERSION':__version__,
        'TITLE':''
    }
config = {}
if fcgPath.exists():
    config = json.load(open(configPathStr,'r'))
if config.get('CONFIG_VERSION')!=CONFIG_VERSION:
    '''config版本错误'''
    config = config_template
    json.dump(config_template,open(configPathStr,'w'))
else:
    config['FONT'] = [[item[0],int(item[1])] for item in config['FONT']]
        
avatarHiddenMap = {
    'physical attack':'力量',
    'magical attack':'智力',
    'physical defense':'体力',
    'magical defense':'精神',
    'HP MAX':'HP MAX',
    'MP MAX':'MP MAX',
    'HP regen speed':'HP恢复',
    'MP Regen speed':'MP恢复',
    'attack speed':'攻速',
    'move speed':'移速',
    'cast speed':'吟唱',
    'inventory limit':'负重',
    'stuck':'命中率',
    'stuck resistance':'回避率',
    'all activestatus resistance':'异常抗性',
    'hit recovery':'硬直',
    'equipment magical defence':'魔法防御',
    'equipment physical defence':'物理防御',
    'jump power':'跳跃',
    'physical critical hit':'物理暴击',
    'magical critical hit':'魔法暴击',
    '':'',
}

if cachePath.exists():
    try:
        with open(pvfCachePathStr,'rb') as pvfFile:
            cacheCompressed = pvfFile.read()
            PVFcacheDicts:dict = pickle.loads(zlib.decompress(cacheCompressed))
            if PVFcacheDicts.get('_cacheVersion') != PVF_CACHE_VERSION:
                PVFcacheDicts = {'_cacheVersion':PVF_CACHE_VERSION}
    except:
        pass

positionDict = {
    0x00:['快捷栏',[3,9]],
    0x01:['装备栏',[9,57]],
    0x02:['消耗品',[57,105]],
    0x03:['材料',[105,153]],
    0x04:['任务材料',[153,201]],
    0x05:['宠物',[98,99]],#正在使用的宠物
    0x06:['宠物装备',[0,49],[99,102]],#装备栏和正在使用的装备
    0x07:['宠物消耗品',[49,98]],
    0x0a:['副职业',[201,249]]
}

def getStackableTypeDetailZh(itemID):
    segType,segments = getItemInfo(itemID)
    type = None 
    for i in range(len(segments)-1):
        if segments[i] == '[stackable type]':
            type = segments[i+1].replace('[','').replace(']','')
    if type is not None:
        resType = typeDict.get(type)
    return resType

def getStackableTypeMainIdAndZh(itemID):
    if itemID in creatureEquipDict.keys():
        return 0x06,'宠物装备'
    elif itemID in equipmentDict.keys():
        return 0x01,'装备'
    segType,segments = getItemInfo(itemID)
    type = None 
    if len(segments)==0:
        #print('viewer-物品不存在',itemID,segments)
        return 0x00,None
    for i in range(len(segments)-1):
        if segments[i] == '[stackable type]':
            type = segments[i+1].replace('[','').replace(']','')
            break


    resType = ''
    for typeName, typeContentDict in formatedTypeDict.items():
        if type in typeContentDict.keys():
            resType = typeName
            break
    if resType in ['消耗品','礼包','悬赏令','etc','宝珠']:
        resTypeID = 0x02
    elif resType in ['材料']:
        resTypeID = 0x03
    elif resType in ['任务材料']:
        resTypeID = 0x04
    elif resType in ['宠物']:
        resTypeID = 0x07
    elif resType in ['副职业']:
        resTypeID = 0x0a
    else:
        resTypeID = 0x00
        print(f'viewer-物品种类未知{itemID,type,resType,segments}')


    return resTypeID,resType

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
            sealType = magicSealDict.get(sealID)
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

def unpackBLOB_Item(fbytes):
    '''返回[index, DnfItemGrid对象]'''
    items_bytes = zlib.decompress(fbytes[4:])
    num = len(items_bytes)//61
    result = []
    for i in range(num):
        #if items_bytes[i*61:(i+1)*61] == b'\x00'*61:continue
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

def getItemInfo(itemID:int):
    if PVFcacheDict.get('stringtable') is not None:
        stringtable = PVFcacheDict['stringtable']
        nString = PVFcacheDict['nstring']
        idPathContentDict = PVFcacheDict['idPathContentDict']
        #try:
        res = pvfReader.TinyPVF.content2List(idPathContentDict.get(itemID),stringtable,nString)
        #except:
        #    res = '',['无此id记录']
    else:
        res =  'type',['']
    return res

def equipmentDetailDict_transform():
    global equipmentForamted
    keyMap = {
        '短剑':'ssword','太刀':'katana','巨剑':'hsword','钝器':'club','光剑':'beamsword',
        '手套':'knuckle','臂铠':'gauntlet','爪':'claw','拳套':'boxglove','东方棍':'tonfa',
        '自动手枪':'automatic','手弩':'bowgun','左轮':'revolver','步枪':'musket','手炮':'hcannon',
        '法杖':'staff','魔杖':'rod','棍棒':'pole','矛':'spear','扫把':'broom',
        '十字架':'cross','镰刀':'scythe','念珠':'rosary','图腾':'totem','战斧':'axe',
        '手杖':'wand','匕首':'dagger','双剑':'twinsword','项链':'amulet','手镯':'wrist',
        '戒指':'ring','辅助装备':'support','魔法石':'magicstone','称号':'title',
        '上衣':'jacket','头肩':'shoulder','下装':'pants','腰带':'belt','鞋':'shoes',
        '布甲':'cloth','皮甲':'leather','轻甲':'larmor','重甲':'harmor','板甲':'plate',
        '鬼剑士':'swordman','格斗家':'fighter','神枪手':'gunner','魔法师':'mage','圣职者':'priest',
        '暗夜使者':'thief'
    }
    keyMapTMP = {}
    for key,value in keyMap.items():
        keyMapTMP[value] =key
    keyMap.update(keyMapTMP)
    equipmentForamted = {
        '武器':{
            '鬼剑士':{'短剑':{},'太刀':{},'巨剑':{},'钝器':{},'光剑':{}},
            '格斗家':{'手套':{},'臂铠':{},'爪':{},'拳套':{},'东方棍':{}},
            '神枪手':{'自动手枪':{},'手弩':{},'左轮':{},'步枪':{},'手炮':{}},
            '魔法师':{'法杖':{},'魔杖':{},'棍棒':{},'矛':{},'扫把':{}},
            '圣职者':{'十字架':{},'镰刀':{},'念珠':{},'图腾':{},'战斧':{}},
            '暗夜使者':{'手杖':{},'匕首':{},'双剑':{}}
        },
        '防具':{
            '布甲':{'上衣':{},'头肩':{},'下装':{},'腰带':{},'鞋':{}},
            '皮甲':{'上衣':{},'头肩':{},'下装':{},'腰带':{},'鞋':{}},
            '轻甲':{'上衣':{},'头肩':{},'下装':{},'腰带':{},'鞋':{}},
            '重甲':{'上衣':{},'头肩':{},'下装':{},'腰带':{},'鞋':{}},
            '板甲':{'上衣':{},'头肩':{},'下装':{},'腰带':{},'鞋':{}}
        },
        '首饰':{
            '项链':{},
            '手镯':{},
            '戒指':{}
        },
        '特殊装备':{
            '辅助装备':{},
            '魔法石':{},
            '称号':{},
            '其它':{}
        },
        '其它':{
            '其它':{}
        }
    }
    i=0
    def add_dict_all(outDict:dict,inDict:dict):
        nonlocal i
        if isinstance(inDict,dict):
            for key,value in inDict.items():
                if isinstance(value,str):
                    outDict[key] = convert(value.strip(),'zh-cn')
                    i+=1
                else:
                    add_dict_all(outDict,value)

    for dirName,dirDict in PVFcacheDict['equipmentStructuredDict'].items():
        if dirName not in ['character','creature','monster']:
            add_dict_all(equipmentForamted['特殊装备']['其它'],dirDict)
        if dirName == 'creature':
            add_dict_all(creatureEquipDict,dirDict)
    
    for dir1Name, dir2Dict in PVFcacheDict['equipmentStructuredDict']['character'].items():
        if dir1Name == 'common':#处理防具和首饰
            for commonType, partDir in dir2Dict.items():
                if keyMap.get(commonType) is None:  #未识别的物品，保存到其它后跳过
                    keyMap[commonType] = commonType
                    add_dict_all(equipmentForamted['其它']['其它'],partDir)
                    continue
                if not isinstance(partDir,dict):    #直接放到根目录的物品，保存到其它后跳过
                    if isinstance(partDir,str):
                        id_, name = commonType, partDir
                        equipmentForamted['其它']['其它'][id_] = convert(name.strip(),'zh-cn')
                    continue
                if commonType in ['amulet','wrist','ring']:#首饰
                    add_dict_all(equipmentForamted['首饰'][keyMap[commonType]],partDir)
                elif commonType in ['magicstone','title','support']:    #特殊装备
                    add_dict_all(equipmentForamted['特殊装备'][keyMap[commonType]],partDir)
                else:   #是防具
                    for armorType,itemDict in partDir.items():
                        if not isinstance(itemDict,dict):   #直接放到防具根目录的物品，放到其它后跳过
                            if isinstance(itemDict,str):
                                id_, name = armorType,itemDict
                                equipmentForamted['其它']['其它'][id_] = convert(name.strip(),'zh-cn')
                            continue
                        add_dict_all(equipmentForamted['防具'][keyMap[armorType]][keyMap[commonType]],partDir)

        else:   #处理武器
            jobName = dir1Name
            if jobName not in keyMap.keys():    #扩充角色类型
                keyMap[jobName] = jobName
                equipmentForamted['武器'][jobName] = {}
            jobDirsDict = dir2Dict
            if not isinstance(jobDirsDict,dict):continue
            for weaponDirName, weaponTypeDict in jobDirsDict.items():
                #print(jobName,weaponDirName,weaponTypeDict.keys())
                if weaponDirName=='weapon':
                    for weaponType, weaponDict in weaponTypeDict.items():
                        if not isinstance(weaponDict,dict): 
                            if isinstance(weaponDict,str):
                                id_, name = weaponType, weaponDict
                                equipmentForamted['特殊装备']['其它'][id_] = convert(name.strip(),'zh-cn')
                            continue
                        
                        if weaponType not in keyMap.keys(): #扩充武器名
                            keyMap[weaponType] = weaponType
                            equipmentForamted['武器'][keyMap[jobName]][weaponType] = {}

                        if keyMap[weaponType] not in equipmentForamted['武器'][keyMap[jobName]].keys(): #扩充职业武器类型
                            equipmentForamted['武器'][keyMap[jobName]][keyMap[weaponType]] = {}

                        targetDict = equipmentForamted['武器'][keyMap[jobName]][keyMap[weaponType]]
                        add_dict_all(targetDict,weaponDict)
                else:
                    equipmentForamted['武器'][keyMap[jobName]]['其它'] = {}
                    add_dict_all(equipmentForamted['武器'][keyMap[jobName]]['其它'],weaponTypeDict)

    print(f'装备查询转换完成,{i}件装备')
    return equipmentForamted

def searchItem(keys,itemList=None,fuzzy=True):
    if itemList is None:
        itemList = ITEMS_dict.items()
    res = []
    regexList = []
    for key in keys.split(' '):
        if fuzzy:
            pattern = '.*?'.join(key)
        else:
            pattern = key
        regex = re.compile(pattern,re.IGNORECASE)
        regexList.append(regex)
    for id_,name in itemList:
        matchNum = 0
        for regex in regexList:
            try:
                match = regex.search(name)
                if  match:
                    matchNum += 1
                    continue
            except:
                pass
        if matchNum == len(regexList):
            res.append([id_,name])
    
    return sorted(res,key=lambda x:len(x[1]))

def searchMagicSeal(key):
    res = []
    pattern = '.*?'.join(key)
    regex = re.compile(pattern)
    for id_,name in magicSealDict.items():
        try:
            match = regex.search(name)
            if match:
                res.append([id_,name])
        except:
            pass
    
    return sorted(res,key=lambda x:len(x[1]))
                
def loadItems2(usePVF=False,pvfPath='',showFunc=lambda x:print(x),MD5='0'):        
    global ITEMS_dict,  PVFcacheDict, magicSealDict, jobDict, equipmentDict, stackableDict, avatarHiddenList, expTableList
    ITEMS = []
    ITEMS_dict = {}
    jobDict = {}
    magicSealDict = {}
    if pvfPath=='':
        pvfPath = config['PVF_PATH']
    if usePVF :
        p = Path(pvfPath)
        if  MD5 in PVFcacheDicts.keys():
            if PVFcacheDicts.get(MD5) is not None:
                #PVFcacheDict_tmp = PVFcacheDicts.get(MD5)
                #if isinstance(PVFcacheDict_tmp,dict):
                PVFcacheDict = PVFcacheDicts.get(MD5)
                info = f'加载pvf缓存完成'
                config['PVF_PATH'] = MD5
                #print(PVFcacheDict['avatarHidden'])
                
        elif  '.pvf' in pvfPath and p.exists():
            MD5 = hashlib.md5(open(pvfPath,'rb').read()).hexdigest().upper()
            if MD5 in PVFcacheDicts.keys():
                PVFcacheDict = PVFcacheDicts.get(MD5)
                info = f'加载pvf缓存完成' 
            else:
                pvf = pvfReader.TinyPVF(pvfHeader=pvfReader.PVFHeader(pvfPath))
                print('加载PVF中...\n',pvf.pvfHeader)
                all_items_dict = pvfReader.get_Item_Dict(pvf)
                if all_items_dict==False:
                    return False
                PVFcacheDict = {}
                PVFcacheDict['stringtable'] = pvf.stringTable
                PVFcacheDict['nstring'] = pvf.nString
                PVFcacheDict['idPathContentDict'] = all_items_dict.pop('idPathContentDict')
                PVFcacheDict['magicSealDict'] = all_items_dict.pop('magicSealDict')
                PVFcacheDict['jobDict'] = all_items_dict.pop('jobDict')
                PVFcacheDict['equipment'] = all_items_dict.pop('equipment')
                PVFcacheDict['stackable'] = all_items_dict.pop('stackable')
                PVFcacheDict['equipmentStructuredDict'] = all_items_dict.pop('equipmentStructuredDict')
                PVFcacheDict['avatarHidden'] = all_items_dict.pop('avatarHidden')
                PVFcacheDict['expTable'] = all_items_dict.pop('expTable')
                
                info = f'加载pvf文件完成'
                PVFcacheDicts[MD5] = PVFcacheDict
                pvfFile = open(pvfCachePathStr,'wb')
                PVFcacheDict['nstring'].tinyPVF = None
                cacheCompressed = zlib.compress(pickle.dumps(PVFcacheDicts))
                pvfFile.write(cacheCompressed)
                pvfFile.close()
                print(f'pvf cache saved. {PVFcacheDict.keys()}')                
            config['PVF_PATH'] = MD5
        else:
            info = 'PVF文件路径错误'
            return info
        ITEMS_dict = {}
        ITEMS_dict.update(PVFcacheDict['stackable'])
        ITEMS_dict.update(PVFcacheDict['equipment'])
        magicSealDict = PVFcacheDict['magicSealDict']
        jobDict = PVFcacheDict['jobDict']
        equipmentDict = PVFcacheDict['equipment']
        stackableDict = PVFcacheDict['stackable']
        avatarHiddenList_En = copy.deepcopy(PVFcacheDict['avatarHidden'])
        if len(PVFcacheDict['expTable'])!=0:
            expTableList = PVFcacheDict['expTable']
        equipmentDetailDict_transform() #转换为便于索引的格式
        info += f' 物品：{len(PVFcacheDict["stackable"].keys())}条，装备{len(PVFcacheDict["equipment"])}条'
    else:
        csvList = list(filter(lambda item:item.name[-4:].lower()=='.csv',[item for item in csvPath.iterdir()]))
        print(f'物品文件列表:',csvList)
        for fcsv in csvList:
            csv_reader = list(csv.reader(open(fcsv,encoding='utf-8',errors='ignore')))[1:]
            ITEMS.extend(csv_reader)
        for item in ITEMS:
            if len(item)!=2:
                print(item)
            else:
                ITEMS_dict[int(item[1])] = item[0]
        magicSealDict = json.load(open(magicSealDictPathStr,'r'))
        jobDict = json.load(open(jobDictPathStr,'r'))
        avatarHiddenList_En = json.load(open(avatarHiddenPathStr,'r'))
        expTableList = json.load(open(expTablePath,'r'))
        info = f'加载csv文件获得{len(ITEMS)}条物品信息记录，魔法封印{len(magicSealDict.keys())}条'

    for key,value in ITEMS_dict.items():
        try:
            ITEMS_dict[key] = convert(value,'zh-cn').strip()
        except:
            ITEMS_dict[key] = value
    magicSealDict_tmp = {}
    for key,value in magicSealDict.items():
        magicSealDict_tmp[int(key)] = value
    magicSealDict = magicSealDict_tmp
    jobDict_tmp = {}
    for key,value in jobDict.items():
        valueNew = {}
        for key1, value1 in value.items():
            valueNew[int(key1)] = convert(value1,'zh-cn').strip()
        jobDict_tmp[int(key)] = valueNew
    jobDict = jobDict_tmp
    for key,value in equipmentDict.items():
        equipmentDict[key] = convert(value,'zh-cn')
    for key,value in stackableDict.items():
        stackableDict[key] = convert(value,'zh-cn')
    for i in range(len(avatarHiddenList_En)):
        for j,value in enumerate(avatarHiddenList_En[i]):
            avatarHiddenList_En[i][j] = avatarHiddenMap[value]
    avatarHiddenList = avatarHiddenList_En
    json.dump(config,open(configPathStr,'w'),ensure_ascii=False)
    return info





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
        res.append([ui_id,ITEMS_dict.get(it_id),it_id])
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
        res.append([ui_id,ITEMS_dict.get(it_id),it_id,name_new])
    return res

def get_online_charac():
    loginCursor = connectorUsed['login_cursor']
    loginDb = connectorUsed['login_db']
    get_login_account_sql = f'select m_id from login_account_3 where login_status=1'
    loginCursor.execute(get_login_account_sql)
    onlineAccounts = [item[0] for item in loginCursor.fetchall()]
    #print(onlineAccounts)

    gameDB = connectorUsed['game_event_db']
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
    #return result




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
                expTableList_with_lv0 = [0,0] + expTableList
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
        json.dump(config,open(configPathStr,'w'),ensure_ascii=False)
        print(f'数据库连接成功({len(connectorAvailuableDictList)})')
        return f'数据库连接成功({len(connectorAvailuableDictList)})'




if __name__=='__main__':
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

