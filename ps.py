import  os,shutil,psutil
from tkinter import ttk, messagebox
import subprocess
from tkinter.filedialog import askopenfilename, asksaveasfilename
from pathlib import Path
import threading
import time
ICON_PATH = r'.\config\DNF.ico'
B2E_PATH = r'config\b2e.exe'
workingFlg = False


def getDNF():
    dnfCMDLines = []
    for proc in psutil.process_iter():
        try:
            if proc.name().lower()=='dnf.exe':
                dnfCMDLines.append(proc)
            time.sleep(0.001)
        except:
            pass    
    return dnfCMDLines

def saveStart(runFunc=lambda:...):
    def inner():
        global workingFlg
        workingFlg = True
        print('搜寻DNF进程中...')
        dnfCMDLines = getDNF()
        workingFlg = False
        if len(dnfCMDLines) == 0:
            print('未找到DNF游戏进程！')
            #messagebox.showinfo('DNF未启动','未找到DNF游戏进程！')
            workingFlg = False
            runFunc()
            return False
        print(dnfCMDLines)
        dnfPath = dnfCMDLines[0].exe()
        dnfArgs = dnfCMDLines[0].cmdline()[1:]
        dnfPath = Path(dnfCMDLines[0].exe())
        startCMD_full = 'start "" ' + f'"{dnfPath}" ' + ' '.join(dnfArgs)
        startCMD = 'start '+ ' '.join(dnfCMDLines[0].cmdline())
        
        b2ePath = os.path.join(os.getcwd(),B2E_PATH)
        outPath = Path(asksaveasfilename(title=f'请保存至DNF.exe同级游戏目录',filetypes=[('可执行文件',f'*.exe')],initialfile=f'DNF一键登录.exe',initialdir=dnfPath.parent))
        if len(str(outPath))<2:
            return False
        if str(outPath)[-4:]!='.exe':
            outPath = Path(str(outPath)+'.exe')
        outPath_bat = Path(str(outPath)[:-3] + 'bat')
        with open(outPath_bat,'w') as f:
            f.write(startCMD)
        print(outPath_bat)
        cmd = f'"{b2ePath}" /bat "{outPath_bat}" /exe "{outPath}" /icon "{ICON_PATH}" /invisible'# 
        print(cmd)
        pi = subprocess.Popen(cmd,shell=False,cwd=os.getcwd(),stdout=subprocess.PIPE)
        blankLineNum = 0
        for i in iter(pi.stdout.readline,'b'):
            ret = i.decode('gbk',errors='ignore').strip()
            if ret=='':
                blankLineNum+=1
                if blankLineNum>4:
                    pi.kill()
                    break
            else:
                print(ret) #编码问题
        
        with open(outPath_bat,'w') as f:
            f.write(startCMD_full)
        if outPath.exists():
            openDirCMD = f'explorer.exe /select,{str(outPath)}'
            subprocess.Popen(openDirCMD,shell=False)
            print('保存结束')
        else:
            print('保存失败')
        runFunc()
        
    if workingFlg:
        return False
    t = threading.Thread(target=inner)
    t.setDaemon(True)
    t.start()
    

if __name__=='__main__':
    saveStart()