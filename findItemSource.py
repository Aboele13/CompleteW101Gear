from bs4 import BeautifulSoup

from webAccess import fetch_url_content, replace_img_with_filename


def get_item_source(item_name, formatted_info):
    
    if item_name in raid_gear:
        return "Raid"
    elif item_name in rematch_gear:
        return "Rematch"
    
    text = " ".join(formatted_info)
    
    if "This item has been retired" in text:
        return "Retired"
    # dropped by someone
    elif "No drop sources known" not in text:
        for one_shot_source in one_shot_sources_list():
            if one_shot_source in text:
                return "One Shot Housing Gauntlet"
        if "The Nullity" in formatted_info:
            return "Raid"
        # this still needs to get looked at
        elif "(Tier " in text:
            return "Gold Key/Gauntlet"
    # not dropped by anyone
    else:
        if "Recipe:" in text and "Card Pack" not in text:
            return "Crafting"
        elif "Fishing Chests" in text:
            return "Fishing"
        elif "Card Pack" in text and "Recipe:" in text:
            return "Gold Key/Gauntlet"
        elif "Card Pack" in text or "Crown Shop" in text:
            return "Crowns"
        elif "Gift Card:" in text:
            return "Gift Card"
    return "Drop/Vendor"

# one shot dungeons (exalted, baddle of the bands, etc.)
def one_shot_sources_list():
    return ["Krokopatra (Rank ", "Rattlebones (Rank ", "Meowiarty (Rank ", "Zeus Sky Father (Zeus ", "Patt Minotaur (Tier ", "Forest Grump (Tier "]

# rematch duels
def rematch_item_list():
    rematch_items = []

    url = "https://wiki.wizard101central.com/wiki/NPC:Raquel"
        
    html_content = fetch_url_content(url)
    if html_content:
        # Parse HTML content and replace <img> tags with filenames
        soup = BeautifulSoup(html_content, 'html.parser')
        soup = replace_img_with_filename(soup)
        
        # Extract all visible text from the modified HTML content
        text_content = soup.get_text(separator='\n', strip=True)
        
        lines = text_content.splitlines()
            
        for i in range(len(lines)):
            if lines[i] == "Link to Item":
                rematch_items.append(lines[i - 2])
                
    # remove all the gauntlet recipes at the bottom, only keep gear
    i = len(rematch_items) - 1
    while i >= 0:
        if " Recharge" in list[i] or " Rematch" in list[i]:
            rematch_items.pop()
            i -= 1
        else:
            break
    
    return rematch_items

# raid gear that can be crafted or dropped by nullity
def raid_item_list():
    raid_gear = []
    
    urls = [
        "https://wiki.wizard101central.com/wiki/NPC:Gwyn_Fellwarden",
        "https://wiki.wizard101central.com/wiki/NPC:Gwyn_Fellwarden_(Crying_Sky_Raid)",
        "https://wiki.wizard101central.com/wiki/NPC:Gwyn_Fellwarden_(Cabal%27s_Revenge_Raid)"
    ]
        
    for url in urls:
        html_content = fetch_url_content(url)
        if html_content:
            # Parse HTML content and replace <img> tags with filenames
            soup = BeautifulSoup(html_content, 'html.parser')
            soup = replace_img_with_filename(soup)
        
            # Extract all visible text from the modified HTML content
            text_content = soup.get_text(separator='\n', strip=True)
        
            lines = text_content.splitlines()
            
            for i in range(len(lines)):
                if lines[i] == "Link to Item":
                    raid_gear.append(lines[i - 2])
    
    return raid_gear

# gold key bosses
def gold_key_sources_list():
    list = []
    
    return list

# housing gauntlet
def housing_gaunlet_sources_list():
    list = []
    
    return list

rematch_gear = rematch_item_list()
raid_gear = raid_item_list()

