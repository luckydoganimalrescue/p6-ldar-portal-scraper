#!/usr/bin/env python

__doc__ = """
Usage:
  images.py --pin <pin> --user <user> --password <password> [--start-page N] [--hold <hold_str>] \
[--year-pattern <year_str>]

Options:
  --pin            <pin>       Pet Portal Account Pin
  --user           <user>      Pet Portal User Name
  --password       <password>  Pet Portal Password
  --start-page     <N>         Start Downloads on page N
  --hold           <hold_str>  String to identify hold status [default: Hold]
  --year-pattern   <year_str>  Year pattern to identify animals (e.g., '-21-') [default: -21-]

Environment:

N/A
"""

import re
import sys
from typing import Any, Dict, List, Optional

import docopt
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


def login(browser: WebDriver, args: Dict[str, str]) -> None:
    """
    Login to the RescueGroups Portal
    """
    browser.get("https://portal.rescuegroups.org/login#atbh")

    pin = browser.find_element(
        By.XPATH, '//*[@id="mainbody"]/form/table/tbody/tr[1]/td[2]/input'
    )
    user = browser.find_element(
        By.XPATH, '//*[@id="mainbody"]/form/table/tbody/tr[2]/td[2]/input'
    )
    password = browser.find_element(
        By.XPATH, '//*[@id="mainbody"]/form/table/tbody/tr[3]/td[2]/input'
    )

    pin.send_keys(args["--pin"])
    user.send_keys(args["--user"])
    password.send_keys(args["--password"])

    browser.find_element(
        By.XPATH, '//*[@id="mainbody"]/form/table/tbody/tr[5]/td[2]/input'
    ).click()


def list_page(browser: WebDriver, page_number: int) -> None:
    """
    Navigate to the list page
    """
    browser.get(f"https://portal.rescuegroups.org/list?&listStart={page_number}")


def sanitize(html: str, previous: Tag) -> str:
    """
    Clean up the HTML content for filenames
    """
    clean = html.replace("\n", "").replace("Adopted", "")
    clean = previous.get_text() + "-" + clean
    clean = re.sub(r"[^a-zA-Z0-9\-]", "", clean)
    return clean


def save_image(src: str, filename: str) -> None:
    """
    Save the image to the filesystem
    """
    with open(f"pages/{filename}.jpg", "wb") as file:
        response = requests.get(src, timeout=5)
        file.write(response.content)


def show_animal(browser: WebDriver, href: str) -> None:
    """
    Navigate to the animal's page
    """
    browser.get(f"https://portal.rescuegroups.org/{href}")


def show_picture(browser: WebDriver) -> None:
    """
    Display the animal's picture
    """
    browser.find_element(
        By.XPATH,
        '//*[@id="mainbody"]/table[7]/tbody/tr[2]/td[1]/table/tbody/tr/td[2]/a/img',
    ).click()


def close_picture(browser: WebDriver) -> None:
    """
    Close the full-size picture view
    """

    browser.find_element(By.XPATH, '//*[@id="fullSize"]/a').click()


def get_pic_url(browser: WebDriver) -> str:
    """
    Extract the picture URL
    """
    img = browser.find_element(By.XPATH, '//*[@id="fullSize"]/div[2]/img')
    return img.get_attribute("src") or ""


def download_links(browser: WebDriver, links: List[Dict[str, str]]) -> None:
    """
    Download images from the provided links
    """
    for link in links:
        show_animal(browser, link["href"])
        show_picture(browser)
        src = get_pic_url(browser)
        save_image(src, link["filename"])
        close_picture(browser)


def process_table_data(tds: List[Tag]) -> List[Dict[str, str]]:
    """
    Process the HTML table data and return download links
    """
    previous: Optional[Tag] = None
    links: List[Dict[str, str]] = []

    for td in tds:
        html = td.get_text()
        if re.match(r"Hold", html) and re.match(r".*-21-.*", html, re.DOTALL):
            if previous:
                tag_a = previous.find("a")
                # Ensure the result is a Tag and has the href attribute
                if isinstance(tag_a, Tag) and "href" in tag_a.attrs:
                    info = {
                        "href": tag_a["href"],
                        "filename": sanitize(html, previous),
                    }
                    links.append(info)

        previous = td

    return links


def run_search(browser: WebDriver) -> None:
    """
    Perform a search on the portal
    """

    browser.find_element(
        By.XPATH, '//*[@id="mainbody"]/table[2]/tbody/tr[2]/td/a'
    ).click()
    browser.find_element(By.XPATH, '//*[@id="simpleFilter"]/div[1]/a').click()


def main(args: Dict[str, Any]) -> int:
    """
    Main function
    """
    browser: WebDriver = webdriver.Chrome()
    login(browser, args)

    run_search(browser)

    start_page: int = int(args.get("--start-page", 1))
    end_page: int = 120

    for i in range(start_page, end_page):
        list_page(browser, i)

        html_source: str = browser.page_source
        soup = BeautifulSoup(html_source, "html.parser")
        tds: List[Tag] = soup.find_all("td")

        links: List[Dict[str, str]] = process_table_data(tds)

        download_links(browser, links)

    browser.quit()

    return 0


if __name__ == "__main__":
    arguments = docopt.docopt(__doc__)
    print(arguments)
    sys.exit(main(arguments))
