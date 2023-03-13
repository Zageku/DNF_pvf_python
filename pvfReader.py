import struct
from struct import unpack
from zhconv import convert
import json
from pathlib import Path
import multiprocessing
    
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
        keywords = []
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
        #tmp_index = fp.tell()
        #fp.seek(0)
        self.fullFile = None#fp.read()
        #fp.close()
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
    def __init__(self,tableBytes:bytes) -> None:
        self.length = struct.unpack('I',tableBytes[:4])[0]  #字符串数量
        self.StringTableStrIndex = tableBytes[4:]#4+self.length*4*2
        self.stringTableChunk = tableBytes[4+self.length*4*2:]
        self.converted = False
        self.convertChunk = []
        self.convertZhcn()
    def __getitem__(self,n):
        # 指第n和n+1个int，不是第n组int
        if self.converted:
            #print(self.convertChunk[n])
            return self.convertChunk[n]
        else:
            StrIndex = struct.unpack('<II',self.StringTableStrIndex[n*4:n*4+8])
            value = convert(self.StringTableStrIndex[StrIndex[0]:StrIndex[1]].decode('big5','ignore'),'zh-cn')
            #print(value)
        return value
    def convertZhcn(self):
        self.convertChunk = []
        for n in range(self.length*2):
            StrIndex = struct.unpack('<II',self.StringTableStrIndex[n*4:n*4+8])
            value = self.StringTableStrIndex[StrIndex[0]:StrIndex[1]].decode('big5','ignore')
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
    def __getitem__(self,key):
        return self.strDict.get(key)
    
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

    def _load_Leafs_multi(self,args):
        part,dirs,paths,structured,pvfHeader = args
        taskPart,allPartNum = part
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
        return self.fileTreeDict
    
    def load_Leafs_multi(self,dirs=[],paths=[],structured=False,pvfHeader:PVFHeader=None):
        print('多核心加载PVF中...')
        cores = multiprocessing.cpu_count()
        taskNum = len(dirs)
        pool = multiprocessing.Pool(processes=min(cores,taskNum))
        args = [[[i,taskNum],[dirs[i]],paths,structured,pvfHeader] for i in range(taskNum)]
        if pvfHeader is None:
            pvfHeader  = self.pvfHeader
        self.pvfHeader.index = 0
        try:
            pvfHeader.fp.close()
        except:
            pass
        finally:
            pvfHeader.fp = None
        for res in pool.imap_unordered(self._load_Leafs_multi,args):
            self.fileTreeDict = rec_merge(self.fileTreeDict,res)
        if self.stringTable is None:
            self.stringTable = StringTable(self.read_File_In_Decrypted_Bin('stringtable.bin'))
            self.nString = Lst_lite2(self.read_File_In_Decrypted_Bin('n_string.lst'),self,self.stringTable)
        return self.fileTreeDict
        
    loadLeafFunc = load_Leafs
        

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
            #res = decrypt_Bytes(pvfHeader.fullFile[pvfHeader.filePackIndexShift+leaf['relativeOffset']:pvfHeader.filePackIndexShift+leaf['relativeOffset']+leaf['fileLength']] ,leaf['fileCrc32'])
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
                valuesRead.append(stringQuote+stringtable[values[i]]+stringQuote)
            elif types[i] in [8]:
                valuesRead.append(stringtable[values[i]])
            elif types[i] in [9]:
                valuesRead.append(nString.get_N_Str(values[i])[stringtable[values[i+1]]])
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
        return [types,valuesRead]
    
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
    def list2Dict(fileInListWithType:list,formatDepth=-1):
        typeList,fileInList = fileInListWithType
        segmentKeys = []    #存放带结束符的段落
        for value in fileInList:
            if isinstance(value,str) and value[:2]=='[/' and value[-1]==']':
                segmentKeys.append(value.replace('/',''))
        #print(fileInListWithType)
        res = {}
        segment = [0,0,0]
        segTypes = []
        segmentKey = None
        multiFlg = False
        segmentInSegmentFlg = False
        for i,value in enumerate(fileInList):
            if isinstance(value,str) and len(value)>0 and value[-1] == ']' and value.replace('/','') in keywords:# or (typeList[i]!=7 and isinstance(value,str) and len(value)>1 and value[0]=='[' and value[-1]==']'):
                # 判断是否为新的段
                if multiFlg and value.replace('/','')!=segmentKey:
                    segmengFin = False
                    segmentInSegmentFlg = True   #是段中段的标识
                    #    segmentInSegmentFlg = True
                        #print('segInSeg',value)
                else:
                    if len(segment)>0:
                        segmengFin = True
                    else:
                        segmengFin = False
            
                if segmengFin: # 是新的段，保存数据，判断新段类型
                    #print('new seg,', value)
                    if segmentKey is not None:
                        if segmentInSegmentFlg and formatDepth!=0 and len(segment)>1:
                            res[segmentKey] = TinyPVF.list2Dict([segTypes,segment])
                        else:
                            res[segmentKey] = segment
                        #if segmentKey not in keywords:
                        #    keywords.append(segmentKey)
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
                        segment = []
                        segTypes = []
                else:   # 不是新的段，添加数据
                    segment.append(value)
                    #segTypes.append(typeList[i])
            else:
                segment.append(value)
                #segTypes.append(typeList[i])
        if len(segment)>0 and segmentKey is not None:
            res[segmentKey] = segment
            #if segmentKey not in keywords:
            #    keywords.append(segmentKey)
        #print(res,'\n')
        return res

    @staticmethod
    def content2Dict(content,stringtable:StringTable,nString:Lst_lite2,stringQuote=''):
        return TinyPVF.list2Dict(TinyPVF.content2List(content,stringtable,nString,stringQuote=''))
    
    @staticmethod
    def dictSegment2text(dictSegment:dict,prefix='',prefixAdd='    ')->str:
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
    path,encode = ['stackable/stackable.lst','big5']
    stackableDetail_dict = {}
    stackable_dict = {}
    print('物品信息加载...')
    
    ItemLst = pvf.load_Lst_File(path,encode=encode)
    for id_,path_ in ItemLst.tableList:
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
            continue
    return stackable_dict, stackableDetail_dict

def get_Equipment_Dict3(pvf:TinyPVF):
    
    equipmentStructuredDict = {'character':{}}#拥有目录结构的dict
    equipmentDict = {}  #只有id对应的dict
    equipmentDetailDict = {}
    path = 'equipment/equipment.lst'
    
    print('装备信息加载...')
    #
    ItemLst = pvf.load_Lst_File(path,encode='big5')
    for id_,path_ in ItemLst.tableList:
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

def get_Item_Dict(pvf:TinyPVF,*args):
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

    equipmentStructuredDict, equipmentDict, equipmentDetailDict = get_Equipment_Dict3(pvf)
    all_item_dict['equipment'] = equipmentDict
    all_item_dict['equipmentStructuredDict'] = equipmentStructuredDict
    all_item_dict['equipment_detail'] = equipmentDetailDict

    #stackable_dict = get_Stackable_dict2(pvf)
    
    stackable_dict, stackable_detail_dict = get_Stackable_dict3(pvf)
    all_item_dict['stackable'] = stackable_dict
    all_item_dict['stackable_detail'] = stackable_detail_dict


    #all_item_dict['idPathContentDict'] = pvf.fileContentDict
    all_item_dict['avatarHidden'] = get_Hidden_Avatar_List2(pvf)
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
    ItemLst = pvf.load_Lst_File(path,encode='big5')
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
    return tmp_item_dict

def get_Item_Dict_Multi(pvf:TinyPVF,pool=None):
    '''传入pvf文件树，返回物品id:name的字典'''
    try:
        pvf.loadLeafFunc(['stackable','character','etc','equipment'])
    except Exception as e:
        print(f'PVF目录树加载失败，{e}')
        return False 
    
    args_1 = ['magic','job','equip','stackable','avatar','exp']
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

def portal2(args):
    funcName,pvf = args
    tmp_item_dict = {}
    if funcName=='magic':
        pvf.load_Leafs(['etc'])
        tmp_item_dict['magicSealDict'] = get_Magic_Seal_Dict2(pvf)
    elif funcName=='job':
        pvf.load_Leafs(['character'])
        tmp_item_dict['jobDict'] = get_Job_Dict2(pvf)
    elif funcName=='equip':
        import multiprocessing
        cores = multiprocessing.cpu_count()
        taskPartNum = 4
        pool = multiprocessing.Pool(processes=min(cores,taskPartNum))
        print(f'新建装备加载进程池({taskPartNum})')
        pvf.load_Leafs(['equipment'])
        try:
            pvf.pvfHeader.fp.close()
        except:
            pass
        finally:
            pvf.pvfHeader.fp = None
        args_equ = [[[i,taskPartNum],pvf] for i in range(taskPartNum)]
        tmp_item_dict['equipment'] = {}
        tmp_item_dict['equipmentStructuredDict'] = {}
        tmp_item_dict['equipment_detail'] = {}
        for res in pool.imap_unordered(get_Equipment_Dict_multi,args_equ):
            equipmentStructuredDict, equipmentDict, equipmentDetailDict = res
            tmp_item_dict['equipment'].update(equipmentDict)
            tmp_item_dict['equipmentStructuredDict'].update(equipmentStructuredDict)
            tmp_item_dict['equipment_detail'].update(equipmentDetailDict)
        pool.close()
    elif funcName=='stackable':
        pvf.load_Leafs(['stackable'])
        stackable_dict, stackable_detail_dict = get_Stackable_dict3(pvf)
        tmp_item_dict['stackable'] = stackable_dict
        tmp_item_dict['stackable_detail'] = stackable_detail_dict
    elif funcName=='avatar':
        pvf.load_Leafs(['etc'])
        tmp_item_dict['avatarHidden'] = get_Hidden_Avatar_List2(pvf)
    elif funcName=='exp':
        pvf.load_Leafs(['character'])
        expTable = get_exp_table2(pvf)
        tmp_item_dict['expTable'] = expTable
    return tmp_item_dict

def get_Item_Dict_Multi2(pvf:TinyPVF,pool=None):
    '''传入pvf文件树，返回物品id:name的字典'''
    
    args_1 = ['magic','job','equip','stackable','avatar','exp']
    print('进程池：',pool)
    if pool is None:
        cores = multiprocessing.cpu_count()
        taskNum = len(args_1)
        processNum = min(cores,taskNum)
        pool = multiprocessing.Pool(processes=processNum)
        print('新建进程池')
    try:
        pvf.pvfHeader.fp.close()
    except:
        pass
    finally:
        pvf.pvfHeader.fp = None
    args = [[arg1,pvf] for arg1 in args_1]
    
    all_items_dict = {}
    for res in pool.imap_unordered(portal2,args):
        all_items_dict.update(res)
    pool.close()
    return all_items_dict

LOAD_FUNC = get_Item_Dict

def test_multi():

    PVF = r'E:\system sound infomation\客户端20221030\客户端20230212\KHD\Script.pvf'
    pvfHeader=PVFHeader(PVF)
    pvf = TinyPVF(pvfHeader=pvfHeader)   
    #pvf.load_Leafs_multi(['stackable','character','etc','equipment'],paths=['etc/avatar_roulette/avatarfixedhiddenoptionlist.etc'])
    items = get_Item_Dict_Multi2(pvf)
    for key,value in items.items():
        if isinstance(value,str):
            continue
        print(key,len(value),str(value)[:50])

    






def test5():
    PVF = r'E:\system sound infomation\客户端20221030\客户端20230212\KHD\Script.pvf'
    pvfHeader=PVFHeader(PVF)
    pvf = TinyPVF(pvfHeader=pvfHeader)   
    items = get_Item_Dict(pvf)
    print('加载完成...')
    for key,value in items.items():
        if isinstance(value,str):
            continue
        print(key,len(value),str(value)[:50])
    #import json
    #json.dump(keywords,open('./config/pvfKeywords.json','w'))

def test():
    PVF = r'E:\system sound infomation\客户端20221030\地下城与勇士\Script.pvf'
    #PVF = r'E:\system sound infomation\客户端20221030\客户端20230212\KHD\Script.pvf'
    pvfHeader=PVFHeader(PVF)
    pvf = TinyPVF(pvfHeader=pvfHeader)   
    pvf.load_Leafs(['stackable'],paths=['etc/avatar_roulette/avatarfixedhiddenoptionlist.etc'])
    path = 'stackable/cash/creature/creature_food.stk'
    #path = 'stackable/monstercard/mcard_2015_mercenary_card_10008454.stk'
    res = pvf.read_File_In_List2(path)
    for i in range(len(res[1])):
        print(res[0][i],res[1][i])
    ''' res = pvf.read_FIle_In_Dict(path)
    for key,value in res.items():
        print(key,value,pvf.read_Segment_With_Key(path,key))'''
    
    print(pvf.read_File_In_Text(path))


if __name__=='__main__':
    test()


    



