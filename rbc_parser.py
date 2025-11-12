import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import quote


class RBCNewsParser:
    BASE_URL = "https://www.rbc.ru"
    SEARCH_URL = f"{BASE_URL}/search"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_news(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        encoded_query = quote(query)
        search_url = f"{self.SEARCH_URL}/?query={encoded_query}"
        
        try:
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = self._extract_news_items(soup, limit)
            
            return news_items
        except requests.RequestException as e:
            raise Exception(f"Ошибка при запросе к сайту: {e}")
    
    def _extract_news_items(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, str]]:
        news_items = []
        
        search_results = soup.find_all('div', class_='search-item') or \
                        soup.find_all('a', class_='search-item__link') or \
                        soup.find_all('div', class_='item') or \
                        soup.find_all('article')
        
        if not search_results:
            search_results = soup.find_all('a', href=lambda x: x and '/news/' in x)
        
        for item in search_results[:limit * 2]:
            if len(news_items) >= limit:
                break
            
            news_data = self._parse_news_item(item)
            if news_data and news_data.get('title'):
                news_items.append(news_data)
        
        return news_items[:limit]
    
    def _parse_news_item(self, item) -> Dict[str, str]:
        news_data = {}
        
        title_elem = item.find('span', class_='search-item__text') or \
                    item.find('div', class_='item__title') or \
                    item.find('h3') or \
                    item.find('a', class_='search-item__link')
        
        if title_elem:
            news_data['title'] = title_elem.get_text(strip=True)
        elif item.name == 'a' and item.get('title'):
            news_data['title'] = item.get('title')
        elif item.get_text(strip=True):
            news_data['title'] = item.get_text(strip=True)[:200]
        
        link_elem = item if item.name == 'a' else item.find('a')
        if link_elem and link_elem.get('href'):
            href = link_elem.get('href')
            if href.startswith('/'):
                news_data['link'] = f"{self.BASE_URL}{href}"
            elif href.startswith('http'):
                news_data['link'] = href
            else:
                news_data['link'] = f"{self.BASE_URL}/{href}"
        
        date_elem = item.find('span', class_='search-item__date') or \
                    item.find('time') or \
                    item.find('div', class_='item__date')
        if date_elem:
            news_data['date'] = date_elem.get_text(strip=True)
        
        return news_data


def main():
    parser = RBCNewsParser()
    query = "Сбербанк"
    
    print(f"Поиск новостей по запросу: {query}\n")
    
    try:
        news_list = parser.search_news(query, limit=5)
        
        if not news_list:
            print("Новости не найдены.")
            return
        
        print(f"Найдено новостей: {len(news_list)}\n")
        print("=" * 80)
        
        for idx, news in enumerate(news_list, 1):
            print(f"\n{idx}. {news.get('title', 'Без названия')}")
            if news.get('link'):
                print(f"   Ссылка: {news['link']}")
            if news.get('date'):
                print(f"   Дата: {news['date']}")
            print("-" * 80)
    
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()


