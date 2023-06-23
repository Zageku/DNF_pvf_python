import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import socket
import pickle
import json
import datetime
import zlib
import threading

import uuid
mac_address = uuid.uuid1().hex[-12:].upper()
mac_address = '-'.join([mac_address[i:i+2] for i in range(0, 11, 2)])
#print(mac_address)

oldPrint = print
logFunc = [oldPrint]
def print(*args,**kw):
    logFunc[-1](*args,**kw)

def inThread(func):
    def inner(*args,**kw):
        t = threading.Thread(target=lambda:func(*args,**kw))
        t.setDaemon(True)
        t.start()
        return t
    return inner

class MessageframeWidget(ttk.Frame):
    def __init__(self, master=None, **kw):
        super(MessageframeWidget, self).__init__(master, **kw)
        self.msgListFrame = ttk.Labelframe(self)
        self.msgListFrame.configure(height=200, text='留言列表', width=200)
        frame3 = ttk.Frame(self.msgListFrame)
        frame3.configure(height=200, width=200)
        self.msgFilterE = ttk.Combobox(frame3)
        self.msgFilterE.configure(state="readonly", values='全部 普通 发电 广告 求助 分享')
        self.msgFilterE.pack(side="left")
        self.msgFilterE.bind("<<ComboboxSelected>>", self.filt_message, add="")
        button3 = ttk.Button(frame3)
        button3.configure(text='发布留言')
        button3.pack(side="right")
        button3.configure(command=self.prePostMessage)
        frame3.pack(fill="x", padx=5, side="top")
        frame2 = ttk.Frame(self.msgListFrame)
        frame2.configure(height=200, width=200)
        self.msgListTree = ttk.Treeview(frame2)
        self.msgListTree.configure(selectmode="extended", show="headings")
        self.msgListTree_cols = [
            'column1',
            'column2',
            'column3',
            'column4',
            'column5',
            'column7',
            'column6']
        self.msgListTree_dcols = [
            'column2',
            'column3',
            'column4',
            'column5',
            'column7']
        self.msgListTree.configure(
            columns=self.msgListTree_cols,
            displaycolumns=self.msgListTree_dcols)
        self.msgListTree.column(
            "column1",
            anchor="center",
            stretch="true",
            width=40,
            minwidth=20)
        self.msgListTree.column(
            "column2",
            anchor="center",
            stretch="true",
            width=40,
            minwidth=20)
        self.msgListTree.column(
            "column3",
            anchor="center",
            stretch="true",
            width=20,
            minwidth=20)
        self.msgListTree.column(
            "column4",
            anchor="center",
            stretch="true",
            width=80,
            minwidth=20)
        self.msgListTree.column(
            "column5",
            anchor="center",
            stretch="true",
            width=50,
            minwidth=20)
        self.msgListTree.column(
            "column7",
            anchor="center",
            stretch="true",
            width=25,
            minwidth=20)
        self.msgListTree.column(
            "column6",
            anchor="center",
            stretch="true",
            width=80,
            minwidth=20)
        self.msgListTree.heading("column1", anchor="center", text='留言IP')
        self.msgListTree.heading("column2", anchor="center", text='昵称')
        self.msgListTree.heading("column3", anchor="center", text='分类')
        self.msgListTree.heading("column4", anchor="center", text='标题')
        self.msgListTree.heading("column5", anchor="center", text='时间')
        self.msgListTree.heading("column7", anchor="center", text='赞数')
        self.msgListTree.heading("column6", anchor="center", text='ID')
        self.msgListTree.pack(expand="true", fill="both", side="left")
        self.msgListTree.bind("<<TreeviewSelect>>", self.showMessage, add="")
        self.msgListBar = ttk.Scrollbar(frame2)
        self.msgListBar.configure(orient="vertical")
        self.msgListBar.pack(expand="false", fill="y", side="right")
        frame2.pack(expand="true", fill="both", side="top")
        self.msgListFrame.pack(expand="true", fill="both", side="left")
        self.msgDetailFrame = ttk.Labelframe(self)
        self.msgDetailFrame.configure(height=200, text='留言详情', width=200)
        self.ip_topicLabel = ttk.Label(self.msgDetailFrame)
        self.ip_topicLabel.configure(text='标题')
        self.ip_topicLabel.grid(column=0, row=0)
        self.msgTopic_IPE = ttk.Entry(self.msgDetailFrame)
        self.msgTopic_IPE.grid(column=1, row=0, sticky="ew")
        label2 = ttk.Label(self.msgDetailFrame)
        label2.configure(text='昵称')
        label2.grid(column=0, row=1)
        self.msgNameE = ttk.Entry(self.msgDetailFrame)
        self.msgNameE.grid(column=1, row=1, sticky="ew")
        self.msgMainE = tk.Text(self.msgDetailFrame)
        self.msgMainE.configure(height=10, width=30)
        _text_ = '每个IP每天可以发送3条留言\n字数限制200字'
        self.msgMainE.insert("0.0", _text_)
        self.msgMainE.grid(column=0, columnspan=2, row=3, sticky="nsew")
        label3 = ttk.Label(self.msgDetailFrame)
        label3.configure(text='分类')
        label3.grid(column=0, row=2)
        self.msgBtnFrame = ttk.Frame(self.msgDetailFrame)
        self.msgBtnFrame.configure(height=200, width=200)
        self.reportBtn = ttk.Button(self.msgBtnFrame)
        self.reportBtn.configure(text='举报留言')
        self.reportBtn.pack(expand="true", fill="x", side="left")
        self.reportBtn.configure(command=self.reportMsg)
        self.likeBtn = ttk.Button(self.msgBtnFrame)
        self.likeBtn.configure(text='点赞留言')
        self.likeBtn.pack(expand="true", fill="x", side="left")
        self.likeBtn.configure(command=self.likeMsg)
        self.postBtn = ttk.Button(self.msgBtnFrame)
        self.postBtn.configure(text='发布留言')
        self.postBtn.pack(expand="true", fill="x", side="left")
        self.postBtn.configure(command=self.postMsg)
        self.msgBtnFrame.grid(column=0, columnspan=2, row=8, sticky="ew")
        self.msgTypeE = ttk.Combobox(self.msgDetailFrame)
        self.msgTypeE.configure(state="readonly", values='普通 发电 广告 求助 分享')
        self.msgTypeE.grid(column=1, row=2, sticky="ew")
        self.msgDetailFrame.pack(fill="both", side="left")
        self.msgDetailFrame.rowconfigure(3, weight=1)
        self.configure(height=200, width=200)
        self.pack(expand="true", fill="both", side="top")

        self._build()
    @inThread
    def _build(self):
        bar = self.msgListBar
        box = self.msgListTree
        bar.config(command=box.yview)
        box.config(yscrollcommand=bar.set)
        self.msgFilterE.set('全部')
        self.msgDict = {}
        self.prePostMessage()
        self.get_messages()
        self.filt_message()
        #
        
    
    def get_messages(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        msg = {
            'cmd':'get_messages',
        }
        msgBytes = json.dumps(msg).encode('utf-8')
        s.sendto(msgBytes,('127.0.0.1', 23334))
        s.settimeout(5)
        try:
            messageDictBytesCompressed = s.recv(10240)
            msgDictBytes = zlib.decompress(messageDictBytesCompressed)
            self.msgDict = pickle.loads(msgDictBytes)
        except:
            import traceback
            #print(traceback.format_exc())
            print('获取留言失败')
            pass
        #print(self.msgDict)

    def filt_message(self, event=None):
        typeFilt = self.msgFilterE.get()
        self.msgListTree.delete(*self.msgListTree.get_children())
        for msgID,msgDict in self.msgDict.items():
            if typeFilt == '全部' or typeFilt == msgDict['type']:
                self.msgListTree.insert('', 'end', values=(msgDict['ip'],msgDict['name'],msgDict['type'],msgDict['topic'],msgDict['time'],msgDict['like_num'],msgID))


    def prePostMessage(self):
        self.msgTopic_IPE.configure(state='normal')
        self.msgNameE.configure(state='normal')
        self.msgTypeE.configure(state='readonly')
        self.msgMainE.configure(state='normal')
        self.msgTopic_IPE.delete(0, 'end')
        self.msgNameE.delete(0, 'end')
        self.msgTypeE.set('普通')
        self.msgMainE.delete(1.0, 'end')
        #self.msgMainE.insert(1.0, '每个IP每天可以发送3条留言\n字数限制200字')
        self.reportBtn.configure(state='disabled')
        self.likeBtn.configure(state='disabled')
        self.postBtn.configure(state='normal')
        
        pass

    def showMessage(self, event=None):
        self.msgTopic_IPE.configure(state='normal')
        self.msgNameE.configure(state='normal')
        self.msgTypeE.configure(state='disabled')
        self.msgMainE.configure(state='normal')
        self.msgTopic_IPE.delete(0, 'end')
        self.msgNameE.delete(0, 'end')
        self.msgTypeE.set('普通')
        self.msgMainE.delete(1.0, 'end')
        self.reportBtn.configure(state='normal')
        self.likeBtn.configure(state='normal')
        self.postBtn.configure(state='disabled')
        
        sel = self.msgListTree.selection()[-1]
        values = self.msgListTree.item(sel, 'values')
        ip,name,type_,topic,timeStamp,likeNum,ID = values
        msgMain = self.msgDict.get(int(ID))
        
        if msgMain is None:
            self.reportBtn.configure(state='disabled')
            self.likeBtn.configure(state='disabled')
            return
        
        msgMainText = msgMain.get('detail_text', '留言已被删除')

        self.msgTopic_IPE.insert(0, topic)
        self.msgNameE.insert(0, name)
        self.msgTypeE.set(type_)
        self.msgMainE.insert(1.0, msgMainText)
        self.msgTopic_IPE.configure(state='readonly')
        self.msgNameE.configure(state='readonly')
        self.msgMainE.configure(state='disabled')



    def reportMsg(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sel = self.msgListTree.selection()[-1]
        values = self.msgListTree.item(sel, 'values')
        ip,name,type_,topic,timeStamp,likeNum,ID = values
        msg = {
            'cmd':'report_message',
            'msgID':ID,
            'mac_address':mac_address
        }
        msgBytes = json.dumps(msg).encode('utf-8')
        s.sendto(msgBytes,('127.0.0.1', 23334))
        s.close()
        messagebox.showinfo('举报完成', '举报信已发送')
        

    def likeMsg(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sel = self.msgListTree.selection()[-1]
        values = self.msgListTree.item(sel, 'values')
        ip,name,type_,topic,timeStamp,likeNum,ID = values
        msg = {
            'cmd':'like_message',
            'msgID':ID,
            'mac_address':mac_address
        }
        msgBytes = json.dumps(msg).encode('utf-8')
        s.sendto(msgBytes,('127.0.0.1', 23334))
        s.close()
        messagebox.showinfo('点赞完成', '点赞已发送')

    def postMsg(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        topic = self.msgTopic_IPE.get()[:20]
        if len(topic)<5:
            messagebox.showerror('主题为空', '主题不能低于5个字')
            return
        name = self.msgNameE.get()[:20]
        if name == '':
            messagebox.showerror('昵称为空', '昵称不能为空')
            return
        type_ = self.msgTypeE.get()
        if type_ == '':
            messagebox.showerror('类型为空', '类型不能为空')
            return
        msgMain = self.msgMainE.get(1.0, 'end')[:200]
        if msgMain == '':
            messagebox.showerror('内容为空', '内容不能为空')
            return
        if not messagebox.askokcancel('确认发布', f'确认发布留言\n主题：{topic}\n昵称：{name}\n类型：{type_}\n内容：{msgMain}'):
            return
        msg = {
            'cmd':'post_message',
            'topic':self.msgTopic_IPE.get()[:20],
            'name':self.msgNameE.get()[:20],
            'type':self.msgTypeE.get()[:10],
            'detail_text':self.msgMainE.get(1.0, 'end')[:200],
            'mac_address':mac_address
        }
        msgBytes = json.dumps(msg).encode('utf-8')
        s.sendto(msgBytes,('127.0.0.1', 23334))
        
        s.settimeout(2)
        try:
            res = s.recv(1024)
            if b'ok' in res:
                messagebox.showinfo('发布完成', '留言已发送，请等待审核')
            else:
                messagebox.showinfo('发布失败', f'留言发送失败,{res.decode("utf-8", "ignore")}')
        except:
            messagebox.showinfo('发布失败', '留言发送失败，服务器无响应')
            pass
        s.close()

if __name__ == "__main__":
    root = tk.Tk()
    widget = MessageframeWidget(root)
    widget.pack(expand=True, fill="both")
    root.mainloop()

