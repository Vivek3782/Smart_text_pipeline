from django.core.management.base import BaseCommand
from scraper.models import ScrapedData
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

class Command(BaseCommand):
    help = 'Scrapes IMDB movie reviews and saves title and text separately'

    def handle(self, *args, **kwargs):
        chrome_options = Options()
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            url = "https://www.imdb.com/title/tt1375666/reviews"
            print(f"Navigating to: {url}")
            driver.get(url)
            time.sleep(5)

            # Handle spoiler buttons and show more buttons
            self.handle_dynamic_content(driver)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Try different approaches to find review containers
            reviews_data = self.extract_reviews_with_titles(soup, driver)
            
            count = 0
            for review_data in reviews_data:
                title = review_data.get('title', '').strip()
                text = review_data.get('text', '').strip()
                
                if text and len(text) > 50:  # Only save if there's substantial text
                    ScrapedData.objects.create(
                        source_url=url,
                        review_title=title,
                        raw_text=text
                    )
                    count += 1
                    print(f"Saved review {count}:")
                    print(f"  Title: {title[:100]}...")
                    print(f"  Text: {text[:100]}...")
                    print("-" * 50)

            self.stdout.write(self.style.SUCCESS(f'Successfully scraped {count} reviews with titles.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error occurred: {str(e)}'))
            import traceback
            traceback.print_exc()
        finally:
            driver.quit()

    def handle_dynamic_content(self, driver):
        """Handle spoiler buttons and dynamic content loading"""
        try:
            # Click spoiler buttons
            spoiler_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'spoiler') or contains(@class, 'spoiler')]")
            
            for button in spoiler_buttons:
                try:
                    if button.is_displayed():
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(1)
                except:
                    pass

            # Click "Show more" buttons
            show_more_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Show more') or contains(@class, 'show-more')]")
            
            for button in show_more_buttons:
                try:
                    if button.is_displayed():
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(1)
                except:
                    pass

            # Scroll to load more content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        except Exception as e:
            print(f"Error handling dynamic content: {e}")

    def extract_reviews_with_titles(self, soup, driver):
        """Extract reviews with separate title and text"""
        reviews_data = []
        
        # Method 1: Try modern IMDB structure
        review_containers = soup.find_all('div', {'data-testid': 'review-card'})
        if not review_containers:
            review_containers = soup.find_all('div', class_='review-container')
        if not review_containers:
            review_containers = soup.find_all('div', class_='lister-item')
        
        print(f"Found {len(review_containers)} review containers")
        
        for container in review_containers:
            try:
                # Extract title - try multiple selectors
                title = self.extract_title(container)
                
                # Extract review text - try multiple selectors
                text = self.extract_text(container)
                
                if title or text:
                    reviews_data.append({
                        'title': title,
                        'text': text
                    })
                    
            except Exception as e:
                print(f"Error extracting from container: {e}")
                continue
        
        # Method 2: If no structured containers found, try alternative approach
        if not reviews_data:
            reviews_data = self.extract_reviews_alternative(soup)
        
        return reviews_data

    def extract_title(self, container):
        """Extract review title from container"""
        title_selectors = [
            'a.title',
            'h3 a',
            'div[data-testid="review-title"]',
            '.review-title',
            '.titleReviewBarItem .titleReviewBarSubItem .title',
            'a[href*="review"]',
            '.ipc-title__text',
            'h4 a'
        ]
        
        for selector in title_selectors:
            try:
                if selector.startswith('.') or selector.startswith('['):
                    title_elem = container.select_one(selector)
                else:
                    title_elem = container.find(selector.split()[0], class_=selector.split('.')[1] if '.' in selector else None)
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 5:
                        return title
            except:
                continue
        
        return ""

    def extract_text(self, container):
        """Extract review text from container"""
        text_selectors = [
            'div.text.show-more__control',
            'div[data-testid="review-summary"]',
            'div[data-testid="review-text"]',
            '.review-text',
            '.content .text',
            'div.content',
            '.lister-item-content .text',
            'div[class*="review-text"]',
            '.ipc-html-content-inner-div'
        ]
        
        for selector in text_selectors:
            try:
                if selector.startswith('.') or selector.startswith('['):
                    text_elem = container.select_one(selector)
                else:
                    text_elem = container.find('div', class_=selector.replace('div.', ''))
                
                if text_elem:
                    text = text_elem.get_text(strip=True)
                    if text and len(text) > 50:
                        return text
            except:
                continue
        
        # Fallback: get all text from container and try to identify review content
        all_text = container.get_text(strip=True)
        if len(all_text) > 100:
            # Try to remove non-review content (ratings, dates, etc.)
            lines = all_text.split('\n')
            substantial_lines = [line.strip() for line in lines if len(line.strip()) > 50]
            if substantial_lines:
                return ' '.join(substantial_lines)
        
        return ""

    def extract_reviews_alternative(self, soup):
        """Alternative method if structured containers not found"""
        reviews_data = []
        
        # Look for title links and nearby text
        title_links = soup.find_all('a', href=lambda x: x and 'review' in x)
        
        for link in title_links:
            try:
                title = link.get_text(strip=True)
                
                # Look for review text near the title
                parent = link.parent
                for _ in range(3):  # Go up 3 levels to find review container
                    if parent:
                        text_divs = parent.find_all('div')
                        for div in text_divs:
                            text = div.get_text(strip=True)
                            if len(text) > 100 and text != title:
                                reviews_data.append({
                                    'title': title,
                                    'text': text
                                })
                                break
                        if reviews_data and reviews_data[-1]['title'] == title:
                            break
                        parent = parent.parent
                    else:
                        break
                        
            except Exception as e:
                continue
        
        return reviews_data