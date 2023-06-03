import tkinter as tk
import tkinter.ttk as ttk


class CreatureframeWidget(tk.Frame):
    def __init__(self, master=None, **kw):
        super(CreatureframeWidget, self).__init__(master, **kw)
        self.invBowserFrame = tk.LabelFrame(self)
        self.invBowserFrame.configure(height=200, text='当前物品列表', width=200)
        frame2 = ttk.Frame(self.invBowserFrame)
        frame2.configure(height=200, width=200)
        self.treeViewFrame = ttk.Frame(frame2)
        self.treeViewFrame.configure(height=200, width=200)
        self.itemsTreev_now = ttk.Treeview(self.treeViewFrame)
        self.itemsTreev_now.configure(selectmode="extended", show="headings")
        self.itemsTreev_now_cols = ['column1', 'column2', 'column5', 'column6']
        self.itemsTreev_now_dcols = [
            'column1', 'column2', 'column5', 'column6']
        self.itemsTreev_now.configure(
            columns=self.itemsTreev_now_cols,
            displaycolumns=self.itemsTreev_now_dcols)
        self.itemsTreev_now.column(
            "column1",
            anchor="center",
            stretch="true",
            width=40,
            minwidth=20)
        self.itemsTreev_now.column(
            "column2",
            anchor="center",
            stretch="true",
            width=120,
            minwidth=20)
        self.itemsTreev_now.column(
            "column5",
            anchor="center",
            stretch="true",
            width=80,
            minwidth=20)
        self.itemsTreev_now.column(
            "column6",
            anchor="center",
            stretch="true",
            width=80,
            minwidth=20)
        self.itemsTreev_now.heading("column1", anchor="center", text=' ')
        self.itemsTreev_now.heading("column2", anchor="center", text='宠物名')
        self.itemsTreev_now.heading("column5", anchor="center", text='物品ID')
        self.itemsTreev_now.heading("column6", anchor="center", text='昵称')
        self.itemsTreev_now.pack(expand="true", fill="both", side="left")
        self.itemsTreev_bar = ttk.Scrollbar(self.treeViewFrame)
        self.itemsTreev_bar.configure(orient="vertical")
        self.itemsTreev_bar.pack(fill="y", side="right")
        self.treeViewFrame.pack(expand="true", fill="both", side="top")
        self.blobFuncFrame = ttk.Frame(frame2)
        self.blobFuncFrame.configure(height=200, width=200)
        self.deleteBtn = ttk.Button(self.blobFuncFrame)
        self.deleteBtn.configure(text='删除选中')
        self.deleteBtn.pack(expand="true", fill="x", side="left")
        self.deleteBtn.configure(command=self.ask_delete)
        self.blobFuncFrame.pack(fill="x", side="top")
        frame2.pack(expand="true", fill="both", side="top")
        self.invBowserFrame.pack(expand="true", fill="both", side="left")
        self.configure(height=200, width=200)
        self.pack(expand="true", fill="both", side="top")

    def ask_delete(self):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    widget = CreatureframeWidget(root)
    widget.pack(expand=True, fill="both")
    root.mainloop()
