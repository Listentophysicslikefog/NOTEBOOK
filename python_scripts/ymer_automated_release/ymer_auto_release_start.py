#!/usr/bin/python
# -*- coding:utf-8 -*-
import json
import os
import sys
import time
import socket
import log_info
import generate_freyr_conf
import generate_ymer_ip
import release_ymer
import ymer_clone_request
import get_clone_udisk_status
import destroy_udisk_by_set
import ymer_open_close_set
import ymer_check_deploy_environment
import ymer_phone_warn
import generate_hela_conf
import generate_idun_conf
import mikasa_robot
sys.path.append(
    os.path.abspath(os.path.join(__file__, '../../../../libs')))
import fastcall

#目前ymer变更，不同的net_typ、storage_type、disk_type类型配置都是一样的，我们任意选一种组合作为获取模板配置的路径即可，这里目前统一使用： tcp、raw、ssd
# net_type: tcp/rdma
# storage_type: raw/fs
# disk_type: raw/fs

global log
log = log_info.logger()

global global_lock_file
global_lock_file = ""

global deploy_region
deploy_region = ""

global all_release_set
all_release_set = [ ]  

global release_publish
release_publish = ""

global deploy_center
deploy_center = "172.20.180.156"

global clone_image
clone_image = ""

global image_size 
image_size = 0


class SetInfo:
    region = ""
    set_id = 0
    set_type = ""
    set_status_befor_release = 10
    set_status_now = 10

    def __init__(self,region, set_id, set_type, set_status_befor_release, set_status_now):
        self.region = region
        self.set_id = set_id
        self.set_type = set_type
        self.set_status_befor_release = set_status_befor_release 
        self.set_status_now = set_status_now

    def robot_send_msg(self, msg_info):
        #msg_base = " region: " + self.region + ", set: " + str(self.set_id)
        all_msg = msg_info #+ msg_base
        mikasa_robot.sendmsg_by_robot_name("UDisk-MikasaRobot", all_msg, "markdown")
    def dump_set_info(self):
        global log
        log_err = log.get_error_handle()
        log_inf = log.get_info_handle()
        set_info = "region : " + str(self.region) + " set_id: " + str(self.set_id) + "  set_type: " + str(self.set_type) + "  set_status_befor_release: " + str(self.set_status_befor_release) + " set_status_now:" + str(self.set_status_now)
        log_inf.info(set_info)
        
    def phone_warn(self,message):
        ymer_phone_warn.deploy_phone_warn(str(self.region), str(self.set_id), message)








def ReleaseStart():
    global deploy_center
    global release_publish
    global all_release_set
    global global_lock_file
    global clone_image
    global image_size
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    freyr_publish = "freyr-" + release_publish
    hela_publish = "hela-" + release_publish
    idun_publish = "idun-" + release_publish
    host_name = socket.getfqdn(socket.gethostname())
    for one_set in all_release_set:
        info = "Locked successfully. Ymer Begin releasing. Publishing machine:" + str(host_name) + " region: " + one_set.region + " set: " + str(one_set.set_id) + " set type :" + str(one_set.set_type) + " set status : " + str(one_set.set_status_now) + " release_publish: " + str(release_publish)
        log_inf.info(info)
        robot_msg = "Ymer Begin releasing. Publishing machine:" + str(host_name) + " region: " + one_set.region + " set: " + str(one_set.set_id) + " set type :" + str(one_set.set_type)
        one_set.robot_send_msg(robot_msg)
        if one_set.set_status_befor_release !=  one_set.set_status_now :
            err = "ERROR: set_status_befor_release: " + str(one_set.set_status_befor_release) + "  set_status_now: " + str(one_set.set_status_now) + "  not the same"
            log_err.error(err)
            one_set.robot_send_msg(err)
            phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " 开 始 克 隆 时  set 状 态 检 测 失 败"
            one_set.phone_warn(phon_warn_info)
            exit(-1)  
        # 1.关闭将要发布的set,关闭set 更改状态为10，只关闭开启的set，就是状态为0的set  更新set set_status_now的状态 
        if one_set.set_status_befor_release == 0 and one_set.set_status_now == 0:
            ret = ymer_open_close_set.change_set_status(one_set.region, one_set.set_id, 10)
            if ret != 0:
                err = "ERROR: ymer_open_close_set.change_set_status close set failed.  region: " + one_set.region + "  set_id: " + str(one_set.set_id)
                log_err.error(err)
                one_set.robot_send_msg(err)
                phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " 开 始 克 隆 时 关 闭 set 失 败"
                one_set.phone_warn(phon_warn_info)
                exit(-1)
            # 1.1 更新set对象的现在状态
            one_set.set_status_now = 10

        # 2.判断set的类型,开始变更不同类型的set
        if one_set.set_type == "non-p2p":
            #2.1 只变更freyr模块.  先刷配置文件
            ret = generate_freyr_conf.generate_config(one_set.region, str(one_set.set_id), "tcp", "raw", "ssd")
            if ret != 0:
                err = "ERROR: YmerAutoRelease generate freyr conf failed, set_type: non-p2p  region: " + one_set.region + " set_id: " + str(one_set.set_id)
                log_err.error(err)
                one_set.robot_send_msg(err)
                # robbot发消息  恢复set原来状态
                phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " 非 p2p 生 成 配 置 文 件 失 败"
                one_set.phone_warn(phon_warn_info)
                one_set.phone_warn(phon_warn_info)
                exit(ret)
            # 2.2 生成ymer相关ip list文件
            ret = generate_ymer_ip.generate_ymer_all_ip(one_set.region, str(one_set.set_id))
            if ret["retcode"] != 0:
                log_err.error(str(ret["retmsg"]))
                err = "ERROR: YmerAutoRelease generate ymer all ip_list  failed, set_type: non-p2p  region: " + one_set.region + " set_id: " + str(one_set.set_id)
                log_err.error(err)
                one_set.robot_send_msg(err)
                phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " 非 p2p 生 成 ip 列 表 失 败"
                one_set.phone_warn(phon_warn_info)
                exit(ret["retcode"])
                    
            # 2.3 开始变更ymer 模块
            ret = release_ymer.ymer_release_fast("freyr", one_set.region, str(one_set.set_id), freyr_publish, deploy_center, 0)
            if ret["retcode"] != 0:
                err = "ERROR: release_ymer.ymer_release_fast freyr failed.  error: "+ str(ret["retmsg"])
                log_err.error(err)
                one_set.robot_send_msg(err)
                phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " 非 p2p 变 更 失 败"
                one_set.phone_warn(phon_warn_info)
                exit(ret["retcode"])
            release_info = "release non-p2p complete. clone verification will be performed. region: " + one_set.region + " set_id: " + str(one_set.set_id) + " set type :" + str(one_set.set_type) + " set status : " + str(one_set.set_status_now)           
            log_inf.info(release_info)
            robot_msg = "release non-p2p complete. region: "+ one_set.region + " set_id: " + str(one_set.set_id) + " set type :" + str(one_set.set_type)
            one_set.robot_send_msg(robot_msg)
        # 2. p2p类型发布hela idun。freyr
        elif one_set.set_type == "p2p": 
            #2.1. 刷配置文件
            ret = generate_freyr_conf.generate_config(one_set.region, str(one_set.set_id), "tcp", "raw", "ssd")
            if ret != 0:
                err = "ERROR: YmerAutoRelease generate freyr conf failed, set_type: p2p  region: " + one_set.region + " set_id: " + str(one_set.set_id)
                log_err.error(err)
                one_set.robot_send_msg(err)
                # robbot发消息  恢复set原来状态
                phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " p2p 生 成 freyr 配 置 文 件 失 败"
                one_set.phone_warn(phon_warn_info)
                exit(ret)
             # 2.2 生成ymer相关ip list文件
            ret = generate_ymer_ip.generate_ymer_all_ip(one_set.region, str(one_set.set_id))
            if ret["retcode"] != 0:
                log_err.error(str(ret["retmsg"]))
                err = "ERROR: YmerAutoRelease generate ymer all ip_list  failed, set_type: p2p  region: " + one_set.region + " set_id: " + str(one_set.set_id)
                log_err.error(err)
                one_set.robot_send_msg(err)
                phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " p2p 生 成 ip 列 表  失 败"
                one_set.phone_warn(phon_warn_info)
                exit(ret["retcode"])
             # 2.3 开始变更ymer freyr 模块
            ret = release_ymer.ymer_release_fast("freyr", one_set.region, str(one_set.set_id), freyr_publish, deploy_center, 0)
            if ret["retcode"] != 0:
                err = "ERROR: release_ymer.ymer_release_fast freyr failed.  error: "+ str(ret["retmsg"])
                log_err.error(err)
                one_set.robot_send_msg(err)
                phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " p2p 变 更 freyr  失 败"
                one_set.phone_warn(phon_warn_info)
                exit(ret["retcode"])
            # 2.4 开始刷hela的配置 变更hela模块
            ret = generate_hela_conf.generate_config(one_set.region, str(one_set.set_id), "tcp", "raw", "ssd")
            if ret != 0:
                err = "ERROR:  YmerAutoRelease generate hela conf failed, set_type: p2p  region: " + one_set.region + " set_id: " + str(one_set.set_id)
                log_err.error(err)
                one_set.robot_send_msg(err)
                # robbot发消息  恢复set原来状态
                phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " p2p 生 成 hela 配 置 文 件 失 败"
                one_set.phone_warn(phon_warn_info)
                exit(ret)
            # 2.5 开始变更 hela模块
            ret = release_ymer.ymer_release_fast("hela", one_set.region, str(one_set.set_id), hela_publish, deploy_center, 0)
            if ret["retcode"] != 0:
                err = "ERROR: release_ymer.ymer_release_fast hela failed.  error: "+ str(ret["retmsg"])
                log_err.error(err)
                one_set.robot_send_msg(err)
                phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " p2p 变 更 hela  失 败"
                one_set.phone_warn(phon_warn_info)
                exit(ret["retcode"])
            #2.6 开始刷新idun配置
            ret = generate_idun_conf.generate_config(one_set.region, str(one_set.set_id), "tcp", "raw", "ssd")            
            if ret != 0:
                err = "ERROR: YmerAutoRelease generate idun conf failed, set_type: p2p  region: " + one_set.region + " set_id: " + str(one_set.set_id)
                log_err.error(err)
                one_set.robot_send_msg(err)
                # robbot发消息  恢复set原来状态
                phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " p2p 生 成 idun 配 置 文 件 失 败"
                one_set.phone_warn(phon_warn_info)
                exit(ret)
           # 2.5 开始变更 idun模块
            ret = release_ymer.ymer_release_fast("idun", one_set.region, str(one_set.set_id), idun_publish, deploy_center, 0)
            if ret["retcode"] != 0:
                err = "ERROR: release_ymer.ymer_release_fast hela failed.  error: "+ str(ret["retmsg"])
                log_err.error(err)
                one_set.robot_send_msg(err)
                phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " p2p 变 更 idun  失 败"
                one_set.phone_warn(phon_warn_info)
                exit(ret["retcode"])
            release_info = "release p2p complete. clone verification will be performed. region: " + one_set.region + " set_id: " + str(one_set.set_id) + " set type :" + str(one_set.set_type) + " set status : " + str(one_set.set_status_now)
            log_inf.info(release_info)
            robot_msg = "release p2p complete. region: " + one_set.region + " set_id: " + str(one_set.set_id) + " set type :" + str(one_set.set_type)
            one_set.robot_send_msg(robot_msg)
        else :
            err = "ERROR:  set type error. region: " + one_set.region + " set: " + str(one_set.set_id) + " set type :" + str(one_set.set_type)                    
            log_err.error(err)
            one_set.robot_send_msg(err)
            phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " set 类 型 错 误"
            one_set.phone_warn(phon_warn_info)
            exit(-1)
        # 3. 开始进行clone. 验证是否变更成功        
            # 3.1 clone的盘id
        # 变更后等待 ymer模块初始化完成
        time.sleep(9)
        t = time.time()
        generate_disk_id = "ymer_clone_" + str(long(t))
        ret = ymer_clone_request.clone_request(one_set.region, one_set.set_id, clone_image, image_size, generate_disk_id)
        if ret["retcode"] != 0:
            err = "ERROR: ymer_clone_request.clone_request clone failed. error: " + str(ret["retmsg"])
            log_err.error(err)
            one_set.robot_send_msg(err)
            phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " 变 更 完 成 验 证 失 败"
            one_set.phone_warn(phon_warn_info)
            exit(ret["retcode"])
        if ret["ubs_id"] != generate_disk_id:
            err = "ERROR: ubs_id: " + ret["ubs_id"] + " generate_disk_id: " + generate_disk_id + " are not the same"
            log_err.error(err)
            one_set.robot_send_msg(err)
            phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " 变 更 完 成 验 证 失 败"
            one_set.phone_warn(phon_warn_info)
            exit(-1)
        # 4. 判断clone是否完成
        ret = get_clone_udisk_status.check_clone_result(one_set.region, str(one_set.set_id), generate_disk_id)       
        if ret != 0:
            err = "ERROR:  maybe disk clone failed, ubs_id: " +  generate_disk_id +  ".  region: " + one_set.region + " set: " + str(one_set.set_id) + " set type :" + str(one_set.set_type)
            log_err.error(err)
            one_set.robot_send_msg(err)
            phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " 变 更 完 成 验 证 失 败"
            one_set.phone_warn(phon_warn_info)
            exit(-1)
        # 5. clone 完成 删除clone的盘
        ret = destroy_udisk_by_set.ymer_destory_udisk(one_set.region, str(one_set.set_id), generate_disk_id)
        if ret != 0:
            err = "ERROR:  destroy_udisk_by_set.ymer_destory_udisk destory disk failed. region: " + one_set.region + "  set_id: " + str(one_set.set_id) + " ubs_id: "  + generate_disk_id
            log_err.error(err)
            one_set.robot_send_msg(err)
            phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " 变 更 完 成 验 证 失 败"
            one_set.phone_warn(phon_warn_info)
            exit(-1)
        #6.恢复set为最开始的状态
        if one_set.set_status_now != one_set.set_status_befor_release:
            ret = ymer_open_close_set.change_set_status(one_set.region, one_set.set_id, 0)
            if ret != 0:
                err = "ERROR:  ymer_open_close_set.change_set_status close set failed.  region: " + one_set.region + "  set_id: " + str(one_set.set_id) + " want change status to:" + str(one_set.set_status_befor_release)
                log_err.error(err)
                one_set.robot_send_msg(err)
                phon_warn_info = str(one_set.region) + " " + str(one_set.set_id) + " 变 更 完 成 验 证 失 败"
                one_set.phone_warn(phon_warn_info)
                exit(-1)
        # 7. 继续变更下一个set
        #ymer_check_deploy_environment.remove_lock_file(global_lock_file)
        success_info = "region: " + one_set.region + "  set_id: " + str(one_set.set_id)  + " release finish. clone  verification complete. disk has been deleted, will release next set."
        log_inf.info(success_info)
        robot_msg = "region: " + one_set.region + "  set_id: " + str(one_set.set_id)  + " release finish. clone  verification complete."
        one_set.robot_send_msg(robot_msg)
    # 8. 变更完需要变更的所有set后解锁 
    ymer_check_deploy_environment.remove_lock_file(global_lock_file)
    success_info = "all set  release finish. clone  verification complete. lock has been released ."   
    log_inf.info(success_info)
    robot_msg = "all set  release finish. clone  verification complete."
    one_set.robot_send_msg(robot_msg)

def check_run_path():
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    runpath=os.getcwd()
    if runpath.find("limax") != -1:
        info = "running path is :" + str(runpath)
        log_inf.info(info)
    else:
        err = " running path is : " + str(runpath) + "err, please running script in /root/linax/udisk/tool/ymer_automated_release dir"
        log_err.error(err)
        one_set.robot_send_msg(err)
        sys.exit(-1)

def get_set_type(region, set_id):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    host_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                             "region", region, set_id, "host_info")

    p2p_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                           "region", region, set_id, "p2p_info")
    is_exit = os.path.exists(host_file)
    if not is_exit:
        err = "host_file not exit maybe region or set_id is error, please check carefully, region : " + region + "  set_id: " + set_id
        log_err.error(err)
        sys.exit(-1)
    if os.path.exists(p2p_file):
        info = "region :" + region + "  set_id: " + set_id + " is p2p set"
        log_inf.info(info)
        return "p2p"
    else:
        info = "region :" + region + "  set_id: " + set_id + " is non-p2p set"
        log_inf.info(info)
        return "non-p2p"

def judgement_set_type(release_type, set_type):
    get_set_type = [ "p2p", "non-p2p" ]
    config_type = [ "p2p", "non-p2p", "all" ]
    if (set_type in get_set_type) and (release_type in config_type):
        return 0
    else:
        return -1

def generate_release_set():
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    release_list_file = './release_lists.json'
    is_exists = os.path.exists("./release_lists.json")
    if not is_exists:
        err = "release_lists.json not exit"
        log_err.error(err)
        sys.exit(-1)
    with open(release_list_file) as f:
        load_data = json.load(f)
    config_info = str(json.dumps(load_data, indent=4, sort_keys=True))
    log_inf.info(config_info)
    global all_release_set
    global release_publish
    global deploy_region
    #print(json.dumps(load_data, indent=4, sort_keys=True))
    region_info = load_data.get("release_info")
    release_publish = load_data.get("version")
    print(release_publish)
    print len(region_info)
    if len(region_info) != 1:
        err = "release_info error. A release management machine can only release one region, you release: " + str(len(region_info)) + " region " 
        log_err.error(err)
        f.close()
        sys.exit(-1)
    for one_region in region_info:
        global clone_image
        global image_size
        
        print('region: ', one_region.get("region"))
        region = one_region.get("region")
        deploy_region = region
        lock_deploy_environment()
        release_type = one_region.get("release_type")
        print("release_one_region : %s , release_type: %s", one_region.get("release_one_region"), one_region.get("release_type"))
        clone_image = one_region.get("clone_image")
        image_size = one_region.get("image_size")
        print clone_image, image_size, type(image_size)
        release_set_list = {} 
        release_one_region = one_region.get("release_one_region")
        #print(release_one_region=="Yes")
        #print(type(release_one_region))
        if one_region.get("release_one_region") == "Yes":
            release_set_list = fastcall.get_all_sets_by_region(region)
            release_set_list.sort(reverse=False)
        elif one_region.get("release_one_region") == "No":
            release_set_list = one_region.get("set")
        else:
            err = "release_one_region type error , please use Yes or No, you use : " + str(one_region.get("release_one_region") )
            log_err.error(err)
            f.close()
            sys.exit(-1)
            
        for set_id in release_set_list:
                       
            set_type = get_set_type(region, str(set_id))
            #print('set-%d' % int(set_id))
            #obj = SetInfo(one_region.get("region"), set)
            #obj.analyze_set_info()
            set_status =  ymer_open_close_set.get_set_status(region, set_id)
            if set_status != 10 and set_status != 20 and set_status != 0:
                err = "set: "  + str(set_id) + "  status: " + str(set_status) + " is error "
                log_err.error(err)
                f.close()
                sys.exit(-1)
            if release_type == "p2p" and set_type == "p2p":
                obj = SetInfo(region, set_id, set_type, set_status, set_status)                  
                all_release_set.append(obj)
            if release_type == "non-p2p" and set_type == "non-p2p":
                obj = SetInfo(region, set_id, set_type, set_status, set_status)
                all_release_set.append(obj)
            if release_type == "all" and (set_type == "p2p" or set_type == "non-p2p"):
                obj = SetInfo(region, set_id, set_type, set_status, set_status)
                all_release_set.append(obj)
            else:
                rc = judgement_set_type(release_type, set_type)
                if rc != 0:
                    err = "release_type: " + release_type + " or set_type: "+ set_type  + "  is error"
                    log_err.error(err)
                    f.close()
                    sys.exit(-1)
                continue
    f.close()
    for one_set in all_release_set:
        one_set.dump_set_info()


# 需要先执行generate_release_set() 获取deploy_region 的值后才可以执行 但是先生成配置再检测可能导致同时有两个在发布时第二个发布覆盖正在发布的配置文件
# 但是生成配置是存放在不同的set的所有应该没什么影响
# 加锁 lock
def lock_deploy_environment():
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    global global_lock_file
    global deploy_region
    rc,host_name,host_ip,lock_name = ymer_check_deploy_environment.check_deploy_environment(deploy_region)
    if rc != 0 and host_name == None and host_ip == None and lock_name == None:
        err = "ymer_check_deploy_environment.check_deploy_environment check lock and deploy environment failed. region: " + deploy_region
        log_err.error(err)
        exit(-1)
    global_lock_file = lock_name
    info = "check_deploy_environment check lock and deploy environment success. region: " + deploy_region + "deploy  host name: " + str(host_name) + "  lock file : " + str(global_lock_file)
    log_inf.info(info)

def main():
    
    check_run_path()
    generate_release_set()
    #lock_deploy_environment()
    ReleaseStart()
if __name__ == "__main__":
    main()
