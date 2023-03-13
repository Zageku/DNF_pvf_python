import requests
from pathlib import Path
import os
import json
import threading
LOCAL_VERSION_PATH = Path('./config/versionDict.json')
UPDATE_INFO_URL = r'https://raw.githubusercontent.com/Zageku/DNF_pvf_python/main/versionDict.json'
versionDict = {
        'VERSION':'230313',
        'URL':'',
        'history':{
            '230313':'url'
        }
    }
if LOCAL_VERSION_PATH.exists():
    try:
        versionDict = json.load(open(LOCAL_VERSION_PATH,'r'))
    except:
        pass
        
local_version = versionDict.get('VERSION')  
local_version_url = versionDict.get('URL')  
versionDict_remote = {}
targetPath = Path('')
UPDATING_FLG = False
newFileName = ''
def gen_Update_Json(new_version,new_url):
    if new_version==local_version and new_url==local_version_url:   #版本无变化
        json.dump(versionDict,open(LOCAL_VERSION_PATH,'w'),ensure_ascii=False)
        return False
    versionDict_new = versionDict.copy()
    if not isinstance(versionDict_new['history'],dict):
        versionDict_new['history'] = {}
    versionDict_new['history'][local_version] = local_version_url
    versionDict_new['VERSION'] = new_version
    versionDict_new['URL'] = new_url
    json.dump(versionDict_new,open(LOCAL_VERSION_PATH,'w'),ensure_ascii=False)
    return True

def check_Update():
    global  versionDict_remote, targetPath
    try:
        updateFile = requests.get(UPDATE_INFO_URL).content.decode()
        versionDict_remote = json.loads(updateFile)
        print(versionDict_remote)
        #print(local_version,versionDict_remote['history'].keys())
        if local_version in versionDict_remote['history'].keys():
            url:str = versionDict_remote['URL']
            newFileName = '背包编辑工具-'+url.rsplit('/')[-1]
            targetPath = Path(os.getcwd()).joinpath(newFileName)
            return True
        else:
            return False
    except:
        print('更新列表获取失败')
        return False


def get_Update():
    def inner():
        global UPDATING_FLG
        file = requests.get(versionDict_remote['URL']).content
        fileName = '背包编辑工具-'+versionDict_remote['URL'].rsplit('/')[-1]
        with open(fileName,'wb') as f:
            f.write(file)
            UPDATING_FLG = False
    t = threading.Thread(target=inner)
    t.setDaemon(True)
    t.start()
    global UPDATING_FLG
    UPDATING_FLG = True
def get_Update2(finFunc=lambda:...):
    def inner():
        global UPDATING_FLG, newFileName
        url:str = versionDict_remote['URL']
        content = requests.get(url,stream=True)
        total_size = int(content.headers['Content-Length'])
        newFileName = '背包编辑工具-'+url.rsplit('/')[-1]
        #targetPath = Path(os.getcwd()).joinpath(newFileName)
        temp_size = 0
        mode = 'wb'
        print(f"{url.split('/')[-1]} 总：%d 字节，开始下载..." % (total_size,))
        headers = {'Range': 'bytes=%d-' % temp_size,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"}

        res_left = requests.get(url, stream=True, headers=headers)
        with open(targetPath, mode) as f:
            for chunk in res_left.iter_content(chunk_size=1024):
                temp_size += len(chunk)
                f.write(chunk)
                f.flush()
        #下载完成后检查大小，不完整或过度下载则删除后重新进行下载
        if temp_size!=total_size:
            targetPath.unlink()
            print(f'[ERROR] {targetPath}文件大小错误，重新进行下载')
            return get_Update2(finFunc)
        else:
            print(f'[INFO] {targetPath} 下载完成')
            UPDATING_FLG = False
            finFunc()

    t = threading.Thread(target=inner)
    t.setDaemon(True)
    t.start()
    global UPDATING_FLG
    UPDATING_FLG = True
if __name__=='__main__':
    gen_Update_Json('230314','https://github.com/Zageku/DNF_pvf_python/releases/download/v2.0.0/dnf_package_tool_v2.0.0_.zip')
    print(versionDict)
    check_Update()
    get_Update2()
    import  time
    while UPDATING_FLG:
        time.sleep(1)