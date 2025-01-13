from bs4 import BeautifulSoup

from webAccess import fetch_url_content, replace_img_with_filename

clothing_gear_types = {"Hats", "Robes", "Boots"}
accessory_gear_types = {"Wands", "Athames", "Amulets", "Rings", "Decks"}
starting_pip_gear_types = {"Wands", "Decks"}

all_gear_types_list = ['Hats', 'Robes', 'Boots', 'Wands', 'Athames', 'Amulets', 'Rings', 'Pets', 'Mounts', 'Decks']
all_jewel_shapes_list = ['Tear', 'Circle', 'Square', 'Triangle', 'Sword', 'Shield', 'Power']

schools_of_items = {"Global", "Balance", "Death", "Fire", "Ice", "Life", "Myth", "Storm"}
all_stat_schools = schools_of_items | {"Shadow"}
damage_ICs = ["Epic", "Colossal", "Gargantuan", "Monstrous", "Giant", "Strong"] # UPDATE WITH NEW DAMAGE ITEM CARDS

accounts = ['Andrew', 'Chris', 'Tessa']

def is_int(input):
    try:
        int(input)
        return True
    except:
        return False

# [Ter, Cir, Sqr, Tri], [Hlt, Res, Dmg, Prc, Acc, Pip, DIC, Blk, Cnv, Stn, Out, Inc, OIC, Arc]
def abbreviate_jewel(shape, jewel_name):
    shape_to_abbr = {
        'Tear': 'Ter',
        'Circle': 'Cir',
        'Square': 'Sqr',
        'Triangle': 'Tri',
    }
    
    jewel_name = jewel_name.lower()
    
    if "health" in jewel_name and shape != 'Triangle':
        return f"{shape_to_abbr[shape]}Hlt"
    elif "defense" in jewel_name:
        return f"{shape_to_abbr[shape]}Res"
    elif "damage" in jewel_name and shape == 'Circle':
        return f"{shape_to_abbr[shape]}Dmg"
    elif "piercing" in jewel_name:
        return f"{shape_to_abbr[shape]}Prc"
    elif "accurate" in jewel_name:
        return f"{shape_to_abbr[shape]}Acc"
    elif "conversion" in jewel_name:
        return f"{shape_to_abbr[shape]}Cnv"
    elif "resilient" in jewel_name:
        return f"{shape_to_abbr[shape]}Stn"
    elif "archmastery" in jewel_name:
        return f"{shape_to_abbr[shape]}Arc"
    elif "blocking" in jewel_name:
        return f"{shape_to_abbr[shape]}Blk"
    elif "mending" in jewel_name:
        return f"{shape_to_abbr[shape]}Out"
    elif "healing" in jewel_name:
        return f"{shape_to_abbr[shape]}Inc"
    elif any(damage_IC.lower() in jewel_name for damage_IC in damage_ICs):
        return f"{shape_to_abbr[shape]}DIC"
    elif "pip" in jewel_name:
        return f"{shape_to_abbr[shape]}Pip"
    else:
        return f"{shape_to_abbr[shape]}OIC"

# [Swd, Shd, Pow], [Dis, Csh, Pun, Blk, Res, Mnd, Acc, Cnv]
def abbreviate_pin(shape, pin_name):
    shape_to_abbr = {
        'Sword': 'Swd',
        'Shield': 'Shd',
        'Power': 'Pwr',
    }
    
    pin_name = pin_name.lower()
    
    if "disabling" in pin_name:
        return f"{shape_to_abbr[shape]}Dis"
    elif "crushing" in pin_name:
        return f"{shape_to_abbr[shape]}Csh"
    elif "punishing" in pin_name:
        return f"{shape_to_abbr[shape]}Pun"
    elif "blocking" in pin_name:
        return f"{shape_to_abbr[shape]}Blk"
    elif "resist" in pin_name:
        return f"{shape_to_abbr[shape]}Res"
    elif "mending" in pin_name:
        return f"{shape_to_abbr[shape]}Mnd"
    elif "accurate" in pin_name:
        return f"{shape_to_abbr[shape]}Acc"
    elif "conversion" in pin_name:
        return f"{shape_to_abbr[shape]}Cnv"
    else:
        return f"{shape_to_abbr[shape]}Oth"

def print_gear_type_options():
    for i in range(len(all_gear_types_list)):
        print(f"[{(i + 1) % 10}] {all_gear_types_list[i]}")
    print("")

def distribute_global_stats(df):
    schools = {"Balance", "Death", "Fire", "Ice", "Life", "Myth", "Storm", "Shadow"}
    
    col_headers = df.columns.tolist()
    
    for col_header in col_headers:
        split_ret = col_header.split('Global ')
        if len(split_ret) > 1:
            for school in schools:
                df[school + ' ' + split_ret[1]] += df[col_header]
    
    return df

def reorder_df_cols(df): # health, damage, flat damage, resist, flat resist, accuracy, critical, critical block, pierce, stun resist, incoming, outgoing, pip conserve, power pip, shadow pip, archmastery
    
    ordered_stats = ['Max Health']
    schools = ['Global', 'Fire', 'Ice', 'Storm', 'Myth', 'Life', 'Death', 'Balance', 'Shadow']
    
    for stat in ['Damage', 'Flat Damage', 'Resistance', 'Flat Resistance', 'Accuracy', 'Critical Rating', 'Critical Block Rating', 'Armor Piercing']:
        for school in schools:
            ordered_stats.append(school + " " + stat)
    
    for stat in ['Stun Resistance', 'Incoming Healing', 'Outgoing Healing']:
        ordered_stats.append(stat)
    
    for school in schools:
        ordered_stats.append(school + " Pip Conversion Rating")
    
    for stat in ['Power Pip Chance', 'Shadow Pip Rating', 'Archmastery Rating']:
        ordered_stats.append(stat)
    
    for i in reversed(range(len(ordered_stats))):
        stat_col = df.pop(ordered_stats[i])
        df.insert(2, ordered_stats[i], stat_col)
    
    return df

def extract_item_card_info_from_url(url):
    html_content = fetch_url_content(url)
    if html_content:
        # Parse HTML content and replace <img> tags with filenames
        soup = BeautifulSoup(html_content, 'html.parser')
        soup = replace_img_with_filename(soup)
        # Extract all visible text from the modified HTML content
        text_content = soup.get_text(separator='\n', strip=True)
        lines = text_content.splitlines()
        # Extract content between "ItemCard:" and "Documentation on how to edit this page"
        start_index = None
        end_index = None
        for i, line in enumerate(lines):
            if line.startswith("ItemCard:"):
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
    else: # this means connection failure, just retry
        return extract_item_card_info_from_url(url)

def find_next_page_link(soup):
    # Look for the "(next page)" link
    next_page_link = soup.find('a', string='next page')
    if next_page_link and 'href' in next_page_link.attrs:
        return next_page_link['href']
    return None