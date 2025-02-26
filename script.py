from playwright.sync_api import sync_playwright, Response
from datetime import timezone, datetime
from time import sleep
import csv


a = f'''##############################################
        Script ini dibuat untuk keperluan tugas linguistik korpus pada mata kuliah Bahasa dan Media
        Dibuat oleh: Taufik Rahmadiansyah, NPM: 180210220044
##############################################'''

print(a)
link = input("Enter the Instagram link: ")
cake = str(input("Enter the cookies: "))
filename = input("Enter the filename: (e.g. data.csv): ")
cookies = []
for i in cake.split('; '):
    b = {}
    b['name'] = i.split('=')[0]
    b['value'] = i.split('=')[1]
    b['domain'] = '.instagram.com'
    b['path'] = '/'
    cookies.append(b)

bucket = []
def intercept_response(response: Response):
    global bucket
    if response.request.resource_type == "xhr":
        if 'xdt_api__v1__feed__user_timeline_graphql_connection' in response.text():
            node = response.json()['data']['xdt_api__v1__feed__user_timeline_graphql_connection']['edges']
            for value in node:
                data = {}
                tagged = []
                data['profile_url'] = f'''https://instagram.com/{value['node']['user']['username']}'''
                data['username'] = value['node']['user']['username']
                data['fullname'] = value['node']['user']['full_name']
                data['post_url'] = f'''https://instagram.com/p/{value['node']['code']}'''
                data['caption'] = value['node']['caption']['text'] if value['node']['caption'] != None else 'None'
                data['comment_count'] = value['node']['comment_count']
                data['like_count'] = value['node']['like_count']
                data['location'] = value['node']['location']['name'] if value['node']['location'] != None else 'None'
                data['pub_date'] = datetime.fromtimestamp(value['node']['taken_at'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                data['tagged'] = tagged
                try:
                    usertags = value['node']['usertags']['in']
                    for i in range(10):
                        dict = {}
                        dict['tagged_fullname'] = usertags[i]['user']['full_name']
                        dict['tagged_username'] = usertags[i]['user']['username']
                        tagged.append(dict)
                except TypeError:
                    while len(tagged) < 10:   
                        dict = {}
                        dict['tagged_fullname'] = 'None'
                        dict['tagged_username'] = 'None'
                        tagged.append(dict)
                except IndexError:
                    while len(tagged) < 10:
                        dict = {}
                        dict['tagged_fullname'] = 'None'
                        dict['tagged_username'] = 'None'
                        tagged.append(dict)
                bucket.append(data)
                print(f'''Post scrapped:{len(bucket)}''')  

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context()
    context.add_cookies(cookies)
    page = context.new_page()
    page.on("response", intercept_response)
    page.goto(link)

    _prev_height = -1
    _max_scrolls = 50
    _scroll_count = 0
    while _scroll_count < _max_scrolls:
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        page.wait_for_timeout(2000)
        new_height = page.evaluate('document.body.scrollHeight')
        if new_height == _prev_height:
            break
        _prev_height = new_height
        _scroll_count += 1
        sleep(1)

    context.close()
    browser.close()

flattened_data = []
for entry in bucket:
    flattened_entry = entry.copy()
    for i in range(10):
        tagged_fullname = entry['tagged'][i]['tagged_fullname'] if i < len(entry['tagged']) else ''
        tagged_username = entry['tagged'][i]['tagged_username'] if i < len(entry['tagged']) else ''
        flattened_entry[f'tagged_fullname_{i+1}'] = tagged_fullname
        flattened_entry[f'tagged_username_{i+1}'] = tagged_username
    del flattened_entry['tagged']
    flattened_data.append(flattened_entry)

header = flattened_data[0].keys()

with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=header)
    writer.writeheader()
    writer.writerows(flattened_data)

print(f"Data has been written to {filename}")
