from bs4 import BeautifulSoup

from webAccess import fetch_url_content, replace_img_with_filename


# drop, gold, crowns, crafting, fishing, raid, gift card, keys, one shot, housing gauntlet, rematch, retired (scroll of fortune / promotion / code)
def get_item_source(item_name, formatted_info, is_mount):
    # clothes and accessories
    if not is_mount:
        return get_clothing_accessory_source(item_name, formatted_info)
    # mounts
    else:
        return get_mount_source(item_name, formatted_info)
    
# helper function for getting source of clothing and accessories
def get_clothing_accessory_source(item_name, formatted_info):
    
    if item_name in raid_gear:
        return "Raid"
    elif item_name in rematch_gear:
        return "Rematch"
    elif formatted_info[-1] == "From Gauntlet":
        return "Housing Gauntlet"
        
    text = " ".join(formatted_info)
        
    # says its retired or through quest
    if "This item has been retired" in text or "Free codes" in text or "promotional" in text or "Scroll of Fortune" in text:
        return "Unavailable"
    # can be bought for gold
    elif "Buy Price:" in formatted_info and "Gold" in formatted_info[formatted_info.index("Buy Price:") + 1]:
        return "Gold Vendor"
    # dropped by someone
    elif "No drop sources known" not in text:
        for gold_key_source in gold_key_bosses_list():
            if gold_key_source in text and only_drop_source(gold_key_source, formatted_info):
                return "Gold Key"
        for stone_key_source in stone_key_bosses_list():
            if stone_key_source in text and only_drop_source(stone_key_source, formatted_info):
                return "Stone Key"
        for wooden_key_source in wooden_key_bosses_list():
            if wooden_key_source in text and only_drop_source(wooden_key_source, formatted_info):
                return "Wooden Key"
        for one_shot_source in one_shot_sources_list():
            if one_shot_source in text and only_drop_source(one_shot_source, formatted_info):
                return "One Shot Housing Gauntlet"
        if only_drop_source("The Nullity", formatted_info):
            return "Raid"
        # other crowns items must be from Gold Key
        elif "(Tier " in text and only_drop_source(formatted_info[formatted_info.index("Dropped By:") + 1], formatted_info):
            return "Gold Key"
        # any thing else is a normal drop
        else:
            return "Drop"
    # not dropped by anyone
    else:
        if "Obtainable from Locked Chests in:" in formatted_info:
            idx = formatted_info.index("Obtainable from Locked Chests in:")
            if formatted_info[idx + 1] in wooden_key_chests_list():
                return "Wooden Key"
            elif formatted_info[idx + 1] in stone_key_chests_list():
                return "Stone Key"
        elif "Recipe" in text and "Card Pack" not in text:
            return "Crafting"
        elif "Fishing Chests" in text:
            return "Fishing"
        elif "Card Pack" in text and "Recipe:" in text:
            return "Gold Key"
        elif "Card Pack" in text or "Crown Shop" in text:
            return "Crowns"
        elif "Gift Card:" in text:
            return "Gift Card"
        
    # if it says nothing, it's retired
    return "Unavailable"
    
# helper function to get source of mounts
def get_mount_source(item_name, formatted_info):
    
    text = " ".join(formatted_info)
    
    if "This item has been retired" in text or "Free codes" in text or "promotional" in text or "Scroll of Fortune" in text:
        source = "Retired"
    elif "No drop sources known" not in text:
        if "Crafting Recipes" in text:
            source = "Crafting"
        elif "(Tier " in text or "(Rank " in text:
            source = "Gold Key/Gauntlet"
    elif "Crafting Recipes" in text:
        source = "Crafting"
    elif "Fishing Chests" in text:
        source = "Fishing"
    elif "Gift Card" in text:
        source = "Gift Card"
    elif "Card Pack" in text or "Crown Shop" in text:
        source = "Crowns"
    elif "No drop sources known" in text:
        source = "Retired"
    return source

def only_drop_source(drop_source, formatted_info):
    if drop_source in formatted_info:
        drop_source_i = formatted_info.index(drop_source)
        if formatted_info[drop_source_i - 1] != "Dropped By:":
            return False
        elif formatted_info[drop_source_i + 1] != "Obtained from Locked Chests in:" and formatted_info[drop_source_i + 1] != "Vendor Sell Price:":
            return False
        else:
            return True
    else:
        return False

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

def create_creature_list(url):
    creature_list = []

    html_content = fetch_url_content(url)
    if html_content:
        # Parse HTML content and replace <img> tags with filenames
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract all visible text from the modified HTML content
        text_content = soup.get_text(separator='\n', strip=True)
        
        lines = text_content.splitlines()
        
        for i in range(len(lines)):
            if "Creature:" in lines[i]:
                creature_list.append(lines[i].replace("Creature:", ""))

    return creature_list

# gold key bosses
def gold_key_bosses_list():
    return create_creature_list("https://wiki.wizard101central.com/wiki/Category:Gold_Skeleton_Key_Bosses")

# stone key bosses
def stone_key_bosses_list():
    return create_creature_list("https://wiki.wizard101central.com/wiki/Category:Stone_Skeleton_Key_Bosses")

# stone key chests
def stone_key_chests_list():
    return ["Castle Darkmoor"]

# wooden key bosses
def wooden_key_bosses_list():
    return create_creature_list("https://wiki.wizard101central.com/wiki/Category:Wooden_Skeleton_Key_Bosses")

# wooden key chests
def wooden_key_chests_list():
    return ["Lower Zigazag", "Main Hall", "Pagoda of Harmony"]

# housing gauntlet
def housing_gaunlet_sources_list():
    list = []
    
    return list

rematch_gear = rematch_item_list()
raid_gear = raid_item_list()

