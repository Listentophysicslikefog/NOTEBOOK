#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import pymongo
import subprocess
import re
import log_info

global log
log = log_info.logger()

def help():
    print "Usage: " + sys.argv[0] + " <region> <set>"


def checkip(ip):
  p = re.compile(
      '^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
  if p.match(ip):
      return True
  else:
      return False

def check_dir_exit(region, set_id, dir_file, file_type):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    is_exists = os.path.exists(dir_file)
    if not is_exists:
        err = "region :" + region + " set_id: " + str(set_id)  + "  " + file_type + ": " + str(host_file) + "not exit"
        log_err.error(err)
        return -1
    else:
        return 0

def generate_ymer_all_ip(region, set_id):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    #region = sys.argv[1]
    #set_id = sys.argv[2]

    host_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                             "region", region, set_id, "host_info")
    vm_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                           "region", region, set_id, "vm_info")
    p2p_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                           "region", region, set_id, "p2p_info")

    ret = check_dir_exit(region, set_id, host_file, "host_file")
    if ret != 0:
        err = "host_file not exit "
        log_err.error(err)
        ret_msg= {'retcode': -1, 'retmsg': err}
        return ret_msg
    ret = check_dir_exit(region, set_id, vm_file, "vm_file")
    if ret != 0:
        err = "vm_file not exit "
        log_err.error(err)
        ret_msg= {'retcode': -1, 'retmsg': err}
        return ret_msg

    middle_file_path_per_set = "./middle_file/" + region + '-' + str(set_id)
    is_exists = os.path.exists(middle_file_path_per_set)
    if not is_exists:
        os.makedirs(middle_file_path_per_set)
        info = "path: " + middle_file_path_per_set + "  have been create, all set middle file will been saved here"
        log_inf.info(info)
    else:
        info = "path: " + middle_file_path_per_set + "  have exit"
        log_inf.info(info)
    host_ips = []
    idun_ips = []
    host_info = open(host_file).read().split("\n")
    vm_info = open(vm_file).read().split("\n")
    for line in host_info:
        line = line.strip()
        if checkip(line) == False:
            continue
        host_ips.append(line)
    host_list =middle_file_path_per_set + "/host_ips"
    f = open(host_list, 'w')
    for line in host_ips:
      f.write(line)
      f.write("\n")
    f.close()

    if os.path.exists(p2p_file):
      p2p_info = open(p2p_file).read().split("\n")
      for line in p2p_info:
        line_map = line.split()
        if len(line_map) == 0:
            continue
        if line_map[0] == "idun":
            idun_ips.append(line_map[1])
        idun_list = middle_file_path_per_set + "/idun_ips"
      f = open(idun_list, 'w')
      for line in idun_ips:
        f.write(line)
        f.write("\n")
      f.close()
    # 输出host_ips的hostname
    os.system("pssh -l root -h %s -P hostname" % host_list)
    success_info = "generate hela freyr idun ip list success"
    log_inf.info(success_info)
    ret_msg= {'retcode': 0, 'retmsg': success_info}
    return ret_msg


def main():
    if len(sys.argv[1:]) < 2:
        help()
        sys.exit()

    region = sys.argv[1]
    set_id = sys.argv[2]

    host_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                             "region", region, set_id, "host_info")
    vm_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                           "region", region, set_id, "vm_info")
    p2p_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                           "region", region, set_id, "p2p_info")
    
    middle_file_path_per_set = "./middle_file/" + region + '-' + str(set_id)
    is_exists = os.path.exists(middle_file_path_per_set)
    if not is_exists:
        os.makedirs(middle_file_path_per_set)
        #logging.info(
         #   'path: %s have been create, all set middle file will been saved here',
          #  middle_file_path_per_set)
    #else:
        #logging.info('path have exist: %s', middle_file_path_per_set)
    host_ips = []
    idun_ips = []
    host_info = open(host_file).read().split("\n")
    vm_info = open(vm_file).read().split("\n")
    for line in host_info:
        line = line.strip()
        if checkip(line) == False:
            continue
        host_ips.append(line)
    host_list =middle_file_path_per_set + "/host_ips"
    f = open(host_list, 'w')
    for line in host_ips:
      f.write(line)
      f.write("\n")
    f.close()

    if os.path.exists(p2p_file):
      p2p_info = open(p2p_file).read().split("\n")
      for line in p2p_info:
        line_map = line.split()
        if len(line_map) == 0:
            continue
        if line_map[0] == "idun":
            idun_ips.append(line_map[1])
        idun_list = middle_file_path_per_set + "/idun_ips"
      f = open(idun_list, 'w')
      for line in idun_ips:
        f.write(line)
        f.write("\n")
      f.close()
    # 输出host_ips的hostname
    os.system("pssh -l root -h %s -P hostname" % host_list)


if __name__ == "__main__":
    #main()
    ret = generate_ymer_all_ip("hn02", "3101")
    print ret
