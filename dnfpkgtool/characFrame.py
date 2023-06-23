
import tkinter as tk
import tkinter.ttk as ttk
if not hasattr(ttk,'Spinbox'):
    class Spinbox(ttk.Entry):
        def __init__(self, master=None, **kw):  #from_=0,to=99,
            ttk.Entry.__init__(self, master, "ttk::spinbox", **kw)
        def set(self, value):
            self.tk.call(self._w, "set", value)
    ttk.Spinbox = Spinbox

class CharacframeWidget(ttk.Frame):
    def __init__(self, master=None, **kw):
        super(CharacframeWidget, self).__init__(master, **kw)
        frame2 = ttk.Frame(self)
        frame2.configure(height=200, width=200)
        self.otherFunctionFrame = ttk.Labelframe(frame2)
        self.otherFunctionFrame.configure(height=200, text='附加功能', width=150)
        frame7 = ttk.Frame(self.otherFunctionFrame)
        frame7.configure(height=100, width=150)
        self.saveStartBtn = ttk.Button(frame7)
        self.saveStartBtn.configure(text='生成一键启动器')
        self.saveStartBtn.pack(fill="x", pady=1, side="top")
        self.saveStartBtn.configure(command=self.saveStart)
        self.pvfCacheMBtn = ttk.Button(frame7)
        self.pvfCacheMBtn.configure(text='PVF缓存管理器')
        self.pvfCacheMBtn.pack(fill="x", pady=1, side="top")
        self.pvfCacheMBtn.configure(command=self.open_PVF_Cache_Edit)
        self.pvfToolBtn = ttk.Button(frame7)
        self.pvfToolBtn.configure(text='PVF工具')
        self.pvfToolBtn.pack(fill="x", pady=1, side="top")
        self.pvfToolBtn.configure(command=self._open_PVF_Editor)
        self.enableAuctionBtn = ttk.Button(frame7)
        self.enableAuctionBtn.configure(text='启用拍卖行')
        self.enableAuctionBtn.pack(fill="x", pady=1, side="top")
        self.enableAuctionBtn.configure(command=self.enable_auction)
        self.checkUpdateBtn = ttk.Checkbutton(frame7)
        self.updateCheckVar = tk.IntVar()
        self.checkUpdateBtn.configure(
            text='自动检查更新', variable=self.updateCheckVar)
        self.checkUpdateBtn.pack(expand="true", side="top")
        self.HDresolutionBtn = ttk.Checkbutton(frame7)
        self.HDResolutionVar = tk.IntVar()
        self.HDresolutionBtn.configure(
            text='高分辨率缩放', variable=self.HDResolutionVar)
        self.HDresolutionBtn.pack(expand="true", side="top")
        frame7.pack(expand="true", fill="both", padx=3, side="top")
        self.otherFunctionFrame.pack(fill="y", side="left")
        self.gitHubFrame = ttk.Frame(frame2)
        self.gitHubFrame.configure(height=150, width=150)
        self.gitHubFrame.pack(side="right")
        self.characEntriesFrame = ttk.Frame(frame2)
        self.characEntriesFrame.configure(height=200, width=200)
        label1 = ttk.Label(self.characEntriesFrame)
        label1.configure(text='角色名：')
        label1.grid(column=0, row=0)
        self.nameE = ttk.Entry(self.characEntriesFrame)
        self.nameE.grid(
            column=1,
            columnspan=2,
            padx=1,
            pady=1,
            row=0,
            sticky="ew")
        label2 = ttk.Label(self.characEntriesFrame)
        label2.configure(text='角色等级：')
        label2.grid(column=0, row=1)
        self.levE = ttk.Spinbox(self.characEntriesFrame)
        self.levE.configure(width=8)
        self.levE.grid(column=1, padx=1, pady=1, row=1, sticky="ew")
        checkbutton2 = ttk.Checkbutton(self.characEntriesFrame)
        self.isVIP = tk.IntVar()
        checkbutton2.configure(text='VIP账户', variable=self.isVIP)
        checkbutton2.grid(column=2, row=1)
        label3 = ttk.Label(self.characEntriesFrame)
        label3.configure(text='职业：')
        label3.grid(column=0, row=2)
        self.jobE = ttk.Combobox(self.characEntriesFrame)
        self.jobE.configure(width=8)
        self.jobE.grid(column=1, padx=1, pady=1, row=2, sticky="ew")
        self.jobE.bind("<<ComboboxSelected>>", self.set_grow_type, add="")
        self.jobE2 = ttk.Combobox(self.characEntriesFrame)
        self.jobE2.configure(width=8)
        self.jobE2.grid(column=2, padx=1, row=2, sticky="ew")
        label4 = ttk.Label(self.characEntriesFrame)
        label4.configure(text='成长类型：')
        label4.grid(column=0, row=3)
        self.growTypeE = ttk.Combobox(self.characEntriesFrame)
        self.growTypeE.configure(width=8)
        self.growTypeE.grid(
            column=1,
            columnspan=2,
            padx=1,
            pady=1,
            row=3,
            sticky="ew")
        label5 = ttk.Label(self.characEntriesFrame)
        label5.configure(text='觉醒标识：')
        label5.grid(column=0, row=4)
        self.wakeFlgE = ttk.Combobox(self.characEntriesFrame)
        self.wakeFlgE.configure(width=8)
        self.wakeFlgE.grid(column=1, padx=1, pady=1, row=4, sticky="ew")
        checkbutton3 = ttk.Checkbutton(self.characEntriesFrame)
        self.isReturnUser = tk.IntVar()
        checkbutton3.configure(text='回归玩家', variable=self.isReturnUser)
        checkbutton3.grid(column=2, row=4)
        self.commitBtn = ttk.Button(self.characEntriesFrame)
        self.commitBtn.configure(text='提交修改')
        self.commitBtn.grid(column=0, columnspan=3, padx=1, row=5, sticky="ew")
        self.commitBtn.configure(command=self.commit)
        self.characEntriesFrame.pack(
            anchor="center",
            expand="true",
            fill="both",
            padx=5,
            pady=5,
            side="top")
        self.characEntriesFrame.rowconfigure("all", weight=1)
        self.characEntriesFrame.columnconfigure(1, weight=1)
        frame2.pack(fill="x", side="top")
        self.imageFrame = ttk.Frame(self)
        self.imageFrame.configure(height=200, width=200)
        self.imageFrame.pack(expand="true", fill="both", side="top")
        self.configure(height=200, width=200)
        self.pack(expand="true", fill="both", side="top")

    def saveStart(self):
        pass

    def open_PVF_Cache_Edit(self):
        pass

    def enable_auction(self):
        pass

    def _open_PVF_Editor(self):
        pass

    def set_grow_type(self, event=None):
        pass

    def commit(self):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    widget = CharacframeWidget(root)
    widget.pack(expand=True, fill="both")
    root.mainloop()

