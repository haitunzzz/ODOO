#!/usr/bin/env python 
# -*- coding: utf-8 -*- 

from ftplib import FTP 

def ftp_up(filename = "test.txt"): 
    ftp=FTP() 
    ftp.set_debuglevel(2)#打开调试级别2，显示详细信息;0为关闭调试信息 
    ftp.connect('202.176.14.85')#连接 
    ftp.login('macftp','W@r@t@hs')#登录，如果匿名登录则用空串代替即可 
    print ftp.getwelcome()#显示ftp服务器欢迎信息 
    print(11)
    #ftp.cwd('xxx/xxx/') #选择操作目录 
    bufsize = 1024#设置缓冲块大小 
    file_handler = open(filename,'rb')#以读模式在本地打开文件 
    ftp.storbinary('STOR %s' % os.path.basename(filename),file_handler,bufsize)#上传文件 
    ftp.set_debuglevel(0) 
    file_handler.close() 
    ftp.quit() 
    print "ftp up OK" 
ftp_up()
