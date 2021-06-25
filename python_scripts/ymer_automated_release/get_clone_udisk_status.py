#!/usr/bin/python
# -*- coding: UTF-8 -*-
import pymongo
import sys
import os
import time
import log_info 
global log
log = log_info.logger()
def get_clone_disk_info(region_name, set_name, disk_id):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    set_dir = None
    if os.environ.has_key("LIMAX_DIR"):
        set_dir = os.path.join(os.environ["LIMAX_DIR"], "udisk", "region",
                               region_name, str(set_name))
    else:
        set_dir = os.path.join(os.environ["HOME"], "limax", "udisk", "region",
                               region_name, str(set_name))
    if not os.path.exists(set_dir):
        err = "region_name: "+ region_name + "  set_dir %s not found", set_dir
        log_err.error(err)
        return -1,-1
    db_file = os.path.join(set_dir, "db_info")
    db_info = open(db_file).read()
    db_info_lines = db_info.split("\n")
    db_ip_info = db_info_lines[1]
    db_ip_info_cols = db_ip_info.split()
    db_ips = [db_ip_info_cols[1], db_ip_info_cols[2]]
    db_port_info = db_info_lines[2]
    db_port = int(db_port_info.split()[1])
    db_name = db_info_lines[3].split()[1]
    
    client = pymongo.MongoClient(db_ips[0], db_port)
    udisk_db = client[db_name]
    cloning_udisk = list(udisk_db["t_clone_task"].find({"dst_extern_id":disk_id}))
    #print len(cloning_udisk[0]), len(list(cloning_udisk))
    if len(list(cloning_udisk)) != 1:
        err="region :" + region_name + " set: "+ set_name + "dst_extern_id : "+ disk_id + " not exit or not insert to db, get len is: " + str(len(list(cloning_udisk))) + ", info is :"+ str(cloning_udisk[0])
        log_err.error(err)
        return -1,-1
    if len(list(cloning_udisk)) == 1:
        status_info = "clone lcs: " + str(cloning_udisk[0]["dst_extern_id"]) + "status: " + str(cloning_udisk[0]["status"])
        log_inf.info(status_info)
        return int(cloning_udisk[0]["status"]),0 
def check_clone_result(region_name, set_name, disk_id):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    for i in range(66):
        time.sleep(5)
        status,rc= get_clone_disk_info(region_name, set_name, disk_id)
        if rc != 0:
            err = "region :" + region_name + " set: "+ set_name + "dst_extern_id : "+ disk_id +", get disk status error, check count is : " + str(i)
            log_err.error(err)
            return -1
        if status == 1:
            err = "region :" + region_name + " set: "+ set_name + "dst_extern_id : "+ disk_id + ", clone udisk failed, please check exactlly"
            log_err.error(err)
            return -1
        elif status == 0:
            info = "region :" + region_name + " set: "+ set_name + " dst_extern_id : "+ disk_id + ", disk is cloning , the next get udsik clone status after 5 seconds"
            log_inf.info(info)
        elif status == 2:
            info = "region: " + region_name + "  set_id: " + str(set_name) +  " ubs_id: " + disk_id + " clone success"
            log_inf.info(info)
            return 0
        else:
            err = "region :" + region_name + " set: "+ set_name + "dst_extern_id : "+ disk_id + ", not get udisk clone status or get status failed"
            log_err.error(err)
            return -1
    err = "region :" + region_name + " set: "+ set_name + "dst_extern_id : "+ disk_id + ", during 66*5s clone not success,maybe clone failed"
    log_err.error(err)
    return -1

def help():
    print "please use: " + sys.argv[0] + " [region] [set]  [extern_id]"
def main():
    if len(sys.argv[1:]) != 3:
        help()
        return -1
        sys.exit(1)
    region_name = sys.argv[1]
    set_name = sys.argv[2]
    disk_id = sys.argv[3]
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    for i in range(66):
        time.sleep(5)
        status,rc= get_clone_disk_info(region_name, set_name, disk_id)
        if rc != 0:
            err = "region :" + region_name + " set: "+ set_name + "dst_extern_id : "+ disk_id +", get disk status error, check count is : " + str(i) 
            log_err.error(err)
            return -1
        if status == 1:
            err = "region :" + region_name + " set: "+ set_name + "dst_extern_id : "+ disk_id + ", clone udisk failed, please check exactlly"
            log_err.error(err)
            return -1
        if status == 0:
            info = "region :" + region_name + " set: "+ set_name + "dst_extern_id : "+ disk_id + ", disk is cloneing , the next get udsik clone status after 5 seconds" 
            log_inf.info(info)
        if status == 2:
            print("clone success")
            return 0
        else:
            err = "region :" + region_name + " set: "+ set_name + "dst_extern_id : "+ disk_id + ", not get udisk clone status or get status failed"
            return -1
    err = "region :" + region_name + " set: "+ set_name + "dst_extern_id : "+ disk_id + ", during 66*5s clone not success,maybe clone failed"
    log_err.error(err)
    return -1    

def test():
    ret = check_clone_result("hn02", 3101, "hongwei_ymer_test")
    print ret
if __name__ == "__main__":
    #main()
    test()
