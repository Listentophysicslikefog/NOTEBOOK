#!/usr/bin/env python2
# coding=utf8

import os, sys
sys.path.append(
  os.path.abspath(os.path.join(__file__, '../../../../../third_part/message')))
sys.path.append(
  os.path.abspath(os.path.join(__file__, '../../../../../third_part/wiwo_python')))
sys.path.append(
  os.path.abspath(os.path.join(__file__, '../../../../libs')))
import fastcall
from wiwo_python import Client
import ubs2_pb2 as udisk
sys.path.append(os.path.abspath(os.path.join(__file__, '../../../../libs')))
from zk_helper_v1 import get_service_ip_port
import log_info

global log
log = log_info.logger()

def destory_udisk(ip, port, extern_id):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    client = Client(ip, port)
    try:
        client.connect()
    except Exception as e:
        err = "connect buddy failed. ip:" + str(ip) + " port:" + str(port) + ". error:" +  str(e)
        log_err.error(err)
        return -1

    req = udisk.DestroyUBSRequest();
    req.ubs_id = extern_id
    res = client.request(req, udisk.DESTROY_UBS_REQUEST,
                         udisk.destroy_ubs_request,
                         udisk.destroy_ubs_response)

    if res.rc.retcode != 0:
        err = "Failed to get delete udisk. res:" + str(res)
        log_err.error(err)
        error = " error is: " + str(res.rc.error_message)
        log_err.error(error)
        return -1
    destory_info = "send delete udisk to buddy success. result: " + str(res)
    log_inf.info(destory_info)
    return 0


def get_buddy_ip(region, set_id):
  global log
  log_err = log.get_error_handle()
  log_inf = log.get_info_handle()
  if os.environ.has_key("LIMAX_DIR"):
    region_dir = os.path.join(os.environ["LIMAX_DIR"],
                              "udisk", "region", region)
  else:
    region_dir = os.path.join(os.environ["HOME"], "limax",
                             "udisk", "region", region)
  if not os.path.exists(region_dir):
    err = "region:" + region + "  set_id:" + str(set_id) + " dir: " + str(region_dir) +  " not exists"
    log_err.error(err)
    return -1,None,None
  set_name = "set" + str(set_id)
  buddy_zk_path = os.path.join("/NS/udisk", set_name, "UBSMaster")
  zk_addr = fastcall.get_zookeeper_servers(region, set_id)
  ip, port= get_service_ip_port(zk_addr, buddy_zk_path)
  return 0,ip,port

def ymer_destory_udisk(region, set_id, extern_id):
    global log
    log_err = log.get_error_handle()
    log_inf = log.get_info_handle()
    rc,ip,port = get_buddy_ip(region, set_id)
    if rc !=0 or ip == None or port == None:
        err = "get buddy ip port error. rc: " + str(rc) + " ip:" + str(ip) + " port:" + str(port)
        log_err.error(err)
        return -1
    rc = destory_udisk(ip, port, extern_id)
    if rc != 0:
        err = "delete udisk failed or connect buddy failed."        
        log_err.error(err)
        return -1
    info = "delete udisk: " + extern_id + " success"
    log_inf.info(info)
    return 0
if __name__ == "__main__":
  if len(sys.argv) < 4:
    print " Usage: " + sys.argv[0] + " <region> <set> <extern_id>"
    sys.exit(1)
  region = sys.argv[1]
  set_id = sys.argv[2]
  extern_id = sys.argv[3]
  #ip, port = get_buddy_ip(region, set_id)
  #destory_udisk(ip, port, extern_id)
  rc = ymer_destory_udisk(region, set_id, extern_id)
  print rc

