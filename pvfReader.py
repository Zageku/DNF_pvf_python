import struct
from struct import unpack
import multiprocessing
import json

'''
    TODO: 更多种类文件的解密读取。

    PVF存储结构：
    header 头部，不加密，存储有文件树的密钥
    fileTree 文件树，使用头部的密钥进行加密，解密后是对应文件的大小、偏移、文件路径、密钥
    data 文件数据，各自使用对应的密钥进行加密

    pvf文件：
    stringtable.bin 存储有所有的文本字段，其他文件只存储文本的字段索引。代码使用StringTable类处理
    n_string.lst 存储有一些str文件的路径

    *.str 表示一些stringTable的等价文本替换，例如 growtype_name_0 等同于 格斗家。代码使用Str类处理
    *.lst id列表，例如 stackable.lst，存着物品id和对应的物品文件（.stk）之间的映射列表。代码使用Lst类处理
    *.stk 物品文件，解密后按字节读取，替换为stringtable对应文本。部分stk需要使用str文本进行二次替换（字段为0x09和0x0a）。代码使用

'''

def decrypt_Bytes(inputBytes:bytes,crc):
    '''对原始字节流进行初步预处理'''
    key = 0x81A79011
    xor = crc ^ key
    int_num = len(inputBytes)//4
    key_all = xor.to_bytes(4,'little')*int_num
    value_Xored_all = int.from_bytes(key_all,'little') ^ int.from_bytes(inputBytes,'little')
    mask_1 = 0b00000000_00000000_00000000_00111111
    mask_2 = 0b11111111_11111111_11111111_11000000
    mask_1_all = int.from_bytes(mask_1.to_bytes(4,'little')*int_num,'little')
    mask_2_all = int.from_bytes(mask_2.to_bytes(4,'little')*int_num,'little')
    value_1 = value_Xored_all & mask_1_all
    value_2 = value_Xored_all & mask_2_all
    value = value_1<<26 | value_2>>6
    return value.to_bytes(4*int_num,'little')

class PVFHeader():
    def __init__(self,path):
        fp = open(path,'rb')
        self.pvfPath = path
        self.uuid_len = struct.unpack('i',fp.read(4))[0]
        self.uuid = fp.read(self.uuid_len)
        self.PVFversion = struct.unpack('i',fp.read(4))[0]
        self.dirTreeLength = struct.unpack('i',fp.read(4))[0] #长度
        self.dirTreeCrc32 = struct.unpack('I',fp.read(4))[0]
        self.numFilesInDirTree:int = struct.unpack('I',fp.read(4))[0]
        self.filePackIndexShift = fp.tell() + self.dirTreeLength
        #读内部文件树头
        unpackedHeaderTree = fp.read(self.dirTreeLength)
        #int_num = header.dirTreeLength//4
        self.unpackedHeaderTreeDecrypted = decrypt_Bytes(unpackedHeaderTree,self.dirTreeCrc32)
        self.index = 0  #用于读取HeaderTree的指针
        self.fp = fp
        tmp_index = fp.tell()
        fp.seek(0)
        self.fullFile = fp.read()
        fp.seek(tmp_index)
    def get_Header_Tree_Bytes(self,byte_num=4):
        res = self.unpackedHeaderTreeDecrypted[self.index:self.index+byte_num]
        self.index += byte_num
        return res

    def __repr__(self):
        return f'PVF [{self.uuid.decode()}]\nVer:{self.PVFversion}\nTreeLength:{self.dirTreeLength} \nCRC:{hex(self.dirTreeCrc32)}\n{self.numFilesInDirTree} files'
    __str__ = __repr__

class StringTable():
    '''stringtable.bin文件对象'''
    def __init__(self,tableBytes:bytes) -> None:
        self.length = struct.unpack('I',tableBytes[:4])[0]
        self.StringTableStrIndex = tableBytes[4:]#4+self.length*4*2
        self.stringTableChunk = tableBytes[4+self.length*4*2:]
    def __getitem__(self,n):
        #print(len(self.StringTableStrIndex),n*4,n*4+8)
        StrIndex = struct.unpack('<II',self.StringTableStrIndex[n*4:n*4+8])
        value = self.StringTableStrIndex[StrIndex[0]:StrIndex[1]].decode('big5','ignore')
        return value

class Str():
    '''处理*.str文件'''
    def __init__(self,contentText):
        self.text = contentText
        lines = filter(lambda l:'>' in l,self.text.split('\n'))
        self.strDict = {}
        for line in lines:
            key,value = line.split('>',1)
            self.strDict[key] = value
    def __getitem__(self,key):
        return self.strDict.get(key)
    
    def __repr__(self):
        return 'Str object. <'+str(self.strDict.items())[:100] + '...>'
    __str__ = __repr__

class Lst_lite2():
    '''处理*.lst文件对象'''
    def __init__(self,contentBytes,tinyPVF,stringtable,encode='big5',baseDir=''):
        self.vercode = contentBytes[:2]
        self.tableList = []
        self.tableDict = {} #存储lst的数据
        self.strDict = {}   #存储索引对应的str对象
        self.tinyPVF = tinyPVF
        self.fileContentDict = tinyPVF.fileContentDict
        self.stringtable:StringTable = stringtable
        self.baseDir = baseDir
        i = 2
        while i+10<=len(contentBytes):
            a,aa,b,bb = struct.unpack('<bIbI',contentBytes[i:i+10])
            if a==2:
                index = aa
            elif a==7:
                StrIndexIndex = aa
            if b==2:
                index = bb
            elif b==7:
                StrIndexIndex = bb
            string = self.stringtable[StrIndexIndex]
            if encode!='big5':
                string = string.encode('big5').decode(encode,'ignore')
            self.tableList.append([index,string])
            self.tableDict[index] = string
            self.encode = encode
            i+=10
    def __getitem__(self,n):
        '''返回字符串'''
        return self.tableDict[n]

    def get_N_Str(self,n)->Str:
        res = self.strDict.get(n)
        if res is None:
            content = self.fileContentDict.get(self.tableDict[n].lower())
            if content is None:
                content = self.tinyPVF.read_File_In_Decrypted_Bin(self.tableDict[n].lower())
            self.strDict[n] = Str(content.decode(self.encode,'ignore'))#self.getStr(path=self.tableDict[n])
            res = self.strDict.get(n)
        return res
    
    def __repr__(self):
        return 'Lst object. <'+str(self.tableList)[:100] + '...>'
    __str__ = __repr__


class TinyPVF():
    '''用于快速查询的pvf节点'''
    def __init__(self,pvfHeader:PVFHeader=None) -> None:
        self.pvfStructuredDict = {}   #按结构存储PVF文件树
        self.fileTreeDict = {}  #按 path: leaf存储文件树
        self.pvfHeader = pvfHeader
        self.fileContentDict = {}   #按路径或者物品id作为key存储文件内容
        self.stringTable:StringTable = None
        self.nString:Lst_lite2 = None
    
    def load_Leafs(self,dirs=[],paths=[],structured=False,pvfHeader:PVFHeader=None):
        '''按pvfHeader读取叶子，当structured为true时，同时会生成结构化的字典'''
        if pvfHeader is None:
            pvfHeader  = self.pvfHeader
        self.pvfHeader.index = 0
        for i in range(pvfHeader.numFilesInDirTree):
            leaf = {
                'fn' : unpack('I',pvfHeader.get_Header_Tree_Bytes(4))[0],
                'filePathLength' : unpack('I',pvfHeader.get_Header_Tree_Bytes(4))[0],
            }
            leaf.update({
                'filePath' : pvfHeader.get_Header_Tree_Bytes(leaf['filePathLength']).decode("CP949").lower(),  #全部转换为小写
                'fileLength' : (unpack('I',pvfHeader.get_Header_Tree_Bytes(4))[0]+ 3) & 0xFFFFFFFC,
                'fileCrc32' : unpack('I',pvfHeader.get_Header_Tree_Bytes(4))[0],
                'relativeOffset' : unpack('I',pvfHeader.get_Header_Tree_Bytes(4))[0],
            })
            if leaf['filePath'][0] == '/':
                leaf['filePath'] = leaf['filePath'][1:]
            if len(dirs)>0 or len(paths)>0:
                leafpaths = leaf['filePath'].split('/')
                if len(leafpaths)>1 and leafpaths[0] not in dirs and leaf['filePath'] not in paths:
                    continue
            self.fileTreeDict[leaf['filePath']] = leaf  #存到路径：文件字典
            if structured:
                dirs = leaf['filePath'].split('/')[1:-1]
                targetDict = self.pvfStructuredDict
                for dirName in dirs:
                    if dirName not in targetDict.keys():
                        targetDict[dirName] = {}
                    targetDict = targetDict[dirName]
                targetDict[leaf['filePath']] = leaf         #存到结构文件字典
        if self.stringTable is None:
            self.stringTable = StringTable(self.read_File_In_Decrypted_Bin('stringtable.bin'))
            self.nString = Lst_lite2(self.read_File_In_Decrypted_Bin('n_string.lst'),self,self.stringTable)
        return self.fileTreeDict

    def load_Lst_File(self,path='',encode='big5'):
        '''读取并创建lst对象'''
        content = self.read_File_In_Decrypted_Bin(path)
        if '/' in path:
            baseDir,basename = path.rsplit('/',1)
        else:
            baseDir = ''
            basename = path
        return Lst_lite2(content,self,self.stringTable,encode,baseDir)    
    def read_File_In_Decrypted_Bin(self,fpath:str='',pvfHeader=None):
        '''传入路径，返回初步解密后的字节流'''
        fpath = fpath.lower()
        if fpath[0]=='/':
            fpath = fpath[1:]
        leaf =  self.fileTreeDict.get(fpath)
        if leaf is None:
            self.load_Leafs(paths=[fpath])
            leaf =  self.fileTreeDict.get(fpath)
        if pvfHeader is None:
            pvfHeader = self.pvfHeader
        if self.fileContentDict.get(fpath) is not None:
            return self.fileContentDict.get(fpath)
        #res = decrypt_Bytes(get_FilePack_FileDict_FullPack(leaf,pvfHeader),leaf['fileCrc32'])
        #res = decrypt_Bytes(get_FilePack_FileDict_pvfPath(leaf,pvfHeader,pvfHeader.pvfPath),leaf['fileCrc32'])
        try:
            res = decrypt_Bytes(pvfHeader.fullFile[pvfHeader.filePackIndexShift+leaf['relativeOffset']:pvfHeader.filePackIndexShift+leaf['relativeOffset']+leaf['fileLength']] ,leaf['fileCrc32'])
        except:
            print(fpath,leaf)
            res = b''
        self.fileContentDict[fpath] = res
        return res
    
    @staticmethod
    def content2List(content,stringtable:StringTable,nString:Lst_lite2):
        '''读取二进制文本，如stk文件，将解密字段类型和关键字返回为list'''
        if content is None:
            return[[],[]]
        shift = 2
        unit_num = (len(content)-2)//5
        structPattern = '<'
        unitTypes = []
        for i in range(unit_num):
            unitType = content[i*5+shift]
            unitTypes.append(unitType)
            if unitType in [2,3,5,6,7,8,9,10]:
                structPattern+='BI'
            elif unitType in [4]:
                structPattern+='Bf'
            else:
                structPattern+='BI'
        units = struct.unpack(structPattern,content[2:2+5*unit_num])
        types = units[::2]
        values = units[1::2]
        valuesRead = []
        for i in range(unit_num):
            if types[i] in [2]:
                valuesRead.append(values[i])
            if types[i] in [3]:
                valuesRead.append(values[i])
            elif types[i] in [4]:
                valuesRead.append(values[i])
            elif types[i] in [5]:
                valuesRead.append(stringtable[values[i]])
            elif types[i] in [6]:
                valuesRead.append(stringtable[values[i]])
            elif types[i] in [7]:
                valuesRead.append(stringtable[values[i]])
            elif types[i] in [8]:
                valuesRead.append(stringtable[values[i]])
            elif types[i] in [9]:
                valuesRead.append(nString.get_N_Str(values[i])[stringtable[values[i+1]]])
        return [types,valuesRead]
    
    def read_File_In_List2(self,fpath='',pvfheader:PVFHeader=None,stringtable:StringTable=None,nString:Lst_lite2=None,fileTreeDict:dict=None):
        if pvfheader is None:
            pvfheader = self.pvfHeader
        if stringtable is None:
            stringtable = self.stringTable
        if nString is None:
            nString  = self.nString
        if fileTreeDict is None:
            fileTreeDict = self.fileTreeDict
        if '//' in fpath:
            fpath = fpath.replace('//','/')
        content = self.read_File_In_Decrypted_Bin(fpath)
        return self.content2List(content,stringtable,nString)
        '''shift = 2
        unit_num = (len(content)-2)//5
        structPattern = '<'
        for i in range(unit_num):
            unitType = content[i*5+shift]
            if unitType in [2,3,5,6,7,8,9,10]:
                structPattern+='BI'
            elif unitType in [4]:
                structPattern+='Bf'
            else:
                structPattern+='BI'
        units = struct.unpack(structPattern,content[2:2+5*unit_num])
        
        types = units[::2]
        values = units[1::2]
        valuesRead = []
        for i in range(unit_num):
            if types[i] in [2]:
                valuesRead.append(values[i])
            if types[i] in [3]:
                valuesRead.append(values[i])
            elif types[i] in [4]:
                valuesRead.append(values[i])
            elif types[i] in [5]:
                valuesRead.append(stringtable[values[i]])
            elif types[i] in [6]:
                valuesRead.append(stringtable[values[i]])
            elif types[i] in [7]:
                valuesRead.append(stringtable[values[i]])
            elif types[i] in [8]:
                valuesRead.append(stringtable[values[i]])
            elif types[i] in [9]:
                valuesRead.append(nString.get_N_Str(values[i])[stringtable[values[i+1]]])
        return [types,valuesRead]'''

    def read_Segment_With_Key(self,fpath='',key='')->list:
        '''将指定二进制文件按stk规则读取后返回dict'''
        stkvalue = self.read_File_In_List2(fpath)
        start = False
        res = []
        for value in stkvalue[1]:
            if value == key:
                start = True
            elif start and len(str(value))>0 and str(value)[0]=='[' and str(value)[-1]==']':
                if len(res) == 0:
                    res.append(value)
                break
            elif start:
                res.append(value)
        return res   
    
def get_Magic_Seal_Dict2(pvf:TinyPVF):
    import zhconv
    magicSealPath = r'etc/randomoption/randomizedoptionoverall2.etc'
    print('魔法封印加载...')
    try:
        res = pvf.read_File_In_List2(magicSealPath)
        postFixStart = False
        magicSealDict = {}
        for i in range(len(res[1])-1):
            if res[1][i] == '[postfix]':
                postFixStart = True
            if res[1][i] == '[/postfix]':
                postFixStart = False
                break
            if postFixStart:
                if isinstance(res[1][i],int) and '/' not in str(res[1][i+1]):
                    try:
                        magicSealDict[res[1][i]] = zhconv.convert(res[1][i+1].replace('[','').replace(']','').split(':')[0],'zh-cn').strip()
                    except:
                        pass
    except Exception as e:
        print(f'魔法封印文件加载错误 {e}')
        magicSealDict = {0:'pvf魔法封印无法正常读取'}
    return magicSealDict

def get_Job_Dict2(pvf:TinyPVF):
    jobDict = {}
    print('角色信息加载...')
    try:
        characs = pvf.load_Lst_File('character/character.lst')
        for id_,path in characs.tableList:
            growTypes = {}
            chrFileInList = pvf.read_File_In_List2(characs.baseDir+'/'+path)
            i = 0
            printFlg = False
            for lines in chrFileInList[1]:
                if '[growtype name]' == lines.strip():
                    printFlg=True
                elif printFlg:
                    if '[' in lines:
                        break 
                    growTypes[i] = lines
                    i += 1
            jobDict[id_] = growTypes
    except:
        print('职业列表加载失败')
    return jobDict

def get_exp_table2(pvf:TinyPVF):
    try:
        expTablePath = r'character/exptable.tbl'
        expTableList = pvf.read_File_In_List2(expTablePath)
        expTableList = list(filter(lambda value:isinstance(value,int),expTableList[1]))
        #json.dump(expTableList,open('config/expTable.json','w'))
    except:
        print('等级经验列表加载失败')
        return []
    return expTableList

def get_Equipment_Dict2(pvf:TinyPVF):
    
    equipmentStructuredDict = {'character':{}}#拥有目录结构的dict
    equipmentDict = {}  #只有id对应的dict
    path = 'equipment/equipment.lst'
    
    print('装备信息加载...')
    try:
        ItemLst = pvf.load_Lst_File(path,encode='big5')
        for id_,path_ in ItemLst.tableList:
            dirs = path_.split('/')[:-1]
            detailedDict = equipmentStructuredDict
            for dirName in dirs:
                if dirName not in detailedDict.keys():
                    detailedDict[dirName] = {}
                detailedDict = detailedDict[dirName]

            fpath = ItemLst.baseDir+'/'+path_
            if '//' in fpath:
                fpath = fpath.replace('//','/')
            res = pvf.read_Segment_With_Key(fpath,'[name]')
            try:
                equipmentDict[id_] = ''.join(res)
            except:
                #print(res)
                equipmentDict[id_] = ''.join([str(item) for item in res])
            detailedDict[id_] = equipmentDict[id_]
            pvf.fileContentDict[id_] = pvf.fileContentDict[fpath.lower()]
    except:
        print('武器列表加载失败')
    return equipmentStructuredDict, equipmentDict

def get_Stackable_dict2(pvf:TinyPVF):
    path,encode = ['stackable/stackable.lst','big5']
    
    stackable_dict = {}
    print('物品信息加载...')
    try:
        ItemLst = pvf.load_Lst_File(path,encode=encode)
        for id_,path_ in ItemLst.tableList:
            fpath = ItemLst.baseDir+'/'+path_
            if '//' in fpath:
                fpath = fpath.replace('//','/')
            res = pvf.read_Segment_With_Key(fpath,'[name]')
            try:
                stackable_dict[id_] = ''.join(res)
            except:
                #print(id_,res)
                stackable_dict[id_]= ''.join([str(item) for item in res])
            pvf.fileContentDict[id_] = pvf.fileContentDict[fpath.lower()]
    except:
        print('道具列表加载失败')
    return stackable_dict

def get_Hidden_Avatar_List2(pvf:TinyPVF):
    avatarHiddenPath = 'etc/avatar_roulette/avatarfixedhiddenoptionlist.etc'
    print('时装潜力加载...')
    upper = False
    rare = False
    upperList = []
    rareList = []
    try:
        res = pvf.read_File_In_List2(avatarHiddenPath)
        for value in res[1]:
            if value == '[upper]':
                upper = True
                continue
            if value == '[/upper]':
                upper = False
                continue
            if value == '[rare]':
                rare = True
                continue
            if value == '[/rare]':
                rare = False
                continue
            if '[' in str(value) and upper:
                upperList.append(value[1:-1])
            if '[' in str(value) and rare:
                rareList.append(value[1:-1])
    except:
        print('时装潜能加载失败')
    #json.dump([upperList,rareList],open('./config/avatarHidden.json','w'))
    return upperList,rareList

def get_Item_Dict(pvf:TinyPVF):
    '''传入pvf文件树，返回物品id:name的字典'''
    try:
        pvf.load_Leafs(['stackable','character','etc','equipment'],paths=['etc/avatar_roulette/avatarfixedhiddenoptionlist.etc'])
    except Exception as e:
        print(f'PVF目录树加载失败，{e}')
        return False

    all_item_dict = {}
    magicSealDict = get_Magic_Seal_Dict2(pvf)
    all_item_dict['magicSealDict'] = magicSealDict

    jobDict = get_Job_Dict2(pvf)
    all_item_dict['jobDict'] = jobDict
    print(jobDict)
    expTable = get_exp_table2(pvf)
    all_item_dict['expTable'] = expTable

    equipmentStructuredDict, equipmentDict = get_Equipment_Dict2(pvf)
    all_item_dict['equipment'] = equipmentDict
    all_item_dict['equipmentStructuredDict'] = equipmentStructuredDict

    stackable_dict = get_Stackable_dict2(pvf)
    all_item_dict['stackable'] = stackable_dict

    all_item_dict['idPathContentDict'] = pvf.fileContentDict
    all_item_dict['avatarHidden'] = get_Hidden_Avatar_List2(pvf)
    return all_item_dict

def test5():
    PVF = r'E:\system sound infomation\客户端20221030\客户端20230212\KHD\Script.pvf'
    pvfHeader=PVFHeader(PVF)
    pvf = TinyPVF(pvfHeader=pvfHeader)   
    items = get_Item_Dict(pvf)
    print('加载完成...')
    for key,value in items.items():
        if isinstance(value,str):
            continue
        print(key,len(value))
if __name__=='__main__':
    test5()


    



