#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import pymongo
import subprocess
import re
sys.path.append(
  os.path.abspath(os.path.join(__file__, '../../../../libs')))
import fastcall
import log_info

check_items = ["db_name", "enable_hela", "my_name", "my_set", "umongo", "metaserver",
               "access", "ark_access", "hela", "idun", "listen_ip", "listen_port", "path", "server", "global_server"]


global log
log = log_info.logger()

def help():
    print (sys.argv[0] + " Usage: <region> <set> <tcp/rdma> <raw/fs> <sata/ssd>")

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
                    err =  "%s is different, old: %s, new: %s" % (conf_key, old_conf_map[conf_key], conf_value)
                    log_err.error(err)
                    return False
    return True

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
    global_zk_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                                  "region", region, "global_zookeeper")
    if not os.path.exists(global_zk_file):
        err = "global_zk_file  dir not exit, region: " + region + " set_id:" + set_id
        log_err.error(err)
        return -1
    global_zookeeper_server = open(global_zk_file).read().split("\n")[0]

    conf_file_dir = "_".join([net_type, storage_type, disk_type])
    comm_conf_file_name = os.path.join(os.environ['HOME'], "limax", "udisk",
                                  "release", conf_file_dir, "freyr-only.conf")
    ymer_conf_file_name = os.path.join(os.environ['HOME'], "limax", "udisk",
                                  "release", conf_file_dir, "freyr-ymer.conf")

    if not os.path.exists(comm_conf_file_name):
        err = "comm_conf_file_name dir: " + str(comm_conf_file_name) + "  not exit, region: " + region + " set_id:" + str(set_id)
        log_err.error(err)
        return -1
    if not os.path.exists(ymer_conf_file_name):
        err = "ymer_conf_file_name dir: " + str(ymer_conf_file_name) + "  not exit, region: " + region + " set_id:" + str(set_id)
        log_err.error(err)
        return -1

    p2p_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                           "region", region, set_id, "p2p_info")
    if os.path.exists(p2p_file):
        conf_file_name = ymer_conf_file_name
        conf_file = "region: " + region + " set_id:" + str(set_id) + " is p2p, use freyr-ymer conf: " + str(conf_file_name)
        log_inf.info(conf_file)
    else:
        conf_file_name = comm_conf_file_name
        conf_file = "region: " + region + " set_id:" + str(set_id) + " not p2p, use freyr-only conf: " + str(conf_file_name)
        log_inf.info(conf_file)
    if os.path.exists(conf_file_name) == False:
        err = "comm_conf_file_name dir: " + str(conf_file_name) + "  not exit, region: " + region + " set_id:" + str(set_id)
        log_err.error(err)
        return -1
    configuration = open(conf_file_name, 'r').read()

    host_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                             "region", region, set_id, "host_info")
    if not os.path.exists(host_file):
        err = "host_file dir: " + str(host_file) + "  not exit, region: " + region + " set_id:" + set_id
        log_err.error(err)
        return -1
    host_info = open(host_file).read().split("\n")
    find_new_conf_dir = "./middle_file/" + region + "-"+ str(set_id)
    if not os.path.exists(find_new_conf_dir):
        os.makedirs(find_new_conf_dir)
    instance = 0
    for host in host_info:
        host = host.strip()
        if checkip(host) == False:
            continue
        deploy_info = "@@@@@@@@@@@@@ now deploy freyr ip: " + host + " @@@@@@@@@@@@@@"
        log_inf.info(deploy_info)
        new_conf = str(configuration)
        new_conf = new_conf.replace("$my_instance", str(instance), 10)
        new_conf = new_conf.replace("$my_set", set_id, 10)
        new_conf = new_conf.replace("$server", zookeeper_server, 10)
        new_conf = new_conf.replace(
            "$global_server", global_zookeeper_server, 10)
        new_conf = new_conf.replace("$listen_ip", host, 10)
        new_conf_file_name = find_new_conf_dir +  "/freyr.conf"
        new_conf_file = open(new_conf_file_name, 'w')
        new_conf_file.write(new_conf)
        new_conf_file.close()
        cmd = "ssh root@%s \"mv /root/udisk/freyr/conf/freyr.conf /root/udisk/freyr/conf/freyr.conf.bak\"" % (
            host)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()
        status = pipe.returncode
        if status != 0:
            err = "Failed to backup freyr conf ip: "+  host + "  cmd: "+ cmd
            log_err.error(err)
            return -1
        cmd = "scp %s root@%s:/root/udisk/freyr/conf/freyr.conf" % (
            new_conf_file_name, host)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()
        status = pipe.returncode
        if status != 0:
            err = "Failed to scp freyr conf to host: " + str(host)
            log_err.error(err)
            return -1
            #sys.exit(1)

        # diff不同
        cmd = "ssh root@%s \"diff /root/udisk/freyr/conf/freyr.conf.bak /root/udisk/freyr/conf/freyr.conf | grep -E '<|>'\"" % (
            host)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()
        status = pipe.returncode
        if status != 0 and status != 1:
            err ="cmd: " + cmd +  ",freyr  diff failed, status: " + str(status) + "  output: " + str(output)
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
    global_zk_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                                  "region", region, "global_zookeeper")
    global_zookeeper_server = open(global_zk_file).read().split("\n")[0]

    conf_file_dir = "_".join([net_type, storage_type, disk_type])
    comm_conf_file_name = os.path.join(os.environ['HOME'], "limax", "udisk",
                                  "release", conf_file_dir, "freyr-only.conf")
    ymer_conf_file_name = os.path.join(os.environ['HOME'], "limax", "udisk",
                                  "release", conf_file_dir, "freyr-ymer.conf")

    p2p_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                           "region", region, set_id, "p2p_info")
    if os.path.exists(p2p_file):
        conf_file_name = ymer_conf_file_name
    else:
        conf_file_name = comm_conf_file_name
    print("use freyr conf: " + conf_file_name)

    if os.path.exists(conf_file_name) == False:
        print conf_file_name + " not exists"
        sys.exit()
    configuration = open(conf_file_name, 'r').read()

    host_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                             "region", region, set_id, "host_info")
    host_info = open(host_file).read().split("\n")
    instance = 0
    for host in host_info:
        host = host.strip()
        if checkip(host) == False:
            continue
        print("@@@@@@@@@@@@@ now deploy freyr ip: %s @@@@@@@@@@@@@@" % host)
        new_conf = str(configuration)
        new_conf = new_conf.replace("$my_instance", str(instance), 10)
        new_conf = new_conf.replace("$my_set", set_id, 10)
        new_conf = new_conf.replace("$server", zookeeper_server, 10)
        new_conf = new_conf.replace(
            "$global_server", global_zookeeper_server, 10)
        new_conf = new_conf.replace("$listen_ip", host, 10)
        new_conf_file_name = "freyr.conf"
        new_conf_file = open(new_conf_file_name, 'w')
        new_conf_file.write(new_conf)
        new_conf_file.close()
        cmd = "ssh root@%s \"mv /root/udisk/freyr/conf/freyr.conf /root/udisk/freyr/conf/freyr.conf.bak\"" % (
            host)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()
        status = pipe.returncode
        if status != 0:
            print "Failed to backup freyr conf", host
            sys.exit(1)
        cmd = "scp %s root@%s:/root/udisk/freyr/conf/freyr.conf" % (
            new_conf_file_name, host)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()
        status = pipe.returncode
        if status != 0:
            print "Failed to scp freyr conf", host
            sys.exit(1)
        # diff不同
        cmd = "ssh root@%s \"diff /root/udisk/freyr/conf/freyr.conf.bak /root/udisk/freyr/conf/freyr.conf | grep -E '<|>'\"" % (
            host)
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
    re = generate_config("hn02", "3101", "tcp", "raw", "ssd")
    print re
