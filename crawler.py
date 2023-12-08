import requests
from bs4 import BeautifulSoup
import os

visited_links = set()
links_written = set()
DOMAIN_END_POINT = ''

def get_child_urls(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links_list = []

    for link in soup.find_all('a'):
        url_href = link.get('href')
        if url_href and url_href.startswith("/") and url_href != "/":
            links_list.append(url_href)

    for child_link in links_list:
        if child_link.startswith("/"):
            child_url = DOMAIN_END_POINT + child_link
            # print('Before -- ',visited_links,'child_link -- ',child_link)
            # print(child_link not in visited_links)
            if child_link not in visited_links:
                print(child_url + " -- " + child_link)
                visited_links.add(child_link)
                # print('After -- ',visited_links)
                get_child_urls(child_url)

    with open("URLs.txt", "a") as f:
        for url in links_list:
            if url not in links_written:
                links_written.add(url)
                f.write(url + "\n")

def read_from_sources(base_url):

    with open("URLs.txt", "r") as f:
        existing_urls = f.read().splitlines()
        for url in existing_urls:
            print("Read from URL:", base_url + url)

            # get the content of URL
            page = requests.get(base_url + url)

            # Creating BeautifulSoup object
            soup = BeautifulSoup(page.content, "html.parser")

            #ignoring Scripts and Styles for Scrapping
            [x.extract() for x in soup.findAll(['script', 'style'])]

            # Get the text from the URL
            text = soup.get_text()

            # Removing all the new lines
            # output = ' '.join(text.split())
            output = ' '.join(line.strip() if line.strip() else '' for line in text.splitlines())

            #Saving the scraped content to a file
            with open('web_scrapped_data.txt', 'a') as f:
                f.write(output+ "\n")

def clean_up():
    # Check if the file exists before removing
    if os.path.exists("URLs.txt"):
        os.remove("URLs.txt")
        print("File 'URLs.txt' removed successfully.")
    else:
        print("File 'URLs.txt' does not exist.")

    # Check if the file exists before removing
    if os.path.exists("web_scrapped_data.txt"):
        os.remove("web_scrapped_data.txt")
        print("File 'web_scrapped_data.txt' removed successfully.")
    else:
        print("File 'web_scrapped_data.txt' does not exist.")

# Doing clean up
clean_up()
# Get the website URL
url = input("Enter website URL: ")
DOMAIN_END_POINT=url
get_child_urls(url)
read_from_sources(url)
