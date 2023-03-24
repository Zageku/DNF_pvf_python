import requests
from pathlib import Path
import os
import json
import threading
LOCAL_VERSION_PATH = Path('./config/versionDict.json')
UPDATE_INFO_URL_LIST = [r'https://raw.githubusercontent.com/Zageku/DNF_pvf_python/main/versionDict.json',
                        r'https://kyap-1256331219.cos.ap-beijing.myqcloud.com/versionDict.json'
                    ]
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
        print('版本号加载失败，使用原始版本')
        
local_version = versionDict.get('VERSION')  
local_version_url = versionDict.get('URL')  
versionDict_remote = {}
targetPath = Path('')
UPDATING_FLG = False
newFileName = ''

proxies = { "http": None, "https": None}
def gen_Update_Json(new_version,new_url,info=''):
    if new_version==versionDict['VERSION'] or new_version in versionDict['history'].keys():   #版本已存在
        json.dump(versionDict,open(LOCAL_VERSION_PATH,'w'),ensure_ascii=False)
        print('版本号已存在！')
        return False
    versionDict_new = versionDict.copy()
    if not isinstance(versionDict_new['history'],dict):
        versionDict_new['history'] = {}
    versionDict_new['history'][versionDict_new['VERSION']] = versionDict_new['URL'] 
    versionDict_new['VERSION'] = new_version
    versionDict_new['URL'] = new_url
    versionDict_new['INFO'] = info
    json.dump(versionDict_new,open(LOCAL_VERSION_PATH,'w'),ensure_ascii=False)
    return versionDict_new

def check_Update():
    global  versionDict_remote, targetPath
    print(f'当前版本：{versionDict}')
    for UPDATE_url in UPDATE_INFO_URL_LIST:
        try:
            updateFile = requests.get(UPDATE_url,timeout=3, proxies=proxies)
            try:
                updateFile = updateFile.content.decode('GB2312')
            except:
                updateFile = updateFile.content.decode()
            #print(updateFile)
            versionDict_remote = json.loads(updateFile)
            print(f'{UPDATE_url}\n更新列表：{versionDict_remote}')
            #print(local_version,versionDict_remote['history'].keys())
            if local_version in versionDict_remote['history'].keys() and local_version!= versionDict_remote['VERSION']: #在历史版本且不是最新版
                url:str = versionDict_remote['URL']
                newFileName = '背包编辑工具-'+url.rsplit('/')[-1]
                targetPath = Path(os.getcwd()).joinpath(newFileName)
                return True
            elif versionDict_remote['VERSION'] not in versionDict['history'].keys() and local_version!= versionDict_remote['VERSION']:    #服务器版本不在本地列表中
                url:str = versionDict_remote['URL']
                newFileName = '背包编辑工具-'+url.rsplit('/')[-1]
                targetPath = Path(os.getcwd()).joinpath(newFileName)
                return True
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
        try:
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
            
            res_left = requests.get(url, stream=True, headers=headers, proxies=proxies)
            with open(targetPath, mode) as f:
                for chunk in res_left.iter_content(chunk_size=102400):
                    temp_size += len(chunk)
                    f.write(chunk)
                    f.flush()
                    print(f"{temp_size}/{total_size}")
            #下载完成后检查大小，不完整或过度下载则删除后重新进行下载
            if temp_size!=total_size:
                targetPath.unlink()
                print(f'[ERROR] {targetPath}文件大小错误，重新进行下载')
                return get_Update2(finFunc)
            else:
                print(f'[INFO] {targetPath} 下载完成')
                UPDATING_FLG = False
                finFunc()
        except Exception as e:
            print(f'下载失败 {e}')
            UPDATING_FLG = False

    t = threading.Thread(target=inner)
    t.setDaemon(True)
    t.start()
    global UPDATING_FLG
    UPDATING_FLG = True
if __name__=='__main__':
    update_state = check_Update()
    
    print('本地：',versionDict)
    print('云端：',versionDict_remote)
    versionDict = versionDict_remote
    versionDict = gen_Update_Json('230319a','此处为URL','修复邮件发送时装显示过期的bug\n[增量更新]下载后请解压覆盖文件')
    print('新本地：',versionDict)
    versionDict = {
        'VERSION':'230313',
        'URL':'',
        'history':{
            '230313':'url'
        }
    }
    update_state = check_Update()
    print('版本号更新：',update_state)
    print(versionDict_remote)
    targetPath = Path(os.getcwd()).joinpath('newFileName.zip')
    '''get_Update2()
    import  time
    while UPDATING_FLG:
        time.sleep(1)'''