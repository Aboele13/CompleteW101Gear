import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from bs4 import BeautifulSoup

import utils
from webAccess import fetch_url_content, replace_img_with_filename


def extract_bullet_points_from_html(html_content, school):
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    bullet_points = []

    # Find all list items (<li>) that contain the text "Spell:"
    for li in soup.find_all('li'):
        if li.text.strip().startswith("Spell:"):
            # Check if the list item contains a hyperlink (<a> tag)
            a_tag = li.find('a', href=True)
            if a_tag:
                spell_name = li.text.strip()
                if spell_name != f'Spell:{school} School Spells':
                    bullet_points.append({
                        'text': spell_name,
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
        
        # Extract content between "Spell:" and "Documentation on how to edit this page"
        start_index = None
        end_index = None
        for i, line in enumerate(lines):
            if line.startswith("Spell:"):
                start_index = i
            if line.startswith("Documentation on how to edit this page"):
                end_index = i
                break
        
        if start_index and end_index:
            return lines[start_index:end_index]
        elif start_index:
            return lines[start_index:]
        else:
            return []
    else:
        return []

def format_extracted_info(extracted_info):
    formatted_info = []
    for line in extracted_info:
        # Clean up extra commas and percentage signs
        cleaned_line = re.sub(r'\((\d+px-)?\d+(Icon|Item)\d+ *', '', line.replace(',', '').replace('%', '').replace('.png)', '').replace('_', ' ')) # handle most file gross stuff
        if len(cleaned_line) > 0:
            cleaned_line = cleaned_line[1:] if cleaned_line[0] == " " else cleaned_line
            formatted_info.append(cleaned_line)
    
    return formatted_info

def description_to_damage(description):
    nums = []
    
    curr_num = ''
    per_pip = False
    
    for i in range(len(description)):
        char = description[i]
        if char.isdigit() or char in {'+', "-"}:
            curr_num = f"{curr_num}{char}"
        elif curr_num:
            nums.append(curr_num)
            curr_num = ''
        elif i + 5 < len(description) and description[i:i + 6] == "Rounds":
            nums.pop()
        elif not per_pip and i + 6 < len(description) and description[i:i + 7] == "per Pip":
            per_pip = True
    
    # description can't end with number, so we're done checking
    
    # remove charms/wards (they start with + or -)
    i = 0
    while i < len(nums):
        if nums[i][0] in {'+', "-"}:
            nums.pop(i)
        else:
            i += 1
    
    # get rid of dot damage
    nums = nums[0] if nums else '0'
    
    # find average in range
    if '-' in nums:
        two_nums = nums.split('-')
        nums = (int(two_nums[0]) + int(two_nums[1])) // 2
    
    return int(nums) * 5 if per_pip else int(nums) # update if starter pips increases

def set_owned_AOEs(spell_data): # update the owned spell everytime i get a new one (or spellement upgrade)
    
    # first AOE each school gets
    defaults = {"Deer Knight", "Meteor Strike", "Sandstorm", "Humongofrog", "Tempest", "Blizzard", "Ratatoskr's Spin"}
    
    # create the list of extra AOEs each account has
    andrew_owned_AOEs = {
        "Iron Curse", "Rainbow Serpent (Tier 3a)",
        "Deer Knight (Tier 2a)", "Ship of Fools", "Wobbegong Frenzy (Tier 3a)",
        "Phantasmania! (Tier 3a)",
        "Reindeer Knight",
        "Drop Bear Fury (Tier 3a)",
        "Bunyip's Rage (Tier 3a)",
        } | defaults
    chris_owned_AOEs = {"Bunyip's Rage"} | defaults
    tessa_owned_AOEs = {"Zand the Bandit"} | defaults
    
    # start each col value as False
    spell_data['Andrew Owned'] = False
    spell_data['Chris Owned'] = False
    spell_data['Tessa Owned'] = False
    
    # set to true if name matches
    if spell_data['Spell'] in andrew_owned_AOEs:
        spell_data['Andrew Owned'] = True
    if spell_data['Spell'] in chris_owned_AOEs:
        spell_data['Chris Owned'] = True
    if spell_data['Spell'] in tessa_owned_AOEs:
        spell_data['Tessa Owned'] = True
    
    return spell_data

def parse_spell(formatted_info, spell_name):
    spell_data = {
        'Spell': spell_name,
        'Pip Cost': 0,
        'School': "I don't know the school",
        'Damage': 0,
        'Has DOT': False,
    }
    
    for i, line in enumerate(formatted_info):
        if "Pip Cost" == line:
            pip_cost = formatted_info[i + 1]
            spell_data['Pip Cost'] += 5 if pip_cost == 'X' else int(pip_cost) # update if starter pips increases
        elif "School" == line:
            spell_data['School'] = formatted_info[i + 1]
        elif "Spell Description" == line:
            description = formatted_info[i + 1]
            if "Damage over" in description and "Rounds" in description:
                spell_data['Has DOT'] = True
            spell_data['Damage'] = description_to_damage(description)
        elif "School Pip Cost" == line:
            j = i + 1
            while formatted_info[j] != "Accuracy": # accounting for multiple school pips needed
                spell_data['Pip Cost'] += (int(formatted_info[j]) * 2)
                j += 2
    
    # set columns for which spells Andrew/Chris/Tessa have
    spell_data = set_owned_AOEs(spell_data)
    
    return spell_data

def spell_exceptions(spell_name): # catch spells that have language of AOEs, but aren't
    if spell_name.startswith("Natural Attack"): # natural attacks
        return True
    if spell_name.startswith("Mass "):
        return True
    if spell_name.startswith("Queen Calypso"):
        return True
    if spell_name.startswith("Windstorm"):
        return True
    if spell_name.startswith("Avenging Fossil"):
        return True
    if spell_name.startswith("Winged Sorrow"):
        return True
    if "Plague" in spell_name:
        return True
    if spell_name.startswith("Pork's Plan"):
        return True
    if spell_name.startswith("Scald"):
        return True
    if spell_name.startswith("Sun Serpent"):
        return True
    if spell_name.startswith("Scion of Fire"):
        return True
    
    return False

def is_not_aoe(spell_name, text_info):
    all_text = " ".join(text_info)
    
    # remove the spells I don't want
    if spell_exceptions(spell_name): # description has language of AOEs, but they aren't
        return True
    if "Beastmoon" in all_text: # beastmoon spells
        return True
    if "This Spell is cast by " in all_text: # creature only spells
        return True
    if "This Spell is given during the following battles" in all_text: # battle-specific spells
        return True
    if "PvP Only" in all_text: # pvp only spells
        return True
    if "all enemies" not in all_text: # spells that don't affect all enemies
        return True
    if "damage" not in all_text and "Damage" not in all_text: # spells that don't do damage
        return True
    if "(" in spell_name and "(Tier " not in spell_name: # outdated spell variants
        return True
    if "Shadow Pip Cost" in all_text: # shad spells (since shadow pips aren't guaranteed)
        return True
    
    return False

def process_bullet_point(base_url, bullet_point):
    spell_name = bullet_point['text'].replace("Spell:", "").strip()
    
    # Construct absolute URL for the hyperlink
    full_url = urllib.parse.urljoin(base_url, bullet_point['link'])
    print(f"Link: {full_url}")
    
    # Fetch and extract all information from the hyperlink
    text_info = extract_information_from_url(full_url)
    
    if text_info:
        
        # remove the spells I don't want
        if is_not_aoe(spell_name, text_info):
            return None
        
        formatted_info = format_extracted_info(text_info)
        
        # if spell_name == "Pork's Plan": # testing
        #     print(formatted_info)
        
        return parse_spell(formatted_info, spell_name)
    else: # failed to collect info from page, just retry
        return process_bullet_point(base_url, bullet_point)
        # if this is actually broken, the page url will just be printed over and over so i know what page needs attention

def update_AOEs():
    
    bullet_points = []
    
    for school in utils.schools_of_items:
        if school != "Global":
            
            base_url = "https://wiki.wizard101central.com"
            url = f"https://wiki.wizard101central.com/wiki/Category:{school}_Spells"
            
            print(f'\nCollecting {school} Spells...')

            while url:
                # Fetch content from the URL
                html_content = fetch_url_content(url)

                if html_content:
                    soup = BeautifulSoup(html_content, 'html.parser')
                    # Extract bullet points with links from the HTML content
                    bullet_points.extend(extract_bullet_points_from_html(html_content, school))

                    # Find the "(next page)" link
                    next_page_link = utils.find_next_page_link(soup)
                    if next_page_link:
                        url = urllib.parse.urljoin(base_url, next_page_link)
                    else:
                        url = None
                else:
                    print("Failed to fetch content from the URL.")
                    continue
    
    print('')
    
    # multithread webscraping
    def process_bullets_multithreaded(base_url, bullet_points):
        spells_data = []
        def process_and_collect(bp):
            return process_bullet_point(base_url, bp)
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(process_and_collect, bullet_points))
            spells_data.extend(results)
        return spells_data

    # call function to multithread webscrape
    spells_data = process_bullets_multithreaded(base_url, bullet_points)
    spells_data = [spell for spell in spells_data if spell is not None]
    
    # move all items to dataframe
    df = pd.DataFrame(spells_data).fillna(0)  # fill all empty values with 0
    df = df[df['Pip Cost'] <= 5] # only get AOEs I can use round one, update if starter pips changes
    df = df.sort_values(by=['School', 'Spell'], ascending=[True, True]).reset_index(drop=True)
    print(df)
    file_path = f'Other_CSVs\\AOEs.csv'
    try:
        df.to_csv(file_path, index=False)
    except:
        input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
        df.to_csv(file_path, index=False)

