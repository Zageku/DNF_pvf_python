import struct
from struct import unpack
from zhconv import convert
import json
from pathlib import Path
import multiprocessing
import zlib
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
    except:
        pass

GEN_KEYWORD = False

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

class PVFHeader():
    def __init__(self,path,readFullFile=False):
        fp = open(path,'rb')
        self.pvfPath = path
        self.uuid_len = struct.unpack('i',fp.read(4))[0]
        self.uuid = fp.read(self.uuid_len)
        self.PVFversion = struct.unpack('i',fp.read(4))[0]
        self.dirTreeLength = struct.unpack('i',fp.read(4))[0] #长度
        self.dirTreeCrc32 = struct.unpack('I',fp.read(4))[0]
        self.numFilesInDirTree:int = struct.unpack('I',fp.read(4))[0]
        self.filePackIndexShift = fp.tell() + self.dirTreeLength
        self.headerLength = fp.tell()
        #读内部文件树头
        headerTreeBytes = fp.read(self.dirTreeLength)
        #int_num = header.dirTreeLength//4
        self.headerTreeBytes = headerTreeBytes
        self.unpackedHeaderTreeDecrypted = decrypt_Bytes(headerTreeBytes,self.dirTreeCrc32)
        self.index = 0  #用于读取HeaderTree的指针
        self.fp = fp
        #tmp_index = fp.tell()
        if readFullFile:
            self.filePackBytes = fp.read()
            fp.seek(0)
            self.fullFile = fp.read()
        else:
            self.fullFile = None
        #fp.close()
    def to_bytes(self,CRC:int,fileNum=0,treeLength=0,uuid=b'\x00'*36):
        if fileNum==0:
            fileNum = self.numFilesInDirTree
        if treeLength==0:
            treeLength = self.dirTreeLength
        #CRC = zlib.crc32(treechunk,fileNum).to_bytes(4,'little')
        res = bytearray()
        res += len(uuid).to_bytes(4,'little')
        res += uuid
        res += self.PVFversion.to_bytes(4,'little')
        res += treeLength.to_bytes(4,'little')
        res += CRC.to_bytes(4,'little')#dirTreeCrc32.to_bytes(4,'little')
        res += fileNum.to_bytes(4,'little')
        #print(res)
        print('pvfHeader:',len(res),res)
        return res
    def get_Header_Tree_Bytes(self,byte_num=4):
        res = self.unpackedHeaderTreeDecrypted[self.index:self.index+byte_num]
        self.index += byte_num
        return res
    def read_bytes(self,startIndex,length):
        if self.fullFile is not None:
            return self.fullFile[startIndex:startIndex+length]
        else:
            if self.fp is None:
                self.fp = open(self.pvfPath,'rb')
            self.fp.seek(startIndex)
            return self.fp.read(length)
    def __repr__(self):
        return f'PVF [{self.uuid.decode()}]\nVer:{self.PVFversion}\nTreeLength:{self.dirTreeLength} \nCRC:{hex(self.dirTreeCrc32)}\n{self.numFilesInDirTree} files'
    __str__ = __repr__

class StringTable():
    '''stringtable.bin文件对象'''
    def __init__(self,tableBytes:bytes,encode='big5') -> None:
        self.length = struct.unpack('I',tableBytes[:4])[0]  #字符串数量
        self.StringTableStrIndex = tableBytes[4:]#4+self.length*4*2
        self.stringTableChunk = tableBytes[4+self.length*4*2:]
        self.converted = False
        self.encode = encode
        self.convertChunk = []
        if encode=='big5':
            self.convertZhcn()
    def __getitem__(self,n):
        # 指第n和n+1个int，不是第n组int
        if self.converted:
            #print(self.convertChunk[n])
            return self.convertChunk[n]
        else:
            StrIndex = struct.unpack('<II',self.StringTableStrIndex[n*4:n*4+8])
            value = convert(self.StringTableStrIndex[StrIndex[0]:StrIndex[1]].decode(self.encode,'ignore'),'zh-cn')
            #print(value)
        return value
    def convertZhcn(self):
        self.convertChunk = []
        for n in range(self.length*2):
            StrIndex = struct.unpack('<II',self.StringTableStrIndex[n*4:n*4+8])
            value = self.StringTableStrIndex[StrIndex[0]:StrIndex[1]].decode(self.encode,'ignore')
            self.convertChunk.append(convert(value,'zh-cn'))
        self.converted = True

class Str():
    '''处理*.str文件'''
    def __init__(self,contentText):
        self.text = convert(contentText,'zh-cn')
        lines = filter(lambda l:'>' in l,self.text.split('\n'))
        self.strDict = {}
        for line in lines:
            key,value = line.split('>',1)
            self.strDict[key] = value
        #print(len(self.strDict.keys()))
    def __getitem__(self,key):
        res = self.strDict.get(key)
        if res is not None:
            #print(key,res)
            return res.replace('\r','')
        else:
            return 'None'
    
    def __repr__(self):
        return 'Str object. <'+str(self.strDict.items())[:100] + '...>'
    __str__ = __repr__

class Lst_lite2():
    '''处理*.lst文件对象'''
    def __init__(self,contentBytes,tinyPVF,stringtable,encode='big5',baseDir='',convertZhcn=True):
        self.vercode = contentBytes[:2]
        self.tableList = []
        self.tableDict = {} #存储lst的数据
        self.strDict = {}   #存储索引对应的str对象
        self.tinyPVF = tinyPVF
        self.fileContentDict = tinyPVF.fileContentDict
        self.stringtable:StringTable = stringtable
        self.baseDir = baseDir
        self.encode = encode
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
            self.tableList.append([index,string])
            self.tableDict[index] = string
            
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
    def __init__(self,pvfHeader:PVFHeader=None,encode='big5') -> None:
        self.pvfStructuredDict = {}   #按结构存储PVF文件树
        self.fileTreeDict = {}  #按 path: leaf存储文件树
        self.pvfHeader = pvfHeader
        self.fileContentDict = {}   #按路径或者物品id作为key存储文件内容
        self.stringTable:StringTable = None
        self.nString:Lst_lite2 = None
        self.encode = encode
    
    def load_Leafs(self,dirs=[],structured=False,pvfHeader:PVFHeader=None):
        '''按pvfHeader读取叶子，当structured为true时，同时会生成结构化的字典'''
        if pvfHeader is None:
            pvfHeader  = self.pvfHeader
        self.pvfHeader.index = 0
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
                'fileLength' : (unpack('I',fileLength_bytes)[0]+ 3) & 0xFFFFFFFC,'fileLength_bytes':fileLength_bytes,
                'fileCrc32' : unpack('I',fileCrc32_bytes)[0],'fileCrc32_bytes':fileCrc32_bytes,
                'relativeOffset' : unpack('I',relativeOffset_bytes)[0],
                'content':b'',
            }

            if leaf['filePath'][0] == '/':
                print(leaf['filePath'])
                leaf['filePath'] = leaf['filePath'][1:]
            '''if len(dirs)>0 or len(paths)>0:
                leafpaths = leaf['filePath'].split('/')
                if len(leafpaths)>1 and leafpaths[0] not in dirs and leaf['filePath'] not in paths:
                    continue'''
            #print(leaf)
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
            stringtableBytes = self.read_File_In_Decrypted_Bin('stringtable.bin')
            self.stringTable = StringTable(stringtableBytes,self.encode)
            self.nString = Lst_lite2(self.read_File_In_Decrypted_Bin('n_string.lst'),self,self.stringTable,self.encode)
        return self.fileTreeDict

    loadLeafFunc = load_Leafs
        
    def load_Lst_File(self,path='',encode=''):
        '''读取并创建lst对象'''
        content = self.read_File_In_Decrypted_Bin(path)
        if encode=='':
            encode = self.encode
        if '/' in path:
            baseDir,basename = path.rsplit('/',1)
        else:
            baseDir = ''
            basename = path
        return Lst_lite2(content,self,self.stringTable,encode,baseDir)    
    def read_File_In_Decrypted_Bin(self,fpath:str='',pvfHeader=None):
        '''传入路径，返回初步解密后的字节流'''
        fpath = fpath.lower().replace('\\','/')
        if fpath[0]=='/':
            fpath = fpath[1:]
        leaf =  self.fileTreeDict.get(fpath)
        
        if leaf is None:
            dir = fpath.split('/')[0]
            self.load_Leafs(dirs=[dir])
            leaf =  self.fileTreeDict.get(fpath)
        if pvfHeader is None:
            pvfHeader = self.pvfHeader
        if self.fileContentDict.get(fpath) is not None:
            return self.fileContentDict.get(fpath)
        try:
            res = decrypt_Bytes(pvfHeader.read_bytes(pvfHeader.filePackIndexShift+leaf['relativeOffset'],leaf['fileLength']),leaf['fileCrc32'])
        except:
            print(fpath,leaf)
            res = b''
        #self.fileContentDict[fpath] = res
        return res
    
    @staticmethod
    def content2List(content,stringtable:StringTable,nString:Lst_lite2,stringQuote='',convertZhcn=False):
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
        valuesRead = []
        typesInList = []
        for i in range(unit_num):
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
            else:
                typesInList.pop(-1)
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
        return [typesInList,valuesRead]
    
    def read_File_In_List_FROM_Bytes(self,fileInBytes):
        stringtable = self.stringTable
        nString  = self.nString
        return self.content2List(fileInBytes,stringtable,nString)

    def read_File_In_List2(self,fpath='',pvfheader:PVFHeader=None,stringtable:StringTable=None,nString:Lst_lite2=None,fileTreeDict:dict=None,stringQuote=''):
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
        return self.content2List(content,stringtable,nString,stringQuote)
    
    @staticmethod
    def list2Dict(fileInListWithType:list,parentKey=None):
        typeList,fileInList = fileInListWithType
        segmentKeysWithEndMark = []    #存放带结束符的段落
        for value in fileInList:
            if isinstance(value,str) and value[:2]=='[/' and value[-1]==']':
                segmentKeysWithEndMark.append(value.replace('/',''))
        #print(fileInListWithType)
        if subKeywordsDict.get('__segInSegKeys__') is None:
            subKeywordsDict['__segInSegKeys__'] = {}
        if subKeywordsDict.get('__quoteInSegKeys__') is None:
            subKeywordsDict['__quoteInSegKeys__'] = {}
        res = {}
        segment = []
        segTypes = []
        segmentKey = None
        endMarkFlg = False
        segmentInSegmentFlg = False
        for i,value in enumerate(fileInList):
            if typeList[i]==5:             
                # 判断是否为新的段
                if endMarkFlg and value.replace('/','')!=segmentKey:
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
                        if segmentInSegmentFlg and len(segment)>1:
                            res[segmentKey] = TinyPVF.list2Dict([segTypes,segment],segmentKey)
                        else:
                            res[segmentKey] = segment
                        # 用于生成keywords文件
                        if GEN_KEYWORD:
                            if subKeywordsDict.get(segmentKey)!= endMarkFlg:    #优先保存为True，表示有段落结束符
                                if subKeywordsDict.get(segmentKey)==False or subKeywordsDict.get(segmentKey) is None:
                                    subKeywordsDict[segmentKey] = endMarkFlg
                            if parentKey is not None:   #保存母子节点信息
                                
                                if subKeywordsDict['__segInSegKeys__'].get(parentKey) is None:
                                    subKeywordsDict['__segInSegKeys__'][parentKey] = {}
                                #print(parentKey,segmentKey)
                                subKeywordsDict['__segInSegKeys__'][parentKey][segmentKey] = 1
                            if isinstance(segment,list):
                                for i,value_ in enumerate(segment):
                                    if isinstance(value_,str) and len(value_)>0 and value_[0]=='[' and value_[-1]==']':
                                        tmp = []    #非段名的带方括号文本，把内容提取出来
                                        for j in range(i+1,len(segment)):
                                            value__ = segment[j]
                                            if isinstance(value__,str) and len(value__)>0 and value__[0]=='[' and value__[-1]==']':
                                                break 
                                            else:
                                                if isinstance(value__,str) and len(value__)>15: #超长的描述字符串或文件路径，忽略
                                                    continue
                                                tmp.append(value__)
                                        if subKeywordsDict['__quoteInSegKeys__'].get(segmentKey) is None:
                                            subKeywordsDict['__quoteInSegKeys__'][segmentKey] = {}
                                        oldValue = subKeywordsDict['__quoteInSegKeys__'][segmentKey].get(value_)
                                        if oldValue is None:
                                            subKeywordsDict['__quoteInSegKeys__'][segmentKey][value_] = []
                                        if len(tmp)==1 and tuple(tmp) not in subKeywordsDict['__quoteInSegKeys__'][segmentKey][value_]:
                                            subKeywordsDict['__quoteInSegKeys__'][segmentKey][value_].append(tuple(tmp))
                                        elif len(tmp)>0 and tuple(tmp) not in subKeywordsDict['__quoteInSegKeys__'][segmentKey][value_] and len(subKeywordsDict['__quoteInSegKeys__'][segmentKey][value_])<3:
                                            subKeywordsDict['__quoteInSegKeys__'][segmentKey][value_].append(tuple(tmp))
                    segmentInSegmentFlg = False
                    if '/' in value:
                        segmentKey = None
                        endMarkFlg = False
                    else:
                        segmentKey = value
                        if segmentKey in segmentKeysWithEndMark:
                            endMarkFlg = True #有结束符
                        else:
                            endMarkFlg = False
                        segment = []
                        segTypes = []
                        #print('--new segment',segmentKey)
                else:   # 不是新的段，添加数据
                    segment.append(value)
                    segTypes.append(typeList[i])
            else:
                segment.append(value)
                segTypes.append(typeList[i])
        if len(segment)>0 and segmentKey is not None:
            res[segmentKey] = segment
            # 用于生成keywords文件
            if subKeywordsDict.get(segmentKey) is None:
                subKeywordsDict[segmentKey] = False
            #if segmentKey not in keywords:
            #    keywords.append(segmentKey)
        #print(res,'\n')
        return res

    @staticmethod
    def content2Dict(content,stringtable:StringTable,nString:Lst_lite2,stringQuote=''):
        return TinyPVF.list2Dict(TinyPVF.content2List(content,stringtable,nString,stringQuote=''))
    
    @staticmethod
    def dictSegment2text(dictSegment:dict,prefix='',prefixAdd='    ')->str:
        '''递归对字段转换为带缩进的文本'''
        #print('segment',dictSegment,'prefix:',prefix)
        res = ''
        for key,segment in dictSegment.items():
            res += prefix + key + '\n'
            if isinstance(segment,dict):
                res += TinyPVF.dictSegment2text(segment,prefix+prefixAdd) #+ prefix + '/'+ key + '\n'
            else:
                tmpres = ''
                for value in segment:
                    tmpres += str(value) + ' '
                    tmpres = tmpres.replace('\n','\n'+prefix +prefixAdd).replace(r'%%',r'%')
                #if len(segment)>3:
                #    tmpres += '\n' + prefix + '/'+key
                res += prefix +prefixAdd + tmpres +'\n'
            #print('------\n',res)
        return res
    
    @staticmethod
    def content2Text(content,stringtable:StringTable,nString:Lst_lite2,stringQuote=''):

        fileInDict = TinyPVF.list2Dict(TinyPVF.content2List(content,stringtable,nString,stringQuote=''))
        res = TinyPVF.dictSegment2text(fileInDict)
        return res


    def read_FIle_In_Dict(self,fpath='',pvfheader:PVFHeader=None,stringtable:StringTable=None,nString:Lst_lite2=None,fileTreeDict:dict=None):
        fileInListWithType = self.read_File_In_List2(fpath,pvfheader,stringtable,nString,fileTreeDict)
        return self.list2Dict(fileInListWithType)
    
    def read_File_In_Text(self,fpath='',pvfheader:PVFHeader=None,stringtable:StringTable=None,nString:Lst_lite2=None,fileTreeDict:dict=None):
        return self.content2Text(self.read_File_In_Decrypted_Bin(fpath),self.stringTable,self.nString)

    
    def read_Segment_With_Key(self,fpath='',key='')->list:
        fileInListWithType = self.read_File_In_List2(fpath)
        typeList,fileInList = fileInListWithType
        isMultiSegmentKey = False    #结束符的段落
        for value in fileInList:
            if isinstance(value,str) and value[:2]=='[/' and value[-1]==']' and value.replace('/','')==key:
                isMultiSegmentKey = True
        segment = []
        start = False
        for i,value in enumerate(fileInList):
            if value == key:
                start = True
            elif typeList[i]!=7 and start and isinstance(value,str) and len(value)>0 and value[0]=='[' and value[-1]==']':    #段结束判断
                if isMultiSegmentKey:
                    if value.replace('/','') == key:
                        break
                    else:
                        segment.append(value)
                else:
                    break
            elif start:
                segment.append(value)
        return segment   

    def read_Segment_With_Key_Old(self,fpath='',key='')->list:
        '''将指定二进制文件按stk规则读取后返回dict'''
        fileInListWithType = self.read_File_In_List2(fpath)
        start = False
        res = []
        for value in fileInListWithType[1]:
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
    print('职业信息加载...')
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

def get_Stackable_dict3(pvf:TinyPVF):
    path = 'stackable/stackable.lst'
    stackableDetail_dict = {}
    stackable_dict = {}
    
    redundancyList = []
    failList = []
    ItemLst = pvf.load_Lst_File(path)
    print(f'物品信息加载...({len(ItemLst.tableList)})')
    for id_,path_ in ItemLst.tableList:
        if stackable_dict.get(id_) is not None:
            redundancyList.append(id_)
        try:
            fpath = ItemLst.baseDir+'/'+path_
            if '//' in fpath:
                fpath = fpath.replace('//','/')
            stackableDetail_dict[id_] = pvf.read_FIle_In_Dict(fpath)

            res = stackableDetail_dict[id_].get('[name]')
            try:
                stackable_dict[id_] = ''.join(res)
            except:
                stackable_dict[id_] = ''.join([str(item) for item in res])
            #pvf.fileContentDict[id_] = pvf.fileContentDict[fpath.lower()]
        except:
            failList.append([id_,path_])
            continue
    if redundancyList!=[]:
        print(f'物品列表重复：{len(redundancyList)},{redundancyList}')
    if failList!=[]:
        print(f'物品加载失败：{len(failList)},{failList}')
    return stackable_dict, stackableDetail_dict

def get_Equipment_Dict3(pvf:TinyPVF):
    
    equipmentStructuredDict = {'character':{}}#拥有目录结构的dict
    equipmentDict = {}  #只有id对应的dict
    equipmentDetailDict = {}
    path = 'equipment/equipment.lst'
    redundancyList = []
    failList= []
    ItemLst = pvf.load_Lst_File(path)
    print(f'装备信息加载...({len(ItemLst.tableList)})')
    for id_,path_ in ItemLst.tableList:
        #print(id_,path_)
        if equipmentDict.get(id_)!=None:
            redundancyList.append(id_)
        try:
            dirs = path_.split('/')[:-1]
            detailedDict = equipmentStructuredDict
            for dirName in dirs:
                if dirName not in detailedDict.keys():
                    detailedDict[dirName] = {}
                detailedDict = detailedDict[dirName]

            fpath = ItemLst.baseDir+'/'+path_
            if '//' in fpath:
                fpath = fpath.replace('//','/')
            equipmentDetailDict[id_] = pvf.read_FIle_In_Dict(fpath)
            res = equipmentDetailDict[id_].get('[name]')
            try:
                equipmentDict[id_] = ''.join(res)
            except:
                equipmentDict[id_] = ''.join([str(item) for item in res])
            detailedDict[id_] = equipmentDict[id_]
        #pvf.fileContentDict[id_] = pvf.fileContentDict[fpath.lower()]
        except:
            failList.append([id_,ItemLst.baseDir+'/'+path_])
            continue
    if redundancyList!=[]:
        print(f'装备列表重复：{len(redundancyList)},{redundancyList}')
    if failList!=[]:
        print(f'装备加载失败：{len(failList)},{failList}')
    return equipmentStructuredDict, equipmentDict, equipmentDetailDict

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

def get_dungeon_Dict(pvf:TinyPVF):
    dungeonListPath = 'dungeon/dungeon.lst'
    
    dungeonLst = pvf.load_Lst_File(dungeonListPath)
    print(f'加载副本列表...({len(dungeonLst.tableList)})')
    dungeonDict = {}
    redundancyList = []
    failList = []
    for id_,path_ in dungeonLst.tableList:
        if dungeonDict.get(id_) is not None:
            redundancyList.append(id_)
            
        try:
            fpath = dungeonLst.baseDir+'/'+path_
            if '//' in fpath:
                fpath = fpath.replace('//','/')
            dungeonDict[id_] = pvf.read_FIle_In_Dict(fpath)
        except:
            failList.append([id_,path_])
            continue
    if redundancyList!=[]:
        print(f'副本列表重复：{len(redundancyList)},{redundancyList}')
    if failList!=[]:
        print(f'副本加载失败：{len(failList)},{failList}')
    return dungeonDict

def get_quest_dict(pvf:TinyPVF):
    questListPath = 'n_quest/quest.lst'
    questLst = pvf.load_Lst_File(questListPath)
    print(f'加载任务列表...({len(questLst.tableList)})')
    questDict = {}
    redundancyList = []
    failList = []
    for id_,path_ in questLst.tableList:
        if questDict.get(id_) is not None:
            redundancyList.append(id_)
            
        try:
            fpath = questLst.baseDir+'/'+path_
            if '//' in fpath:
                fpath = fpath.replace('//','/')
            questDict[id_] = pvf.read_FIle_In_Dict(fpath)
        except:
            failList.append([id_,path_])
            continue
    if redundancyList!=[]:
        print(f'任务列表重复：{len(redundancyList)},{redundancyList}')
    if failList!=[]:
        print(f'任务加载失败：{len(failList)},{failList}')
    return questDict

def get_Item_Dict(pvf:TinyPVF,genKeywords=False,*args):
    '''传入pvf文件树，返回物品id:name的字典'''
    #try:
    pvf.load_Leafs(['stackable','character','etc','equipment','dungeon','n_quest'])
    #except Exception as e:
    #    print(f'PVF目录树加载失败，{e}')
    #    return False
    global GEN_KEYWORD, subKeywordsDict, keywordsDict
    if genKeywords:
        keywordsDict = {
            'stackable':{},
            'equipment':{},
            'dungeon':{},
            'quest':{}
        }
        
        GEN_KEYWORD = True
    all_item_dict = {}
    magicSealDict = get_Magic_Seal_Dict2(pvf)
    all_item_dict['magicSealDict'] = magicSealDict

    jobDict = get_Job_Dict2(pvf)
    all_item_dict['jobDict'] = jobDict
    #print(jobDict)
    expTable = get_exp_table2(pvf)
    all_item_dict['expTable'] = expTable

    subKeywordsDict = keywordsDict['equipment']
    equipmentStructuredDict, equipmentDict, equipmentDetailDict = get_Equipment_Dict3(pvf)
    all_item_dict['equipment'] = equipmentDict
    all_item_dict['equipmentStructuredDict'] = equipmentStructuredDict
    all_item_dict['equipment_detail'] = equipmentDetailDict

    #stackable_dict = get_Stackable_dict2(pvf)
    if genKeywords:
        import json
        json.dump(keywordsDict,open('./config/pvfKeywordsDict.json','w'))
    subKeywordsDict = keywordsDict['stackable']
    stackable_dict, stackable_detail_dict = get_Stackable_dict3(pvf)
    all_item_dict['stackable'] = stackable_dict
    all_item_dict['stackable_detail'] = stackable_detail_dict
    if genKeywords:
        import json
        json.dump(keywordsDict,open('./config/pvfKeywordsDict.json','w'))
    subKeywordsDict = keywordsDict['dungeon']
    all_item_dict['dungeon'] = get_dungeon_Dict(pvf)


    #all_item_dict['idPathContentDict'] = pvf.fileContentDict
    all_item_dict['avatarHidden'] = get_Hidden_Avatar_List2(pvf)

    subKeywordsDict = keywordsDict['quest']
    all_item_dict['quest'] = get_quest_dict(pvf)
    if genKeywords:
        import json
        json.dump(keywordsDict,open('./config/pvfKeywordsDict.json','w'))
    return all_item_dict


def get_Equipment_Dict_multi(args): #分为x个part
    part,pvf = args
    taskPart,allPartNum = part
    pvf:TinyPVF
    equipmentStructuredDict = {'character':{}}#拥有目录结构的dict
    equipmentDict = {}  #只有id对应的dict
    equipmentDetailDict = {}
    path = 'equipment/equipment.lst'
    print(f'装备信息加载...{taskPart}/{allPartNum}')
    ItemLst = pvf.load_Lst_File(path)
    length = len(ItemLst.tableList)
    fileListInTask = ItemLst.tableList[taskPart*length//allPartNum:(taskPart+1)*length//allPartNum]
    for id_,path_ in fileListInTask:
        try:
            dirs = path_.split('/')[:-1]
            detailedDict = equipmentStructuredDict
            for dirName in dirs:
                if dirName not in detailedDict.keys():
                    detailedDict[dirName] = {}
                detailedDict = detailedDict[dirName]

            fpath = ItemLst.baseDir+'/'+path_
            if '//' in fpath:
                fpath = fpath.replace('//','/')
            equipmentDetailDict[id_] = pvf.read_FIle_In_Dict(fpath)
            res = equipmentDetailDict[id_].get('[name]')
            try:
                equipmentDict[id_] = ''.join(res)
            except:
                equipmentDict[id_] = ''.join([str(item) for item in res])
            detailedDict[id_] = equipmentDict[id_]
            #pvf.fileContentDict[id_] = pvf.fileContentDict[fpath.lower()]
        except:
            continue
    return equipmentStructuredDict, equipmentDict, equipmentDetailDict

def portal(args):
    funcName,pvf = args
    tmp_item_dict = {}
    if funcName=='magic':
        #pvf.load_Leafs(['etc'])
        tmp_item_dict['magicSealDict'] = get_Magic_Seal_Dict2(pvf)
    elif funcName=='job':
        #pvf.load_Leafs(['character'])
        tmp_item_dict['jobDict'] = get_Job_Dict2(pvf)
    elif funcName=='equip':
        import multiprocessing
        cores = multiprocessing.cpu_count()
        taskPartNum = 4
        pool = multiprocessing.Pool(processes=min(cores,taskPartNum))
        #pvf.load_Leafs(['equipment'])
        args_equ = [[[i,taskPartNum],pvf] for i in range(taskPartNum)]
        tmp_item_dict['equipment'] = {}
        tmp_item_dict['equipmentStructuredDict'] = {}
        tmp_item_dict['equipment_detail'] = {}
        for res in pool.imap_unordered(get_Equipment_Dict_multi,args_equ):
            equipmentStructuredDict, equipmentDict, equipmentDetailDict = res
            tmp_item_dict['equipment'].update(equipmentDict)
            tmp_item_dict['equipmentStructuredDict'].update(equipmentStructuredDict)
            tmp_item_dict['equipment_detail'].update(equipmentDetailDict)
    elif funcName=='stackable':
        #pvf.load_Leafs(['stackable'])
        stackable_dict, stackable_detail_dict = get_Stackable_dict3(pvf)
        tmp_item_dict['stackable'] = stackable_dict
        tmp_item_dict['stackable_detail'] = stackable_detail_dict
    elif funcName=='avatar':
        #pvf.load_Leafs(['etc'])
        tmp_item_dict['avatarHidden'] = get_Hidden_Avatar_List2(pvf)
    elif funcName=='exp':
        #pvf.load_Leafs(['character'])
        expTable = get_exp_table2(pvf)
        tmp_item_dict['expTable'] = expTable
    elif funcName=='dungeon':
        dungeonDict = get_dungeon_Dict(pvf)
        tmp_item_dict['dungeon'] = dungeonDict
    return tmp_item_dict

def get_Item_Dict_Multi(pvf:TinyPVF,pool=None):
    '''传入pvf文件树，返回物品id:name的字典'''
    try:
        pvf.loadLeafFunc(['stackable','character','etc','equipment','dungeon','n_quest'])
    except Exception as e:
        print(f'PVF目录树加载失败，{e}')
        return False 
    
    args_1 = ['magic','job','equip','stackable','avatar','exp','dungeon']
    if pool is None:
        cores = multiprocessing.cpu_count()
        taskNum = len(args_1)
        processNum = min(cores,taskNum)
        pool = multiprocessing.Pool(processes=processNum)
        print(f'多核心加载PVF中...({processNum})')
    try:
        pvf.pvfHeader.fp.close()
    except:
        pass
    finally:
        pvf.pvfHeader.fp = None
    args = [[arg1,pvf] for arg1 in args_1]
    
    all_items_dict = {}
    for res in pool.imap_unordered(portal,args):
        all_items_dict.update(res)
    pool.close()
    return all_items_dict

LOAD_FUNC = get_Item_Dict

def test_multi():

    PVF = r'E:\system sound infomation\客户端20221030\客户端20230212\KHD\Script.pvf'
    pvfHeader=PVFHeader(PVF)
    pvf = TinyPVF(pvfHeader=pvfHeader)   
    #pvf.load_Leafs_multi(['stackable','character','etc','equipment'],paths=['etc/avatar_roulette/avatarfixedhiddenoptionlist.etc'])
    items = get_Item_Dict_Multi(pvf)
    for key,value in items.items():
        if isinstance(value,str):
            continue
        print(key,len(value),str(value)[:50])

def test_gen_wordDict(encode='big5'):
    PVF = r'E:\system sound infomation\客户端20221030\客户端20230212\KHD\Script_ori.pvf'
    PVF = './Script_new.pvf'
    PVF = r'E:\system sound infomation\客户端20221030\地下城与勇士\Script.pvf'
    PVF = './Script_gbk.pvf'
    pvfHeader=PVFHeader(PVF)
    print(pvfHeader)
    pvf = TinyPVF(pvfHeader,encode)   
    items = get_Item_Dict(pvf,genKeywords=False)
    print('加载完成...')
    for key,value in items.items():
        if isinstance(value,str):
            continue
        print(key,len(value),str(value)[:100])


def test():
    PVF = r'E:\system sound infomation\客户端20221030\地下城与勇士\Script.pvf'
    #PVF = r'E:\system sound infomation\客户端20221030\客户端20230212\KHD\Script.pvf'
    PVF = './Script_new.pvf'
    pvfHeader=PVFHeader(PVF)
    print(pvfHeader)
    pvf = TinyPVF(pvfHeader=pvfHeader)   
    pvf.load_Leafs(['stackable'])
    path = 'stackable/cash/creature/creature_food.stk'
    #path = 'stackable/monstercard/mcard_2015_mercenary_card_10008454.stk'
    res = pvf.read_File_In_List2(path)
    for i in range(len(res[1])):
        print(res[0][i],res[1][i])
    ''' res = pvf.read_FIle_In_Dict(path)
    for key,value in res.items():
        print(key,value,pvf.read_Segment_With_Key(path,key))'''
    
    print(pvf.read_File_In_Text(path))

def test2():
    PVF = r'E:\system sound infomation\客户端20221030\地下城与勇士\Script.pvf'
    PVF = r'E:\system sound infomation\客户端20221030\客户端20230212\KHD\Script.pvf'
    pvfHeader=PVFHeader(PVF)
    pvf = TinyPVF(pvfHeader=pvfHeader)   
    pvf.load_Leafs([])
    path = 'stackable/monsterCard/mcard_twin_l6.stk'
    #path = 'stackable/monstercard/mcard_2015_mercenary_card_10008454.stk'
    import time
    #dungeon = get_dungeon_Dict(pvf)
    res = pvf.read_File_In_List2(path)
    for i in range(len(res[1])):
        print(res[0][i],res[1][i])
    global GEN_KEYWORD, subKeywordsDict
    GEN_KEYWORD = True
    subKeywordsDict = {}
    t1 = time.time()
    res = pvf.read_FIle_In_Dict(path)
    for key,value in res.items():
        print(key,value,pvf.read_Segment_With_Key(path,key))
    t = time.time() - t1
    print(pvf.read_File_In_Text(path))
    print(subKeywordsDict)
    print('time:',t)
    print(len(pvf.pvfHeader.headerTreeBytes))
    print(pvf.fileTreeDict.get('stackable/stackable.lst'))
    return pvf

def get_stk_segkeys():
    PVF = r'E:\system sound infomation\客户端20221030\客户端20230212\KHD\Script_ori.pvf'
    pvfHeader=PVFHeader(PVF)
    print(pvfHeader)
    pvf = TinyPVF(pvfHeader=pvfHeader)   
    pvf.load_Leafs(['stackable'])
    idNameDict,detailDict = get_Stackable_dict3(pvf)
    stkTypeDict = {}
    print('加载物品分类和字段...')
    for itemID,itemDict in detailDict.items():
        stkType = itemDict.get('[stackable type]')
        stkName = itemDict.get('[name]')[0]
        typeStr,typeValue = stkType
        if stkTypeDict.get(typeStr) is None:
            stkTypeDict[typeStr] = {}
        if stkTypeDict[typeStr].get(typeValue) is None:
            stkTypeDict[typeStr][typeValue] = []
        for key in itemDict.keys():
            if key not in stkTypeDict[typeStr][typeValue]:
                stkTypeDict[typeStr][typeValue].append(key)
    with open('./config/stkTypeDict.json','w',errors='replace') as f:
        json.dump(stkTypeDict,f,ensure_ascii=False)

def get_equ_segkeys():
    PVF = r'E:\system sound infomation\客户端20221030\客户端20230212\KHD\Script_ori.pvf'
    pvfHeader=PVFHeader(PVF)
    print(pvfHeader)
    pvf = TinyPVF(pvfHeader=pvfHeader)   
    pvf.load_Leafs(['equipment'])
    equipmentStructuredDict, equipmentDict, detailDict = get_Equipment_Dict3(pvf)
    equTypeDict = {}
    print('加载装备分类和字段...')
    for itemID,itemDict in detailDict.items():
        equType = itemDict.get('[equipment type]')
        stkName = itemDict.get('[name]')[0]
        typeStr,typeValue = equType
        if equTypeDict.get(typeStr) is None:
            equTypeDict[typeStr] = {}
        if equTypeDict[typeStr].get(typeValue) is None:
            equTypeDict[typeStr][typeValue] = []
        for key in itemDict.keys():
            if key not in equTypeDict[typeStr][typeValue]:
                equTypeDict[typeStr][typeValue].append(key)
    with open('./config/equTypeDict.json','w',errors='replace') as f:
        json.dump(equTypeDict,f,ensure_ascii=False)

if __name__=='__main__':
    test_gen_wordDict('gbk')
    #get_equ_segkeys()
    
    #pvf = test2()


    



