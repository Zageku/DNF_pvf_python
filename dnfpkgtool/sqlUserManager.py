
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from . import sqlManager2 as sqlM
import threading

def inThread(func):
    def inner(*args,**kw):
        t = threading.Thread(target=lambda:func(*args,**kw))
        t.setDaemon(True)
        t.start()
        return t
    return inner

class SqluserframeWidget(ttk.Frame):
    def __init__(self, master=None, **kw):
        super(SqluserframeWidget, self).__init__(master, **kw)
        labelframe1 = ttk.Labelframe(self)
        labelframe1.configure(height=200, text='数据库用户', width=200)
        self.sqlUserTree = ttk.Treeview(labelframe1)
        self.sqlUserTree.configure(selectmode="extended", show="headings")
        self.sqlUserTree_cols = ['column1', 'column2']
        self.sqlUserTree_dcols = ['column1', 'column2']
        self.sqlUserTree.configure(
            columns=self.sqlUserTree_cols,
            displaycolumns=self.sqlUserTree_dcols)
        self.sqlUserTree.column(
            "column1",
            anchor="w",
            stretch=True,
            width=100,
            minwidth=20)
        self.sqlUserTree.column(
            "column2",
            anchor="w",
            stretch=True,
            width=100,
            minwidth=20)
        self.sqlUserTree.heading("column1", anchor="w", text='用户名')
        self.sqlUserTree.heading("column2", anchor="w", text='连接域')
        self.sqlUserTree.pack(expand=True, fill="both", side="top")
        self.sqlUserTree.bind("<<TreeviewSelect>>", self.show_sel_user, add="")
        labelframe1.pack(expand=True, fill="both", side="left")
        labelframe2 = ttk.Labelframe(self)
        labelframe2.configure(height=200, text='用户编辑', width=200)
        button1 = ttk.Button(labelframe2)
        button1.configure(text='新建用户', width=15)
        button1.pack(fill="x", side="top")
        button1.configure(command=self.new_user)
        button3 = ttk.Button(labelframe2)
        button3.configure(text='删除用户', width=15)
        button3.pack(fill="x", side="top")
        button3.configure(command=self.del_user)
        frame2 = ttk.Frame(labelframe2)
        frame2.configure(height=200, width=200)
        label1 = ttk.Label(frame2)
        label1.configure(text='用户名')
        label1.grid(column=0, row=0)
        self.sqlUserE = ttk.Combobox(frame2)
        self.sqlUserE.configure(values='game root')
        self.sqlUserE.grid(column=1, row=0)
        label2 = ttk.Label(frame2)
        label2.configure(text='主机IP')
        label2.grid(column=0, row=1)
        self.sqlUserIPE = ttk.Combobox(frame2)
        self.sqlUserIPE.configure(values='127.0.0.1 %-任意外网')
        self.sqlUserIPE.grid(column=1, row=1)
        label3 = ttk.Label(frame2)
        label3.configure(text='密码')
        label3.grid(column=0, row=2)
        self.sqlUserPWDE = ttk.Combobox(frame2)
        self.sqlUserPWDE.grid(column=1, row=2)
        button2 = ttk.Button(frame2)
        button2.configure(text='保存修改')
        button2.grid(column=0, columnspan=2, row=3, sticky="ew")
        button2.configure(command=self.save_user)
        frame2.pack(expand=True, side="top")
        labelframe2.pack(expand=False, fill="both", side="left")
        self.configure(height=200, width=200)
        self.pack(expand=True, fill="both", side="top")

    @inThread
    def get_all_users(self):
        self.sqlUserTree.delete(*self.sqlUserTree.get_children())
        sql = "select user, host from mysql.user"
        users = sqlM.execute_and_fetch('mysql',sql)
        for user in users:
            self.sqlUserTree.insert('', 'end', values=user)
        self.allUsers = users

    def show_sel_user(self, event):
        sels = self.sqlUserTree.selection()
        if not sels:
            return
        sel = sels[0]
        userName, host = self.sqlUserTree.item(sel)['values']
        #sql = f"select password from mysql.user where user='{userName}' and host='{host}'"
        #pwd = sqlM.execute_and_fetch('mysql',sql)[0][0]
        self.sqlUserE.set(userName)
        self.sqlUserIPE.set(host)
        self.sqlUserPWDE.set('')

    def new_user(self):
        self.sqlUserE.set('')
        self.sqlUserIPE.set('')
        self.sqlUserPWDE.set('')
        self.sqlUserTree.selection_set()
        pass

    @inThread
    def del_user(self):
        sels = self.sqlUserTree.selection()
        if not messagebox.askokcancel('删除用户', f'确认删除选中的{len(sels)}个用户？\n删除后可能导致无法连接数据库！'):
            return
        for sel in sels:
            userName, host = self.sqlUserTree.item(sel)['values']
            sql = f"drop user '{userName}'@'{host}'"
            sqlM.execute_and_commit('mysql',sql)
        self.get_all_users()
        
        messagebox.showinfo('删除用户', f'删除{len(sels)}个用户完成')

    @inThread
    def save_user(self):
        
        userName = self.sqlUserE.get()
        host = self.sqlUserIPE.get().split('-')[0].strip()
        pwd = self.sqlUserPWDE.get()
        if len(pwd) < 6:
            messagebox.showerror('保存用户', '密码长度不能少于6位')
            return
        if not userName or not host or not pwd:
            messagebox.showerror('保存用户', '用户名、主机IP、密码不能为空')
            return
        sels = self.sqlUserTree.selection()
        if not sels:    # 新建用户并赋予权限
            # 检查是否已经有同名用户
            sql = f"select user, host from mysql.user where user='{userName}' and host='{host}'"
            if sqlM.execute_and_fetch('mysql',sql):
                messagebox.showerror('保存用户', f'已经存在用户{userName}@{host}')
                return
            sql = f"create user '{userName}'@'{host}' identified by '{pwd}'"
            sqlM.execute_and_commit('mysql',sql)
            sql = f"grant all privileges on *.* to '{userName}'@'{host}' with grant option"
            sqlM.execute_and_commit('mysql',sql)

        else:   # 修改用户
            sel = sels[0]
            oldUserName, oldHost = self.sqlUserTree.item(sel)['values']
            if userName != oldUserName or host != oldHost:
                sql = f"rename user '{oldUserName}'@'{oldHost}' to '{userName}'@'{host}';"
                sqlM.execute_and_commit('mysql',sql)
            # get sql version
            sql = "select version()"
            version:str = sqlM.execute_and_fetch('mysql',sql)[0][0]
            if version.startswith('8'):
                sql = f"alter user '{userName}'@'{host}' identified WITH mysql_native_password by '{pwd}';"
            else:
                sql = f"set password for '{userName}'@'{host}' = password('{pwd}');"
            sqlM.execute_and_commit('mysql',sql)
            sql = f"grant all privileges on *.* to '{userName}'@'{host}' with grant option"
            sqlM.execute_and_commit('mysql',sql)
        self.get_all_users()
        # check if user has been created
        sql = f"select user, host from mysql.user where user='{userName}' and host='{host}'"
        if not sqlM.execute_and_fetch('mysql',sql):
            messagebox.showerror('保存用户', f'保存用户{userName}@{host}失败')
            return
        messagebox.showinfo('保存完成', f'成功保存用户{userName}@{host}')
        


if __name__ == "__main__":
    root = tk.Tk()
    widget = SqluserframeWidget(root)
    widget.pack(expand=True, fill="both")
    root.mainloop()

