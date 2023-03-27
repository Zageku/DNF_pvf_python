# DNF_pvf_python
![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/ico.png)

DNF台服pvf以及数据库背包blob字段读取。dnf背包清理工具。

本工具用于编辑角色背包，搜索PVF物品，强制穿戴装备，时装潜能开启，时装删除宠物删除，武器强化锻造增幅，4词条魔法封印编辑，角色改名，角色转职觉醒，角色升级降级，以及自动查询替换PVF后导致的背包内炸角色物品。
 
# 食用说明

### 1、文件目录：

解压文件包，除开可执行EXE文件，目录分别代表：

1、config配置文件，里面有github图片、首页和角色信息页的图片、魔法封印、物品信息、职业信息以及本地pvf读取缓存；

2、log日志文件，可以存储软件执行过程中的一部分日志；

3、python源代码及执行环境，里面有完整的python运行开发环境，如果有需求且有一定的代码能力，可以直接编写文件夹内的GUI.py修改程序。

![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/52.png)



### 2、数据库连接与角色搜索

软件运行后，上方为数据库连接信息。点击链接后至多会有3个连接器实现对数据库的连接。

当一个连接器都连不上时，会提示数据库连接失败。

当角色列表出现乱码等问题时，可以通过切换连接器和修改编码来调整。默认会自动选择一个能够正常解码的选项。

当编码不能正常解析时，修改角色信息可能会导致角色名错误，在游戏内使用改名卡即可。


#### 数据来源

读取本地CSV或者PVF文件来作为数据参考。

CSV提取自台服dnf吧一键端（2022）。

当没有加载PVF时，无法使用道具专用搜索和装备专用搜索。

PVF文件读取后会在config目录创建本地缓存pvf.cache，不同的PVF根据MD5值加以区分，同一个PVF在不同目录也是不会重复读取的。

读取后，可以通过最下方的选择框选择PVF。
 
![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/72.png)

### 3、物品编辑与备份

在标签页“物品栏”、“穿戴栏”、“宠物栏”、“仓库”四个页面中，可以对所持有的物品进行详细编辑修改，也可使用导出字段/导入字段的方式保存对应数据到本地文件或将本地文件上传至服务端。

当加载角色背包或修改背包内容时，会自动检测背包中是否有当前PVF所不能识别或者状态与PVF冲突的物品，并加以颜色区分标注。

红色：与PVF冲突；

黄色：物品种类未知或不存在该物品；

灰色：编辑后删除的物品；

蓝色：编辑过的物品。

当选择为装备时，可以使用右侧编辑面板的所有功能，包括强化锻造、修改魔法封印等。

此外，可以通过生成字节，复制字节后粘贴到别的位置导入的方式复制物品，也可以用这个方法强制穿戴角色本身无法穿戴的装备。

![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/77.png)

### 4、高级搜索

道具高级搜索和装备高级搜索。

可以通过名称、PVF文本、物品分类对道具和装备进行详细搜索。

可以使用空格分隔多个关键词配合模糊来对物品信息搜索。

例如开启模糊搜索+关键词 “冷却减 出血” 表示同时存在 “冷xx却xx减” 和 “出xx血”的物品；

关闭模糊搜索，指代同时存在 “冷却减” 和 “出血”的物品。

选中搜索PVF文本，会同时搜索所有物品的PVF信息，否则只对物品名进行搜索。

搜索完成后选中结果可以显示物品的PVF信息，点击提交可以直接将搜索结果填充至当前页面的物品编辑栏中。
 
![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/55.png)

 

### 5、时装宠物邮件

这两个页面功能很少，宠物和邮件只能删除，时装可以开启时装潜能。选项可以通过按住ctrl或shift进行多选，支持左右键拖拽来添加删除。

删除与修改前会提示是否确定进行操作。
 
![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/56.png)

![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/57-1.png)
 
### 6、角色信息编辑

可以升级降级，可以改名，可以转职觉醒。

改名成功与否取决于数据库是否出现重名问题，以及数据库是否能够正确识别编码。

当名称超过长度（20字节）则会自动裁剪。

可以在名字前面加空格，但是后面加的空格会被去除。

左侧为额外功能区，一键启动器可以在登陆游戏的情况下自动生成，之后使用启动器可以不用输入账号密码直接进入游戏；PVF缓存编辑器可以对已经缓存的PVF缓存进行编辑或数据导出，本脚本使用的CSV也可使用该功能导出。

右侧点击是我的GitHub项目主页，有条件的朋友帮忙点个星星，二次开发的朋友务必点个叉子，每一份的支持都是免费开源软件继续发展的动力。

![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/79.png)

![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/73.png)

![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/74.png)

### 7、GM工具

基本的GM工具集，可以充值点数、发送邮件、开关活动和服务器的一键启动停止，支持自定义指令执行。

在加载PVF后，邮件可自动区分宠物邮件时装邮件。

![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/03.png)

![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/04.png)

![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/05.png)

![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/06.png)

![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/07.png)

### 8、PVF工具

可简单对PVF进行修改，例如道具属性、装备属性和整体爆率。

![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/111.png)

![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/112.png)

![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/113.png)

![Image text](https://github.com/Zageku/DNF_pvf_python/raw/main/images/114.png)


