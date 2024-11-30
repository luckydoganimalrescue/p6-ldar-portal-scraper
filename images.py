#!/usr/bin/env python

__doc__ = """
Usage:
  images.py --pin <pin> --user <user> --password <password> [--start-page N] [--hold <hold_str>]
  [--year-pattern <year_str>]

Options:
  --pin=<pin>       Pet Portal Account Pin
  --user=<user>      Pet Portal User Name
  --password=<password>  Pet Portal Password
  --start-page= <N>         Start Downloads on page N
  --hold=<hold_str>  String to identify hold status [default: Hold]
  --year-pattern=<year_str>  Year pattern to identify animals (e.g., '-24-') [default: -24-]

Environment:

N/A
"""

import re
import sys
import time
from typing import Any, Dict, List, Optional

import docopt
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


class RescuePortal:
    """
    Main entry point for the script.
    """

    def __init__(self, args: Dict[str, str]):
        self.args = args
        self.browser: WebDriver = webdriver.Chrome()

    def login(self) -> None:
        """
        Login to the RescueGroups Portal
        """
        self.browser.get("https://portal.rescuegroups.org/login#atbh")

        pin = self.browser.find_element(
            By.XPATH, '//*[@id="mainbody"]/form/table/tbody/tr[1]/td[2]/input'
        )
        user = self.browser.find_element(
            By.XPATH, '//*[@id="mainbody"]/form/table/tbody/tr[2]/td[2]/input'
        )
        password = self.browser.find_element(
            By.XPATH, '//*[@id="mainbody"]/form/table/tbody/tr[3]/td[2]/input'
        )

        pin.send_keys(self.args["--pin"])
        user.send_keys(self.args["--user"])
        password.send_keys(self.args["--password"])

        self.browser.find_element(
            By.XPATH, '//*[@id="mainbody"]/form/table/tbody/tr[5]/td[2]/input'
        ).click()

    def list_page(self, page_number: int) -> None:
        """
        Navigate to the list page
        """
        print(f"Processing page {page_number}")
        self.browser.get(
            f"https://portal.rescuegroups.org/list?&listStart={page_number}"
        )

    def sanitize(self, html: str, previous: Tag) -> str:
        """
        Clean up the HTML content for filenames
        """
        clean = html.replace("\n", "").replace("Adopted", "")
        clean = previous.get_text() + "-" + clean
        clean = re.sub(r"[^a-zA-Z0-9\-]", "", clean)
        return clean

    def save_image(self, src: str, filename: str) -> None:
        """
        Save the image to the filesystem
        """
        with open(f"pages/{filename}.jpg", "wb") as file:
            response = requests.get(src, timeout=5)
            file.write(response.content)

    def show_animal(self, href: str) -> None:
        """
        Navigate to the animal's page
        """
        print(f"Processing https://portal.rescuegroups.org/{href}")
        self.browser.get(f"https://portal.rescuegroups.org/{href}")

    def show_picture(self) -> None:
        """
        Display the animal's picture
        """
        self.browser.find_element(
            By.XPATH,
            '//*[@id="mainbody"]/table[7]/tbody/tr[2]/td[1]/table/tbody/tr/td[2]/a/img',
        ).click()

    def close_picture(self) -> None:
        """
        Close the full-size picture view
        """
        self.browser.find_element(By.XPATH, '//*[@id="fullSize"]/a').click()

    def get_pic_url(self) -> str:
        """
        Extract the picture URL
        """
        img = self.browser.find_element(By.XPATH, '//*[@id="fullSize"]/div[2]/img')
        return img.get_attribute("src") or ""

    def download_links(self, links: List[Dict[str, str]]) -> None:
        """
        Download images from the provided links
        """
        for link in links:
            self.show_animal(link["href"])
            self.show_picture()
            src = self.get_pic_url()
            self.save_image(src, link["filename"])
            self.close_picture()

    def process_table_data(self, tds: List[Tag]) -> List[Dict[str, str]]:
        """
        Process the HTML table data and return download links
        """
        previous: Optional[Tag] = None
        links: List[Dict[str, str]] = []

        hold_str = self.args.get("--hold", "Hold")
        year_pattern = self.args.get("--year-pattern", "-24-")

        for td in tds:
            html = td.get_text()
            if re.match(hold_str, html) and re.match(
                f".*{year_pattern}.*", html, re.DOTALL
            ):
                if previous:
                    tag_a = previous.find("a")
                    # Ensure the result is a Tag and has the href attribute
                    if isinstance(tag_a, Tag) and "href" in tag_a.attrs:
                        info = {
                            "href": tag_a["href"],
                            "filename": self.sanitize(html, previous),
                        }
                        links.append(info)

            previous = td

        return links

    def run_search(self) -> None:
        """
        Perform a search on the portal
        """
        self.browser.find_element(
            By.XPATH, '//*[@id="mainbody"]/table[2]/tbody/tr[2]/td/a'
        ).click()
        self.browser.find_element(By.XPATH, '//*[@id="simpleFilter"]/div[1]/a').click()

    def run(self) -> int:
        """
        Main function to execute the entire workflow
        """
        self.login()
        self.run_search()

        start_page: int = int(self.args.get("--start-page", 1))
        end_page: int = 45

        for i in range(start_page, end_page):
            self.list_page(i)

            html_source: str = self.browser.page_source
            soup = BeautifulSoup(html_source, "html.parser")
            tds: List[Tag] = soup.find_all("td")

            links: List[Dict[str, str]] = self.process_table_data(tds)

            self.download_links(links)

        self.browser.quit()
        return 0


def main(args: Dict[str, Any]) -> int:
    """
    Main entry point for the script.
    """
    portal = RescuePortal(args)
    return portal.run()


if __name__ == "__main__":
    arguments = docopt.docopt(__doc__)
    sys.exit(main(arguments))
