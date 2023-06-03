import cacheManager as cacheM 
import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter import ttk,messagebox
import threading, time
from toolTip import CreateOnceToolTip,CreateToolTip
from pathlib import Path
import paramiko
import os

WIDTH,HEIGHT = cacheM.config['SIZE']
def configFrame(frame:tk.Frame,state='disable'):
    for widget in frame.children.values():
        if type(widget) in [tk.Frame,tk.LabelFrame,ttk.LabelFrame]:
            configFrame(widget,state)
        else:
            try:
                widget.config(state=state)
            except:
                continue

oldPrint = print
logFunc = [oldPrint]
def print(*args,**kw):
    logFunc[-1](*args,**kw)

class SSHServerProtocol:
    def __init__(self,app,ip,port,user,pwd='',keyPath=''):
        self.master = app
        self.app = app
        self.ip = ip
        self.port = port
        self.user = user
        self.pwd = pwd
        self.keyPath = keyPath
        self.connectingFlg = False
        self.connectedFlg = False
        self.startingFlg = False
        self.ssh = paramiko.SSHClient
        self.connect()

    def connect(self):
        def inner():
            if self.connectedFlg:
                try:
                    self.ssh.close()
                    self.transPort.close()
                except:
                    pass
            ip = self.ip
            port = int(self.port)
            user = self.user
            self.connectingFlg = True
            if self.keyPath!='':
                if os.path.exists(self.keyPath):
                    try:
                        private_key  = paramiko.RSAKey.from_private_key_file(self.keyPath)
                    except Exception as e:
                        messagebox.showerror('错误',f'密钥文件读取错误{e}')
                        return False
                    try:
                        ssh.connect(ip, username=user, port=port, pkey=private_key,timeout=3)
                        self.transPort = paramiko.Transport((ip,port))
                        self.transPort.connect(username=user, pkey=private_key)
                    except Exception as e:
                        print(f'SSH密钥连接失败 {e}')
                        self.connectedFlg = False
                        self.connectingFlg = False
                        return False
                    cacheM.config['SERVER_PWD'] = ''
                else:
                    messagebox.showerror('错误',f'密钥文件[{self.keyPath}]不存在')
                    return False
            else:
                pwd = self.pwd
                try:
                    ssh.connect(ip, username=user, port=port, password=pwd,timeout=3)
                    self.transPort = paramiko.Transport((ip,port))
                    self.transPort.connect(username=user, password=pwd)
                    
                except Exception as e:
                    print(f'SSH连接失败 {e}')
                    self.connectedFlg = False
                    self.connectingFlg = False
                    return False
                cacheM.config['SERVER_PWD'] = pwd
            cacheM.config['SERVER_IP'] = ip
            cacheM.config['SERVER_PORT'] = port
            cacheM.config['SERVER_USER'] = user
            cacheM.config['SERVER_CONFIGS'][ip] = {'port':port,'pwd':pwd,'user':user,'keyPath':self.keyPath}
            cacheM.save_config()
            self.connectedFlg = True
            print('服务器已连接！')
            self.connectingFlg = False

        self.connectingFlg = False
        self.connectedFlg = False
        self.ssh = paramiko.SSHClient()
        ssh = self.ssh
        self.transPort = paramiko.Transport
        # 允许连接不在know_hosts文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        inner()  

    def run_file(self,fileName):
        def inner():
            ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(f'sh "/root/{fileName}"')
            while True:
                res = ssh_stdout.readline()
                if res == '':
                    break
                time.sleep(0.001)
                print(res)
            print(f'{fileName}执行完毕')
        t = threading.Thread(target=inner)
        t.setDaemon(True)
        t.start()

    def run_cmd(self,cmd='ls',endStr=None):
        def inner():
            ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd)
            t = 0
            while True:
                try:
                    res = ssh_stdout.readline()
                    if res.replace('\n','') == '':
                        t += 1
                        if t==10: break
                    else:
                        t = 0
                        if endStr is not None and endStr in res:
                            break
                        print(res.replace('\n',''))
                    time.sleep(0.02)
                except:
                    break
            #self.title(f'指令执行完毕')
            print(f'指令执行完毕')
            #time.sleep(60)

        t = threading.Thread(target=inner)
        t.setDaemon(True)
        t.start()
        return t

    def run_cmd2(self,cmd='ls'):
        def inner():
            chan = self.ssh.invoke_shell()
            chan.send(cmd + '\n')
            buff = ''
            while not buff.endswith('#'):
                resp = chan.recv(1024)
                buff += resp.decode('utf-8',errors='replace')
                print(resp)

        t = threading.Thread(target=inner)
        t.setDaemon(True)
        t.start()
        return t
    
    def uploadFile(self):
        def inner():
            def printTotals(transferred, toBeTransferred):
                nonlocal time_now
                if time.time() - time_now>1:
                    print("Transferred: {0}\tOut of: {1}".format(transferred, toBeTransferred))
                    print("%.3fM/%.3fM" % (transferred/1e6, toBeTransferred/1e6))
                    time_now += 1

            pvfPath = askopenfilename(filetypes=[('DNF Script.pvf file','*.pvf')])                
            if pvfPath=='' or not Path(pvfPath).exists():
                print('文件错误')
                return False
            print(pvfPath)
            sftp = paramiko.SFTPClient.from_transport(self.transPort)
            remote_path = r'/home/neople/game/Script.pvf'
            cmd = r'ls /home/neople/game/'
            ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd)
            res = ssh_stdout.readlines()
            #print(res)
            if len(res)<5:
                print('目标文件夹异常')
                return False
            time_now = time.time()
            sftp.put(pvfPath,remote_path,callback=printTotals)
            print('上传完成！')
            upPatch = messagebox.askokcancel('上传完成，是否上传等级补丁？')
            if upPatch:
                remote_path = r'/home/neople/game/df_game_r'
                patchPath = askopenfilename()    
                if patchPath=='':
                    print('补丁文件错误')
                    return False
                sftp.put(patchPath,remote_path,callback=printTotals)
        t = threading.Thread(target=inner)
        t.start()

    def lsDir(self,dirPath='/'):
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(f"ls {dirPath}")
        files = [item.strip() for item in ssh_stdout.readlines()]
        return files

    def downloadFile(self,filePath='',targetPath='',progressBarPos=[200,200],progressBarMaster=None):
        def showProgress(transferred, toBeTransferred):
            #print(transferred,toBeTransferred)
            nonlocal time_now
            if time.time() - time_now>1:
                progressBar['maximum'] = toBeTransferred
                # 进度值初始值
                progressBar['value'] = transferred
                progressBar.update()
                time_now += 0.1

        # 使用paramiko下载文件到本机
        if progressBarMaster is None:
            progressBarMaster = self.master
        progressWin = tk.Toplevel(progressBarMaster)
        progressWin.geometry(f"+{progressBarPos[0]}+{progressBarPos[1]}")
        progressWin.overrideredirect(True)
        progressWin.wm_attributes('-topmost', 1)
        progressBar = ttk.Progressbar(progressWin)
        progressBar.pack()
        time_now = time.time()
        try:
            sftp = paramiko.SFTPClient.from_transport(self.transPort)
            sftp.get(filePath, targetPath,callback=showProgress)
        except:
            progressWin.destroy()
            return False
        progressWin.destroy()
        return True
    
    def run_server(self):
        def inner():
            if self.startingFlg:
                print('服务器正在启动中！请点击停止服务器')
                return False
            self.startingFlg = True
            ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command("sh /root/run")
            print('DNF服务器启动中...')
            while True:
                res = ssh_stdout.readline()
                if res == '':
                    break
                if 'Connect To Guild Server' in str(res):
                    print('服务器启动完成')
                    break
                if 'success' in str(res).lower() or 'error' in str(res).lower() or 'fail' in str(res).lower():
                    print(str(res).strip())
            self.startingFlg = False
            
        t = threading.Thread(target=inner)
        t.setDaemon(True)
        t.start()

    def stop_server(self):
        def inner():
            self.startingFlg = False
            print('指令执行中...')
            ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command("sh /root/stop")
            ssh_stdout.readlines()
            ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command("sh /root/stop")
            ssh_stdout.readlines()
            print('服务器已停止')
        t = threading.Thread(target=inner)
        t.setDaemon(True)
        t.start()

    def restart_channel(self):
        self.run_file('run1')

        
    
    
class ServerCtrlFrame(tk.Frame):
    def __init__(self,tabView,tabName='服务器',titlefunc=lambda x:...,autoConnect=True,*args,**kw):
        def connect(show=True,key=False):
            def inner():
                if self.connectedFlg:
                    try:
                        ssh.close()
                        self.transPort.close()
                    except:
                        pass
                ip = ipE.get()
                port = int(portE.get())
                user = userE.get()
                self.connectingFlg = True
                if key:
                    keyPath = askopenfilename(filetypes=[('密钥文件','*.pub'),('所有文件','*.*')])
                    if not keyPath:
                        return False
                    
                    try:
                        private_key  = paramiko.RSAKey.from_private_key_file(keyPath)
                    except Exception as e:
                        messagebox.showerror('错误',f'密钥文件错误{e}')
                        return False
                    try:
                        ssh.connect(ip, username=user, port=port, pkey=private_key,timeout=3)
                        self.transPort = paramiko.Transport((ip,port))
                        self.transPort.connect(username=user, pkey=private_key)
                    except Exception as e:
                        if show:
                            print(f'连接失败 {e}')
                            self.title(f'连接失败 {e}')
                        self.connectedFlg = False
                        self.connectingFlg = False
                        return False
                    cacheM.config['SERVER_PWD'] = ''
                else:
                    pwd = pwdE.get()
                    try:
                        ssh.connect(ip, username=user, port=port, password=pwd,timeout=3)
                        self.transPort = paramiko.Transport((ip,port))
                        self.transPort.connect(username=user, password=pwd)
                        
                    except Exception as e:
                        if show:
                            print(f'连接失败 {e}')
                            self.title(f'连接失败 {e}')
                        self.connectedFlg = False
                        self.connectingFlg = False
                        return False
                    cacheM.config['SERVER_PWD'] = pwd
                cacheM.config['SERVER_IP'] = ip
                cacheM.config['SERVER_PORT'] = port
                cacheM.config['SERVER_USER'] = user
                cacheM.config['SERVER_CONFIGS'][ip] = {'port':port,'pwd':pwd,'user':user}
                cacheM.save_config()
                configFrame(serverFuncFrame,'normal')
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls /root")
                files = [item.strip() for item in ssh_stdout.readlines()]
                for fileSelE in fileSelEList:
                    fileSelE.config(values=files)
                self.connectedFlg = True
                self.ip = ip
                self.title('服务器已连接！')
                self.connectingFlg = False
            t = threading.Thread(target = inner)
            t.setDaemon(True)
            t.start()        
        def run_server():
            def inner():
                nonlocal startingFlg
                if startingFlg:
                    self.title('服务器正在启动中！请点击停止服务器')
                    return False
                startingFlg = True
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("sh /root/run")
                self.title('DNF服务器启动中...')
                while True:
                    res = ssh_stdout.readline()
                    print(res)
                    if res == '':
                        break
                    if 'Connect To Guild Server' in str(res):
                        self.title('服务器启动完成')
                        break
                    if 'success' in str(res).lower() or 'error' in str(res).lower():
                        self.title(str(res).strip())
                startingFlg = False
                
            t = threading.Thread(target=inner)
            t.setDaemon(True)
            t.start()

        def stop_server():
            def inner():
                nonlocal startingFlg
                startingFlg = False
                self.title('指令执行中...')
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("sh /root/stop")
                ssh_stdout.readlines()
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("sh /root/stop")
                ssh_stdout.readlines()
                print('服务器已停止')
                self.title('服务器已停止')
            t = threading.Thread(target=inner)
            t.setDaemon(True)
            t.start()

        def restart_channel():
            run_file('run1')

        def run_file(fileName):
            def inner():
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(f'sh "/root/{fileName}"')
                while True:
                    res = ssh_stdout.readline()
                    if res == '':
                        break
                    time.sleep(0.05)
                    self.title(res)
                self.title(f'{fileName}执行完毕')

            t = threading.Thread(target=inner)
            t.setDaemon(True)
            t.start()

        def run_cmd(cmd='ls',endStr=None):
            def inner():
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
                t = 0
                while True:
                    try:
                        res = ssh_stdout.readline()
                        if res.replace('\n','') == '':
                            t += 1
                            if t==10: break
                        else:
                            t = 0
                            if endStr is not None and endStr in res:
                                break
                            self.title(res)
                            print(res.replace('\n',''))
                        time.sleep(0.02)
                    except:
                        break
                #self.title(f'指令执行完毕')
                print(f'指令执行完毕')
                #time.sleep(60)

            t = threading.Thread(target=inner)
            t.setDaemon(True)
            t.start()
            return t

        def run_cmd2(cmd='ls'):
            def inner():
                chan = ssh.invoke_shell()
                chan.send(cmd + '\n')
                buff = ''
                while not buff.endswith('#'):
                    resp = chan.recv(1024)
                    buff += resp.decode('utf-8',errors='replace')
                    print(resp)

            t = threading.Thread(target=inner)
            t.setDaemon(True)
            t.start()
            return t

        def load_diy():
            diyList = cacheM.config['DIY']
            for i,diy in enumerate(diyList):
                try:
                    fileSelEList[i].set(diy)
                except:
                    pass
            diyList = cacheM.config['DIY_2']
            for i,diy in enumerate(diyList):
                try:
                    cmdEList[i].insert(0,diy)
                except:
                    pass
        def save_diy():
            diyList = []
            for selE in fileSelEList:
                diyList.append(selE.get())
            cacheM.config['DIY'] = diyList
            diyList = []
            for selE in cmdEList:
                diyList.append(selE.get())
            cacheM.config['DIY_2'] = diyList
            cacheM.save_config()
        
        def uploadFile():
            def inner():
                def printTotals(transferred, toBeTransferred):
                    nonlocal time_now
                    if time.time() - time_now>1:
                        print("Transferred: {0}\tOut of: {1}".format(transferred, toBeTransferred))
                        self.title("%.3fM/%.3fM" % (transferred/1e6, toBeTransferred/1e6))
                        time_now += 1

                pvfPath = askopenfilename(filetypes=[('DNF Script.pvf file','*.pvf')])                
                if pvfPath=='' or not Path(pvfPath).exists():
                    self.title('文件错误')
                    return False
                print(pvfPath)
                sftp = paramiko.SFTPClient.from_transport(self.transPort)
                remote_path = r'/home/neople/game/Script.pvf'
                cmd = r'ls /home/neople/game/'
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
                res = ssh_stdout.readlines()
                #print(res)
                if len(res)<5:
                    self.title('目标文件夹异常')
                    return False
                time_now = time.time()
                sftp.put(pvfPath,remote_path,callback=printTotals)
                self.title('上传完成！')
                upPatch = messagebox.askokcancel('上传完成，是否上传等级补丁？')
                if upPatch:
                    remote_path = r'/home/neople/game/df_game_r'
                    patchPath = askopenfilename()    
                    if patchPath=='':
                        self.title('补丁文件错误')
                        return False
                    sftp.put(patchPath,remote_path,callback=printTotals)
            t = threading.Thread(target=inner)
            t.start()
    
        def lsDir(dirPath='/'):
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(f"ls {dirPath}")
            files = [item.strip() for item in ssh_stdout.readlines()]
            return files

        def downloadFile(filePath='',targetPath='',progressBarPos=[200,200],progressBarMaster=None):
            def showProgress(transferred, toBeTransferred):
                #print(transferred,toBeTransferred)
                nonlocal time_now
                if time.time() - time_now>1:
                    progressBar['maximum'] = toBeTransferred
                    # 进度值初始值
                    progressBar['value'] = transferred
                    progressBar.update()
                    time_now += 0.1

            # 使用paramiko下载文件到本机
            if progressBarMaster is None:
                progressBarMaster = self.master
            progressWin = tk.Toplevel(progressBarMaster)
            progressWin.geometry(f"+{progressBarPos[0]}+{progressBarPos[1]}")
            progressWin.overrideredirect(True)
            progressWin.wm_attributes('-topmost', 1)
            progressBar = ttk.Progressbar(progressWin)
            progressBar.pack()
            time_now = time.time()
            try:
                sftp = paramiko.SFTPClient.from_transport(self.transPort)
                sftp.get(filePath, targetPath,callback=showProgress)
            except:
                progressWin.destroy()
                return False
            progressWin.destroy()
            return True
            
        self.run_cmd = run_cmd
        self.lsDir = lsDir
        self.downloadFile = downloadFile
        self.connectingFlg = False
        self.connectedFlg = False
        import paramiko
        self.title = titlefunc
        ssh = paramiko.SSHClient()
        self.ssh = ssh
        self.transPort:paramiko.Transport = None
        
        
        # 允许连接不在know_hosts文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        startingFlg = False
        serverFrame = tk.Frame(tabView)
        tabView.add(serverFrame,text=tabName)
        self.master = tabView
        serverConFrame = tk.Frame(serverFrame)
        serverConFrame.pack()
        from cacheManager import config
        if True:
            tk.Label(serverConFrame,text='IP').grid(row=0,column=1,sticky='we')
            ipE = ttk.Entry(serverConFrame,width=int(WIDTH*13))
            ipE.grid(row=0,column=2,pady=5,sticky='we')
            ipE.insert(0,config['SERVER_IP'])
            tk.Label(serverConFrame,text='端口').grid(row=0,column=3,sticky='we')
            portE = ttk.Entry(serverConFrame,width=int(WIDTH*2))
            portE.insert(0,config['SERVER_PORT'])
            portE.grid(row=0,column=4,sticky='we')
            tk.Label(serverConFrame,text='用户名').grid(row=1,column=1,sticky='we')
            userE = ttk.Entry(serverConFrame,width=int(WIDTH*4))
            userE.insert(0,config['SERVER_USER'])
            userE.grid(row=1,column=2,sticky='we')
            tk.Label(serverConFrame,text='密码').grid(row=1,column=3,sticky='we')
            pwdE = ttk.Entry(serverConFrame,width=int(WIDTH*7))#,show='*'
            pwdE.insert(0,config['SERVER_PWD'])
            pwdE.grid(row=1,column=4,sticky='we')
            db_conBTN = ttk.Button(serverConFrame,text='连接',command=connect)
            db_conBTN.grid(row=0,column=5,rowspan=1,pady=5,padx=5,sticky='we')
            db_conBTN2 = ttk.Button(serverConFrame,text='密钥连接',command=lambda:connect(key=True))
            db_conBTN2.grid(row=1,column=5,rowspan=1,pady=5,padx=5,sticky='we')

        self.ipE = ipE
        self.portE = portE
        self.pwdE = pwdE
        self.userE = userE
        self.connect = connect

        #ttk.Separator(serverFrame, orient='horizontal').pack(fill='x')
        serverFuncFrame = tk.Frame(serverFrame)
        serverFuncFrame.pack()
        if True:
            cfg = {'padx':1,'pady':3, 'sticky':'nswe'}
            normalFuncFrame = tk.Frame(serverFuncFrame)
            normalFuncFrame.pack()
            runBtn = ttk.Button(normalFuncFrame,text='启动服务器',command=run_server,width=int(WIDTH*10))
            runBtn.grid(row=3,column=2,**cfg)
            CreateToolTip(runBtn,'执行/root/run文件')
            stopBtn = ttk.Button(normalFuncFrame,text='停止服务器',command=stop_server,width=int(WIDTH*10))
            stopBtn.grid(row=3,column=3,**cfg)
            CreateToolTip(stopBtn,'执行/root/stop文件')
            run1Btn = ttk.Button(normalFuncFrame,text='重启频道',command=restart_channel,width=int(WIDTH*10))
            run1Btn.grid(row=3,column=4,**cfg)
            CreateToolTip(run1Btn,'执行/root/run1文件')
            uploadBtn = ttk.Button(normalFuncFrame,text='上传PVF',command=uploadFile,width=int(WIDTH*10))
            uploadBtn.grid(row=3,column=5,**cfg)
            #ttk.Button(normalFuncFrame,text='',command=downloadFile,width=int(WIDTH*14)).grid(row=4,column=4,**cfg)
            CreateToolTip(uploadBtn,'上传到/home/neople/game/Script.pvf并将原文件覆盖')
            diyFuncFrame = ttk.LabelFrame(serverFuncFrame,text='自定义功能')
            diyFuncFrame.pack()
            fileSelEList= []
            cmdEList = []
            def diy_func_frame(master,row):
                fileSelE1 = ttk.Combobox(master,width=int(WIDTH*11))
                fileSelE1.grid(row=row,column=1,**cfg)
                CreateToolTip(fileSelE1,textFunc=lambda:'执行脚本：'+fileSelE1.get())
                ttk.Button(master,text='执行',command=lambda:run_file(fileSelE1.get()),width=int(WIDTH*7)).grid(row=row,column=2,**cfg)
                fileSelE2 = ttk.Combobox(master,width=int(WIDTH*11))
                fileSelE2.grid(row=row,column=3,**cfg)
                CreateToolTip(fileSelE2,textFunc=lambda:'执行脚本：'+fileSelE2.get())
                ttk.Button(master,text='执行',command=lambda:run_file(fileSelE2.get()),width=int(WIDTH*7)).grid(row=row,column=4,**cfg)
                fileSelEList.extend([fileSelE1,fileSelE2])
                fileSelE1.bind('<<ComboboxSelected>>',lambda e:save_diy())
                fileSelE2.bind('<<ComboboxSelected>>',lambda e:save_diy())
            def diy_func_frame2(master,row):
                cmdE = ttk.Entry(master,width=int(WIDTH*11))
                cmdE.grid(row=row,column=1,columnspan=3,**cfg)
                ttk.Button(master,text='执行',command=lambda:run_cmd(cmdE.get()),width=int(WIDTH*7)).grid(row=row,column=4,**cfg)
                cmdEList.append(cmdE)
                cmdE.bind('<<FocusOut>>',lambda e:save_diy())
                CreateToolTip(cmdE,textFunc=lambda:'shell指令：'+cmdE.get())
            for i in range(int(2*HEIGHT)):
                diy_func_frame(diyFuncFrame,i)

            for i in range(int(2*HEIGHT),int(4*HEIGHT)):
                diy_func_frame2(diyFuncFrame,i)

            load_diy()
            configFrame(serverFuncFrame,'disable')
            if autoConnect:
                connect(False)


if __name__=='__main__':
    t = tk.Tk()
    t.title('DNF服务器管理')
    t.iconbitmap('./config/ico.ico')
    tab = ttk.Notebook(t)
    tab.pack()
    ServerCtrlFrame(tab,titlefunc=t.title)
    t.mainloop()