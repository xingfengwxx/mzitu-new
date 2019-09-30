#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-11-29 14:35:35
# @Author  : swz
# @Email   : js_swz2008@163.com
import requests
import time
from lxml import etree
import pymongo

class IPProxyPool():
    
    def __init__(self):
        self.headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}
        self.url = 'http://www.xicidaili.com/nn/'
        self.client = pymongo.MongoClient('localhost',27017)
        self.xici = self.client['xici']
        self.xiciipinfo =self.xici['xiciipinfo']
        self.count(2)

    def getip(self,num):
        #爬西祠所有代理，更新放入数据库
        url = self.url + str(num)
        wb_data = requests.get(url, headers= self.headers)
        html = etree.HTML(wb_data.text)
        ips = html.xpath('//tr[@class="odd"]/td[2]/text()')
        ports = html.xpath('//tr[@class="odd"]/td[3]/text()')
        protocols = html.xpath('//tr[@class="odd"]/td[6]/text()')
        areas = html.xpath('//tr[@class="odd"]/td[4]/a/text()')
        for ip, port, protocol, area in zip(ips, ports, protocols, areas):
            data = {
                'ip': ip,
                'port': port,
                'protocol': protocol,
                'area': area
            }
            print ('保存代理ip信息：'+ str(data))
            self.xiciipinfo.save(data) ##将data中的内容写入数据库。
            # self.xiciipinfo.update({'ip':ip}, {'$set':data}, True)

    def count(self,num):
        for i in range(1,num):
            self.getip(i)
            time.sleep(1)
        map(self.iptest, self.getiplist())#验证删除不可用ip

    def dbclose(self):
        self.client.close()

    def getiplist(self):
        # 将数据库内数据整理放入列表
        ips = self.xiciipinfo.find()
        proxylist = []
        for i in ips:
            b = 'http:'+'//'+i['ip'] + ":" + i['port']
            proxies = {"http": b}
            proxylist.append(proxies)
        return proxylist

    def iptest(self, proxy):
        # 检测ip，并更新进入数据库，删掉不可用的ip
        ip = proxy['http'][7:].split(':')[0]
        try:
            requests.get('http://www.mzitu.com/all', proxies = proxy, timeout = 5)
        except:
            self.xiciipinfo.remove({'ip': ip})  # 用remove方法，将符合条件的删掉
            print ('remove it now.....{}'.format(ip))
        else:
            print ('<<<<<<<<<<<<<<<<<.............success:'+ proxy)

proxy = IPProxyPool()