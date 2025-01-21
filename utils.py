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

max_level = 170 # UPDATE WITH NEW WORLDS

def is_int(input):
    try:
        int(input)
        return True
    except:
        return False

def extract_int(str):
    num_str = []
    
    for char in str:
        if char.isdigit():
            num_str.append(char)
    
    return int("".join(num_str))

def scale_down_damage(orig_damage):
    if orig_damage >= 259:
        return 240
    elif orig_damage >= 249:
        return 239
    elif orig_damage >= 241:
        return 238
    elif orig_damage >= 237:
        return 237
    else: # soft cap is 237
        return orig_damage

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

def view_school_stats_only(school, df):
    cols_to_drop = []
    for col in df.columns:
        pot_school = col.split()[0]
        if pot_school in all_stat_schools and pot_school != school and col != "Shadow Pip Rating":
            if col == 'Global Resistance':
                cols_to_drop.append(f'{school} Resistance')
            elif col == 'Global Flat Resistance':
                cols_to_drop.append(f'{school} Flat Resistance')
            elif col == 'Global Critical Block Rating':
                cols_to_drop.append(f'{school} Critical Block Rating')
            else:
                cols_to_drop.append(col)
    df = df.drop(cols_to_drop, axis=1)
    df.columns = [col.replace(school + " ", "").replace('Global' + ' ', '') for col in df.columns]
    
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
    
    for stat in ['Power Pip Chance', 'Shadow Pip Rating', 'Archmastery Rating', 'Enchant Damage']:
        ordered_stats.append(stat)
    
    for i in reversed(range(len(ordered_stats))):
        stat_col_name = ordered_stats[i]
        if stat_col_name in df:
            stat_col_vals = df.pop(stat_col_name)
            df.insert(2, stat_col_name, stat_col_vals)
    
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