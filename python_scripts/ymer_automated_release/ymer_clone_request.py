#!/usr/bin/python
# -*- coding: UTF-8 -*-
import sys, os, time
import zookeeper
sys.path.append(
  os.path.abspath(os.path.join(__file__, '../../../../third_part/message')))
sys.path.append(
  os.path.abspath(os.path.join(__file__, '../../../../third_part/wiwo_python')))
sys.path.append(
  os.path.abspath(os.path.join(__file__, '../../../libs')))
import fastcall
import udisk_pb2, uns_pb2, wiwo_python, ubs2_pb2
import log_info
import re
zk_path_prefix = "/NS/udisk"

global log
log = log_info.logger()


def checkip(ip):
  p = re.compile(
      '^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
  if p.match(ip):
      return True
  else:
      return False



def pb_clone_request(ip, port, set_id, image_id, image_size, generate_disk_id):
  global log
  log_err = log.get_error_handle()
  log_inf = log.get_info_handle()

  client = wiwo_python.Client(ip, port)
  try:
    client.connect()
  except Exception as e:
    err = " Connect access  client ip: " + str(ip) + " port: " + str(port) + " error :%s" % str(e)
    log_err.error(err)
    ret_msg= {'retcode': -1, 'retmsg': err}
    return ret_msg

  req = ubs2_pb2.CloneUBSRequest()
  #reqLogicalChunkInfo = ubs2_pb2.CloneLogicalChunkRequest()
  #reqLogicalChunkInfo.size = 20
  #reqLogicalChunkInfo.lc_name = "hongwei_test_"
  #reqLogicalChunkInfo.company_id = 50140849
  #reqLogicalChunkInfo.account_id = 55741713
  #reqLogicalChunkInfo.lc_id = "hongwei_test_"
  #req.lc_info = reqLogicalChunkInfo 
  req.lc_info.size = int(image_size)  #20
  req.lc_info.lc_name = "hongwei_ymer_clone_verification" #hongwei_202105ymer
  req.lc_info.company_id = 50140849
  req.lc_info.account_id = 55741713
  req.lc_info.id =  str(generate_disk_id)  #"hongwei_202105ymer22" #hongwei_202105ymer
  req.lc_info.disk_type = 5
  req.parent_lc_id = str(image_id)  #"bsi-o1y4hh"
  req.set_id = int(set_id)  #3101
  req_info =" clone request to access ip: " + str(ip) + " port: " + str(port) + " request:  " +  str(req)
  log_inf.info(req_info)
  res = client.request(req, ubs2_pb2.CLONE_UBS_REQUEST,
                       ubs2_pb2.clone_ubs_request,
                       ubs2_pb2.clone_ubs_response)
  print str(res)
  if res.rc.retcode != 0:
    err = " clone udisk request fail, maybe udisk set resourse not enough or access ip or source image error.  error: " + str(res.rc.error_message)
    log_err.error(err)
    ret_msg= {'retcode': -1, 'retmsg': err}
    return ret_msg
  else:
    res_info = " clone request to access success. ip: " + str(ip) + " ubs_id: " + str(res.ubs_id) 
    ret_msg= {'retcode': 0, 'ubs_id': str(res.ubs_id), 'retmsg': res_info}
    log_inf.info(res_info)
    return ret_msg
  #print str(res.rc.retcode), str(res.rc.error_message), str(res.ubs_id)

def clone_request(region, set_id, image_id, image_size, generate_disk_id):
  global log
  log_err = log.get_error_handle()
  log_inf = log.get_info_handle()
  if os.environ.has_key("LIMAX_DIR"):
    region_dir = os.path.join(os.environ["LIMAX_DIR"], "udisk", "region", region)
  else:
    region_dir = os.path.join(os.environ["HOME"], "limax", "udisk", "region", region)
  if not os.path.exists(region_dir):
    err = region_dir + " not exist" + "  region: " + region + " set_id: " + str(set_id)
    log_err.error(err)
    ret_msg= {'retcode': -1, 'retmsg': err}
    return ret_msg
    
  access_file = os.path.join(region_dir, "access")
  if not os.path.exists(access_file):
    err = " access file: "  + str(access_file) +  " not exist" + "  region: " + region + " set_id: " + str(set_id)
    log_err.error(err)
    ret_msg= {'retcode': -1, 'retmsg': err}
    return ret_msg
  access_info = open(access_file).read().split("\n")
  access_ip = ""
  for ip in access_info:
    access_ip = ip
    if checkip(access_ip) == False:
      continue
    else:
      break
  ret = pb_clone_request(ip, 10086, set_id, image_id, image_size, generate_disk_id)
  return ret
def help():
  print " Usage: " + sys.argv[0] + " [region] [set_id] [image_id] [image_size] [generate_disk_id]"


def main():
  if len(sys.argv) != 6:
    help()
    sys.exit(1)
  region = sys.argv[1]
  set_id = sys.argv[2]
  image_id = sys.argv[3]
  image_size = sys.argv[4]
  generate_disk_id = sys.argv[5]
  #ret = clone_request(region, set_id, image_id, image_size, generate_disk_id)
  print str(ret), ret["retcode"]==0


if __name__ == "__main__":
  main()

