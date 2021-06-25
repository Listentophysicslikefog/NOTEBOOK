#!/usr/bin/python
# -*- coding: UTF-8 -*-

import pymongo
import sys
import os
import time
import log_info
sys.path.append(
    os.path.abspath(os.path.join(__file__, '../../../../libs')))
import fastcall

global set_status
set_status = 10

global log
log = log_info.logger()

def get_db_ips(region_name):
    region_dir =fastcall.get_region_dir(region_name)
    db_file = os.path.join(region_dir, "access_db_info")
    f = open(db_file)
    db_info_lines = f.read().split("\n")
    f.close()
    db_ip_info_cols = db_info_lines[1].split()
    db_ips = []
    i = 0
    while i < len(db_ip_info_cols):
        if fastcall.checkip(db_ip_info_cols[i]):
            db_ips.append(db_ip_info_cols[i])
        i = i + 1
    return db_ips
def get_db_port(region_name):
    region_dir =fastcall.get_region_dir(region_name)
    db_file = os.path.join(region_dir, "access_db_info")
    f = open(db_file)
    db_info_lines = f.read().split("\n")
    f.close()
    db_port_info_cols = db_info_lines[2].split()
    if len(db_port_info_cols) < 2:
        return None
    else:
        return int(db_port_info_cols[1])

def get_db_name(region_name):
    region_dir = fastcall.get_region_dir(region_name)
    db_file = os.path.join(region_dir, "access_db_info")
    f = open(db_file)
    db_info_lines = f.read().split("\n")
    f.close()
    db_name_info_cols = db_info_lines[3].split()
    if len(db_name_info_cols) < 2:
        return None
    else:
        return db_name_info_cols[1]

def get_set_status(region_name, set_id):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()

    db_ips = get_db_ips(region_name)
    db_port = get_db_port(region_name)
    db_name = get_db_name(region_name)
    
    info ="region_name: " + region_name + " set_id: " + str(set_id) + " access ip : " + str(db_ips) + "  port : " + str(db_port) + " db_name : " + str(db_name)
    log_inf.info(info)
    client = pymongo.MongoClient(db_ips[0], db_port)
    access_db = client[db_name]
    # 获取set的状态
    set_info = list(access_db["t_set_info"].find({"id": int(set_id)}))
    if len(list(set_info)) != 1:
        err = "region : " + str(region_name) + " set_id : " + str(set_id) + " not in access db or len(list(set_info)) :  " + str(len(list(set_info)))  + "!= 1 ,  access ip : " + str(db_ips) + "  port : " + str(db_port) + " db_name : " + str(db_name)
        log_err.error(err)
        return -1
    status_info = "region :" + str(region_name) + " set :" + str(set_id) +  "  set status:" + str(set_info[0]["state"]) #set_info.count()
    log_inf.info(status_info)

    #print "setinfo ",set_info[0]["commits"]
    #print(type(set_info[0]["state"]))
    get_status = set_info[0]["state"]
    client.close()
    if set_status != 10 and set_status != 0 and set_status != 20: 
        err = "set status error, status is :" + str(set_status)
        log_err.error(err)
        return -1      
    return get_status

def change_set_status(region_name, set_id, change_state):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()

    db_ips = get_db_ips(region_name)
    db_port = get_db_port(region_name)
    db_name = get_db_name(region_name)
    client = pymongo.MongoClient(db_ips[0], db_port)
    access_db = client[db_name]
    # 获取set的状态
    set_info = list(access_db["t_set_info"].find({"id": int(set_id)}))
    print_info = "region :" +  region_name + " set :" + str(set_id) +  " set status:" + str(set_info[0]["state"]) + " want change state to: "+ str(change_state)
    log_inf.info(print_info)
    if len(list(set_info)) != 1:
        err = "region : " + str(region_name) + " set_id : " + str(set_id) + " not in access db or len(list(set_info)) :  " + str(len(list(set_info)))  + "!= 1 ,  access ip : " + str(db_ips) + "  port : " + str(db_port) + " db_name : " + str(db_name)
        log_err.error(err)
        client.close()
        return -1
    if set_info[0]["state"] == int(change_state) or int(change_state) == int(20):
        # set状态和需要更改的状态一样 或者是测试set或者该set没有在limax上面
        info = "not need change state.  region: " + region_name + "  set: " + str(set_id) + " status: " + str(set_info[0]["state"]) + " want change state to: " + str(change_state)
        log_inf.info(info)
        client.close()
        return 0
    if int(change_state) == 0:
        # 打开set
        access_db["t_set_info"].update({"id": int(set_id),"state":set_info[0]["state"]},{'$set':{"state":0}})
        info = "open set.  region: " + region_name + "  set: " + str(set_id) + " status: " + str(set_info[0]["state"]) + " want change state to: " + str(change_state)
        log_inf.info(info)
        client.close()
        return 0
    if int(change_state) == 10:
        # 关闭set
        access_db["t_set_info"].update({"id": int(set_id),"state":set_info[0]["state"]},{'$set':{"state":10}})
        info = "close set.  region: " + region_name + "  set: " + str(set_id) + " status: " + str(set_info[0]["state"]) + " want change state to: " + str(change_state)
        log_inf.info(info)
        client.close()
        return 0
    else: #报错
        err = "you want change state to: " + str(set_status) + " , no such state"
        log_err.error(err)
        client.close()
        return -1

def help():
    print sys.argv[0] + " [region] [set] [set_new_state] or [region] [set]"


def main():
    if len(sys.argv[1:]) < 2:
        help()
        sys.exit(1)

    region_name = sys.argv[1]
    set_name = sys.argv[2]
    #set_new_state = sys.argv[3]
    #ip = get_db_ips(region_name)
    #name = get_db_name(region_name)
    #port = get_db_port(region_name)
    re= get_set_status("hn02",3212)
    print(re)
    print(type(re))
    #re= change_set_status("hn02", 3212, 0)
    print re
    #re= get_set_status("hn02",3212)
    print(re)
    print(type(re))
    global set_status
    #print "\n\nregion all set recent clone task lc count: ", set_status, ip, port, name


if __name__ == "__main__":
    main()
