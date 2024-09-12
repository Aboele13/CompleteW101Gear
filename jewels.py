import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from bs4 import BeautifulSoup

from webAccess import fetch_url_content, replace_img_with_filename

shape = ""

def extract_bullet_points_from_html(html_content):
    if html_content is None:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    bullet_points = []

    # Find all list items (<li>) that contain the text "Jewel:"
    for li in soup.find_all('li'):
        if li.text.strip().startswith("Jewel:"):
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
        
        # Extract content between "Jewel:" and "Acquisition Sources"
        start_index = None
        end_index = None
        for i, line in enumerate(lines):
            if line.startswith("Jewel:"):
                start_index = i
            if line.startswith("Acquisition Source") or line.startswith("Sell Price") or "(10px-%28Icon%29_Counter.png)" in line or line.startswith("Documentation on how"):
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
        cleaned_line = line.replace(',', '').replace('%', '').replace('(25px-28Icon29_', '').replace('(18px-28Icon29_', '').replace('(50px-28Icon29', '').replace('(28Icon29_', '').replace('.png)', '').replace('_', ' ')
        formatted_info.append(cleaned_line)
    return formatted_info

def process_bullet_point(base_url, bullet_point, bad_urls):
    item_name = bullet_point['text'].replace("Jewel:", "").strip()
    
    # Construct absolute URL for the hyperlink
    full_url = urllib.parse.urljoin(base_url, bullet_point['link'])
    print(f"Link: {full_url}")
    
    # Fetch and extract all information from the hyperlink
    text_info, soup = extract_information_from_url(full_url)
    
    if text_info:
        formatted_info = format_extracted_info(text_info)
        bonuses = find_bonus(formatted_info, item_name)
        jewel_data = {
            'Name': item_name
        }
        jewel_data.update(bonuses)
        
        return jewel_data
    else:
        print(f"Failed to fetch content from {full_url}")
        bad_urls.append(full_url)
        return None

# need to get level and effect
def find_bonus(formatted_info, item_name):
    
    bonus = {
        "Shape": shape,
        "Level": 1,
        "School": "Any",
        "Effect": "None"
    }
    
    for i in range(len(formatted_info)):
        if "(Level " in formatted_info[i]:
            bonus["Level"] = int(formatted_info[i].split("(Level ")[1].split("+")[0])
        elif formatted_info[i] == "Level":
            bonus["Level"] = 1 if formatted_info[i + 1] == "Any" else int(formatted_info[i + 1].replace("+", ""))
        elif formatted_info[i] == "School":
            bonus["School"] = formatted_info[i + 1]
        elif formatted_info[i] == "Effect":
            bonus["Effect"] = " ".join(formatted_info[i + 1:])
            return bonus

def keep_right_kind(df):
    
    # only keep jewels I would ideally use
    good_jewels = "|".join(["Health", "Damage", "Armor Piercing", "Global Flat Resistance", "Accuracy", "Power Pip", "Epic Item Card", "Colossal Item Card", "Archmastery"])
    df = df[df["Effect"].str.contains(good_jewels)]
    
    # only keep archmastery under level 50
    df = df[~((df["Effect"].str.contains("Archmastery")) & (df["Level"] >= 50))]
    
    # only keep school specific hitting jewels (stronger)
    ignore_global_jewels = "|".join(["Global Flat Damage", "Global Armor Piercing", "Global Accuracy", "Shadow"])
    df = df[~df["Effect"].str.contains(ignore_global_jewels)]
    
    # remove "Health" item cards
    return df[~df["Effect"].str.contains("Health Item Card")]

# everything has a space in front because it won't be the first word in jewel name
def only_own_school(df, school):
    
    # jewels to keep
    good_jewels = [" Opal"]
    
    if school == "Death":
        good_jewels.append(" Onyx")
    elif school == "Fire":
        good_jewels.append(" Ruby")
    elif school == "Balance":
        good_jewels.append(" Citrine")
    elif school == "Myth":
        good_jewels.append(" Peridot")
    elif school == "Storm":
        good_jewels.append(" Amethyst")
    elif school == "Ice":
        good_jewels.append(" Sapphire")
    elif school == "Life":
        good_jewels.append(" Jade")
    
    # only keep jewels that help this school
    df = df[df["Name"].str.contains("|".join(good_jewels))]
    
    return df

def best_at_level(df):

    # Iterate through the DataFrame
    i = 0
    while i < (len(df) - 1):
        name_one = df.loc[i, 'Name']
        name_one_value = ''.join(re.findall(r'[0-9]', name_one))
        name_one = ''.join(re.findall(r'[^0-9]', name_one))
    
        name_two = df.loc[i + 1, 'Name']
        name_two_value = ''.join(re.findall(r'[0-9]', name_two))
        name_two = ''.join(re.findall(r'[^0-9]', name_two))
        
        if name_one == name_two and name_one_value != '' and name_two_value != '':
            if int(name_one_value) > int(name_two_value):
                df.drop([i + 1], inplace=True)
            else:
                df.drop([i], inplace=True)
            df.reset_index(drop=True, inplace=True)
            i -= 1
        i += 1
    
    return df

def objectively_best_jewels(df, school):

    df = keep_right_kind(df).reset_index(drop=True)
    
    df = only_own_school(df, school).reset_index(drop=True)
    
    df = best_at_level(df).reset_index(drop=True)
    
    return df

def create_school_jewels(schools):
    
    # all jewels for each school (for create set)
    for school in schools:
        df = pd.read_csv(f'Jewels\\All_Jewels.csv')
        df = df[df["School"].isin([school, "Any"])]
        df = df.drop(columns=['School'])
        df.to_csv(f'Jewels\\{school}_Jewels\\All_{school}_Jewels.csv', index=False)
        
    # only objectively best for each school (for view sets)
    for school in schools:
        df = pd.read_csv(f'Jewels\\{school}_Jewels\\All_{school}_Jewels.csv')
        df = objectively_best_jewels(df, school)
        df.to_csv(f'Jewels\\{school}_Jewels\\Objectively_Best_{school}_Jewels.csv', index=False)


def collect_jewels(schools):
    
    base_url = "https://wiki.wizard101central.com"

    jewels_data = []
    
    bad_urls = []
    
    # need to update if they add more jewel shapes
    good_jewel_shapes = ["Tear", "Circle", "Square", "Triangle"]
    for curr_shape in good_jewel_shapes:
        
        global shape
        shape = curr_shape
        
        url = f"https://wiki.wizard101central.com/wiki/Category:{shape}_Shaped_Jewels"
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
                        jewel_data = future.result()
                        if jewel_data:
                            jewels_data.append(jewel_data)
    
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
    
    # all jewels together (for create set)
    df = pd.DataFrame(jewels_data).fillna(0)  # fill all empty values with 0
    df = df.sort_values(by = ["Level", "School", "Name"], ascending = [False, True, False]).reset_index(drop=True) # sort it
    print(df)
    df.to_csv(f'Jewels\\All_Jewels.csv', index=False)
    
    # create dataframes for each school
    create_school_jewels(schools)
    
    return bad_urls

