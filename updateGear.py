import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from bs4 import BeautifulSoup

import findItemSource
import utils
from webAccess import fetch_url_content, replace_img_with_filename


def extract_bullet_points_from_html(html_content):
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    bullet_points = []

    # Find all list items (<li>) that contain the text "Item:" or "Mount:" or "Pet:"
    for li in soup.find_all('li'):
        if li.text.strip().startswith("Item:") or li.text.strip().startswith("Mount:") or li.text.strip().startswith("Pet:"):
            # Check if the list item contains a hyperlink (<a> tag)
            a_tag = li.find('a', href=True)
            if a_tag:
                bullet_points.append({
                    'text': li.text.strip(),
                    'link': a_tag['href']
                })
    
    return bullet_points

def extract_clothing_accessory_info_from_url(lines, soup):
    # Extract content between "Item:" and "Male Image" for clothing
    # Extract content between "Item:" and "Image" for accessories
    start_index = None
    end_index = None
    level_required = None
    gauntlet = False
    for i, line in enumerate(lines):
        if line.startswith("Item:"):
            start_index = i
        if line.startswith("Level Required:"):
            level_required = lines[i + 1].strip().replace("+", "")
            try:
                level_required = int(level_required)
            except ValueError:
                level_required = 1
        if line.startswith("Male Image") or line.startswith("Image"):
            end_index = i
            continue
        if end_index and end_index < i and any(gauntlet in line for gauntlet in findItemSource.housing_gauntlet_list):
            gauntlet = True
    
    if start_index and end_index:
        if not gauntlet:
            return lines[start_index:end_index], level_required, soup
        else:
            list = lines[start_index:end_index]
            list.append("From Gauntlet")
            return list, level_required, soup
    elif start_index:
        if not gauntlet:
            return lines[start_index:], level_required, soup
        else:
            list = lines[start_index:]
            list.append("From Gauntlet")
            return list, level_required, soup
    else:
        return [], level_required, soup

def extract_pet_mount_info_from_url(lines, soup):
    # Extract content between "Pet:" and "Documentation on how to edit this page" for pets
    # Extract content between "Mount:" and "Documentation on how to edit this page" for mounts
    start_index = None
    end_index = None
    level_required = 1
    for i, line in enumerate(lines):
        if line.startswith("Pet:") or line.startswith("Mount:"):
            start_index = i
        if line.startswith("Documentation on how to edit this page"):
            end_index = i
            break
    
    if start_index and end_index:
        return lines[start_index:end_index], level_required, soup
    elif start_index:
        return lines[start_index:], level_required, soup
    else:
        return [], level_required, soup


def extract_information_from_url(url, gear_type):
    html_content = fetch_url_content(url)
    if html_content:
        # Parse HTML content and replace <img> tags with filenames
        soup = BeautifulSoup(html_content, 'html.parser')
        soup = replace_img_with_filename(soup)
        # Extract all visible text from the modified HTML content
        text_content = soup.get_text(separator='\n', strip=True)
        lines = text_content.splitlines()
        
        # retrieve proper lines/levels based on gear type
        if gear_type in utils.clothing_gear_types or gear_type in utils.accessory_gear_types:
            return extract_clothing_accessory_info_from_url(lines, soup)
        elif gear_type == "Mounts" or gear_type == "Pets":
            return extract_pet_mount_info_from_url(lines, soup)
        else: # should never happen
            return [], None, soup
    else:
        return [], None, None

def format_extracted_info_wiki_errors(extracted_info, curr_gear_type):
    formatted_info = []
    for line in extracted_info:
        # Clean up extra commas and percentage signs
        cleaned_line = re.sub(r'\((\d+px-)?\d+(Icon|Item)\d+ *', '', line.replace(',', '').replace('%', '').replace('.png)', '').replace('_', ' ')) # handle most file gross stuff
        cleaned_line = re.sub(r'\(\d+px-\d+Item Card\d+', 'Item Card', cleaned_line) # handle item card file gross stuff
        if len(cleaned_line) > 0:
            cleaned_line = cleaned_line[1:] if cleaned_line[0] == " " else cleaned_line
            formatted_info.append(cleaned_line)
    
    if formatted_info[0] == "Item:Winter Elf Cap (Level 20+)":
        while formatted_info[1] != '50x50px':
            formatted_info.pop(1)
        formatted_info[1] = "Global"
    else:
        print(f"Wiki School Error on {formatted_info[0]}")
        while formatted_info[1] not in utils.schools_of_items:
            formatted_info.pop(1)
    
    return formatted_info

def format_extracted_info(extracted_info, curr_gear_type):
    formatted_info = []
    for line in extracted_info:
        # Clean up extra commas and percentage signs
        cleaned_line = re.sub(r'\((\d+px-)?\d+(Icon|Item)\d+ *', '', line.replace(',', '').replace('%', '').replace('.png)', '').replace('_', ' ')) # handle most file gross stuff
        cleaned_line = re.sub(r'\(\d+px-\d+Item Card\d+', 'Item Card', cleaned_line) # handle item card file gross stuff
        if len(cleaned_line) > 0:
            cleaned_line = cleaned_line[1:] if cleaned_line[0] == " " else cleaned_line
            formatted_info.append(cleaned_line)
    
    # school should come second for clothing and accessories,
    # so remove anything from formatted_info[1] that isn't a school
    if curr_gear_type in utils.clothing_gear_types or curr_gear_type in utils.accessory_gear_types:
        try:
            while formatted_info[1] not in utils.schools_of_items:
                formatted_info.pop(1)
        except: # some wiki pages are errors and don't have schools
            return format_extracted_info_wiki_errors(extracted_info, curr_gear_type)
    
    return formatted_info

def parse_wiki_error_gear(item_name, bonuses, parts):
    # unique cases due to wiki error
    if item_name == "Tenacious Headgear":
        bonuses["Max Health"] = 20
        bonuses["Global Resistance"] = 2
        return bonuses
    elif item_name == "Leisure Dome Suit (Level 130+)":
        bonuses["Max Health"] = 1457
        bonuses["Shadow Pip Rating"] = 18
        bonuses["Global Critical Block Rating"] = 113
        bonuses["Global Resistance"] = 17
        bonuses["Stun Resistance"] = 6
        return bonuses
    elif item_name == "Footwraps of Pictures":
        bonuses["Max Health"] = 21
        bonuses[f"Storm Accuracy"] = 2
        return bonuses
    elif item_name == "Tetrus Deck of Sleet":
        bonuses["Max Health"] = 84
        bonuses["Global Critical Block Rating"] = 43
        bonuses["Ice Pip Conversion Rating"] = 90
        bonuses["Locked Triangle"] = 1
        bonuses["Starting Pips"] = 1
        return bonuses
    elif item_name == "Tetrus Deck of Purpose":
        bonuses["Max Health"] = 75
        bonuses["Global Critical Block Rating"] = 43
        bonuses["Ice Pip Conversion Rating"] = 90
        bonuses["Locked Triangle"] = 1
        bonuses["Starting Pips"] = 1
        return bonuses
    else:
        print(f"Error on {item_name}")
        value = int(parts[0][1:]) # should throw an error and end execution
        return value

def parse_bonuses(formatted_info, item_name, curr_gear_type):
    bonuses = {
        'Max Health': 0,
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

    if curr_gear_type == "Pets": # pets don't have stats to read, they're done here
        return bonuses
    
    capture = False
    
    if curr_gear_type == "Mounts":
        for i, line in enumerate(formatted_info):
            if line.startswith("Stat Boost"):
                capture = True
            elif capture:
                if line == 'View of the Mount in use':
                    if formatted_info[i - 2] == "N/A":
                        return bonuses
                    stat = []
                    j = i - 2
                    while j >= 0:
                        stat.insert(0, formatted_info[j])
                        if formatted_info[j].startswith("+"):
                            value = int(stat[0][1:])
                            category = " ".join(stat[1:])
                            if category in bonuses:
                                bonuses[category] = int(value)
                                break
                        j -= 1
        
        return bonuses
    
    # only moving on if clothing or accessory
    category_parts = []
    value = 0
    
    for i in range(len(formatted_info)):
        if formatted_info[i].startswith("Bonuses:"): # start reading here
            capture = True
        # stop reading once you find one of these
        elif formatted_info[i].startswith("Tradeable") or formatted_info[i].startswith("Auctionable") or formatted_info[i].startswith("No Trade") or formatted_info[i].startswith("Unknown Trade Status") or formatted_info[i].startswith("Item Card") or formatted_info[i].startswith("Sockets"):
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
                try:
                    value = int(parts[0][1:])
                except ValueError:
                    return parse_wiki_error_gear(item_name, bonuses, parts)
                category_parts = parts[1:]
            else:
                category_parts.append(formatted_info[i])
    
    # final check, not included in loop
    if category_parts:
        category = " ".join(category_parts).strip()
        if category in bonuses:
            bonuses[category] += int(value)
    
    # Check for Sockets and count occurrences of specific types
    if curr_gear_type in utils.clothing_gear_types: # pins for clothing
        if "Sockets" in formatted_info:
            sword_pins = formatted_info.count("Sword Socket")
            shield_pins = formatted_info.count("Shield Socket")
            power_pins = formatted_info.count("Power Socket")
            bonuses['Sword Pins'] = int(sword_pins)
            bonuses['Shield Pins'] = int(shield_pins)
            bonuses['Power Pins'] = int(power_pins)
        else:
            bonuses['Sword Pins'] = int(0)
            bonuses['Shield Pins'] = int(0)
            bonuses['Power Pins'] = int(0)
    
    elif curr_gear_type in utils.accessory_gear_types: # jewels for accessories
        if "Sockets" in formatted_info:
            combined_text = " ".join(formatted_info)
            unlocked_tears = combined_text.count("Tear Socket Tear")
            unlocked_circles = combined_text.count("Circle Socket Circle")
            unlocked_squares = combined_text.count("Square Socket Square")
            unlocked_triangles = combined_text.count("Triangle Socket Triangle")
            locked_tears = combined_text.count("Locked Socket Tear")
            locked_circles = combined_text.count("Locked Socket Circle")
            locked_squares = combined_text.count("Locked Socket Square")
            locked_triangles = combined_text.count("Locked Socket Triangle")
            bonuses['Unlocked Tear'] = int(unlocked_tears)
            bonuses['Unlocked Circle'] = int(unlocked_circles)
            bonuses['Unlocked Square'] = int(unlocked_squares)
            bonuses['Unlocked Triangle'] = int(unlocked_triangles)
            bonuses['Locked Tear'] = int(locked_tears)
            bonuses['Locked Circle'] = int(locked_circles)
            bonuses['Locked Square'] = int(locked_squares)
            bonuses['Locked Triangle'] = int(locked_triangles)
        else:
            bonuses['Unlocked Tear'] = 0
            bonuses['Unlocked Circle'] = 0
            bonuses['Unlocked Square'] = 0
            bonuses['Unlocked Triangle'] = 0
            bonuses['Locked Tear'] = 0
            bonuses['Locked Circle'] = 0
            bonuses['Locked Square'] = 0
            bonuses['Locked Triangle'] = 0
    
    # set the starting pips to only wands and decks
    if curr_gear_type in utils.starting_pip_gear_types:
        total_pips = 0
        i = 2
        while i < len(formatted_info):
            if formatted_info[i] == "at start of battle.":
                # Extract number of pips and pip type directly
                num_pips_str = formatted_info[i - 2].replace("+", "")
                num_pips = 0 if num_pips_str == "No" else int(num_pips_str)
                # Determine pip worth based on the previous entry
                pip_worth = 1 if formatted_info[i - 1] == 'Pip' else 2
                # Accumulate total pips
                total_pips += num_pips * pip_worth
            # Move to the next item
            i += 1
        bonuses['Starting Pips'] = total_pips

    return bonuses

def process_bullet_point(base_url, bullet_point, curr_gear_type):
    item_name = bullet_point['text'].replace("Item:", "").replace("Mount:", "").replace("Pet:", "").strip()
    
    # Construct absolute URL for the hyperlink
    full_url = urllib.parse.urljoin(base_url, bullet_point['link'])
    print(f"Link: {full_url}")
    
    # Fetch and extract all information from the hyperlink
    text_info, level_required, soup = extract_information_from_url(full_url, curr_gear_type)
    
    if curr_gear_type == "Mounts" and "Permanent" not in text_info:
        return None
    
    if text_info:
        formatted_info = format_extracted_info(text_info, curr_gear_type)
        item_data = {
            'Name': item_name,
            'Level': int(level_required)
        }
        item_data.update(parse_bonuses(formatted_info, item_name, curr_gear_type))
        
        # set the item's source (pets don't have sources)
        if curr_gear_type != "Pets":
            item_data['Source'] = findItemSource.get_item_source(item_name, formatted_info, curr_gear_type)

        # check for enchantment ICs if not mount
        if curr_gear_type != "Mounts":
            for damage_IC in utils.damage_ICs:
                if f"Item Card {damage_IC}" in formatted_info or f"Item Card {damage_IC} Variation" in formatted_info:
                    item_data["Enchant Damage"] = get_enchant_damage(damage_IC, item_name)
                    break
            if "Enchant Damage" not in item_data:
                item_data["Enchant Damage"] = 0

        # set the item's gear set (or No Gear Set if none)
        # mounts and pets look for "Set"
        if curr_gear_type == "Mounts" or curr_gear_type == "Pets":
            for i in range(len(formatted_info) - 1):
                if formatted_info[i] == 'Set':
                    item_data['Gear Set'] = formatted_info[i + 1]
                    break
        # clothing and accessories look for "From Set:"
        else:
            for i in range(len(formatted_info) - 1):
                if formatted_info[i] == "From Set:" or (curr_gear_type == "Mounts" and formatted_info[i] == 'Set'):
                    item_data['Gear Set'] = formatted_info[i + 1]
                    break
        
        # if item_name == "True Silver Helmet (Level 20+)": # testing
        #     print(formatted_info)
        
        if "Gear Set" not in item_data:
            item_data['Gear Set'] = "No Gear Set"
        
        if "-100 Max" in formatted_info:
            item_data['Usable In'] = "PVP"
        elif "Deckathlete" in item_name:
            item_data['Usable In'] = "Deckathalon"
        else:
            item_data['Usable In'] = "Everything"
        
        # find what school the item is
        if curr_gear_type in utils.clothing_gear_types or curr_gear_type in utils.accessory_gear_types:
            school = formatted_info[1] # school is always the second spot (clothing and accessories)
            pot_mastery_school = formatted_info[2] # if mastery item, the school is in third spot
            if school == "Global" and pot_mastery_school.startswith("Not "): # if it's a mastery item
                item_data['School'] = pot_mastery_school
            else:
                item_data['School'] = school # school is always the second spot (clothing and accessories)
        elif curr_gear_type == "Pets":
            i = formatted_info.index('Loved Snacks') - 1
            if formatted_info[i] in utils.schools_of_items:
                item_data['School'] = formatted_info[i]
            else:
                item_data['School'] = 'Global'
        
        return item_data
    else: # failed to collect info from page, just retry
        return process_bullet_point(base_url, bullet_point, curr_gear_type)
        # if this is actually broken, the page url will just be printed over and over so i know what page needs attention

def get_enchant_damage(damage_IC, item_name):
    text_info, soup = utils.extract_item_card_info_from_url(f"https://wiki.wizard101central.com/wiki/ItemCard:{damage_IC}")
    
    formatted_info = format_extracted_info(text_info, "")
    
    # work backward to find what damage this item matches with
    found_item = False
    i = len(formatted_info) - 1
    while i >= 0:
        if not found_item:
            if formatted_info[i] == item_name:
                found_item = True
        else:
            if formatted_info[i].endswith("Damage to 1 Spell"):
                return int(formatted_info[i].split("+")[1].split()[0])
        i -= 1
    
    #this should never happen, but default value
    return 0

def create_default_pet():
    # create a default pet (no gear set)
    bonuses = {
        'Name': 'Other',
        'Level': 1,
        'Max Health': 0,
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
            
    bonuses['Enchant Damage'] = 0
    bonuses['Gear Set'] = 'No Gear Set'
    bonuses['Usable In'] = 'Everything'
    bonuses['School'] = 'Global'
    
    # move all items to dataframe
    return pd.DataFrame([bonuses]).fillna(0)  # fill all empty values with 0

def remove_normal_pets(df):
    # Identify numerical columns, excluding 'Level'
    numeric_cols = df.select_dtypes(include=['number']).drop('Level', axis=1).columns

    # Filter out rows where all numerical columns (excluding 'Level') are zero AND 'Gear Set' is 'No Gear Set'
    df = df[~((df[numeric_cols] == 0).all(axis=1) & (df['Gear Set'] == 'No Gear Set'))].reset_index(drop=True)
    
    # Append the default pet to the original DataFrame
    return pd.concat([df, create_default_pet()], ignore_index=True)

def create_pet_variants(df):
    # personal variations of a "perfect pet" (personal opinion)
    variations = [{"Name": "Max Resist", "Global Resistance": 21}]
    
    for school in utils.schools_of_items:
        if school != "Global":
            variations.append({"Name": f"{school} Max Damage", "Global Damage": 11, f"{school} Damage": 22})
            variations.append({"Name": f"{school} Triple Double", "Global Damage": 7, f"{school} Damage": 18, "Global Resistance": 17})
            
            # I have the above, only uncomment the below if I want to experiment with new pets
            # variations.append({"Name": f"{school} 3 Damage, 2 Pierce, Resist", "Global Damage": 6, f"{school} Damage": 16, "Global Resistance": 10, "Global Armor Piercing": 5})
            # variations.append({"Name": f"{school} 3 Damage, 2 Pierce", "Global Damage": 7, f"{school} Damage": 18, "Global Armor Piercing": 6})
            # variations.append({"Name": f"{school} Triple Double, Accuracy", "Global Damage": 6, f"{school} Damage": 16, "Global Resistance": 15, f"{school} Accuracy": 10})
            # variations.append({"Name": f"{school} Triple Double, Pierce", "Global Damage": 6, f"{school} Damage": 16, "Global Resistance": 15, "Global Armor Piercing": 3})
            # variations.append({"Name": f"{school} 3 Damage, 2 Pierce, Accuracy", "Global Damage": 6, f"{school} Damage": 16, f"{school} Accuracy": 10, "Global Armor Piercing": 5})
            # variations.append({"Name": f"{school} 3 Damage, Resist, Pierce, Accuracy", "Global Damage": 6, f"{school} Damage": 16, "Global Resistance": 10, f"{school} Accuracy": 10, "Global Armor Piercing": 3})
            # variations.append({"Name": f"{school} 3 Damage, Resist, Pierce", "Global Damage": 7, f"{school} Damage": 18, "Global Resistance": 11, "Global Armor Piercing": 4})
            # variations.append({"Name": f"{school} 3 Damage, Resist, Accuracy", "Global Damage": 7, f"{school} Damage": 18, "Global Resistance": 11, f"{school} Accuracy": 10})
            # variations.append({"Name": f"{school} 3 Damage, Pierce, Accuracy", "Global Damage": 7, f"{school} Damage": 18, f"{school} Accuracy": 10, "Global Armor Piercing": 4})
    
    # Prepare a DataFrame for variations
    variations_df = pd.DataFrame(variations)
    # Explode the DataFrame by repeating each row for each variation
    exploded_df = df.loc[df.index.repeat(len(variations))].reset_index(drop=True)
    # Repeat the variations DataFrame to match exploded rows
    repeated_variations = pd.concat([variations_df] * len(df), ignore_index=True)

    # Add variation names to the 'Name' column
    exploded_df['Name'] += " (" + repeated_variations['Name'] + ")"

    # Add other stats from variations to the DataFrame
    for stat in variations_df.columns:
        if stat != "Name":
            exploded_df[stat] = exploded_df[stat].add(repeated_variations[stat], fill_value=0)

    return exploded_df

def clean_gear_df(df, curr_gear_type):
    if curr_gear_type == "Pets":
        df = create_pet_variants(remove_normal_pets(df)).reset_index(drop=True)
    df = utils.distribute_global_stats(df)
    df = utils.reorder_df_cols(df)
    df = df.sort_values(by = "Name", ascending = True).reset_index(drop=True)
    return df

def update_gear(gear_types):
    
    for curr_gear_type in gear_types:
        
        base_url = "https://wiki.wizard101central.com"
        url = f"https://wiki.wizard101central.com/wiki/Category:{curr_gear_type}"

        bullet_points = []
        
        print(f'\nCollecting {curr_gear_type}...\n')

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
        def process_bullets_multithreaded(base_url, bullet_points, curr_gear_type):
            items_data = []
            def process_and_collect(bp):
                return process_bullet_point(base_url, bp, curr_gear_type)
            with ThreadPoolExecutor() as executor:
                results = list(executor.map(process_and_collect, bullet_points))
                items_data.extend(results)
            return items_data

        # call function to multithread webscrape
        items_data = process_bullets_multithreaded(base_url, bullet_points, curr_gear_type)
        if curr_gear_type == 'Mounts': # check for mounts being None (happens when they're not permanent)
            items_data = [item for item in items_data if item is not None]
        
        # move all items to dataframe
        df = pd.DataFrame(items_data).fillna(0)  # fill all empty values with 0
        df = clean_gear_df(df, curr_gear_type)
        print(df)
        file_path = f'Gear\\All_Gear\\All_{curr_gear_type}.csv'
        try:
            df.to_csv(file_path, index=False)
        except:
            input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
            df.to_csv(file_path, index=False)

        # update all schools
        for school in utils.schools_of_items: # change this if i want to test one school
            if school != "Global":
                file_path = f'Gear\\{school}_Gear\\{school}_{curr_gear_type}.csv'
                school_df = df if curr_gear_type == "Mounts" else df[(df['School'].str.startswith('Not') & ~df['School'].str.endswith(school)) | df['School'].isin([school, 'Global'])].reset_index(drop=True)
                try:
                    school_df.to_csv(file_path, index=False)
                except:
                    input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
                    school_df.to_csv(file_path, index=False)
