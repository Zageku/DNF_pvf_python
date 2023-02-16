import struct
from struct import unpack
#import os
from pathlib import Path

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





def decryptBytes(inputBytes,crc):
    '''对原始字节流进行初步预处理'''
    key = 0x81A79011
    xor = crc ^ key
    decrypted = bytearray()
    int_num = len(inputBytes)//4
    for i in range(int_num):
        value_Xored = struct.unpack('I',inputBytes[i*4:i*4+4])[0]^xor
        value_with_extra = value_Xored>>6 | value_Xored<<26
        value = 0xffffffff & value_with_extra
        decrypted.extend(struct.pack('I',value))
    return decrypted

def getFilePack(path,pvfTree,fp=None):
    '''读取pvfTree指定path的字节数据'''
    leaf:TreeLeaf = pvfTree.leafDict.get(path)
    if fp is None:
        fp = pvfTree.pvfHeader.fp
    if fp is None or fp.closed:
        fp = open(pvfTree.pvfHeader.pvfPath,'rb')
    if leaf is not None:
        fp.seek(pvfTree.pvfHeader.filePackIndexShift+leaf.relativeOffset)
        return fp.read(leaf.fileLength)
    else:
        return b'path error'

def getFilePack_leaf(leaf,pvfheader,fpath=''):
    '''读取pvfTree指定path的字节数据'''
    fp = open(fpath,'rb')
    if leaf is not None:
        fp.seek(pvfheader.filePackIndexShift+leaf.relativeOffset)
        return fp.read(leaf.fileLength)
    else:
        return b'path error'
    
def getFilePack2(path,pvfTree,fullFile:bytes):
    '''读取pvfTree指定path的字节数据'''
    leaf:TreeLeaf = pvfTree.leafDict.get(path)
    if leaf is not None:
        return fullFile[pvfTree.header.filePackIndexShift+leaf.relativeOffset:pvfTree.header.filePackIndexShift+leaf.relativeOffset+leaf.fileLength]     
    else:
        return b'path error'


class PVFHeader():
    def __init__(self,path):
        fp = open(path,'rb')
        self.pvfPath = path
        self.uuid_len = struct.unpack('i',fp.read(4))[0]
        self.uuid = fp.read(self.uuid_len)
        self.PVFversion = struct.unpack('i',fp.read(4))[0]
        self.dirTreeLength = struct.unpack('i',fp.read(4))[0] #长度
        self.dirTreeCrc32 = struct.unpack('I',fp.read(4))[0]
        self.numFilesInDirTree = struct.unpack('I',fp.read(4))[0]
        self.filePackIndexShift = fp.tell() + self.dirTreeLength
        #读内部文件树头
        unpackedHeaderTree = fp.read(self.dirTreeLength)
        #int_num = header.dirTreeLength//4
        self.unpackedHeaderTreeDecrypted = decryptBytes(unpackedHeaderTree,self.dirTreeCrc32)
        self.index = 0  #用于读取HeaderTree的指针
        self.fp = fp
    def getHeaderTreeBytes(self,byte_num=4):
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

class Lst():
    '''处理*.lst文件对象'''
    def __init__(self,contentBytes,pvf=None,baseDir='',encode='big5',leafDict={},pvfHeader:PVFHeader=None,pvfpath='',stringtable=None):
        self.vercode = contentBytes[:2]
        self.tableList = []
        self.tableDict = {} #存储lst的数据
        self.strDict = {}   #存储索引对应的str对象
        
        self.baseDir = baseDir
        self.pvf = pvf
        self.leafDict = leafDict
        if pvfHeader is not None:
            self.pvfHeader = pvfHeader
            if pvfpath!='':
                self.pvfHeader.pvfPath = pvfpath
        self.stringtable:StringTable = stringtable
        if pvf is not None: #PVF优先级更高
            self.stringtable:StringTable = pvf.stringtable
            self.pvfHeader = pvf.pvfHeader
            self.leafDict = pvf.leafDict
        i = 2
        while i+10<len(contentBytes):
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
            i+=10
    def __getitem__(self,n):
        '''返回字符串'''
        return self.tableDict[n]

    def getStr(self,path='',encode='big5'):
        '''读取.str文件，返回Str对象'''
        #print(path,len(self.leafDict.keys()))
        content = tmp_idPathContentDict.get(path.lower())
        if content is None:
            leaf = self.leafDict.get(path.lower())
            binFile = getFilePack_leaf(leaf,self.pvfHeader,self.pvfHeader.pvfPath)
            content = decryptBytes(binFile,leaf.fileCrc32).decode(encode,'ignore')
            tmp_idPathContentDict[path.lower()] = content
        return Str(content)

    def getNStr(self,n)->Str:
        res = self.strDict.get(n)
        if res is None:
            if self.pvf is not None:
                self.strDict[n] = self.pvf.getStr(path=self.tableDict[n])
                res = self.strDict.get(n)
            else:
                self.strDict[n] = self.getStr(path=self.tableDict[n])
                res = self.strDict.get(n)
        return res
    
    
    def __repr__(self):
        return 'Lst object. <'+str(self.tableList)[:100] + '...>'
    __str__ = __repr__

class Lst_lite():
    '''处理*.lst文件对象'''
    def __init__(self,contentBytes,idPathContentDict,stringtable,encode='big5'):
        self.vercode = contentBytes[:2]
        self.tableList = []
        self.tableDict = {} #存储lst的数据
        self.strDict = {}   #存储索引对应的str对象
        self.idPathContentDict = idPathContentDict
        self.stringtable:StringTable = stringtable
        i = 2
        while i+10<len(contentBytes):
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
            i+=10
    def __getitem__(self,n):
        '''返回字符串'''
        return self.tableDict[n]

    def getNStr(self,n)->Str:
        res = self.strDict.get(n)
        if res is None:
            content = self.idPathContentDict.get(self.tableDict[n].lower())
            self.strDict[n] = Str(content)#self.getStr(path=self.tableDict[n])
            res = self.strDict.get(n)
        return res
    
    def __repr__(self):
        return 'Lst object. <'+str(self.tableList)[:100] + '...>'
    __str__ = __repr__

class TreeLeaf():
    '''叶子节点，存放header的一条记录数据'''
    def __init__(self,pvfHeader:PVFHeader):
        self.fn = unpack('I',pvfHeader.getHeaderTreeBytes(4))[0]
        self.filePathLength = unpack('I',pvfHeader.getHeaderTreeBytes(4))[0]
        self.filePath = pvfHeader.getHeaderTreeBytes(self.filePathLength).decode("CP949")
        self.fileLength = (unpack('I',pvfHeader.getHeaderTreeBytes(4))[0]+ 3) & 0xFFFFFFFC
        self.fileCrc32 = unpack('I',pvfHeader.getHeaderTreeBytes(4))[0]
        self.relativeOffset = unpack('I',pvfHeader.getHeaderTreeBytes(4))[0]
    def __repr__(self) -> str:
        return f'file_number:{self.fn} path:{self.filePath} file_length:{self.fileLength} CRC :{hex(self.fileCrc32)} offset:{self.relativeOffset}'

class TinyPVF():
    '''用于快速查询的pvf节点'''
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def getFileInList(leaf:TreeLeaf,pvfheader:PVFHeader,stringtable:StringTable,nString:Lst,fpath:str):
        '''读取二进制文本，如stk文件，将解密字段类型和关键字返回为list'''
        binFile = getFilePack_leaf(leaf,pvfheader,fpath)
        content = decryptBytes(binFile,leaf.fileCrc32)
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
                valuesRead.append(nString.getNStr(values[i])[stringtable[values[i+1]]])
        return [types,valuesRead]
    
    @staticmethod
    def content2List(content,stringtable:StringTable,nString:Lst):
        '''读取二进制文本，如stk文件，将解密字段类型和关键字返回为list'''
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
                valuesRead.append(nString.getNStr(values[i])[stringtable[values[i+1]]])
        return [types,valuesRead]

class FileTree():
    '''PVF文件树对象'''
    def __init__(self,path='',parent=None,leaf:TreeLeaf=None,content=b'',pvfHeader:PVFHeader=None,root=None):
        if parent is None:
            parent = self   #上级目录指向自己
        if root is None:
            root = self     #根节点
        self._leaf = leaf
        self._parent = parent
        self._subDirs = []
        self._content = content #存放原始二进制数据
        self._root = root
        self._fileNum = 0
        if len(path)>0 and path[0]=='/':
            path = path[1:] #去掉最开始的/以免生成树的时候出现死循环
        self._path = path

        self._name = Path(path).name#os.path.split(path)[-1]
        if pvfHeader is not None:
            self.pvfHeader = pvfHeader
    def addDir(self,fileTree):
        '''将目录树加入'''
        p = Path(fileTree._path)
        dirName = p.parent.name 
        baseName = p.name
        #dirName, baseName = os.path.split(fileTree._path)   #当前目录下的文件/文件夹，直接设置为子目录/文件
        self._fileNum +=1
        if dirName == self._path:
            if not hasattr(self,baseName):
                self._subDirs.append(fileTree)
                setattr(self,baseName,fileTree)
                fileTree._parent = self
                fileTree._root = self._root
        elif self._path == dirName[:len(self._path)]: #当前目录的子目录,判断下一级子目录是否存在，不存在就创建，然后调用该目录进行addDir
            if self._path!='':perfixLen = len(self._path)+1
            else:perfixLen = len(self._path)
            subdir,*tmp = dirName[perfixLen:].split('/')
            if not hasattr(self,subdir):
                #print('create path ' + self._path+'/'+subdir + ' ' + directory._path)
                self.addDir(FileTree(self._path+'/'+subdir,self,root=self._root))
                #print('Dir added. ' + self._path+'/'+subdir)
                #if self.path=='':print(subdir, directory._path)
            getattr(self,subdir).addDir(fileTree)

    def loadLeafs(self,dirs=[]):
        '''读取pvf目录生成文件树和叶子数据，根据传入的目录进行加载，传入目录为空时全部加载'''
        dirTreeLeafList = []
        leafDict = {}
        self.pvfHeader.index = 0
        for i in range(self.pvfHeader.numFilesInDirTree):
            leaf = TreeLeaf(self.pvfHeader)
            if len(dirs)>0:
                paths = leaf.filePath.split('/')
                if len(paths)>1 and paths[0] not in dirs:
                    continue
            dirTreeLeafList.append(leaf)
            #leafDict[leaf.fn] = leaf
            leafDict[leaf.filePath] = leaf
            self.addDir(FileTree(leaf.filePath,leaf=leaf))
        self.leafDict = leafDict
        self.dirTreeLeafList = dirTreeLeafList
        self.stringtable = StringTable(self.getDecryptedBin('stringtable.bin'))
        self.nStringTable = Lst(self.getDecryptedBin('n_string.lst'),leafDict=self.leafDict,pvfHeader=self.pvfHeader,stringtable=self.stringtable)#,self
        self.nStringTableLite = Lst_lite(self.getDecryptedBin('n_string.lst'),tmp_idPathContentDict,stringtable=self.stringtable)
    
    @property
    def nString(self):
        '''相当于调用nstringtable'''
        if hasattr(self,'nStringTable'):
            return self.nStringTable
        else:
            return self._root.nStringTable
    
    def __repr__(self):
        if len(self._subDirs)==0:   #当前节点下没有子节点，为二进制文件
            return f'binary file {self._path}'
        res = f'{self._path}\n'
        for subdir in self._subDirs:    #当前节点下有子节点，为文件夹
            res += f'\t{subdir._name}\n'
        return res
    __str__ = __repr__

    def __getitem__(self,key):
        if hasattr(self,key):
            return getattr(self,key)
    
    def getBin(self,path=''):
        '''返回原始二进制流'''
        if path=='':
            path = self._path
        res = getFilePack(path,self._root)
        '''if path == self._path:
            self._content = res'''
        return res
    
    def getDecryptedBin(self,path:str=''):
        '''传入路径，返回初步解密后的字节流'''
        if path=='':
            path = self._path
        path = path.lower()
        res = decryptBytes(getFilePack(path,self._root),self._root.leafDict[path].fileCrc32)
        tmp_idPathContentDict[path] = res
        return res

    def getNStringText(self,n):
        '''获取nstring文件的第n索引的文本内容'''
        path = self.nString.tableDict[n]
        fileText = self.getDecryptedBin(path).decode('big5')
        return fileText

    def getFileInList(self,path=''):
        '''读取二进制文本，如stk文件，将解密字段类型和关键字返回为list'''
        if path=='':
            content = self.getDecryptedBin()
        else:
            content = self.getDecryptedBin(path)
        shift = 2
        unit_num = (len(content)-2)//5
        structPattern = '<'
        unitTypes = []
        res = {}
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
                valuesRead.append(self._root.stringtable[values[i]])
            elif types[i] in [6]:
                valuesRead.append(self._root.stringtable[values[i]])
            elif types[i] in [7]:
                valuesRead.append(self._root.stringtable[values[i]])
            elif types[i] in [8]:
                valuesRead.append(self._root.stringtable[values[i]])
            elif types[i] in [9]:
                valuesRead.append(self.nString.getNStr(values[i])[self._root.stringtable[values[i+1]]])
        return [types,valuesRead]

    def getFileInDict(self,path=''):
        '''FIXME:将指定二进制文件按stk规则读取后返回dict'''
        stkvalue = self.getFileInList(path)
        stkDict = {}
        key = ''
        value_ = ''
        for value in stkvalue[1]:
            value = str(value)
            if  len(value)>2 and value[0]=='[' and value[-1]==']':
                if key!='':stkDict[key]=value_
                key = value[1:-1]
                value_ = ''
            else:
                value_ += value
        return stkDict
    
    def _content2text(self,content:bytes):
        '''FIXME:处理普通文本，stk等'''
        shift = 2
        unit_num = (len(content)-2)//5
        structPattern = '<'
        unitTypes = []
        text = ''
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
        for i in range(unit_num):
            if types[i] in [2]:
                text += str(values[i]) + '\t'
            if types[i] in [3]:
                text += "{IntEx=`" + str(values[i]) + "`}\t"
            elif types[i] in [4]:
                text += '%.6f' % values[i] + "\t"
            elif types[i] in [5]:
                text +=f'\n{self._root.stringtable[values[i]]}\n'
            elif types[i] in [6]:
                text += '{Command=`' + self._root.stringtable[values[i]] + "`}\n"
            elif types[i] in [7]:
                text += "`" + self._root.stringtable[values[i]] + "`\n"
            elif types[i] in [8]:
                text += '{CommandSeparator=`' + self._root.stringtable[values[i]] + "`}\n"
            elif types[i] in [9,10]:
                text += self._root.stringtable[values[i+1]] + self.nString.getNStr(values[i])[self._root.stringtable[values[i+1]]]#"<StringLinkIndex" + "::" + (self._root.stringtable[values[i+1]]) + "`" #+ (self.nString[values[i]].keyValPairList[stringtable[values[i+1]]]) +"`>\r\n"
        return text

    def getFileInText(self,path=''):
        '''尝试将文件转换为文本'''
        content = self.getDecryptedBin(path)
        return self._content2text(content)
    
    def getLst(self,path='',encode='big5'):
        '''读取并创建lst对象'''
        if path=='':
            content = self.getDecryptedBin()
            baseDir = self._parent._path
        else:
            content = self.getDecryptedBin(path)
            p = Path(path)
            baseDir = p.parent.name 
            basename = p.name
            #baseDir,basename = os.path.split(path)
        return Lst(content,self._root,baseDir,encode)

    def getStr(self,path='',encode='big5'):
        '''读取.str文件，返回Str对象'''
        if path=='':
            content = self.getDecryptedBin().decode(encode,'ignore')
        else:
            content = self.getDecryptedBin(path).decode(encode,'ignore')
        return Str(content)

    def getTree(self,path:str):
        '''传入相对路径，返回树节点'''
        indexes = path.split('/')
        treeCurrent = self
        for index in indexes:
            treeCurrent = getattr(treeCurrent,index)
        return treeCurrent
    def getFiles(self,depth=1):
        '''返回当前目录下除去目录的所有文件列表'''
        res = []
        for obj in self._subDirs:
            if len(obj._subDirs)==0:
                res.append(obj)
            elif depth!=1:
                res.extend(obj.getFiles(depth-1))
        return res



itemLST_LIST =[ #存放物品列表的lst文件
    #['itemname.lst','CP949'],
    ['stackable/stackable.lst','big5'],
    
    ['equipment/equipment.lst','big5']
]
tmp_idPathContentDict = {}
def getItemDict(pvf:FileTree):
    '''传入pvf文件树，返回物品id:name的字典'''
    stackable_dict = {}
    leafDict_lite = {}
    #stackable_dict['stackablePath_dict'] = {}
    
    for path,encode in itemLST_LIST:
        ItemLst = pvf.getLst(path,encode=encode)
        for id_,path_ in ItemLst.tableList:
            try:
                res = pvf.getFileInDict(ItemLst.baseDir+'/'+path_)
                stackable_dict[id_] = res.get('name')
                leafDict_lite[id_] = pvf.leafDict[ItemLst.baseDir+'/'+path_.lower()]
                tmp_idPathContentDict[id_] = tmp_idPathContentDict[ItemLst.baseDir+'/'+path_.lower()]
                #stackable_dict['stackablePath_dict'][id_] = ItemLst.baseDir+'/'+path_
                
            except: #路径不存在
                stackable_dict[id_] = path_
    #stackable_dict['leafDict_lite'] = leafDict_lite
    stackable_dict['idPathContentDict'] = tmp_idPathContentDict
    return stackable_dict


def loadSkills(pvf:FileTree):
    '''数据库的skill表，blob字段解压后每两个字节代表一个技能，分别是技能编号和技能等级'''
    ...

def test():
    PVF = r'Script.pvf'
    pvf = FileTree(pvfHeader=PVFHeader(PVF))
    print(pvf.pvfHeader)
    pvf.loadLeafs(['character','stackable','equipment'])

    print(pvf.leafDict["stringtable.bin"])
    print(pvf["stringtable.bin"])
    print(pvf.nString)
    print(Str(pvf.getDecryptedBin(list(pvf.nString.tableDict.values())[0]).decode('big5')))
    #print(pvf.stackable)
    print(pvf.leafDict[r'stackable/10000134.stk'])
    pvf.getFileInList('stackable/book_skill2.stk')
    print('tinyPVF读取文件：',TinyPVF.getFileInList(pvf.leafDict['stackable/book_skill2.stk'],pvf.pvfHeader,pvf.stringtable,pvf.nString,pvf.pvfHeader.pvfPath))



    print('pvf根目录文件数量：',len(pvf.getFiles()))
    print('pvf文件总数量：',len(pvf.getFiles(0)))
    print('pvf stackable目录下文件数量：',len(pvf.stackable.getFiles()))
    print('pvf stackable目录递归查询文件数量：',len(pvf.stackable.getFiles(0)))

    stackable_dict = getItemDict(pvf)
    print('物品列表加载：',str(stackable_dict)[:200])
    return pvf

if __name__=='__main__':
    
    pvf = test()


    



