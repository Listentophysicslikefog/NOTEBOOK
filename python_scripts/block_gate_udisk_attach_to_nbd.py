#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import fcntl
import os
import time
import sys
import commands
ERR = 1
OK = 0
LOCK = "False"
class UDiskNbdLock(object):
	def __init__(self, udisk_dir, udsik_file):
		if not os.path.exists(udisk_dir):
			os.makedirs(udisk_dir)
		try:
			self.file_name = udisk_dir + udsik_file + ".lock"
			self.handle = open(self.file_name, 'wb')
		except Exception:
			print("'%s' cannot open: %s " % (os.getpid(), self.file_name))
			print(2)
                        print("Open lock file fail")
                        print(None)
			exit(1)
		if self.lock() == False:
			print("'%s' __init__ " % (self.file_name))
			print("lock file error, maybe file has be lock")
			print(2)
			print("Not grab the lock")
			print(None)
			exit(1)
	def __del__(self):
		try:
			self.unlock()
			self.handle.close()
		except:
			pass

	def lock(self):
       # '''同步锁,其他进程获取不到需等待 | fcntl.LOCK_NB 函数不能获得文件锁就立即返回 '''
		try:
			fcntl.flock(self.handle, fcntl.LOCK_EX|fcntl.LOCK_NB)
			print("'%s' locked successful: %s " % (self.file_name, os.getpid()))
			global LOCK
			LOCK = "True"
			return True
		except:
			print("'%s' locked failed: %s " % (self.file_name, os.getpid()))
			return False

	def unlock(self):
		try:
			fcntl.flock(self.handle, fcntl.LOCK_UN)
			if LOCK == "True":
				print("'%s' unlocked successful: %s " % (self.file_name, os.getpid()))
		except:
			if LOCK == "True":
				print("'%s' unlocked failed: %s " % (self.file_name, os.getpid()))
				return False
def help():
	print(sys.argv[0] + " <udisk_id>")

def execCmd(cmd):
	r = os.popen(cmd)
	text = r.read()
	r.close()
	return text

def add_qemu_nbd(udisk_id):
     #''' 1. lock global nbd '''
	#nbd_lock = UDiskNbdLock("/var/lock/","login_nbd")
	nbd_lock = UDiskNbdLock("/var/lock/","login_nbd")
	(nbd_lock)  #clean warning
	time.sleep(9)
	GetNbd=""
	nbdPath = ""
	cmdudisk = "ps aux | grep -w " + udisk_id  + " | grep -v grep | grep -v python"
	cmdudiskres = execCmd(cmdudisk)
	if len(cmdudiskres) != int(0):
		print(cmdudiskres)
		print("this udisk is attatched")
		return ERR,None
	cmd = "ls /dev/nbd* | grep \"nbd[0-9]\+$\""
	output =execCmd(cmd)# subprocess.getstatusoutput(cmd)
	res = output.split("\n")
	#print(res)
	for i in range(len(res)-1): 
		ret = os.access(res[i],os.F_OK)
		if str(ret) != 'True':
			print("this nbd may be broken:%s" % ret)
		getNbdCmd = "ps aux | grep " + res[i] + " | grep -cv grep"
		print("this nbd not bad:%s" % res[i])
		nbdstatus = execCmd(getNbdCmd)#commands.getstatusoutput(getNbdCmd)
		print(nbdstatus)
		nbdstatus = nbdstatus.split("\n")
		del nbdstatus[-1]
		print(nbdstatus)
		if  nbdstatus[0] == "0":
			GetNbd = res[i]
			print(GetNbd)
			nbdPath = "/sys/block/nbd" + str(i) + "/pid"
			print(nbdPath)
			try:
				if os.path.getsize(nbdPath) > 0:
					print('pid not empty nbd is using')
					GetNbd = ""
				else:   #print('empty file')
					print('pid is empty nbd is using')
					GetNbd = ""
        # Empty file exists
			except OSError as e:
				print("pid not exit in this nbd, so this nbd can be use ")
				break
    # File does not exists or is non accessible
	if GetNbd == "":
		print("get nbd error")
		return ERR, None
   # ''' 3. attach udisk to nbd device'''
	cmd = "qemu-nbd -c " + GetNbd + " udisk:block-udisk:6688:%s -f raw"  % (udisk_id)
	output = execCmd(cmd)#subprocess.getstatusoutput(cmd)
	print(len(output))
	if len(output) == 0:
		print("success attatch udisk to nbd")
		return OK,GetNbd
	else:
		return ERR,None
if __name__ == "__main__":
	if len(sys.argv) == 2:
		udisk_id = sys.argv[1]
	else:
		help()
		exit(1)
	#nbd_lock = UDiskNbdLock("/var/lock/","login_nbd_chaos")
	retcod,nbds = add_qemu_nbd(udisk_id)
	print(retcod)
	print(LOCK)
	print(nbds)
	exit(0)
	
