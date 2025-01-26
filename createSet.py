import sys

import pandas as pd

import utils


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
        elif school in utils.schools_of_wizards:
            return school
        else:
            print('\nInvalid input, please enter a valid school')

def select_account(set_components):
    
    while True:
        print(f"\nWhich account would you like to view this set for: {utils.accounts} Or b to go back or q to quit\n")
        
        account = input()
        
        if account.lower() == 'b':
            return
        elif account.lower() == 'q':
            sys.exit()
        elif account in utils.accounts:
            set_components['Account'] = account
            return
        else:
            print('\nInvalid input, please try again')

def get_base_values(set_components):
    
    complete_base_values = { # this comes before stats
        'Name': 'Base Values',
        'Level': set_components['Level'],
    }
    complete_base_values.update(utils.empty_stats())
    complete_base_values['School'] = set_components['School'] # this comes after stats
    
    df = pd.read_csv(f"Base_Values\\{set_components['School']}_Base_Values.csv")
    
    complete_base_values.update(df.iloc[set_components['Level'] - 1].to_dict()) # actually fill the proper base values
    
    return complete_base_values

def get_totals(items, account):
    
    totals = {
        'Name': f"{account}'s Total",
        'Level': items[-1]['Level'],
        'Enchant Damage': 0,
        'School': items[-1]['School']
    }
    
    for col in items[0]:
        if col not in {'Name', 'Level', 'Enchant Damage', 'Gear Set', 'School'}:
            total = 0
            for item in items:
                total += item[col]
            totals[col] = total
        elif col == 'Enchant Damage':
            for item in items:
                totals['Enchant Damage'] = max(totals['Enchant Damage'], item['Enchant Damage'])
        elif col == 'Gear Set':
            gear_set = ''
            for item in items:
                if item['Gear Set'] != 'No Gear Set':
                    if gear_set:
                        gear_set = f"{gear_set}, {item['Gear Set']}"
                    else:
                        gear_set = item['Gear Set']
            if gear_set:
                totals['Gear Set'] = gear_set
    # clean way to set gear sets (counting each set piece)
    totals['Gear Set'] = utils.tally_gear_sets(items)
    
    # apply set bonuses
    utils.add_set_bonuses(totals)
    
    # scale down damages
    for school in utils.schools_of_items:
        totals[f'{school} Damage'] = utils.scale_down_damage(totals[f'{school} Damage'])
    
    return totals

def school_cant_use_item(set_school, item_school):
    if item_school == set_school or item_school == 'Global':
        return False
    elif item_school.startswith("Not ") and item_school != f'Not {set_school}':
        return False
    # else
    return True

def select_socket(item, school, level, shape):
    
    df = pd.read_csv(f"Jewels\\{school}_Jewels\\{school}_{shape}_Jewels.csv")
    df = df[df['Level'] <= level]
    
    while len(df) > 20 or len(df) == 0:
        if len(df) == 0:
            print(f"\nNo {shape} Sockets have this name, resetting to the full dataframe\n")
            df = pd.read_csv(f"Jewels\\{item['School']}_Jewels\\{item['School']}_{shape}_Jewels.csv")
            df = df[df['Level'] <= level]
        else:
            print(df)
            print(f"\nEnter part of the {shape} Socket's name to filter down the dataframe, or submit nothing to select no socket, or q to quit:\n")
            name_substr = input().lower()
            if name_substr == 'q':
                sys.exit()
            elif not name_substr:
                df = df[df['Name'].str.contains("This is an impossible name to wipe the dataframe")].reset_index(drop=True)
                break
            else:
                df = df[df['Name'].str.contains(name_substr, case=False)].reset_index(drop=True)
    
    if len(df) > 0:
        data = df.to_dict('records')
        
        while True:
            
            print("\nPlease enter the number next to the item you'd like to add, or b to reset or q to quit\n")

            for i, record in enumerate(data):
                print(f"[{i}] {record['Name']} - Level {record['Level']}")
            print('')
            
            socket_i = input().lower()
            if socket_i == 'b':
                return select_socket(item, shape)
            elif socket_i == 'q':
                sys.exit()
            elif utils.is_int(socket_i):
                socket_i = int(socket_i)
                if socket_i < 0 or socket_i >= len(data):
                    print(f"\nInvalid input, please enter an integer between 0 and {len(data) - 1}")
                else:
                    added_socket_name = data[socket_i]['Name']
                    
                    # add the stats
                    # Determine the columns to sum
                    exclude_columns = {'Name', 'Level', 'School', 'Enchant Damage'}
                    columns_to_sum = [col for col in data[socket_i] if col not in exclude_columns]
                    
                    total_values = {col: item[col] for col in columns_to_sum}
                    for col in columns_to_sum:
                        total_values[col] += data[socket_i][col] # all stats get added together
                    
                    # Update the result entry with the computed totals for summable columns
                    item.update(total_values)
                    item['Enchant Damage'] = max(item['Enchant Damage'], data[socket_i]['Enchant Damage'])
                    item['Level'] = max(item['Level'], data[socket_i]['Level']) # if socket level is greater than item, update item level to match
                    
                    print(f"\nThe specified {added_socket_name} has been added\n")
                    if shape in {'Sword', 'Shield', 'Power'}:
                        return f"({utils.abbreviate_pin(shape, added_socket_name)})"
                    else:
                        return f"({utils.abbreviate_jewel(shape, added_socket_name)})"
            else:
                print(f"\nInvalid input, please enter an integer between 0 and {len(data) - 1}")
    else:
        return ''

def apply_jewels(item, school, level):
    tears = item['Unlocked Tear'] + item['Locked Tear']
    circles = item['Unlocked Circle'] + item['Locked Circle']
    squares = item['Unlocked Square'] + item['Locked Square']
    triangles = item['Unlocked Triangle'] + item['Locked Triangle']
    
    jewels_used = ''
    
    for i in range(tears):
        jewels_used += select_socket(item, school, level, 'Tear')
    for i in range(circles):
        jewels_used += select_socket(item, school, level, 'Circle')
    for i in range(squares):
        jewels_used += select_socket(item, school, level, 'Square')
    for i in range(triangles):
        jewels_used += select_socket(item, school, level, 'Triangle')
    
    item['Name'] = f"{item['Name']} {jewels_used}" if jewels_used else f"{item['Name']} (No Jewels)"
    return item

def apply_pins(item, school, level):
    swords = item['Sword Pins']
    shields = item['Shield Pins']
    powers = item['Power Pins']
    
    pins_used = ''
    
    for i in range(swords):
        pins_used += select_socket(item, school, level, 'Sword')
    for i in range(shields):
        pins_used += select_socket(item, school, level, 'Shield')
    for i in range(powers):
        pins_used += select_socket(item, school, level, 'Power')
    
    item['Name'] = f"{item['Name']} {pins_used}" if pins_used else f"{item['Name']} (No Pins)"
    return item

def add_item(school, level, gear_type):
    
    curr_gear_type = f"{gear_type}s" if gear_type != 'Boots' else gear_type
    
    df = pd.read_csv(f'Gear\\{school}_Gear\\{school}_{curr_gear_type}.csv')
    df = df[df['Level'] <= level]
    
    # narrow down the item search to 20 based on name
    while len(df) > 20 or len(df) == 0:
        if len(df) == 0:
            print(f"\nNo {curr_gear_type} have this name, resetting to the full dataframe\n")
            df = pd.read_csv(f'Gear\\{school}_Gear\\{school}_{curr_gear_type}.csv')
            df = df[df['Level'] <= level]
        else:
            print(df)
            print("\nEnter part of the item name to filter down the dataframe, or b to go back or q to quit:\n")
            name_substr = input().lower()
            if name_substr == 'b':
                return None
            elif name_substr == 'q':
                sys.exit()
            else:
                df = df[df['Name'].str.contains(name_substr, case=False)].reset_index(drop=True)
    
    data = df.to_dict('records')
    
    # select which item from the 20 remaining
    item = None
    
    while True:
        
        print("\nPlease enter the number next to the item you'd like to add, or b to reset or q to quit\n")

        for i, record in enumerate(data):
            item_info = f"[{i}] {record['Name']} - Level {record['Level']}"
            if curr_gear_type != 'Mounts':
                item_info = f"{item_info} - {record['School']}"
            print(item_info)
        print('')
        
        item_i = input().lower()
        if item_i == 'b':
            return None
        elif item_i == 'q':
            sys.exit()
        elif utils.is_int(item_i):
            item_i = int(item_i)
            if item_i < 0 or item_i >= len(data):
                print(f"\nInvalid input, please enter an integer between 0 and {len(data) - 1}")
            else:
                item = data[item_i]
                break
        else:
            print(f"\nInvalid input, please enter an integer between 0 and {len(data) - 1}")
    
    if curr_gear_type in utils.accessory_gear_types:
        item = apply_jewels(item, school, level)
    elif curr_gear_type in utils.clothing_gear_types:
        item = apply_pins(item, school, level)
    
    return item

def overwrite_cols(set_components, gear_type, new_item):
    
    for col in set_components[gear_type]:
        if col == 'Name':
            set_components[gear_type]['Name'] = new_item['Name']
        else:
            set_components[gear_type][col] = new_item[col]

def is_dragoon_hit_better(orig_damage, df):
    
    amulet_name = df.iloc[5]['Name']
    for dragoon_amulet in utils.dragoon_amulet_damages:
        if amulet_name.startswith(dragoon_amulet):
            return max(orig_damage, utils.dragoon_amulet_damages[dragoon_amulet])
    
    return orig_damage

def get_resist_multiplier(row, school_stats_only, school, resist):
    if school_stats_only:
        if row['Armor Piercing'] >= resist:
            return 1.0
        else:
            return 0.01 * (100 - (resist - row['Armor Piercing']))
    else:
        if row[f'{school} Armor Piercing'] >= resist:
            return 1.0
        else:
            return 0.01 * (100 - (resist - row[f'{school} Armor Piercing']))

def get_round_one_damage(df, mob, high_resist, set_components):
    # get enemy information
    enemy_df = pd.read_csv(f"Other_CSVs\\Enemy_Stats.csv")
    wiz_level = set_components['Level']
    enemy_df = enemy_df[(enemy_df['Low Level'] <= wiz_level) & (enemy_df['High Level'] >= wiz_level)].reset_index(drop=True)
    enemy_stats = enemy_df.iloc[0].to_dict()
    resist = 60 if high_resist else (enemy_stats['Mob Resist'] if mob else enemy_stats['Boss Resist'])
    block = enemy_stats['Mob Block'] if mob else enemy_stats['Boss Block']
    
    # get enchant
    enchant_damage = df.iloc[-1].to_dict()['Enchant Damage']
    
    # get spell damage
    spell_df = pd.read_csv(f'Other_CSVs\\AOEs.csv')
    spell_df = spell_df[(spell_df['School'] == set_components['School']) & (spell_df[f"{set_components['Account']} Owned"])].reset_index(drop=True)
    spell_df['Damage'] = spell_df.apply(
        lambda row: row['Damage'] + (enchant_damage // 2) if row['Has DOT'] else row['Damage'] + enchant_damage,
        axis=1
    )
    spell_damage = spell_df.sort_values(by='Damage', ascending=False).reset_index(drop=True).iloc[0].to_dict()['Damage']
    spell_damage = is_dragoon_hit_better(spell_damage, df)
    
    # return the formula
    if set_components['School Stats Only']:
        return ((spell_damage * (1.0 + (df['Damage'] / 100)) + df['Flat Damage']) * (1.0 + (df['Critical Rating'] / (df['Critical Rating'] + 3 * block))) * df.apply(
            get_resist_multiplier,
            axis=1,
            school_stats_only=True,
            school=set_components['School'],
            resist=resist
        )).astype(int)
    else:
        school = set_components['School']
        return int((spell_damage * (1.0 + (df[f'{school} Damage'] / 100)) + df[f'{school} Flat Damage']) * (1.0 + (df[f'{school} Critical Rating'] / (df[f'{school} Critical Rating'] + 3 * block))) * df.apply(
            get_resist_multiplier,
            axis=1,
            school_stats_only=False,
            school=school,
            resist=resist
        )).astype(int)

def add_personal_stats(df, set_components):
    if set_components['School Stats Only']:
        df['Adjusted Health'] = df['Max Health'] + (df['Resistance'] * 120)
        df['Balanced Rating'] = df['Max Health'] + (df['Resistance'] * 120) + (df['Damage'] * 120) + (df['Armor Piercing'] * 120 * 10 // 6)
        df['Mob R1 Dmg'] = get_round_one_damage(df, True, False, set_components)
        df['Mob HighRes R1 Dmg'] = get_round_one_damage(df, True, True, set_components)
        df['Boss R1 Dmg'] = get_round_one_damage(df, False, False, set_components)
    else:
        df['Adjusted Health'] = df['Max Health'] + (df['Global Resistance'] * 120)
        df['Balanced Rating'] = df['Max Health'] + (df['Global Resistance'] * 120) + (df[f"{set_components['School']} Damage"] * 120) + (df[f"{set_components['School']} Armor Piercing"] * 120 * 10 // 6)
        df['Mob R1 Dmg'] = get_round_one_damage(df, True, False, set_components)
        df['Mob HighRes R1 Dmg'] = get_round_one_damage(df, True, True, set_components)
        df['Boss R1 Dmg'] = get_round_one_damage(df, False, False, set_components)
    
    return df

def create_set():
    
    set_components = {
        'School': 'Death',
        'Level': utils.max_level,
        'Account': 'Andrew',
        'School Stats Only': True,
        'Hat': utils.empty_item('Hat'),
        'Robe': utils.empty_item('Robe'),
        'Boots': utils.empty_item('Boots'),
        'Wand': utils.empty_item('Wand'),
        'Athame': utils.empty_item('Athame'),
        'Amulet': utils.empty_item('Amulet'),
        'Ring': utils.empty_item('Ring'),
        'Pet': utils.empty_item('Pet'),
        'Mount': utils.empty_item('Mount'),
        'Deck': utils.empty_item('Deck'),
    }
    
    while True:
        
        items = []
        
        for component in set_components:
            if component not in {'School', 'Level', 'Account', 'School Stats Only'}:
                items.append(set_components[component])
        
        # add in the base values
        items.append(get_base_values(set_components))
        
        # add in the total row
        items.append(get_totals(items, set_components['Account']))
        
        df = pd.DataFrame(items)
        # df = utils.distribute_global_stats(df)
        df = utils.reorder_df_cols(df, 3)
        if set_components['School Stats Only']:
            df = utils.view_school_stats_only(set_components['School'], df)
        
        # add in personal stats
        df = add_personal_stats(df, set_components)
        
        print(df)
        
        file_path = 'CompleteW101Gear_Output.csv'
        try:
            df.to_csv(file_path, index=False)
        except:
            input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
            df.to_csv(file_path, index=False)
        
        action = input(f"\nWhat would you like to change? Enter School, Level, Account, School Stats Only, or the item (Hat, Boots, Pet, etc.) to alter the set, or b to go back or q to quit\n\n")
        action_lower = action.lower()
        
        if action_lower == 'b':
            return True
        elif action_lower == 'q':
            sys.exit()
        elif action_lower == 'school':
            new_school = select_school()
            if new_school:
                set_components['School'] = new_school
                # check to see if any items need to be removed (wrong school)
                for component in set_components:
                    if component not in {'School', 'Level', 'School Stats Only'}:
                        if school_cant_use_item(new_school, set_components[component]['School']):
                            set_components[component] = utils.empty_item(component)
                
        elif action_lower == 'level':
            new_level = select_level()
            if new_level:
                set_components['Level'] = new_level
                # check to see if any items need to be removed (item level is too high)
                for component in set_components:
                    if component not in {'School', 'Level', 'School Stats Only', 'Account'}:
                        if set_components[component]['Level'] > new_level:
                            set_components[component] = utils.empty_item(component)
        elif action_lower == 'account':
            select_account(set_components)
        elif action_lower == 'school stats only':
            set_components['School Stats Only'] = not set_components['School Stats Only']
        elif action in set_components:
            item_name = set_components[action]['Name']
            if item_name != f"No {action} Equipped":
                print(f"\nRemoving the {action} {item_name}\n")
                set_components[action] = utils.empty_item(action)
            else:
                new_item = add_item(set_components['School'], set_components['Level'], action)
                if new_item:
                    overwrite_cols(set_components, action, new_item)
        else:
            print('\nInvalid input, please try again')
