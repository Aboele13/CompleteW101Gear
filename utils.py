from bs4 import BeautifulSoup

from webAccess import fetch_url_content, replace_img_with_filename

clothing_gear_types = {"Hats", "Robes", "Boots"}
accessory_gear_types = {"Wands", "Athames", "Amulets", "Rings", "Decks"}
starting_pip_gear_types = {"Wands", "Decks"}

schools_of_items = {"Global", "Balance", "Death", "Fire", "Ice", "Life", "Myth", "Storm"}
all_stat_schools = schools_of_items | {"Shadow"}
damage_ICs = ["Epic", "Colossal", "Gargantuan", "Monstrous", "Giant", "Strong"] # UPDATE WITH NEW DAMAGE ITEM CARDS

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
            return lines[start_index:end_index], soup
        elif start_index:
            return lines[start_index:], soup
        else:
            return [], soup
    else: # this means connection failure, just retry
        return extract_item_card_info_from_url(url)

def find_next_page_link(soup):
    # Look for the "(next page)" link
    next_page_link = soup.find('a', string='next page')
    if next_page_link and 'href' in next_page_link.attrs:
        return next_page_link['href']
    return None