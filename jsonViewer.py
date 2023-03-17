# Credit to https://stackoverflow.com/a/22722889/122364
import uuid
import tkinter as tk
from tkinter import ttk



def json_tree(tree:ttk.Treeview, parent, dictionary,depth=-1):
    if depth==0:
        return True
    for key in dictionary:
        uid = uuid.uuid4()
        if isinstance(dictionary[key], dict):
            try:
                if dictionary[key].get('[name]') is not None:
                    values = dictionary[key].get('[name]')
                else:
                    values = str(list(dictionary[key].keys()))
                tree.insert(parent, 'end', uid, text=key,values=[values],tags='dir')
            except:
                tree.insert(parent, 'end', uid, text=key,values=['ERROR'],tags='dir')
            json_tree(tree, uid, dictionary[key],depth-1)
        elif isinstance(dictionary[key], list) or isinstance(dictionary[key],tuple):
            try:
                tree.insert(parent, 'end', uid, text=str(key) + '[]',values=[str(dictionary[key])])
            except:
                tree.insert(parent, 'end', uid, text=str(key) + '[]',values=['ERROR'])
            json_tree(tree,
                      uid,
                      dict([(i, x) for i, x in enumerate(dictionary[key])]),
                      depth=depth-1)
        else:
            value = dictionary[key]
            #print(value)
            if value is None:
                value = 'None'
            try:
                tree.insert(parent, 'end', uid, text=str(key), value=[value],tags='value')
            except:
                tree.insert(parent, 'end', uid, text=str(key), value=['ERROR'],tags='value')



def show_data(data):
    def fixed_map(option):
        return [elm for elm in style.map('Treeview', query_opt=option) if
        elm[:2] != ('!disabled', '!selected')]

    style = ttk.Style()
    style.map('Treeview', foreground=fixed_map('foreground'),
    background=fixed_map('background'))
    # Setup the root UI
    root = tk.Tk()
    root.title("JSON viewer")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # Setup the Frames
    tree_frame = ttk.Frame(root, padding="3")
    tree_frame.grid(row=0, column=0, sticky=tk.NSEW)

    # Setup the Tree
    tree = ttk.Treeview(tree_frame, columns='Values')
    tree.column('Values', width=100, anchor='center')
    tree.heading('Values', text='Values')
    tree.tag_configure('dir', background='lightblue')
    json_tree(tree, '', data)
    tree.pack(fill=tk.BOTH, expand=1)

    # Limit windows minimum dimensions
    root.update_idletasks()
    root.minsize(500, 800)
    root.mainloop()

if __name__=='__main__':
    d = {
        '123213':{123:'asdasd'},
        123333:{'ddddd':111},
        'list':[1,2,3,4,5]
    }
    show_data(d)