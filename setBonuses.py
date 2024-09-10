import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import combinations_with_replacement

import pandas as pd
from bs4 import BeautifulSoup

from webAccess import fetch_url_content, replace_img_with_filename


def extract_bullet_points_from_html(html_content):
    if html_content is None:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    bullet_points = []

    # Find all list items (<li>) that contain the text "Set:"
    for li in soup.find_all('li'):
        if li.text.strip().startswith("Set:"):
            # Check if the list item contains a hyperlink (<a> tag)
            a_tag = li.find('a', href=True)
            if a_tag:
                bullet_points.append({
                    'text': li.text.strip(),
                    'link': a_tag['href']
                })
    
    return bullet_points

def extract_information_from_url(url):
    html_content = fetch_url_content(url)
    if html_content:
        # Parse HTML content and replace <img> tags with filenames
        soup = BeautifulSoup(html_content, 'html.parser')
        soup = replace_img_with_filename(soup)
        
        # Extract all visible text from the modified HTML content
        text_content = soup.get_text(separator='\n', strip=True)
        
        lines = text_content.splitlines()
        
        # Extract content between "Set:" and "Male Image"
        start_index = None
        end_index = None
        for i, line in enumerate(lines):
            if line.startswith("Set:"):
                start_index = i
            if line.startswith("Male Image"):
                end_index = i
                break
        
        if start_index is not None and end_index is not None:
            return lines[start_index:end_index], soup
        elif start_index is not None:
            return lines[start_index:], soup
        else:
            return [], soup
    else:
        return [], None, None

def find_next_page_link(soup):
    # Look for the "(next page)" link
    next_page_link = soup.find('a', string='next page')
    if next_page_link and 'href' in next_page_link.attrs:
        return next_page_link['href']
    return None

# fix
def format_extracted_info(extracted_info):
    formatted_info = []
    skip_phrases = ["From Wizard101 Wiki", "Jump to:", "navigation", "search"]
    for line in extracted_info:
        if any(phrase in line for phrase in skip_phrases):
            continue
        # Clean up extra commas and percentage signs
        cleaned_line = line.replace(',', '').replace('%', '').replace('(25px-28Icon29_', '').replace('(18px-28Icon29_', '').replace('(50px-28Icon29', '').replace('(28Icon29_', '').replace('.png)', '').replace('_', ' ')
        formatted_info.append(cleaned_line)
    return formatted_info

# fix
def process_bullet_point(base_url, bullet_point, bad_urls):
    item_name = bullet_point['text'].replace("Set:", "").strip()
    
    # Construct absolute URL for the hyperlink
    full_url = urllib.parse.urljoin(base_url, bullet_point['link'])
    print(f"Link: {full_url}")
    
    # Fetch and extract all information from the hyperlink
    text_info, soup = extract_information_from_url(full_url)
    
    if text_info:
        formatted_info = format_extracted_info(text_info)
        print(formatted_info)
    #     bonuses = find_bonus(formatted_info, item_name)
    #     jewel_data = {
    #         'Name': item_name
    #     }
    #     jewel_data.update(bonuses)
        
    #     return jewel_data
    # else:
    #     print(f"Failed to fetch content from {full_url}")
    #     bad_urls.append(full_url)
    #     return None

# fix
def find_bonus(formatted_info, item_name):
    
    bonus = {
        "Level": 1,
        "Effect": "None"
    }
    
    for i in range(len(formatted_info)):
        if "(Level " in formatted_info[i]:
            bonus["Level"] = int(formatted_info[i].split("(Level ")[1].split("+")[0])
        elif formatted_info[i] == "Level":
            bonus["Level"] = 1 if formatted_info[i + 1] == "Any" else int(formatted_info[i + 1].replace("+", ""))
        elif formatted_info[i] == "Effect":
            bonus["Effect"] = " ".join(formatted_info[i + 1:])
            return bonus

def sort_set_bonuses_df(df):
    return df.sort_values(by = "Name", ascending = True).reset_index(drop=True)

def get_set_bonuses():
    
    base_url = "https://wiki.wizard101central.com"
    url = "https://wiki.wizard101central.com/wiki/Category:Sets"
    
    items_data = []
    
    bad_urls = []

    while url:
        # Fetch content from the URL
        html_content = fetch_url_content(url)

        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Extract bullet points with links from the HTML content
            bullet_points = extract_bullet_points_from_html(html_content)

            with ThreadPoolExecutor(max_workers=85) as executor:
                futures = [executor.submit(process_bullet_point, base_url, bp, bad_urls) for bp in bullet_points]
                for future in as_completed(futures):
                    item_data = future.result()
                    if item_data:
                        items_data.append(item_data)
                
            # Find the "(next page)" link
            next_page_link = find_next_page_link(soup)
            if next_page_link:
                url = urllib.parse.urljoin(base_url, next_page_link)
            else:
                url = None
        else:
            print("Failed to fetch content from the URL.")
            break

    # move all items to dataframe
    df = pd.DataFrame(items_data).fillna(0)  # fill all empty values with 0
    df = sort_set_bonuses_df(df)
    print(df)
    df.to_csv(f'Set_Bonuses.csv', index=False)
        
    return bad_urls
