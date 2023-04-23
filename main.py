from time import sleep
from bs4 import BeautifulSoup
import requests
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from flask import Flask, render_template, url_for, redirect, request
import Recommendation_system
import Sentimental_Analysis

# python -m pip install pandas
from urllib3 import Retry
from requests.adapters import HTTPAdapter


app = Flask(__name__)
# Set the path to the Chrome driver executable
chrome_driver_path = os.path.abspath('chromedriver')

# Open a Chrome browser window
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in headless mode to avoid opening a visible window
driver = webdriver.Chrome(executable_path=chrome_driver_path, options=options)

# Run JavaScript code to get the user agent header
script = "return navigator.userAgent;"
user_agent_header = driver.execute_script(script)

# Close the browser window
driver.quit()


HEADERS = ({     
    'User-Agent': user_agent_header,
    'Accept-Language': 'en-US, en;q=0.5'})



def getnextpage(soup, link):
    # this will return the next page URL
    pages = soup.find('div', {'class': 'a-form-actions a-spacing-top-extra-large'}).find('ul',
                                                                                         {'class': 'a-pagination'})
    if not pages.find('li', {'class': 'a-disabled a-last'}):
        # url = 'https://www.amazon.in' +
        url = pages.find('li', {'class': 'a-last'}).find('a')['href']
        return url
    else:
        return ""


def get_soup_with_header(url):
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.content, 'html.parser')
    return soup


reviewlist = []


def get_reviews(soup):
    reviews = soup.find_all('div', {'data-hook': 'review'})
    try:
        for item in reviews:
            # review = {
            # 'title': item.find('a', {'data-hook': 'review-title'}).text.strip(),
            # 'rating':  float(item.find('i', {'data-hook': 'review-star-rating'}).text.replace('out of 5 stars', '').strip()),
            # 'body': item.find('span', {'data-hook': 'review-body'}).text.strip(),
            # }
            review = []
            try:
                review = {
                    'body': item.find('span', {'data-hook': 'review-body'}).text.strip()
                }
                reviewlist.append(review)
            except:
                pass

    except:
        pass


@app.route('/main_func/<products>')
def main_func(products):
    product = products
    url = "https://www.amazon.in/s?k=" + product.replace(" ", "+")
    soup = get_soup_with_header(url)
    #print(soup)
    findlink = soup.find('div', {
        'class': 'sg-col sg-col-4-of-12 sg-col-8-of-16 sg-col-12-of-20 sg-col-12-of-24 s-list-col-right'})

    print("link of the product", findlink)
    x = findlink.find('a', {'class': 'a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal'})
    nextPage = x.get("href")
    str1 = 'https://www.amazon.in' + nextPage
    print("str1", str1)
    link = []
    page = BeautifulSoup(requests.get(str1, headers=HEADERS).content, 'html.parser')
    for i in page.findAll("a", {'data-hook': "see-all-reviews-link-foot"}):
        link.append(i['href'])

    print(link)
    for j in range(len(link)):
        for k in range(100):
            url = 'https://www.amazon.in' + link[j] + '&pageNumber=' + str(k)
            print(url)
            response = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(response.content)
            for i in soup.findAll("span", {'data-hook': "review-body"}):
                #reviewlist.append(i.text)
                review = {
                    'body': i.text
                }
                reviewlist.append(review)

    """
    previous code for getting next page and then scraping the reviews
    next_soup = get_soup_with_header(str)
    links = next_soup.find('div', {'id': 'reviews-medley-footer'})
    print(links)
    final_link = "https://www.amazon.in" + links.a.get("href")

    for x in range(1, 100):
        print(final_link)
        soup = get_soup_with_header(final_link)
        print(soup)
        print(f'Getting page: {x}')
        get_reviews(soup)
        print(len(reviewlist))        sleep(3)
        if not soup.find('li', {'class': 'a-disabled a-last '}):
            # a = soup.select(a[href='/Test-Exclusive_2020_1123-Multi-3GB-Storage/product-reviews/B089MS8NVX/ref=cm_cr_arp_d_paging_btm_6?ie=UTF8&pageNumber=6&reviewerType=all_reviews'])
            final_link = getnextpage(soup, final_link)
            # print("a = ",a)
            print("url comming ", final_link)
            if final_link == "":
                break
            pass
        else:
            break
    """

    df = pd.DataFrame(reviewlist)
    df.to_csv('reviews.csv', index=False)
    results = Sentimental_Analysis.analysis()
    return render_template("sentimental_result.html", content=results)


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/contact')
def contact():
    return render_template("contact.html")


@app.route('/recommend', methods=["POST", "GET"])
def call_to_scrapper():
    if request.method == "GET":
        return render_template("recommend_details.html")
    if request.method == 'POST':
        order = request.form.get("order")
        brand = request.form.get("brand")
        price = request.form.get("price")
        cpr_price = request.form.get("approx_price")
        margin = request.form.get("dip")
        choice = request.form.get(("choice"))
        links_dict = Recommendation_system.communicator(order, brand, price, cpr_price, margin, choice)
        return render_template("recommend_result.html", content=links_dict)


@app.route('/sentimental_analysis', methods=["POST", "GET"])
def sentimental_analysis():
    if request.method == "GET":
        return render_template("sentimental_analysis.html")
    if request.method == 'POST':
        products = request.form
        return redirect(url_for('main_func', products=products))


if __name__ == '__main__':
    app.run(debug=True)
