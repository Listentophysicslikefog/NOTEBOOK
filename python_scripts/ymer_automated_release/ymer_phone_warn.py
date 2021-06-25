#!/usr/bin/python
# -*- coding: UTF-8 -*-
import sys, os, time
import zookeeper
sys.path.append(
  os.path.abspath(os.path.join(__file__, '../../../../../third_part/message')))
sys.path.append(
  os.path.abspath(os.path.join(__file__, '../../../../../third_part/wiwo_python')))
sys.path.append(
  os.path.abspath(os.path.join(__file__, '../../../../libs')))
sys.path.append(
  os.path.abspath(os.path.join(__file__, '../../ums/108000')))
import fastcall
import log_info
import udisk_pb2, uns_pb2, wiwo_python, ubs2_pb2
import ums

zk_path_prefix = "/NS/udisk"
global log
log = log_info.logger()


def ymer_deploy_phone_warn(ip, port, region, set_id, message):
  global log
  log_err = log.get_error_handle()
  log_inf = log.get_info_handle()
  client = wiwo_python.Client(ip, port)
  try:
    client.connect()
  except Exception as e:
    return

  req = ums.PushMessageRequest()
  #reqLogicalChunkInfo = ubs2_pb2.CloneLogicalChunkRequest()
  #reqLogicalChunkInfo.size = 20
  #reqLogicalChunkInfo.lc_name = "hongwei_test_"
  #reqLogicalChunkInfo.company_id = 50140849
  #reqLogicalChunkInfo.account_id = 55741713
  #reqLogicalChunkInfo.lc_id = "hongwei_test_"
  #req.lc_info = reqLogicalChunkInfo 
  req.notify_type = 1
  req.authkey = 562774067
  dest_obj = req.dest_object.add()
  dest_obj.message_type= 12
  #dest_obj.message_type_v2= 4
  dest_obj.phone.append("15304866027")
  dest_obj.content= str(message)
  req_info = "send phone warn request: " + str(req) + "  region: " + str(region) + "  set_id: " + str(set_id)
  log_inf.info(req_info) 
  
  res = client.request(req, ums.PUSH_MESSAGE_REQUEST,
                         ums.push_message_request,
                         ums.push_message_response)
  res_info = "send phone warn response: " + str(res) + "  region: " + str(region) + "  set_id: " + str(set_id)
  log_inf.info(res_info)

def deploy_phone_warn(region, set_id, message):
  ymer_deploy_phone_warn("172.27.116.103","6507", region, set_id, message)

def help():
  print " Usage: " + sys.argv[0] + " [region] [set_id]"
def main():
  if len(sys.argv) >= 3:
    help()
    sys.exit(1)
#ymer_deploy_phone_warn("172.27.116.103","6507", "hn02", "6666", "hn02 1102 发布ymer克隆模块失败")
#deploy_phone_warn("hn02",1102,"hn02 1102 发布ymer克隆模块失败")

if __name__ == "__main__":
  main()

