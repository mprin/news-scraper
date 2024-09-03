from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import threading
import re

# Initialize the Firebase app with your service account credentials
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://****.firebaseio.com/'
})

# Define a function to scrape and insert a single article into the database
def scrape_and_insert_article(link, ref):
    # Check if the article already exists in the database
    articles = ref.order_by_child('Link To Article').equal_to(link).get()
    if articles:
        print("Article already exists:", link)
        return

    # # Scrape the article data
    driver.get(link)
    
    
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "mainArticle")))
    page_content = driver.page_source
    soup = BeautifulSoup(page_content, "html.parser")
    paragraphs = soup.find_all("p")
    image = soup.find('img', class_="object-fit-cover").get('src')
    title = soup.find('h1', class_="text-explosion").text
    author = soup.find('span', class_="sc-author").text
    publishDate = soup.find('span', class_="sc-time").text

    # Combine all the paragraphs into a single text field
    article = ""
    for paragraph in paragraphs:
        article += paragraph.text + "\n"
        
        # Split the text into sentences using regex
    sentences = re.split('[.?!\n]', article)
    # Remove any empty or very short sentences
    sentences = [s for s in sentences if len(s) > 10]
    # Take the first 2-3 sentences as the brief description
    description = ' '.join(sentences[:3])

    # Check if the article already exists in the database
    article_exists = False
    articles = ref.order_by_child('Link To Article').equal_to(link).get()
    for key in articles:
        if articles[key]['Full Article'] == article:
            article_exists = True
            break

    # Push the data to the Firebase Realtime Database if the article doesn't already exist
    if not article_exists:
        ref.push().set({
            'Link To Article': link,
            'Image': image,
            'Title': title,
            'Description': description,
            'Author': author,
            'Publish Date': publishDate,
            'Full Article': article
        })
        print("Inserted article:", link)
        
def process_news(url):
    # Retrieve the page content
    driver.get(url['url'])
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "sc-list-item")))
    page_content = driver.page_source

    # Parse the page content using BeautifulSoup
    soup = BeautifulSoup(page_content, "html.parser")

    # Find all the list items on the page
    lists = soup.find_all("a", class_="sc-list-item")

    # Loop through each list item and start a thread to scrape and insert the article data
    threads = []
    for list in lists:
        link = list.get('href')
        t = threading.Thread(target=scrape_and_insert_article, args=(link, ref))
        threads.append(t)
        t.start()

    # Wait for all threads to finish before exiting the program
    for t in threads:
        t.join()

# Set up the Chrome webdriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

# Wait for the page to fully load before scraping the data
wait = WebDriverWait(driver, 10)

# Get a reference to the Firebase Realtime Database
ref = db.reference('/')

websites = [
            {
             'key': 1,
             'url': "https://farmnewsnow.com/more-blog/?sort=publish_date&categories=-1&offset=0&items_per_page=5&items_per_more_page=5&el_class=&length_of_article_summary=320&display_author_name=no&display_view=no&display_date=yes&layout=0&column_width=0&promo_position=default&target=&back_url=%2Fmore-blog%2F&back_page_name=More%2BBlog%2BPosts"
            },
            {
             'key': 2,
             'url': "https://farmnewsnow.com/more-blog/?sort=publish_date&categories=-1&offset=0&items_per_page=5&items_per_more_page=5&el_class=&length_of_article_summary=320&display_author_name=no&display_view=no&display_date=yes&layout=0&column_width=0&promo_position=default&target=&back_url=%2Fmore-blog%2F&back_page_name=More%2BBlog%2BPosts"
            }
            ]

for url in websites:
    process_news(url)

# Quit the Chrome webdriver
driver.quit()
