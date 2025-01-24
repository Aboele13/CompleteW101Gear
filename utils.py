import pandas as pd
from bs4 import BeautifulSoup

from webAccess import fetch_url_content, replace_img_with_filename

clothing_gear_types = {"Hats", "Robes", "Boots"}
accessory_gear_types = {"Wands", "Athames", "Amulets", "Rings", "Decks"}
starting_pip_gear_types = {"Wands", "Decks"}

all_gear_types_list = ['Hats', 'Robes', 'Boots', 'Wands', 'Athames', 'Amulets', 'Rings', 'Pets', 'Mounts', 'Decks']
all_jewel_shapes_list = ['Tear', 'Circle', 'Square', 'Triangle', 'Sword', 'Shield', 'Power']

schools_of_wizards = {"Balance", "Death", "Fire", "Ice", "Life", "Myth", "Storm"}
schools_of_items = schools_of_wizards | {"Global"}
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

def get_perfect_acc(school):
    school_to_acc = {
        'Death': 20,
        'Fire': 30,
        'Balance': 20,
        'Myth': 25,
        'Storm': 35,
        'Ice': 25,
        'Life': 15
    }
    return school_to_acc[school]

def empty_stats():
    
    stats = {
        'Max Health': 0,
        'Power Pip Chance': 0,
        'Stun Resistance': 0,
        'Incoming Healing': 0,
        'Outgoing Healing': 0,
        'Shadow Pip Rating': 0,
        'Archmastery Rating': 0,
        'Enchant Damage': 0,
        'Gear Set': 'No Gear Set',
    }
    
    poss_school_spec_cate = ["Damage", "Resistance", "Accuracy", "Critical Rating", "Critical Block Rating", "Armor Piercing", "Pip Conversion Rating", "Flat Damage", "Flat Resistance"]
    
    for stat_school in all_stat_schools:
        for stat in poss_school_spec_cate:
            stats[f"{stat_school} {stat}"] = 0
    
    return stats

def empty_item(gear_type):
    item = { # these come before stats
        'Name': f"No {gear_type} Equipped",
        'Level': 1,
    }
    item.update(empty_stats())
    item['School'] = 'Global' # school after stats
    
    return item

def objectively_best_gear(df, filters):
    # Identify the columns to compare
    bad_cols = {"Name", "Level", "Source", "Gear Set", "Usable In", "School", "Owned"}
    if "Jeweled" in filters: # if items are already jeweled, the number of sockets doesn't matter
        bad_cols = bad_cols | {'Sword Pins', 'Shield Pins', 'Power Pins', 'Unlocked Tear', 'Unlocked Circle', 'Unlocked Square', 'Unlocked Triangle', 'Locked Tear', 'Locked Circle', 'Locked Square', 'Locked Triangle'}
    cols_to_compare = [col for col in df.columns if col not in bad_cols]
    remove_records = set()

    # Convert DataFrame to numpy for faster row-wise operations
    data = df.to_dict('records')

    for i, row1 in enumerate(data):
        if i in remove_records:
            continue  # Skip rows that are already marked for removal
        for j, row2 in enumerate(data[i + 1:], start=i + 1):
            if j in remove_records:
                continue

            # Initial flags
            i_stays, j_stays = False, False

            # Compare gear sets
            if row1['Gear Set'] != 'No Gear Set' and row1['Gear Set'] != row2['Gear Set']:
                i_stays = True
            if row2['Gear Set'] != 'No Gear Set' and row1['Gear Set'] != row2['Gear Set']:
                j_stays = True

            # Compare usability
            if row1['Usable In'] == 'Everything' and row2['Usable In'] != 'Everything':
                i_stays = True
            if row2['Usable In'] == 'Everything' and row1['Usable In'] != 'Everything':
                j_stays = True

            # Compare numeric stats
            for col in cols_to_compare:
                if not i_stays and row1[col] > row2[col]:
                    i_stays = True
                if not j_stays and row1[col] < row2[col]:
                    j_stays = True
                if i_stays and j_stays:
                    break

            # Mark rows for removal based on comparisons
            if not i_stays and not j_stays:
                # if not row1["Owned"] and row2["Owned"]: # you only own the second one, so remove the first
                #     remove_records.add(i)
                #     break
                # else: # you own the first, both, or neither, so get rid of the second one
                    remove_records.add(j)
            elif not i_stays:
                remove_records.add(i)
                break
            elif not j_stays:
                remove_records.add(j)

    # Return the filtered DataFrame
    return df.drop(remove_records).reset_index(drop=True)

def objectively_best_jewels(df):
    # Identify the columns to compare
    cols_to_compare = [col for col in df.columns if col not in {"Name", "Level", "School"}]
    remove_records = set()

    # Convert DataFrame to numpy for faster row-wise operations
    data = df.to_dict('records')

    for i, row1 in enumerate(data):
        if i in remove_records:
            continue  # Skip rows that are already marked for removal
        for j, row2 in enumerate(data[i + 1:], start=i + 1):
            if j in remove_records:
                continue

            # Initial flags
            i_stays, j_stays = False, False

            # Compare numeric stats
            for col in cols_to_compare:
                if not i_stays and row1[col] > row2[col]:
                    i_stays = True
                if not j_stays and row1[col] < row2[col]:
                    j_stays = True
                if i_stays and j_stays:
                    break

            # Mark rows for removal based on comparisons
            if not j_stays: # 2nd is worse or equal
                remove_records.add(j)
            elif not i_stays:
                remove_records.add(i)
                break

    # Return the filtered DataFrame
    return df.drop(remove_records).reset_index(drop=True)

def match_default_jewel_school(filters): # get school specific circle and triangle jewels
    school_to_jewel = {
        'Death': 'Onyx',
        'Fire': 'Ruby',
        'Balance': 'Citrine',
        'Myth': 'Peridot',
        'Storm': 'Amethyst',
        'Ice': 'Sapphire',
        'Life': 'Jade',
        'All': 'Opal'
    }
    
    # circle jewels
    df = pd.read_csv(f"Jewels\\{filters['School']}_Jewels\\{filters['School']}_Circle_Jewels.csv")
    # damage uses primary school and level
    if 'damage' in filters['Jeweled']['Circles']:
        filters['Jeweled']['Circles'].remove('damage')
        damage_percent_jewels_df = df[(df['Name'].str.contains(f"Damage {school_to_jewel[filters['School']]}")) & (df['Name'].str.extract(f"({filters['School']})").notnull().any(axis=1))].reset_index(drop=True)
        if len(damage_percent_jewels_df) > 0 and filters['Level'] >= max_level:
            filters['Jeweled']['Circles'].add(objectively_best_jewels(damage_percent_jewels_df).iloc[0]['Name'].lower())
        else:
            filters['Jeweled']['Circles'].add(f"damage {school_to_jewel[filters['School']].lower()}")
    
    # pierce needs secondary school
    if 'piercing' in filters['Jeweled']['Circles']:
        sec_school_pierce_df = df[(df[f"{filters['Jeweled']['Secondary School']} Armor Piercing"] > 0) & (df[f"{filters['School']} Armor Piercing"] > 0) & (df['Global Armor Piercing'] == 0)].reset_index(drop=True)
        if len(sec_school_pierce_df) > 0:
            name = sec_school_pierce_df.iloc[0]['Name'].split()[0]
            filters['Jeweled']['Circles'].remove('piercing')
            filters['Jeweled']['Circles'].add(f'{name.lower()} piercing')
        else:
            filters['Jeweled']['Circles'].remove('piercing')
            filters['Jeweled']['Circles'].add(f"piercing {school_to_jewel[filters['School']].lower()}")
    
    # triangle jewels
    # accuracy just uses primary school
    if 'accurate' in filters['Jeweled']['Triangles']:
        filters['Jeweled']['Triangles'].remove('accurate')
        filters['Jeweled']['Triangles'].add(f"accurate {school_to_jewel[filters['School']].lower()}")

def set_default_jeweled(filters):
    def_sec_school = 'Life' if filters['School'] != 'Life' else 'Death'
    filters['Jeweled'] = {
        'Unlock': True,
        'Secondary School': def_sec_school,
        'Tears': {'health'} if filters['Level'] >= 50 else {'health', 'archmastery'},
        'Circles': {'damage', 'piercing'},
        'Squares': {'health'} if filters['Level'] >= max_level else {'defense opal'},
        'Triangles': {'accurate', 'pip opal'} | set([item_card.lower() for item_card in damage_ICs]),
        'Swords': {'disabling'},
        'Shields': {'resist'},
        'Powers': {'accurate'}
    }
    match_default_jewel_school(filters)

def set_jeweled(filters):
    if filters['School'] == 'All':
        print(f"\nItems can not be jeweled when school is 'All'. Move into a school to jewel the items")
        if 'Jeweled' in filters:
            filters.pop('Jeweled')
        return
    if 'Jeweled' in filters:
        remove = 'Nothing'
        print('\nThere are already Jeweled specifications, would you like to remove them? (Y/n), or b to go back\n')
        while True:
            remove = input().lower()
            if remove == 'y':
                filters.pop('Jeweled')
                return
            elif remove == 'n':
                modify_jeweled(filters)
                return
            elif remove == 'b':
                return
            else:
                print('\nInvalid input, please enter Y to remove, n to modify, or b to go back\n:')
    else:
        modify_jeweled(filters)

def set_unlock(jeweled_dict):
    unlock = 'Nothing'
    curr_value = f"Curr value: {jeweled_dict['Unlock']}. " if 'Unlock' in jeweled_dict else ""
    print(f'\nWhat should be the Unlock value? {curr_value}Enter True or False, or b to go back\n')
    while True:
        unlock = input().lower()
        if unlock == 'true':
            jeweled_dict['Unlock'] = True
            return False
        elif unlock == 'false':
            jeweled_dict['Unlock'] = False
            return False
        elif unlock == 'b':
            return True
        else:
            print('\nInvalid input, please enter True for unlocked, False for locked, or b to go back/cancel:\n')

def set_secondary_school(jeweled_dict, filters):
    sec_school = 'Nothing'
    curr_value = f"Curr value: {jeweled_dict['Secondary School']}. " if 'Secondary School' in jeweled_dict else ""
    print(f'\nWhat will be the secondary school? {curr_value}Or b to go back/cancel\n')
    while True:
        sec_school = input()
        if sec_school == filters['School']:
            print("\nThe secondary school can't be the same as the primary school. Please try again\n")
        elif sec_school in schools_of_wizards:
            jeweled_dict['Secondary School'] = sec_school
            return False
        elif sec_school.lower() == 'b':
            return True
        else:
            print("\nInvalid input, please try again with a valid school\n")

def set_tear_jewels(jeweled_dict):
    tears = set()
    curr_value = f"Curr value: {jeweled_dict['Tears']}. " if 'Tears' in jeweled_dict else ""
    print(f'\nEnter Tear Jewel names to keep, one at a time. When finished, submit an empty string, or b to go back/cancel. {curr_value}\n')
    while True:
        jewel = input().lower()
        if jewel == 'b':
            return True
        elif jewel:
            tears.add(jewel)
        else:
            jeweled_dict['Tears'] = tears
            return False

def set_circle_jewels(jeweled_dict):
    circles = set()
    curr_value = f"Curr value: {jeweled_dict['Circles']}. " if 'Circles' in jeweled_dict else ""
    print(f'\nEnter Circle Jewel names to keep, one at a time. When finished, submit an empty string, or b to go back/cancel. {curr_value}\n')
    while True:
        jewel = input().lower()
        if jewel == 'b':
            return True
        elif jewel:
            circles.add(jewel)
        else:
            jeweled_dict['Circles'] = circles
            return False

def set_square_jewels(jeweled_dict):
    squares = set()
    curr_value = f"Curr value: {jeweled_dict['Squares']}. " if 'Squares' in jeweled_dict else ""
    print(f'\nEnter Square Jewel names to keep, one at a time. When finished, submit an empty string, or b to go back/cancel. {curr_value}\n')
    while True:
        jewel = input().lower()
        if jewel == 'b':
            return True
        elif jewel:
            squares.add(jewel)
        else:
            jeweled_dict['Squares'] = squares
            return False

def set_triangle_jewels(jeweled_dict):
    triangles = set()
    curr_value = f"Curr value: {jeweled_dict['Triangles']}. " if 'Triangles' in jeweled_dict else ""
    print(f'\nEnter Triangle Jewel names to keep, one at a time. When finished, submit an empty string, or b to go back/cancel. {curr_value}\n')
    while True:
        jewel = input().lower()
        if jewel == 'b':
            return True
        elif jewel:
            triangles.add(jewel)
        else:
            jeweled_dict['Triangles'] = triangles
            return False

def set_sword_pins(jeweled_dict):
    swords = set()
    curr_value = f"Curr value: {jeweled_dict['Swords']}. " if 'Swords' in jeweled_dict else ""
    print(f'\nEnter Sword Pin names to keep, one at a time. When finished, submit an empty string, or b to go back/cancel. {curr_value}\n')
    while True:
        pin = input().lower()
        if pin == 'b':
            return True
        elif pin:
            swords.add(pin)
        else:
            jeweled_dict['Swords'] = swords
            return False

def set_shield_pins(jeweled_dict):
    shields = set()
    curr_value = f"Curr value: {jeweled_dict['Shields']}. " if 'Shields' in jeweled_dict else ""
    print(f'\nEnter Shield Pin names to keep, one at a time. When finished, submit an empty string, or b to go back/cancel. {curr_value}\n')
    while True:
        pin = input().lower()
        if pin == 'b':
            return True
        elif pin:
            shields.add(pin)
        else:
            jeweled_dict['Shields'] = shields
            return False

def set_power_pins(jeweled_dict):
    powers = set()
    curr_value = f"Curr value: {jeweled_dict['Powers']}. " if 'Powers' in jeweled_dict else ""
    print(f'\nEnter Power Pin names to keep, one at a time. When finished, submit an empty string, or b to go back/cancel. {curr_value}\n')
    while True:
        pin = input().lower()
        if pin == 'b':
            return True
        elif pin:
            powers.add(pin)
        else:
            jeweled_dict['Powers'] = powers
            return False

def modify_jeweled(filters):
    
    default = 'Nothing'
    print('\nWould you like to accept the default jewel values? (Y/n) or b to go back\n')
    while True:
        default = input().lower()
        if default == 'y':
            set_default_jeweled(filters)
            return
        elif default == 'n':
            jeweled_dict = filters['Jeweled'] if 'Jeweled' in filters else {}
            
            if set_unlock(jeweled_dict):
                return
            if set_secondary_school(jeweled_dict, filters):
                return
            if set_tear_jewels(jeweled_dict):
                return
            if set_circle_jewels(jeweled_dict):
                return
            if set_square_jewels(jeweled_dict):
                return
            if set_triangle_jewels(jeweled_dict):
                return
            if set_sword_pins(jeweled_dict):
                return
            if set_shield_pins(jeweled_dict):
                return
            if set_power_pins(jeweled_dict):
                return
            filters['Jeweled'] = jeweled_dict
            return
        elif default == 'b':
            return
        else:
            print('\nInvalid input, please enter Y for default, n to set your own, or b to go back\n')

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