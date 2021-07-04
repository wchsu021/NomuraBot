# import keyword
# print(keyword.kwlist)

import pandas as pd
import requests
from datetime import date, datetime, time, timedelta
from bs4 import BeautifulSoup
import json
import urllib.parse as urlparse
# import datetime
import calendar

"""
鉅亨網的爬蟲
直接利用其API，但有30筆的上限
若要抓多篇新聞，則分段成一天為單位，分多次爬取
"""

categories = {}
with open('database/categories.json', 'r') as f:
    categories = json.load(f)

categoryIds = [827, 838, 847, 852, 854, 839, 840, 841]
baseUrl = 'https://news.cnyes.com/'
baseApiUrl = 'https://news.cnyes.com/api/v3/news/category/'
baseWebUrl = 'https://news.cnyes.com/news/id/'

def get_date_range_list(date_range):
    
    date_range_list = []
    
    start_time = date(int(date_range[0].split('-')[0]), int(date_range[0].split('-')[1]), int(date_range[0].split('-')[2]))
    end_time = date(int(date_range[1].split('-')[0]), int(date_range[1].split('-')[1]), int(date_range[1].split('-')[2]))

    target_time = start_time
    while target_time <= end_time:
        if target_time.day <= 15:
            target_end = date(target_time.year, target_time.month, 15)
        else:
            target_end = date(target_time.year, target_time.month, calendar.monthrange(target_time.year, target_time.month)[1])
        if target_end > end_time:
            target_end = end_time
        date_range_list.append([target_time.strftime("%Y-%m-%d"), target_end.strftime("%Y-%m-%d")])
        target_time = target_end + timedelta(days=1)
        
    return date_range_list

class DataFormat:
    def __init__(self, newsId, categoryId, categoryName, title, author, article, timestamp):
        self.newsId = newsId
        self.categoryId = categoryId
        self.categoryName = categoryName
        self.title = title
        self.author = author
        self.article = article
        self.timestamp = timestamp

    def getData(self):
        return {
            'newsId': self.newsId,
            'categoryId': self.categoryId,
            'categoryName': self.categoryName,
            'title': self.title,
            'author': self.author,
            'article': self.article,
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp)
        }

class ArticlesCollector:
    def __init__(self, category_name, date_range):
        '''
        rl_category_name: tw_sotck/台股, future/期貨, fund/基金, fund/外匯, tw_insurance/保險, tw_housenews/房產
        '''
        self.__baseUrl = baseUrl
        self.__baseApiUrl = baseApiUrl
        self.__baseWebUrl = baseWebUrl
        self.category_name = category_name
        self.__responseDataList = []
        self.__url_category_name = categories[self.category_name]['categoryName']
        self.__filename = categories[self.category_name]['fileName']
        self.__date_range = date_range
        self.__startAt = int(datetime.combine(pd.to_datetime(date_range[0]), time.min).timestamp())
        self.__endAt = int(datetime.combine(pd.to_datetime(date_range[1]), time.max).timestamp())
        self.__limit = 30
        self.__existing_df = None
    
    
    def is_author(self, tag):
        '''
        判斷作者node
        '''
        return tag.has_attr('itemprop') and tag.get('itemprop') == 'author'
  
    def is_article(self, tag):
        '''
        判斷文章node
        '''
        return tag.has_attr('itemprop') and tag.get('itemprop') == 'articleBody'
  
    def store_to_csv(self):
        '''
        儲存結果為CSV檔
        '''
        columns = columns=['newsId', 'categoryId', 'categoryName', 'author', 'title', 'article', 'timestamp', 'datetime']
        df = pd.DataFrame(self.__responseDataList, columns=columns)
        try:
            if (self.__existing_df is None):
                df.to_csv('database/'+self.__filename, index=False, encoding='utf8')
            else:
                df_new = pd.concat([self.__existing_df, df])
                df_new.drop_duplicates(subset=['newsId', 'categoryId'], inplace=True, keep='last')
                df_new.to_csv('database/'+self.__filename, index=False, encoding='utf8')    
            print('Updated to ' + self.__filename)
            return df if self.__existing_df is None else df_new
        except Exception as exc:
            print(str(exc))
            print("No upload")
            return exc
  
    def get_api_data(self, payload):
        '''
        依照文章類別取得文章列表資訊
        '''
        try:
            r = requests.get(urlparse.urljoin(self.__baseApiUrl, self.__url_category_name), params=payload)
            r.raise_for_status()
            response = r.json()['items']
            self.__last_page = response['last_page']
            return response
        except Exception as exc:
            raise exc
      
    def response_handler(self, list_data, show_message):
        '''
        取得逐筆的文章
        '''
        if (list_data['categoryId'] not in categoryIds):
            return None

        if (show_message):
            print('Fetching ' +  self.category_name + ' newsId:' + str(list_data['newsId']) + '... ', end='')

        res = requests.get(urlparse.urljoin(baseWebUrl, str(list_data['newsId'])))

        try:
            res.raise_for_status()
        except Exception as exc:
            raise exc

        soup = BeautifulSoup(res.text, 'lxml')
        author = soup.find(self.is_author).span.string
        article = ''.join([text.text for text in soup.find(self.is_article).select('p')])

        if (show_message):
            print('Done')
  
        return DataFormat(list_data['newsId'], list_data['categoryId'], self.category_name, list_data['title'], author, article, list_data['publishAt']).getData()
  
    def get_articles(self, show_message=True):      
        '''
        show_message: 是否顯示request過程
        '''
        payload = {
          'startAt': self.__startAt,
          'endAt': self.__endAt,
          'limit': self.__limit,
          'page': 0
        }

        err_msg = None
        response = {}
    
        try:
            self.__existing_df = pd.read_csv('database/'+self.__filename)
        except Exception as exc:
            print(str(exc))
        
        while True:
            if ('last_page' in response and payload['page'] == response['last_page']):
                print("last_page")
                break
            else:
                try:
                    payload['page'] += 1
                    try:
                        response = self.get_api_data(payload)    
                        last_page = response['last_page']
                        if (response['last_page'] == 0):
                            print('no available data between ' + self.__date_range[0] + ' ~ ' + self.__date_range[1])
                            break
                    except Exception as exc:
                        err_msg = str(exc)
                        print(err_msg)
                    
                    if (show_message):
                        print(self.category_name + ' (' + str(payload['page']) + '/' + str(response['last_page']) + '):')
                    for data in response['data']:  
                        try:
                            rtn = self.response_handler(data, show_message)    
                            if (rtn is not None):
                                self.__responseDataList.append(rtn)
                        except Exception as exc:
                            err_msg = str(exc)
                            print(err_msg)
                    if (len(self.__responseDataList)):
                        self.store_to_csv()
                except Exception as exc:
                    err_msg = str(exc)
                    print(err_msg)
                break

date_range = ['2020-10-01', '2020-12-31']

## 將要抓取的日期區間做分段
date_range_list = get_date_range_list(date_range)

## 每段分開爬取，避免單次爬取超過上限
for d in date_range_list:
    ## get_articles(False): 不顯示log
    ArticlesCollector('stock', d).get_articles()
    # ArticlesCollector('future', date_range).get_articles()
    # ArticlesCollector('forex', date_range).get_articles()
    # ArticlesCollector('house', date_range).get_articles()
    # ArticlesCollector('insurance', date_range).get_articles()
    ArticlesCollector('fund', d).get_articles()
