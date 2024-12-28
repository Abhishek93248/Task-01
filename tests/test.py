import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import requests
import os

driver = webdriver.Remote(
            command_executor="https://hub.browserstack.com/wd/hub"
        )

driver.get("https://elpais.com")

try:
    cookie_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
    )
    cookie_button.click()
except:
    print("No cookie consent found or already accepted")

try:
    opinion_link = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'https://elpais.com/opinion/')]"))
    )
    opinion_link.click()
except Exception as e:
    print(f"Error clicking Opinion link: {e}")

articles = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.XPATH, "//article[@data-word]"))
)

os.makedirs('article_images', exist_ok=True)

def get_article_details(article, index):
    """Extract details from the articles"""
    try:

        link = article.find_element(By.XPATH, ".//h2/a").get_attribute("href")
        driver.execute_script(f"window.open('{link}');")
        driver.switch_to.window(driver.window_handles[-1])
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )

        try:
            title_element = driver.find_element(By.TAG_NAME, "h1")
            title = title_element.text.strip() if title_element else "No title found"
            print(f"Title: {title}")
        except Exception as e:
            title="N/A"
            print(f"Error extracting title: {e}")

        try:
            content_element = driver.find_element(By.TAG_NAME, "h2")
            content = content_element.text.strip() if content_element else "No content found"
            print(f"Content: {content[:100]}...")
        except Exception as e:
            content = "N/A"
            print(f"Error extracting content: {e}")
        time.sleep(5)
        try:
            image_tag = driver.find_element(By.CSS_SELECTOR, "img._re.a_m-h")
            image_url = image_tag.get_attribute("src")
            if image_url:
                response = requests.get(image_url)
                if response.status_code == 200:
                    with open(f'article_images/article_{index}_cover.jpg', 'wb') as f:
                        f.write(response.content)
                    print(f"Cover image saved: article_{index}_cover.jpg")
            else:
                raise Exception("No image found")
        except Exception as e:
            print(f"No image found {index}: {e}")

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        return {
            'title': title,
            'content': content
        }
    except Exception as e:
        print(f"Error processing article {index}: {e}")
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        return None

article_data = []
for i, article in enumerate(articles[:5], 1):  
    print(f"\nProcessing article {i}...")
    article_info = get_article_details(article, i)
    if article_info:
        print(f"\nArticle {i}:")
        print("Original Title:", article_info['title'])
        print("Content Preview:", article_info['content'][:200], "...\n")
        article_data.append(article_info)

print("\nTranslating titles...")
url = "https://rapid-translate-multi-traduction.p.rapidapi.com/t"
translated_titles = []
for article in article_data:
    try:

        payload = {
	"from": "es",
	"to": "en",
	"q": article['title']
    }
        headers = {
	"x-rapidapi-key": "",
	"x-rapidapi-host": "rapid-translate-multi-traduction.p.rapidapi.com",
	"Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        
        translated_title = response.json()[0]
        translated_titles.append(translated_title)
        print(f"Original: {article['title']}")
        print(f"Translated: {translated_title}\n")
        time.sleep(1)  
    except Exception as e:
        print(f"Translation error: {e}")
        translated_titles.append("Translation failed")

print("\nAnalyzing word frequency in translated titles...")
word_counts = {}
for title in translated_titles:
    words = title.lower().split()
    for word in words:
        if len(word) > 3: 
            word_counts[word] = word_counts.get(word, 0) + 1

repeated_words = {word: count for word, count in word_counts.items() if count > 2}

if repeated_words:
    print("\nWords appearing more than twice:")
    for word, count in repeated_words.items():
        print(f"'{word}' appears {count} times")
else:
    print("No words appear more than twice")

driver.quit()





