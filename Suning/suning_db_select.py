# -#- coding:utf-8 -*-
# @Time    :2019/3/1 21:36
import pymongo
import pandas as pd

MONGO_URL = 'localhost'
MONGO_DB = 'suning'
MONGO_TABLE = 'suning_comments'

'''
suning_comment
苏宁网站共获取到商品  106509  个！
其中有评论的商品  26495  个！ 没有评论的商品有  80014 个！
苏宁网站共获取到评论  1032581  条！
suning_comments
苏宁网站共获取到商品  80114  个！
其中有评论的商品  80038  个！ 没有评论的商品有  76 个！
苏宁网站共获取到评论  2529052  条！

'''
def get_url_num_from_mongo():
	client = pymongo.MongoClient(MONGO_URL)  	# 连接数据库
	db = client[MONGO_DB]
	table = db[MONGO_TABLE] 	# 读取数据
	totaldata = pd.DataFrame(list(table.find()))
	data = pd.DataFrame(list(table.find({"comments.comment_content":{"$exists":"true"}}))) 	# 选择需要显示的字段
	data = data[['comments']] #data[['_id'，'product_url']] - len(totaldata)
	print("苏宁网站共获取到商品 ",len(totaldata) ," 个！")
	print("其中有评论的商品 ",len(data)," 个！ 没有评论的商品有 ",len(totaldata)- len(data),'个！')
	length = 0
	for index,row in data.iterrows():
		comments = row['comments']
		length += len(comments)
	print("苏宁网站共获取到评论 ",length," 条！\n")
	return length


if __name__ == '__main__':
	get_url_num_from_mongo()