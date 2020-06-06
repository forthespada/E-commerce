# -*- coding: utf-8 -*-
# @Time    : 2018/12/16 10:51
import re,requests

def whole_website_sort():
	sort_url =  'https://www.jd.com/allSort.aspx'
	response = requests.get(sort_url).text
	reg = re.compile(r'<a href="//list(.*?)"',re.S)
	total_sort = reg.findall(response)
	for i in range(0,len(total_sort)):
		total_sort[i] = 'https://list' + total_sort[i]
	return total_sort



