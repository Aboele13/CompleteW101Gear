import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from bs4 import BeautifulSoup

import findItemSource
from webAccess import fetch_url_content, replace_img_with_filename

school = None

def extract_bullet_points_from_html(html_content):
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    bullet_points = []

    # Find all list items (<li>) that contain the text "Mount:"
    for li in soup.find_all('li'):
        if li.text.strip().startswith("Mount:"):
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
            return ["-100% Max"], None
        
        lines = text_content.splitlines()
        
        # Extract content between "Mount:" and "Documentation on how to edit this page"
        start_index = None
        end_index = None
        for i, line in enumerate(lines):
            if line.startswith("Mount:"):
                start_index = i
            if line.startswith("Documentation on how to edit this page"):
                end_index = i
                break
        
        if start_index and end_index:
            return lines[start_index:end_index], soup
        elif start_index:
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
    skip_phrases = ["From Wizard101 Wiki", "Jump to:", "navigation", "search", f"(50px-%28Icon%29_Mount.png)"]
    for line in extracted_info:
        if any(phrase in line for phrase in skip_phrases):
            continue
        # Clean up extra commas and percentage signs
        cleaned_line = line.replace(',', '').replace('%', '').replace("(15px-%28Icon%29_M", "").replace("(21px-%28Icon%29_", "").replace("(21px-28Icon29", "").replace('(25px-28Icon29_', '').replace('(18px-28Icon29_', '').replace('(15px-28Icon29', '').replace("(328px-28Item29", "").replace("(28Item29", "").replace('.png)', '').replace('_', ' ')
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

def parse_bonuses(info_lines):
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
        
    capture = False
    
    for i, line in enumerate(info_lines):
        if line.startswith("Stat Boost"):
            capture = True
        elif capture:
            if line == 'View of the Mount in use':
                if info_lines[i - 2] == "N/A":
                    return bonuses
                stat = []
                j = i - 2
                while j >= 0:
                    stat.insert(0, info_lines[j])
                    if info_lines[j].startswith("+"):
                        value = int(stat[0][1:])
                        category = " ".join(stat[1:])
                        if category in bonuses:
                            bonuses[category] = int(value)
                            break
                    j -= 1
    
    return bonuses

def process_bullet_point(base_url, bullet_point, bad_urls):
    item_name = bullet_point['text'].replace("Mount:", "").strip()
    
    # Construct absolute URL for the hyperlink
    full_url = urllib.parse.urljoin(base_url, bullet_point['link'])
    print(f"Link: {full_url}")
    
    # Fetch and extract all information from the hyperlink
    text_info, soup = extract_information_from_url(full_url)
    
    if ["-100% Max"] == text_info:
        return None
    if "Permanent" not in text_info:
        return None
    elif text_info:
        formatted_info = format_extracted_info(text_info)
        bonuses = parse_bonuses(formatted_info)
        item_data = {
            'Name': item_name,
        }
        item_data.update(bonuses)
        
        # set the item's source
        item_data['Source'] = findItemSource.get_item_source(item_name, formatted_info, True)
        
        # set the item's gear set (or None if none)
        for i in range(len(formatted_info) - 1):
            if formatted_info[i] == "Set":
                item_data['Gear Set'] = formatted_info[i + 1]
                break
            
        if "Gear Set" not in item_data:
            item_data['Gear Set'] = "None"
        
        return item_data
    else:
        print(f"Failed to fetch content from {full_url}")
        bad_urls.append(f"{full_url}, {school}, Mounts")
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
    
    return df[['Name', 'Level', 'Health', 'Damage', 'Resist', 'Accuracy', 'Power Pip', 'Critical', 'Critical Block', 'Pierce', 'Stun Resist', 'Incoming', 'Outgoing', 'Pip Conserve', 'Shadow Pip', 'Archmastery', 'Source', 'Owned', 'Gear Set']]

def clean_mounts_df(df):
    combine_school_and_global_stats(df)
    df = only_show_necessary_cols(df)
    df = df.sort_values(by = ["Damage", "Resist", "Health", "Pierce", "Critical", "Accuracy", "Power Pip", "Critical Block", "Shadow Pip", "Archmastery", "Incoming", "Outgoing", "Pip Conserve", "Stun Resist", "Gear Set", "Owned", "Name"],
                        ascending = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, True]).reset_index(drop=True)
    return df
# this likely gets moved to html along with all the other objectively better functions
def remove_normal_mounts(df):
    # List of columns to check
    stats = ['Health', 'Damage', 'Resist', 'Accuracy', 'Power Pip', 'Critical', 'Critical Block', 'Pierce', 'Stun Resist', 'Incoming', 'Outgoing', 'Pip Conserve', 'Shadow Pip', 'Archmastery']

    # Condition to check if all specified columns are 0
    condition_all_zero = (df[stats] == 0).all(axis=1)

    # Condition to check if either 'd' or 'e' is True
    condition_d_or_e_true = df['Owned'] | (df['Gear Set'] != "None")

    # Combine conditions: keep rows if not all zero or if 'd' or 'e' is True
    df = df[~condition_all_zero | condition_d_or_e_true].reset_index(drop = True)
    
    default_mount = pd.DataFrame([{"Name": "Other", "Level": 1, "Health": 0, "Damage": 0, "Resist": 0, "Accuracy": 0, "Power Pip": 0, "Critical": 0, "Critical Block": 0, "Pierce": 0, "Stun Resist": 0, "Incoming": 0, "Outgoing": 0, "Pip Conserve": 0, "Shadow Pip": 0, "Archmastery": 0, "Source": "Gold Vendor", "Owned": True, "Gear Set": "None"}])

    df = df._append(default_mount, ignore_index = True)
    
    return df


def create_mounts(main_school):
    
    global school
    school = main_school
    
    base_url = "https://wiki.wizard101central.com"
    url = "https://wiki.wizard101central.com/wiki/index.php?title=Category:Mounts"
    
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
    df = clean_mounts_df(df)
    # df = remove_normal_mounts(df) # save this function as a "remove objectively worse"
    print(df)
    df.to_csv(f'Gear\\{school}_Gear\\{school}_Mounts.csv', index=False)
        
    return bad_urls
