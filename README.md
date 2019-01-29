# pysphere-esxi-control
## Requirements

Python2.7 & PySphere

## Usages
```$ python ./pySimpleVmCtrl.py --help
usage: pySimpleVmCtrl.py [-h] [-v] [-H HOST] [-U USER] [-P PASSWD] [-A ACTION]
                         [-g GUEST] [--store DATASTORE] [--net NETWORK]
                         [--disk DISKSIZE] [--cpu CPU] [--mem MEMORY]
                         [--os OPERATINGSYSTEM]

examples:
# list available datastores and networks and guests on ESXi host 192.168.1.2
python ./pySimpleVmCtrl.py -H 192.168.1.2 -U root -P password -A list-host -A list-guest

# create a guest called test-01
python ./pySimpleVmCtrl.py -H 192.168.1.2 -U root -P password -A create \
         --disk 40 --store "[MainDS]" --cpu 2 --mem 4096 --net LAN -g test-01

# power on guest test-01
python ./pySimpleVmCtrl.py -v -H 192.168.1.2 -U root -P password -A on -g test-01

Arguments:

optional arguments:
  -h, --help            show this help message and exit
  -v                    be verbose [False]
  -H HOST               hostname esxi server [localhost]
  -U USER               username to connect to esx [root]
  -P PASSWD             password [read from stdin]
  -A ACTION             what to do [list-host|list-guest|off|on|reboot|del|create]
  -g GUEST              Guest virtual machine name
  --store DATASTORE     (create) datastore to use
  --net NETWORK         (create) network to connect to
  --disk DISKSIZE       (create) disksize in GB [8]
  --cpu CPU             (create) cpu count [1]
  --mem MEMORY          (create) memory in MB [1024]
  --os OPERATINGSYSTEM  (create) Operating system [rhel6_64Guest]
```
