import itertools
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from bs4 import BeautifulSoup

import utils
from webAccess import fetch_url_content, replace_img_with_filename


def extract_bullet_points_from_html(html_content):
    if not html_content:
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
    skip_phrases = ["From Wizard101 Wiki", "Jump to:", "navigation", "search"]
    for line in extracted_info:
        if any(phrase in line for phrase in skip_phrases):
            continue
        # Clean up extra commas and percentage signs
        cleaned_line = re.sub(r'\((\d+px-)?\d+(Icon|Item|General)\d+ *', '', line.replace(',', '').replace('%', '').replace('.png)', '').replace('_', ' ')) # handle most file gross stuff
        formatted_info.append(cleaned_line[1:] if (cleaned_line and cleaned_line[0] == " ") else cleaned_line)
    return formatted_info

def process_bullet_point(base_url, bullet_point):
    set_name = bullet_point['text'].replace("Set:", "").strip()
    
    # Construct absolute URL for the hyperlink
    full_url = urllib.parse.urljoin(base_url, bullet_point['link'])
    print(f"Link: {full_url}")
    
    # Fetch and extract all information from the hyperlink
    text_info, soup = extract_information_from_url(full_url)
    
    if text_info:
        formatted_info = format_extracted_info(text_info)
        school = 'Global'
        
        # set the set's school
        if set_name != "Fossil Avenger's Set": # fossil is exception, doesn't need to get checked
            school = formatted_info[formatted_info.index("Set Bonuses") - 1]
            if school == 'Any':
                school = 'Global'
        
        sets_data = []
        for pieces in range(2, 11):
            sets_data.append(find_bonus(formatted_info, set_name, school, pieces))
        
        return sets_data
    else: # failed to collect info from page, just retry
        return process_bullet_point(base_url, bullet_point)
        # if this is actually broken, the page url will just be printed over and over so i know what page needs attention

def find_bonus(formatted_info, set_name, school, pieces):
    
    bonuses = {
        'Name': set_name,
        'Pieces': pieces,
        'Max Health': 0,
        'Power Pip Chance': 0,
        'Stun Resistance': 0,
        'Incoming Healing': 0,
        'Outgoing Healing': 0,
        'Shadow Pip': 0,
        'Archmastery': 0,
    }
    
    poss_school_spec_cate = ["Damage", "Resistance", "Accuracy", "Critical", "Critical Block", "Armor Piercing", "Pip Conversion", "Flat Damage", "Flat Resistance"]
    
    for stat_school in utils.all_stat_schools:
        for stat in poss_school_spec_cate:
            bonuses[f"{stat_school} {stat}"] = 0
    
    bonuses['School'] = school
    
    capture = False
    category_parts = []
    value = 0
    
    for i in range(len(formatted_info)):
        if formatted_info[i].startswith(f'Tier {pieces} Stats'): # start reading here
            capture = True
        # stop reading once you find one of these
        elif capture and (formatted_info[i].startswith("Tier ") or formatted_info[i].startswith("Items in this Set")):
            break
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
                value = int(parts[0][1:])
                category_parts = parts[1:]
            else:
                category_parts.append(formatted_info[i])
    
    # final check, not included in loop
    if category_parts:
        category = " ".join(category_parts).strip()
        if category in bonuses:
            bonuses[category] += int(value)
    
    return bonuses

def accumulate_stats(df):
    
    # Get column names to exclude
    exclude_cols = ['Name', 'Pieces', 'School']
    # Get column names to include in the calculation
    include_cols = [col for col in df.columns if col not in exclude_cols]
    
    for i in range(1, len(df)):
        if df.iloc[i]['Name'] == df.iloc[i - 1]['Name']:
            df.loc[i, include_cols] += df.loc[i - 1, include_cols]
    return df

def update_set_bonuses():
    
    base_url = "https://wiki.wizard101central.com"
    url = "https://wiki.wizard101central.com/wiki/Category:Sets"
    
    bullet_points = []
    
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
    
    # multithread webscraping
    def process_bullets_multithreaded(base_url, bullet_points):
        sets_data = []
        def process_and_collect(bp):
            return process_bullet_point(base_url, bp)
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(process_and_collect, bullet_points))
            sets_data.extend(itertools.chain.from_iterable(results))
        return sets_data

    # call function to multithread webscrape
    sets_data = process_bullets_multithreaded(base_url, bullet_points)
    
    # move all items to dataframe
    df = pd.DataFrame(sets_data)
    df = utils.distribute_global_stats(df)
    # rename columns due to wiki inconsistencies
    df = df.rename(columns = {col: col + " Rating" for col in df.columns if (col.endswith("Critical") or col.endswith("Critical Block") or col.endswith("Shadow Pip") or col.endswith("Archmastery") or col.endswith("Pip Conversion"))}) # must come before block
    df = df.sort_values(by = ["Name", 'Pieces'], ascending = [True, True]).reset_index(drop=True)
    df = accumulate_stats(df)
    df = utils.reorder_df_cols(df, 3)
    print(df)
    file_path = f'Set_Bonuses\\All_Set_Bonuses.csv'
    try:
        df.to_csv(file_path, index=False)
    except:
        input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
        df.to_csv(file_path, index=False)

    # update all schools
    for school in utils.schools_of_wizards: # change this if i want to test one school
        file_path = f'Set_Bonuses\\{school}_Set_Bonuses.csv'
        school_df = df[df['School'].isin([school, 'Global'])]
        try:
            school_df.to_csv(file_path, index=False)
        except:
            input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
            school_df.to_csv(file_path, index=False)
