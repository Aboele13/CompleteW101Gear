import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from bs4 import BeautifulSoup

import utils
from webAccess import fetch_url_content, replace_img_with_filename

all_jewel_shapes = {'Tear', 'Circle', 'Square', 'Triangle'}
all_pin_shapes = {'Sword', 'Shield', 'Power'}

def extract_bullet_points_from_html(html_content):
    if not html_content:
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
            if line.startswith("Acquisition Source") or line.startswith("Sell Price") or line.startswith("Documentation on how") or "(10px-%28Icon%29_Counter.png)" in line or line == "Shatter":
                end_index = i
                break
        
        if start_index and end_index:
            return lines[start_index:end_index], soup
        elif start_index:
            return lines[start_index:], soup
        else:
            return [], soup
    else:
        return [], None, None

def format_extracted_info(extracted_info):
    formatted_info = []
    for line in extracted_info:
        # Clean up extra commas and percentage signs
        cleaned_line = re.sub(r'\((\d+px-)?\d+(Icon|Item)\d+ *', '', line.replace(',', '').replace('%', '').replace('.png)', '').replace('_', ' ')) # handle most file gross stuff
        cleaned_line = re.sub(r'\(\d+px-\d+Item Card\d+', 'Item Card', cleaned_line) # handle item card file gross stuff
        if len(cleaned_line) > 0:
            cleaned_line = cleaned_line[1:] if cleaned_line[0] == " " else cleaned_line
            formatted_info.append(cleaned_line)
    
    if formatted_info[-1] == "Item Card":
        formatted_info[-2] = formatted_info[-1] + ' ' + formatted_info[-2]
        formatted_info = formatted_info[:-1]
    
    return formatted_info

def get_enchant_damage(damage_IC, jewel_name):
    text_info, soup = utils.extract_item_card_info_from_url(f"https://wiki.wizard101central.com/wiki/ItemCard:{damage_IC}")
    
    formatted_info = format_extracted_info(text_info)
    
    # work backward to find what damage this item matches with
    found_item = False
    i = len(formatted_info) - 1
    while i >= 0:
        if not found_item:
            if formatted_info[i] == jewel_name:
                found_item = True
        else:
            if formatted_info[i].endswith("Damage to 1 Spell"):
                return int(formatted_info[i].split("+")[1].split()[0])
        i -= 1
    
    #this should never happen, but default value
    return 0

def process_bullet_point(base_url, bullet_point):
    jewel_name = bullet_point['text'].replace("Jewel:", "").strip()
    
    # Construct absolute URL for the hyperlink
    full_url = urllib.parse.urljoin(base_url, bullet_point['link'])
    print(f"Link: {full_url}")
    
    # Fetch and extract all information from the hyperlink
    text_info, soup = extract_information_from_url(full_url)
    
    if text_info:
        formatted_info = format_extracted_info(text_info)
        bonuses = find_bonus(formatted_info, jewel_name)
        jewel_data = {
            'Name': jewel_name
        }
        jewel_data.update(bonuses)
        
        # if jewel_name == "Storm Crushing Pin (170, Balance)": # testing
        #     print(formatted_info)
        
        for damage_IC in utils.damage_ICs:
            if f"Item Card {damage_IC}" in formatted_info or f"Item Card {damage_IC} Variation" in formatted_info:
                jewel_data["Enchant Damage"] = get_enchant_damage(damage_IC, jewel_name)
                break
        if "Enchant Damage" not in jewel_data:
            jewel_data["Enchant Damage"] = 0
        
        # set the school last
        jewel_data["School"] = formatted_info[formatted_info.index('School') + 1] if 'School' in formatted_info else 'Global'
        
        return jewel_data
    else:
        # failed to collect info from page, just retry
        return process_bullet_point(base_url, bullet_point)
        # if this is actually broken, the page url will just be printed over and over so i know what page needs attention

# need to get level and effect
def find_bonus(formatted_info, jewel_name):
    
    bonuses = {
        "Level": 1,
        'Health': 0,
        'Power Pip Chance': 0,
        'Stun Resistance': 0,
        'Incoming Healing': 0,
        'Outgoing Healing': 0,
        'Shadow Pip Rating': 0,
        'Archmastery Rating': 0,
    }
    
    poss_school_spec_cate = ["Damage", "Resistance", "Accuracy", "Critical Rating", "Critical Block Rating", "Armor Piercing", "Pip Conversion Rating", "Flat Damage", "Flat Resistance"]
    
    for stat_school in utils.all_stat_schools:
        for stat in poss_school_spec_cate:
            bonuses[f"{stat_school} {stat}"] = 0
    
    capture = False
    category_parts = []
    value = 0
    
    for i in range(len(formatted_info)):
        if "(Level " in formatted_info[i]:
            bonuses["Level"] = int(formatted_info[i].split("(Level ")[1].split("+")[0])
        elif formatted_info[i] == "Level":
            bonuses["Level"] = 1 if formatted_info[i + 1] == "Any" else int(formatted_info[i + 1].replace("+", ""))
        elif formatted_info[i] == "Effect":
            capture = True
        elif capture: # in the range you should be reading
            if (formatted_info[i].startswith("+") and not formatted_info[i].startswith("+No")) or formatted_info[i].startswith("-"): # starts with +number
                if category_parts: # already some part of a stat
                    category = " ".join(category_parts).strip()
                    if category in bonuses:
                        bonuses[category] += int(value)
                    elif category in utils.all_stat_schools:
                        # look forward for nearest category and concatenate
                            curr_school = category
                            poss_cate = []
                            j = i + 2
                            while j < len(formatted_info):
                                if formatted_info[j].startswith("+"):
                                    j += 1
                                elif formatted_info[j] in utils.all_stat_schools:
                                    j += 1
                                else:
                                    poss_cate.append(formatted_info[j])
                                    poss_cate_str = " ".join(poss_cate)
                                    if poss_cate_str in poss_school_spec_cate:
                                        bonuses[curr_school + " " + poss_cate_str] += int(value)
                                        break
                                    else:
                                        j += 1
                    category_parts = []
                parts = formatted_info[i].split()
                try:
                    value = int(parts[0][1:])
                except ValueError:
                    return parse_wiki_error_jewels(jewel_name, bonuses, parts)
                category_parts = parts[1:]
            else:
                category_parts.append(formatted_info[i])

    # final check, not included in loop
    if category_parts:
        category = " ".join(category_parts).strip()
        if category in bonuses:
            bonuses[category] += int(value)
    
    return bonuses

def parse_wiki_error_jewels(jewel_name, bonuses, parts):
    # unique cases due to wiki error
    if jewel_name == "Name of bad wiki jewel here":
        # set bonuses[category] = here
        return bonuses
    else:
        print(f"Error on {jewel_name}")
        value = int(parts[0][1:]) # should throw an error and end execution
        return value

def clean_jewels_df(df):
    df = utils.distribute_global_stats(df)
    df = df.rename(columns={'Health': 'Max Health'})
    df = utils.reorder_df_cols(df)
    df = df.sort_values(by = ['Level', 'School', 'Name'], ascending = [False, True, True]).reset_index(drop=True)
    return df

def update_jewels(jewel_shapes):
    
    for curr_jewel_shape in jewel_shapes:
        
        base_url = "https://wiki.wizard101central.com"
        url = f"https://wiki.wizard101central.com/wiki/Category:{curr_jewel_shape}-Shaped_Jewels" if curr_jewel_shape in all_jewel_shapes else f"https://wiki.wizard101central.com/wiki/Category:{curr_jewel_shape}_Pins"
        
        jewels_data = []
        bullet_points = []
        
        if curr_jewel_shape in all_jewel_shapes:
            print(f'\nCollecting {curr_jewel_shape} Jewels...\n')
        elif curr_jewel_shape in all_pin_shapes:
            print(f'\nCollecting {curr_jewel_shape} Pins...\n')
        
        while url:
            # Fetch content from the URL
            html_content = fetch_url_content(url)

            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                # Extract bullet points with links from the HTML content
                bullet_points.extend(extract_bullet_points_from_html(html_content))
    
                # Find the "(next page)" link
                next_page_link = utils.find_next_page_link(soup)
                if next_page_link:
                    url = urllib.parse.urljoin(base_url, next_page_link)
                else:
                    url = None
            else:
                print("Failed to fetch content from the URL.")
                continue
        
        with ThreadPoolExecutor(max_workers=85) as executor:
            futures = [executor.submit(process_bullet_point, base_url, bp) for bp in bullet_points]
            for future in as_completed(futures):
                jewel_data = future.result()
                if jewel_data:
                    jewels_data.append(jewel_data)
        
        # move all items to dataframe
        df = pd.DataFrame(jewels_data).fillna(0)  # fill all empty values with 0
        df = clean_jewels_df(df)
        print(df)
        file_path = f'Jewels\\All_Jewels\\All_{curr_jewel_shape}_Jewels.csv'
        try:
            df.to_csv(file_path, index=False)
        except:
            input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
            df.to_csv(file_path, index=False)

        # update all schools
        for school in utils.schools_of_items: # change this if i want to test one school
            if school != "Global":
                file_path = f'Jewels\\{school}_Jewels\\{school}_{curr_jewel_shape}_Jewels.csv'
                school_df = df[(df['School'].str.startswith('Not') & ~df['School'].str.endswith(school)) | df['School'].isin([school, 'Global'])].reset_index(drop=True)
                try:
                    school_df.to_csv(file_path, index=False)
                except:
                    input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
                    school_df.to_csv(file_path, index=False)
