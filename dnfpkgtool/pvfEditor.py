import struct
from struct import unpack
from zhconv import convert
import json
from pathlib import Path
from .pvfReader import *
import zlib
import random
from . import cacheManager as cacheM
'''
    保存文件：
    0、 不增加文件，只修改文件
    1、 所有修改过的文件保存在 editedLeafDict 中
    2、 editedLeafDict 文件CRC全部设定为 KEY
    3、 生成文件块和文件树
        对原始文件树所有leaf进行遍历，重新计算文件的偏移（树）
        如果文件是编辑后的，重新进行加密后放入文件块
        如果文件未被加密，直接原始数据放入文件快
    4、 文件树的长度应该没有变化，对文件树进行加密
    5、 拼接文件头，文件树，文件块，导出数据

'''
KEY = 0x81A79011
INT = 2
STRING = 7
LSTPATHDICT = {
    'stackable':['stackable/stackable.lst','.stk'],
    'equipment':['equipment/equipment.lst','equ'],
    #'dungeon':['dungeon/dungeon.lst','.dgn']
} 

keywords = []
keyWordPath = Path('./config/pvfKeywords.json')
if keyWordPath.exists():
    try:
        keywords = json.load(open(keyWordPath,'r'))
    except:
        pass

keywordsDict ={}
subKeywordsDict = {}
keywordsDictPath = Path('./config/pvfKeywordsDict.json')
if keywordsDictPath.exists():
    try:
        keywordsDict = json.load(open(keywordsDictPath,'r'))
    except Exception as e:
        print(e)
        pass

#print(keywordsDict.keys())

SegKeyDict = {}
with open('./config/stkTypeDict.json','r') as f:
    SegKeyDict['stackable'] = json.load(f)
with open('./config/equTypeDict.json','r') as f:
    SegKeyDict['equipment'] = json.load(f)

GEN_KEYWORD = len(keywords)>0 or keywordsDict!={}

def decrypt_Bytes(inputBytes:bytes,crc=0x81A79011):
    '''对原始字节流进行初步预处理'''
    xor = crc ^ KEY
    length = len(inputBytes)
    inputBytes += b'\x00' * ((4-(len(inputBytes)%4)) % 4)
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
    return value.to_bytes(4*int_num,'little')[:length]

def encrypt_Bytes(inputBytes:bytes,crc=0x81A79011):
    inputBytes += b'\x00' * ((4-(len(inputBytes)%4)) % 4)
    int_num = len(inputBytes)//4
    inputValue = int.from_bytes(inputBytes,'little')
    mask_1 = 0b11111100_00000000_00000000_00000000
    mask_2 = 0b00000011_11111111_11111111_11111111
    mask_1_all = int.from_bytes(mask_1.to_bytes(4,'little')*int_num,'little')
    mask_2_all = int.from_bytes(mask_2.to_bytes(4,'little')*int_num,'little')
    value_1 = inputValue & mask_1_all
    value_2 = inputValue & mask_2_all
    value = value_1>>26 | value_2<<6

    xor = crc ^ KEY
    key_all = xor.to_bytes(4,'little')*int_num
    value_Xored_all = int.from_bytes(key_all,'little') ^ value

    return value_Xored_all.to_bytes(4*int_num,'little')



def rec_merge(d1, d2)->dict:
    """
    递归合并字典
    :param d1: {"a": {"c": 2, "d": 1}, "b": 2}
    :param d2: {"a": {"c": 1, "f": {"zzz": 2}}, "c": 3, }
    :return: {'a': {'c': 1, 'd': 1, 'f': {'zzz': 2}}, 'b': 2, 'c': 3}
    """
    for key, value in d2.items():
        if key not in d1:
            d1[key] = value
        else:
            if isinstance(value, dict):
                rec_merge(d1[key], value)
            else:
                d1[key] = value
    return d1

class StringTableEditor(StringTable):
    '''stringtable.bin文件对象'''
    def __init__(self,tableBytes:bytes,encode='big5') -> None:
        self.bytes = tableBytes
        self.encode = encode
        self.addNum = 0
        self.length:int = struct.unpack('I',tableBytes[:4])[0]  #字符串索引长度，共有length个字符串，（length+1）个int
        self.StringTableStrIndexBytes = bytearray(tableBytes[4:4+self.length*4+4])#4+self.length*4*2
        self.stringTableChunk = bytearray(tableBytes[4+self.length*4+4:])
        self.converted = False
        self.convertChunk = []
        self.stringRevMap = {}  #保存字符串到索引的转换
        self.genMapDict()
    def __getitem__(self,n):
        # 指第n和n+1个int，不是第n组int
        try:
            StrIndex = struct.unpack('<II',self.StringTableStrIndexBytes[n*4:n*4+8])
            bias = self.length*4 + 4
            value = convert(self.stringTableChunk[StrIndex[0]-bias:StrIndex[1]-bias].decode(self.encode,'ignore'),'zh-cn').replace('\r','')
        except:
            print(f'索引超出限制，当前:{n}，总长：{self.length+self.addNum},{self.StringTableStrIndexBytes[n*4:n*4+8]} {len(self.StringTableStrIndexBytes[n*4:n*4+8])}')
            value = 'error'
        #print(value)
        return value
    def __getitem1__(self,n):
        # 指第n和n+1个int，不是第n组int
        StrIndex = struct.unpack('<II',self.StringTableStrIndexBytes[n*4:n*4+8])
        value = convert(self.StringTableStrIndexBytes[StrIndex[0]:StrIndex[1]].decode(self.encode,'ignore'),'zh-cn')#.replace('\r','')
        #print(value)
        return value
    def genMapDict(self):
        print(f'正在遍历stringtable字典...文件编码：{self.encode}')
        for n in range(self.length):
            string = self.__getitem__(n)
            if self.stringRevMap.get(string) is not None:
                continue
            self.stringRevMap[string] = n

    def add(self,string='',force=False):
        if self.stringRevMap.get(string) is not None and force==False:
            return self.stringRevMap.get(string)
        
        startIndex = int.from_bytes(self.StringTableStrIndexBytes[-4:],'little')
        if self.encode == 'big5':
            string = convert(string,'zh-tw')
        strBin = string.encode(self.encode,'replace')
        stopIndex = startIndex + len(strBin)
        self.stringTableChunk += strBin
        self.StringTableStrIndexBytes += struct.pack('I',stopIndex)
        self.addNum += 1
        print(f'stringtable新增字符：{string.strip()}-{self.length + self.addNum - 1}')
        self.stringRevMap[string] = self.length + self.addNum - 1
        return self.length + self.addNum - 1    #从0开始索引，需要-1
    def to_bytes_old(self):
        StrIndexBytes_new = bytearray()
        print('新增字符数：',self.addNum,f'总字符数:{self.length}->{self.length+self.addNum}')
        for i in range(self.length+1+self.addNum):
            intValue:int = int.from_bytes(self.StringTableStrIndexBytes[i*4:i*4+4],'little')
            intValue_new = intValue + self.addNum*4
            StrIndexBytes_new += intValue_new.to_bytes(4,'little')
        length_new = self.length+self.addNum
        #res = length_new.to_bytes(4,'little') + StrIndexBytes_new + self.stringTableChunk
        length = self.length+1+self.addNum + len(self.stringTableChunk)
        if length%4!=0:
            print(f'stringtable补充字符：{(4-length%4)}')
            zeroNum = (4-length%4)
            self.stringTableChunk += b'\x00' * zeroNum
            StrIndex_last = int.from_bytes(StrIndexBytes_new[-4:],'little')
            StrIndex_last += zeroNum
            StrIndexBytes_new[-4:] = StrIndex_last.to_bytes(4,'little')
        res = length_new.to_bytes(4,'little') + StrIndexBytes_new + self.stringTableChunk
        return res

    def to_bytes(self):
        StrIndexBytes_new = bytearray()
        print('新增字符数：',self.addNum,f'总字符数:{self.length}->{self.length+self.addNum}')
        
        #res = length_new.to_bytes(4,'little') + StrIndexBytes_new + self.stringTableChunk
        length = len(self.stringTableChunk)
        if length%4!=0:
            print(f'stringtable补充字符：{(4-length%4)}')
            zeroNum = (4-length%4)
            self.add('0'*zeroNum,True)
        for i in range(self.length+1+self.addNum):
            intValue:int = int.from_bytes(self.StringTableStrIndexBytes[i*4:i*4+4],'little')
            intValue_new = intValue + self.addNum*4
            StrIndexBytes_new += intValue_new.to_bytes(4,'little')
        length_new = self.length+self.addNum
        res = length_new.to_bytes(4,'little') + StrIndexBytes_new + self.stringTableChunk
        return res

        
class LstEditor():
    '''处理*.lst文件对象'''
    def __init__(self,contentBytes,stringtable:StringTableEditor,encode='big5',baseDir='',suffix=''):
        self.vercode = contentBytes[:2]
        self.suffix = suffix
        self.contenBytes = contentBytes
        self.tableList = []
        self.tableDict_rev = {}
        self.tableDict = {} #存储lst的数据
        self.strDict = {}   #存储索引对应的str对象
        self.tableList_extend = []  #存储新添加的数据
        self.tableList_remove = []  #存储要删除的数据
        self.stringtable:StringTableEditor = stringtable
        self.baseDir = baseDir
        self.encode = encode
        i = 2
        while i+10<=len(contentBytes):
            a,aa,b,bb = struct.unpack('<bIbI',contentBytes[i:i+10]) # 字符串/数据 或者 数据/字符串
            if a==INT:
                index = aa
            elif a==STRING:
                StrIndexIndex = aa
            if b==INT:
                index = bb
            elif b==STRING:
                StrIndexIndex = bb
            string = self.stringtable[StrIndexIndex]
            self.tableList.append([index,string])
            self.tableDict[index] = string
            self.tableDict_rev[string.rsplit('.')[0]] = [index]
            
            i+=10
    def __getitem__(self,n):
        '''返回字符串'''
        return self.tableDict[n]
        
    def add(self,itemID=0,string=''):
        if self.tableDict_rev.get(string.rsplit('.')[0]) is not None:
            return self.tableDict_rev.get(string.rsplit('.')[0]), string
        if itemID==0 or itemID is None:
            while True:
                itemID:int = random.randint(1,pow(2,15))
                if self.tableDict.get(itemID) is None and cacheM.ITEMS_dict.get(itemID) is None:
                    break
        if string=='':
            string = str(itemID)
        string += self.suffix
        self.tableList.append([itemID,string])
        self.tableDict[itemID] = string
        self.tableList_extend.append([itemID,string])
        return itemID,string
    
    def remove(self,itemID):
        self.remove(itemID)

    def to_bytes(self):
        res = bytearray(self.vercode)
        for itemID,string in self.tableList:
            if itemID in self.tableList_remove:
                continue
            res += INT.to_bytes(1,'little')
            res += itemID.to_bytes(4,'little')
            strIndex = self.stringtable.add(string)
            res += STRING.to_bytes(1,'little')
            res += strIndex.to_bytes(4,'little')
        return res        

    def __repr__(self):
        return 'LstEditor object. <'+str(self.tableList)[:100] + '...>'
    __str__ = __repr__


class TinyPVFEditor(TinyPVF):
    '''用于快速查询的pvf节点'''
    def __init__(self,pvfHeader:PVFHeader=None,encode = 'big5') -> None:
        self.pvfStructuredDict = {}   #按结构存储PVF文件树
        self.fileTreeDict = {}  #按 path: leaf存储文件树
        self.editedLeafDict = {}
        self.newLeafDict = {}
        self.leafInList = []
        #self.fnDict = {}    #记录所有的fn
        self.fnList = []
        self.pvfHeader = pvfHeader
        self.fileContentDict = {}   #按路径或者物品id作为key存储文件内容 #未启用
        self.stringTable:StringTableEditor = None
        self.nString:Lst_lite2 = None
        self.encode = encode
    
    def load_Leafs(self,dirs=[],structured=False):
        '''按pvfHeader读取叶子，当structured为true时，同时会生成结构化的字典'''
        pvfHeader  = self.pvfHeader
        self.structured = structured
        self.pvfHeader.index = 0
        print(f'加载文件树...文件编码：{self.encode}')
        for i in range(pvfHeader.numFilesInDirTree):
            index = pvfHeader.index
            fn_bytes = pvfHeader.get_Header_Tree_Bytes(4)
            
            filePathLength_bytes = pvfHeader.get_Header_Tree_Bytes(4)
            filePathLength = unpack('I',filePathLength_bytes)[0]
            filePath_bytes = pvfHeader.get_Header_Tree_Bytes(filePathLength)
            fileLength_bytes = pvfHeader.get_Header_Tree_Bytes(4)
            fileCrc32_bytes = pvfHeader.get_Header_Tree_Bytes(4)
            relativeOffset_bytes = pvfHeader.get_Header_Tree_Bytes(4)
            try:
                leaf = {
                    'index':index,
                    'fn' : unpack('I',fn_bytes)[0],'fn_bytes':fn_bytes,
                    'filePathLength' : unpack('I',filePathLength_bytes)[0],'filePathLength_bytes':filePathLength_bytes,
                    'filePath' : filePath_bytes.decode("CP949").lower(),  #全部转换为小写
                    'filePath_bytes':filePath_bytes,
                    'fileLength' : (unpack('I',fileLength_bytes)[0]+ 3) & 0xFFFFFFFC,'fileLength_bytes':fileLength_bytes,
                    'fileLength_real':unpack('I',fileLength_bytes)[0],
                    'fileCrc32' : unpack('I',fileCrc32_bytes)[0],'fileCrc32_bytes':fileCrc32_bytes,
                    'relativeOffset' : unpack('I',relativeOffset_bytes)[0],
                    'content':b'',
                }
            except:
                print(fn_bytes,filePathLength,filePath_bytes,fileLength_bytes)
            #self.fnDict[leaf['fn']] = fn_bytes
            self.fnList.append(leaf['fn'])

            if leaf['filePath'][0] == '/':
                leaf['filePath'] = leaf['filePath'][1:]
            self.fileTreeDict[leaf['filePath']] = leaf  #存到路径：文件字典
            self.leafInList.append(leaf)
            if structured:
                dirs = leaf['filePath'].split('/')[1:-1]
                targetDict = self.pvfStructuredDict
                for dirName in dirs:
                    if dirName not in targetDict.keys():
                        targetDict[dirName] = {}
                    targetDict = targetDict[dirName]
                targetDict[leaf['filePath']] = leaf         #存到结构文件字典
            if i%100000==0:
                print(f'加载进度：{i//10000}/{pvfHeader.numFilesInDirTree//10000}')
        if self.stringTable is None:
            self.stringTable = StringTableEditor(self.read_File_In_Decrypted_Bin('stringtable.bin')[:self.fileTreeDict['stringtable.bin']['fileLength_real']],self.encode)
            self.nString = Lst_lite2(self.read_File_In_Decrypted_Bin('n_string.lst'),self,self.stringTable,self.encode)
            self.lstDict = {
            'stackable':LstEditor(self.read_File_In_Decrypted_Bin('stackable/stackable.lst'),self.stringTable,baseDir='stackable',suffix='.stk'),
            'equipment':LstEditor(self.read_File_In_Decrypted_Bin('equipment/equipment.lst'),self.stringTable,baseDir='equipment',suffix='.equ'),
            'dungeon':LstEditor(self.read_File_In_Decrypted_Bin('dungeon/dungeon.lst'),self.stringTable,baseDir='dungeon',suffix='.dgn')
            }
        return self.fileTreeDict
    
    @staticmethod
    def content2List_with_bin(content,stringtable:StringTableEditor,nString:Lst_lite2,stringQuote='',convertZhcn=False):
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
                structPattern+='Bi'
            elif unitType in [4]:
                structPattern+='Bf'
            else:
                structPattern+='Bi'
        units = struct.unpack(structPattern,content[2:2+5*unit_num])
        types = units[::2]
        values = units[1::2]
        binaryInList = []
        valuesRead = []
        typesInList = []
        for i in range(unit_num):
            binaryInList.append(content[2+5*i:2+5*i+5])
            typesInList.append(types[i])
            if types[i] in [2]:
                valuesRead.append(values[i])
            elif types[i] in [3]:
                valuesRead.append(values[i])
            elif types[i] in [4]:
                valuesRead.append(values[i])
            elif types[i] in [5]:
                valuesRead.append(stringtable[values[i]])
            elif types[i] in [6]:
                valuesRead.append(stringtable[values[i]])
            elif types[i] in [7]:
                valuesRead.append(stringQuote+stringtable[values[i]]+stringQuote)
            elif types[i] in [8]:
                valuesRead.append(stringtable[values[i]])
            elif types[i] in [9]:
                valuesRead.append(nString.get_N_Str(values[i])[stringtable[values[i+1]]])
                binaryInList[-1] += content[2+5*i+5:2+5*i+10]
            else:
                typesInList.pop(-1)
                binaryInList.pop(-1)
            length = len(valuesRead)
            #print(length,len(binaryInList))
            #print(valuesRead[length-1],content[2+5*i:2+5*i+5],binaryInList[length-1])
        if convertZhcn:
            valuesRead_old = valuesRead.copy()
            valuesRead = []
            for value in valuesRead_old:
                if isinstance(value,str):
                    try:
                        valuesRead.append(convert(value,'zh-cn'))
                    except:
                        valuesRead.append(value)
                else:
                    valuesRead.append(value)
        return [typesInList,valuesRead,binaryInList]

    @staticmethod
    def list2Dict_with_bin(fileInListWithTypeAndBin:list,formatDepth=-1):
        typeList,fileInList,binaryList = fileInListWithTypeAndBin
        
        segmentKeys = []    #存放带结束符的段落
        for i,value in enumerate(fileInList):
            if isinstance(value,str) and value[:2]=='[/' and value[-1]==']':
                segmentKeys.append(value.replace('/',''))
            #print(typeList[i],fileInList[i],binaryList[i])
        #print(fileInListWithType)
        res = {}
        segment = []    #保存段内容
        segTypes = []   #保存段内容的字段类型
        binarys = []    #保存原始数据，第一个数据是段名，最后多出来的是段结尾
        segmentKey = None
        multiFlg = False
        segmentInSegmentFlg = False
        for i,value in enumerate(fileInList):            
            checkNewSeg = False
            if typeList[i]==5:
                checkNewSeg = True
            if checkNewSeg:
                # 判断是否为新的段
                if multiFlg and value.replace('/','')!=segmentKey:
                    segmengFin = False
                    segmentInSegmentFlg = True   #是段中段的标识
                else:
                    if len(segment)>0 or '/' in value or segmentKey is None:
                        segmengFin = True
                    else:
                        segmengFin = False
                #print(segmentKey,value,'segmengFin:',segmengFin,'segmentInSegmentFlg:',segmentInSegmentFlg)
                if segmengFin: # 是新的段，保存数据，判断新段类型
                    #print('new seg,', value)
                    if segmentKey is not None:
                        if segmentInSegmentFlg and formatDepth!=0 and len(segment)>1:
                            res[segmentKey] = [TinyPVFEditor.list2Dict_with_bin([segTypes,segment,binarys]),binarys]
                        else:
                            res[segmentKey] = [segment,binarys]

                        #print(segmentKey,segment)
                    segmentInSegmentFlg = False
                    if '/' in value:
                        segmentKey = None
                        multiFlg = False
                    else:
                        segmentKey = value
                        if segmentKey in segmentKeys:
                            multiFlg = True #有结束符
                        else:
                            multiFlg = False
                        if res.get(segmentKey) is None:
                            segment = []
                            segTypes = []
                            binarys = []
                        else:
                            segment, binarys = res.get(segmentKey)
                            segTypes = []   #暂定出现两个同名段的时候，不会出现段中段
                        #print('--new segment',segmentKey)
                else:   # 不是新的段，添加数据
                    segment.append(value)
                    segTypes.append(typeList[i])
                    #binarys.append(binaryList[i])
            else:
                segment.append(value)
                segTypes.append(typeList[i])
                #binarys.append(binaryList[i])
            binarys.append(binaryList[i])
            #print(binarys)
        if len(segment)>0 and segmentKey is not None:
            res[segmentKey] = [segment,binarys]
            # 用于生成keywords文件
            if subKeywordsDict.get(segmentKey) is None:
                subKeywordsDict[segmentKey] = False
            #if segmentKey not in keywords:
            #    keywords.append(segmentKey)
        #print(res,'\n')
        return res

    def read_File_In_List_with_Bin(self,fpath='',pvfheader:PVFHeader=None,stringtable:StringTable=None,nString:Lst_lite2=None,fileTreeDict:dict=None,stringQuote=''):
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
        return self.content2List_with_bin(content,stringtable,nString,stringQuote)
    
    def read_FIle_In_Dict_with_Bin(self,fpath='',pvfheader:PVFHeader=None,stringtable:StringTable=None,nString:Lst_lite2=None,fileTreeDict:dict=None):
        fileInListWithTypeAndBin = self.read_File_In_List_with_Bin(fpath,pvfheader,stringtable,nString,fileTreeDict)
        return self.list2Dict_with_bin(fileInListWithTypeAndBin)
    
    @staticmethod
    def dict2list(fileInDict:dict,fileType='stackable'):
        def add(type,value):
            nonlocal valueList,valueTypeList
            if not isinstance(type,list):
                valueList.append(value)
                valueTypeList.append(type)
            else:
                valueList.extend(value)
                valueTypeList.extend(type)
        valueList = []
        valueTypeList = []
        segDict = keywordsDict.get(fileType)
        SEG_KEY = 5
        STRING = 7
        INT = 2
        FLOAT = 4
        CMD_SEP = 8
        CMD = 6
        for segmentKey,segment in fileInDict.items():
            add(SEG_KEY,segmentKey)
            if isinstance(segment,dict):
                type,value = TinyPVFEditor.dict2list(segment)
                add(type,value)
            else:
                if not isinstance(segment,list):
                    segment = [segment]
                for value in segment:
                    if isinstance(value,str):
                        add(STRING,value.replace('\r',''))
                    elif isinstance(value,int):
                        add(INT,value)
                    elif isinstance(value,float):
                        add(FLOAT)
            if segDict.get(segmentKey)==True:
                add(SEG_KEY,'[/'+segmentKey[1:])
                #print('段中段',segmentKey)
        return valueTypeList,valueList    
    
    def list2DecryptedBin(self,fileInList:list,prefix=b'\xb0\xd0',CMD=False):
        def build(fileInList):
            binary_tmp = bytearray()
            for value in fileInList:
                #print(value)
                if isinstance(value,dict):
                    for segKey,segValueList in value.items():
                        stringIndex  = self.stringTable.add(segKey)
                        binary_tmp += SEG_KEY.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')  #字段字节
                        if segKey=='[command]': #处理操作指令
                            binary_tmp += build(segValueList,CMD=True)
                        else:
                            binary_tmp += build(segValueList)
                        if segValueList[-1] is True:  #段末有结束符号
                            segKeyEndMark = '[/' + segKey[1:]
                            stringIndex  = self.stringTable.add(segKeyEndMark)
                            binary_tmp += SEG_KEY.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')  #字段字节
                else:
                    if isinstance(value,str):
                        
                        stringIndex = self.stringTable.add(value)    #stringtable添加新的字段
                        if CMD==False:
                            binary_tmp += STRING.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')
                        else:
                            if value==',':
                                binary_tmp += CMD8.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')
                            else:
                                binary_tmp += CMD6.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')

                    elif value is not True and isinstance(value,int):
                        binary_tmp += INT.to_bytes(1,'little') + struct.pack('i',value)#value.to_bytes(4,'little')
                    elif isinstance(value,float):
                        binary_tmp += FLOAT.to_bytes(1,'little') + struct.pack('f',value)
            return binary_tmp
        SEG_KEY = 5
        STRING = 7
        INT = 2
        FLOAT = 4
        CMD6 = 6
        CMD8 = 8
        binary = bytearray() + prefix
        binary += build(fileInList)
        '''for value in fileInList:
            print(value)
            if isinstance(value,dict):
                for segKey,segValueList in value.items():
                    stringIndex  = self.stringTable.add(segKey)
                    binary += SEG_KEY.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')  #字段字节
                    binary += self.list2DecryptedBin(segValueList,b'')
                    if segValueList[-1]==True:  #段末有结束符号
                        segKeyEndMark = '[/' + segKey[1:]
                        stringIndex  = self.stringTable.add(segKeyEndMark)
                        binary += SEG_KEY.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')  #字段字节
            else:
                if isinstance(value,str):
                    stringIndex = self.stringTable.add(value)    #stringtable添加新的字段
                    binary += STRING.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')
                elif isinstance(value,int):
                    binary += INT.to_bytes(1,'little') + struct.pack('i',value)#value.to_bytes(4,'little')
                elif isinstance(value,float):
                    binary += FLOAT.to_bytes(1,'little') + struct.pack('f',value)'''
        binary += b'\x00' * ((4-(len(binary)%4)) % 4)
        return binary

    def dict2DecryptedBin2(self,fileInDict:dict,filePath:str):
        '''完全新生成文件段'''
        def build(newDict:dict):
            '''TODO: 新字段的添加'''
            tmp_binary = b''
            for key,values in newDict.items():
                if key not in ['[possible kiri protect]'] and values==[] or values=={} or values=='':
                    continue    #空字段跳过
                if '-' in key:  # 多个同字段文件使用 - 后缀区分
                    key = key.split('-')[0]
                stringIndex  = self.stringTable.add(key)
                tmp_binary += SEG_KEY.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')  #字段字节
                if isinstance(values,dict): #是段中段
                    tmp_binary += build(values)
                elif isinstance(values,list):   #字段内数值处理
                    for i,value in enumerate(values):
                        if isinstance(value,str):
                            stringIndex = stringTable.add(value)    #stringtable添加新的字段
                            if key!='[command]':
                                tmp_binary += STRING.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')
                            else:
                                if value==',':
                                    tmp_binary += CMD8.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')
                                else:
                                    tmp_binary += CMD6.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')
                        elif isinstance(value,int):
                            tmp_binary += INT.to_bytes(1,'little') + struct.pack('i',value)#value.to_bytes(4,'little')
                        elif isinstance(value,float):
                            tmp_binary += FLOAT.to_bytes(1,'little') + struct.pack('f',value)
                    
                if segDict.get(key)==True and key!='[drop prob]':  #有段落结束符号
                    stringIndex  = self.stringTable.add('[/'+key[1:])
                    tmp_binary += SEG_KEY.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')  #字段字节
                #tmp_binary += SEG_KEY.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')  #字段字节

            return tmp_binary

        SEG_KEY = 5
        STRING = 7
        INT = 2
        FLOAT = 4
        CMD8 = 8
        CMD6 = 6
        fileType = filePath.split('/',1)[0]
        
        #print(keywordsDict.keys())
        segDict = keywordsDict.get(fileType)
        #print(fileType,segDict)
        stringTable = self.stringTable
        if '//' in filePath:
            filePath = filePath.replace('//','/')

        binary = b'\xb0\xd0'
        binary += build(fileInDict)
        binary += b'\x00' * ((4-(len(binary)%4)) % 4)
        return binary
    
    def _dict2DecryptedBin3(self,fileInDict:dict,filePath:str):
        '''完全新生成文件段'''
        def build(newDict:dict):
            '''TODO: 新字段的添加'''
            tmp_binary = b''
            for key,values in newDict.items():
                if values==[] or values=={} or values=='':
                    continue    #空字段跳过
                stringIndex  = self.stringTable.add(key)
                tmp_binary += SEG_KEY.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')  #字段字节
                if isinstance(values,dict): #是段中段
                    tmp_binary += build(values)
                elif isinstance(values,list):   #字段内数值处理
                    for i,value in enumerate(values):
                        if isinstance(value,str):
                            stringIndex = stringTable.add(value)    #stringtable添加新的字段
                            tmp_binary += STRING.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')
                        elif isinstance(value,int):
                            tmp_binary += INT.to_bytes(1,'little') + struct.pack('i',value)#value.to_bytes(4,'little')
                        elif isinstance(value,float):
                            tmp_binary += FLOAT.to_bytes(1,'little') + struct.pack('f',value)
                    
                if segDict.get(key)==True:  #有段落结束符号
                    stringIndex  = self.stringTable.add('[/'+key[1:])
                    tmp_binary += SEG_KEY.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')  #字段字节
                #tmp_binary += SEG_KEY.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')  #字段字节

            return tmp_binary

        SEG_KEY = 5
        STRING = 7
        INT = 2
        FLOAT = 4
        fileType = filePath.split('/',1)[0]
        segDict = keywordsDict.get(fileType)
        stringTable = self.stringTable
        if '//' in filePath:
            filePath = filePath.replace('//','/')

        binary = b'\xb0\xd0'
        binary += build(fileInDict)
        binary += b'\x00' * ((4-(len(binary)%4)) % 4)
        return binary
    
    def _dict2DecryptedBin(self,fileInDict:list,filePath:str):
        '''在原有字段的基础上编辑字段'''
        def build(newDict:dict,oldDictWithBytes:dict):
            '''TODO: 新字段的添加'''
            tmp_binary = b''
            for key,values in newDict.items():
                seg = oldDictWithBytes.get(key)
                if seg is None:
                    continue
                oldValues,oldBytes = seg
                tmp_binary += oldBytes[0]  #字段字节
                if isinstance(values,dict): #是段中段
                    tmp_binary += build(values,oldValues)
                elif isinstance(values,list):   #字段内数值处理
                    for i,value in enumerate(values):
                        if i<len(oldValues) and value==oldValues[i]: #没有变化
                            tmp_binary += oldBytes[i+1]
                            continue
                        elif isinstance(value,str):
                            stringIndex = stringTable.add(value)    #stringtable添加新的字段
                            tmp_binary += STRING.to_bytes(1,'little') + stringIndex.to_bytes(4,'little')
                        elif isinstance(value,int):
                            tmp_binary += INT.to_bytes(1,'little') + struct.pack('i',value)#value.to_bytes(4,'little')
                        elif isinstance(value,float):
                            tmp_binary += FLOAT.to_bytes(1,'little') + struct.pack('f',value)
                    if oldBytes[-1][0]==SEG_KEY:#原始字节结尾是字段（[/字段名]）
                        tmp_binary += oldBytes[-1]
            if oldBytes[-1][0]==SEG_KEY:#原始字节结尾是字段（[/字段名]）
                if tmp_binary[-5:]!=oldBytes[-1]:
                    tmp_binary += oldBytes[-1]  #结尾字段不同，则把结尾字段加进来
            return tmp_binary

        SEG_KEY = 5
        STRING = 7
        INT = 2
        FLOAT = 4
        fileType = filePath.split('/',1)[0]
        segDict = keywordsDict.get(fileType)
        stringTable = self.stringTable
        
        if '//' in filePath:
            filePath = filePath.replace('//','/')
        fileInDict_origin = self.read_FIle_In_Dict_with_Bin(filePath)

        binary = b'\xb0\xd0'
        binary += build(fileInDict,fileInDict_origin)
        binary += b'\x00' * ((4-(len(binary)%4)) % 4)
        return binary
    
    @staticmethod
    def itemID2itemPath(itemID,lst:LstEditor):
        path = lst.baseDir + '/' +lst.tableDict.get(itemID)
        return path

    def read_File_In_Bin(self,fpath:str='',pvfHeader=None):
        '''传入路径，返回未解密的字节流'''
        fpath = fpath.lower().replace('\\','/')
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
        try:
            res = pvfHeader.read_bytes(pvfHeader.filePackIndexShift+leaf['relativeOffset'],leaf['fileLength'])
        except:
            print(fpath,leaf)
            res = b''
        return res
    
    def read_File_In_Decrypted_Bin(self,fpath:str='',pvfHeader=None):
        '''传入路径，返回初步解密后的字节流'''
        fpath = fpath.lower().replace('\\','/')
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
            #res = decrypt_Bytes(pvfHeader.fullFile[pvfHeader.filePackIndexShift+leaf['relativeOffset']:pvfHeader.filePackIndexShift+leaf['relativeOffset']+leaf['fileLength']] ,leaf['fileCrc32'])
            #print(fpath,leaf['fileCrc32'],pvfHeader.read_bytes(pvfHeader.filePackIndexShift+leaf['relativeOffset'],leaf['fileLength']))
            res = decrypt_Bytes(pvfHeader.read_bytes(pvfHeader.filePackIndexShift+leaf['relativeOffset'],leaf['fileLength']),leaf['fileCrc32'])
        except:
            print(fpath,leaf)
            res = b''
        #self.fileContentDict[fpath] = res
        return res
    
    def newFile(self,fileType='stackable',fileName='fileName'):
        '''TODO '''
        def newLeaf():
            leaf = {
                'filePath' : lst.baseDir+'/'+fname.decode("CP949").lower(),  #全部转换为小写
                'content':b'',
            }
            return leaf
        def get_new_dict():
            if fileType=='stackable':
                newDict = {'[stackable type]':['waste',0]}
            elif fileType=='equipment':
                newDict = {'[equipment type]':[]}
            fill_Dict_SegKeys(newDict)
            return newDict
        lst:LstEditor = self.lstDict.get(fileType)
        if lst is None:
            return '未实现'
        itemID,fname = lst.add(fileName)
        leaf = newLeaf()
        self.editedLeafDict = leaf
        leaf['itemInDict'] = get_new_dict()
        fill_Dict_SegKeys()

    def gen_File_chunk(self,uuid=b'',fileVersion=None):
        def calcCRC(leaf:dict):
            return zlib.crc32(leaf['content'],leaf['fn'])#.to_bytes(4,'little')
        def leaf2bytes(leaf:dict):
            res = b''
            if leaf.get('fn') is None: #新文件，重新计算文件头
                print(f'新节点...{leaf["itemInDict"].get("[name]")}')
                fn = self.fnList[-1] + 1
                self.fnList.append(fn)
                '''while True:
                    fn:int = random.randint(1,pow(2,31))
                    if self.fnDict.get(fn) is None:
                        break'''
                leaf['fn'] = fn
                leaf['fn_bytes'] = fn.to_bytes(4,'little')
                #self.fnDict[fn] = leaf['fn_bytes']
                leaf['filePath_bytes'] = leaf['filePath'].encode('CP949','replace')
                leaf['filePathLength_bytes'] = len(leaf['filePath_bytes']).to_bytes(4,'little')
            res += leaf['fn_bytes']
            res += leaf['filePathLength_bytes']
            res += leaf['filePath_bytes']
            
            if leaf['content']!=b'':
                print(f'保存文件...{leaf["filePath_bytes"]}...{len(leaf["content"])} 字节')
                print(f'old CRC:{leaf.get("fileCrc32")}')
                fileLength = len(leaf['content'])
                res += fileLength.to_bytes(4,'little')
                leaf['fileCrc32']=calcCRC(leaf)
                print(f'new crc:{leaf.get("fileCrc32")}')
            else:
                res += leaf['fileLength_bytes']
            res += leaf['fileCrc32'].to_bytes(4,'little')    #_bytes
            relativeOffset = len(fileChunk)
            res += relativeOffset.to_bytes(4,'little')
            return res

        def buildHeader():
            nonlocal uuid, fileVersion
            if uuid==b'':
                uuid = pvfHeader.uuid#b'hey vergil, your portal-opening days are over.'
            uuidLen = len(uuid)
            header = b''
            header += uuidLen.to_bytes(4,'little')
            header += uuid
            if fileVersion is None:
                fileVersion = pvfHeader.PVFversion
            header += fileVersion.to_bytes(4,'little')
            treeLength = len(treeChunk_encrypt)
            header += treeLength.to_bytes(4,'little')
            header += PVFCRC.to_bytes(4,'little')
            fileNum = pvfHeader.numFilesInDirTree + newFIleNum
            header +=  fileNum.to_bytes(4,'little')
            return header

        fileChunk = bytearray()
        treeChunk = bytearray()
        pvfHeader:PVFHeader  = self.pvfHeader
        pvfHeader.index = 0
        lstObjDict = {}
        #lstLeafDict = {}
        for leafType,lstInfo in LSTPATHDICT.items():
            lstPath, suffix = lstInfo
            lstObjDict[leafType] = LstEditor(self.read_File_In_Decrypted_Bin(lstPath),self.stringTable,baseDir=leafType,suffix=suffix)
            #lstLeafDict[lstPath] = self.fileTreeDict[lstPath]
        for path,leaf in self.editedLeafDict.items():
            if leaf.get('itemInList') is not None and leaf['content']==b'':
                print(f'计算文件字节[list]...{leaf["filePath"]}')
                try:
                    leaf['content'] = self.list2DecryptedBin(leaf['itemInList'])
                except:
                    return False
            elif leaf.get('itemInDict') is not None and leaf['content']==b'':
                print(f'计算文件字节...{leaf["filePath"]}')
                leaf['content'] = self.dict2DecryptedBin2(leaf['itemInDict'],leaf['filePath'])
            
        
        for leafType,leafInDict in self.newLeafDict.items():
            if leafInDict=={}:continue
            lstObj:LstEditor = lstObjDict.get(leafType)
            if lstObj is not None:
                for tmpID,leaf in leafInDict.items():
                    itemID = leaf.get('itemID')
                    filePath = leaf.get('filePath')
                    if filePath is None:
                        filePath = ''
                    else:
                        filePath = filePath.split('/',1)[-1]
                    itemID,filePath = lstObj.add(itemID,filePath)
                    leaf['itemID'] = itemID
                    leaf['filePath'] = leafType + '/' + filePath
                    leaf['content'] = self.dict2DecryptedBin2(leaf['itemInDict'],leaf['filePath'])
                    print(f'新物品[{leaf["itemInDict"].get("[name]")}]生成随机ID-{itemID}')
                    self.editedLeafDict[leaf['filePath']] = leaf
                lstPath = LSTPATHDICT.get(leafType)[0]
                lstLeaf = self.fileTreeDict[lstPath].copy()
                lstLeaf['content'] = lstObj.to_bytes()
                self.editedLeafDict[lstPath] = lstLeaf

        #处理stringtable
        if len(self.editedLeafDict.keys())>0:
            self.editedLeafDict['stringtable.bin'] = self.fileTreeDict['stringtable.bin']
            self.editedLeafDict['stringtable.bin']['content'] = self.stringTable.to_bytes()

        for i in range(pvfHeader.numFilesInDirTree):    
            
            index = pvfHeader.index
            fn_bytes = pvfHeader.get_Header_Tree_Bytes(4)
            filePathLength_bytes = pvfHeader.get_Header_Tree_Bytes(4)
            filePathLength = unpack('I',filePathLength_bytes)[0]
            filePath_bytes = pvfHeader.get_Header_Tree_Bytes(filePathLength)
            fileLength_bytes = pvfHeader.get_Header_Tree_Bytes(4)
            fileCrc32_bytes = pvfHeader.get_Header_Tree_Bytes(4)
            relativeOffset_bytes = pvfHeader.get_Header_Tree_Bytes(4)
            leaf = {
                'index':index,
                'fn' : unpack('I',fn_bytes)[0],'fn_bytes':fn_bytes,
                'filePathLength' : unpack('I',filePathLength_bytes)[0],'filePathLength_bytes':filePathLength_bytes,
                'filePath' : filePath_bytes.decode("CP949").lower(),  #全部转换为小写
                'filePath_bytes':filePath_bytes,
                'fileLength' : (unpack('I',fileLength_bytes)[0]+ 3) & 0xFFFFFFFC,'fileLength_bytes':fileLength_bytes, #(unpack('I',fileLength_bytes)[0]+ 3) & 0xFFFFFFFC
                'fileLength_real':unpack('I',fileLength_bytes)[0],
                'fileCrc32' : unpack('I',fileCrc32_bytes)[0],'fileCrc32_bytes':fileCrc32_bytes,
                'relativeOffset' : unpack('I',relativeOffset_bytes)[0],
                'content':b'',  #保存解密后的字节
            }
            if leaf['filePath'][0] == '/':
                leaf['filePath'] = leaf['filePath'][1:]
            editedLeaf = self.editedLeafDict.get(leaf['filePath'])
            try:
                treeChunk_tmp = bytearray()
                fileChunk_tmp = bytearray()
                if editedLeaf is not None:#editedLeaf is not None:# and leaf['filePath']=='stringtable.bin'
                    treeChunk_tmp += leaf2bytes(editedLeaf)
                    fileChunk_tmp += encrypt_Bytes(editedLeaf['content'],editedLeaf['fileCrc32'])
                    #fileChunk_tmp += pvfHeader.read_bytes(pvfHeader.filePackIndexShift+leaf['relativeOffset'],leaf['fileLength'])
                    self.editedLeafDict.pop(leaf['filePath'])
                else:
                    treeChunk_tmp += leaf2bytes(leaf)
                    fileChunk_tmp += pvfHeader.read_bytes(pvfHeader.filePackIndexShift+leaf['relativeOffset'],leaf['fileLength'])
            except:
                treeChunk_tmp = b''
                fileChunk_tmp = b''
                print(f'文件导出失败,{leaf}')
            treeChunk += treeChunk_tmp
            fileChunk += fileChunk_tmp
            if i % 20000==0:
                print(f'\t{i},{leaf["filePath"].split("/")[0]}')
        newFIleNum = 0
        for filePath,leaf in self.editedLeafDict.items():   #新追加的文件
            try:
                treeChunk_tmp = bytearray()
                fileChunk_tmp = bytearray()
                treeChunk_tmp += leaf2bytes(leaf)
                fileChunk_tmp += encrypt_Bytes(leaf['content'],leaf['fileCrc32'])
            except:
                treeChunk_tmp = b''
                fileChunk_tmp = b''
                print(f'文件导出失败,{leaf}')
            treeChunk += treeChunk_tmp
            fileChunk += fileChunk_tmp
            newFIleNum += 1
        treeChunk += b'\x00' * ((4-(len(treeChunk)%4)) % 4)
        print(f'文件树长度：{len(treeChunk)}，文件块长度：{len(fileChunk)}')
        PVFCRC = zlib.crc32(treeChunk,pvfHeader.numFilesInDirTree+ newFIleNum)
        print('PVFCRC:',hex(PVFCRC))
        treeChunk_encrypt = encrypt_Bytes(treeChunk,PVFCRC)
        #print(len(treeChunk),len(fileChunk))
        fullFile = buildHeader() + treeChunk_encrypt + fileChunk# + b'Hey, Vergil! Your portal opening days are over.'
        return fullFile


def fill_Dict_SegKeys(fileInDict:dict):
    '''TODO: 增加装备种类'''
    def fill(originDict:dict,keysList=[]):
        for key in keysList:
            if key not in originDict.keys():
                originDict[key] = []
        return originDict
    if fileInDict.get('[stackable type]') is not None:
        stackableType,stackableValue = fileInDict.get('[stackable type]')
        keysList = SegKeyDict['stackable'][stackableType][str(stackableValue)]
        fill(fileInDict,keysList)
    return fileInDict



def test():

    PVF = r'E:\system sound infomation\客户端20221030\地下城与勇士\Script.pvf'
    PVF = r'E:\system sound infomation\客户端20221030\客户端20230212\KHD\Script.pvf'
    #PVF = r'./Script_new.pvf'
    pvfHeader=PVFHeader(PVF,True)
    print(pvfHeader)
    pvf = TinyPVFEditor(pvfHeader=pvfHeader)   
    pvf.load_Leafs(['stackable'])
    path = 'stackable/cash/creature/creature_food.stk'
    #path = 'stackable/monstercard/mcard_2015_mercenary_card_10008454.stk'
    leaf =  pvf.fileTreeDict.get(path)#.copy()
    fileInDict = pvf.read_File_In_Dict(path)
    leaf['itemInDict'] = fileInDict
    print(fileInDict)

    if True:
        print(leaf)
        leaf['fn'] -= 1
        leaf['fn_bytes'] = leaf['fn'].to_bytes(4,'little')
        #fill_Dict_SegKeys(fileInDict)
        #fileInDict['[name]'] = ['宠物高级饲料']
        print('修改文件为：')
        print(leaf)
        #bytes_new = pvf.dict2DecryptedBin2(fileInDict,path)#dict2DecryptedBin(fileInDict,path)#
        #print(bytes_new)
        #leaf['content'] = bytes_new
        pvf.editedLeafDict[path] = leaf

    if True:
        #pvf.editedLeafDict['stringtable.bin'] = pvf.fileTreeDict['stringtable.bin']
        #pvf.editedLeafDict['stringtable.bin']['content'] = pvf.stringTable.to_bytes()
        fullFile = pvf.gen_File_chunk()
        with open('Script_new.pvf','wb') as f:
            f.write(fullFile)
        print('文件已保存')
    return pvf

def resave():
    PVF = r'./Script_new_ut.pvf'
    pvfHeader=PVFHeader(PVF,True)
    print(pvfHeader)
    pvf = TinyPVFEditor(pvfHeader=pvfHeader)   
    pvf.load_Leafs(['stackable'])
    fullFile = pvf.gen_File_chunk()
    with open('Script_resave.pvf','wb') as f:
        f.write(fullFile)


def test2():
    PVF = r'E:\system sound infomation\客户端20221030\客户端20230212\KHD\Script.pvf'
    #PVF = r'./Script_new.pvf'
    #PVF = r'./Script_resave.pvf'
    pvfHeader=PVFHeader(PVF,True)
    print(hex(zlib.crc32(pvfHeader.unpackedHeaderTreeDecrypted,pvfHeader.numFilesInDirTree)))
    print(pvfHeader)
    pvf = TinyPVFEditor(pvfHeader=pvfHeader)   
    pvf.load_Leafs(['stackable'])
    #PVF2 = r'./Script_new_ut.pvf'
    #PVF2 = r'E:\system sound infomation\客户端20221030\客户端20230212\KHD\Script_resave2-ut.pvf'
    PVF2 = r'./Script_new.pvf'
    pvfHeader2=PVFHeader(PVF2,True)
    print(hex(zlib.crc32(pvfHeader.unpackedHeaderTreeDecrypted,pvfHeader.numFilesInDirTree)))
    print(pvfHeader2)
    pvf2 = TinyPVFEditor(pvfHeader=pvfHeader2)   
    pvf2.load_Leafs(['stackable'])

    print('pvf头字节对比：',pvfHeader.fullFile[:56]==pvfHeader2.fullFile[:56])
    print('pvf文件树字节对比：',pvfHeader.headerTreeBytes==pvfHeader2.headerTreeBytes)
    print('pvf文件树解密对比：',pvfHeader.unpackedHeaderTreeDecrypted==pvfHeader2.unpackedHeaderTreeDecrypted)
    print('pvf文件块对比：',pvfHeader.filePackBytes == pvfHeader2.filePackBytes,len(pvfHeader.filePackBytes),len( pvfHeader2.filePackBytes) )
    print('pvf全文件对比：',pvfHeader.fullFile==pvfHeader2.fullFile)
    l1 = len(pvfHeader.fullFile)
    l2 = len(pvfHeader2.fullFile)
    m = min(l1,l2)
    print('相同字节数对比：',pvfHeader.fullFile[:m]==pvfHeader2.fullFile[:m])
    print(pvfHeader.fullFile[m:],pvfHeader2.fullFile[m:])
    if False:
        for key,value in pvf.fileTreeDict.items():
            value2 = pvf2.fileTreeDict.get(key)
            if value!=value2:
                print(key)
                print(value)
                print(value2)

    path = 'stackable/cash/creature/creature_food.stk'
    l1 = pvf.read_File_In_List_with_Bin(path)
    l2 = pvf2.read_File_In_List_with_Bin(path)
    f1 = pvf.read_File_In_Decrypted_Bin(path)
    f2 = pvf2.read_File_In_Decrypted_Bin(path)

    print('文件字节对比：',f1==f2)
    leaf1 = pvf.fileTreeDict.get(path)
    leaf2 = pvf2.fileTreeDict.get(path)
    print('叶子节点对比：')
    print(leaf1)
    print(leaf2)
    print(len(pvf2.pvfHeader.headerTreeBytes))
    '''stkLst = pvf2.fileTreeDict.get('stackable/stackable.lst')
    print(stkLst)
    for i in range(len(pvf2.leafInList)):
        if pvf2.leafInList[i]==stkLst:
            for j in range(i-10,i+10):
                print(pvf2.leafInList[j]['filePath'])
            break'''
    
    '''if f1!=f2:
        for i in range(len(l2[0])):
            print(l1[0][i],l2[0][i],l1[1][i],l2[1][i],l1[2][i],l2[2][i],l1[2][i]==l2[2][i])
    else:
        print(pvf.read_FIle_In_Dict(path))'''

    st1 = pvf.stringTable
    st2 = pvf2.stringTable
    
    print('stringtable文件对比：',len(st1.bytes),len(st2.bytes),st1.bytes==st2.bytes)
    stkLst = pvf2.fileTreeDict.get('stackable/stackable')
    
    print(pvf.fileTreeDict.get('stringtable.bin'))
    print(pvf2.fileTreeDict.get('stringtable.bin'))
    

def test_List_edit():
    fpath = r'clientonly/skilltree/atfighter_sp.co'
    PVF = r'E:\system sound infomation\客户端20221030\地下城与勇士\Script.pvf'
    #PVF = r'E:\system sound infomation\客户端20221030\客户端20230212\KHD\Script.pvf'
    #PVF = r'./Script_new.pvf'
    pvfHeader=PVFHeader(PVF,True)
    print(pvfHeader)
    pvf = TinyPVFEditor(pvfHeader=pvfHeader)   
    pvf.load_Leafs(['stackable'])
    path = 'stackable/cash/creature/creature_food.stk'
    path = 'skill/mage/dragonspear.skl'
    #path = 'stackable/monstercard/mcard_2015_mercenary_card_10008454.stk'
    leaf =  pvf.fileTreeDict.get(path)#.copy()
    oldBin = pvf.read_File_In_Decrypted_Bin(path)
    fileInDict = pvf.read_File_In_Dict(path)
    fileInList = pvf.read_File_In_Structed_List(path)
    for line in fileInList:
        print(line)
    #print(fileInList)
    binary = pvf.list2DecryptedBin(fileInList)
    fileInList2 = pvf.convert_Bin_to_List(binary)
    print(fileInList2)
    print(binary)
    print(oldBin)


if __name__=='__main__':
    #pvf = test()
    #pvf = test2()
    test_List_edit()


    



