import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import combinations_with_replacement

import pandas as pd
from bs4 import BeautifulSoup

from webAccess import fetch_url_content, replace_img_with_filename

shape = ""

# this needs to collect from the df (probably html?)
def get_jewel_effects(school, level):
    return [155, 11, 6, 550, 16, 10]

# def jewel_the_gear(df):
#     # Create new rows for each item with each variation
#     new_rows = []
#     for i, row in df.iterrows():
#         # original (unjeweled)
#         new_rows.append(row.to_dict())
        
#         # unlocked combinations
#         if any(row[col] != 0 for col in ['Unlocked Tear', 'Unlocked Circle', 'Unlocked Square', 'Unlocked Triangle']):
#             new_rows.extend(jewel_unlocked_sockets(row))
        
#         # locked combinations
#         if any(row[col] != 0 for col in ['Locked Tear', 'Locked Circle', 'Locked Square', 'Locked Triangle']):
#             new_rows.extend(jewel_locked_sockets(row))
    
#     return pd.DataFrame(new_rows)

# def jewel_unlocked_sockets(item):
#     # Define the conversions
#     conversions = {
#         'Unlocked Tear': ('Health', jewel_effects[0]),
#         'Unlocked Circle': [('Damage', jewel_effects[1]), ('Pierce', jewel_effects[2])],
#         'Unlocked Square': ('Health', jewel_effects[3]),
#         'Unlocked Triangle': [('Accuracy', jewel_effects[4]), ('Pips', jewel_effects[5])]
#     }
    
#     # Start with the base item, converting Tears and Squares
#     base_item = item.copy()
#     for col, (target, value) in [('Unlocked Tear', conversions['Unlocked Tear']), ('Unlocked Square', conversions['Unlocked Square'])]:
#         base_item[target] += value * base_item[col]
#         base_item[col] = 0

#     # List to hold all variants
#     variants = []

#     # Generate all unique combinations for Circles and Triangles
#     circle_combinations = list(combinations_with_replacement(conversions['Unlocked Circle'], item['Unlocked Circle']))
#     triangle_combinations = list(combinations_with_replacement(conversions['Unlocked Triangle'], item['Unlocked Triangle']))

#     # Create variants based on the combinations
#     for circle_combo in circle_combinations:
#         for triangle_combo in triangle_combinations:
#             variant = base_item.copy()
            
#             # Apply circle effects
#             for (effect, value), count in {(effect, value): circle_combo.count((effect, value)) for (effect, value) in set(circle_combo)}.items():
#                 variant[effect] += value * count
            
#             # Apply triangle effects
#             for (effect, value), count in {(effect, value): triangle_combo.count((effect, value)) for (effect, value) in set(triangle_combo)}.items():
#                 variant[effect] += value * count
            
#             # Reset conversion items to 0
#             for key in ['Unlocked Tear', 'Unlocked Circle', 'Unlocked Square', 'Unlocked Triangle']:
#                 variant[key] = 0
            
#             # Convert to dict and add Name
#             variant_dict = variant.to_dict()
#             variant_dict['Name'] = item['Name']  # Keep the original name for all variants
            
#             variants.append(variant_dict)
    
#     return variants

# def jewel_locked_sockets(item):
#     item["Unlocked Tear"] += item["Locked Tear"]
#     item["Unlocked Circle"] += item["Locked Circle"]
#     item["Unlocked Square"] += item["Locked Square"]
#     item["Unlocked Triangle"] += item["Locked Triangle"]
    
#     item["Locked Tear"] = 0
#     item["Locked Circle"] = 0
#     item["Locked Square"] = 0
#     item["Locked Triangle"] = 0
    
#     return jewel_unlocked_sockets(item)

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

def process_bullet_point(base_url, bullet_point):
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
        return None

# need to get level and effect
def find_bonus(formatted_info, item_name):
    
    bonus = {
        "Shape": shape,
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

def clean_jewel_df(df):
    return df.sort_values(by = ["Level", "Name"], ascending = [False, False]).reset_index(drop=True)

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

def only_own_school_170(df):
    
    # keep 170+ damage jewels school specific
    schools = ["(Death)", "(Fire)", "(Balance)", "(Myth)", "(Storm)", "(Ice)", "(Life)"]
    jewels = ["Onyx", "Ruby", "Citrine", "Peridot", "Amethyst", "Sapphire", "Jade"]

    # Iterate over the DataFrame and collect indices to drop
    indices_to_drop = []

    for index, row in df.iterrows():
        # Check if the last word in the 'Name' column matches any of the schools
        school_found = next((school for school in schools if school == row["Name"].split()[-1]), None)
        
        # if the jewel's effect is not for the jewel's school
        if school_found and jewels[schools.index(school_found)] not in row["Name"]:
            indices_to_drop.append(index)

    # Drop the collected indices from the DataFrame
    df.drop(indices_to_drop, inplace=True)
    
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

def objectively_best_jewels(df):

    df = keep_right_kind(df).reset_index(drop=True)
    
    df = only_own_school_170(df).reset_index(drop=True)
    
    df = best_at_level(df).reset_index(drop=True)
    
    return df

def collect_jewels():
    
    base_url = "https://wiki.wizard101central.com"

    jewels_data = []
    
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
                    futures = [executor.submit(process_bullet_point, base_url, bp) for bp in bullet_points]
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
    df = clean_jewel_df(df)
    print(df)
    df.to_csv(f'Jewels_All.csv', index=False)
    
    # objectively best jewels (for view sets)
    df = objectively_best_jewels(pd.read_csv("Jewels_All.csv"))
    print(df)
    df.to_csv(f'Jewels_Objectively_Best.csv', index=False)
    
    return df
