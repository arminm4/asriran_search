import re

STANDARD_NUMBERS = {'۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4', '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'}

posting_errors = 0
parsing_errors = 0
def number_standardizer(num):
    tmp = ''
    for i in num:
        tmp += STANDARD_NUMBERS[i]
    return tmp


def date_normalizer(date_str):
    normal_date = re.search(r'(\d*)-(\d*)-(\d*)', date_str).group(0)
    normal_time = re.search(r'\d+:\d+', date_str).group(0)
    return normal_date, normal_time


def parser(article):
    date, time = date_normalizer(article.findAll('div', {'class': 'header_pdate'})[0].text)
    body_div = article.findAll('div', {'class': 'body'})[0]
    all_paragraphs = body_div.findAll('p')
    if len(all_paragraphs) == 0:
        all_paragraphs = body_div.findAll('div')
    body = ''
    for paragraph in all_paragraphs:
        body += paragraph.text
    image = article.findAll('img', {'class': 'lead_image'})
    if len(image) > 0:
        image = image[0]['src']
    code = re.search(r'(\d+)', article.findAll('div', {'class': 'news_id_c'})[0].text.strip()).group(0)
    title = article.findAll('h1', {'class': 'title'})[0].a['title']
    subtitle = article.findAll('div', {'class': 'subtitle'})[0].text.strip()
    category = article.findAll('div', {'class': 'news_path'})[0].findAll('a')[1].text
    tags = [x.text for x in article.findAll('a', {'class': 'tags_item'})]
    link = article.findAll('a', {'class': 'link_en'})[0]['href']
#re.sub(r'\s+', ' ', body)
    return {'title': title,
            'subtitle': subtitle,
            'body': body,
            'category': category,
            'tags': tags,
            'code': code,
            'code_en': number_standardizer(code),
            'link': link,
            'date': date,
            'time': time,
            'image': image}


def crawler(from_date, to_date):
    import jdatetime
    from bs4 import BeautifulSoup
    import requests

    today_date = re.sub('-', '/', str(jdatetime.date.today()))

    if from_date is None:
        from_date = today_date

    if to_date is None:
        to_date = today_date

    has_next = True
    with open('links.txt', 'at', encoding='utf-8') as f:
        articles = []
        page_number = 1
        while has_next:
            url = f'https://www.asriran.com/fa/archive?service_id=-1&sec_id=-1&cat_id=-1&rpp=100&from_date={from_date}' \
                  f'&to_date={to_date}&p={page_number}'
            print(url)
            res = requests.get(url)
            soup = BeautifulSoup(res.text, 'html.parser')
            articles += soup.findAll('article', {'class': 'vizhe_cv'})
            has_next = soup.find('a', {'class': 'next'}) is not None
            page_number += 1
        data = []
        i = 1
        print(f'articles = {len(articles)})')
        for article in articles:
            try:
                print(f'i = ${i}, https://www.asriran.com{article.a["href"]}')
                tmp = parser(BeautifulSoup(requests.get(f'https://www.asriran.com{article.a["href"]}').text, 'html.parser'))
                data.append(tmp)
                i += 1
            except:
                global parsing_errors
                parsing_errors += 1
        c = 1
        for x in data:
            try:
                r = requests.post("http://localhost:9200/articles/_doc", json=x)
                #while r.status_code != 201:
                #    r = requests.post("http://localhost:9200/articles/_doc", json=x)
                print('Posted article #', c)
                c += 1
            except:
                global posting_errors
                posting_errors += 1
            #f.write('{\n')
            #cnt = len(x.keys())
            #i = 0
            #for y in zip(x.keys(), x.values()):
                #if i == cnt-1:
                #    f.write(f'{y[0]} : {y[1]}\n')
                #else:
                #    f.write(f'{y[0]} : {y[1]},\n')
            #f.write('},\n')


if __name__ == '__main__':
    crawler('1402/07/29', '1402/08/01')
    print(f'posting errors = {posting_errors}')
    print(f'parsing errors = {parsing_errors}')