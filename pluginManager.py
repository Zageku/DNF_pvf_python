try:
    ONEKEY_FLG = False
    oneKeyWin = None
    #print(dir(oneKey))
    def openOneyKey(a):
        import oneKey_lite as oneKey
        import tkinter as tk
        global ONEKEY_FLG, oneKeyWin
        if ONEKEY_FLG:
            oneKeyWin.wm_attributes('-topmost', 1)
            oneKeyWin.wm_attributes('-topmost', 0)
            return
        
        def quit():
            global ONEKEY_FLG
            ONEKEY_FLG=False
            oneKeyWin.destroy()
        
        oneKeyWin = tk.Toplevel(a.w)
        oneKeyWin.title('全服道具检索工具-体验版')
        oneKeyWin.protocol('WM_DELETE_WINDOW',quit)
        IconPath = 'config/ico.ico'
        oneKeyWin.iconbitmap(IconPath)
        app = oneKey.OnekeyframeApp(oneKeyWin)
        app.pkgTool = a
        app.connSQL()
        ONEKEY_FLG = True
    
    def openOneyKey(a):
        import webbrowser
        import cacheManager as cacheM
        webbrowser.open(cacheM.config['QQ'])
except:
    pass
