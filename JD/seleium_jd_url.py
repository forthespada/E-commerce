# -#- coding:utf-8 -*-
# @Time    :2019/3/10 10:25
'''
直接request获取京东商品url速度太慢，采用seleium
'''
from selenium import webdriver
from selenium.webdriver.common.by  import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests,re,json,pymongo,time,csv
from lxml import etree
from requests.exceptions import RequestException
from pyquery import PyQuery as pq
import numpy as np
import pandas as pd

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
chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("start-maximized")
chrome_options.add_argument("disable-infobars")
# chrome_options.add_argument('--headless')
chrome_options.add_argument("--disable-gpu")
prefs = {"profile.managed_default_content_settings.images":2}
chrome_options.add_experimental_option("prefs",prefs)
browser = webdriver.Chrome(chrome_options = chrome_options)
wait = WebDriverWait(browser,10)
MONGO_URL = 'localhost'
MONGO_DB = 'jd'
MONGO_TABLE = 'jd_comment'
MONGO_TABLE_URL = 'jd_urls'

def scroll_down():
	scroll_down = 0
	while True:
		if(scroll_down<10):
			browser.execute_script("window.scrollBy(0,1500)")
			time.sleep(np.random.rand()/10+0.01)
			scroll_down += 1
		else:
			break

def get_one_product_url_from_mongo():
	client = pymongo.MongoClient(MONGO_URL)
	db = client[MONGO_DB]
	try:
		product_url = db[MONGO_TABLE_URL].find_one({},{"product_url":{"$slice":1}})
		product_url = product_url['product_url']
		db[MONGO_TABLE_URL].delete_one({"product_url":product_url}) #取出元素后删除
		return product_url
	except:
		print("表jd_url取出数据错误")
def get_url_num_from_mongo():
	client = pymongo.MongoClient(MONGO_URL)  	# 连接数据库
	db = client[MONGO_DB]
	table = db[MONGO_TABLE_URL] 	# 读取数据
	data = pd.DataFrame(list(table.find())) 	# 选择需要显示的字段
	try:
		data = data[['product_url']] #data[['_id'，'product_url']]
		data = data['product_url']
		print("表jd_url中存在商品链接共",len(data),"个，开始爬取商品")
		return len(data)
	except:
		print("表jd_url中不存在元素")
		return None

def write_product_url_to_mongo(product_urls):
	# out = open('jd_url_csv139.csv','a', newline='') 		#打开文件，追加a，设定写入模式
	# csv_write = csv.writer(out,dialect='excel') 	#写入具体内容
	# for product_url in product_urls:
	# 	product_url = 'https://item.jd.com/' +  product_url +'.html'
	# 	url = [product_url]
	# 	try:
	# 		csv_write.writerow(url)
	# 	except:
	# 		print("写入失败：",url)

	# print(product_urls)
	client = pymongo.MongoClient(MONGO_URL)
	db = client[MONGO_DB]
	for product_url in product_urls:
		product_url = 'https://item.jd.com/' +  product_url +'.html'
		product_url = {'product_url':product_url}
		try:
			if db[MONGO_TABLE_URL].update({'product_url':product_url['product_url']},{'$set':product_url},True):
				pass
				# print("更新成功")
		except:
			print("插入商品链接失败",product_url)

def write_product_to_mongo(url,result): # 插入商品信息成功
	product_id = url.split('/')[-1].split('.')[0]
	product_id = {'product_id':product_id}
	result = {'product':result}
	client = pymongo.MongoClient(MONGO_URL)
	db = client[MONGO_DB]
	if db[MONGO_TABLE].update({'product_id':product_id['product_id']},{'$set':product_id},True) and db[MONGO_TABLE].update({'product_id':product_id['product_id']},{'$set':result},True):
		pass
	else:
		print("插入商品信息失败，商品url:",url)

def write_comment_to_mongo(url,result): # 插入评论信息
	product_id = url.split('=')[1].split('&')[0]
	product_id = {'product_id':product_id}
	for i in range(len(result)):
		comment = {'comment':result[i]}
		client = pymongo.MongoClient(MONGO_URL)
		db = client[MONGO_DB]
		if db[MONGO_TABLE].update({'product_id':product_id['product_id']},{'$set':product_id},True) and db[MONGO_TABLE].update({'product_id':product_id['product_id']},{'$addToSet':comment},True):
			pass
		else:
			print("插入商品评论失败，评论url:",url)

def get_list_url(): #京东全站分类的url
	sort_url = 'https://www.jd.com/allSort.aspx'
	browser.get(sort_url)
	scroll_down()
	wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#service-2017 > div.w > ol > li.item.fore2')))
	content = browser.page_source
	reg = re.compile(r'<a href="//list\.jd\.com/list\.html\?cat=(.*?)"',re.S)
	list_urls = reg.findall(content)
	for i in range(len(list_urls)):
		list_urls[i] = 'https://list.jd.com/list.html?cat=' + list_urls[i]
	print("京东商品类别一共有",len(list_urls),"个！")
	return list_urls

def parse_comment_page(url): # 评论界面可能获取失败或者当前界面本来就为空即评论没有了
	for i in range(3):
		try:
			content = requests.get(url,headers=headers,timeout=2).text
			if content:
				comment_result = json.loads(content)
				if len(comment_result['comments']) != 0:
					print(url)
					time.sleep(np.random.rand()/10)
					return content
		except:
			pass
	return None

def parse_page(url):
	for i in range(3):
		try:
			response = requests.get(url,headers=headers,timeout=2)
			if '京东首页' in response.text:
				time.sleep(np.random.rand()/10)
				return response.text
		except:
			pass
	return None

def get_total_page_num(list_url): # 查询总共需要爬去的总页数
	try:
		response = requests.get(list_url,headers=headers)
		if response.status_code == 200:
			page_num_reg = re.compile(r'class="p-skip".*?共<b>(.*?)</b>页',re.S)
			total_page_num = page_num_reg.findall(response.text)[0]
			print("此类商品共有",total_page_num,"页！")
			return total_page_num
	except TimeoutError: # 网速过慢容易引发错误，加上try,错了就再次发起请求
		get_total_page_num() # 再次请求

def get_total_product_id(product_url,page_num,browser): # 获取京东某页全部商品id
	page_url = product_url +"&page="+ str(page_num)
	browser.get(page_url)
	scroll_down()
	# wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#service-2017 > div.w > ol > li.item.fore2')))
	content = browser.page_source
	selector = etree.HTML(content)
	productidlist = []
	items = selector.xpath('//*[@id="plist"]/ul/li')
	for item in items:
		productid = item.xpath('div/@data-sku')
		if len(productid) != 1:
			productid= item.xpath('div/div/div[@class="gl-i-tab-content"]/div[2]/@data-sku')
		productidlist.append(productid)
	return productidlist


def extract(url, content):
	try:
		product_id = url.split('/')[-1].split('.')[0]
		doc = pq(content)
		#商品类别
		product_categories = []
		categoryitems = doc.find('#crumb-wrap > div > div.crumb.fl.clearfix > div.item').items()
		for item in categoryitems:
			categoryitem = item.find('a').text()
			if len(categoryitem) != 0:
				product_categories.append(categoryitem)
		category3 = doc.find('#crumb-wrap > div > div.crumb.fl.clearfix > div.item.ellipsis').text()
		product_categories.append(category3)

		#商品名，描述
		product_name = doc.find('#name > div.sku-name').text()
		if len(product_name)== 0:
			 product_name = doc.find('body > div:nth-child(9) > div > div.itemInfo-wrap > div.sku-name').text()
		product_description = doc.find('#detail > div.tab-con > div:nth-child(1) > div.p-parameter').text()
		product_description = product_description.replace('\n','  ').replace('\xa0','').replace('>>','')
		# product_price = doc.find('body > div:nth-child(11) > div > div.itemInfo-wrap > div.summary.summary-first > div > div.summary-price.J-summary-price > div.dd > span.p-price').text()

		#商品价格
		product_price_url = "https://c0.3.cn/stock?skuId=" + product_id +"&cat=1320,1583,1592&venderId=13572&area=1_72_2799_0&buyNum=1&choseSuitSkuIds=&extraParam={%22originid%22:%221%22}&ch=1&fqsp=0&pduid=1540516052714659336599&"
		product_price_content = requests.get(product_price_url,headers=headers).text
		product_price_result = json.loads(product_price_content)
		product_price = product_price_result['stock']['jdPrice']['p']

		product = {
			"product_categories":product_categories,
			"product_name":product_name,
			"product_description":product_description,
			"product_price":product_price

		}
		write_product_to_mongo(url,product)
		# print(product["product_name"])
		return product
	except Exception:
		print("商品信息获取失败！",url)
		# raise UnknownSite(url)

def reviewExtract(url, content):
	try:
		commentlist = []
		comment_result = json.loads(content)
		for j in range(0,10): #分别解析每一页10个评论的数据，获得评论文本，时间，分数，点赞数，评论id
			try:
				comment_content = comment_result['comments'][j]['content']
				comment_time = comment_result['comments'][j]['creationTime']
				comment_user_id = comment_result['comments'][j]['id']
				comment_score = comment_result['comments'][j]['score']
				comment_like_num=comment_result['comments'][j]['usefulVoteCount']
				comment_user_nickname=comment_result['comments'][j]['nickname']
				comment ={
					'comment_user_id':comment_user_id,
					'comment_user_nickname':comment_user_nickname,
					'comment_score':comment_score,
					'comment_like_num':comment_like_num,
					'comment_content':comment_content,
					'comment_time':comment_time,
				}
				# write_comment_to_mongo(url,comment)
				commentlist.append(comment)
			except:
				continue
		time.sleep(np.random.rand()/10)
		return commentlist
	except Exception:
		# return UnknownSite(url)
		print("商品评论获取失败！",url)

if __name__ == '__main__':
	start_time = time.time()
	TOTAL_COMMENT_NUM = 0
	TOTAL_PRODUCT_NUM = get_url_num_from_mongo()
	TOTAL_PRODUCT_NUM =None
	if TOTAL_PRODUCT_NUM is None:
		product_list_urls = []
		list_urls = get_list_url()
		browser.quit()
		for j in range(len(list_urls)):  # #获取京东全部商品id
			# if j<50:
			# 	continue
			browser = webdriver.Chrome(chrome_options = chrome_options)
			list_url = list_urls[j]
			print("第",j,"个商品，还剩",len(list_urls) - j,"个，开始爬取此类商品：",list_url)
			try:
				total_page_num = get_total_page_num(list_url) # 某类商品全部页数,有可能一个商品也没有，所以直接跳过去
				for i in range(1,int(total_page_num)+1):#循环总页数
					product_list_url_temp = get_total_product_id(list_url,i,browser)#获取第i页全部商品的id
					for j in product_list_url_temp:
						product_list_urls.append(j[0])
					write_product_url_to_mongo(product_list_urls)
					print("第",i,"页共有商品",len(product_list_url_temp),"个！当前时间为",time.strftime("%Y/%m/%d/%H:%M:%S"))
					time.sleep(np.random.rand()/10)
			except:
				continue
			print("截至目前为止共获取到商品：",len(product_list_urls),"个！")
			browser.quit()

	# for i in range(TOTAL_PRODUCT_NUM): # #获取京东全部商品信息和评论
	# 	product_url = get_one_product_url_from_mongo()
	# 	text = parse_page(product_url)
	# 	if text != None:
	# 		product = extract(product_url,text)
	# 		time.sleep(np.random.rand()/10)
	# 		print("第",i,"个商品，还剩",TOTAL_PRODUCT_NUM-i,"个商品,商品链接为",product_url)
	# 	else:
	# 		continue
	# 	productid = product_url.split('/')[-1].split('.')[0]
	# 	comment_urls = ['https://sclub.jd.com/comment/productPageComments.action?productId='+productid+'&score=0&sortType=5&page={0}&pageSize=10&isShadowSku=0&rid=0&fold=1'.format(i) for i in range(100)]
	# 	'''京东默认最多显示100页的评论，0-99页，每页10条评论，也就是100*10，最多1000条评论'''
	# 	for comment_url in comment_urls:
	# 		content = parse_comment_page(comment_url)
	# 		if content==None:
	# 			break
	# 		else:
	# 			comment = reviewExtract(comment_url,content)
	# 			write_comment_to_mongo(comment_url,comment)
	# 			TOTAL_COMMENT_NUM += len(comment)
	# 			time.sleep(np.random.rand()/10)
	# 	print("截至目前为止获取评论",TOTAL_COMMENT_NUM,"条！")
	#
	# print("一共获得京东网站评论",TOTAL_COMMENT_NUM,"条！")
	# end_time = time.time()
	# seconds =end_time - start_time
	# m, s = divmod(seconds, 60)
	# h, m = divmod(m, 60)  # 转化整个爬取时间为时分秒的形式
	# print("所花费总时间为%d时%02d分%02d秒" % (h, m, s))



