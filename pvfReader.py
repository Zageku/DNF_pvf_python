import struct
from struct import unpack
#import os
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





def decryptBytes_old(inputBytes,crc):
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


def get_File_fp_path(path,pvfTree,fp=None):
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

def get_FilePack_leaf_pvfPath(leaf,pvfheader,fpath=''):
    '''读取pvfTree指定path的字节数据'''
    fp = open(fpath,'rb')
    if leaf is not None:
        fp.seek(pvfheader.filePackIndexShift+leaf.relativeOffset)
        return fp.read(leaf.fileLength)
    else:
        return b'path error'
    
def get_File_FullPack_path(path,pvfTree,fullFile:bytes=b''):
    '''读取pvfTree指定path的字节数据'''
    leaf:TreeLeaf = pvfTree.leafDict.get(path)
    if fullFile==b'':
        fullFile = pvfTree.pvfHeader.fullFile
    if leaf is not None:
        return fullFile[pvfTree.pvfHeader.filePackIndexShift+leaf.relativeOffset:pvfTree.pvfHeader.filePackIndexShift+leaf.relativeOffset+leaf.fileLength]     
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
            i+=10
    def __getitem__(self,n):
        '''返回字符串'''
        return self.tableDict[n]

    def read_Str_file(self,path='',encode='big5'):
        '''按路径读取.str文件，返回Str对象'''
        #print(path,len(self.leafDict.keys()))
        content = tmp_idPathContentDict.get(path.lower())
        if content is None:
            leaf = self.leafDict.get(path.lower())
            if leaf is None:
                self.pvf.loadLeafs(path = [path])
            binFile = get_FilePack_leaf_pvfPath(leaf,self.pvfHeader,self.pvfHeader.pvfPath)
            content = decrypt_Bytes(binFile,leaf.fileCrc32)
            tmp_idPathContentDict[path.lower()] = content
        return Str(content.decode(encode,'ignore'))

    def get_N_Str(self,n)->Str:
        '''读取lst第n条记录并返回Str对象'''
        res = self.strDict.get(n)
        if res is None:
            if self.pvf is not None:
                self.strDict[n] = self.pvf.load_Str_File(path=self.tableDict[n])
                res = self.strDict.get(n)
            else:
                self.strDict[n] = self.read_Str_file(path=self.tableDict[n])
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
            self.encode = encode
            i+=10
    def __getitem__(self,n):
        '''返回字符串'''
        return self.tableDict[n]

    def get_N_Str(self,n)->Str:
        res = self.strDict.get(n)
        if res is None:
            content = self.idPathContentDict.get(self.tableDict[n].lower())
            self.strDict[n] = Str(content.decode(self.encode,'ignore'))#self.getStr(path=self.tableDict[n])
            res = self.strDict.get(n)
        return res
    
    def __repr__(self):
        return 'Lst object. <'+str(self.tableList)[:100] + '...>'
    __str__ = __repr__

class TreeLeaf():
    '''叶子节点，存放header的一条记录数据'''
    def __init__(self,pvfHeader:PVFHeader):
        self.fn = unpack('I',pvfHeader.get_Header_Tree_Bytes(4))[0]
        self.filePathLength = unpack('I',pvfHeader.get_Header_Tree_Bytes(4))[0]
        self.filePath = pvfHeader.get_Header_Tree_Bytes(self.filePathLength).decode("CP949")
        self.fileLength = (unpack('I',pvfHeader.get_Header_Tree_Bytes(4))[0]+ 3) & 0xFFFFFFFC
        self.fileCrc32 = unpack('I',pvfHeader.get_Header_Tree_Bytes(4))[0]
        self.relativeOffset = unpack('I',pvfHeader.get_Header_Tree_Bytes(4))[0]
    def __repr__(self) -> str:
        return f'file_number:{self.fn} path:{self.filePath} file_length:{self.fileLength} CRC :{hex(self.fileCrc32)} offset:{self.relativeOffset}'

class TinyPVF():
    '''用于快速查询的pvf节点'''
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def read_File_In_List(leaf:TreeLeaf,pvfheader:PVFHeader,stringtable:StringTable,nString:Lst_lite,fpath:str):
        '''读取二进制文本，如stk文件，将解密字段类型和关键字返回为list'''
        binFile = get_FilePack_leaf_pvfPath(leaf,pvfheader,fpath)
        content = decrypt_Bytes(binFile,leaf.fileCrc32)
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
                valuesRead.append(nString.get_N_Str(values[i])[stringtable[values[i+1]]])
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
        self.leafDict = {}
        self._fileNum = 0
        if len(path)>0 and path[0]=='/':
            path = path[1:] #去掉最开始的/以免生成树的时候出现死循环
        self._path = path

        self._name = path.rsplit('/',1)[-1]#Path(path).name#os.path.split(path)[-1]
        if pvfHeader is not None:
            self.pvfHeader = pvfHeader
    def add_Dir(self,fileTree):
        '''将目录树加入'''
        if '/' in fileTree._path:
            dirName, baseName = fileTree._path.rsplit('/',1)
        else:
            dirName = ''
            baseName = fileTree._path
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
                self.add_Dir(FileTree(self._path+'/'+subdir,self,root=self._root))
                #print('Dir added. ' + self._path+'/'+subdir)
                #if self.path=='':print(subdir, directory._path)
            getattr(self,subdir).add_Dir(fileTree)

    def loadLeafs(self,dirs=[],paths:list=[]):
        '''读取pvf目录生成文件树和叶子数据，根据传入的目录进行加载，传入目录为空时全部加载'''
        #dirTreeLeafList = []
        leafDict = {}
        self.pvfHeader.index = 0
        if len(paths)==0:
            for i in range(self.pvfHeader.numFilesInDirTree):
                leaf = TreeLeaf(self.pvfHeader)
                if len(dirs)>0:
                    leafpaths = leaf.filePath.split('/')
                    if len(leafpaths)>1 and leafpaths[0] not in dirs:
                        continue

                leafDict[leaf.filePath] = leaf
                self.add_Dir(FileTree(leaf.filePath,leaf=leaf))
        else:
            for i in range(self.pvfHeader.numFilesInDirTree):
                leaf = TreeLeaf(self.pvfHeader)
                if leaf.filePath.lower() not in paths:
                    continue
                leafDict[leaf.filePath] = leaf
                self.add_Dir(FileTree(leaf.filePath,leaf=leaf))
                paths.remove(leaf.filePath)
        self.leafDict.update(leafDict)
        #self.dirTreeLeafList = dirTreeLeafList
        if hasattr(self,'stringtable'):
            return leafDict
        self.stringtable = StringTable(self.get_Decrypted_Bin('stringtable.bin'))
        self.nStringTable = Lst(self.get_Decrypted_Bin('n_string.lst'),leafDict=self.leafDict,pvf=self,pvfHeader=self.pvfHeader,stringtable=self.stringtable)#,self
        self.nStringTableLite = Lst_lite(self.get_Decrypted_Bin('n_string.lst'),tmp_idPathContentDict,stringtable=self.stringtable)
        return leafDict
    
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
    
    def get_Bin(self,path=''):
        '''返回原始二进制流'''
        if path=='':
            path = self._path
        res = get_File_FullPack_path(path,self._root)
        '''if path == self._path:
            self._content = res'''
        return res
    
    def get_Decrypted_Bin(self,path:str=''):
        '''传入路径，返回初步解密后的字节流'''
        if path=='':
            path = self._path
        path = path.lower()
        if path not in self._root.leafDict.keys():
            self._root.loadLeafs(paths=[path])
        res = decrypt_Bytes(get_File_FullPack_path(path,self._root),self._root.leafDict[path].fileCrc32)
        tmp_idPathContentDict[path] = res
        return res

    def get_NString_Text_n(self,n):
        '''获取nstring文件的第n索引的文本内容'''
        path = self.nString.tableDict[n]
        fileText = self.get_Decrypted_Bin(path).decode('big5')
        return fileText

    def read_File_In_List(self,path=''):
        '''读取二进制文本，如stk文件，将解密字段类型和关键字返回为list'''
        if path=='':
            content = self.get_Decrypted_Bin()
        else:
            content = self.get_Decrypted_Bin(path)
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
                valuesRead.append(self.nString.get_N_Str(values[i])[self._root.stringtable[values[i+1]]])
        return [types,valuesRead]

    def read_File_In_Dict(self,path=''):
        '''FIXME:将指定二进制文件按stk规则读取后返回dict'''
        stkvalue = self.read_File_In_List(path)
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
    
    def read_File_In_Dict2(self,path=''):
        '''将指定二进制文件按stk规则读取后返回dict'''
        stkvalue = self.read_File_In_List(path)
        stkDict = {}
        key = ''
        value_ = ''
        for i in range(len(stkvalue[1])):
            if stkvalue[0][i] == 5:
                if isinstance(stkvalue[1][i],str) and '/' not in stkvalue[1][i]:
                    stkDict[key] = value_
                    key = stkvalue[1][i].replace('[','').replace(']','')
                else:
                    stkDict[key] = value_
                    key = ''
                value_ = ''
            else:
                value_ += ' ' + str(stkvalue[1][i])
                
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
                text += self._root.stringtable[values[i+1]] + self.nString.get_N_Str(values[i])[self._root.stringtable[values[i+1]]]#"<StringLinkIndex" + "::" + (self._root.stringtable[values[i+1]]) + "`" #+ (self.nString[values[i]].keyValPairList[stringtable[values[i+1]]]) +"`>\r\n"
        return text

    def read_File_In_Text(self,path=''):
        '''尝试将文件转换为文本'''
        content = self.get_Decrypted_Bin(path)
        return self._content2text(content)
    
    def load_Lst_File(self,path='',encode='big5'):
        '''读取并创建lst对象'''
        if path=='':
            content = self.get_Decrypted_Bin()
            baseDir = self._parent._path
        else:
            content = self.get_Decrypted_Bin(path)
            if '/' in path:
                baseDir,basename = path.rsplit('/',1)
            else:
                baseDir = ''
                basename = path

            #baseDir,basename = os.path.split(path)
        return Lst(content,self._root,baseDir,encode)

    def load_Str_File(self,path='',encode='big5'):
        '''读取.str文件，返回Str对象'''
        if path=='':
            content = self.get_Decrypted_Bin().decode(encode,'ignore')
        else:
            content = self.get_Decrypted_Bin(path).decode(encode,'ignore')
        return Str(content)

    def get_FileTree(self,path:str):
        '''传入相对路径，返回树节点'''
        indexes = path.split('/')
        treeCurrent = self
        for index in indexes:
            treeCurrent = getattr(treeCurrent,index)
        return treeCurrent
    def get_file_list(self,depth=1):
        '''返回当前目录下除去目录的所有文件列表'''
        res = []
        for obj in self._subDirs:
            if len(obj._subDirs)==0:
                res.append(obj)
            elif depth!=1:
                res.extend(obj.getFiles(depth-1))
        return res





tmp_idPathContentDict = {}

def get_Magic_Seal_Dict(pvf:FileTree):
    import zhconv
    magicSealPath = r'etc/randomoption/randomizedoptionoverall2.etc'
    
    print('魔法封印加载...')
    try:
        res = pvf.read_File_In_List(magicSealPath)
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


def get_Job_Dict(pvf:FileTree):
    jobDict = {}
    if not hasattr(pvf,'character'):
        pvf.loadLeafs(['character'])
    characs = pvf.load_Lst_File('character/character.lst')
    print('角色信息加载...')
    for id_,path in characs.tableList:
        growTypes = {}
        chrFileInList = pvf.read_File_In_List(characs.baseDir+'/'+path)
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
    return jobDict

def get_Equipment_Dict(pvf:FileTree):
    
    equipmentStructuredDict = {}#拥有目录结构的dict
    equipmentDict = {}  #只有id对应的dict
    pvf.loadLeafs(['equipment'])
    path = 'equipment/equipment.lst'
    ItemLst = pvf.load_Lst_File(path,encode='big5')
    print('装备信息加载...')
    for id_,path_ in ItemLst.tableList:
        try:
            dirs = path_.split('/')[:-1]
            detailedDict = equipmentStructuredDict
            for dirName in dirs:
                if dirName not in detailedDict.keys():
                    detailedDict[dirName] = {}
                detailedDict = detailedDict[dirName]
                
            res = pvf.read_File_In_Dict(ItemLst.baseDir+'/'+path_)
            equipmentDict[id_] = res.get('name')
            detailedDict[id_] = equipmentDict[id_]
            tmp_idPathContentDict[id_] = tmp_idPathContentDict[ItemLst.baseDir+'/'+path_.lower()]
        except: #路径不存在
            equipmentDict[id_] = path_
    return equipmentStructuredDict, equipmentDict



itemLST_LIST =[ #存放物品列表的lst文件
        #['itemname.lst','CP949'],
        ['stackable/stackable.lst','big5'],
        
        #['equipment/equipment.lst','big5']
    ]  

def get_Stackable_dict(pvf:FileTree):
    
    path,encode = ['stackable/stackable.lst','big5']
    ItemLst = pvf.load_Lst_File(path,encode=encode)
    stackable_dict = {}
    print('物品信息加载...')
    for id_,path_ in ItemLst.tableList:
        try:
            res = pvf.read_File_In_Dict(ItemLst.baseDir+'/'+path_)
            stackable_dict[id_] = res.get('name')
            tmp_idPathContentDict[id_] = tmp_idPathContentDict[ItemLst.baseDir+'/'+path_.lower()]
        except: #路径不存在
            stackable_dict[id_] = path_
    return stackable_dict

def get_Item_Dict(pvf:FileTree):
    '''传入pvf文件树，返回物品id:name的字典'''

    pvf.loadLeafs(['stackable','character','etc'])
    #magicLeaf = pvf.loadLeafs([])

    all_item_dict = {}
    magicSealDict = get_Magic_Seal_Dict(pvf)
    all_item_dict['magicSealDict'] = magicSealDict

    jobDict = get_Job_Dict(pvf)
    all_item_dict['jobDict'] = jobDict

    equipmentStructuredDict, equipmentDict = get_Equipment_Dict(pvf)
    all_item_dict['equipment'] = equipmentDict
    all_item_dict['equipmentStructuredDict'] = equipmentStructuredDict

    stackable_dict = get_Stackable_dict(pvf)
    all_item_dict['stackable'] = stackable_dict

    all_item_dict['idPathContentDict'] = tmp_idPathContentDict
    return all_item_dict




def test():
    import time
    t1 = time.time()
    PVF = r'E:\DNF local\客户端20230212\KHD\Script.pvf'
    pvf = FileTree(pvfHeader=PVFHeader(PVF))
    t2 = time.time()
    print(pvf.pvfHeader)
    pvf.loadLeafs(['character','stackable','equipment'])
    t3 = time.time()
    print(pvf.leafDict["stringtable.bin"])
    print(pvf["stringtable.bin"])
    print(pvf.nString)
    print(Str(pvf.get_Decrypted_Bin(list(pvf.nString.tableDict.values())[0]).decode('big5')))
    #print(pvf.stackable)
    print(pvf.leafDict[r'stackable/10000134.stk'])
    pvf.read_File_In_List('stackable/book_skill2.stk')
    print('tinyPVF读取文件：',TinyPVF.read_File_In_List(pvf.leafDict['stackable/book_skill2.stk'],pvf.pvfHeader,pvf.stringtable,pvf.nString,pvf.pvfHeader.pvfPath))



    print('pvf根目录文件数量：',len(pvf.get_file_list()))
    print('pvf文件总数量：',len(pvf.get_file_list(0)))
    print('pvf stackable目录下文件数量：',len(pvf.stackable.getFiles()))
    print('pvf stackable目录递归查询文件数量：',len(pvf.stackable.getFiles(0)))
    t4 = time.time()
    stackable_dict = get_Item_Dict(pvf)
    t5 = time.time()
    print('物品列表加载：',str(stackable_dict)[:2000])
    print('物品列表加载：',stackable_dict[0])
    print('加载pvf头，加载叶子节点，显示一些数据，读取文件获取物品目录，总耗时')
    print(t2-t1,t3-t2,t4-t3,t5-t4,t5-t1)
    return pvf

def test2():
    import time
    t1 = time.time()
    PVF = r'E:\system sound infomation\客户端20221030\地下城与勇士\Script.pvf'
    pvf = FileTree(pvfHeader=PVFHeader(PVF))
    t2 = time.time()
    print(pvf.pvfHeader)
    paths = [item[0] for item in itemLST_LIST]
    paths.extend(['stringtable.bin','n_string.lst'])
    pvf.loadLeafs(paths=paths)
    print(pvf.get_file_list())
    res = get_Magic_Seal_Dict(pvf)
    import json
    json.dump(res,open('magicSealDict.json','w'))
    for item in res.items():
        print(item)
    print('===魔法封印结束')

    equipmentDetialedDict, equipmentDict = get_Equipment_Dict(pvf)
    print(equipmentDetialedDict.keys())
    print(str(equipmentDetialedDict)[:2000])
    print('====装备结束')

    pvf.loadLeafs(['stackable'])
    t3 = time.time()
    stackable_dict = {}
    path,encode = ['stackable/stackable.lst','big5']
    ItemLst = pvf.load_Lst_File(path,encode=encode)
    for id_,path_ in ItemLst.tableList:
        try:
            res = pvf.read_File_In_Dict(ItemLst.baseDir+'/'+path_)
            stackable_dict[id_] = res.get('name')
            #leafDict_lite[id_] = pvf.leafDict[ItemLst.baseDir+'/'+path_.lower()]
            tmp_idPathContentDict[id_] = tmp_idPathContentDict[ItemLst.baseDir+'/'+path_.lower()]
        except: #路径不存在
            stackable_dict[id_] = path_
    stackable_dict.update(equipmentDict)
    t4 = time.time()
    print('物品列表加载：',str(stackable_dict)[:2000])
    print('====物品结束')
    
    print(t4-t1,'s')

def test3():
    PVF = r'E:\system sound infomation\客户端20221030\地下城与勇士\Script.pvf'
    pvf = FileTree(pvfHeader=PVFHeader(PVF))
    jobDict = get_Job_Dict(pvf)
    print(jobDict)
    with open('jobDict.json','w') as f:
        json.dump(jobDict,f)
    return pvf,jobDict

def test4():
    PVF = r'E:\system sound infomation\客户端20221030\地下城与勇士\Script.pvf'
    pvf = FileTree(pvfHeader=PVFHeader(PVF))
    items = get_Item_Dict(pvf)
    print('加载完成...')
    for key,value in items.items():
        if isinstance(value,str):
            continue
        print(key,len(value))

if __name__=='__main__':
    
    test4()


    



