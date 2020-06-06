# -*- coding: utf-8 -*-
# @Time    : 2018/12/30 21:57
import requests,json,re,time
from lxml import etree
header = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'
}
url = 'https://item.gome.com.cn/A0006532743-pop8012554861.html'#'https://item.gome.com.cn/A0006532738-pop8012554841.html'
commenturl = 'https://ss.gome.com.cn/item/v1/prdevajsonp/appraiseNew/A0005681005/0/all/0/3191/flag/appraise/all'
def parse_page(url):
	for i in range(6):
		try:
			response = requests.get(url,headers=header,timeout=2).text
			if '国美首页' in response:
				return response
		except:
			pass
	return None
def parse_comment_page(url):
	for i in range(6):
		try:
			response = requests.get(url,headers=header,timeout=5).text
			response = response[4:][:-1]
			response_json = json.loads(response)
			content = response_json['evaList']['Evalist']
			return content
		except:
			pass
	return None

def reviewExtract(url, content):
	commentlist = []
	try:
		for i in range(len(content)):
			comment_content =content[i]['appraiseElSum']
			print(comment_content)
			if comment_content == '此用户没有填写内容': # 去掉默认评论
				continue
			comment_time = content[i]['post_time']
			# print(comment_time)
			comment_user_id = content[i]['appraiseId']
			# print(comment_user_id)
			comment_user_nickname = content[i]['loginname']
			# print(comment_user_nickname)
			comment_score = content[i]['mscore']
			# print(comment_score)
			comment_like_num = content[i]['apprnum']
			comment_like_num
			comment = {
				'comment_user_id':comment_user_id,
				'comment_user_nickname':comment_user_nickname,
				'comment_score':comment_score,
				'comment_like_num':comment_like_num,
				'comment_content':comment_content,
				'comment_time':comment_time
				}
			print(comment)
			commentlist.append(comment)
			# print(url,"\n获取到评论",len(commentList),"条！")
		return commentlist
	except Exception:
		print("此页评论获取失败！",url)
def extract(url,content):
	#商品类别，商品名，描述
	product_categories = []
	selector = etree.HTML(content)
	try:
		items = selector.xpath('/html/body/div[@class="breadcrumbs-wrapper"]/div/div[1]/ul/li')
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
		# //*[@id="gm-prd-main"]/div[1]/h1
	except:
		des_reg = re.compile('description:"(.*?)"')
		product_description = des_reg.findall(content)[0]
	print(product_description)

	#商品价格
	product_id= url.split('/')[-1]
	product_id_first=product_id.split('-')[0]
	product_id_second=product_id.split('-')[1].split('.')[0]
	price_url = 'https://ss.gome.com.cn/item/v1/d/m/store/unite/'+product_id_first+'/'+product_id_second+'/N/32010100/320101001/1/null/flag/item/allStores'
	price_response = requests.get(price_url,headers=header).text
	price_response = price_response[10:][:-1]
	price_json = json.loads(price_response)
	product_price = price_json['result']['gomePrice']['salePrice']

	product = {
		"product_categories":product_categories,
		"product_name":product_name,
		"product_price":product_price,
		"product_description":product_description
	}
	print(url)
	print(product)
	return product

if __name__ == '__main__':


	t = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
	print(t)# text = parse_page(url)
	# # print(text)
	# extract(url,text)
	# text = parse_comment_page(commenturl)
	#
	# reviewExtract(commenturl,text)