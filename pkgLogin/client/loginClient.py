import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import time
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
import base64
import json
import socket
import hashlib
import uuid
import threading
import pathlib
import subprocess
import zlib
VERSION = 'alpha 0.0.1'

remoteAddr = '192.168.200.131'
public_key_str = '''-----BEGIN RSA PUBLIC KEY-----

-----END RSA PUBLIC KEY-----'''


import os
import sys
import os

oldPrint = print
logFunc = [oldPrint]
def print(*args,**kw):
    logFunc[-1](*args,**kw)
logFunc.append(lambda *args:...)

tmpDir = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
abs_pth = os.path.abspath(sys.argv[0])
workDir = pathlib.Path(os.path.dirname(abs_pth))
launcherName = '背包测试登录器'
print(123,workDir)
dllPath = workDir.joinpath('pkglogin.dll')
if dllPath.exists():
    with open(dllPath,'rb') as f:
        dllData = f.read()
    dllData = zlib.decompress(dllData)
    loginInfo = json.loads(dllData)
    remoteAddr = (loginInfo['ip'],int(loginInfo['port']))
    public_key_str = loginInfo['public_key']
    launcherName = loginInfo['launcherName']
print(remoteAddr)


    
iconPath = 'ico.ico'
iconPath = tmpDir.joinpath(iconPath)
public_key = RSA.importKey(public_key_str)

def encryptPkt_client(dataInDict,public_key):
    dataInBytes = json.dumps(dataInDict).encode(errors='replace')
    dataPieces = [dataInBytes[i:i+100] for i in range(0,len(dataInBytes),100)]
    encryptedBytes = b''
    cipher = PKCS1_cipher.new(public_key)
    for dataPiece in dataPieces:
        tmp = cipher.encrypt(dataPiece)
        encryptedBytes += tmp
        #print(len(tmp))
    return base64.b64encode(encryptedBytes)


sockDict = {}
def send_new(addr,dataBytes,reConnect=True):
    def sendPkt(sock:socket.socket,dataBytes):
        length = len(dataBytes)
        dataWithLenHeader = length.to_bytes(4,'big') + dataBytes
        sock.sendall(dataWithLenHeader)
    try:
        sock = sockDict.get(addr)
        if sock is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(addr)
            sockDict[addr] = sock
        print(dataBytes)
        sendPkt(sock,dataBytes)
    except:
        if reConnect:
            sockDict[addr] = None
            send_new(addr,dataBytes,False)
        

def recv_new(addr):
    def recvPkt(sock:socket.socket):
        data = b''
        while len(data)<4:
            data += sock.recv(4-len(data))
        length = int.from_bytes(data,'big')
        if length>12134:    #超长包，认为是非法链接
            #print(f'超长包{length}')
            return b''
        data = b''
        while len(data)<length:
            data += sock.recv(length-len(data))
        return data
    sock = sockDict.get(addr)
    if sock is None:
        print('套接字为空')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(addr)
        sockDict[addr] = sock
        return b''
    return recvPkt(sock)

def inThread(func):
    def inner(*args,**kw):
        t = threading.Thread(target=lambda:func(*args,**kw))
        t.setDaemon(True)
        t.start()
        return t
    return inner

def startDNF(token='',toml=''):
    tomlName = 'DNF.toml'
    toml = toml.replace('\r','')
    workDirPath = pathlib.Path(workDir)
    tomlPath = workDirPath.joinpath(tomlName)
    oldContent = ''
    if tomlPath.exists():   #记录原始数据
        with open(tomlPath,'r',encoding='utf-8') as f:
            oldContent = f.read()
    with open(tomlPath,'w',encoding='utf-8') as f: #写入新数据
        f.write(toml)
    executeFileName = DNF_EXE
    launchCmd = f'"{workDirPath.joinpath(executeFileName)}"  {token}'
    subprocess.Popen(launchCmd,shell=True, cwd=workDirPath)
    time.sleep(5)
    with open(tomlPath,'w',encoding='utf-8') as f:  #恢复原始数据
        f.write(oldContent)
    return True
    
CFG_PATH = 'pkgLauncher.json'

class LoginuiApp:
    def __init__(self, master:tk.Tk=None):
        # build ui
        frame1 = ttk.Frame(master)
        frame1.configure(height=200, width=200)
        self.imgFrame = ttk.Frame(frame1)
        self.imgFrame.configure(height=200, width=200)
        self.imgLabel = ttk.Label(self.imgFrame)
        self.imgLabel.configure(text=' ')
        self.imgLabel.pack(side="top")
        self.imgFrame.pack(side="left")
        frame3 = ttk.Frame(frame1)
        frame3.configure(height=200, width=200)
        frame4 = ttk.Frame(frame3)
        frame4.configure(height=200, width=200)
        label2 = ttk.Label(frame4)
        label2.configure(text='网关状态：')
        label2.pack(side="left")
        self.gateWayStatLabel = ttk.Label(frame4)
        self.gateWayStatLabel.configure(text='测试中')
        self.gateWayStatLabel.pack(side="right")
        frame4.pack(side="top")
        frame5 = ttk.Frame(frame3)
        frame5.configure(height=200, width=200)
        label4 = ttk.Label(frame5)
        label4.configure(text=' 账号 ')
        label4.grid(column=0, row=0)
        label5 = ttk.Label(frame5)
        label5.configure(text=' 密码 ')
        label5.grid(column=0, row=1)
        label6 = ttk.Label(frame5)
        label6.configure(text='服务器')
        label6.grid(column=0, row=2)
        self.userNameE = ttk.Combobox(frame5)
        self.userNameE.grid(column=1, row=0, sticky="ew")
        self.pwdE = ttk.Combobox(frame5)
        self.pwdE.grid(column=1, row=1, sticky="ew")
        self.serverE = ttk.Combobox(frame5)
        self.serverE.configure(state="readonly")
        self.serverE.grid(column=1, row=2, sticky="ew")
        frame5.pack(fill="both", side="top")
        self.loginBtn = ttk.Button(frame3)
        self.loginBtn.configure(text='登录账号')
        self.loginBtn.pack(fill="x", side="top")
        self.loginBtn.configure(command=self.login_in)
        button2 = ttk.Button(frame3)
        button2.configure(text='注册账号')
        button2.pack(fill="x", side="top")
        button2.configure(command=self.register_account)
        frame3.pack(side="top")
        frame1.pack(side="top")


        # Main widget
        self.mainwindow = frame1
        self.master = master

        self._build()

    def _build(self):
        imgPath = iconPath
        img = Image.open(imgPath)
        #img = img.resize((200, 200), Image.ANTIALIAS)
        self.img = ImageTk.PhotoImage(img)
        self.imgLabel.configure(image=self.img)
        self.serverE.set('---')
        self.pwdE.config(show='*')
        self.load_cfg()
        self.get_server()

    def run(self):
        self.mainwindow.mainloop()

    def select_account(self,event):
        accountName = self.userNameE.get()
        pwd = self.cfgDict['historyAccounts'][accountName]
        self.pwdE.set(pwd)

    @inThread
    def load_cfg(self):
        try:
            with open(CFG_PATH,'r',encoding='utf-8') as f:
                cfgDict = json.load(f)
        except:
            cfgDict = {}
        self.cfgDict = cfgDict
        accountName = cfgDict.get('accountName','')
        pwd = cfgDict.get('pwd','')
        self.userNameE.set(accountName)
        self.pwdE.set(pwd)
        historyAccountsDict = cfgDict.get('historyAccounts',{})
        historyAccounts = list(historyAccountsDict.keys())
        self.userNameE['values'] = historyAccounts


    @inThread
    def save_cfg(self):
        with open(CFG_PATH,'w',encoding='utf-8') as f:
            json.dump(self.cfgDict,f,ensure_ascii=False,indent=4)

    @inThread
    def get_server(self):
        dataInDict = {'cmd':'get_server'}
        mac = uuid.getnode()
        mac_hex = hex(mac)[2:].zfill(12) #转换成16进制
        mac_addr = ':'.join(mac_hex[i:i+2] for i in range(0, 12, 2)) #添加:符号
        dataInDict['macAddr'] = mac_addr
        encryptedData = encryptPkt_client(dataInDict,public_key)
        send_new(remoteAddr,encryptedData)
        responseData_b64 = recv_new(remoteAddr)
        responseDict:dict = json.loads(base64.b64decode(responseData_b64))
        if responseDict.get('stat')==0:
            messagebox.showerror('获取服务器列表失败',responseDict.get('info',''))
            self.gateWayStatLabel.config(text='连接失败',foreground='red')
            return
        self.serverList = responseDict.get('servers',[])
        serverValues = []
        for i,server in enumerate(self.serverList):
            severName = server.get('name','')
            serverValues.append(f'[{i}]{severName}')
        self.serverE['values'] = serverValues
        self.serverE.set(serverValues[0])

        self.gateWayStatLabel.config(text='已连接',foreground='green')
        return
        


    @inThread
    def login_in(self):
        self.loginBtn.config(state='disabled')
        dataInDict = {'cmd':'login','macAddr':'','accountName':'','pwdMD5':'','server':'','version':VERSION}
        mac = uuid.getnode()
        mac_hex = hex(mac)[2:].zfill(12) #转换成16进制
        mac_addr = ':'.join(mac_hex[i:i+2] for i in range(0, 12, 2)) #添加:符号
        accountName = self.userNameE.get()
        pwd = self.pwdE.get()
        pwdMD5 = hashlib.md5(pwd.encode()).hexdigest()
        server = int(self.serverE.get().split(']')[0][1:])
        dataInDict['macAddr'] = mac_addr
        dataInDict['accountName'] = accountName
        dataInDict['pwdMD5'] = pwdMD5
        dataInDict['server'] = server
        encryptedData = encryptPkt_client(dataInDict,public_key)
        send_new(remoteAddr,encryptedData)
        responseData_b64 = recv_new(remoteAddr)
        responseDict:dict = json.loads(base64.b64decode(responseData_b64))
        
        if responseDict.get('stat')==1:
            token = responseDict.get('token')
            if token is None:
                messagebox.showerror('登录失败','服务器返回数据异常')
                return
            if responseDict.get('info','')!='':
                messagebox.showinfo('提示信息',responseDict.get('info'))
            toml = self.serverList[server].get('toml','')
            self.cfgDict['accountName'] = accountName
            self.cfgDict['pwd'] = pwd
            historyAccountsDict = self.cfgDict.get('historyAccounts',{})
            historyAccountsDict[accountName] = pwd
            self.cfgDict['historyAccounts'] = historyAccountsDict
            self.save_cfg()
            startDNF(token,toml)
            self.master.destroy()
            exit()
            quit()
            return
        else:
            messagebox.showerror('登录失败',responseDict.get('info',''))
            self.loginBtn.config(state='normal')
            return
        

    def register_account(self):
        try:
            self.regWin.focus_force()
            return
        except:
            pass
        self.regWin = tk.Toplevel(self.mainwindow)
        self.regWin.title('注册账号')
        self.regWin.iconbitmap(iconPath)
        self.loginFrame = LoginuiRegWidget(self.regWin)
        self.regWin.protocol("WM_DELETE_WINDOW", self.regWinClose)
        self.regWin.mainloop()
    
    def regWinClose(self):
        self.regWin.destroy()

class LoginuiRegWidget(ttk.Frame):
    def __init__(self, master=None, **kw):
        super(LoginuiRegWidget, self).__init__(master, **kw)
        label1 = ttk.Label(self)
        label1.configure(text='用户名')
        label1.grid(column=0, padx=20, row=0)
        entry1 = ttk.Entry(self)
        entry1.grid(column=1, row=0)
        label2 = ttk.Label(self)
        label2.configure(text='密码')
        label2.grid(column=0, row=1)
        entry2 = ttk.Entry(self)
        entry2.grid(column=1, row=1)
        label3 = ttk.Label(self)
        label3.configure(text='QQ')
        label3.grid(column=0, row=2)
        entry3 = ttk.Entry(self)
        entry3.grid(column=1, row=2)
        button1 = ttk.Button(self)
        button1.configure(text='注册账号')
        button1.grid(column=0, columnspan=2, row=3, sticky="ew")
        button1.configure(command=self.commit_register)
        self.configure(height=200, width=200)
        self.pack(side="top")

        self.master = master

    def commit_register(self):
        dateInDct = {'cmd':'register','accountName':'','pwdMD5':'','qq':''}
        accountName:str = self.children['!entry'].get()
        pwd = self.children['!entry2'].get()
        qq = self.children['!entry3'].get()
        pwdMD5 = hashlib.md5(pwd.encode()).hexdigest()
        # check if accountName use ascii char
        if not accountName.isascii():
            messagebox.showerror('注册失败','用户名只能使用英文和数字')
            self.master.focus_force()
            return
        if len(accountName)<4 or len(accountName)>16:
            messagebox.showerror('注册失败','用户名长度必须在4-16个字符之间')
            self.master.focus_force()
            return
        if len(pwd)<6 or len(pwd)>16:
            messagebox.showerror('注册失败','密码长度必须在6-16个字符之间')
            self.master.focus_force()
            return
        
        dateInDct['accountName'] = accountName
        dateInDct['pwdMD5'] = pwdMD5
        dateInDct['qq'] = qq
        encryptedData = encryptPkt_client(dateInDct,public_key)
        send_new(remoteAddr,encryptedData)
        responseData_b64 = recv_new(remoteAddr)
        responseDict:dict = json.loads(base64.b64decode(responseData_b64))
        if responseDict.get('stat')==1:
            messagebox.showinfo('注册成功',responseDict.get('info',''))
            app.userNameE.set(accountName)
            app.pwdE.set(pwd)
            self.master.destroy()
        else:
            messagebox.showerror('注册失败',responseDict.get('info',''))
            return


if __name__ == "__main__":
    root = tk.Tk()
    root.title(launcherName)
    root.iconbitmap(iconPath)
    app = LoginuiApp(root)
    root.update()
    onlineSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    filesInDir = [i.name for i in workDir.iterdir() if i.is_file()]
    filesInParentDir = [i.name for i in workDir.parent.iterdir() if i.is_file()]
    if 'DNF.exe' in filesInDir:
        DNF_EXE = 'DNF.exe'
    elif 'dnf.exe' in filesInDir:
        DNF_EXE = 'dnf.exe'
    elif 'DNF.exe' in filesInParentDir:
        DNF_EXE = 'DNF.exe'
        workDir = workDir.parent
    elif 'dnf.exe' in filesInParentDir:
        DNF_EXE = 'dnf.exe'
        workDir = workDir.parent
    else:
        messagebox.showerror('启动失败','请将程序放置在DNF目录下')
    app.run()

