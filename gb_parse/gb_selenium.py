from selenium import webdriver
from selenium.webdriver.common.keys import Keys

if __name__ == '__main__':
    url = 'https://habr.com/'
    browser = webdriver.Chrome()
    browser.get(url)
    print(1)