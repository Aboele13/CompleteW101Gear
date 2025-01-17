import sys

import pandas as pd

import utils


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
    
    for stat_school in utils.all_stat_schools:
        for stat in poss_school_spec_cate:
            stats[f"{stat_school} {stat}"] = 0
    
    return stats

def empty_item(gear_type):
    item = {
        'Item': f"No {gear_type} Selected",
        'Level': 1,
        'School': 'Global',
    }
    item.update(empty_stats())
    
    return item

def select_level():
    level = 0
    
    while True:
        level = input('\nWhat level you would like to create a set for? Or b to go back or q to quit\n\n')
        level_lower = level.lower()
        
        if level_lower == 'b':
            return None
        elif level_lower == 'q':
            sys.exit()
        elif utils.is_int(level):
            level = int(level)
            if level > 0 and level <= utils.max_level:
                return level
            else:
                print(f'\nInvalid input, please enter a number between 1 and {utils.max_level}')
        else:
            print(f'\nInvalid input, please enter a number between 1 and {utils.max_level}')

def select_school():
    school = 'Nothing'
    
    while True:
        school = input('\nWhat school you would like to create a set for? Or b to go back or q to quit\n\n')
        school_lower = school.lower()
        
        if school_lower == 'b':
            return None
        elif school_lower == 'q':
            sys.exit()
        elif school in utils.schools_of_items and school != 'Global':
            return school
        else:
            print('\nInvalid input, please enter a valid school')

def get_base_values(set_components):
    
    complete_base_values = {
        'Item': 'Base Values',
        'Level': set_components['Level'],
        'School': set_components['School'],
    }
    complete_base_values.update(empty_stats())
    
    df = pd.read_csv(f"Base_Values\\{set_components['School']}_Base_Values.csv")
    
    complete_base_values.update(df.iloc[set_components['Level'] - 1].to_dict())
    
    return complete_base_values

def school_cant_use_item(set_school, item_school):
    if item_school == set_school or item_school == 'Global':
        return False
    elif item_school.startswith("Not ") and item_school != f'Not {set_school}':
        return False
    # else
    return True

def create_set():
    
    set_components = {
        'School': 'Death',
        'Level': utils.max_level,
        'School Stats Only': True,
        'Hat': empty_item('Hat'),
        'Robe': empty_item('Robe'),
        'Boots': empty_item('Boots'),
        'Wand': empty_item('Wand'),
        'Athame': empty_item('Athame'),
        'Amulet': empty_item('Amulet'),
        'Ring': empty_item('Ring'),
        'Pet': empty_item('Pet'),
        'Mount': empty_item('Mount'),
        'Deck': empty_item('Deck'),
    }
    
    while True:
        
        items = []
        
        for component in set_components:
            if component not in {'School', 'Level', 'School Stats Only'}:
                items.append(set_components[component])
        
        # add in the base values
        items.append(get_base_values(set_components))
        
        # add in the total row
        
        
        df = pd.DataFrame(items).fillna(0)
        df = utils.reorder_df_cols(df)
        if set_components['School Stats Only']:
            df = utils.view_school_stats_only(set_components['School'], df)
        
        print(df)
        
        file_path = 'CompleteW101Gear_Output.csv'
        try:
            df.to_csv(file_path, index=False)
        except:
            input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
            df.to_csv(file_path, index=False)
        
        action = input(f"\nWhat would you like to change? Enter School, Level, or the item (Hat, Boots, Pet, etc.) to alter the set, or b to go back or q to quit\n\n").lower()
        
        if action == 'b':
            return True
        elif action == 'q':
            sys.exit()
        elif action == 'school':
            new_school = select_school()
            if new_school:
                set_components['School'] = new_school
                # check to see if any items need to be removed (wrong school)
                for component in set_components:
                    if component not in {'School', 'Level', 'School Stats Only'}:
                        if school_cant_use_item(new_school, set_components[component]['School']):
                            set_components[component] = empty_item(component)
                
        elif action == 'level':
            new_level = select_level()
            if new_level:
                set_components['Level'] = new_level
                # check to see if any items need to be removed (item level is too high)
                for component in set_components:
                    if component not in {'School', 'Level', 'School Stats Only'}:
                        if set_components[component]['Level'] > new_level:
                            set_components[component] = empty_item(component)
        elif (action in [component.lower() for component in set_components]) and (action not in {'base values', 'total'}):
            print(f'\nAltering {action}')
        else:
            print('\nInvalid input, please try again')
