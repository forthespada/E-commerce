# -*- coding: utf-8 -*-
# @Time    : 2018/12/30 20:18
import requests,re,pymongo,json,time
import numpy as np
import pandas as pd
from lxml import etree

user_agent_list = ["Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
"Mozilla/5.0 (Windows NT 10.0; …) Gecko/20100101 Firefox/61.0",
"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36",
"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36",
"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
"Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10.5; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15"
 ]

headers = {'User-Agent':np.random.choice(user_agent_list)}
MONGO_URL = 'localhost'
MONGO_DB = 'guomei'
MONGO_TABLE = 'guomei_comment'
MONGO_TABLE_URL = 'guomei_url'

def get_one_product_url_from_mongo():
	client = pymongo.MongoClient(MONGO_URL)
	db = client[MONGO_DB]
	try:
		product_url = db[MONGO_TABLE_URL].find_one({},{"product_url":{"$slice":1}})
		product_url = product_url['product_url']
		db[MONGO_TABLE_URL].delete_one({"product_url":product_url}) #取出元素后删除
		return product_url
	except:
		print("表guomei_url取出数据错误")
def get_url_num_from_mongo():
	client = pymongo.MongoClient(MONGO_URL)  	# 连接数据库
	db = client[MONGO_DB]
	table = db[MONGO_TABLE_URL] 	# 读取数据
	data = pd.DataFrame(list(table.find())) 	# 选择需要显示的字段
	try:
		data = data[['product_url']] #data[['_id'，'product_url']]
		data = data['product_url']
		print("表guomei_url中存在商品链接共",len(data),"个，开始爬取商品")
		return len(data)
	except:
		print("表guomei_url中不存在元素")
		return None

def write_product_url_to_mongo(product_urls):
	client = pymongo.MongoClient(MONGO_URL)
	db = client[MONGO_DB]
	for product_url in product_urls:
		product_url = {'product_url':product_url}
		if db[MONGO_TABLE_URL].update({'product_url':product_url['product_url']},{'$set':product_url},True):
			pass
		else:
			print("插入商品链接失败:",product_url)

def write_product_to_mongo(url,result):
	product_id= url.split('/')[-1].split('.')[0]
	product_id = {'product_id':product_id}
	result = {'product':result}
	client = pymongo.MongoClient(MONGO_URL)
	db = client[MONGO_DB]
	if db[MONGO_TABLE].update({'product_id':product_id['product_id']},{'$set':product_id},True) and db[MONGO_TABLE].update({'product_id':product_id['product_id']},{'$set':result},True):
		pass
	else:
		print("插入商品信息失败，商品url:",url)

def write_comment_to_mongo(url,comments):
	product_id= url.split('/')[-1].split('.')[0]
	product_id = {'product_id':product_id}
	client = pymongo.MongoClient(MONGO_URL)
	db = client[MONGO_DB]
	for i in range(len(comments)):
		comment = {'comments':comments[i]}
		if db[MONGO_TABLE].update({'product_id':product_id['product_id']},{'$set':product_id},True) and db[MONGO_TABLE].update({'product_id':product_id['product_id']},{'$addToSet':comment},True):
			pass
		else:
			print("插入商品评论失败，商品url为:",url)

def parse_page(url):
	for i in range(6):
		try:
			response = requests.get(url,headers=headers,timeout=2).text
			if '国美首页' in response:
				return response
		except:
			pass
	return None
def parse_comment_page(url):
	for i in range(6):
		try:
			response = requests.get(url,headers=headers,timeout=5).text
			response = response[4:][:-1]
			response_json = json.loads(response)
			content = response_json['evaList']['Evalist']
			return content
		except:
			pass
	return None

def get_total_sorts_url():
	sort_url = 'https://list.gome.com.cn/'
	response = requests.get(sort_url,headers=headers).text
	listReg = re.compile(r'<a target="_blank".*?href="(.*?)"')
	productsort = listReg.findall(response)
	productsort = productsort[1:]
	product_sorts = []
	for i in range(len(productsort)):
		if productsort[i].startswith('//list'):
			productsort[i] = 'https:' + productsort[i]
			product_sorts.append(productsort[i])
	print("国美商品种类共有",len(product_sorts),"类！")
	return product_sorts
def get_total_product_url(list_url):
	response = requests.get(list_url,headers=headers).text
	page_numreg = re.compile('<span class="min-pager-number" id="min-pager-number">(.*?)</span>')
	product_page_num = page_numreg.findall(response)
	product_page_num = product_page_num[0].split('/')[1] # 获取该类商品总页数

	product_urls = []
	productreg = re.compile('<a class="emcodeItem item-link" target="_blank".*?href="(.*?)"') # 获取第一页商品的全部链接
	product_urltemp = productreg.findall(response)
	for i in range(len(product_urltemp)):
		product_urls.append('https:' + product_urltemp[i].split('?')[0])

	for i in range(2,int(product_page_num)+1): # 获取第二页及其以后的商品链接
		list_url = list_url[0:-5] + '-00-0-48-1-0-0-0-1-0-0-0-0-0-0-0-0-0.html?&page='+ str(i)+'&aCnt=0'
		response = requests.get(list_url,headers=headers).text
		productreg = re.compile('<a class="emcodeItem item-link" target="_blank".*?href="(.*?)"') # 获取第二页及其以后的商品链接
		product_urltemp = productreg.findall(response)
		for i in range(len(product_urltemp)):
			product_urls.append('https:' + product_urltemp[i].split('?')[0])

	write_product_url_to_mongo(product_urls)
	return product_urls

def extract(url,content):
	#商品类别，商品名，描述
	product_categories = []
	selector = etree.HTML(content)

	try:
		items = selector.xpath('/html/body/div[@class="breadcrumbs-wrapper"]/div/div[1]/ul/li') #已经发现某类商品类别和描述两种类型了
		for item in items:
			categorytemp = item.xpath('a/@title')[0]
			product_categories.append(categorytemp)
		product_categories = product_categories[1:]
		product_name = selector.xpath('//*[@id="gm-prd-main"]/div[@class="hgroup"]/h1/text()')[0]
	except:
		items = selector.xpath('/html/body/div[@class="wbox"]/div/a')
		for item in items:
			categorytemp = item.xpath('@title')
			if len(categorytemp) !=0:
				categorytemp = categorytemp[0]
				product_categories.append(categorytemp)
		product_categories = product_categories[1:]
		product_name = selector.xpath('//*[@id="gm-prd-main"]/li[1]/h1/text()')[0]

	try:
		product_description = selector.xpath('/html/head/meta[@name="description"]/@content')[0]
	except:
		des_reg = re.compile('description:"(.*?)"')
		product_description = des_reg.findall(content)[0]
		
	try:
		#商品价格
		product_id= url.split('/')[-1]
		product_id_first=product_id.split('-')[0]
		product_id_second=product_id.split('-')[1].split('.')[0]
		price_url = 'https://ss.gome.com.cn/item/v1/d/m/store/unite/'+product_id_first+'/'+product_id_second+'/N/32010100/320101001/1/null/flag/item/allStores'
		price_response = requests.get(price_url,headers=headers).text
		price_response = price_response[10:][:-1]
		price_json = json.loads(price_response)
		product_price = price_json['result']['gomePrice']['salePrice']
	except:
		product_price = None

	product = {
		"product_categories":product_categories,
		"product_name":product_name,
		"product_price":product_price,
		"product_description":product_description
	}
	return product

def reviewExtract(url, content):
	commentlist = []
	try:
		for i in range(len(content)):
			comment_content =content[i]['appraiseElSum']
			comment_time = content[i]['post_time']
			comment_user_id = content[i]['appraiseId']
			try:
				comment_user_nickname = content[i]['loginname'] #国美有的评论还真没有用户名，可能是刷单或者之类的
			except:
				comment_user_nickname = None
			comment_score = content[i]['mscore']
			comment_like_num = content[i]['apprnum']
			comment = {
				'comment_user_id':comment_user_id,
				'comment_user_nickname':comment_user_nickname,
				'comment_score':comment_score,
				'comment_like_num':comment_like_num,
				'comment_content':comment_content,
				'comment_time':comment_time
				}
			commentlist.append(comment)
		time.sleep(np.random.rand()/100)
		return commentlist
	except Exception:
		print("此页评论获取失败！",url)


if __name__ == '__main__':

	start_time = time.time()
	TOTAL_COMMENT_NUM = 0
	TOTAL_PRODUCT_NUM = get_url_num_from_mongo()
	# TOTAL_PRODUCT_NUM =None
	if TOTAL_PRODUCT_NUM is None:	
		product_urls_temp = 0
		product_sort_urls = get_total_sorts_url()
		for product_sort_url in product_sort_urls: #获取国美全部商品id
			try:
				product_urls = get_total_product_url(product_sort_url)  #有些类别可能一个商品也没有，所以直接跳过去
				product_urls_temp += len(product_urls)
				print("截至目前为止获取商品",product_urls_temp,"条！")
			except:
				continue
		TOTAL_PRODUCT_NUM = get_url_num_from_mongo()


	for i in range(TOTAL_PRODUCT_NUM):#获取国美全部商品信息和评论
		product_url = get_one_product_url_from_mongo()
		content = parse_page(product_url)
		if content == None: #某个商品解析失败，跳过
			continue
		print("第",i,"个商品，还剩",TOTAL_PRODUCT_NUM-i,"个商品,商品链接为",product_url)
		product = extract(product_url,content)
		write_product_to_mongo(product_url,product)
		product_id_first=product_url.split('/')[-1].split('-')[0]
		product_id_second=product_url.split('/')[-1].split('-')[1].split('.')[0]
		comment_urls = ['https://ss.gome.com.cn/item/v1/prdevajsonp/appraiseNew/'+product_id_first+'/{0}/all/0/3191/flag/appraise/all'.format(i) for i in range(51)] #国美和苏宁一样，最多显示50页评论
		try:
			for comment_url in comment_urls:
				comment_content = parse_comment_page(comment_url)
				if comment_content != None:
					comments = reviewExtract(comment_url,comment_content) #评论获取
					print(comment_url)
					write_comment_to_mongo(product_url,comments)
					TOTAL_COMMENT_NUM += len(comments)
				else:
					break #评论并没有50页，结束循环，开始下一个商品
		except Exception:
			print("商品评论获取失败！",comment_url)
		print("截至目前为止获取评论",TOTAL_COMMENT_NUM,"条！")

	print("一共获得国美网站评论",TOTAL_COMMENT_NUM,"条！")
	end_time = time.time()
	seconds = end_time - start_time
	m,s = divmod(seconds,60)
	h, m = divmod(m, 60)  # 转化整个爬取时间为时分秒的形式
	print("所花费总时间为%d时%02d分%02d秒" % (h, m, s))


