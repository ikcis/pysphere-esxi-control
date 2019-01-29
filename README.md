# pysphere-esxi-control

ESXiGuest.py实现ESXiGuestClass用户类，针对用户对虚拟机的操作，如有快闪，开机，关机，重启等方法

ESXiHost.py实现ESXiHostClass服务端类，有登陆连接服务器，配置信息查看等方法

pySimpleVmCtrl.py实现命令行格式，命令行会调用用户类和服务端类的方法，用于终端命令行输入来访问，操作服务器。
