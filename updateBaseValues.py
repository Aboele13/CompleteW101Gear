import pandas as pd
from bs4 import BeautifulSoup

import utils
from webAccess import fetch_url_content

max_level = 170 # UPDATE WITH NEW WORLDS

def get_all_lines():
    
    url = "https://wiki.wizard101central.com/wiki/Basic:Level_Chart"
    html_content = fetch_url_content(url)
    if html_content:
        # Parse HTML content and replace <img> tags with filenames
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract all visible text from the modified HTML content
        text_content = soup.get_text(separator='\n', strip=True)
        
        lines = text_content.splitlines()
        
        lines = lines[lines.index("001"):]
        lines = lines[:lines.index("Experience")]
        
        return lines
    else: # failed to collect info from page, just retry
        return get_all_lines()
        # if this is actually broken, the page url will just be printed over and over so i know what page needs attention

def remove_mana_and_energy(all_lines):
    
    lines = all_lines[:all_lines.index("Pip Conversion")]
    
    # remove [Go to Top]
    lines_to_remove = {"[", "]", "Go to Top", "Level"}
    i = 0
    while i < len(lines):
        if lines[i] in lines_to_remove:
            lines.pop(i)
            i -= 1
        i += 1
    
    good_lines = []
    
    for j in range(len(lines)):
        if j % 13 != 8 and j % 13 != 10: # would need to get updated if new stats added
            good_lines.append(lines[j])
    
    return good_lines

def create_hp_lists(all_lines):
    
    lines = remove_mana_and_energy(all_lines)
    
    # lists (Level, Fire, Ice, Storm, Myth, Life, Death, Balance, Pip, Shad, Arch)
    lists = [[] for _ in range(11)] # would need to get updated if new stats added
    
    list_i = 0
    for line in lines:
        lists[list_i].append(line)
        list_i = list_i + 1 if list_i + 1 < len(lists) else 0
    
    return lists
    
def pip_conversion_lines(all_lines):
    pip_conv_section = all_lines[all_lines.index("Pip Conversion"):]
    return pip_conv_section[pip_conv_section.index("110"):] # would need to get updated if pip conserve given to lower wizards

def fill_zeroes(lists):
    
    for list in lists:
        while len(list) < max_level:
            list.insert(0, "0")
    
    return lists

def create_pip_conv_lists(all_lines):
    
    lines = pip_conversion_lines(all_lines)
    
    # lists (Level, Fire, Ice, Storm, Myth, Life, Death, Balance)
    lists = [[] for _ in range(8)]
    
    list_i = 0
    for line in lines:
        lists[list_i].append(line)
        list_i = list_i + 1 if list_i + 1 < len(lists) else 0
    
    lists = fill_zeroes(lists)
    
    return lists[1:]

# remove %, deal with ??? and convert to int
def clean_list(list):
    
    # make everything an int
    for i in range(len(list)):
        if "?" not in list[i]:
            list[i] = int(list[i].replace("%", ""))
            
    # average for ???
    for i in range(len(list)):
        if isinstance(list[i], str): # only str left are ???
            
            left = -1
            right = -1
            j = i - 1
            k = i + 1
            
            while j >= 0:
                if isinstance(list[j], int): # found something to the left
                    left = j
                    break
                j -= 1
            
            while k < len(list):
                if isinstance(list[k], int): # found something to the right
                    right = k
                    break
                k += 1
            
            if left == -1: # nothing found to the left, need 2 on the right
                left = right
                right = -1
                k = left + 1
                while k < len(list):
                    if isinstance(list[k], int):
                        right = k
                        break
                    k += 1
            
            if right == -1: # nothing found to the right, need 2 on the left
                right = left
                left = -1
                j = right - 1
                while j >= 0:
                    if isinstance(list[j], int):
                        left = j
                        break
                    j -= 1
            
            # both must be found by now, right >= left always
            dist = right - left
            diff = list[right] - list[left]
            avg = diff / dist
            
            if right < i: # both are less than
                list[i] = int(round(list[right] + (avg * (i - right))))
            elif left > i: # both are greater than
                list[i] = int(round(list[left] - (avg * (left - i))))
            else: # one on each side
                list[i] = int(round(list[left] + (avg * (i - left))))
    
    return list

def clean_lists(lists):
    
    for list in lists:
        list = clean_list(list)
    
    return lists

def update_base_values():
    
    all_lines = get_all_lines()
    
    lists = create_hp_lists(all_lines)
    lists.extend(create_pip_conv_lists(all_lines))
    
    [level, fire, ice, storm, myth, life, death, balance, pip, shad, arch, fire_pc, ice_pc, storm_pc, myth_pc, life_pc, death_pc, balance_pc] = clean_lists(lists)

    # columns in the base values dataframe
    data = {
        "Level": level,
        "Fire Max Health": fire,
        "Ice Max Health": ice,
        "Storm Max Health": storm,
        "Myth Max Health": myth,
        "Life Max Health": life,
        "Death Max Health": death,
        "Balance Max Health": balance,
        "Power Pip": pip,
        "Shadow Pip": shad,
        "Archmastery": arch,
        "Fire Pip Conversion Rating": fire_pc,
        "Ice Pip Conversion Rating": ice_pc,
        "Storm Pip Conversion Rating": storm_pc,
        "Myth Pip Conversion Rating": myth_pc,
        "Life Pip Conversion Rating": life_pc,
        "Death Pip Conversion Rating": death_pc,
        "Balance Pip Conversion Rating": balance_pc
    }

    # move all items to dataframe
    df = pd.DataFrame(data).fillna(0)  # fill all empty values with 0
    print(df)
    file_path = f'Base_Values\\All_Base_Values.csv'
    try:
        df.to_csv(file_path, index=False)
    except:
        input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
        df.to_csv(file_path, index=False)
    
    # create dataframes for each school
    for school in utils.schools_of_items:
        if school != "Global":
            school_df = df[["Level", f"{school} Max Health", "Power Pip", "Shadow Pip", "Archmastery", f"{school} Pip Conversion Rating"]]
            school_df = school_df.rename(columns={f"{school} Max Health": 'Max Health'})
            file_path = f'Base_Values\\{school}_Base_Values.csv'
            try:
                school_df.to_csv(file_path, index=False)
            except:
                input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
                school_df.to_csv(file_path, index=False)
