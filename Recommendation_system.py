import re

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from webdrivermanager.chrome import ChromeDriverManager
from textblob import TextBlob
import requests
import pandas as pd
import ast
import json
import webbrowser
import time
import datetime


def search_am(phrase):
    link_start = "https://www.amazon.in/s?k="
    link_end = "&ref=nb_sb_noss"
    link = link_start + phrase.replace(' ', '+') + link_end
    print("search am link_full= ", link)

    driver = webdriver.Chrome()
    # driver = webdriver.Chrome("C:\Program Files (x86)\chromedriver.exe")

    wait = WebDriverWait(driver, 5)
    driver.get(link)

    names_of_ele = []
    list_of_ele_on_page = driver.find_elements(By.CSS_SELECTOR, 'a')
    i = 0
    for name in list_of_ele_on_page:
        className = name.get_attribute('class')
        if className == 'a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal':
            names_of_ele.append(name)
            i += 1

    links = []
    for i in names_of_ele:
        temp = i.get_attribute('href')
        links.append(temp)

    driver.quit()

    return links


def get_element_dets(link):
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 2)
    driver.get(link)
    driver.minimize_window()
    try:
        title1 = driver.find_element(By.ID, "productTitle")
        title2 = title1.text
    except:
        title2 = " "

    try:
        popular = driver.find_element(By.ID, "acrCustomerReviewText").text
        popularity = popular.replace(" ratings", "").replace(",", "")
    except:
        popularity = '0'

    try:
        rating = driver.find_element(By.CSS_SELECTOR, "span[class='a-size-medium a-color-base']").text
        rate = rating.replace(" out of 5", "")
    except:
        rate = '0'
    feat_f = []

    try:
        pr = driver.find_element(By.CSS_SELECTOR,
                                 "span[class='a-price aok-align-center reinventPricePriceToPayMargin priceToPay'] span[class='a-price-whole']").text
        price = pr.replace(',', '')
    except:
        price = 0

    try:
        technical_details = driver.find_element(By.ID, 'productDetails_techSpec_section_1')

        # Get all the rows in the technical details table
        rows = technical_details.find_elements(By.TAG_NAME, 'tr')

        # Loop through each row and get the details
        for row in rows:
            # Get the label and value
            label = row.find_element(By.TAG_NAME, 'th').text
            value = row.find_element(By.TAG_NAME, 'td').text
            feat_f.append(label + ':' + str(value))

    except:
        feat_f = [':']
    # print(feat_f)
    feedback_f = []
    try:
        feedback_section = driver.find_element(By.ID, 'reviews-medley-footer')

        # Find all the feedback elements within the section
        feedback_elements = feedback_section.find_elements(By.XPATH,
                                                           "//a[@class='a-size-base a-link-normal review-title a-color-base review-title-content a-text-bold']//span")

        # Loop through each feedback element and extract the feedback text
        for feedback_element in feedback_elements:
            feedback_text = feedback_element.text
            feedback_f.append(feedback_text)
    except:
        feedback_f.append(" ")

    driver.quit()
    return title2, rate, popularity, price, feat_f, feedback_f


def caller(phrase):
    links = search_am(phrase)
    data = {}
    print(len(links))
    i = 0
    for link in links:
        if i < 7:
            data[link] = {}
            title, rate, popularity, price, feat_f, feedback_f = get_element_dets(link)
            data[link]['feedback'] = feedback_f
            data[link]['title'] = title
            data[link]['rate'] = rate
            data[link]['popularity'] = popularity
            data[link]['features'] = feat_f
                # if isinstance(price, int):
            data[link]['price'] = price
            i = i+1
        """else:

            data[link]['price'] = price.split(' ')[1]
        # print(len(data))"""
    return data


def assign_popularity_rating():
    with open('products.json', 'r') as openfile:

        data = json.load(openfile)
    try:
        temp = 0
        for k in data.keys():
            p = int(data[k]['popularity'])
            r = float(data[k]['rate'])
            if p < 50:
                temp = 1
            elif p < 100:
                temp = 2
            elif p < 150:
                temp = 3
            else:
                temp = 4
            score = (temp)
            data[k]['Popularity_Score'] = score
            data[k]['Rating_Score'] = r
    except:
        pass
    with open("products_mod.json", "w") as outfile:
        json.dump(data, outfile)


def assign_sentiment_rating():
    with open('products_mod.json', 'r') as openfile:

        data = json.load(openfile)
    #print(data)
    sm = 0
    for k in data.keys():
        temp = data[k]['feedback']
        # print(temp)
        # res = json.loads(temp)
        z = 0
        sm = 0
        for i in temp:
            # print(i)
            z += 1
            t = TextBlob(i).sentiment.polarity
            # print(t)
            sm += t
        if (z == 0):
            rating = 0
        else:
            # print(sm
            # print(z)
            rating = sm / z
        data[k]['Review_Score'] = rating
    with open("products_mod_2.json", "w") as outfile:
        json.dump(data, outfile)


def check_price_relevence(cpr_price, margin):
    with open('products_mod_2.json', 'r') as openfile:

        data = json.load(openfile)

    price = float(cpr_price)
    margin = float(margin)
    try:
        for k in data.keys():
            data_ref = str(data[k]['price'])
            tem = data_ref.replace(',', '')
            temp = float(tem)

            if temp < price + margin and temp > price - margin:
                rating = 1
            else:
                rating = 0

            data[k]['Price_relevence_Score'] = rating
    except:
        pass

    with open("products_mod_3.json", "w") as outfile:
        json.dump(data, outfile)


def form_featureset():
    with open('products_mod_3.json', 'r') as openfile:

        data = json.load(openfile)
        feat = []
        set_c = []
        print(data)
        for k in data.keys():

            temp = data[k]['features']

            temp2 = []

            for i in temp:
                tag = i.split(':')[0]
                if tag not in feat:
                    feat.append(tag)
        # print(feat)
        for k in data.keys():
            temp = data[k]['features']
            temp2 = [-1] * len(feat)
            for i in temp:
                tag = i.split(':')[0]

                ind = feat.index(tag)

                temp2[ind] = i.split(':')[1]

            set_c.append(temp2)

    df = pd.DataFrame(set_c, columns=feat)
    df.to_csv('product_descriptions.csv', index=False)
    return df


def sort_d(data):
    """tot = {}
    l = []
    for k in data.keys():
        tot[k] = data[k]['Total_score']
        print("tot[k]- ",tot[k])
    # print(tot)
    l.append(sorted(tot.items(), reverse=True, key=lambda x: x[1]))
    # print("data coming in sort fun - ", data)
    # print("sort list l-",l)
    print("l- ", l)
    l_f = []
    i = 0
    # print((l[0])[0][1])
    while i < 5:
        l_f.append(l[0][i][0])
        i = i + 1
    return l_f"""
    items = [(key, item['Total_score']) for key, item in data.items()]

    # Sort the list of tuples by the "Total_score" value in descending order
    sorted_items = sorted(items, key=lambda x: x[1], reverse=True)

    # Return a list of the top 5 keys in descending order by "Total_score"
    return [item[0] for item in sorted_items[:5]]


def tune_search(choice):
    with open('products_mod_3.json', 'r') as openfile:

        data = json.load(openfile)

    #print("tune search - ", data)
    for k in data.keys():
        price_rel = data[k]['Price_relevence_Score']
        review_score = data[k]['Review_Score']
        pop_score = data[k]['Popularity_Score']
        pop_score_k = pop_score / 4

        rate_score = data[k]['Rating_Score']
        rate_score_k = rate_score / 5

        if choice == 1:
            total_score = 5 * pop_score_k + rate_score_k + review_score + price_rel
        if choice == 2:
            total_score = pop_score_k + 5 * rate_score_k + review_score + price_rel
        if choice == 3:
            total_score = pop_score_k + rate_score_k + review_score + 5 * price_rel
        if choice == 4:
            total_score = pop_score_k + rate_score_k + 5 * review_score + price_rel

        else:
            total_score = pop_score_k + rate_score_k + review_score + price_rel
        data[k]['Total_score'] = total_score
        # print(data[k]['Total_score'])
    links = sort_d(data)
    with open("products_mod_3.json", "w") as outfile:
        json.dump(data, outfile)

    # print("tune search links after opertaion - ", data)

    return links


def communicator(order, brand, price, cpr_price, margin, choice):
    order = order
    brand = brand
    price = price
    cpr_price = cpr_price
    margin = margin
    choice = choice

    if brand.lower() != 'no':
        order_m = order + " by " + brand
    else:
        order_m = order
    if price.lower() != 'no':
        order_f = order_m + " price " + price
    else:
        order_f = order_m
    data = caller(order_f)
    #print(data)

    with open("products.json", "w") as outfile:
        json.dump(data, outfile)
    assign_popularity_rating()
    assign_sentiment_rating()
    check_price_relevence(cpr_price, margin)
    df = form_featureset()
    #print("Your results are ready...........")

    #print("commutor data of df - \n", df)

    #print("product_descriptions.csv has been saved.You can check the company model and features for referral later as per convinience")

    #print("Please specify how your choices should be sorted? \n 1 for popularity based \n 2 for rating based \n 3 for price relevence based \n 4 for review based \n 5 for overall.")

    #choice = int(input())

    links = tune_search(choice)
    # print("commutor links - ",links)
    #print("Here are your best 5 results")

    #for link in links:
    #    webbrowser.open(link)

    time.sleep(5)
    options = [1, 2, 3, 4, 5]
    options_title = ["Popularity", "Rating", "Price", "Review", "Overall"]
    result_dict = {}
    # print("Here are the other bests")
    for i in range(1,6):
        links = tune_search(i)
        result_dict[options_title[i-1]] = links

    return result_dict
# communicator()
