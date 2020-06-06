# -#- coding:utf-8 -*-
# @Time    :2019/7/3 10:37
# 将巨量CSV文件写入mysql数据库中
#处理suning_comment.csv文件
import pandas as pd
import json,pymysql,time
import numpy as np


def main():
	pd.set_option('display.max_columns',5000)
	pd.set_option('display.max_rows',None)
	pd.set_option('max_colwidth',100)
	df = pd.read_csv(r'F:\suning_comment.csv')
	num = int(df.describe().ix[0,0])

	print("---------遍历出所有行-------")
	for i in range(num):
		print(i)
		item = df.ix[i,:]
		product_url = 'https://product.suning.com/' + item['product_id']+ '.html'
		# print('product_url',product_url)
		product_id = item['product_id']
		# print('product_id',product_id)
		if item['product'] is not np.nan:
			product = json.loads(item['product'])
			# print(product)
			product_price = product['product_price'] if product['product_price'] is not np.nan else None
			# print('product_price',product_price)
			product_name = product['product_name'] if product['product_name'] is not np.nan else None
			# print('product_name',product_name)
			product_description = product['product_description'] if product['product_description'] is not np.nan else None
			# print('product_description',product_description)
			product_categories = product['product_categories'] if product['product_categories'] is not np.nan else None
			# print('product_categories',product_categories)
			categories = {}
			for cate_level in range(len(product_categories)):
				categories[str(cate_level)]=product_categories[cate_level]
		else:
			continue

		# print(categories)
		# print("str cate",str(categories))
		# categories.clear()

		config={
		"host":"127.0.0.1",
		"user":"root",
		"password":"123456",
		"database":"mysql",
		"use_unicode":True,
		# "charset":"utf8"
		}
		db = pymysql.connect(**config)
		cursor = db.cursor()
		product_sql = "INSERT INTO suning_product(product_id,product_name,product_url,product_price,product_description,product_categories,time) VALUES(%s,%s,%s,%s,%s,%s,%s)"
		# print(content['Name'],content['Information'],content['Score'],content['Grade_score_totalnumber_Of_people'])
		current_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
		cursor.execute(product_sql,(product_id,product_name,product_url,product_price,product_description,str(categories),current_time))
		db.commit()  #提交数据

		if item['comments'] is not np.nan:
			# print(i)
			# print('此商品评论为空')
			comments = json.loads(item['comments'])
			review_sql = "INSERT INTO suning_review(product_id,review_id,reviewer_nickname,review_content,review_rating,review_helpful,review_time,time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
			for comment in comments:
				# print(comment)
				review_id = comment['comment_user_id'] if comment['comment_user_id'] is not np.nan else None
				# print('review_id',review_id)
				reviewer_name = comment['comment_user_nickname'] if comment['comment_user_nickname'] is not np.nan  else None
				# print('reviewer_name',reviewer_name)
				review_rating = comment['comment_score'] if comment['comment_score'] is not np.nan else None
				# print('review_rating',review_rating)
				review_helpful = comment['comment_like_num'] if comment['comment_like_num'] is not np.nan else None
				# print('review_helpful',review_helpful)
				review_content = comment['comment_content'] if comment['comment_content'] is not np.nan else None
				# print('review_content',review_content)
				review_time = comment['comment_time'] if comment['comment_time'] is not np.nan else None
				# print('review_time',review_time)
				if '用户没有填写' in review_content:
					continue
				else:
					current_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
					cursor.execute(review_sql,(product_id,review_id,reviewer_name,review_content,review_rating,review_helpful,review_time,current_time))
					db.commit()  #提交数据
		else:
			print('此商品评论为空')
		cursor.close()
		db.close()


if __name__ == '__main__':
	main()