#!/usr/bin/env python 
#encoding=utf-8
import socket 
import subprocess
import time
import os 
import  commands
import log_info
global global_lock_dir
global_lock_dir = "/root/ymer_deploy_lock"
global log
log = log_info.logger()

def create_file(filename):
    path = "/root/ymer_deploy_lock"
    if not os.path.isdir(path):  # 无文件夹时创建
        os.makedirs(path)
    if not os.path.isfile(filename):  # 无文件时创建
        fd = open(filename, mode="w")
        fd.close()
    else:
        pass
def remove_lock_file(file_name):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    rm_file_cmd = "cd /root/ymer_deploy_lock;" + "rm -rf ./" + str(file_name)
    (status, output) = commands.getstatusoutput(rm_file_cmd)
    if status != 0:
        err = "failed to delete faile." + " path: " + str(global_lock_dir)  + ", file name :" + str(file_name) + " status: "+ str(status) + ", cmd: "+ str(rm_file_cmd)
        log_err.error(err)
        return -1
    info = "delete file success. " + " path: " + str(global_lock_dir)  + ", file name :" + str(file_name)
    log_inf.info(info)
    return 0

def check_lock_file():
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    myname = socket.getfqdn(socket.gethostname())
    myip = socket.gethostbyname(myname)
    (status, output) = commands.getstatusoutput('ls /root/ymer_deploy_lock')
    if status != 0:
        err = "failed to get ymer global deploy lock, status: "+ str(status) + ", cmd: "+ str(cmd)
        log_err.error(err)
        return -1
    print status, output
    output.strip()
    files = "ymer-deploy-" +  str(myname) + "-" + str(myip) + ".lock"
    print output == files


def check_deploy_environment(region):
    global global_lock_dir
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    # 1. 检测发布管理机器是否和需要发布的region一样
    host_name = socket.getfqdn(socket.gethostname())
    host_ip = socket.gethostbyname(host_name)
    region_name = str(region) + "-udisk-support"
    #region_name = "udisk-testmanager"
    if region_name != host_name:
        err = "The publishing management machine is different from the region to be published. " + " region name: " + str(region_name) + "  publish machine: " + str(host_name) + " publish machine ip:" + str(host_ip)
        log_err.error(err)
        return -1,None,None,None
    # 2. 先检测是否有lock 是否有ymer发布
    if not os.path.isdir(global_lock_dir):
        os.makedirs(global_lock_dir)
    check_lock_cmd = "ls /root/ymer_deploy_lock | wc -l"
    (status, output) = commands.getstatusoutput(check_lock_cmd)
    if status != 0:
        err = "failed first to check ymer generate lock, status: "+ str(status) + ", cmd: "+ str(check_lock_cmd)
        log_err.error(err)
        return -1,None,None,None
    
    if int(output.strip()) != 0:
        err = "this publish machine already in release ymer. region name: " + str(region_name) + "  publish machine: " + str(host_name) + " publish machine ip:" + str(host_ip) + " path :" + global_lock_dir
        log_err.error(err)
        return -1,None,None,None
    # 3. 创建ymer发布的lock文件
    t = time.time()
    lock_file_name = "ymer-deploy-" +  str(host_name) + "-" + str(long(t)) + ".lock"
    #myname = socket.getfqdn(socket.gethostname())
    #myip = socket.gethostbyname(myname)
    ymer_lock = global_lock_dir + "/" + lock_file_name
    create_file(ymer_lock)
    # 4. 检测lock文件是否创建成功
    check_lock_file_cmd = " ls /root/ymer_deploy_lock | grep " + str(lock_file_name) + "| wc -l" 
    (status, output) = commands.getstatusoutput(check_lock_file_cmd)
    if status != 0:
        err = "failed to get lock file.  status: "+ str(status) + ", cmd: "+ str(check_lock_file_cmd)
        log_err.error(err)
        return -1,None,None,None
    if int(output.strip()) != 1:
        err = " maybe create lock file failed. file name: " + str(lock_file_name) + "  cmd: " + str(check_lock_file_cmd)
        log_err.error(err)
        return -1,None,None,None
    # 5. 等待2s后再检测lock的数量，避免存在同时创建lock file导致检测不准确
    time.sleep(2)
    second_check_lock_cmd = "ls /root/ymer_deploy_lock | wc -l"
    (status, output) = commands.getstatusoutput(second_check_lock_cmd)
    if status != 0:
        err = " failed second to check ymer generate lock, status: "+ str(status) + ", cmd: "+ str(second_check_lock_cmd)
        log_err.error(err)
        return -1,None,None,None
    if int(output.strip()) != 1:
        err = "second check this publish machine maybe already in release ymer.  region name: " + str(region_name) + "  publish machine: " + str(host_name) + " publish machine ip:" + str(host_ip) + " path :" + global_lock_dir
        log_err.error(err)
        return -1,None,None,None
    info = "check ymer generate  environment and lock success, will start generate ymer"
    log_inf.info(info)
    return 0,str(host_name),str(host_ip),str(lock_file_name)
    
def test(region):
    rc,host_name,host_ip,lock_name = check_deploy_environment(region)
    #rc = check_deploy_environment(region)
    if rc != 0:
        print "error"
    print rc,host_name,host_ip,lock_name
    #print remove_lock_file(lock_name)
if __name__ == "__main__":
    #check_deploy_environment("hn02")
    test("hn02")
