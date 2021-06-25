#!/usr/bin/python
# -*-coding:UTF-8-*-
import logging
import os
import time
from logging import handlers
 
class logger(object):
  
  """
  终端打印不同颜色的日志，在pycharm中如果强行规定了日志的颜色， 这个方法不会起作用， 但是
  对于终端，这个方法是可以打印不同颜色的日志的。
  """ 
 
  #在这里定义StreamHandler，可以实现单例， 所有的logger()共用一个StreamHandler
  ch = logging.StreamHandler()
  def __init__(self):
    self.logger = logging.getLogger()
    if not self.logger.handlers:
      #如果self.logger没有handler， 就执行以下代码添加handler
      self.logger.setLevel(logging.DEBUG)
      self.log_path = os.getcwd()+"/ymer_deploy_log"
      if not os.path.exists(self.log_path):
        os.makedirs(self.log_path)
 
      # 创建一个handler,用于写入日志文件
      #fh = logging.FileHandler(self.log_path + '/ymer-deploy-' + time.strftime("%Y%m%d", time.localtime()) + '.log',encoding='utf-8')
      fh = handlers.RotatingFileHandler(self.log_path + '/ymer-deploy-' + time.strftime("%Y%m%d", time.localtime()) + '.log', maxBytes = 50*1024*1024, backupCount = 10, encoding='utf-8')
      fh.setLevel(logging.INFO)
 
      # 定义handler的输出格式
      #formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)05d',datefmt='%Y-%m-%d,%H:%M:%S')
      formatter = logging.Formatter(fmt='[%(asctime)s.%(msecs)03d] - [%(levelname)s] : %(message)s -  [%(filename)s:%(lineno)d]',datefmt='%Y-%m-%d,%H:%M:%S')
      #formatter = logging.Formatter('[%(asctime)s] - [%(levelname)s] - %(message)s')
      fh.setFormatter(formatter)
 
      # 给logger添加handler
      self.logger.addHandler(fh)
 
  def get_debug_handle(self):
    self.fontColor('\033[0;32m%s\033[0m')
    return self.logger
    #self.logger.debug(message)
 
  def get_info_handle(self):
    self.fontColor('\033[0;37m%s\033[0m')
    return self.logger
    #self.logger.info(message)
 
  def get_warning_handle(self):
    self.fontColor('\033[0;34m%s\033[0m')
    return self.logger
    #self.logger.warning(message)
 
  def get_error_handle(self):
    self.fontColor('\033[0;31m%s\033[0m')
    return self.logger
    #self.logger.error(message)
 
  def get_critical_handle(self):
    self.fontColor('\033[0;35m%s\033[0m')
    return self.logger
    #self.logger.critical(message)
 
  def fontColor(self, color):
    #不同的日志输出不同的颜色
    formatter = logging.Formatter(color % '[%(asctime)s] - [%(levelname)s] : %(message)s')
    self.ch.setFormatter(formatter)
    self.logger.addHandler(self.ch)
 
 
if __name__ == "__main__":
  logger = logger()
  log_warn = logger.get_warning_handle()
  log_warn.warning("12345")
  log_info = logger.get_info_handle()
  log_info.info("12345")
