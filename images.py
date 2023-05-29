#!/usr/bin/env python

"""
Usage:
  images.py --pin <pin> --user <user> --password <password> [--start-page N]

Options:
  --pin        <pin>       Pet Portal Account Pin
  --user       <user>      Pet Portal User Name
  --password   <password>  Pet Portal Password
  --start-page <N>         Start Downloads on page N

Environment:
N/A
"""

from __future__ import print_function

import docopt
import sys
import re
import requests

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

def login(browser, args):
    """
    """

    browser.get("https://portal.rescuegroups.org/login#atbh")

    pin = browser.find_element_by_xpath('//*[@id="mainbody"]/form/table/tbody/tr[1]/td[2]/input')
    user = browser.find_element_by_xpath('//*[@id="mainbody"]/form/table/tbody/tr[2]/td[2]/input')
    password = browser.find_element_by_xpath('//*[@id="mainbody"]/form/table/tbody/tr[3]/td[2]/input')

    pin.send_keys(args['pin'])
    user.send_keys(args['user'])
    password.send_keys(args['password'])

    browser.find_element_by_xpath('//*[@id="mainbody"]/form/table/tbody/tr[5]/td[2]/input').click()

def list_page(browser, i):
    """
    """

    print("https://portal.rescuegroups.org/list?&listStart={}".format(i))
    browser.get("https://portal.rescuegroups.org/list?&listStart={}".format(i))

def sanitize(html, previous):
    """
    """

    clean = html.replace("\n", "")
    clean = clean.replace("Adopted", "")
    clean = previous.get_text() + "-" + clean
    clean = re.sub('[^a-zA-Z0-9\-]', "", clean)

    return clean

def save_image(src, filename):
    """
    """

    print("{} -> {}".format(src, filename))
    with open("pages/{}.jpg".format(filename), "wb") as file:
        response = requests.get(src)
        file.write(response.content)

def show_animal(browser, href):
    """
    """

    browser.get("https://portal.rescuegroups.org/{}".format(href))


def show_picture(browser):
    """
    """

    browser.find_element_by_xpath('//*[@id="mainbody"]/table[7]/tbody/tr[2]/td[1]/table/tbody/tr/td[2]/a/img').click()

def close_picture(browser):
    """
    """

    browser.find_element_by_xpath('//*[@id="fullSize"]/a').click()

def get_pic_url(browser):
    """
    """

    img = browser.find_element_by_xpath('//*[@id="fullSize"]/div[2]/img')
    src = img.get_attribute('src')

    return src

def download_links(browser, links):
    """
    """

    for link in links:
        href = link['href']
        filename = link['filename']

        show_animal(browser, href)
        show_picture(browser)
        src = get_pic_url(browser)
        save_image(src, filename)
        close_picture(browser)

def process_table_data(tds):
    """
    """

    previous = None
    links = []
    for td in tds:
        html = td.get_text()
        if re.match('Hold', html) and re.match('.*-21-.*', html, re.DOTALL):
            tag_a = previous.find('a')

            info = {}
            info['href'] = tag_a['href']
            info['filename'] = sanitize(html, previous)

            links.append(info)
        previous = td
    return links

def run_search(browser):
    """
    """

    # click Pet List
    browser.find_element_by_xpath('//*[@id="mainbody"]/table[2]/tbody/tr[2]/td/a').click()

    # click more options
    browser.find_element_by_xpath('//*[@id="simpleFilter"]/div[1]/a').click()

    # click
    return

def main(args):
    """
    """

    browser = webdriver.Chrome()
    login(browser, args)

    run_search(browser)

    start_page = 1
    end_page = 120

    for i in range(start_page, end_page):
        list_page(browser, i)

        html_source = browser.page_source
        soup = BeautifulSoup(html_source, "html.parser")
        tds = soup.find_all('td')

        links = process_table_data(tds)

        download_links(browser, links)

    browser.close()

    return 0

if __name__ == '__main__':
    arguments =  {}
    arguments['pin']        = ''
#    arguments['user']       = ''
#    arguments['password']   = ''
#    arguments['start-page'] = 1

#    arguments = docopt.docopt(__doc__, options_first=True, version="0.0.1")
    sys.exit(main(arguments))
