import os
import urllib.parse
from urllib.request import Request, urlopen


def fetch_url_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        if url.startswith('http'):
            response = Request(url, headers=headers)
        else:
            full_url = urllib.parse.urljoin('https://wiki.wizard101central.com', url)
            response = Request(full_url, headers=headers)
            
        return urlopen(response).read()
    except Exception as err:
        print(f"Error occurred: {err}\nRetrying {url}")
        return fetch_url_content(url)
    
    return None

def replace_img_with_filename(soup):
    for img in soup.find_all('img'):
        if 'src' in img.attrs:
            img_url = img['src']
            img_filename = os.path.basename(img_url)
            img.replace_with(f'({img_filename})')
    return soup
