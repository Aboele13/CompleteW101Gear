from bs4 import BeautifulSoup

from webAccess import fetch_url_content, replace_img_with_filename


# drop, bazaar, gold, crowns, crafting, fishing, raid, gift card, skeleton keys, one shot, housing gauntlet, rematch, unavailable (scroll of fortune / promotion / code)
def get_item_source(item_name, formatted_info, is_mount):
    
    sources_list = []
    
    # clothes and accessories
    if not is_mount:
        sources_list = get_clothing_accessory_source(item_name, formatted_info)
    # mounts
    else:
        sources_list = get_mount_source(formatted_info)
    
    return order_sources_list(sources_list)
    
# helper function for getting source of clothing and accessories
def get_clothing_accessory_source(item_name, formatted_info):
    
    # should only return one source if raid, rematch
    if item_name in raid_gear or "The Nullity" in formatted_info:
        return ["Raid"] # raid
    if item_name in rematch_gear:
        return ["Rematch"] # rematch
    
    text = " ".join(formatted_info)
    
    # retired items can still be auctionable
    if "This item has been retired" in text:
        if "Auctionable" in formatted_info:
            return ["Bazaar"] # retired item at bazaar
        else:
            return ["Unavailable"] # retired
        
    # multiple sources
    
    sources = []
    
    # gold vendor
    if "Buy Price:" in formatted_info and "Gold" in formatted_info[formatted_info.index("Buy Price:") + 1]:
        sources.append("Gold Vendor")
        
    if "No drop sources known" not in formatted_info:
        for gold_key_source in gold_key_bosses: # dropped by gold key boss
            if gold_key_source in formatted_info:
                sources.append("Gold Key")
                break
        for stone_key_source in stone_key_bosses: # dropped by stone key boss
            if stone_key_source in formatted_info:
                sources.append("Stone Key")
                break
        for wooden_key_source in wooden_key_bosses: # dropped by wooden key boss
            if wooden_key_source in formatted_info:
                sources.append("Wooden Key")
                break
        for one_shot_source in one_shot_sources_list(): # dropped by one shot housing gauntlet source
            if one_shot_source in text:
                sources.append("One Shot Housing Gauntlet")
                break
        # any thing else is a normal drop
        if has_normal_drop(formatted_info, gold_key_bosses + stone_key_bosses + wooden_key_bosses + one_shot_sources_list()):
            sources.append("Drop")
            
    # can be bought at bazaar
    if "Auctionable" in formatted_info:
        sources.append("Bazaar")
        
    # housing gauntlet gear
    if formatted_info[-1] == "From Gauntlet":
        sources.append("Housing Gauntlet")
        if "Drop" in sources: # the drop is actually housing gauntlet, not normal
            sources.remove("Drop")
        
    # crafting
    if "Recipe:" in formatted_info or "Recipes:" in formatted_info:
        sources.append("Crafting")
        
    # locked chests (keys)
    if "Obtainable from Locked Chests in:" in text:
        idx = formatted_info.index("Obtainable from Locked Chests in:")
        if formatted_info[idx + 1] in wooden_key_chests: # wooden key chest
            sources.append("Wooden Key")
        elif formatted_info[idx + 1] in stone_key_chests: # stone key chest
            sources.append("Stone Key")
    
    
    if "Fishing Chests" in text: # fishing
        sources.append("Fishing")
    if "Card Pack" in text and "Recipe:" in text: # gold key crafting
        if "World Pack (" not in text and "Housing Gauntlet" not in sources: # world pack gear and housing gear aren't gold key gear
            sources.append("Gold Key")
    if "Card Pack" in text or "Crown Shop" in text: # card park or crown shop
        sources.append("Crowns")
    if "Gift Card" in text: # gift card
        sources.append("Gift Card")
    if "Reward From:" in formatted_info: # quest
        sources.append("Quest")
    
    # everything is added now, make final adjustments
    if len(sources) == 0: # unavailable if not found anywhere
        return ["Unavailable"]
    elif "Gold Key" in sources and "Crafting" in sources: # you can only craft with gold key reagents
        sources.remove("Crafting")
    elif "Housing Gauntlet" in sources and "Crafting" in sources: # you can only craft with gauntlet reagents
        sources.remove("Crafting")
        
    return sources
    
# helper function to get source of mounts
def get_mount_source(formatted_info):
    
    # mount can't be raid, rematch, or bazaar
    
    text = " ".join(formatted_info)
    
    # retired items can still be auctionable
    if "This item has been retired" in text:
        return ["Unavailable"] # retired
        
    # multiple sources
    
    sources = []
    
    # gold vendor
    if formatted_info[formatted_info.index("Permanent") + 1] == "Gold" or formatted_info[formatted_info.index("Permanent") + 3] == "Gold":
        sources.append("Gold Vendor")
        
    if "No drop sources known" not in formatted_info:
        for gold_key_source in gold_key_bosses: # dropped by gold key boss
            if gold_key_source in formatted_info:
                sources.append("Gold Key")
                break
        for stone_key_source in stone_key_bosses: # dropped by stone key boss
            if stone_key_source in formatted_info:
                sources.append("Stone Key")
                break
        for wooden_key_source in wooden_key_bosses: # dropped by wooden key boss
            if wooden_key_source in formatted_info:
                sources.append("Wooden Key")
                break
        for one_shot_source in one_shot_sources_list(): # dropped by one shot housing gauntlet source
            if one_shot_source in text:
                sources.append("One Shot Housing Gauntlet")
                break
        # any thing else is a normal drop
        if has_normal_drop(formatted_info, gold_key_bosses + stone_key_bosses + wooden_key_bosses + one_shot_sources_list()):
            sources.append("Drop")
        # housing gauntlet gear using " (Tier "
        if has_normal_drop(formatted_info, gold_key_bosses + stone_key_bosses + wooden_key_bosses + one_shot_sources_list(), actually_mount_from_housing=True):
            sources.append("Housing Gauntlet")
    
    # crafting
    if "Crafting Recipes" in formatted_info:
        sources.append("Crafting")
        
    # locked chests (keys)
    if "Obtainable from Locked Chests in:" in text:
        idx = formatted_info.index("Obtainable from Locked Chests in:")
        if formatted_info[idx + 1] in wooden_key_chests: # wooden key chest
            sources.append("Wooden Key")
        elif formatted_info[idx + 1] in stone_key_chests: # stone key chest
            sources.append("Stone Key")
    
    
    if "Fishing Chests" in text: # fishing
        sources.append("Fishing")
    # no gold key crafting mounts
    if "Card Packs and Bundles" in text or "Crown Shop" in text: # card park or crown shop
        sources.append("Crowns")
    if "Gift Card" in text: # gift card
        sources.append("Gift Card")
    # no permanent mounts given through quests
    
    # everything is added now, make final adjustments
    if len(sources) == 0: # unavailable if not found anywhere
        return ["Unavailable"]
    # mounts maybe can be crafted even if from gold key or housing gauntlet
        
    return sources

# ideal order
# gold, drop, bazaar, crafting, keys, housing gauntlet, rematch, quest, one shot, fishing, raid, crowns, gift card
# drop, bazaar, gold, crowns, crafting, fishing, raid, gift card, skeleton keys, one shot, housing gauntlet, rematch, unavailable
def order_sources_list(sources_list):
    
    if sources_list == ["Unavailable"]:
        return "Unavailable"
    
    # ideal order
    possible_sources = ["Gold Vendor", "Drop", "Bazaar", "Crafting", "Gold Key", "Stone Key", "Wooden Key", "Housing Gauntlet", "Rematch", "Quest", "One Shot Housing Gauntlet", "Fishing", "Raid", "Crowns", "Gift Card"]
    
    ordered_sources = [] # the reordering of sources_list
    
    for source in possible_sources:
        if source in sources_list:
            ordered_sources.append(source)
            
    return ", ".join(ordered_sources)

def has_normal_drop(formatted_info, arr, actually_mount_from_housing = False):
    
    ending_phrases = ["From Set", "Vendor", "Obtainable from", "Rewarded from", "Card Packs and Bundles", "Gift Card", "Granted by Interacting with ", "Crafting Recipe"]
    
    try:
        i = formatted_info.index("Dropped By:") + 1 # clothing and accessories
    except:
        i = formatted_info.index("Dropped by") + 1 # mounts
    
    while i < len(formatted_info) and all(end not in formatted_info[i] for end in ending_phrases): # if none of the ending phrases are the next line
        if not actually_mount_from_housing:
            if all(creature not in formatted_info[i] for creature in arr) and " (Tier " not in formatted_info[i]: # if the creature isn't anything special
                return True
        else:
            if all(creature not in formatted_info[i] for creature in arr) and " (Tier " in formatted_info[i]: # if the creature has "Tier" (from housing gauntlet)
                return True
        i += 1
        
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

# housing gauntlet names
def create_housing_gauntlet_list():
        
    gauntlet_list = []

    html_content = fetch_url_content("https://wiki.wizard101central.com/wiki/Category:Housing_Instances")
    if html_content:
        # Parse HTML content and replace <img> tags with filenames
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract all visible text from the modified HTML content
        text_content = soup.get_text(separator='\n', strip=True)
        
        lines = text_content.splitlines()
        
        for i in range(len(lines)):
            if "Location:" in lines[i]:
                gauntlet_list.append(lines[i].replace("Location:", ""))

    return clean_housing_gauntlet_list(gauntlet_list)

def create_locked_chest_list(url):
    
    chest_list = []

    html_content = fetch_url_content(url)
    if html_content:
        # Parse HTML content and replace <img> tags with filenames
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract all visible text from the modified HTML content
        text_content = soup.get_text(separator='\n', strip=True)
        
        lines = text_content.splitlines()
        
        for i in range(len(lines)):
            if "LockedChest:" in lines[i]:
                chest_list.append(lines[i].replace("LockedChest:", ""))

    return clean_housing_gauntlet_list(chest_list)

# unique list of only housing gauntlets
def clean_housing_gauntlet_list(gauntlet_list):
    
    i = 0
    
    # remove (Tier x) from all gauntlet names
    gauntlet_list = [gauntlet.split(" (Tier ")[0] for gauntlet in gauntlet_list]
    
    while i < len(gauntlet_list):
        gauntlet = gauntlet_list[i]
        if gauntlet == "TestHousingGauntlet" or (i > 0 and gauntlet == gauntlet_list[i - 1]) or (gauntlet == "Baddle of the Bands" or gauntlet == "Tanglewood Terror") or (gauntlet.split()[-1] == "Challenge" or gauntlet.split()[-1] == "Rematch"):
            gauntlet_list.pop(i)
            i -= 1
        i += 1
            
    return gauntlet_list

# gold key bosses
def gold_key_bosses_list():
    return create_creature_list("https://wiki.wizard101central.com/wiki/Category:Gold_Skeleton_Key_Bosses")

# stone key bosses
def stone_key_bosses_list():
    return create_creature_list("https://wiki.wizard101central.com/wiki/Category:Stone_Skeleton_Key_Bosses")

# stone key chests
def stone_key_chests_list():
    return create_locked_chest_list("https://wiki.wizard101central.com/wiki/Category:Stone_Skeleton_Key_Locked_Chests")

# wooden key bosses
def wooden_key_bosses_list():
    return create_creature_list("https://wiki.wizard101central.com/wiki/Category:Wooden_Skeleton_Key_Bosses")

# wooden key chests
def wooden_key_chests_list():
    return create_locked_chest_list("https://wiki.wizard101central.com/wiki/Category:Wooden_Skeleton_Key_Locked_Chests")

rematch_gear = rematch_item_list()
raid_gear = raid_item_list()
gold_key_bosses = gold_key_bosses_list()
stone_key_bosses = stone_key_bosses_list()
wooden_key_bosses = wooden_key_bosses_list()
stone_key_chests = stone_key_chests_list()
wooden_key_chests = wooden_key_chests_list()
housing_gauntlet_list = create_housing_gauntlet_list()