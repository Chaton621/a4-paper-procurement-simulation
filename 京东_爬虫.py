import time
import csv
import random
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def manual_login_and_search(driver, search_keyword):
    driver.get("https://www.jd.com")
    print("请手动登录京东账号，登录完成后输入搜索关键词，程序将自动继续...")
    while True:
        if "京东" in driver.title:
            try:
                driver.find_element(By.CLASS_NAME, "nickname")
                print("登录成功！开始搜索商品...")
                break
            except:
                pass
        time.sleep(3)

    search_box = driver.find_element(By.ID, "key")
    search_box.clear()
    search_box.send_keys(search_keyword)
    driver.find_element(By.CLASS_NAME, "button").click()
    time.sleep(5)

def product_matches(title):
    keywords = ["70g", "A4", "复印纸", "5包", "500张"]
    return all(kw in title for kw in keywords)

def parse_product_list(html):
    soup = BeautifulSoup(html, "lxml")
    items = []
    product_list = soup.select(".gl-item")

    for product in product_list:
        name_tag = product.select_one(".p-name a")
        if not name_tag:
            continue

        full_title = name_tag.get_text(strip=True)
        if not product_matches(full_title):
            continue

        product_url = "https:" + name_tag.get("href") if name_tag.get("href") else "无"
        price_tag = product.select_one(".p-price strong i")
        price = price_tag.get_text(strip=True) if price_tag else "无"
        comment_tag = product.select_one(".p-commit a")
        comment_num = comment_tag.get_text(strip=True) if comment_tag else "无"

        items.append({
            "商品名称": full_title,
            "规格": "70g A4 每箱5包 每包500张",
            "价格": price,
            "评论数": comment_num,
            "商品链接": product_url
        })
    return items

def save_to_csv(data, filename):
    if not data:
        print("无数据，跳过保存")
        return
    keys = data[0].keys()
    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

def main():
    driver = create_driver()
    search_keyword = "70g A4复印纸 每箱5包 每包500张"
    manual_login_and_search(driver, search_keyword)

    all_data = []
    max_pages = 10

    for page in range(1, max_pages + 1):
        print(f"\n请手动翻到第 {page} 页，然后按回车键开始抓取...")
        input("按回车开始爬取本页数据...")
        time.sleep(random.uniform(3, 5))

        html = driver.page_source
        items = parse_product_list(html)
        all_data.extend(items)

        print(f"第 {page} 页数据抓取完成，共抓取 {len(items)} 条记录。")

    driver.quit()
    save_to_csv(all_data, "jd_a4_paper_filtered_manual.csv")
    print("数据保存完成：jd_a4_paper_filtered_manual.csv")

if __name__ == "__main__":
    main()
