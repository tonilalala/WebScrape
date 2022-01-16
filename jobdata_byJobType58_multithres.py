from selenium import webdriver

import selenium.webdriver.support.ui as ui
from selenium.webdriver.chrome.options import Options
import threading
from multiprocessing import Queue
from tqdm import tqdm
from time import sleep
import json
import sys
import timeit
from importlib import reload
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

q = Queue()
queue_chrome=Queue()

hot_cities = ["北京", "上海", "广州", "深圳", "成都", "杭州", "南京", "天津", "武汉", "重庆"]
selected_jobtypes = ["餐饮", "家政保洁/安保", "美容/美发", "娱乐/休闲", "保健按摩", "运动健身", "人事/行政/后勤", "司机", "销售", "客服", "贸易/采购",
                     "超市/百货/零售", "淘宝职位", "房产中介", "酒店", "市场/媒介/公关", "广告/会展/咨询", "美术/设计/创意", "普工/技工", "物流/仓储",
                     "汽车制造/服务", "计算机/互联网/通信", "教育培训", "财务/审计/统计", "金融/银行/证券/投资", "保险", "医院/医疗/护理", "建筑"]
job_categories = {"生活 | 服务业": ["餐饮", "家政保洁/安保", "美容/美发", "娱乐/休闲", "保健按摩", "运动健身"],
                  "人力 | 行政 | 管理": ["人事/行政/后勤", "司机"],
                  "销售 | 客服 | 采购 | 淘宝": ["销售", "客服", "贸易/采购", "超市/百货/零售", "淘宝职位", "房产中介"],
                  "酒店": ["酒店"],
                  "市场 | 媒介 | 广告 | 设计": ["市场/媒介/公关", "广告/会展/咨询", "美术/设计/创意"],
                  "生产 | 物流 | 质控 | 汽车": ["普工/技工", "物流/仓储", "汽车制造/服务"],
                  "网络 | 通信 | 电子": ["计算机/互联网/通信"],
                  "法律 | 教育 | 翻译 | 出版": ["教育培训"],
                  "财会 | 金融 | 保险": ["财务/审计/统计", "金融/银行/证券/投资", "保险"],
                  "医疗 | 制药 | 环保": ["医院/医疗/护理"],
                  "建筑 | 装修 | 物业 | 其他": ["建筑"]}

def gen_para():
    selected_cities = ["广州"]

    x = -1920
    y = 1
    long = 475
    high = 300
    reslution_x = 1920
    for i in range(len(selected_cities)):
        if (x + long >= reslution_x):
            y = y + high
            x = -1920
        else:
            x = x + long
        queue_chrome.put([x, y, long, high, selected_cities[i]])
    return len(selected_cities)

result = {}
def start_webdriver():
    start = timeit.default_timer()
    chrome_options = Options()
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
    chrome_options.add_argument('blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度

    browser = webdriver.Chrome(chrome_options=chrome_options, executable_path="./chromedriver")
    chrome_para=queue_chrome.get()
    browser.set_window_size(chrome_para[2], chrome_para[3])
    browser.set_window_position(chrome_para[0], chrome_para[1])

    wait = ui.WebDriverWait(browser, 10)

    browser.get(
        "https://www.58.com/changecity.html?catepath=job.shtml&catename=%E6%8B%9B%E8%81%98%E4%BF%A1%E6%81%AF&fullpath=9224&PGTID=0d202408-0000-1405-0a04-9682bbc57518&ClickID=1")
    wait.until(lambda browser: browser.find_element_by_class_name("content-city"))

    sleep(3)

    categories_list = list(job_categories.keys())
    for k in tqdm(range(len(categories_list))):
        category = categories_list[k]
        selected_jobtypes = job_categories[category]
        for j in range(len(selected_jobtypes)):
            jobtype = selected_jobtypes[j]
            city_name = chrome_para[4]
            try:
                print("Current Parsing: ", category, jobtype, city_name)
                if city_name in hot_cities:
                    city = browser.find_elements_by_xpath('//*[@id="hot"]//*[text()="{}"]'.format(city_name))[0]
                else:
                    city = \
                        browser.find_elements_by_xpath('//*[@id="content-box"]//*[text()="{}"]'.format(city_name))[0]
                city.click()
                sleep(3)


                element = WebDriverWait(browser, 20).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="sidebar-left"]//*[text()="{}"]'.format(category))))
                try:
                    element.click()
                except:
                    element.send_keys("\n")

                print("here")

                element = WebDriverWait(browser, 20).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="sidebar-right"]//*[text()="{}"]'.format(jobtype))))
                sleep(5)
                try:
                    element.click()
                except:
                    element.send_keys("\n")


                print("there")

                sleep(5)


                wait.until(lambda browser: browser.find_element_by_id("filterTime"))

                time_filter_elem = browser.find_element_by_id("filterTime")
                time_filter_elem.click()


                sleep(1)
                element = WebDriverWait(browser, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '七天以内')]")))
                try:
                    element.click()
                except:
                    element.send_keys("\n")

                wait.until(lambda browser: browser.find_element_by_class_name("selected_options"))

                number = browser.find_element_by_class_name("selected_options").find_element_by_class_name(
                    "total").text
                number = int(number.split(" ")[1])
                result["_".join([category, jobtype, city_name])] = number

                sleep(5)
                browser.get(
                    "https://www.58.com/changecity.html?catepath=job.shtml&catename=%E6%8B%9B%E8%81%98%E4%BF%A1%E6%81%AF&fullpath=9224&PGTID=0d202408-0000-1405-0a04-9682bbc57518&ClickID=1")
                wait.until(lambda browser: browser.find_element_by_class_name("content-city"))


            except:
                print("FAIL!!!!!")
                result["_".join([category, jobtype, city_name])] = 0
                browser.get(
                    "https://www.58.com/changecity.html?catepath=job.shtml&catename=%E6%8B%9B%E8%81%98%E4%BF%A1%E6%81%AF&fullpath=9224&PGTID=0d202408-0000-1405-0a04-9682bbc57518&ClickID=1")
                wait.until(lambda browser: browser.find_element_by_class_name("content-city"))
                continue



if __name__ == "__main__":
    start = timeit.default_timer()
    number_chrome = gen_para()
    all_thres = []
    for i in range(number_chrome):
        t = threading.Thread(target=start_webdriver)
        t.start()
        all_thres.append(t)

    for t in all_thres:
        t.join()

    print("Totale Time: ",  timeit.default_timer() - start )
    with open("result_jobtype.json", 'w') as outfile:
        json.dump(result, outfile)

