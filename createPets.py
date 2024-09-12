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

    # Find all list items (<li>) that contain the text "Pet:"
    for li in soup.find_all('li'):
        if li.text.strip().startswith("Pet:"):
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
        
        # Check if "-100% Max" is in the text content, if so, skip processing
        if "-100% Max" in text_content:
            return ["-100% Max"], None, soup
        
        lines = text_content.splitlines()
        
        # Extract content between "Pet:" and "Documentation on how to edit this page"
        start_index = None
        end_index = None
        for i, line in enumerate(lines):
            if line.startswith("Pet:"):
                start_index = i
            if line.startswith("Documentation on how to edit this page"):
                end_index = i
                break
        
        if start_index is not None and end_index is not None:
            return lines[start_index:end_index], soup
        elif start_index is not None:
            return lines[start_index:], soup
        else:
            return [], soup
    else:
        return [], None

def find_next_page_link(soup):
    # Look for the "(next page)" link
    next_page_link = soup.find('a', string='next page')
    if next_page_link and 'href' in next_page_link.attrs:
        return next_page_link['href']
    return None

def format_extracted_info(extracted_info):
    formatted_info = []
    skip_phrases = ["From Wizard101 Wiki", "Jump to:", "navigation", "search", f"(50px-%28Icon%29_Pet.png)"]
    for line in extracted_info:
        if any(phrase in line for phrase in skip_phrases):
            continue
        # Clean up extra commas and percentage signs
        cleaned_line = line.replace(',', '').replace('%', '').replace("(15px-%28Icon%29_M", "").replace("(21px-%28Icon%29_", "").replace("(21px-28Icon29", "").replace('(25px-28Icon29_', '').replace('(18px-28Icon29_', '').replace('.png)', '').replace('_', ' ')
        if len(cleaned_line) > 0:
            cleaned_line = cleaned_line[1:] if cleaned_line[0] == " " else cleaned_line
            formatted_info.append(cleaned_line)
    return formatted_info

def parse_wiki_error_gear(item_name, bonuses, parts):
    # unique cases due to wiki error
    if item_name == "Fill in here with name of bad wiki item":
        return bonuses
    else:
        print(f"Error on {item_name}")
        value = int(parts[0][1:]) # should throw an error and end execution
        return value

def parse_bonuses(info_lines, item_name):
    bonuses = {
        'Max Health': 0,
        f'{school} Damage': 0,
        'Global Damage': 0,
        f'{school} Resistance': 0,
        'Global Resistance': 0,
        f'{school} Accuracy': 0,
        'Global Accuracy': 0,
        'Power Pip Chance': 0,
        f'{school} Critical Rating': 0,
        'Global Critical Rating': 0,
        f'{school} Critical Block Rating': 0,
        'Global Critical Block Rating': 0,
        f'{school} Armor Piercing': 0,
        'Global Armor Piercing': 0,
        'Stun Resistance': 0,
        'Incoming Healing': 0,
        'Outgoing Healing': 0,
        f'{school} Pip Conversion Rating': 0,
        'Global Pip Conversion Rating': 0,
        'Shadow Pip Rating': 0,
        'Archmastery Rating': 0
    }
    
    return bonuses

def process_bullet_point(base_url, bullet_point, bad_urls):
    item_name = bullet_point['text'].replace("Pet:", "").strip()
    
    # Construct absolute URL for the hyperlink
    full_url = urllib.parse.urljoin(base_url, bullet_point['link'])
    print(f"Link: {full_url}")
    
    # Fetch and extract all information from the hyperlink
    text_info, soup = extract_information_from_url(full_url)
    
    if "-100% Max" in text_info:
        return None
    elif text_info:
        formatted_info = format_extracted_info(text_info)
        bonuses = parse_bonuses(formatted_info, item_name)
        item_data = {
            'Name': item_name,
        }
        item_data.update(bonuses)
        
        item_data['Gear Set'] = formatted_info[formatted_info.index("Set") + 1] if "Set" in formatted_info else "None"
        
        return item_data
    else:
        print(f"Failed to fetch content from {full_url}")
        bad_urls.append(full_url)
        return None

def combine_school_and_global_stats(df):
    df["Damage"] = df[f"{school} Damage"] + df["Global Damage"]
    df["Accuracy"] = df[f"{school} Accuracy"] + df["Global Accuracy"]
    df["Critical"] = df[f"{school} Critical Rating"] + df["Global Critical Rating"]
    df["Pierce"] = df[f"{school} Armor Piercing"] + df["Global Armor Piercing"]
    df["Pip Conserve"] = df[f"{school} Pip Conversion Rating"] + df["Global Pip Conversion Rating"]

def only_show_necessary_cols(df):
    df.rename(columns={'Max Health': 'Health', 'Global Resistance': 'Resist', 'Power Pip Chance': 'Power Pip', 'Global Critical Block Rating': 'Critical Block', 'Stun Resistance': 'Stun Resist', 'Incoming Healing': 'Incoming', 'Outgoing Healing': 'Outgoing', 'Shadow Pip Rating': 'Shadow Pip', 'Archmastery Rating': 'Archmastery'}, inplace=True)
    df["Level"] = 1
    df["Owned"] = False
    
    return df[['Name', 'Level', 'Health', 'Damage', 'Resist', 'Accuracy', 'Power Pip', 'Critical', 'Critical Block', 'Pierce', 'Stun Resist', 'Incoming', 'Outgoing', 'Pip Conserve', 'Shadow Pip', 'Archmastery', 'Owned', 'Gear Set']]

def clean_pets_df(df):
    combine_school_and_global_stats(df)
    df = only_show_necessary_cols(df)
    return df

def remove_normal_pets(df):
    # List of columns to check
    stats = ['Health', 'Damage', 'Resist', 'Accuracy', 'Power Pip', 'Critical', 'Critical Block', 'Pierce', 'Stun Resist', 'Incoming', 'Outgoing', 'Pip Conserve', 'Shadow Pip', 'Archmastery']

    # Condition to check if all specified columns are 0
    condition_all_zero = (df[stats] == 0).all(axis=1)

    # Condition to check if either 'd' or 'e' is True
    condition_d_or_e_true = df['Owned'] | (df['Gear Set'] != "None")
    
    # Combine conditions: keep rows if not all zero or if 'd' or 'e' is True
    df = df[~condition_all_zero | condition_d_or_e_true].reset_index(drop = True)
    
    # sort by gear set
    df = df.sort_values(by = "Gear Set", ascending = True).reset_index(drop=True)
    
    # add default pet (not a gear set pet)
    default_pet = pd.DataFrame([{"Name": "Other", "Level": 1, "Health": 0, "Damage": 0, "Resist": 0, "Accuracy": 0, "Power Pip": 0, "Critical": 0, "Critical Block": 0, "Pierce": 0, "Stun Resist": 0, "Incoming": 0, "Outgoing": 0, "Pip Conserve": 0, "Shadow Pip": 0, "Archmastery": 0, "Owned": False, "Gear Set": "None"}])

    df = df._append(default_pet, ignore_index = True)
    
    return df

def create_pet_variants(df):
    
    # personal variations of a "perfect pet" (personal opinion)
    variations = [
        {"Name": "Max Damage", "Damage": 33, "Resist": 0, "Accuracy": 0, "Pierce": 0},
        {"Name": "Triple Double", "Damage": 25, "Resist": 17, "Accuracy": 0, "Pierce": 0},
        {"Name": "Max Resist", "Damage": 0, "Resist": 21, "Accuracy": 0, "Pierce": 0},
        {"Name": "3 Damage, 2 Pierce, Resist", "Damage": 22, "Resist": 10, "Accuracy": 0, "Pierce": 5},
        {"Name": "3 Damage, 2 Pierce", "Damage": 25, "Resist": 0, "Accuracy": 0, "Pierce": 6},
        {"Name": "Triple Double, Accuracy", "Damage": 22, "Resist": 15, "Accuracy": 10, "Pierce": 0},
        {"Name": "Triple Double, Pierce", "Damage": 22, "Resist": 15, "Accuracy": 0, "Pierce": 3},
        {"Name": "3 Damage, 2 Pierce, Accuracy", "Damage": 22, "Resist": 0, "Accuracy": 10, "Pierce": 5},
        {"Name": "3 Damage, Resist, Pierce, Accuracy", "Damage": 22, "Resist": 10, "Accuracy": 10, "Pierce": 3},
        {"Name": "3 Damage, Resist, Pierce", "Damage": 25, "Resist": 11, "Accuracy": 0, "Pierce": 4},
        {"Name": "3 Damage, Resist, Accuracy", "Damage": 25, "Resist": 11, "Accuracy": 10, "Pierce": 0},
        {"Name": "3 Damage, Pierce, Accuracy", "Damage": 25, "Resist": 0, "Accuracy": 10, "Pierce": 4}
    ]
    
    # Create new rows for each item with each variation
    new_rows = []
    for i, row in df.iterrows():
        for variation in variations:
            new_row = row.copy()
            new_row['Damage'] += variation['Damage']
            new_row['Resist'] += variation['Resist']
            new_row['Accuracy'] += variation['Accuracy']
            new_row["Pierce"] += variation["Pierce"]
            new_row['Name'] = f"{row['Name']} ({variation['Name']})"  # Rename item to indicate variation
            new_rows.append(new_row)

    # Create a new DataFrame with the new rows
    new_df = pd.DataFrame(new_rows)
    
    new_df = new_df.sort_values(by = ["Damage", "Resist", "Health", "Pierce", "Critical", "Accuracy", "Power Pip", "Critical Block", "Shadow Pip", "Archmastery", "Incoming", "Outgoing", "Pip Conserve", "Stun Resist", "Owned"],
                        ascending = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]).reset_index(drop=True)
    
    return new_df

def create_pets(main_school):
    
    global school
    school = main_school
    
    base_url = "https://wiki.wizard101central.com"
    url = "https://wiki.wizard101central.com/wiki/Category:Pets"
    
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
    df = clean_pets_df(df)
    df = remove_normal_pets(df)
    df = create_pet_variants(df)
    print(df)
    df.to_csv(f'Gear\\{school}_Gear\\{school}_Pets.csv', index=False)
        
    return bad_urls
