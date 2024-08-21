import os
import urllib.parse

import requests


def fetch_url_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        if url.startswith('http'):
            response = requests.get(url, headers=headers)
        else:
            full_url = urllib.parse.urljoin('https://wiki.wizard101central.com', url)
            response = requests.get(full_url, headers=headers)
            
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        return response.text
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    except Exception as err:
        print(f"Other error occurred: {err}")
    
    return None

def replace_img_with_filename(soup):
    for img in soup.find_all('img'):
        if 'src' in img.attrs:
            img_url = img['src']
            img_filename = os.path.basename(img_url)
            img.replace_with(f'({img_filename})')
    return soup