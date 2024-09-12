import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from bs4 import BeautifulSoup

from webAccess import fetch_url_content, replace_img_with_filename

school = None

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
        
        # Extract content between "Set:" and "Items in this Set"
        start_index = None
        end_index = None
        for i, line in enumerate(lines):
            if line.startswith("Set:"):
                start_index = i
            if line.startswith("Items in this Set"):
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

def format_extracted_info(extracted_info):
    formatted_info = []
    skip_phrases = ["From Wizard101 Wiki", "Jump to:", "navigation", "search"]
    for line in extracted_info:
        if any(phrase in line for phrase in skip_phrases):
            continue
        # Clean up extra commas and percentage signs
        cleaned_line = line.replace(',', '').replace('%', '').replace('(25px-28Icon29_', '').replace('(18px-28Icon29_', '').replace('(50px-28Icon29', '').replace('(28Icon29_', '').replace('(89px-28General29_', '').replace('.png)', '').replace('_', ' ')
        formatted_info.append(cleaned_line[1:] if (cleaned_line and cleaned_line[0] == " ") else cleaned_line)
    return formatted_info

def process_bullet_point(base_url, bullet_point, bad_urls):
    set_name = bullet_point['text'].replace("Set:", "").strip()
    
    # Construct absolute URL for the hyperlink
    full_url = urllib.parse.urljoin(base_url, bullet_point['link'])
    print(f"Link: {full_url}")
    
    # Fetch and extract all information from the hyperlink
    text_info, soup = extract_information_from_url(full_url)
    
    if text_info:
        formatted_info = format_extracted_info(text_info)
        if set_name != "Fossil Avenger's Set": # fossil is exception, doesn't need to get checked
            set_school = formatted_info[formatted_info.index("Set Bonuses") - 1]
            if set_school != school and set_school != "Global": # remove set bonuses for other schools
                return None
        set_data = find_bonus(formatted_info, set_name)
        
        return set_data
    else:
        print(f"Failed to fetch content from {full_url}")
        bad_urls.append(full_url)
        return None

def rename_good_bonuses(bonuses):
    replacements = {
        "Resistance": "Resist",
        "Pip Chance": "Pip",
        "Max Health": "Health",
        "Armor Piercing": "Pierce",
        "Pip Conversion": "Pip Conserve",
        " Healing": "",
        "ShadPip": "Shadow Pip"
    }
    
    for i in range(len(bonuses)):
        for key in replacements:
            bonuses[i] = bonuses[i].replace(key, replacements[key])
            
    return bonuses

def clean_bonuses_str(bonuses_str):
    bonuses_str = bonuses_str.replace("Gain 1 Power Pip when you defeat an enemy once per Round (no PvP)", "") # don't need this
    bonuses_str = bonuses_str.replace(f"{school} ", "").replace("Global ", "") # remove good schools, then any school that appears should be removed
    return bonuses_str.replace("Shadow Pip Rating", "ShadPip") # special occasion so not treated as Shadow school stat

def remove_unwanted_bonuses(bonuses):
    bonuses_str = clean_bonuses_str(" ".join(bonuses))
    bonuses_in_tier = bonuses_str.replace(" +", "+").split("+") # each bonus starts with +, so separate each bonus
    if bonuses_in_tier and not bonuses_in_tier[0]: # removes blank start to list
        bonuses_in_tier = bonuses_in_tier[1:]
    
    all_schools = {"Death", "Fire", "Balance", "Myth", "Storm", "Ice", "Life", "Shadow"}
    
    j = 0
    while j < len(bonuses_in_tier):
        if ("Mana" in bonuses_in_tier[j]) or ("Item Card" in bonuses_in_tier[j]) or ("Movement Speed" in bonuses_in_tier[j]):
            bonuses_in_tier.pop(j)
            j -= 1
        else:
            words = bonuses_in_tier[j].split()
            for word in words:
                if word in all_schools:
                    bonuses_in_tier.pop(j)
                    j -= 1
                    break
        j += 1
    
    if not bonuses_in_tier:
        return "None"
    else:
        bonuses_in_tier = rename_good_bonuses(bonuses_in_tier)
    
    return ", ".join(bonuses_in_tier)

def find_bonus(formatted_info, set_name):
    
    set = {
        'Name': set_name,
        '2 Pieces': 'None',
        '3 Pieces': 'None',
        '4 Pieces': 'None',
        '5 Pieces': 'None',
        '6 Pieces': 'None',
        '7 Pieces': 'None',
        '8 Pieces': 'None',
        '9 Pieces': 'None',
        '10 Pieces': 'None'
    }
    
    for i in range(2, 11):
        try:
            j = formatted_info.index(f"Tier {i} Stats:") + 1
        except:
            try:
                j = formatted_info.index(f"Tier {i} Stats") + 1
            except:
                continue
        
        bonuses = []
        
        while (j < len(formatted_info)) and ("Tier " not in formatted_info[j]):
            if formatted_info[j]:
                bonuses.append(formatted_info[j])
            j += 1
        
        # remove bonuses that don't help
        set[f"{i} Pieces"] = remove_unwanted_bonuses(bonuses)
    
    return set

def get_set_bonuses(main_school):
    
    global school
    school = main_school
    
    base_url = "https://wiki.wizard101central.com"
    url = "https://wiki.wizard101central.com/wiki/Category:Sets"
    
    sets_data = []
    
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
                        sets_data.append(item_data)
                
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
    df = pd.DataFrame(sets_data).fillna(0)  # fill all empty values with 0
    df = df.sort_values(by = "Name", ascending = True).reset_index(drop=True)
    print(df)
    df.to_csv(f'Set_Bonuses\\{school}_Set_Bonuses.csv', index=False)
        
    return bad_urls
