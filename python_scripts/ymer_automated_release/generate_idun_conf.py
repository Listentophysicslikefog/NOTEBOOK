#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import pymongo
import subprocess
import re
import commands
sys.path.append(
  os.path.abspath(os.path.join(__file__, '../../../../libs')))
import fastcall
import log_info
check_items = ["db_name", "my_name", "set", "umongo", "metaserver",
               "listen_ip", "listen_port", "path", "server"]

global log
log = log_info.logger()

def help():
    print (sys.argv[0] + " Usage: <region> <set> <tcp/rdma> <raw/fs> <sata/ssd>>")

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


def check_process_exist(idun_ip, name):
    cmd = 'ssh root@%s ps -aux | grep -w %s | egrep -v \"grep|vim|vi|less|bash\" | wc -l' % (idun_ip, name)
    process_num = int(os.popen(cmd).readlines()[0].strip())
    if process_num > 0:
        print("@@@@@ idun_ip %s has %s process" % (idun_ip, name))
        return True
    else:
        return False

def check_remote_dir_exist(idun_ip):
    cmd = 'ssh root@%s ls /root/udisk/ | grep idun | wc -l' % (idun_ip)
    idun_dir_num = int(os.popen(cmd).readlines()[0].strip())
    if idun_dir_num > 0:
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
                                  "release", conf_file_dir, "idun.conf")
    if os.path.exists(conf_file_name) == False:
        err = conf_file_name + " not exists, we should use this config generate new config"
        log_err.error(err)
        return -1

    configuration = open(conf_file_name, 'r').read()

    p2p_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                           "region", region, set_id, "p2p_info")
    if not os.path.exists(p2p_file):
        err = "this set not p2p, no need to deploy idun, ymer not supprted for %s %s" % (region, set_id)
        log_err.error(err)
        return -1
    p2p_info = open(p2p_file).read().split("\n")
    find_new_conf_dir = "./middle_file/" + region + "-"+ set_id
    if not os.path.exists(find_new_conf_dir):
        os.makedirs(find_new_conf_dir)
    instance = 0
    for line in p2p_info:
        line_map = line.split()
        if len(line_map) == 0:
            continue
        if line_map[0] != "idun":
            continue
        idun_ip = line_map[1].strip()

        if checkip(idun_ip) == False:
            continue
        start_idun_info = "=====>>>> generate idun config for idun_ip: " + idun_ip
        log_inf.info(start_idun_info)
        # idun不是所有的机器都要发布
        new_conf = str(configuration)
        new_conf = new_conf.replace("$instance", str(instance), 10)
        new_conf = new_conf.replace("$set", "set"+set_id, 10)
        new_conf = new_conf.replace("$server", zookeeper_server, 10)
        new_conf = new_conf.replace("$listen_ip", idun_ip, 10)
        new_conf_file_name = find_new_conf_dir + "/idun.conf"
        new_conf_file = open(new_conf_file_name, 'w')
        new_conf_file.write(new_conf)
        new_conf_file.close()

        cmd = ""
        idun_dir_exist = check_remote_dir_exist(idun_ip)
        if idun_dir_exist:
            cmd = "ssh root@%s \"mkdir -p /root/udisk/idun;mkdir -p /root/udisk/idun/conf/;mv /root/udisk/idun/conf/idun.conf /root/udisk/idun/conf/idun.conf.bak\"" % (idun_ip)
        else:
            cmd = "ssh root@%s \"mkdir -p /root/udisk/idun;mkdir -p /root/udisk/idun/conf/;mkdir -p /var/log/udisk/idun\"" % (idun_ip)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()
        status = pipe.returncode
        if status != 0:
            err = "Failed to backup idun conf ip: "+  idun_ip + "  cmd: "+ cmd
            log_err.error(err)
            return -1
        cmd = "scp %s root@%s:/root/udisk/idun/conf/idun.conf" % (
            new_conf_file_name, idun_ip)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()
        status = pipe.returncode
        if status != 0:
            err = "Failed to scp idun conf ip: " +  idun_ip + "  cmd: " + cmd
            log_err.error(err)
            return -1
        cmd = "scp %s root@%s:/root/udisk/idun/conf/idun.conf" % (
            new_conf_file_name, idun_ip)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()
        status = pipe.returncode
        if status != 0:
            err = "Failed to scp idun conf ip: " +  idun_ip + "  cmd: " + cmd
            log_err.error(err)
            return -1
        # diff不同
        if idun_dir_exist:
            cmd = "ssh root@%s \"diff /root/udisk/idun/conf/idun.conf.bak /root/udisk/idun/conf/idun.conf | grep -E '<|>'\"" % (idun_ip)
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
        sys.exit()

    region = sys.argv[1]
    set_id = sys.argv[2]
    net_type = sys.argv[3]
    storage_type = sys.argv[4]
    disk_type = sys.argv[5]

    zookeeper_server = fastcall.get_zookeeper_servers(region, set_id)

    conf_file_dir = "_".join([net_type, storage_type, disk_type])
    conf_file_name = os.path.join(os.environ['HOME'], "limax", "udisk",
                                  "release", conf_file_dir, "idun.conf")

    if os.path.exists(conf_file_name) == False:
        print conf_file_name + " not exists"
        sys.exit()
    configuration = open(conf_file_name, 'r').read()

    p2p_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                           "region", region, set_id, "p2p_info")
    if not os.path.exists(p2p_file):
        print("ymer not supprted for %s %s" % (region, set_id))
        sys.exit()
    p2p_info = open(p2p_file).read().split("\n")
    instance = 0
    for line in p2p_info:
        line_map = line.split()
        if len(line_map) == 0:
            continue
        if line_map[0] != "idun":
            continue
        idun_ip = line_map[1].strip()

        if checkip(idun_ip) == False:
            continue
        print("=====>>>> generate idun config for idun_ip: " + idun_ip)
        # idun不是所有的机器都要发布
        new_conf = str(configuration)
        new_conf = new_conf.replace("$instance", str(instance), 10)
        new_conf = new_conf.replace("$set", "set"+set_id, 10)
        new_conf = new_conf.replace("$server", zookeeper_server, 10)
        new_conf = new_conf.replace("$listen_ip", idun_ip, 10)
        new_conf_file_name = "idun.conf"
        new_conf_file = open(new_conf_file_name, 'w')
        new_conf_file.write(new_conf)
        new_conf_file.close()

        idun_dir_exist = check_remote_dir_exist(idun_ip)
        if idun_dir_exist:
            cmd = "ssh root@%s \"mkdir -p /root/udisk/idun;mkdir -p /root/udisk/idun/conf/;mv /root/udisk/idun/conf/idun.conf /root/udisk/idun/conf/idun.conf.bak\"" % (idun_ip)
        else:
            cmd = "ssh root@%s \"mkdir -p /root/udisk/idun;mkdir -p /root/udisk/idun/conf/;mkdir -p /var/log/udisk/idun\"" % (idun_ip)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()
        status = pipe.returncode
        if status != 0:
            print "Failed to backup idun conf", idun_ip
            sys.exit(1)
        cmd = "scp %s root@%s:/root/udisk/idun/conf/idun.conf" % (
            new_conf_file_name, idun_ip)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()
        status = pipe.returncode
        if status != 0:
            print "Failed to scp idun conf", idun_ip
            sys.exit(1)
        # diff不同
        if idun_dir_exist:
            cmd = "ssh root@%s \"diff /root/udisk/idun/conf/idun.conf.bak /root/udisk/idun/conf/idun.conf | grep -E '<|>'\"" % (idun_ip)
            pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            output = pipe.communicate()
            status = pipe.returncode
            if status != 0 and status != 1:
                print "diff failed, status", status
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
                print "check config diff failed"
                print output[0]
                sys.exit(1)
        instance += 1


if __name__ == "__main__":
    #main()
    generate_config("hn02", "3101", "tcp", "raw", "ssd")
