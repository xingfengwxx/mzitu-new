#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-11-28 17:14:46
# @Author  : swz
# @Email   : js_swz2008@163.com
from bs4 import BeautifulSoup
import os
from download import http
import pymongo
import datetime
import re
import shutil

class mzitu():

    def __init__(self):
        self.client = pymongo.MongoClient('localhost',27017)
        self.mzitu = self.client['mzitu']
        self.meizitu_collection =self.mzitu['mzituinfo']
        self.title = '' ##用来保存页面主题
        self.url = '' ##用来保存页面地址
        self.img_urls = [] ##初始化一个列表用来保存图片地址

    def all_url(self, url):
        html = http.get(url, 5) ##
        all_a = BeautifulSoup(html.text, 'lxml').find('div', class_='all').find_all('a')
        if url == 'http://www.mzitu.com/all':
            del all_a[0] ##删除第一个a标签
            self.mkdir('无主题')
        for a in all_a:
            title = a.get_text()
            self.title = title ##将主题保存到self.title中
            print(u'开始保存：', title)
            if not self.mkdir(title): ##跳过已存在的文件夹
                print(u'已经跳过：', title)
                continue
            href = a['href']
            self.url = href ##将页面地址保存到self.url中
            if self.meizitu_collection.find_one({'主题页面': href}):  ##判断这个主题是否已经在数据库中、不在就运行else下的内容，在则忽略。
                print(u'这个页面已经爬取过了')
            else:
                self.html(href)
        print(u'恭喜您下载完成啦！')
        ##把目录外的图片移动到“无主题”
        self.mvfile("E:/","E:/mzitu/无主题")

    def html(self, href):
        html = http.get(href, 5)##
        max_span = BeautifulSoup(html.text, 'lxml').find('div', class_ ='pagenavi').find_all('span')[-2].get_text()##获取最大页数
        page_num = 0  ##这个当作计数器用 （用来判断图片是否下载完毕）
        for page in range(1, int(max_span) + 1):
            page_num = page_num + 1 ##每for循环一次就+1(当page_num等于max_span的时候，就证明我们的在下载最后一张图片了）
            page_url = href + '/' + str(page)
            self.img(page_url, max_span, page_num) ##把上面需要的两个变量，传递给下一个函数

    def img(self, page_url, max_span, page_num): ##添加上面传递的参数
        img_html = http.get(page_url, 5) ##
        img_url = BeautifulSoup(img_html.text, 'lxml').find('div', class_='main-image').find('img')['src']
        self.img_urls.append(img_url) ##每一次 for page in range(1, int(max_span) + 1)获取到的图片地址都会添加到 img_urls这个初始化的列表
        if int(max_span) == page_num: ##传递下来的两个参数 当max_span和Page_num相等时，就是最后一张图片了，最后一次下载图片并保存到数据库中。
            self.save(img_url,page_url)
            post = {  ##构造一个字典
                '标题': self.title,
                '主题页面': self.url,
                '图片地址': self.img_urls,
                '获取时间': datetime.datetime.now()
            }
            self.meizitu_collection.save(post) ##将post中的内容写入数据库。
            print(u'#############################插入数据库成功############################')
        else:  ##max_span 不等于 page_num执行这下面
            self.save(img_url,page_url)

    def save(self, img_url, page_url):
        """
        :param img_url: 图片的url
        :param page_url: 页面地址的url
        :return: true/false
        """
        name = img_url[-9:-4]
        try:
            print(u'保存文件：', img_url)
            img = http.requestpic(img_url,page_url)
            f = open(name + '.jpg', 'ab')
            f.write(img.content)
            f.close()
        except FileNotFoundError: ##捕获异常，继续往下走
            print(u'图片不存在已跳过：', img_url)
            return False

    def mkdir(self, path): ##这个函数创建文件夹
        """
        :param path: 创建目录的名字
        :return: true/false
        """
        path = self.strip(path) ##创建目录过滤非法字符
        isExists = os.path.exists(os.path.join("E:/mzitu", path))
        if not isExists:
            print(u'建了一个：', path, u'的文件夹！')
            os.makedirs(os.path.join("E:/mzitu", path ))
            os.chdir(os.path.join("E:/mzitu", path)) ##切换到目录
            return True
        else:
            print(u'名字叫做：', path, u'的文件夹已经存在了！')
            return False

    def strip(self, path):
        """
        :param path: 需要清洗的文件夹名字
        :return: 清洗掉Windows系统非法文件夹名字的字符串
        """
        path = re.sub(r'[\\*|<>/:?"]', '', str(path))
        return path

    def mvfile(self, path, newpath):##移动文件到指定目录
        """
        :param path: 移动文件所在路径
        :param newpath: 移动文件目标路径
        :return: None
        """
        for item in os.listdir(path):#遍历该路径中文件和文件夹
            name = os.path.basename(item)  # 获取文件名
            full_path = os.path.join(path, name)  # 将文件名与文件目录连接起来，形成完整路径
            if name.endswith('jpg'):##判断是否是图片类型
                shutil.move(full_path, newpath)#移动文件到目标路径（移动+重命名）
                print(u'###########',name,u'没有主题，已移动到无主题！###########')

    def rmdir(self,path):##清理空文件夹和空文件
        """
        :param path: 文件路径，检查此文件路径下的子文件
        :return: None
        """
        for item in os.listdir(path):#遍历该路径中文件和文件夹
            full_path = os.path.join(path, item)  # 将目录与文件目录连接起来，形成完整路径
            if not os.listdir(full_path):  # 如果子文件为空
                shutil.rmtree(full_path,True)#递归删除
                print (u'#########################',full_path,u'目录为空，已清理成功!########################')

Mzitu = mzitu() ##实例化
Mzitu.all_url('http://www.mzitu.com/all') ##给函数all_url传入参数  可以当作启动爬虫（就是入口）
# Mzitu.all_url('http://www.mzitu.com/old') ##爬取早期图片
Mzitu.rmdir('E:/mzitu')##删除空目录和空文件
