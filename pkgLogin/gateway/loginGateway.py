# -*- coding:utf-8 -*-
import socket
import pymysql_new as pymysql
from pymysql_new.cursors import Cursor
import asyncio
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5 as PKCS1_signature
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
import base64
import json
import pickle
import datetime
import threading
import signal
import traceback
import random
import time
import os


def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    exit(0)

DB_IP = '127.0.0.1'
DB_PORT = 3306
DB_USER = 'game'
DB_PWD = 'uu5!^jg'
SERVER_ADDR = ('0.0.0.0',10086)
INIT_CERA = 100000
INIT_CERAPOINT = 100000
serverList = []
cfgFile = 'gateway.json'
if os.path.exists(cfgFile):
    with open(cfgFile,'r',encoding='utf-8') as f:
        configDict = json.loads(f.read())
        DB_IP = configDict.get('DB_IP',DB_IP)
        DB_PORT = configDict.get('DB_PORT',DB_PORT)
        DB_USER = configDict.get('DB_USER',DB_USER)
        DB_PWD = configDict.get('DB_PWD',DB_PWD)
        SERVER_ADDR = configDict.get('SERVER_IP',('0.0.0.0',10086))
        SERVER_ADDR = ('0.0.0.0',SERVER_ADDR[1])
        INIT_CERA = configDict.get('INIT_CERA',INIT_CERA)
        INIT_CERAPOINT = configDict.get('INIT_CERAPOINT',INIT_CERAPOINT)
        serverList = configDict.get('SERVER_LIST',serverList)
        

if not isinstance(serverList,list):
    serverList = [serverList]

print(f'网关监听地址:{SERVER_ADDR}')
print(f'数据库地址:{DB_IP}:{DB_PORT}')
print(f'初始CERA:{INIT_CERA}')
print(f'初始CERAPOINT:{INIT_CERAPOINT}')
print(f'数据库账号:{DB_USER}')
print(f'数据库密码:{DB_PWD}')
print(f'服务器:{serverList[0]["name"]}')


def inThread(func):
    def inner(*args,**kw):
        t = threading.Thread(target=lambda:func(*args,**kw))
        t.setDaemon(True)
        t.start()
        return t
    return inner


execute_queue = []  #[(taskID,args,'fetch'/'commit'/None),...]
resDict = {}    # {id:res}
@inThread
def executor():
    global execute_queue
    while True:
        if len(execute_queue)>0:
            try:
                taskID,args,execType = execute_queue.pop(0)
                if execType=='fetch':
                    resDict[taskID] = execute_fech(*args)
                    #oldPrint(taskID,args,resDict[taskID])
                elif execType=='commit':
                    resDict[taskID] = execute_commit(*args)
                else:
                    resDict[taskID] = execute(*args)
            except Exception as e:
                print(f'[执行错误]{args} {e}')
        else:
            time.sleep(0.001)
executor()

def genTaskID():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S%f') + str(random.randint(0,100000))

connectorDict = {}
def newConnector(db=''):
    global  connectorDict
    print(f'新连接,{db}')
    for _ in range(2):
        try:
            dbConn = pymysql.connect(user=DB_USER, password=DB_PWD, host=DB_IP, port=DB_PORT, database=db,charset='utf8',connect_timeout=2,autocommit=True)
            connectorDict[db] = dbConn

            return True
        except Exception as e:
            traceback.print_exc()
            pass
    return False

def execute(db,sql,args=None,charset='utf8',reConn=True):
    if connectorDict.get(db) is None:
        if not newConnector(db):
            print(db,sql,args)
            print(f'数据库{db}连接失败')
            return []
    try:
        connector:pymysql.connections.Connection = connectorDict[db]
        connector.set_charset(charset)
        cursor = connector.cursor()
        if args is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql,args)
        print(sql)
        return True
    except Exception as e:
        if reConn:
            #print(f'数据库{db}连接失败，尝试重新连接... 错误信息:{e}')
            connectorDict[db] = None
            return execute(db,sql,args,charset,False)

def execute_fech(db,sql,args=None,charset='utf8',reConn=True):
    #print(db,connectorDict,connectorDict.get(db))
    if connectorDict.get(db) is None:
        if not newConnector(db):
            print(db,sql,args)
            print(f'数据库{db}连接失败')
            return []
    try:
        #print(sql,'执行中')
        connector:pymysql.connections.Connection = connectorDict[db]
        connector.set_charset(charset)
        cursor = connector.cursor()
        if args is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql,args)
        res = cursor.fetchall()
        return res
    except Exception as e:
        if reConn:
            print(f'数据库{db}连接失败，尝试重新连接... 错误信息:{e}')
            connectorDict[db] = None
            return execute_fech(db,sql,args,charset,False)

def execute_commit(db,sql,args=None,charset='utf8',reConn=True):
    if connectorDict.get(db) is None:
        if not newConnector(db):
            #print(db,sql,args)
            print(f'数据库{db}连接失败')
            return False
    try:
        #print(sql)
        connector:pymysql.connections.Connection = connectorDict[db]
        connector.set_charset(charset)
        cursor = connector.cursor()
        if args is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql,args)
        connector.commit()
        return True
    except Exception as e:
        if reConn:
            traceback.print_exc()
            print(f'数据库{db}语句执行失败，尝试重新连接... 错误信息:{e}')
            connectorDict[db] = None
            return execute_commit(db,sql,args,charset,False)
    print(f'数据库{db}语句{sql}执行失败')
    return False


def execute_sql(db,sql,args=None,charset='utf8'):
    taskID = genTaskID()#datetime.datetime.now().strftime('%Y%m%d%H%M%S%f') + str(random.randint(0,1000))
    execute_queue.append((taskID,[db,sql,args,charset],'execute'))
    while True:
        if resDict.get(taskID) is not None:
            res = resDict.pop(taskID)
            return res
        else:
            time.sleep(0.005)

def execute_and_fech(db,sql,args=None,charset='utf8'):
    taskID = genTaskID()#datetime.datetime.now().strftime('%Y%m%d%H%M%S%f') + str(random.randint(0,1000))
    execute_queue.append((taskID,[db,sql,args,charset],'fetch'))
    while True:
        if resDict.get(taskID) is not None:
            res = resDict.pop(taskID)
            return res
        else:
            time.sleep(0.005)

def execute_and_commit(db,sql,args=None,charset='utf8'):
    taskID = genTaskID()#datetime.datetime.now().strftime('%Y%m%d%H%M%S%f') + str(random.randint(0,1000))
    execute_queue.append((taskID,[db,sql,args,charset],'commit'))
    while True:
        if resDict.get(taskID) is not None:
            res = resDict.pop(taskID)
            return res
        else:
            time.sleep(0.005)

def commit_all():
    for connector in connectorDict.values():
        try:
            connector.commit()
        except:
            pass

db:pymysql.Connection = None
cur:Cursor = None
def connect_sql():
    global db,cur, pymysql
    try:
        db = pymysql.connect(user=DB_USER, password=DB_PWD, host=DB_IP, port=DB_PORT, charset='utf8',connect_timeout=2)
        cur = db.cursor()
    except:
        import pymysql_old as pymysql
        from pymysql_old.cursors import Cursor
        db = pymysql.connect(user=DB_USER, password=DB_PWD, host=DB_IP, port=DB_PORT, charset='utf8',connect_timeout=2)
        cur = db.cursor()
    return True

def loadPEM():
    '''获取TCP私钥、登陆加密私钥'''
    PEMPATH = 'pkglogin_private_tcp.pem'
    with open(PEMPATH, "r") as f:
        private_key_ = f.read()                                # 获取私钥
    priKeyTCP = RSA.importKey(private_key_)

    PEMPATH = 'private_key.pem'
    with open(PEMPATH, "r") as f:
        private_key_ = f.read()                                # 获取私钥
    priKeyLogin = private_key_.encode()
    return priKeyTCP,priKeyLogin

priKeyTCP,priKeyLogin = loadPEM()

def decryptPkt_server(encryptedBytes):
    cipher = PKCS1_cipher.new(priKeyTCP)
    encryptedBytes = base64.b64decode(encryptedBytes)
    dataPieces = [encryptedBytes[i:i+256] for i in range(0,len(encryptedBytes),256)]
    decryptedBytes = b''
    for dataPiece in dataPieces:
        decryptedBytes += cipher.decrypt(dataPiece,b'')
    #print(len(encryptedBytes),len(decryptedBytes))
    #print(decryptedBytes)
    dataInDict = json.loads(decryptedBytes)
    return dataInDict

def sendPkt(sock:socket.socket,dataBytes):
    length = len(dataBytes)
    dataWithLenHeader = length.to_bytes(4,'big') + dataBytes
    sock.sendall(dataWithLenHeader)

def recvPkt(sock:socket.socket):
    data = b''
    time_start = 0
    while len(data)<4:
        data += sock.recv(4-len(data))
        if time_start==0:
            time_start = time.time()
        time.sleep(0.001)
        if time.time()-time_start>5:
            print('接收数据超时-1')
            return b''
    length = int.from_bytes(data,'big')
    time_start = time.time()
    if length>1024000:    #超长包，认为是非法链接
        print('数据超长')
        return b''
    data = b''
    while len(data)<length:
        data += sock.recv(length-len(data))
        time.sleep(0.001)
        if time.time()-time_start>5:
            print('接收数据超时-2')
            return b''
    return data




def get_server_list(sock,addr,pkgDict:dict={})->dict:
    responseDict = {
        'stat':1,
        'servers':serverList,
        'info':''
    }
    return responseDict


def check_mac(macAddr):
    return True

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
banIPDict = {
    'ip':[0,datetime.datetime]
}
BAN_monitor_time = datetime.timedelta(minutes=5)
MAX_LOGIN_ERROR = 5
def login_account(sock,addr=('127.0.0.1',1000),pkgDict:dict={})->dict:
    '''{stat:0/1,token:token,info:info}'''
    def cal_token(uid):
        def openssl_private_encrypt(data):
            key = load_pem_private_key(priKeyLogin, None, backend=default_backend())
            backend = default_backend()
            length = backend._lib.EVP_PKEY_size(key._evp_pkey)
            buffer = backend._ffi.new('unsigned char[]', length)
            result = backend._lib.RSA_private_encrypt(
                len(data), data, buffer,
                backend._lib.EVP_PKEY_get1_RSA(key._evp_pkey),
                backend._lib.RSA_PKCS1_PADDING)
            backend.openssl_assert(result == length)
            res = backend._ffi.buffer(buffer)[:]
            #print(res)
            return base64.b64encode(backend._ffi.buffer(buffer)[:]).decode()
        data = '%08x010101010101010101010101010101010101010101010101010101010101010155914510010403030101' % uid
        dataInBytes = bytes.fromhex(data)
        print(f'账号登陆{uid}')
        return openssl_private_encrypt(dataInBytes)
    
    def check_uid():
        sql = 'select uid from accounts where accountname=%s and password=%s'
        res = execute_and_fech('d_taiwan',sql,(accountName,pwdMD5))
        if len(res)==0:
            return -1
        uid = res[0][0]
        return uid
    
    
    host = addr[0]
    macAddr = pkgDict.get('macAddr')
    if not check_mac(macAddr):
        return {'stat':0,'info':'MAC地址被封禁','token':''}
    accountName = pkgDict.get('accountName')
    pwdMD5 = pkgDict.get('pwdMD5')
    server = pkgDict.get('server')
    uid = check_uid()
    if uid==-1:
        
        timeNow = datetime.datetime.now()
        errorList = banIPDict.get(host,[datetime.datetime.now()])
        for errorDateTime in errorList:
            if timeNow-errorDateTime>BAN_monitor_time:
                errorList.remove(errorDateTime)
        errorList.append(timeNow)
        banIPDict[host] = errorList
        if len(errorList)>MAX_LOGIN_ERROR:
            return {'stat':0,'info':'验证错误次数过多，请5分钟后重试','token':''}
        return {'stat':0,'info':f'账号或密码错误({len(errorList)}/5)','token':''}

    token = cal_token(uid)
    banIPDict[host] = []
    return {'stat':1,'info':'','token':token}

DAILY_REGISTER_LIMIT = 10
reg_host_dict = {
    'ip':[datetime.datetime]
}

def register_account(sock,addr=('127.0.0.1',1000),pkgDict:dict={})->dict:
    '''{stat:0/1,info:info}'''
    def register():
        sql = 'select * from accounts where accountname=%s'
        res = execute_and_fech('d_taiwan',sql,(accountName,))
        if len(res)>0:
            return {'stat':0,'info':'账号已存在'}
        sql = 'insert into accounts(accountname,password,qq) values(%s,%s,%s)'
        res = execute_and_commit('d_taiwan',sql,(accountName,pwdMD5,qq))
        sel = 'select uid from accounts where accountname=%s and password=%s'
        res = execute_and_fech('d_taiwan',sel,(accountName,pwdMD5))
        if len(res)==0:
            return {'stat':0,'info':'注册失败，请重试'}
        uid = res[0][0]
        sql = f'insert into d_taiwan.limit_create_character (m_id) VALUES ({uid})'
        res = execute_and_commit('d_taiwan',sql)
        sql = f'insert into d_taiwan.member_info (m_id,user_id) VALUES ({uid},{uid})'
        res = execute_and_commit('d_taiwan',sql)
        sql = f'insert into d_taiwan.member_join_info (m_id) VALUES ({uid})'
        res = execute_and_commit('d_taiwan',sql)
        sql = f'insert into d_taiwan.member_miles (m_id) VALUES ({uid})'
        res = execute_and_commit('d_taiwan',sql)
        sql = f'insert into d_taiwan.member_white_account (m_id) VALUES ({uid})'
        res = execute_and_commit('d_taiwan',sql)
        sql = f'insert into taiwan_login.member_login (m_id) VALUES ({uid})'
        res = execute_and_commit('taiwan_login',sql)
        sql = f'insert into taiwan_billing.cash_cera (account,cera,mod_date,reg_date) VALUES ({uid},{INIT_CERA},NOW(),NOW())'
        res = execute_and_commit('taiwan_billing',sql)
        sql = f'insert into taiwan_billing.cash_cera_point (account,cera_point,mod_date,reg_date) VALUES ({uid},{INIT_CERAPOINT},NOW(),NOW())'
        res = execute_and_commit('taiwan_billing',sql)
        sql = f'insert into taiwan_cain_2nd.member_avatar_coin (m_id) VALUES ({uid})'
        res = execute_and_commit('taiwan_cain_2nd',sql)
        hostRegisterList = reg_host_dict.get(host,[datetime.datetime.now()])
        timeNow = datetime.datetime.now()
        for registerDateTime in hostRegisterList:
            if timeNow-registerDateTime>datetime.timedelta(days=1):
                hostRegisterList.remove(registerDateTime)
        hostRegisterList.append(timeNow)
        reg_host_dict[host] = hostRegisterList
        return {'stat':1,'info':'注册成功'}
    host = addr[0]
    macAddr = pkgDict.get('macAddr')
    if not check_mac(macAddr):
        return {'stat':0,'info':'MAC地址被封禁'}
    hostRegisterList = reg_host_dict.get(host,[datetime.datetime.now()])
    if len(hostRegisterList)>DAILY_REGISTER_LIMIT:
        return {'stat':0,'info':'该IP于24小时内注册次数已达上限'}
    accountName = pkgDict.get('accountName')
    pwdMD5 = pkgDict.get('pwdMD5')
    qq = pkgDict.get('qq')
    return register()





blackList = {}
@inThread
def handle_client_thread(sock:socket.socket,addr):
    
    try:
        for i in range(10):
            try:
                encryptedDataBytes = recvPkt(sock)
            except:
                print('接收数据异常，关闭连接')
                sock.close()
                return False
            if len(encryptedDataBytes)==0:
                sock.close()
            try:
                dataInDict = decryptPkt_server(encryptedDataBytes)
            except:
                #traceback.print_exc()
                print(f'数据解密异常，关闭连接{addr}')
                sock.close()
                return
            print([addr,dataInDict])
            version = dataInDict.get('version')

            if dataInDict.get('cmd')=='login':
                responseDict = login_account(sock,addr,dataInDict)
            elif dataInDict.get('cmd')=='register':
                responseDict = register_account(sock,addr,dataInDict)
            elif dataInDict.get('cmd')=='get_server':
                responseDict = get_server_list(sock,addr,dataInDict)
            else:
                print(f'未知命令{dataInDict.get("cmd")}，关闭连接{addr}')
                sock.close()
                return
            #print(f'发送数据{responseDict}')
            responseInBytes = base64.b64encode(json.dumps(responseDict).encode())
            sendPkt(sock,responseInBytes)
    except Exception as e:
        print(f'数据错误{e}',addr)
        traceback.print_exc()
    sock.close()
    print(f'连接关闭{addr}')
    return True

@inThread
def serverStart():
    S = socket.socket()
    S.bind(SERVER_ADDR)
    S.listen(5)    #未被接受的队列最长为5个
    print('server started.')
    while True:
        sock, addr = S.accept()
        handle_client_thread(sock, addr)
        print(f'client connected.{addr}')



if __name__=='__main__':
    # ctrl_c 
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    logQueue = []
    oldPrint = print
    def log(*text):
        logQueue.append(text)

    def logger():
        import time
        oldPrint('log start')
        logDir = 'pkgLoginlog'
        if not os.path.exists(logDir):
            os.mkdir(logDir)
        while True:
            while len(logQueue)==0:
                time.sleep(0.001)
            text = logQueue.pop(0)
            
            try:
                tm = time.localtime()
                oldPrint(f'[{"%02d" % tm.tm_mon}-{"%02d" % tm.tm_mday} {"%02d" % tm.tm_hour}:{"%02d" % tm.tm_min}:{"%02d" % tm.tm_sec}]',*text)
                LOGFile = f'./pkgLoginlog/{"%04d" % tm.tm_year}-{"%02d" % tm.tm_mon}-{"%02d" % tm.tm_mday}.log'
                
                if len(text)==1:
                    text = text[0]
                text = str(text)
                
                with open(LOGFile,'a+',encoding='utf-8') as f:
                    log_str = f'[{"%02d" % tm.tm_mon}-{"%02d" % tm.tm_mday} {"%02d" % tm.tm_hour}:{"%02d" % tm.tm_min}:{"%02d" % tm.tm_sec}],{text}\n'
                    f.write(log_str)
                    LOGFLG = False
            except Exception as e:
                oldPrint(e)
                pass
    print = log
    t = threading.Thread(target=logger)
    t.setDaemon(True)
    t.start()
    connect_sql()
    serverStart()
    
    while True:
        time.sleep(1)

    

