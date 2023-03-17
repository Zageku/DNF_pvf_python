import zlib
from pathlib import Path
import csv
import json
import pvfReader
import copy
import hashlib
import pickle
import re
import time 
import threading
__version__ = ''

#print(f'物品栏装备删除工具_CMD {__version__}\n\n')

tinyCachePath = Path('config/pvf.tinycache')
csvPath = Path('config/')
configPath = Path('config/config.json')
cacheDirPath = Path('config/pvfCache')
magicDictPath = Path('config/magicSealDict.json')
jobPath = Path('config/jobDict.json')
avatarPath = Path('config/avatarHidden.json')
expTablePath = Path('config/expTable.json')

PVF_CACHE_VERSION = '230316c'
CONFIG_VERSION = '230314'

config_template = {
        'DB_IP' : '192.168.200.131',
        'DB_PORT' : 3306,
        'DB_USER' : 'game',
        'DB_PWD' : '123456',
        'SERVER_IP': '192.168.200.131',
        'SERVER_PORT' : 22,
        'SERVER_USER' : 'root',
        'SERVER_PWD' : '123456',
        'PVF_PATH': '',
        'TEST_ENABLE': 1,
        'TYPE_CHANGE_ENABLE':0,
        'CONFIG_VERSION':CONFIG_VERSION,
        'GITHUB':'https://github.com/Zageku/DNF_pvf_python',
        'NET_DISK':'https://pan.baidu.com/s/1_rs2t1CjKj4Rzr_1hzQCUQ?pwd=qdnf',
        'INFO':'',
        'FONT':[['',17],['',17],['',20]],
        'VERSION':__version__,
        'TITLE':'',
        'DIY':[],
        'DIY_2':[],
        'SIZE':[1,1]
    }
def save_config():
    json.dump(config,open(configPath,'w'),ensure_ascii=False)

config = config_template
if configPath.exists():
    try:
        config = json.load(open(configPath,'r'))
        if config.get('CONFIG_VERSION')!=CONFIG_VERSION:
            '''config版本错误'''
            config = config_template
            save_config()
        else:
            config['FONT'] = [[item[0],int(item[1])] for item in config['FONT']]
    except:
        pass
else:
    save_config()

ITEMS_dict = {}
stackableDict = {}
equipmentDict = {}
equipmentForamted = {}  #格式化的装备字典
creatureEquipDict = {}  #存储所有宠物装备
PVFcacheDict = {}
magicSealDict = {}
expTableList = []
avatarHiddenList = [[],[]]
jobDict = {}
cardDict_zh = {}
enhanceDict_zh = {}
dungeonDict = {}

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
    7:'宠物消耗品',
    8:'etc',
    9:'悬赏令',
    13:'旧物品',
    11:'礼包',
    12:'契约'
}

formatedTypeDict = {}   #按大类：小类字典 存储
for pvfType, typeZh in typeDict.items():
    if formatedTypeDict.get(formatedTypeMap[typeZh[0]]) is None:
        formatedTypeDict[formatedTypeMap[typeZh[0]]] = {}
    formatedTypeDict[formatedTypeMap[typeZh[0]]][pvfType] = typeZh[1]
#print(formatedTypeDict)

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

cacheSavingFlg = False
cacheSavingNUM = 0  #已经保存好/正在保存的编号
cacheSavingQueueNum = 1 #下一个保存号

class PVFCacheManager:
    '''缓存文件名格式： {MD5}.pvfcache'''
    def __init__(self) -> None:
        self.tinyCache = {'_cacheVersion':PVF_CACHE_VERSION} # MD5: nickName/pvfPath/equNum/stkNum/fileName
        self.loadCacheList()
    
    def loadCacheList(self):
        if tinyCachePath.exists():
            try:
                content = open(tinyCachePath,'r').read()
                self.tinyCache = json.loads(content)

                if self.tinyCache['_cacheVersion']!=PVF_CACHE_VERSION:
                    self.tinyCache = {'_cacheVersion':PVF_CACHE_VERSION}
            except:
                self.tinyCache = {'_cacheVersion':PVF_CACHE_VERSION}
        else:
            self.tinyCache = {'_cacheVersion':PVF_CACHE_VERSION}
        if cacheDirPath.exists():
            for MD5,infoDict in self.tinyCache.copy().items():
                try:
                    if MD5=='_cacheVersion':continue
                    filePath = cacheDirPath.joinpath(infoDict['fileName'])
                    if not filePath.exists():
                        self.tinyCache.pop(MD5)
                except:
                    self.tinyCache.pop(MD5)
        else:
            cacheDirPath.mkdir()
            self.tinyCache = {'_cacheVersion':PVF_CACHE_VERSION}
        #print(self.tinyCache)

    def delCache(self,MD5=''):
        fullPath:Path = cacheDirPath.joinpath(self.tinyCache[MD5]['fileName'])
        fullPath.unlink()
        self.tinyCache.pop(MD5)
        self.saveTinyCache()

    def renameCache(self,MD5='',name=''):
        self.tinyCache[MD5]['nickName'] = name
        self.saveTinyCache()

    def saveTinyCache(self):
        json.dump(self.tinyCache,open(tinyCachePath,'w'))
    
    def saveCache(self,PVFcacheDict={}):
        MD5 = PVFcacheDict.get('MD5')
        newName = f'{MD5}.pvfcache'
        fullPath = cacheDirPath.joinpath(newName)
        PVFcacheDict['_cacheVersion'] = PVF_CACHE_VERSION
        self.tinyCache[MD5] = {
            'nickName':PVFcacheDict['nickName'],
            'pvfPath':PVFcacheDict['pvfPath'],
            'equNum':len(PVFcacheDict['equipment'].keys()),
            'stkNum':len(PVFcacheDict['stackable'].keys()),
            'fileName':newName,
        }
        PVFcacheDict_tmp = {}
        for key,value in PVFcacheDict.items():
            PVFcacheDict_tmp[key] = zlib.compress(pickle.dumps(value))
        content = pickle.dumps(PVFcacheDict_tmp)
        with open(fullPath,'wb') as f:
            f.write(content)
        self.saveTinyCache()

    def loadcache_old(self,MD5):
        fileName = self.tinyCache.get(MD5)['fileName']
        if fileName is not None:
            filePath = cacheDirPath.joinpath(fileName)
            with open(filePath,'rb') as f:
                cacheCompressed = f.read()
                PVFcacheDict:dict = pickle.loads(zlib.decompress(cacheCompressed))
            return PVFcacheDict
    def loadcache2(self,MD5):
        fileName = self.tinyCache.get(MD5)['fileName']
        if fileName is not None:
            filePath = cacheDirPath.joinpath(fileName)
            with open(filePath,'rb') as f:
                cacheCompressed = f.read()
            PVFcacheDict:dict = pickle.loads(cacheCompressed)
            for key,value in PVFcacheDict.items():
                PVFcacheDict[key] = pickle.loads(zlib.decompress(value))
                time.sleep(0.005)   #给主线程活动时间
            return PVFcacheDict

    def saveCache_old(self,PVFcacheDict={}):
        MD5 = PVFcacheDict.get('MD5')
        newName = f'{MD5}.pvfcache'
        fullPath = cacheDirPath.joinpath(newName)
        PVFcacheDict['_cacheVersion'] = PVF_CACHE_VERSION
        self.tinyCache[MD5] = {
            'nickName':PVFcacheDict['nickName'],
            'pvfPath':PVFcacheDict['pvfPath'],
            'equNum':len(PVFcacheDict['equipment'].keys()),
            'stkNum':len(PVFcacheDict['stackable'].keys()),
            'fileName':newName,
        }
        content = zlib.compress(pickle.dumps(PVFcacheDict))        
        with open(fullPath,'wb') as f:
            f.write(content)
        self.saveTinyCache()

    
    def __getitem__(self,MD5=''):
        return self.loadcache2(MD5)
        
    get = __getitem__

    def allMD5(self):
        return list(self.tinyCache.keys())

cacheManager = PVFCacheManager()
tinyCache = cacheManager.tinyCache

def save_PVF_cache(PVFcacheDict_=None):
    def inner():
        global cacheSavingFlg, cacheSavingNUM, cacheSavingQueueNum
        nonlocal PVFcacheDict_
        saveNUM = cacheSavingQueueNum
        cacheSavingQueueNum += 1
        if cacheSavingNUM+1!=saveNUM and cacheSavingFlg==True:
            return False    #前面有要保存的进程
        while cacheSavingFlg==True:
            time.sleep(1)
        if PVFcacheDict_ is None:
            PVFcacheDict_ = PVFcacheDict
        cacheSavingFlg = True
        cacheSavingNUM = saveNUM
        cacheManager.saveCache(PVFcacheDict_)
        cacheSavingFlg = False
    t = threading.Thread(target=inner)
    t.start()

def getStackableTypeMainIdAndZh(itemID):
    '''返回物品种类ID和中文分类'''
    fileInDict = get_Item_Info_In_Dict(itemID)
    if fileInDict is None:
        return 0,''
    
    #处理装备
    equipment_type = fileInDict.get('[equipment type]')
    if equipment_type is not None:
        if 'artifact' in str(equipment_type):
            return 0x06,'宠物装备'
        elif 'creature' in str(equipment_type):
            return 0x05,'宠物'
        elif 'avatar' in str(equipment_type) or ('avatar' in str(fileInDict.keys()) and '[stackable type]'):
            return 0x08,'时装'
    if itemID in equipmentDict.keys():
        return 0x01,'装备'
    
    
    # 处理装备以外的道具
    resType = 'unknown'
    stackable_type = fileInDict.get('[stackable type]') 
    if stackable_type is not None:
        try:
            stackable_type = stackable_type[0][1:-1]
        except:
            print(f'物品种类获取失败:{stackable_type}, {fileInDict}')
            return 0,resType
    for typeName, typeContentDict in formatedTypeDict.items():
        if stackable_type in typeContentDict.keys():
            resType = typeName
            break
    if resType in ['消耗品','礼包','悬赏令','etc','宝珠']:
        resTypeID = 0x02
    elif resType in ['材料']:
        resTypeID = 0x03
    elif resType in ['任务材料']:
        resTypeID = 0x04
    elif resType in ['宠物消耗品']:
        resTypeID = 0x07
    elif resType in ['副职业']:
        resTypeID = 0x0a
    else:
        resTypeID = 0x00    #物品未被分类
    return resTypeID,resType

def get_Item_Info_In_Dict(itemID:int,cacheDict:dict=None):
    if cacheDict is None:
        cacheDict = PVFcacheDict
    stackableDetialDict:dict = cacheDict.get('stackable_detail')
    equipmentDetailDict:dict = cacheDict.get('equipment_detail')
    if stackableDetialDict is not None:
        res = stackableDetialDict.get(itemID)
        if res is None:
            res = equipmentDetailDict.get(itemID)
    else:
        res = {}
    return res

def get_Item_Info_In_Text(itemID:int,cacheDict:dict=None):
    if cacheDict is None:
        cacheDict = PVFcacheDict
    stackableDetialDict:dict = cacheDict.get('stackable_detail')
    equipmentDetailDict:dict = cacheDict.get('equipment_detail')
    if stackableDetialDict is not None:
        resDict = stackableDetialDict.get(itemID)
        if resDict is None:
            resDict = equipmentDetailDict.get(itemID)
        res = pvfReader.TinyPVF.dictSegment2text(resDict)
    else:
        res = ''
    return res

def avatar_Hidden_trans(avatarHiddenList_En:list):
    for i in range(len(avatarHiddenList_En)):
        for j,value in enumerate(avatarHiddenList_En[i]):
            avatarHiddenList_En[i][j] = avatarHiddenMap[value]
    return avatarHiddenList_En

def equipmentDetailDict_transform(equipmentStructuredDict_:dict=None,globalChange=True):
    if globalChange:
        global equipmentForamted
    if equipmentStructuredDict_ is None:
        equipmentStructuredDict = PVFcacheDict['equipmentStructuredDict']
    else:
        equipmentStructuredDict = equipmentStructuredDict_

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
                    outDict[key] = value.strip()
                    i+=1
                else:
                    add_dict_all(outDict,value)

    for dirName,dirDict in equipmentStructuredDict.items():
        if dirName not in ['character','creature','monster']:
            add_dict_all(equipmentForamted['特殊装备']['其它'],dirDict)
        if dirName == 'creature':
            add_dict_all(creatureEquipDict,dirDict)
    
    for dir1Name, dir2Dict in equipmentStructuredDict['character'].items():
        if dir1Name == 'common':#处理防具和首饰
            for commonType, partDir in dir2Dict.items():
                if keyMap.get(commonType) is None:  #未识别的物品，保存到其它后跳过
                    keyMap[commonType] = commonType
                    add_dict_all(equipmentForamted['其它']['其它'],partDir)
                    continue
                if not isinstance(partDir,dict):    #直接放到根目录的物品，保存到其它后跳过
                    if isinstance(partDir,str):
                        id_, name = commonType, partDir
                        equipmentForamted['其它']['其它'][id_] = name.strip()
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
                                equipmentForamted['其它']['其它'][id_] = name.strip()
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
                                equipmentForamted['特殊装备']['其它'][id_] = name.strip()
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

stringMap = {
    'HP':'HP', 'MP':'MP', 'physical':'物理', 'defense':'防御', 'magical':'魔法', 'attack':'攻击', 'water':'水(冰)属性', 'resistance':'抗性','regen':'恢复','MAX':'最大值',
    'speed':'速度','skill':'技能','level':'等级','up':'上升','separate':'独立','rate':'比率','move':'移动','hit recovery':'硬直','jump':'跳跃','power':'抛瓦','inventory':'物品',
    'limit':'上限','fire':'火属性','stuck':'命中','elemental':'元素','property':'属性','critical hit':'暴击','all':'全','stone':'石化','dark':'暗属性','light':'光属性',
    'hold':'束缚','slow':'减速','equipment':'装备','rigidity':'僵直','poison':'毒','activestatus':'异常状态','room':'房间','list':'列表','cast':'吟唱','element':'元素'
}
stringMap_sorted = list(stringMap.items())
stringMap_sorted.sort(key=lambda x:len(x[0]),reverse=True)#把长的词放在前面

def string_2_Zh(string:str):
    if not isinstance(string,str):
        return string
    for key,value in stringMap_sorted:
        string = string.replace(key,value)
    return string.replace(' ','')

def get_card_dict(cacheDict=None):
    if cacheDict is None:
        cacheDict = PVFcacheDict
    cardDict_zh = {}
    enhanceDict_zh = {'[特殊]':{}}
    itemInDict_dict = cacheDict['stackable_detail']
    print('加载怪物卡片...')
    for itemID,itemInDict in itemInDict_dict.items():
        enhanceSeg = itemInDict.get('[enchant]')
        if enhanceSeg is None: continue
        if isinstance(enhanceSeg,dict):
            cardDict_zh[itemID] = {}
            for enhanceKey,enhanceValueInList in enhanceSeg.items():
                enhanceKey_zh = string_2_Zh(enhanceKey)
                if isinstance(enhanceValueInList,list):
                    enhanceValueInList = [string_2_Zh(string) for string in enhanceValueInList]
                    if enhanceKey_zh not in enhanceDict_zh.keys():
                        enhanceDict_zh[enhanceKey_zh] = {itemID:enhanceValueInList}
                    else:
                        enhanceDict_zh[enhanceKey_zh][itemID] = enhanceValueInList
                    cardDict_zh[itemID][enhanceKey_zh] = enhanceValueInList
                else:
                    enhanceDict_zh['[特殊]'][itemID] = enhanceSeg  # dict
                    cardDict_zh[itemID]['[特殊]'] = enhanceSeg 
                    break
    print(f'怪物卡片加载完成({len(cardDict_zh)})')
    return cardDict_zh,enhanceDict_zh


def loadItems2(usePVF=False,pvfPath='',MD5='0',pool=None):        
    global ITEMS_dict,  PVFcacheDict, magicSealDict, jobDict, equipmentDict, stackableDict, avatarHiddenList, expTableList
    global enhanceDict_zh, cardDict_zh, equipmentForamted, creatureEquipDict, dungeonDict
    if pvfPath=='':
        pvfPath = config.get('PVF_PATH')
    if usePVF :
        p = Path(pvfPath)
        if  MD5 in cacheManager.allMD5():
            if cacheManager.get(MD5) is not None:
                PVFcacheDict = cacheManager.get(MD5)
                info = f'加载pvf缓存完成'
                print(info)
                config['PVF_PATH'] = MD5
        elif  '.pvf' in pvfPath and p.exists():
            MD5 = hashlib.md5(open(pvfPath,'rb').read()).hexdigest().upper()
            if MD5 in cacheManager.allMD5():
                PVFcacheDict = cacheManager.get(MD5)
                info = f'加载pvf缓存完成' 
            else:
                pvf = pvfReader.TinyPVF(pvfHeader=pvfReader.PVFHeader(pvfPath))
                print('加载PVF中...\n',pvf.pvfHeader)
                all_items_dict = pvfReader.LOAD_FUNC(pvf,pool)
                if all_items_dict==False:
                    return False
                del pvf
                PVFcacheDict = {}
                PVFcacheDict['magicSealDict'] = all_items_dict.pop('magicSealDict')
                PVFcacheDict['jobDict'] = all_items_dict.pop('jobDict')
                PVFcacheDict['equipment'] = all_items_dict.pop('equipment')
                PVFcacheDict['stackable'] = all_items_dict.pop('stackable')
                PVFcacheDict['avatarHidden'] = all_items_dict.pop('avatarHidden')
                PVFcacheDict['expTable'] = all_items_dict.pop('expTable')
                PVFcacheDict['pvfPath'] = str(pvfPath)
                PVFcacheDict['stackable_detail'] = all_items_dict.pop('stackable_detail')
                PVFcacheDict['equipment_detail'] = all_items_dict.pop('equipment_detail')
                PVFcacheDict['nickName'] = 'None'
                PVFcacheDict['MD5'] = MD5
                PVFcacheDict['equipmentStructuredDict'] = all_items_dict.pop('equipmentStructuredDict')
                PVFcacheDict['equipment_formated'] = equipmentDetailDict_transform()
                PVFcacheDict.pop('equipmentStructuredDict')
                PVFcacheDict['creatureEqu'] = creatureEquipDict
                PVFcacheDict['cardZh'],PVFcacheDict['enhanceZh'] = get_card_dict()
                PVFcacheDict['dungeon'] = all_items_dict.pop('dungeon')
                PVFcacheDict['quest'] = all_items_dict.pop('quest')
                info = f'加载pvf文件完成'
                
                save_PVF_cache()
                #print(f'pvf cache saved. {PVFcacheDict.keys()}')                
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
        equipmentForamted = PVFcacheDict['equipment_formated']
        creatureEquipDict = PVFcacheDict['creatureEqu']
        cardDict_zh = PVFcacheDict['cardZh']
        enhanceDict_zh = PVFcacheDict['enhanceZh']
        avatarHiddenList_En = copy.deepcopy(PVFcacheDict['avatarHidden'])
        dungeonDict = PVFcacheDict['dungeon']
        if len(PVFcacheDict['expTable'])!=0:
            expTableList = PVFcacheDict['expTable']
        info += f' 物品：{len(PVFcacheDict["stackable"].keys())}条，装备{len(PVFcacheDict["equipment"])}条'
    else:
        csvList = list(filter(lambda item:item.name[-4:].lower()=='.csv',[item for item in csvPath.iterdir()]))
        #print(f'物品文件列表:',csvList)
        ITEMS = []
        for fcsv in csvList:
            csv_reader = list(csv.reader(open(fcsv,errors='ignore')))[1:]
            ITEMS.extend(csv_reader)
        for item in ITEMS:
            if len(item)<2:
                print(item)
            else:
                ITEMS_dict[int(item[1])] = item[0]
        magicSealDict = json.load(open(magicDictPath,'r'))
        jobDict = json.load(open(jobPath,'r'))
        avatarHiddenList_En = json.load(open(avatarPath,'r'))
        expTableList = json.load(open(expTablePath,'r'))
        info = f'加载csv文件获得{len(ITEMS)}条物品信息记录，魔法封印{len(magicSealDict.keys())}条'

    for key,value in ITEMS_dict.items():
        ITEMS_dict[key] = value.strip()

    magicSealDict_tmp = {}
    for key,value in magicSealDict.items():
        magicSealDict_tmp[int(key)] = value
    magicSealDict = magicSealDict_tmp
    jobDict_tmp = {}
    for key,value in jobDict.items():
        valueNew = {}
        for key1, value1 in value.items():
            valueNew[int(key1)] = value1.strip()
        jobDict_tmp[int(key)] = valueNew
    jobDict = jobDict_tmp

    for i in range(len(avatarHiddenList_En)):
        for j,value in enumerate(avatarHiddenList_En[i]):
            avatarHiddenList_En[i][j] = avatarHiddenMap[value]
    avatarHiddenList = avatarHiddenList_En
    json.dump(config,open(configPath,'w'),ensure_ascii=False)
    return info

loadItems2()


