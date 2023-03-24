import cacheManager as cacheM 
import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter import ttk
import threading, time
from toolTip import CreateOnceToolTip,CreateToolTip
from pathlib import Path
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
class ServerCtrlFrame(tk.Frame):
    def __init__(self,tabView,tabName='服务器管理',titlefunc=lambda x:...,*args,**kw):
        def connect(show=True):
            def inner():
                ip = db_ip.get()
                port = int(db_port.get())
                user = db_user.get()
                pwd = db_pwd.get()
                try:
                    ssh.connect(ip, username=user, port=port, password=pwd,timeout=3)
                    self.transPort = paramiko.Transport((ip,port))
                    self.transPort.connect(username=user, password=pwd)
                    
                except Exception as e:
                    if show:
                        self.title(f'连接失败 {e}')
                    return False
                cacheM.config['SERVER_IP'] = ip
                cacheM.config['SERVER_PORT'] = port
                cacheM.config['SERVER_USER'] = user
                cacheM.config['SERVER_PWD'] = pwd
                cacheM.save_config()
                configFrame(serverFuncFrame,'normal')
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls /root")
                files = [item.strip() for item in ssh_stdout.readlines()]
                for fileSelE in fileSelEList:
                    fileSelE.config(values=files)
                print(files)
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

        def run_cmd(cmd='ls'):
            def inner():
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
                while True:
                    res = ssh_stdout.readline()
                    if res == '':
                        break
                    time.sleep(0.05)
                    self.title(res)
                    print(res)
                self.title(f'指令执行完毕')

            t = threading.Thread(target=inner)
            t.setDaemon(True)
            t.start()

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
            t = threading.Thread(target=inner)
            t.start()
    
        def downloadFile():
            ...

        import paramiko
        self.title = titlefunc
        ssh = paramiko.SSHClient()
        
        
        # 允许连接不在know_hosts文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        startingFlg = False
        serverFrame = tk.Frame(tabView)
        tabView.add(serverFrame,text=tabName)
        serverConFrame = tk.Frame(serverFrame)
        serverConFrame.pack()
        from cacheManager import config
        if True:
            tk.Label(serverConFrame,text='IP').grid(row=0,column=1,sticky='we')
            db_ip = ttk.Entry(serverConFrame,width=int(WIDTH*13))
            db_ip.grid(row=0,column=2,pady=5,sticky='we')
            db_ip.insert(0,config['SERVER_IP'])
            tk.Label(serverConFrame,text='端口').grid(row=0,column=3,sticky='we')
            db_port = ttk.Entry(serverConFrame,width=int(WIDTH*2))
            db_port.insert(0,config['SERVER_PORT'])
            db_port.grid(row=0,column=4,sticky='we')
            tk.Label(serverConFrame,text='用户名').grid(row=1,column=1,sticky='we')
            db_user = ttk.Entry(serverConFrame,width=int(WIDTH*4))
            db_user.insert(0,config['SERVER_USER'])
            db_user.grid(row=1,column=2,sticky='we')
            tk.Label(serverConFrame,text='密码').grid(row=1,column=3,sticky='we')
            db_pwd = ttk.Entry(serverConFrame,width=int(WIDTH*7))#,show='*'
            db_pwd.insert(0,config['SERVER_PWD'])
            db_pwd.grid(row=1,column=4,sticky='we')
            db_conBTN = ttk.Button(serverConFrame,text='连接',command=connect)
            db_conBTN.grid(row=0,column=5,rowspan=2,pady=5,padx=5,sticky='nswe')

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
            connect(False)


if __name__=='__main__':
    t = tk.Tk()
    t.title('DNF服务器管理')
    t.iconbitmap('./config/ico.ico')
    tab = ttk.Notebook(t)
    tab.pack()
    ServerCtrlFrame(tab,titlefunc=t.title)
    t.mainloop()