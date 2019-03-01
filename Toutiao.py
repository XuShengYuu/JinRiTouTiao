import requests
from urllib.parse import urlencode
from requests.exceptions import RequestException
import io,sys
import json
from bs4 import BeautifulSoup
import re
from config import*
import pymongo
import os
from hashlib import md5
# from multiprocessing import Pool

client = pymongo.MongoClient(MONGO_URL,connect=False)
db = client[MONGO_DB]

sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='gb18030')
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}

def get_page_index(offset,keyword):
	data = {
		'aid':'24',
		'app_name':'web_search',
		'offset':offset,
		'format':'json',
		'keyword':keyword,
		'autoload':'true',
		'count':'20',
		'en_qc':'1',
		'cur_tab':1,
		'from':'search_tab',
		'pd':'synthesis'
	}
	url = 'https://www.toutiao.com/api/search/content/?' + urlencode(data)
	try:
		response = requests.get(url)
		if response.status_code == 200:
			return response.text
		return None
	except RequestException:
		print('请求页出错')
		return None

def parse_page_index(html):
	data = json.loads(html)
	if data and 'data'in data.keys():
		for item in data.get('data'):
			yield item.get('article_url')

def get_page_detail(url):
	try:
		response = requests.get(url,headers=headers)
		if response.status_code == 200:
			return response.text
		return None
	except RequestException:
		# print('请求详情页出错', url)
		return None

def parse_page_detail(html,url):
	soup = BeautifulSoup(html,'lxml')
	title = soup.select('title')[0].get_text() 
	# print(title)
	images_pattern = re.compile('gallery: JSON.parse\("(.*)"\)', re.S)
	# print(images_pattern)
	result = re.search(images_pattern,html)
	# print(result)
		# print(result.group(1))
	if result:
		data = json.loads(result.group(1).replace('\\', ''))
		# print(data)
		if data and 'sub_images' in data.keys():
			sub_images = data.get('sub_images')
			images = [item.get('url') for item in sub_images]
			for image in images:download_image(image)
			return{
				'title':title,
				'url':url,
				'images':images
			}
	
	# print(result)

def save_to_file(result):
	with open(r'C:/Users/AOAO/Desktop/Toutiao.csv','a',encoding='gb18030') as f:
		f.write(json.dumps(result,ensure_ascii=False) + '\n')
		f.close()

def save_to_mongo(result):
	if db[MONGO_TABLE].insert(result):
		print('存储到MongoDB成功',result)
		return True
	return False

def download_image(url):
	try:
		response = requests.get(url)
		if response.status_code == 200:
			save_image(response.content)
			# return response.text
		return None
	except RequestException:
		print('请求图片出错')
		return None

def save_image(content):
	file_dir = 'E:\\Toutiao_images'
	if not os.path.exists(file_dir):
		os.mkdir(file_dir)
	file_path = '{0}/{1}.{2}'.format(file_dir,md5(content).hexdigest(),'jpg')
	with open(file_path,'wb') as f:
		f.write(content)
		f.close()

def main():
	html = get_page_index(0,'街拍')
	for url in parse_page_index(html):
		html = get_page_detail(url)
		if html:
			# parse_page_detail(html,url)
			result = parse_page_detail(html, url)			
			if result!= None:
				save_to_mongo(result)
				# save_to_file(result)
			# print(result)
		# print(url)

if __name__ == '__main__':
	main()

