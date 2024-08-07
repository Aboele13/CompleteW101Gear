import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from bs4 import BeautifulSoup

import findItemSource
from webAccess import fetch_url_content, replace_img_with_filename

school = None
gear_types = ["Wand", "Athame", "Amulet", "Ring", "Deck"]
gear_type = None

def extract_bullet_points_from_html(html_content):
    if html_content is None:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    bullet_points = []

    # Find all list items (<li>) that contain the text "Item:"
    for li in soup.find_all('li'):
        if li.text.strip().startswith("Item:"):
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
        if "Deckathlete" in text_content:
            return ["Deckathlete"], None, soup
        
        lines = text_content.splitlines()
        
        # Extract content between "Item:" and "Image"
        start_index = None
        end_index = None
        level_required = None
        for i, line in enumerate(lines):
            if line.startswith("Item:"):
                start_index = i
            if line.startswith("Level Required:"):
                level_required = lines[i + 1].strip().replace("+", "")
                try:
                    level_required = int(level_required)
                except ValueError:
                    level_required = 1
            if line.startswith("Image"):
                end_index = i
                break
        
        if start_index is not None and end_index is not None:
            return lines[start_index:end_index], level_required, soup
        elif start_index is not None:
            return lines[start_index:], level_required, soup
        else:
            return [], level_required, soup
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
    skip_phrases = ["From Wizard101 Wiki", "Jump to:", "navigation", "search", f"(50px-%28Icon%29_{school}.png)", f"(50px-%28Icon%29_Global.png)", f"(50px-%28Icon%29_{gear_type}.png)"]
    for line in extracted_info:
        if any(phrase in line for phrase in skip_phrases):
            continue
        # Clean up extra commas and percentage signs
        cleaned_line = line.replace(',', '').replace('%', '').replace('(25px-28Icon29_', '').replace('(18px-28Icon29_', '').replace('.png)', '').replace('_', ' ')
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
        'Archmastery Rating': 0,
        'Unlocked Tear': 0,
        'Unlocked Circle': 0,
        'Unlocked Square': 0,
        'Unlocked Triangle': 0,
        'Locked Tear': 0,
        'Locked Circle': 0,
        'Locked Square': 0,
        'Locked Triangle': 0
    }
    
    poss_school_spec_cate = ["Damage", "Resistance", "Accuracy", "Critical Rating", "Critical Block Rating", "Armor Piercing", "Pip Conversion Rating"]
    
    capture = False
    category_parts = []
    value = 0
    valid_schools = {"Global", f"{school}"}
    all_schools = {"Global", "Death", "Fire", "Balance", "Myth", "Storm", "Ice", "Life", "Shadow"}
    
    for i, line in enumerate(info_lines):
        if line.startswith("Bonuses:"):
            capture = True
        elif line.startswith("Tradeable") or line.startswith("Auctionable") or line.startswith("No Trade") or line.startswith("Unknown Trade Status") or line.startswith("Item Card") or line.startswith("Sockets"):
            break
        elif capture:
            if line in all_schools and line not in valid_schools:
                if i > 0 and info_lines[i - 1].startswith("+"):
                    info_lines[i - 1] = ""
                info_lines[i] = ""
                continue
            if line.startswith("+") and not line.startswith("+No"):
                if category_parts:
                    category = " ".join(category_parts).strip()
                    if category in bonuses:
                        bonuses[category] += int(value)
                    elif category in valid_schools:
                        # look forward for nearest category and concatenate
                            curr_school = category
                            poss_cate = ""
                            j = i + 2
                            while j < len(info_lines):
                                if info_lines[j].startswith("+"):
                                    j += 1
                                elif info_lines[j] in all_schools:
                                    j += 1
                                else:
                                    poss_cate += info_lines[j]
                                    if poss_cate in poss_school_spec_cate:
                                        bonuses[curr_school + " " + poss_cate] += int(value)
                                        break
                                    else:
                                        j += 1
                    category_parts = []
                parts = line.split()
                try:
                    value = int(parts[0][1:])
                except ValueError:
                    return parse_wiki_error_gear(item_name, bonuses, parts)
                category_parts = parts[1:]
            else:
                category_parts.append(line)
    
    if category_parts:
        category = " ".join(category_parts).strip()
        if category in bonuses:
            bonuses[category] += int(value)
        
    # Check for Sockets and count occurrences of specific types
    if "Sockets" in info_lines:
        combined_text = " ".join(info_lines)
        unlocked_tears = combined_text.count("Tear Socket Tear")
        unlocked_circles = combined_text.count("Circle Socket Circle")
        unlocked_squares = combined_text.count("Square Socket Square")
        unlocked_triangles = combined_text.count("Triangle Socket Triangle")
        locked_tears = combined_text.count("Locked Socket Tear")
        locked_circles = combined_text.count("Locked Socket Circle")
        locked_squares = combined_text.count("Locked Socket Square")
        locked_triangles = combined_text.count("Locked Socket Triangle")
        bonuses['Unlocked Tear'] = unlocked_tears
        bonuses['Unlocked Circle'] = unlocked_circles
        bonuses['Unlocked Square'] = unlocked_squares
        bonuses['Unlocked Triangle'] = unlocked_triangles
        bonuses['Locked Tear'] = locked_tears
        bonuses['Locked Circle'] = locked_circles
        bonuses['Locked Square'] = locked_squares
        bonuses['Locked Triangle'] = locked_triangles
    
    return bonuses

def process_bullet_point(base_url, bullet_point):
    item_name = bullet_point['text'].replace("Item:", "").strip()
    
    # Construct absolute URL for the hyperlink
    full_url = urllib.parse.urljoin(base_url, bullet_point['link'])
    print(f"Link: {full_url}")
    
    # Fetch and extract all information from the hyperlink
    text_info, level_required, soup = extract_information_from_url(full_url)
    
    if "-100% Max" in text_info:
        return None
    elif "Deckathlete" in text_info:
        return None
    elif text_info:
        formatted_info = format_extracted_info(text_info)
        bonuses = parse_bonuses(formatted_info, item_name)
        item_data = {
            'Name': item_name,
            'Level': level_required
        }
        item_data.update(bonuses)
        
        # set the item's source
        item_data['Source'] = findItemSource.get_item_source(item_name, formatted_info)
        
        # set the item's gear set (or None if none)
        item_data['Gear Set'] = formatted_info[formatted_info.index("From Set:") + 1] if "From Set:" in formatted_info else "None"
        
        # set the starting pips to only wands and decks
        total_pips = 0
        while "at start of battle." in formatted_info:
            at_start_of_battle_index = formatted_info.index("at start of battle.")
            num_pips = int(formatted_info[at_start_of_battle_index - 2].replace("+", ""))
            pip_worth = 2 if formatted_info[at_start_of_battle_index - 1] == 'Power Pip' else 1
            total_pips += (num_pips * pip_worth)
            formatted_info = formatted_info[at_start_of_battle_index + 1:]
            
        item_data['Starting Pips'] = total_pips
        
        return item_data
    else:
        print(f"Failed to fetch content from {full_url}")
        return None

def combine_school_and_global_stats(df):
    df["Damage"] = df[f"{school} Damage"] + df["Global Damage"]
    df["Accuracy"] = df[f"{school} Accuracy"] + df["Global Accuracy"]
    df["Critical"] = df[f"{school} Critical Rating"] + df["Global Critical Rating"]
    df["Pierce"] = df[f"{school} Armor Piercing"] + df["Global Armor Piercing"]
    df["Pip Conserve"] = df[f"{school} Pip Conversion Rating"] + df["Global Pip Conversion Rating"]

def only_show_necessary_cols(df):
    df.rename(columns={'Max Health': 'Health', 'Global Resistance': 'Resist', 'Power Pip Chance': 'Power Pip', 'Global Critical Block Rating': 'Critical Block', 'Stun Resistance': 'Stun Resist', 'Incoming Healing': 'Incoming', 'Outgoing Healing': 'Outgoing', 'Shadow Pip Rating': 'Shadow Pip', 'Archmastery Rating': 'Archmastery'}, inplace=True)
    df["Level"] = df["Level"].astype(int)
    df["Owned"] = False
    
    if gear_type == "Wand" or gear_type == "Deck":
        return df[['Name', 'Level', 'Health', 'Damage', 'Resist', 'Accuracy', 'Power Pip', 'Critical', 'Critical Block', 'Pierce', 'Stun Resist', 'Incoming', 'Outgoing', 'Pip Conserve', 'Shadow Pip', 'Archmastery', 'Starting Pips', 'Unlocked Tear', 'Unlocked Circle', 'Unlocked Square', 'Unlocked Triangle', 'Locked Tear', 'Locked Circle', 'Locked Square', 'Locked Triangle', 'Source', 'Owned', 'Gear Set']]
    else:
        return df[['Name', 'Level', 'Health', 'Damage', 'Resist', 'Accuracy', 'Power Pip', 'Critical', 'Critical Block', 'Pierce', 'Stun Resist', 'Incoming', 'Outgoing', 'Pip Conserve', 'Shadow Pip', 'Archmastery', 'Unlocked Tear', 'Unlocked Circle', 'Unlocked Square', 'Unlocked Triangle', 'Locked Tear', 'Locked Circle', 'Locked Square', 'Locked Triangle', 'Source', 'Owned', 'Gear Set']]

def sort_by_cols(df, *args):
    return df.sort_values(by = list(args), ascending = [False] * len(args)).reset_index(drop=True)

def clean_accessories_df(df):
    combine_school_and_global_stats(df)
    df = only_show_necessary_cols(df)
    return sort_by_cols(df, "Damage", "Resist", "Health", "Pierce", "Critical")

def create_accessories(main_school):
    
    global school
    school = main_school
            
    df_list = []
    
    for type in gear_types:
        
        global gear_type
        gear_type = type
    
        base_url = "https://wiki.wizard101central.com"
        urls = [f"https://wiki.wizard101central.com/wiki/index.php?title=Category:{school}_School_{gear_type}s",
            f"https://wiki.wizard101central.com/wiki/Category:Any_School_{gear_type}s"
            ]
    
        items_data = []

        for url in urls:
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
        df = clean_accessories_df(df)
        print(df)
        df.to_csv(f'{school}_Gear\\{school}_{gear_type}s.csv', index=False)
        
        df_list.append(df)
    
    return df_list
