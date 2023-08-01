import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from Crypto.PublicKey import RSA
import os
import time
import json
import zlib
import pathlib
import shutil
def genPEM(bits=2048):
    key = RSA.generate(bits)                        # 指定位数
    private_key = key.export_key()                  # 私钥
    public_key = key.publickey().export_key()       # 公钥
    return private_key, public_key

defaultToml = '''"服务器地址" = "192.168.200.131"
"角色等级上限" = 90
"一键卖分品级" = 2
"含宠物装备" = 0
"SSS评分开关" = 1
"本地GM开关" = 1
"史诗自动确认开关" = 1
"英雄级开关" = 1
"物品图标开关" = 1
"name2开关" = 0
"品级文本开关" = 1
"连发按键组" = []
"快捷键前置" = "Ctrl"
"无损画质" = 16
"难度命名" = ["普通级", "冒险级", "王者级", "地狱级", "英雄级"]
"品级命名" = ["普通", "高级", "稀有", "神器", "史诗", "勇者", "传说", "神话"]
"简体PVF" = 0
"隐藏功能" = 0

["自动拾取"]
"拾取模式" = 2
"自定义拾取代码组" = [0, 6515]

["自动翻牌"]
"上" = 0
"下" = 0

["史诗闪光"]
"闪光开关" = 1
"闪光代码" = 9413

["补丁信息"]
"补丁名称" = "DOF补丁大合集V7"
"补丁声明" = "本软件永久免费！用途仅限于测试实验、研究学习为目的，请勿用于商业途径及非法运营，严禁将本软件用于与中国现行法律相违背的一切行为！否则，请停止使用，若坚持使用，造成的一切法律责任及所有后果均由使用方承担，与作者无关，特此声明！"
'''

class GatewaymanagerApp:
    def __init__(self, master=None):
        # build ui
        frame1 = ttk.Frame(master)
        frame1.configure(height=200, width=200)
        frame2 = ttk.Frame(frame1)
        frame2.configure(height=200, width=200)
        labelframe1 = ttk.Labelframe(frame2)
        labelframe1.configure(height=200, text='必填项目', width=200)
        label1 = ttk.Label(labelframe1)
        label1.configure(text='游戏服务器IP')
        label1.grid(column=0, row=0)
        self.serverIPE = ttk.Entry(labelframe1)
        self.serverIPE.grid(column=1, row=0, sticky="ew")
        button1 = ttk.Button(labelframe1)
        button1.configure(text='自动填充')
        button1.grid(column=2, row=0, rowspan=2, sticky="n")
        button1.configure(command=self.auto_gen)
        label12 = ttk.Label(labelframe1)
        label12.configure(text='服务器名称')
        label12.grid(column=0, row=1)
        self.serverNameE = ttk.Entry(labelframe1)
        _text_ = '一个服务器'
        self.serverNameE.delete("0", "end")
        self.serverNameE.insert("0", _text_)
        self.serverNameE.grid(column=1, row=1, sticky="ew")
        button2 = ttk.Button(labelframe1)
        button2.configure(text='生成登陆器')
        button2.grid(column=2, row=1, rowspan=2, sticky="s")
        button2.configure(command=self.gen_launcher)
        label13 = ttk.Label(labelframe1)
        label13.configure(text='启动器名称')
        label13.grid(column=0, row=2)
        self.launcherNameE = ttk.Entry(labelframe1)
        _text_ = '默认启动器'
        self.launcherNameE.delete("0", "end")
        self.launcherNameE.insert("0", _text_)
        self.launcherNameE.grid(column=1, row=2, sticky="ew")
        labelframe1.pack(fill="x", side="top")
        labelframe2 = ttk.Labelframe(frame2)
        labelframe2.configure(height=200, text='网关配置', width=200)
        label2 = ttk.Label(labelframe2)
        label2.configure(text=' 网关IP ')
        label2.grid(column=0, row=0)
        self.gatewayIPE = ttk.Entry(labelframe2)
        self.gatewayIPE.configure(width=15)
        self.gatewayIPE.grid(column=1, row=0, sticky="ew")
        label10 = ttk.Label(labelframe2)
        label10.configure(text='注册赠送点券数')
        label10.grid(column=0, row=1)
        self.initCeraE = ttk.Entry(labelframe2)
        _text_ = '100000'
        self.initCeraE.delete("0", "end")
        self.initCeraE.insert("0", _text_)
        self.initCeraE.grid(column=1, columnspan=3, row=1, sticky="ew")
        label11 = ttk.Label(labelframe2)
        label11.configure(text='注册赠送代币数')
        label11.grid(column=0, row=2)
        self.initCeraPointE = ttk.Entry(labelframe2)
        _text_ = '100000'
        self.initCeraPointE.delete("0", "end")
        self.initCeraPointE.insert("0", _text_)
        self.initCeraPointE.grid(column=1, columnspan=3, row=2, sticky="ew")
        label14 = ttk.Label(labelframe2)
        label14.configure(text=' 网关端口 ')
        label14.grid(column=2, row=0)
        self.gatewayPortE = ttk.Entry(labelframe2)
        self.gatewayPortE.configure(width=5)
        _text_ = '10086'
        self.gatewayPortE.delete("0", "end")
        self.gatewayPortE.insert("0", _text_)
        self.gatewayPortE.grid(column=3, row=0, sticky="ew")
        labelframe2.pack(fill="x", side="top")
        labelframe6 = ttk.Labelframe(frame2)
        labelframe6.configure(height=200, text='数据库配置', width=200)
        label15 = ttk.Label(labelframe6)
        label15.configure(text='数据库IP')
        label15.grid(column=0, row=0)
        self.dbIPE = ttk.Entry(labelframe6)
        _text_ = '127.0.0.1'
        self.dbIPE.delete("0", "end")
        self.dbIPE.insert("0", _text_)
        self.dbIPE.grid(column=1, row=0, sticky="ew")
        label16 = ttk.Label(labelframe6)
        label16.configure(text='数据库密码')
        label16.grid(column=0, row=2)
        self.dbPwdE = ttk.Entry(labelframe6)
        _text_ = 'uu5!^jg'
        self.dbPwdE.delete("0", "end")
        self.dbPwdE.insert("0", _text_)
        self.dbPwdE.grid(column=1, row=2, sticky="ew")
        label17 = ttk.Label(labelframe6)
        label17.configure(text='数据库用户')
        label17.grid(column=0, row=4)
        self.dbUserE = ttk.Entry(labelframe6)
        _text_ = 'game'
        self.dbUserE.delete("0", "end")
        self.dbUserE.insert("0", _text_)
        self.dbUserE.grid(column=1, row=4, sticky="ew")
        label18 = ttk.Label(labelframe6)
        label18.configure(text='数据库端口')
        label18.grid(column=0, row=1)
        self.dbPortE = ttk.Entry(labelframe6)
        _text_ = '3306'
        self.dbPortE.delete("0", "end")
        self.dbPortE.insert("0", _text_)
        self.dbPortE.grid(column=1, row=1, sticky="ew")
        labelframe6.pack(fill="x", side="top")
        labelframe6.columnconfigure(1, weight=1)
        labelframe5 = ttk.Labelframe(frame2)
        labelframe5.configure(height=200, text='大合集exe配置', width=200)
        self.tomlE = tk.Text(labelframe5)
        self.tomlE.configure(height=10, width=30)
        self.tomlE.pack(expand="true", fill="both", side="top")
        labelframe5.pack(expand="true", fill="both", side="top")
        frame2.pack(fill="both", side="left")
        frame3 = ttk.Frame(frame1)
        frame3.configure(height=200, width=200)
        labelframe3 = ttk.Labelframe(frame3)
        labelframe3.configure(height=200, text='网关通信密钥', width=200)
        label3 = ttk.Label(labelframe3)
        label3.configure(text=' 私钥 ')
        label3.grid(column=0, row=0)
        self.gatewayPrivateKeyE = tk.Text(labelframe3)
        self.gatewayPrivateKeyE.configure(height=10, width=70)
        self.gatewayPrivateKeyE.grid(column=1, row=0)
        label4 = ttk.Label(labelframe3)
        label4.configure(text=' 公钥 ')
        label4.grid(column=0, row=2)
        self.gatewayPublicKeyE = tk.Text(labelframe3)
        self.gatewayPublicKeyE.configure(height=5, width=50)
        self.gatewayPublicKeyE.grid(column=1, row=2, sticky="nsew")
        labelframe3.pack(side="top")
        labelframe4 = ttk.Labelframe(frame3)
        labelframe4.configure(height=200, text='服务端通信密钥', width=200)
        label7 = ttk.Label(labelframe4)
        label7.configure(text=' 私钥 ')
        label7.grid(column=0, row=0)
        self.gamePrivateKeyE = tk.Text(labelframe4)
        self.gamePrivateKeyE.configure(height=10, width=50)
        self.gamePrivateKeyE.grid(column=1, row=0, sticky="nsew")
        label8 = ttk.Label(labelframe4)
        label8.configure(text=' 公钥 ')
        label8.grid(column=0, row=2)
        self.gamePublicKeyE = tk.Text(labelframe4)
        self.gamePublicKeyE.configure(height=5, width=50)
        self.gamePublicKeyE.grid(column=1, row=2, sticky="nsew")
        labelframe4.pack(fill="both", side="top")
        labelframe4.columnconfigure(1, weight=1)
        frame3.pack(fill="both", side="right")
        frame1.pack(side="top")

        # Main widget
        self.mainwindow = frame1

    def run(self):
        self.mainwindow.mainloop()

    def auto_gen(self):
        ip = self.serverIPE.get()
        tomlConfig = defaultToml.replace('192.168.200.131',ip)
        self.tomlE.delete('0.0',tk.END)
        self.tomlE.insert('0.0',tomlConfig)
        self.gatewayIPE.delete(0,tk.END)
        self.gatewayIPE.insert(0,ip)
        gwPriKey, gwPubKey = genPEM(2048)
        gamePriKey,gamePubKey = genPEM(2048)
        self.gatewayPrivateKeyE.delete('0.0',tk.END)
        self.gatewayPrivateKeyE.insert('0.0',gwPriKey)
        self.gatewayPublicKeyE.delete('0.0',tk.END)
        self.gatewayPublicKeyE.insert('0.0',gwPubKey)
        self.gamePrivateKeyE.delete('0.0',tk.END)
        self.gamePrivateKeyE.insert('0.0',gamePriKey)
        self.gamePublicKeyE.delete('0.0',tk.END)
        self.gamePublicKeyE.insert('0.0',gamePubKey)
        
        pass

    def gen_launcher(self):
        outDir = '生成配置'
        if os.path.exists(outDir) == False:
            os.mkdir(outDir)
        timeNow = time.strftime("%Y%m%d%H%M%S", time.localtime())
        gatewayDir = os.path.join(outDir,'网关'+timeNow)        
        #拷贝文件
        gwDris = ['gateway_bin']
        for dri in gwDris:
            shutil.copytree(dri,gatewayDir)

        gameDir = os.path.join(outDir,'登陆器'+timeNow)
        clientDirs = ['client_exe']
        for dri in clientDirs:
            shutil.copytree(dri,gameDir)

        # 保存4个密钥
        gwPriKey = self.gatewayPrivateKeyE.get('0.0',tk.END)
        gwPubKey = self.gatewayPublicKeyE.get('0.0',tk.END)
        gamePriKey = self.gamePrivateKeyE.get('0.0',tk.END)
        gamePubKey = self.gamePublicKeyE.get('0.0',tk.END)
        with open(os.path.join(gatewayDir,'pkglogin_private_tcp.pem'),'w') as f:
            f.write(gwPriKey)
        with open(os.path.join(gatewayDir,'pkglogin_public_tcp.pem'),'w') as f:
            f.write(gwPubKey)
        with open(os.path.join(gatewayDir,'privatekey.pem'),'w') as f:
            f.write(gamePriKey)
        with open(os.path.join(gatewayDir,'publickey.pem'),'w') as f:
            f.write(gamePubKey)
        
        # 保存登陆器配置
        def save_client_dll(loginInfo={}):
            '''loginInfo:{ip port public_key}'''
            dllData = json.dumps(loginInfo).encode()
            dllData = zlib.compress(dllData)
            #os.mkdir(os.path.join(gameDir,'pkglogin'))
            dllPath = os.path.join(gameDir,'pkglogin\pkglogin.dll')
            with open(dllPath,'wb') as f:
                f.write(dllData)
            return dllPath
        gatewayIP = self.gatewayIPE.get()
        gatewayPort = int(self.gatewayPortE.get())
        gatewayPublicKey = gwPubKey
        launcherName = self.launcherNameE.get()
        loginInfo = {
            'ip':gatewayIP,
            'port':gatewayPort,
            'public_key':gatewayPublicKey,
            'launcherName':launcherName,
        }
        dllPath = save_client_dll(loginInfo)
        # 保存网关配置
        def save_gw_json(gwInfo={}):
            gwPath = os.path.join(gatewayDir,'gateway.json')
            json.dump(gwInfo,open(gwPath,'w',encoding='utf-8'),indent=4,ensure_ascii=False)
            return gwPath
        toml = self.tomlE.get('0.0',tk.END)
        serverName = self.serverNameE.get()
        initCera = int(self.initCeraE.get())
        initCeraPoint = int(self.initCeraPointE.get())
        dbIP = self.dbIPE.get()
        dbPort = int(self.dbPortE.get())
        dbUser = self.dbUserE.get()
        dbPwd = self.dbPwdE.get()
        
        gwInfo = {
            'SERVER_IP':(gatewayIP,gatewayPort),
            'INIT_CERA':initCera,
            'INIT_CERAPOINT':initCeraPoint,
            'DB_IP':dbIP,
            'DB_PORT':dbPort,
            'DB_USER':dbUser,
            'DB_PWD':dbPwd,
            'SERVER_LIST':{'name':serverName,'toml':toml},
        }
        gwPath = save_gw_json(gwInfo)
        absPath = pathlib.Path('.').absolute().joinpath(outDir)

        messagebox.showinfo('提示',f'生成成功！\n生成配置位于{absPath}目录下')
        # open folder
        os.startfile(absPath)


        


if __name__ == "__main__":
    root = tk.Tk()
    root.title('网关登陆器生成器')
    app = GatewaymanagerApp(root)
    app.run()

