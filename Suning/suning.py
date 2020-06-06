# -*- coding: utf-8 -*-
# @Time    : 2018/12/15 23:26
import requests,re,time,json,pymongo
import numpy as np
import pandas as pd
from lxml import etree
from twilio.rest import Client
from requests.exceptions import RequestException


user_agent_list = [
		"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
 ]

headers = {'User-Agent':np.random.choice(user_agent_list)}

MONGO_URL = 'localhost'
MONGO_DB = 'suning'
MONGO_TABLE = 'suning_comment'
MONGO_TABLE_URL = 'suning_url'

def send_sms():
	# 从官网获得以下信息
	account_sid = 'ACe0b411d08bf5953830ee58ddc9e521e3'
	auth_token = '8533bf33d4be5df5e98ea4e835be442e'
	twilio_number = '+15134881641'

	my_number ="+8618556778689"
	msg='苏宁爬虫已完毕！'
	client = Client(account_sid, auth_token)
	try:
		client.messages.create(to=my_number, from_=twilio_number, body=msg)
		print('短信已经发送！')
	except ConnectionError as e:
		print('发送失败，请检查你的账号是否有效或网络是否良好！')
		return e


def distinct_url(products_sort_url,total_list_urls):
	# print(len(products_sort_url))
	# print(len(total_list_urls))
	temp = len(products_sort_url)
	for j in range(temp):
		i = products_sort_url[j]
		if i in total_list_urls:
			continue
		else:
			total_list_urls.append(i)
	print(len(total_list_urls))
def get_one_product_url_from_mongo():
	client = pymongo.MongoClient(MONGO_URL)
	db = client[MONGO_DB]
	try:
		product_url = db[MONGO_TABLE_URL].find_one({},{"product_url":{"$slice":1}})
		product_url = product_url['product_url']
		db[MONGO_TABLE_URL].delete_one({"product_url":product_url}) #取出元素后删除
		return product_url
	except:
		print("表suning_url取出数据错误")
def get_url_num_from_mongo():
	client = pymongo.MongoClient(MONGO_URL)  	# 连接数据库
	db = client[MONGO_DB]
	table = db[MONGO_TABLE_URL] 	# 读取数据
	data = pd.DataFrame(list(table.find())) 	# 选择需要显示的字段
	try:
		data = data[['product_url']] #data[['_id'，'product_url']]
		data = data['product_url']
		print("表suning_url中存在商品链接共",len(data),"个，开始爬取商品")
		return len(data)
	except:
		print("表suning_url中不存在元素")
		return None

def write_product_url_to_mongo(product_urls):
	client = pymongo.MongoClient(MONGO_URL)
	db = client[MONGO_DB]
	result = []
	# print(product_urls)
	for product_url in product_urls:
		product_url = {'product_url':product_url}
		result.append(product_url)
	if db[MONGO_TABLE_URL].insert_many(result):
		pass
	else:
		print("插入商品链接失败:",result)
			
def write_product_to_mongo(url,result): # 插入商品信息成功
	(product_id_first,product_id_second) = parse_product_id(url)
	product_id = {'product_id':product_id_first+'/'+product_id_second }
	result = {'product':result}
	client = pymongo.MongoClient(MONGO_URL)
	db = client[MONGO_DB]
	if db[MONGO_TABLE].update({'product_id':product_id['product_id']},{'$set':product_id},True) and db[MONGO_TABLE].update({'product_id':product_id['product_id']},{'$set':result},True):
			pass
	else:
		print("插入商品信息失败，商品url:",url)

def write_product_comments_to_mongo(result):
	client = pymongo.MongoClient(MONGO_URL)
	db = client[MONGO_DB]
	if db[MONGO_TABLE].insert(result):
		pass
	else:
		print("商品评论插入失败，商品url:","https://product.suning.com/"+result["product_id"] + ".html")


def write_comment_to_mongo(url,result): # 插入商品评论
	(product_id_first,product_id_second) = parse_product_id(url)
	product_id = {'product_id':product_id_first+'/'+product_id_second}
	client = pymongo.MongoClient(MONGO_URL)
	db = client[MONGO_DB]
	if db[MONGO_TABLE].update({'product_id':product_id['product_id']},{"$addToSet":{"comment":{"$each":result}}},True):
			pass
	else:
		print("插入商品评论失败，评论url:",url)
	# for i in range(len(result)):
	# 	comment = {'comment':result[i]}
	# 	client = pymongo.MongoClient(MONGO_URL)
	# 	db = client[MONGO_DB]
	# 	if db[MONGO_TABLE].update({'product_id':product_id['product_id']},{'$set':product_id},True) and db[MONGO_TABLE].update({'product_id':product_id['product_id']},{'$addToSet':comment},True):
	# 		pass
	# 	else:
	# 		print("插入商品评论失败，评论url:",url)

def parse_one_page(url): # 获取界面text
	for i in range(3):
		try:
			s = requests.Session()
			s.keep_alive = False
			response = s.get(url,headers=headers,timeout=3)
			if '返回首页' in response.text:
				# print("开始解析商品：",url)
				return response.text
		except Exception as e:
			# if 'Max retries exceeded with url' in str(e):
			# 	print("断网了,程序退出运行",e)
			# 	exit(-1)
			# else:
			print("出现错误！ERROR",e)
			pass
	return None

def parse_comment_page(url): # 评论界面可能获取失败或者当前界面本来就为空即评论没有了
	for i in range(3):
		try:
			s = requests.Session()
			s.keep_alive = False
			response = s.get(url,headers=headers,timeout=3)
			content = response.text
			if content:
				comment_list = json.loads(content[11:][:-1])['commodityReviews']
				if len(comment_list) != 0:
					for i in range(len(comment_list)):
						if comment_list[i]['content'] =="买家没有填写评价内容！":
							comment_list = comment_list[:i]
							break
					return comment_list
		except Exception as e:
			# if 'Max retries exceeded with url' in str(e):
			# 	print("断网了,程序退出运行",e)
			# 	exit(-1)
			# else:
			print("出现错误！ERROR",e)
			pass
	return None

def parse_list_page(list_url,page_num):
	list_id = list_url.split('-')[1]
	product_urls = []
	for i in range(4):
		list_url_temp = 'https://list.suning.com/emall/searchV1Product.do?ci='+str(list_id)+'&pg=03&cp='+str(page_num)+'&il=0&iy=0&n=1&sesab=ACBAAB&id=IDENTIFYING&cc=773&paging='+str(i)
		for j in range(6):
			try:
				html = requests.get(list_url_temp,headers=headers,timeout=3).text
				selector = etree.HTML(html)
				productitems = selector.xpath('/html/body/li')
				for item in productitems:
					producthref = item.xpath('div/div[@class="product-box"]/div[@class="res-info"]/div[@class="title-selling-point"]/a/@href')
					if len(producthref) == 1:
						product_urls.append('https:'+producthref[0])
				print(list_url_temp)
				break
			except Exception as e:
				if 'Max retries exceeded with url' in str(e):
					print("断网了,程序退出运行")
					# exit(-1)
	print('第',page_num+1,'页获取到商品',len(product_urls),'个！')

	return product_urls

def parse_product_id(url):
	if url.startswith('https://product.suning.com/0000000000/'):
			product_id_first = str(url.split('/')[3])
			product_id_second = str(url.split('/')[4].split('.')[0])
	elif url.startswith('https://th.suning.com/calCpcClicks'):
		idReg = re.compile(r'cmdCode=(.*?)&companyCode=(.*?)&')
		product_id = idReg.search(url)
		product_id_first = '0000000000'
		product_id_second = str(product_id.group(1))
	elif url.startswith('https://review.suning.com/ajax/cluster_review_lists'):
		product_id = url.split('-')
		product_id_first = product_id[3]
		product_id_second = product_id[2].strip('0')
	else:
		product_id_first = str(url.split('/')[3])
		product_id_second = str(url.split('/')[4].split('.')[0])
	return product_id_first,product_id_second

def get_list_url(): #苏宁全站分类的url
	sort_url = 'https://list.suning.com/'
	content = parse_one_page(sort_url)
	reg = re.compile(r'<a href="//list.suning.com/(.*?).html"',re.S)
	list_urls = reg.findall(content)
	length = len(list_urls)
	for i in range(length):
		list_urls[i] = 'https://list.suning.com/' + list_urls[i] + '.html'
	print("苏宁商品类别一共有",length,"个！")
	return list_urls

def get_total_products_urls_num(): #获取所有商品id
	list_urls = get_list_url() #全站商品类别url
	products_urls_num = 0 #全站商品url数量
	# temp_i = 0

	for list_url in list_urls:
		# temp_i += 1
		# if temp_i <= 861:
		# 	continue
		try:
			print("开始爬取此类商品：",list_url)
			total_list_urls = []
			reg = re.compile(r'"pageNumbers":"(\d+)"')
			html = parse_one_page(list_url)
			total_page_numbner = reg.findall(html)
			total_page_numbner = int(total_page_numbner[0])
			if total_page_numbner == 0:  #有些类别可能一个商品也没有,就是某类商品一个也没有那种 直接跳过循环,进行下一个
				continue
			print("此类商品一共",total_page_numbner,"页！")
			products_sort_url = [] #某类商品共有多少个

			html = parse_one_page(list_url)
			selector = etree.HTML(html)
			productitems =  selector.xpath('//*[@id="product-list"]/ul/li')
			for item in productitems:
				producthref = item.xpath('div/div[@class="product-box"]/div[@class="res-info"]/div[@class="title-selling-point"]/a/@href')
				if len(producthref) ==1:
					products_sort_url.append('https:'+producthref[0])
					# products_urls_num.append('https:'+producthref[0])
			list_id = list_url.split('-')[1]
			for i in range(1,4):
				list_url_temp = 'https://list.suning.com/emall/searchV1Product.do?ci='+str(list_id)+'&pg=03&cp=0&il=0&iy=0&n=1&sesab=&id=IDENTIFYING&cc=773&paging='+str(i)
				for j in range(6):
					try:
						html = requests.get(list_url_temp,headers=headers,timeout=3).text
						selector = etree.HTML(html)
						productitems = selector.xpath('/html/body/li')
						for item in productitems:
							producthref = item.xpath('div/div[@class="product-box"]/div[@class="res-info"]/div[@class="title-selling-point"]/a/@href')
							if len(producthref) == 1:
								products_sort_url.append('https:'+producthref[0])
								# products_urls_num.append('https:'+producthref[0])
						print(list_url_temp)
						break
					except	 Exception as e:
						if 'Max retries exceeded with url' in str(e):
							print("断网了,程序退出运行")
							#exit(-1)
						else:
							continue
			print('第 1 页获取到商品',len(products_sort_url),'个！')
				# distinct_url(products_sort_url,total_list__urls)


			if total_page_numbner>1: #翻页，某类商品大于1页
				for page_num in range(1,total_page_numbner):
					# products_sort_url = []
					product_urls = parse_list_page(list_url,page_num)
					# for product_url in product_urls:
					# 	products_urls_num.append(product_url)
					# 	products_sort_url.append(product_url)
					# products_urls_num.extend(product_urls)
					products_sort_url.extend(product_urls)
			distinct_url(products_sort_url,total_list_urls)
			write_product_url_to_mongo(total_list_urls)
			print("此类商品共获得链接",len(total_list_urls),"个！")
			products_urls_num += len(total_list_urls)
			print("截至目前为止共获得商品链接",products_urls_num,"个！")
			print("当前时间为",time.strftime("%Y/%m/%d/%H:%M:%S"))
		except Exception as e:
			if 'Max retries exceeded with url' in str(e):
				print("断网了,程序退出运行")
				# exit(-1)
			else:
				continue

	print("苏宁全站共获取到商品链接",products_urls_num,"个！")
	# return products_urls_num

def extract(url, content):
	try:
		selector = etree.HTML(content)
		#商品类别
		category1 = selector.xpath('//*[@id="category1"]/text()')[0]
		product_categories = []
		product_categories.append(category1)
		categoryitems = selector.xpath('/html/body/div[5]/div/div[1]/div[@class="dropdown"]')
		for item in categoryitems:
			categoryitem = item.xpath('span/a/text()')[0]
			product_categories.append(categoryitem)
		category3 = selector.xpath('//*[@id="productName"]/a/text()')[0]
		product_categories.append(category3)

		#商品名，苏宁描述为图片 ！--
		product_name = selector.xpath('//*[@id="itemDisplayName"]/text()')
		if len(product_name) == 1:
			product_name = product_name[0]
		else:
			product_name = product_name[1]
		product_description = selector.xpath('//*[@id="promotionDesc"]/text()')[0]
		product_description = product_description.replace('&nbsp;',' ')
		product_name = product_name.replace('\t','').replace('\n','').replace('\r','').replace(' ','')
		product_description = product_description.replace('\t','').replace('\n','').replace('\r','').replace(' ','')

		#商品价格
		product_id_first,product_id_second = parse_product_id(url)
		price_url = 'https://icps.suning.com/icps-web/getVarnishAllPrice014/'+'0'*(18-len(product_id_second)) + product_id_second+'_773_7730101_'+product_id_first+'_1_getClusterPrice.vhtm'
		price_text = requests.get(price_url).text
		price_text = price_text[17:][:-3] # 处理str，将其转化为json好转化的格式
		try:
			price_content = json.loads(price_text)
			product_price = price_content['price']
		except:
			print('price获取失败 ',price_url)
			product_price = None

		product = {
			"product_categories":product_categories,
			"product_name":product_name,
			"product_price":product_price,
			"product_description":product_description
		}
		# print(product)
		return product
	except Exception:
		print("商品信息获取失败！",url)

def reviewExtract(url, comment_list):
	commentList = []
	try:
		for i in range(len(comment_list)):
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
			commentList.append(comment)
		# print(url,"\n获取到评论",len(commentList),"条！")
		print(url)
		time.sleep(np.random.rand()/100)
		return commentList
	except Exception:
		# return UnknownSite(url)
		print("此页评论获取失败！",url)

def get_comment_like_num(commodityReviewId):#获取点赞数
	time.sleep(np.random.rand()/100)
	url = 'https://review.suning.com/ajax/useful_count/'+str(commodityReviewId)+'-usefulCnt.htm'
	try:
		comment_like_num_text = requests.get(url).text
		comment_like_num_text = comment_like_num_text[10:][:-1]
		comment_like_num_list = json.loads(comment_like_num_text)
		return  comment_like_num_list['reviewUsefuAndReplylList'][0]['usefulCount']
	except Exception as e:
		if 'Max retries exceeded with url' in str(e):
			print("断网了,程序退出运行")
			exit(-1)
		else:
			return None

if __name__ == '__main__':
	start_time = time.time()
	TOTAL_COMMENT_NUM = 0
	TOTAL_PRODUCT_NUM = get_url_num_from_mongo()
	# TOTAL_PRODUCT_NUM =None # ur1049637 个
	if TOTAL_PRODUCT_NUM is None:
		get_total_products_urls_num() #苏宁商品全部链接
		TOTAL_PRODUCT_NUM = get_url_num_from_mongo()

	for i in range(TOTAL_PRODUCT_NUM): # 挨个解析全部商品并获得评论
		product_url = get_one_product_url_from_mongo()
		html = parse_one_page(product_url)
		try:
			if html!=None:
				product = extract(product_url,html)	#商品获取
				print("第",i,"个商品，还剩",TOTAL_PRODUCT_NUM-i,"个商品,商品链接为",product_url)
			else:
				continue
		except:
			continue
		# write_product_to_mongo(product_url,product)
		comment_reg = re.compile(r'clusterId":"(.*?)"',re.S)
		clusterId = re.findall(comment_reg,html)
		(product_id_first,product_id_second) = parse_product_id(product_url)
		comments = []
		try:
			comment_urls = ["https://review.suning.com/ajax/cluster_review_lists/general-"+str(clusterId[0])+"-"+"0"*(18-len(product_id_second))+ product_id_second+"-"+product_id_first+"-total-{0}-default-10-----reviewList.htm?callback=reviewList".format(j) for j in range(1,51)]
			for comment_url in comment_urls:
				comment_content = parse_comment_page(comment_url)
				if len(comment_content)!= 0:
					comment = reviewExtract(comment_url,comment_content) #评论获取
					# for j in comment:
					comments.extend(comment)
					# write_comment_to_mongo(comment_url,comments)
					# TOTAL_COMMENT_NUM += len(comments)
					# print(len(comments),comments)
				else:
					break
		except Exception:
			print("评论获取失败或抓取完毕",product_url)
		finally:
			if product != None:
				(product_id_first,product_id_second) = parse_product_id(product_url)
				product_id = product_id_first+'/'+product_id_second
				result = {'product_id':product_id,'product':product,'comments':comments}
				write_product_comments_to_mongo(result)
				TOTAL_COMMENT_NUM += len(comments)
		print("截至目前为止获取评论",TOTAL_COMMENT_NUM,"条！")
		print("当前时间为",time.strftime("%Y/%m/%d/%H:%M:%S"))

	print("一共获得苏宁网站评论",TOTAL_COMMENT_NUM,"条！")
	end_time = time.time()
	seconds = end_time - start_time
	m,s = divmod(seconds,60)
	h,m = divmod(m,60)
	print("所花费总时间为%d时%02d分%02d秒" % (h, m, s))
	send_sms()

