# -*- coding: utf-8 -*-
# @Time    : 2018/12/4 19:33
# @Author  : ForthEspada
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

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('disable-infobars')#谷歌不出现在被自动化工具控制
# chrome_options.add_argument('--headless') # 无头浏览器设置, 使用无头容易出错
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_options.add_experimental_option("prefs", prefs) # 不加载图片设置
chrome_options.add_argument('User-Agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36"') # 谷歌文档提到需要加上这个属性来规避bug
chrome_options.add_argument('--disable-gpu') # 谷歌文档提到需要加上这个属性来规避bug
# chrome_options.add_argument(r'--user-data-dir=C:\Users\ADMINI~1\AppData\Local\Temp\scoped_dir11488_22853\Default') # 谷歌有时候大姨妈 需要加上这个 将其中的路径 设置成用户自己的数据目录
browser = webdriver.Chrome(chrome_options=chrome_options)
wait = WebDriverWait(browser,30) # 等待网页反应最多10秒

def scroll_down(): #下滑操作
	sroll_cnt = 0
	while  True:
		if (sroll_cnt) < 15:
				browser.execute_script('window.scrollBy(0, 2000)')
				time.sleep(0.5*np.random.rand())
				sroll_cnt += 1
		else:
			break

def open(KEY_WORD):
	try:
		browser.get('https://www.suning.com/')
		# search_input=browser.find_element_by_id('searchKeywords') #searchKeywords
		search_input = wait.until(
			EC.presence_of_element_located((By.CSS_SELECTOR,'#searchKeywords'))
		)
		search_input.send_keys(KEY_WORD)
		time.sleep(3)
		search_btn=wait.until(
			EC.presence_of_element_located((By.CSS_SELECTOR,'#searchSubmit'))
		)
		search_btn.click()
	except:
		open(KEY_WORD)

def parse_page(page_number):

	scroll_down()
	productlist = []
	wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#product-wrap > div.product-list > ul > li')))
	items =  browser.find_elements_by_css_selector('#product-wrap > div.product-list > ul > li')
	for item  in items:
		try:
			element_temp =  item.find_element_by_css_selector('div.product-box> div.res-info > div.title-selling-point > a')
			title = element_temp.text
			href = element_temp.get_attribute("href")
			price = item.find_element_by_css_selector('div.product-box> div.res-info >div.price-box').text.lstrip('¥')
			shop =item.find_element_by_css_selector('div.product-box> div.res-info >div.store-stock').text#wait.until(item.find_element_by_css_selector('div.product-box> div.res-info >div.store-stock')).text
			product = {
			'title':title,
			'href':href,
			'price':price,
			'shop':shop,
			}
			productlist.append(product)
			time.sleep(np.random.rand())
			# write_to_database(product)
			# print(product)
		except:
			continue

	time.sleep(3*np.random.rand())
	print("第",page_number,"页数据爬取完毕，共",len(productlist),"条")
	if(page_number == 50):# 苏宁默认最多显示50页的搜索结果,50页就结束循环，否则继续翻页
		return None
	else:
		next_page(page_number)

def next_page(page_number):
	try:
		input = wait.until(
				EC.presence_of_element_located((By.CSS_SELECTOR,'#bottomPage'))#当前界面是页码输入框
			)
		submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#bottom_pager > div > a.page-more.ensure')))#确定按钮，第多少页后面的按钮
		input.clear() # 去掉以前的页码
		input.send_keys(page_number+1) #输入新的页码
		submit.click()
		time.sleep(5)
		wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#search-path > h1')))#等待翻页过程
		url = browser.current_url # 翻页后，获取当前页面url
		print('在浏览第',page_number+1,'页的数据')
		print("此时页面url为：",url)
		print('开始爬取第',page_number+1,'页的数据')
		parse_page(page_number+1)
	except TimeoutError:
		next_page(page_number)

def write_to_database(product):
	client = pymongo.MongoClient(MONGO_URL)
	db = client[MONGO_DB]
	try:
		# if db[MONGO_TABLE].update({'title': product['title']}, {'$set': product}, True):
		if db[MONGO_TABLE].update({'href': product['href']}, {'$set': product}, True):
		# # if db[MONGO_TABLE].insert(product):
			pass
	except Exception:
		print("存储到MONGODB错误!\n",product)
		return None

def main():
	start_time = time.time()
	open(KEY_WORD)
	page_number = 1
	parse_page(page_number)
	end_time = time.time()
	seconds =end_time - start_time
	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)  # 转化整个过程时间为时分秒
	print("所花费总时间为%d时%02d分%02d秒" % (h, m, s))

if __name__ == '__main__':
	main()
