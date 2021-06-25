#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import pymongo
import subprocess
import re
import logging
import requests
import log_info
import json
global log
log = log_info.logger()
g_robot_mikasa_url = "http://us3-api.prj-sre-rocket.svc.a3.gw.ucloudadmin.com/v1/robot"
g_robot_name = "UDisk-MikasaRobot"
g_msg_type = "markdown"
# 例子：sendmsg_by_robot_name("UDisk-MikasaRobot", "消息测试，请忽略！", "markdown")


def sendmsg_by_robot_name(robotname, msg, msgtype):
    global log
    log_inf = log.get_info_handle()
    datas = json.dumps({
        "name": robotname,
        "msgtype": msgtype,
        msgtype: {
            "content": msg
        }
    })

    res = requests.post(g_robot_mikasa_url, datas)
    #if res.code == 200:
        #info = "send message successful, retcode: " + str(res.code)
        #log_inf.info(info)
    req_info = "req msg:"+ str(msg)
    log_inf.info(req_info)
    res_info = "req result: " + str(res.json())
    log_inf.info(res_info)


def main():
    if len(sys.argv[1:]) < 1:
        help()
        sys.exit()

    msg = sys.argv[1]
    print "now is releasing test "
    sendmsg_by_robot_name(g_robot_name, "AutoRelease test, please ignore",
                          g_msg_type)


if __name__ == "__main__":
    main()
