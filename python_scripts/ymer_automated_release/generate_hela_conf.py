#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import pymongo
import subprocess
import re
reload(sys)
sys.setdefaultencoding('utf-8')
import commands
sys.path.append(
  os.path.abspath(os.path.join(__file__, '../../../libs')))
import fastcall
from log_info import logger

check_items = ["my_name", "set", "umongo", "metaserver",
               "listen_ip", "listen_port", "path", "server"]
global log
 
log = logger()

def help():
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    warn = sys.argv[0] + " Usage: <region> <set> <tcp/rdma> <raw/fs> <sata/ssd>>"
    log.warning(warn)
    #print (sys.argv[0] + "a Usage: <region> <set> <tcp/rdma> <raw/fs> <sata/ssd>>")
    return -1

def checkip(ip):
    p = re.compile(
        '^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    if p.match(ip):
        return True
    else:
        return False


def checkdiff(old_diff, new_diff):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    old_conf_map = {}
    for line in old_diff:
        if line.find("=") != -1:
            conf_key = line.split('=')[0].strip()
            conf_value = line.split('=')[1].strip()
            old_conf_map[conf_key] = conf_value
    for line in new_diff:
        if line.find("=") != -1:
            conf_key = line.split('=')[0].strip()
            conf_value = line.split('=')[1].strip()
            if conf_key in check_items and old_conf_map.has_key(conf_key):
                if conf_value != old_conf_map[conf_key]:
                    err = "%s is different, old: %s, new: %s" % (conf_key, old_conf_map[conf_key], conf_value)
                    log_err.error(err)
                    return False
    return True

def check_remote_dir_exist(hela_ip):
    cmd = 'ssh root@%s ls /root/udisk/hela/conf/ | grep hela.conf | wc -l' % (hela_ip)
    hela_dir_num = int(os.popen(cmd).readlines()[0].strip())
    if hela_dir_num > 0:
        return True
    else:
        return False


def generate_config(region, set_id, net_type, storage_type, disk_type):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    #region = sys.argv[1]
    #set_id = sys.argv[2]
    #net_type = sys.argv[3]
    #storage_type = sys.argv[4]
    #disk_type = sys.argv[5]

    zookeeper_server = fastcall.get_zookeeper_servers(region, set_id)
    if zookeeper_server == None:
        err = "get zookeeper server fail, region: " + region + " set_id:" + set_id
        log_err.error(err)
        return -1
    conf_file_dir = "_".join([net_type, storage_type, disk_type])
    conf_file_name = os.path.join(os.environ['HOME'], "limax", "udisk",
                                  "release", conf_file_dir, "hela.conf")

    if os.path.exists(conf_file_name) == False:
        err = conf_file_name + " not exists, we should use this config generate new config"
        log_err.error(err)
        return -1
    configuration = open(conf_file_name, 'r').read()

    host_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                             "region", region, set_id, "host_info")

    if not os.path.exists(host_file):
        err ="region: " + region  + " set_id: " + set_id + " host_file: " + host_file + "not exit"
        log_err.error(err)
        return -1
    host_info = open(host_file).read().split("\n")
    p2p_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                           "region", region, set_id, "p2p_info")
    if not os.path.exists(p2p_file):
        err = "this set not p2p, no need to deploy hela, ymer not supprted for %s %s" % (region, set_id)
        log_err.error(err)
        return -1
    find_new_conf_dir = "./middle_file/" + region + "-"+ set_id 
    if not os.path.exists(find_new_conf_dir):
        os.makedirs(find_new_conf_dir)
    instance = 0
    for host in host_info:
        host = host.strip()
        if checkip(host) == False:
            continue
        inf = "=====>>>> generate hela config for hela_ip: " + host
        log_inf.info(inf)
        new_conf = str(configuration)
        new_conf = new_conf.replace("$instance", str(instance), 10)
        new_conf = new_conf.replace("$set", "set"+set_id, 10)
        new_conf = new_conf.replace("$server", zookeeper_server, 10)
        new_conf = new_conf.replace("$listen_ip", host, 10)
        new_conf_file_name = "./middle_file/" + region + "-"+ set_id  + "/hela.conf"
        new_conf_file = open(new_conf_file_name, 'w')
        new_conf_file.write(new_conf)
        new_conf_file.close()

        hela_dir_exist = check_remote_dir_exist(host)
        cmd = ""
        if hela_dir_exist:
            cmd = "ssh root@%s \"mkdir -p /root/udisk/hela;mkdir -p /root/udisk/hela/conf/;mv /root/udisk/hela/conf/hela.conf /root/udisk/hela/conf/hela.conf.bak\"" % (
                host)
        else:
            cmd = "ssh root@%s \"mkdir -p /root/udisk/hela;mkdir -p /root/udisk/hela/conf/;mkdir -p /var/log/udisk/hela\"" % (host)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()
        status = pipe.returncode
        if status != 0:
            err = "Failed to backup hela conf ip: "+  host + "  cmd: "+ cmd
            log_err.error(err)
            return -1
        cmd = "scp %s root@%s:/root/udisk/hela/conf/hela.conf" % (
            new_conf_file_name, host)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()
        status = pipe.returncode
        if status != 0:
            err = "Failed to scp hela conf ip: " +  host + "  cmd: " + cmd
            log_err.error(err)
            return -1
        # diff不同
        if hela_dir_exist:
            cmd = "ssh root@%s \"diff /root/udisk/hela/conf/hela.conf.bak /root/udisk/hela/conf/hela.conf | grep -E '<|>'\"" % (host)
            pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            output = pipe.communicate()
            status = pipe.returncode
            if status != 0 and status != 1:
                err ="cmd: " + cmd +  ", diff failed, status: " + status
                log_err.error(err)
                return -1
            old_diff = []
            new_diff = []
            for line in output[0].split('\n'):
                if len(line) < 2:
                    continue
                if line[0] == '<':
                    old_diff.append(line[1:])
                if line[0] == '>':
                    new_diff.append(line[1:])
            all_diff_info = "old diff is < , new diff is > , all diff info: \n" + str(output[0])
            log_inf.info(all_diff_info)
            if checkdiff(old_diff, new_diff) == False:
                err = "check config diff failed, please check diff detail"
                log_err.error(err)
                return -1
        instance += 1
    return 0










def main():
    if len(sys.argv[1:]) < 5:
        help()
        return -1
        sys.exit()
    log = logger()
    region = sys.argv[1]
    set_id = sys.argv[2]
    net_type = sys.argv[3]
    storage_type = sys.argv[4]
    disk_type = sys.argv[5]

    zookeeper_server = fastcall.get_zookeeper_servers(region, set_id)

    conf_file_dir = "_".join([net_type, storage_type, disk_type])
    conf_file_name = os.path.join(os.environ['HOME'], "limax", "udisk",
                                  "release", conf_file_dir, "hela.conf")

    if os.path.exists(conf_file_name) == False:
        err = conf_file_name + " not exists"
        log_err.error(err)
        print conf_file_name + " not exists"
        return -1
        sys.exit()
    configuration = open(conf_file_name, 'r').read()

    host_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                             "region", region, set_id, "host_info")
    host_info = open(host_file).read().split("\n")
    p2p_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                           "region", region, set_id, "p2p_info")
    if not os.path.exists(p2p_file):
        err = "ymer not supprted for %s %s" % (region, set_id)
        log_err.error(err)
        print("ymer not supprted for %s %s" % (region, set_id))
        return -1
        sys.exit()    
    instance = 0
    for host in host_info:
        host = host.strip()
        if checkip(host) == False:
            continue
        inf = "=====>>>> generate hela config for hela_ip: " + host
        log_inf.info(inf)
        print("=====>>>> generate hela config for hela_ip: " + host)
        new_conf = str(configuration)
        new_conf = new_conf.replace("$instance", str(instance), 10)
        new_conf = new_conf.replace("$set", "set"+set_id, 10)
        new_conf = new_conf.replace("$server", zookeeper_server, 10)
        new_conf = new_conf.replace("$listen_ip", host, 10)
        new_conf_file_name = "hela.conf"
        new_conf_file = open(new_conf_file_name, 'w')
        new_conf_file.write(new_conf)
        new_conf_file.close()

        hela_dir_exist = check_remote_dir_exist(host)
        if hela_dir_exist:
            cmd = "ssh root@%s \"mkdir -p /root/udisk/hela;mkdir -p /root/udisk/hela/conf/;mv /root/udisk/hela/conf/hela.conf /root/udisk/hela/conf/hela.conf.bak\"" % (
                host)
        else:
            cmd = "ssh root@%s \"mkdir -p /root/udisk/hela;mkdir -p /root/udisk/hela/conf/;mkdir -p /var/log/udisk/hela\"" % (host)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()
        status = pipe.returncode
        if status != 0:
            err = "Failed to backup hela conf", host
            log_err.error(err)
            print "Failed to backup hela conf", host
            return -1
            sys.exit(1)
        cmd = "scp %s root@%s:/root/udisk/hela/conf/hela.conf" % (
            new_conf_file_name, host)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()
        status = pipe.returncode
        if status != 0:
            err = "Failed to scp hela conf", host
            log_err.error(err)
            print "Failed to scp hela conf", host
            return -1
            sys.exit(1)
        # diff不同
        if hela_dir_exist:
            cmd = "ssh root@%s \"diff /root/udisk/hela/conf/hela.conf.bak /root/udisk/hela/conf/hela.conf | grep -E '<|>'\"" % (host)
            pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            output = pipe.communicate()
            status = pipe.returncode
            if status != 0 and status != 1:
                err = "diff failed, status", status
                log_err.error(err)
                print "diff failed, status", status
                return -1
                sys.exit(1)
            old_diff = []
            new_diff = []
            for line in output[0].split('\n'):
                if len(line) < 2:
                    continue
                if line[0] == '<':
                    old_diff.append(line[1:])
                if line[0] == '>':
                    new_diff.append(line[1:])
            if checkdiff(old_diff, new_diff) == False:
                err = "check config diff failed, output: " + output[0]
                log_err.error(err)
                return -1
        instance += 1


if __name__ == "__main__":
    #main()
    generate_config("hn02", "3102", "tcp", "raw", "ssd")
