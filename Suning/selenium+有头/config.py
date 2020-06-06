import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import  WebDriverWait
from selenium.webdriver.support import  expected_conditions as EC
from lxml import etree
import re,time,requests,pymongo,json
import numpy as np
from config import *
from pyquery import PyQuery as pq
from requests.exceptions import  RequestException



KEY_WORD = '手机' # 搜索关键字

TOTAL_COMMENT_NUMBER = 0  # 自己指定爬取到的评论总条数为0

MONGO_URL = 'localhost'
MONGO_DB = 'suning'
MONGO_TABLE = 'test2' # 存入数据库的表名
MONGO_COMMENT_TABLE = 'cellphone_comment'

product_name=''
product_description=''
product_categories=''
product_price='' # 分别是商品标题，描述，类别，价格
comment_user_id=''
comment_user_nickname=''
comment_content=''
comment_score=''
comment_like_num=''
comment_time='' # 分别是评价id，文本，评分，点赞数，时间



