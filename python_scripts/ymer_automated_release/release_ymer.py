#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 自动化发布应该单独维护一套相关脚本，否则被别人改后，无法知道自动化发布脚本是否会出问题
import sys, os, time
import zookeeper
import logging
import time
import subprocess
import log_info

sys.path.append(
    os.path.abspath(os.path.join(__file__,
                                 '../../../../../third_part/message')))
sys.path.append(
    os.path.abspath(
        os.path.join(__file__, '../../../../../third_part/wiwo_python')))
sys.path.append(os.path.abspath(os.path.join(__file__, '../../../../libs')))
import fastcall
import udisk_pb2, uns_pb2, wiwo_python

global log 
log = log_info.logger()
def fetch_binary(tmp_path, module_name, binary_file, deploy_centor):
    # get remote bin md5
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    fetch_binary_info = "start fetch binary: " + binary_file + " from deploy_centor: " + str(deploy_centor) + " to :" + str(tmp_path)
    log_inf.info(fetch_binary_info)
    cmd = "ssh root@%s \"md5sum /root/deploy_center/%s/%s | awk '{print \$1}'\"" % (
        deploy_centor, module_name, binary_file)
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    remote_md5 = pipe.communicate()[0].split('\n')[0]
    status = pipe.returncode
    if status != 0:
        err = "failed to get remote binary file md5, status: "+ str(status) + ", cmd: "+ str(cmd)
        log_err.error(err)
        return -1

    # copy remote bin to local
    if not os.path.isdir(tmp_path):
        err = "dir : " + str(tmp_path) + "not exit, this dir will create in generate config or generate ip_list"
        log_err.error(err)
        return -1 
    cmd = "scp root@%s:/root/deploy_center/%s/%s %s" % (
        deploy_centor, module_name, binary_file, tmp_path)
    res = -1
    try:
        #如果命令行执行成功，check_call返回返回码0，否则抛出subprocess.CalledProcessError异常
        res = subprocess.check_call(cmd, shell=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError, exc:
        err = "failed to scp binary file to local, returncode: " + str(exc.returncode) + ", cmd: " + str(exc.cmd) +", output: "+ str(exc.output)
        log_err.error(err)
        return -1
    if res != 0:
        err = "failed to scp binary file to local, res: "+ str(res) + ",  cmd: "+ str(cmd) 
        log_err.error(err)
        return -1

    # get local bin md5
    cmd = "md5sum %s/%s | awk '{print $1}'" % (tmp_path, binary_file)
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    local_md5 = pipe.communicate()[0].split('\n')[0]
    md5_info = "local_md5: " + local_md5 + ", remote_md5: " + remote_md5 + " copy " + str(binary_file) + " from deploy_centor:  " + str(deploy_centor)
    log_inf.info(md5_info)
    status = pipe.returncode
    if status != 0:
        err =  "failed to get local binary file md5, status: "+ str(status) + ", cmd: "+ str(cmd)
        log_err.error(err)
        return -1

    # md5 check
    if local_md5 != remote_md5:
        err = "local_md5: "+ local_md5 + " != remote_md5: "+ remote_md5
        log_err.error(err)
        return -1
    return 0


def copy_binary(tmp_path, region, set_id, module_name, binary_file):
    # get local bin md5
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    copy_binary_info = "start copy binary: " + str(binary_file) + " from :" + str(tmp_path) + "  to " + str(module_name) + " ip_list. region:" + str(region) + "  set_id: " + str(set_id)
    log_inf.info(copy_binary_info)
    cmd = "md5sum %s/%s | awk '{print $1}'" % (tmp_path, binary_file)
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    local_md5 = pipe.communicate()[0].split('\n')[0]
    status = pipe.returncode
    if status != 0:
        err = "failed to get local binary file md5, status: " + str(status) + ", cmd:" + str(cmd)
        log_err.error(err)
        return -1
    ip_file = tmp_path + "/" + region + "-" + set_id
    if module_name == "hela" or module_name == "freyr":
        ip_file = ip_file + "/host_ips"
    elif module_name == "idun":
        ip_file = ip_file + "/idun_ips"
    else:
        err = "module_name: "+ module_name+" error"
        log_err.error(err)
        return -1
    if not os.path.isdir(tmp_path):
        err = "dir : " + str(tmp_path) + "not exit, this dir will create in generate config or generate ip_list"
        log_err.error(err)
        return -1
    host_lists_handle = open(ip_file, 'r')
    list_of_lines = host_lists_handle.readlines()
    for host_ip in list_of_lines:
        host_ip = host_ip.strip()
        # copy local bin to remote
        cmd = "scp %s/%s root@%s:/root/udisk/%s" % (tmp_path, binary_file,
                                                       host_ip, module_name)
        res = -1
        try:
            #如果命令行执行成功，check_call返回返回码0，否则抛出subprocess.CalledProcessError异常
            res = subprocess.check_call(cmd,
                                        shell=True,
                                        stdout=subprocess.PIPE)
        except subprocess.CalledProcessError, exc:
            err = "failed to scp binary local file to remote, maybe remot binary version is the same as this.   returncode: " + str(exc.returncode)  + ", cmd: " + str(exc.cmd) + ", output: " + str(exc.output)
            log_err.error(err)
            return -1
        if res != 0:
            err = "failed to scp binary local file to remote, maybe remot binary version is the same as this.   res: " + str(res) + ",  cmd: "+ cmd
            log_err.error(err)
            return -1

        # get remote md5
        cmd = "ssh root@%s \"md5sum /root/udisk/%s/%s | awk '{print \$1}'\"" % (
            host_ip, module_name, binary_file)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        remote_md5 = pipe.communicate()[0].split('\n')[0]
        status = pipe.returncode
        if status != 0:
            err =  "failed to get remote binary file md5, status: " + str(status) + ", cmd: " + str(cmd)
            log_err.error(err)
            return -1
        md5_info = "local_md5: "+ local_md5 + ",  remote_md5: ", remote_md5 + "  host_ip: " + str(host_ip)
        log_inf.info(md5_info)
        # md5 check
        if local_md5 != remote_md5:
            err = "local_md5: "+ local_md5 + "  != remote_md5: ", remote_md5
            log_err.error(err)
            return -1

    host_lists_handle.close()
    return 0

def check_wathcdog(set_temp_path, module_name):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    host_lists_file = set_temp_path
    if module_name == "hela" or module_name == "freyr":
        host_lists_file = host_lists_file + '/host_ips'
    elif module_name == "idun":
        host_lists_file = host_lists_file + "/idun_ips"
    else:
        err = "module_name: "+ module_name+" error"
        log_err.error(err)
        return -1

    #cmd = "pssh -l root -h %s -i \"ps -ef | grep quick_watchdog | grep -v \$\$\"" % (host_lists_file)
    cmd = "pssh -l root -h %s -i \"ps -ef | grep quick_watchdog | grep -v grep\"" % (
        host_lists_file)
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    result = pipe.communicate()[0].split('\n')[0]
    status = pipe.returncode
    if status != 0:  # grep到quick_watchdog即会返回成功status = 0
        err = "failed to get quick_watchdog, quick_watchdog may be not running, status: " + str(status) + ", cmd: " + str(cmd) + ", result: "+ str(result)
        log_err.error(err)
        return -1
    check_info = " check quick_watchdog success.  status: " + str(status) + "   cmd: " + str(cmd) + ".   result: " + str(result)
    log_inf.info(check_info)
    return 0

def releaseing_binary_file(middle_file_path_one_set, binary_file, module_name, test_mode):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    # 1、获取原来的软链接指向的文件
    original_bin_file_path = ''
    original_softlink_dict = {}
    ymer_before_kill_pid = ""
    ip_list_file = ""
    if module_name == "hela":
        ip_list_file = middle_file_path_one_set + '/host_ips'
        ymer_before_kill_pid = "/hela_before_kill_pid"
    elif module_name == "freyr":
        ip_list_file = middle_file_path_one_set + '/host_ips'
        ymer_before_kill_pid = "/freyr_before_kill_pid"
    elif module_name == "idun":
        ip_list_file = middle_file_path_one_set + "/idun_ips"
        ymer_before_kill_pid = "/idun_before_kill_pid"
    else:
        err = "module_name: "+ module_name+" error"
        log_err.error(err)
        return -1

    host_lists_handle = open(ip_list_file, 'r')
    list_of_lines = host_lists_handle.readlines()
    for host_ip in list_of_lines:
        host_ip = host_ip.strip()
        cmd = "ssh root@%s \"ls -il /root/udisk/%s/%s | awk '{print \$12}'\"" % (
           host_ip, module_name, module_name)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        result = pipe.communicate()[0].split('\n')[0]
        status = pipe.returncode
        if status != 0:
            err = "get original soft linkfile whether right failed.  status: " + str(status) + "  cmd: " + str(cmd) + ", result: " + str(result)
            log_err.error(err)
            return -1
        back_info = "get original soft linkfile whether right success . status: " + str(status)  + "  cmd: " + str(cmd)
        log_inf.info(back_info)
        original_softlink_dict[str(result)] = host_ip
        original_bin_file_path = str(result)

    # 2、检查软链接是否一致,所有ip的软连接都一样所有长度必须为1
    if len(original_softlink_dict) != 1:
        err = "length of original_softlink_dict is:" + str(len(original_softlink_dict)) + " != 1"  
        log_err.error(err)
        for key, value in original_softlink_dict.items():
            err = "softlink index bin file: " + str(key) + ", ip: " + str(value)
            log_err.error(err)
        return -1

    # 3、建立老bin文件的软链接做备份
    host_lists_file = ip_list_file
    cmd = "pssh -l root -h %s -i \"ln -sf %s /root/udisk/%s/%s.bak\"" % (
        host_lists_file, original_bin_file_path, module_name, module_name)
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    result = pipe.communicate()[0].split('\n')[0]
    status = pipe.returncode
    if status != 0:
        err = "failed to backup original soft linkfile. status: " + str(status) + "  cmd: " + str(cmd) + ".  result: " + str(result)
        log_err.error(err)
        return -1
    back_link_info = "backup original soft linkfile success.  status: " + str(status)   + "  cmd : " + str(cmd) 
    log_inf.info(back_link_info)
    # 2、杀服务前保存ymer pid
    ymer_before_kill_pid_dir = middle_file_path_one_set + ymer_before_kill_pid
    if not os.path.isdir(ymer_before_kill_pid_dir):
        os.mkdir(ymer_before_kill_pid_dir)
    cmd = "pssh -l root -o %s -h %s -i \"ps -ef | grep %s/conf  | grep -v grep\"" % (
        ymer_before_kill_pid_dir, host_lists_file, module_name)
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    result = pipe.communicate()[0].split('\n')[0]
    status = pipe.returncode
    if status != 0:
        err = "failed to save: " + module_name + ", before kill pids, status: "+ str(status) + ", cmd: " + str(cmd) + ", result: " + str(result)
        log_err.error(err)
        return -1

    if test_mode == 0:
        # 3、产生新的软链,更新ymer的二进制为发布版本的软连接
        cmd = "pssh -l root -h %s -i \"ln -sf /root/udisk/%s/%s /root/udisk/%s/%s\"" % (
            host_lists_file, module_name, binary_file, module_name, module_name)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        result = pipe.communicate()[0].split('\n')[0]
        status = pipe.returncode
        if status != 0:
            err = "failed to backup original soft linkfile, status: " + str(status) + ", cmd: "+ str(cmd) + ", result: " + str(result)
            log_err.error(err)
            return -1
        new_link_info ="create new soft linkfile success.  status: " + str(status) + ", cmd: "+ str(cmd)
        log_inf.info(new_link_info)
    # 4、软链正确性检 /root/udisk/hela/hela -v 只有hela起来后才会成功看到版本信息
    if pre_check_binary_instruction(middle_file_path_one_set, module_name, module_name) != 0:
        err = "affer modify softlink, start up " + module_name + "failed"
        log_err.error(err)
        return -1

    return 0

def pre_check_binary_instruction(middle_file_path_one_set, module_name, binary_file):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    host_lists_file=""
    if module_name == "hela":
        host_lists_file = middle_file_path_one_set + '/host_ips'
    elif module_name == "freyr":
        host_lists_file = middle_file_path_one_set + '/host_ips'
    elif module_name == "idun":
        host_lists_file = middle_file_path_one_set + "/idun_ips"
    else:
        err = "module_name: "+ module_name+" error"
        log_err.error(err)
        return -1

    hosts = []
    f = open(host_lists_file, 'r')
    for line in f.readlines():
        if line.strip() != "":
            hosts.append(line.strip())
    f.close()

    for host in hosts:
        # ymer -v 启动ymer
        cmd = "ssh root@%s \"/root/udisk/%s/%s -v\"" % (host, module_name, binary_file)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        #result = pipe.communicate()[0].split('\n')[0]
        result = pipe.communicate()
        status = pipe.returncode
        if status != 0:
            err = "failed to get: " + module_name + ", binary_instruction, status: " + str(status) + " , cmd: " + str(cmd)
            log_err.error(err)
            return -1

        # 检查是否存在version字段
        str_result = str(result[0])
        index = str_result.find("version")
        if index != -1:
            continue
        else:
            err = "failed to check version, may be illegal instruction, result: "+ str(result) + ", cmd:" + str(cmd)
            log_err.error(err)
            return -1
    return 0


def releasing_check(middle_file_path_one_set, module_name, test_mode):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    ip_lists_file = ""
    first_look_affer_ymer_killed = ""
    second_look_affer_ymer_killed = ""
    killed_ymer_info = ""
    ymer_before_kill_pid = ""
    if module_name == "hela":
        ip_lists_file = middle_file_path_one_set + '/host_ips'
        ymer_before_kill_pid = "hela_before_kill_pid"
        first_look_affer_ymer_killed = "first_look_affer_hela_killed"
        second_look_affer_ymer_killed = "second_look_affer_hela_killed"
        killed_ymer_info = "/killed_hela_info"
    elif module_name == "freyr":
        ip_lists_file = middle_file_path_one_set + '/host_ips'
        ymer_before_kill_pid = "freyr_before_kill_pid"
        first_look_affer_ymer_killed = "first_look_affer_freyr_killed"
        second_look_affer_ymer_killed = "second_look_affer_freyr_killed"
        killed_ymer_info = "/killed_freyr_info"
    elif module_name == "idun":
        ip_lists_file = middle_file_path_one_set + "/idun_ips"
        ymer_before_kill_pid = "idun_before_kill_pid"
        first_look_affer_ymer_killed = "first_look_affer_idun_killed"
        second_look_affer_ymer_killed = "second_look_affer_idun_killed"
        killed_ymer_info = "/killed_idun_info"
    else:
        err = "module_name: "+ module_name+" error"
        log_err.error(err)
        return -1
    # 1、杀服务 & 保存杀掉的hela、idun、freyr信息
    ymer_killing_info_dir = middle_file_path_one_set + killed_ymer_info
    if not os.path.isdir(ymer_killing_info_dir):
        os.mkdir(ymer_killing_info_dir)
    if test_mode == 0:
        cmd = "pssh -l root -o %s -h %s -i \"ps -ef | grep %s/conf  | grep -v guard | grep -v grep | awk '{print \$2}' | xargs -r kill -9\"" % (
            ymer_killing_info_dir, ip_lists_file, module_name)
    elif test_mode == 1:
        cmd = "pssh -l root -o %s -h %s -i \"ps -ef | grep %s/conf | grep -v guard | grep -v grep | awk '{print \$2}'\"" % (
            ymer_killing_info_dir, ip_lists_file, module_name)
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    result = pipe.communicate()[0].split('\n')[0]
    status = pipe.returncode
    if status != 0:
        err = "failed to killing : "+ module_name + ", status: "+ str(status) + ", cmd: " + str(cmd) + ", result:" + str(result)
        log_err.error(err)
        return -1
    kill_info = "kill old process: "+ module_name + " after 9 seconds" + " cmd:" + str(cmd)
    log_inf.info(kill_info)
    time.sleep(9)
    first_look_dir_path = middle_file_path_one_set + '/' + first_look_affer_ymer_killed
    second_look_dir_path = middle_file_path_one_set + '/' + second_look_affer_ymer_killed
    ymer_before_kill_pid_dir = middle_file_path_one_set + "/" + ymer_before_kill_pid
    if releaseing_done_check_pid(ip_lists_file, module_name, first_look_dir_path,
                                 second_look_dir_path,
                                 ymer_before_kill_pid_dir) != 0:
        err = module_name + " releaseing done but  check pid failed!"
        log_err.error(err)
        return -1

    return 0


def releaseing_done_check_pid(ip_lists_file, module_name, first_look_dir_path,
                             second_look_dir_path, ymer_before_kill_pid_dir):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    host_lists_file = ip_lists_file
    # 1、第一个5s查看ymer信息
    if not os.path.isdir(first_look_dir_path):
        os.mkdir(first_look_dir_path)
    first_kill_info = "first look killed  process: "+ module_name + " after in 5 seconds"
    log_inf.info(first_kill_info)
    time.sleep(5)
    cmd = "pssh -l root -o %s -h %s -i \"ps -ef | grep %s/conf | grep -v guard | grep -v grep\"" % (
        first_look_dir_path, host_lists_file, module_name)
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    result = pipe.communicate()[0].split('\n')[0]
    status = pipe.returncode
    if status != 0:
        err = "failed to first  check killed : "+ module_name + " after 5s, status: " + str(status) + ", cmd: " + str(cmd) + ", result: " + str(result)
        log_err.error(err)
        return -1

    # 2、第二个5s查看ymer信息
    if not os.path.isdir(second_look_dir_path):
        os.mkdir(second_look_dir_path)
    second_kill_info = "second look killed  process: "+ module_name + " after in 10 seconds"
    log_inf.info(second_kill_info)
    time.sleep(5)
    cmd = "pssh -l root -o %s -h %s -i \"ps -ef | grep %s/conf | grep -v guard | grep -v grep\"" % (
        second_look_dir_path, host_lists_file, module_name)
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    result = pipe.communicate()[0].split('\n')[0]
    status = pipe.returncode
    if status != 0:
        err = "failed to second check killed : "+ module_name + " after 5s, status: " + str(status) + ", cmd: " + str(cmd) + ", result: " + str(result)
        log_err.error(err)
        return -1

    # 3、检查pid
    if check_pid(ip_lists_file, module_name, ymer_before_kill_pid_dir,
                 first_look_dir_path, second_look_dir_path) != 0:
        err = "check: "+ module_name + " pid fail"
        log_err.error(err)
        return -1
    success_info="release : " + module_name + " success"
    log_inf.info(success_info)
    return 0

def check_pid(ip_lists_file, module_name, before_kill_pid_path,
              after_kill_first_look_path, after_kill_second_look_path):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    host_list = ip_lists_file
    hosts = []
    f = open(host_list, 'r')
    for line in f.readlines():
        if line.strip() != "":
            hosts.append(line.strip())
    f.close()
    process_count = 0
    is_error = False
    # 遍历每个机器，对比两次ps的pid
    for host in hosts:
        check_info = "begin check "+ module_name +" host:" + str(host)
        log_inf.info(check_info)
        after_kill_first_look_pid_dict = {}
        before_kill_process_list = []
        before_kill = open(before_kill_pid_path + "/" + host, 'r')
        for process_line in before_kill.readlines():
            if process_line.find("grep") != -1:
                continue
            process_name = process_line.split()[9]
            before_kill_process_list.append(process_name)
        before_kill.close()
        # 记录first_look的进程名到pid的映射
        first_look = open(after_kill_first_look_path + "/" + host, 'r')
        for process_line in first_look.readlines():
            if process_line.find("grep") != -1:
                continue
            pid = process_line.split()[1]
            process_name = process_line.split()[9]
            after_kill_first_look_pid_dict[process_name] = pid
            process_count += 1
        first_look.close()
        for value in before_kill_process_list:
            if after_kill_first_look_pid_dict.has_key(value) == False:
                err =module_name +  "host: "+ str(host) + " process: " + str(value) + " before kill exist, after kill not exist!!!"
                log_err.error(err)
                is_error = True
        for key, value in after_kill_first_look_pid_dict.items():
            if key not in before_kill_process_list:
                err =module_name +  "host: "+ str(host) + " process: " + str(value) + " before kill exist, after kill not exist!!!"
                log_err.error(err)
                is_error = True

        # 把second_look得到的pid和first_look对比
        second_look = open(after_kill_second_look_path + "/" + host, 'r')
        for process_line in second_look.readlines():
            if process_line.find("grep") != -1:
                continue
            pid = process_line.split()[1]
            process_name = process_line.split()[9]
            # first_look没有该进程，只打印错误，不退出
            if after_kill_first_look_pid_dict.has_key(process_name) == False:
                err = module_name + "host: "+ str(host) + " process: "+ str(process_name) + "not exists at first look, check directory first_look and second_look"
                log_err.error(err)
                is_error = True
                continue
            # 两次获取到的pid不同，说明进程发生重启，报错并退出检查
            if after_kill_first_look_pid_dict[process_name] != pid:
                errr = module_name + "host: "+ str(host) + " process: "+ str(process_name) + " pid changed, first pid: " + str(after_kill_first_look_pid_dict[process_name]) + " second pid: " + str(pid)
                log_err.error(err)
                is_error = True
            # 比较通过后从map中删除
            after_kill_first_look_pid_dict.pop(process_name)
        # 若比较完成后，map内仍有未删除的key，说明second_look时有进程退出了
        if len(after_kill_first_look_pid_dict.keys()) != 0:
            err = module_name + "host: "+ str(host) + " process: "+ str(after_kill_first_look_pid_dict.keys()) + ", these processes exited during second look"
            log_err.error(err)
            is_error = True
        second_look.close()
    process_count = module_name + " process count :" + str(process_count) + "  should be 1"
    log_inf.info(process_count)
    if is_error:
        err=module_name + " process check fail"
        log_err.error(err)
        return -1
    else:
        success_info=module_name + " process check success"
        log_inf.info(success_info)
        return 0




def ymer_release_fast(module_name, region, set_id, binary_file, deploy_center, test_mode):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    middle_file_path = "./middle_file"
    middle_file_path_per_set = middle_file_path + '/' + region + '-' + set_id
    host_ips_file_path = middle_file_path_per_set
    if module_name == "hela" or module_name == "freyr":
        host_ips_file_path = host_ips_file_path + "/host_ips"
    elif module_name == "idun":
        host_ips_file_path = host_ips_file_path + "/idun_ips"
    else:
        err = "module_name: "+ module_name+" error"
        log_err.error(err)
        ret_msg= {'retcode': -1, 'retmsg': err}
        return ret_msg

    is_exists = os.path.exists(host_ips_file_path)
    if not is_exists:  #如果使用自动化发布脚本，在genera_脚本中会生成host_ips文件
            err = "generate_ip_list failed, ip_list file : " + str(host_ips_file_path) + " not exit"
            log_err.error(err)
            ret_msg= {'retcode': -1, 'retmsg': err}
            return ret_msg
    if fetch_binary(middle_file_path, module_name, binary_file, deploy_center) != 0:
        err = "fetch_binary: "+ str(binary_file) + "  failed" + ", module_name" + module_name
        log_err.error(err)
        ret_msg= {'retcode': -1, 'retmsg': err}
        return ret_msg

    if copy_binary(middle_file_path,  region, set_id, module_name, binary_file) != 0:
        err = "copy_binary: "+ str(binary_file) + " failed, "  + " module_name: " + module_name
        log_err.error(err)
        ret_msg= {'retcode': -1, 'retmsg': err}
        return ret_msg
    #check_wathcdog(host_ips_file_path, module_name) != 0:
    if check_wathcdog(middle_file_path_per_set, module_name) != 0:
        err = "check watchdog failed maybe watchdog not exit"
        log_err.error(err)
        ret_msg= {'retcode': -1, 'retmsg': err}
        return ret_msg

    if releaseing_binary_file(middle_file_path_per_set, binary_file, module_name, test_mode) != 0:
        err = "releaseing_binary_file failed, module_name: " + module_name
        log_err.error(err)
        ret_msg= {'retcode': -1, 'retmsg': err}
        return ret_msg

    if releasing_check(middle_file_path_per_set, module_name, test_mode) != 0:
        err = "releasing_check failed, check :" + module_name + " status failed"
        ret_msg= {'retcode': -1, 'retmsg': err}
        return ret_msg

    ret_msg= {'retcode': 0, 'retmsg': "releasing succeed"}
    return ret_msg

def help():
    print " Usage: " + sys.argv[
        0] + " [region] [set_id] [binary_file] [test_mode] [optional: conf_roolback_uuid]"


def main():
    #re = ymer_release_fast("idun", "hn02", "3101", "idun-21.03.12-6cc73fd-centos7-x86_64", "172.20.180.156",0)
    re = ymer_release_fast("hela", "hn02", "3101", "hela-21.03.23-482fb97-centos7-x86_64", "172.20.180.156",0)
    print re
    print re["retcode"] == -1
    print re["retmsg"]

if __name__ == "__main__":
    main()
