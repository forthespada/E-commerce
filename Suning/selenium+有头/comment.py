# -*- coding: utf-8 -*-
# @Time    : 2018/12/4 9:02
# @Author  : ForthEspada
import numpy as np
from multiprocessing import  Pool
import requests,re,json,time,pymongo,threading
from config import *
from lxml import etree
from pyquery import PyQuery as pq
import pandas as pd
from requests.exceptions import RequestException


lock = threading.Lock()

def get_url_from_mongo(): # 从数据库中选择商品href
	client = pymongo.MongoClient(MONGO_URL)
	db = client[MONGO_DB]
	table = db[MONGO_TABLE]
	href_data = pd.DataFrame(list(table.find())) 	# 选择需要显示的字段
	href_data = href_data[['href']] #data[['href'，'title']]  	# 打印输出
	return href_data

def write_comment_to_mongo(result):
	lock.acquire()
	client = pymongo.MongoClient(MONGO_URL)
	db = client[MONGO_DB]
	# if db[MONGO_COMMENT_TABLE].update({'href': product['href']}, {'$set': product}, True): # 去重功能
	if db[MONGO_COMMENT_TABLE].insert(result):
		pass# print("成功写入数据库",len(resulList),'条数据！')
	else:
		print("存储到MONGODB错误!\n",result)
	lock.release()

def get_one_page(url): # 获取界面text
	try:
		response = requests.get(url)
		if response.status_code == 200:
			return response.content.decode("utf-8")
		else:
			return None
	except RequestException:
		return None

def parse_one_page(url,product_id_first,product_id_second):
	global TOTAL_COMMENT_NUMBER
	html = get_one_page(url)
	if html == None:
		print("商品界面解析失败！",url)
		return None

	doc = pq(html) # 获取商品类别，标题，链接，描述描述
	items = doc('body > div.wrapper-allwidth > div > div.breadcrumb')
	category1 = items.find('#category1').text()
	category2 = items.find('div:nth-child(3) > span > a').text()
	category3 = items.find('div:nth-child(7) > span > a').text()
	category4 = items.find('#productName > a').text()
	product_categories= category1+"-"+category2+"-"+category3
	product_name = category4
	product_url = url
	product_description = doc.find('#itemDisplayName').text()

	#获取商品价格
	price_url = 'https://icps.suning.com/icps-web/getVarnishAllPrice014/'+'0'*(18-len(product_id_second)) + product_id_second+'_773_7730101_'+product_id_first+'_1_getClusterPrice.vhtm'
	price_text = requests.get(price_url).text
	price_text = price_text[17:][:-3] # 处理str，将其转化为json好转化的格式
	try:
		price_content = json.loads(price_text)
		product_price = price_content['price'].split('.')[0]
	except:
		print('price获取失败 ',price_url)
		product_price = None
	# print(product_categories,'  ',product_name,'  ',product_description,'  ',product_price)

	commentList = get_comment_from_page(html,product_id_first,product_id_second)
	for i in commentList:
		i['product_categories'] = product_categories
		i['product_name'] = product_name
		i['product_description'] = product_description
		i['product_price'] = product_price
		i['product_url'] = product_url
		write_comment_to_mongo(i)

	print('获取到商品评论',len(commentList),'条！')
	# write_comment_to_mongo(commentList)
	TOTAL_COMMENT_NUMBER += len(commentList)
	print("截至目前成功写入数据库",TOTAL_COMMENT_NUMBER,'条数据！')


def get_comment_from_page(html,product_id_first,product_id_second):
	commentpattern = re.compile(r'clusterId":"(.*?)"',re.S)
	clusterId = re.findall(commentpattern,html)
	comment_urls = ["https://review.suning.com/ajax/cluster_review_lists/general-"\
				  +str(clusterId[0])+"-"+"0"*(18-len(product_id_second))+ product_id_second+"-"+product_id_first+"-total-{0}-default-10-----reviewList.htm?callback=reviewList".format(i) for i in range(1,51)]
	# 苏宁默认最多显示50页的评论
	commentList = []
	for url in comment_urls:
		try:
			comment_text = requests.get(url).text
			comment_text = comment_text[11:][:-1]
			comment_list = json.loads(comment_text)['commodityReviews']
			for i in  range(10):
				comment_content = comment_list[i]['content']
				comment_time = comment_list[i]['publishTimeStr']
				comment_user_id = comment_list[i]['commodityReviewId']
				comment_user_nickname = comment_list[i]['userInfo']['nickName']
				comment_score = comment_list[i]['qualityStar']
				comment_like_num = get_comment_like_num(comment_user_id)
				comment = {
							'comment_user_id':comment_user_id,
							'comment_user_nickname':comment_user_nickname,
							'comment_score':comment_score,
							'comment_like_num':comment_like_num,
							'comment_content':comment_content,
							'comment_time':comment_time
						  }
				time.sleep(np.random.rand()/100)
				commentList.append(comment)
		except:
			continue
	return commentList

def get_comment_like_num(commodityReviewId):#获取点赞数
	time.sleep(np.random.rand()/100)
	url = 'https://review.suning.com/ajax/useful_count/'+str(commodityReviewId)+'-usefulCnt.htm'
	try:
		comment_like_num_text = requests.get(url).text
		comment_like_num_text = comment_like_num_text[10:][:-1]
		comment_like_num_list = json.loads(comment_like_num_text)
		return  comment_like_num_list['reviewUsefuAndReplylList'][0]['usefulCount']
	except:
		return None

def main(url):
	# for i in range(len(url_list)):
	# 	print(i,' ',url_list[i])
	# 	url = url_list[i]
		time.sleep(3*np.random.rand())
		if url.startswith('https://product.suning.com/0000000000/'):
			product_id_first = str(url.split('/')[3])
			product_id_second = str(url.split('/')[4].split('.')[0])
		elif url.startswith('https://th.suning.com/calCpcClicks'):
			idReg = re.compile(r'cmdCode=(.*?)&companyCode=(.*?)&')
			product_id = idReg.search(url)
			product_id_first = '0000000000'
			product_id_second = str(product_id.group(1))
		else:
			product_id_first = str(url.split('/')[3])
			product_id_second = str(url.split('/')[4].split('.')[0])
		parse_one_page(url,product_id_first,product_id_second)

if __name__ == "__main__":
	start_time = time.time()
	url_list = get_url_from_mongo().iloc[0:]['href']
	# thread_pool = []
	# print('一共有商品',len(url_list))
	# silce_list = int(len(url_list)/4) # 分成10个子线程
	# for i in range(3):
	# 	t = threading.Thread(target = main, args = ([url for url in url_list[i*silce_list:(i+1)*silce_list].copy()], ))
	# 	# 把新创建的线程加入到线程池
	# 	thread_pool.append(t)
	# 	# 启动线程子线程
	# 	t.start()
	# t = threading.Thread(target = main, args = ([url for url in url_list[9*silce_list:].copy()], ))
	# thread_pool.append(t)
	# t.start()
	#
	# for thread in thread_pool:
	# 	# 主线程等待所有子线程退出
	# 	thread.join()

	# silce_quarter = int(len(url_list)/3)
	# productList1 = url_list[676:silce_quarter].copy()
	# productList2 = url_list[silce_quarter:2*silce_quarter].copy()
	# productList3 = url_list[3*silce_quarter:].copy()
	# my_thread_1 = threading.Thread(target = main, args = ([i for i in productList1], ))
	# my_thread_2 = threading.Thread(target = main, args = ([i for i in productList2], ))
	# my_thread_3 = threading.Thread(target = main, args = ([i for i in productList3], ))
	# my_thread_1.start()
	# my_thread_2.start()
	# my_thread_3.start()
	# my_thread_1.join()
	# my_thread_2.join()
	# my_thread_3.join()


	# for i in range(184,len(url_list)+1):
	# 	print(i,' ',url_list[i])
	# 	t = threading.Thread(target=main, args=(url_list[i],))
	# 	t.start()
	# 	t.join()

	# halflist = int(len(url_list)/2)
	# productList1 = url_list[676:halflist].copy()
	# productList2 = url_list[halflist:2].copy()
	# my_thread_1 = threading.Thread(target = main, args = ([i for i in productList1], ))
	# my_thread_2 = threading.Thread(target = main, args = ([i for i in productList2], ))
	# my_thread_1.start()
	# my_thread_2.start()
	# my_thread_1.join()
	# my_thread_2.join()

	# for i in range(5377,len(url_list)+1):
	# 	print(i,' ',url_list[i])
	# 	main(url_list[i])
	pool = Pool(2)
	pool.map(main,url_list)
	pool.close()
	pool.join()

	end_time = time.time()
	times = end_time - start_time
	m, s = divmod(times, 60)
	h, m = divmod(m, 60)  # 转化整个爬取时间为时分秒的形式
	print("所花费总时间为%d时%02d分%02d秒" % (h, m, s))