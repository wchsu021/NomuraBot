import requests
from bs4 import BeautifulSoup
# from pretty_print import pretty_print ## 美化輸出
import urllib.parse ## url 相關應用

if __name__ == '__main__':
    # 導入 模組(module) 
    import requests 
    # 導入 BeautifulSoup 模組(module)：解析HTML 語法工具
    import bs4

    # 文章連結
    URL = "https://www.ptt.cc/bbs/Gossiping/index.html"
    # 設定Header與Cookie
    my_headers = {'cookie': 'over18=1;'}
    # 發送get 請求 到 ptt 八卦版
    response = requests.get(URL, headers = my_headers)


    #  把網頁程式碼(HTML) 丟入 bs4模組分析
    soup = bs4.BeautifulSoup(response.text,"html.parser")

    ## PTT 上方4個欄位
    header = soup.find_all('span','article-meta-value')
    for i in soup.find_all('div', 'r-ent'):
        meta = i.find('div', 'title').find('a') or not_exist
        articles.append({
            'title': meta.getText().strip(), ## strip 去除頭尾字符，預設是空白
            'push': i.find('div', 'nrec').getText(),
            'date': i.find('div', 'date').getText(),
            'author': i.find('div', 'author').getText(),
        })

    print(header)

    # 作者
    author = header[0].text
    # 看版
    board = header[1].text
    # 標題
    title = header[2].text
    # 日期
    date = header[3].text


    ## 查找所有html 元素 抓出內容
    main_container = soup.find(id='main-container')
    # 把所有文字都抓出來
    all_text = main_container.text
    # 把整個內容切割透過 "-- " 切割成2個陣列
    pre_text = all_text.split('--')[0]
        
    # 把每段文字 根據 '\n' 切開
    texts = pre_text.split('\n')
    # 如果你爬多篇你會發現 
    contents = texts[2:]
    # 內容
    content = '\n'.join(contents)


    # 顯示
    print('作者：'+author)
    print('看板：'+board)
    print('標題：'+title)
    print('日期：'+date)
    print('內容：'+content)