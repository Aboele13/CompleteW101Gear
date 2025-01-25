import sys
from itertools import combinations_with_replacement

import pandas as pd

import utils

all_gear_types = {'Hats', 'Robes', 'Boots', 'Wands', 'Athames', 'Amulets', 'Rings', 'Pets', 'Mounts', 'Decks'}
all_pin_shapes = ['Sword', 'Shield', 'Power']
all_jewel_shapes = ['Tear', 'Circle', 'Square', 'Triangle']

def unlock_sockets(df):
    if 'Locked Tear' in df.columns: # then all jewel columns are there
        df['Unlocked Tear'] += df['Locked Tear']
        df['Unlocked Circle'] += df['Locked Circle']
        df['Unlocked Square'] += df['Locked Square']
        df['Unlocked Triangle'] += df['Locked Triangle']
    return df

def create_jeweled_variations(df, jewels_dfs_list, jewel_index):
    if jewel_index >= len(all_jewel_shapes):
        return df
    
    combo_data = []
    items_records = df.to_dict('records')  # Convert items_df to list of dicts
    jewels_records = jewels_dfs_list[jewel_index].to_dict('records')  # Convert jewels_df to list of dicts
    curr_jewel_shape = all_jewel_shapes[jewel_index]
    
    # Determine the columns to sum
    exclude_columns = {'Name', 'Level', 'School', 'Enchant Damage'}
    columns_to_sum = [col for col in jewels_dfs_list[jewel_index].columns if col not in exclude_columns]
    
    for item in items_records:
        # Extract item attributes
        jewels_count = int(item[f'Unlocked {curr_jewel_shape}'])
        
        # Generate all combinations of jewels
        jewel_combinations = combinations_with_replacement(jewels_records, jewels_count)
        
        for combination in jewel_combinations:
            # Initialize totals with item's base values
            total_values = {col: item[col] for col in columns_to_sum}
            
            enchant_damage = item['Enchant Damage']
            
            result = item.copy()
            
            jewels_used = result['Jewels Used'] if 'Jewels Used' in result else ''
            
            for jewel in combination:
                jewels_used += f"({utils.abbreviate_jewel(curr_jewel_shape, jewel['Name'])})"
                for col in columns_to_sum:
                    total_values[col] += jewel[col] # all stats get added together
                enchant_damage = max(enchant_damage, jewel['Enchant Damage']) # except enchant damage is the maximum
            
            # Update the result entry with the computed totals for summable columns
            result.update(total_values)
            result['Enchant Damage'] = enchant_damage
            result['Jewels Used'] = jewels_used if (jewels_used or (jewel_index < len(all_jewel_shapes) - 1)) else '(No Jewels)'
            combo_data.append(result)
            
    combo_df = pd.DataFrame(combo_data)
    return create_jeweled_variations(combo_df, jewels_dfs_list, jewel_index + 1)

def create_pinned_variations(df, pins_dfs_list, pin_index):
    if pin_index >= len(all_pin_shapes):
        return df
    
    combo_data = []
    items_records = df.to_dict('records')  # Convert items_df to list of dicts
    pins_records = pins_dfs_list[pin_index].to_dict('records')  # Convert jewels_df to list of dicts
    curr_jewel_shape = all_pin_shapes[pin_index]
    
    # Determine the columns to sum
    exclude_columns = {'Name', 'Level', 'School', 'Enchant Damage'}
    columns_to_sum = [col for col in pins_dfs_list[pin_index].columns if col not in exclude_columns]
    
    for item in items_records:
        # Extract item attributes
        pins_count = int(item[f"{curr_jewel_shape} Pins"])
        
        # Generate all combinations of pins
        pin_combinations = combinations_with_replacement(pins_records, pins_count)
        
        for combination in pin_combinations:
            # Initialize totals with item's base values
            total_values = {col: item[col] for col in columns_to_sum}
            
            enchant_damage = item['Enchant Damage']
            
            result = item.copy()
            
            pins_used = result['Pins Used'] if 'Pins Used' in result else ''
            
            for pin in combination:
                pins_used += f"({utils.abbreviate_pin(curr_jewel_shape, pin['Name'])})"
                for col in columns_to_sum:
                    total_values[col] += pin[col] # all stats get added together
                enchant_damage = max(enchant_damage, pin['Enchant Damage']) # except enchant damage
            
            # Update the result entry with the computed totals for summable columns
            result.update(total_values)
            result['Enchant Damage'] = enchant_damage
            result['Pins Used'] = pins_used if (pins_used or (pin_index < len(all_pin_shapes) - 1)) else '(No Pins)'
            combo_data.append(result)
    
    combo_df = pd.DataFrame(combo_data)
    return create_pinned_variations(combo_df, pins_dfs_list, pin_index + 1)

def get_jewel_shape_df(filters, jewel_shape):
    
    df = pd.read_csv(f"Jewels\\{filters['School']}_Jewels\\{filters['School']}_{jewel_shape}_Jewels.csv")
    df = df[df['Level'] <= filters['Level']]
    
    jewels_to_keep = filters['Jeweled'][f'{jewel_shape}s']
    
    if jewel_shape in {'Sword', 'Power'}:
        # Check if any string in the set is a substring of the column value
        mask = df['Name'].apply( # sword and power should have the secondary school in there
            lambda x: any(s in x.lower() for s in jewels_to_keep) and x.lower().startswith(f"{filters['Jeweled']['Secondary School']}".lower())
        )
        df = utils.objectively_best_jewels(df[mask].reset_index(drop=True))
    elif jewel_shape == 'Shield':
        # Check if any string in the set is a substring of the column value
        mask = df['Name'].apply(
            lambda x: any(s in x.lower() for s in jewels_to_keep)
        )
        df = utils.objectively_best_jewels(df[mask].reset_index(drop=True))
        
        # get the best school for resist/blocking pins
        jewels_to_keep = {'mending'}
        ordered_damage_schools = ['storm', 'fire', 'myth', 'death', 'balance', 'life', 'ice']
        for school in ordered_damage_schools:
            if len(jewels_to_keep) > 1:
                break
            for full_jewel_name in df['Name']:
                if full_jewel_name.lower().startswith(school):
                    jewels_to_keep.add(school)
                    break
        
        # apply to limit to only one school
        mask = df['Name'].apply(
            lambda x: any(s in x.lower() for s in jewels_to_keep)
        )
        df = df[mask].reset_index(drop=True)
    else:
        # Check if any string in the set is a substring of the column value
        mask = df['Name'].apply(
            lambda x: any(s in x.lower() for s in jewels_to_keep)
        )
        df = utils.objectively_best_jewels(df[mask].reset_index(drop=True))
    
    return df

def jewel_the_items(df, filters):
    
    if filters['Gear Type'] in utils.clothing_gear_types:
        sword_pins_df = get_jewel_shape_df(filters, 'Sword')
        print(sword_pins_df) # testing
        shield_pins_df = get_jewel_shape_df(filters, 'Shield')
        print(shield_pins_df) # testing
        power_pins_df = get_jewel_shape_df(filters, 'Power')
        print(power_pins_df) # testing
        df = create_pinned_variations(df, [sword_pins_df, shield_pins_df, power_pins_df], 0)
    elif filters['Gear Type'] in utils.accessory_gear_types:
        if filters['Jeweled']['Unlock']: # unlock the sockets if specified
            df = unlock_sockets(df)
        tear_jewels_df = get_jewel_shape_df(filters, 'Tear')
        print(tear_jewels_df) # testing
        circle_jewels_df = get_jewel_shape_df(filters, 'Circle')
        print(circle_jewels_df) # testing
        square_jewels_df = get_jewel_shape_df(filters, 'Square')
        print(square_jewels_df) # testing
        triangle_jewels_df = get_jewel_shape_df(filters, 'Triangle')
        print(triangle_jewels_df) # testing
        df = create_jeweled_variations(df, [tear_jewels_df, circle_jewels_df, square_jewels_df, triangle_jewels_df], 0)
    
    return df

def add_owned_column(df, filters):
    
    gear_type = filters['Gear Type']
    socketed = 'Socketed' if 'Jeweled' in filters else 'Unsocketed'
    
    try:
        owned_df = pd.read_csv(f"Owned_Gear\\{filters['Account']}_Owned_Gear\\{filters['Account']}_{socketed}_Owned_Gear\\{filters['Account']}_{socketed}_Owned_{gear_type}.csv")
    except: # if there are no owned items, return the original df with all "Owned" as false
        df['Owned'] = False
        return df
    
    if filters['School'] != 'All':
        owned_df = owned_df[owned_df['School'] == filters['School']]
    
    if (gear_type in utils.clothing_gear_types or gear_type in utils.accessory_gear_types) and socketed == 'Socketed': # need to check both name and jewels/pins
        
        # looking for matching jewels or pins
        sockets = "Jewels" if gear_type in utils.accessory_gear_types else "Pins"
        
        # Add a key to identify matching rows based on both "Name" and "Jewels Used" or "Pins Used"
        merged_df = df.merge(owned_df, on=['Name', f'{sockets} Used'], how='left', indicator=True)
        # Update the "Owned" column: If a match is found in both columns, set to True
        df['Owned'] = merged_df['_merge'] == 'both'
        
    else: # don't need to check pins/jewels, just names
        df['Owned'] = df['Name'].isin(owned_df['Name'])
    
    return df

def view_gear():
    
    # default filters
    filters = {
        'School': 'All',
        'Gear Type': 'Hats',
        'Level': utils.max_level,
        'Account': 'Andrew',
        'Owned': False,
        'Usable In': 'Everything',
        'Objectively Best': False,
        'School Stats Only': True,
        'Good Sources': {"Gold Vendor", "Drop", "Bazaar", "Crafting", "Gold Key", "Stone Key", "Wooden Key", "Housing Gauntlet", "Rematch", "Quest", "Fishing"},
        'Bad Sources': {"One Shot Housing Gauntlet", "Raid", "Crowns", "Gift Card", "Event Drop", "Unavailable"},
    }
    
    action = 'Nothing'
    
    while True:
        
        # collect correct csv
        orig_df = pd.read_csv(f"Gear\\{filters['School']}_Gear\\{filters['School']}_{filters['Gear Type']}.csv")
        df = orig_df.copy()
        
        # filters
        stat_filters = set()
        
        for filter in filters:
            if filter == 'Level':
                df = df[df[filter] <= filters[filter]].reset_index(drop=True)
            elif filter == 'Name':
                df = df[df[filter].str.contains(filters[filter], case=False)].reset_index(drop=True)
            elif filter == 'Gear Set':
                df = df[df[filter] != 'No Gear Set'].reset_index(drop=True)
            elif filter == 'Usable In':
                battle = filters[filter]
                if battle == 'Everything':
                    df = df[df[filter] == 'Everything'].reset_index(drop=True)
                elif battle == 'PVP':
                    df = df[df[filter].isin({'Everything', 'PVP'})].reset_index(drop=True)
                elif battle == 'Deckathalon':
                    df = df[df[filter].isin({"Everything", 'Deckathalon'})].reset_index(drop=True)
            elif filter in ['School', 'Gear Type', 'Objectively Best', 'School Stats Only', 'Good Sources', 'Bad Sources', 'Jeweled', 'Account', 'Owned']:
                pass # these are handled later/elsewhere
            else:
                stat_filters.add(filter) # save for later, jeweling should come first
        
        # jewel/pin the items
        if 'Jeweled' in filters:
            df = jewel_the_items(df, filters)
        
        # add the owned column (has to be after jeweled)
        df = add_owned_column(df, filters)
        
        # filter by the owned column
        if filters['Owned']:
            df = df[df['Owned']].reset_index(drop=True)
        
        # filter by source (has to be after owned column)
        if filters['Gear Type'] != 'Pets':
            df = utils.filter_by_sources(df, filters['Good Sources']).reset_index(drop=True)
        
        # filter by minimum stat requirements (after jeweled)
        for filter in stat_filters:
            if filter in df.columns:
                df = df[df[filter] >= filters[filter]].reset_index(drop=True)
            else:
                filters.pop(filter)
        
        # school stats columns only
        if filters['School Stats Only']:
            curr_school = 'Global' if filters['School'] == 'All' else filters['School']
            df = utils.view_school_stats_only(curr_school, df)
            df = df.sort_values(by=['Damage', 'Resistance', 'Max Health', 'Critical Rating', 'Armor Piercing'], ascending=[False, False, False, False, False]).reset_index(drop=True)
        
        # only objectively best
        if filters['Objectively Best']:
            df = utils.objectively_best_gear(df, filters)
        
        # output
        file_path = 'CompleteW101Gear_Output.csv'
        try:
            df.to_csv(file_path, index=False)
        except:
            input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
            df.to_csv(file_path, index=False)
        
        # print current statuses/filters
        print() # newline for spacing
        for filter in filters:
            print(f'{filter}: {filters[filter]}')
        
        # next action
        action = input("\nWhat would you like to change? Or b to go back to the menu or q to quit\n\n")
        action_lower = action.lower()
        
        if action_lower == 'b':
            return True
        elif action_lower == 'q':
            sys.exit()
        elif action_lower == 'all':
            school = filters['School']
            gear_type = filters['Gear Type']
            account = filters['Account']
            filters = {
                'School': school,
                'Gear Type': gear_type,
                'Level': utils.max_level,
                'Account': account,
                'Owned': False,
                'Usable In': 'All',
                'Objectively Best': False,
                'School Stats Only': False,
                'Good Sources': filters['Good Sources'] | filters['Bad Sources'],
                'Bad Sources': set(),
            }
        elif action_lower == 'school':
            new_school = 'Nothing'
            print(f'\nPlease enter the new school to view, or b to go back:\n{utils.schools_of_items}\n')
            while True:
                new_school = input()
                if new_school.lower() == 'b':
                    break
                elif new_school not in utils.schools_of_items:
                    print(f'\nInvalid input, please enter a valid school from {utils.schools_of_items}, or b to go back\n')
                else:
                    filters['School'] = 'All' if new_school == 'Global' else new_school
                    if 'Jeweled' in filters:
                        if filters['School'] == 'All':
                            print(f"\nItems can not be jeweled when school is 'All'. Move into a school to jewel the items")
                            filters.pop('Jeweled')
                        else:
                            utils.set_default_jeweled(filters)
                    break
        elif action_lower == 'gear type':
            new_gear_type = 'Nothing'
            print('\nPlease enter the new gear type to view, or b to go back:\n')
            while True:
                new_gear_type = input()
                if new_gear_type.lower() == 'b':
                    break
                elif new_gear_type not in all_gear_types:
                    print('\nInvalid input, please enter a valid gear type (Hats, Robes, etc.), or b to go back\n')
                else:
                    filters['Gear Type'] = new_gear_type
                    break
        elif action_lower == 'name':
            filters['Name'] = input(f"\nSearch by name:\n\n")
        elif action_lower == 'gear set':
            if 'Gear Set' in filters:
                filters.pop('Gear Set')
            else:
                filters['Gear Set'] = True
        elif action_lower == 'account':
            account = 'Nothing'
            print(f'\nViewing the gear as which account? Select from {utils.accounts}, or b to go back or q to quit\n')
            account_options = set(utils.accounts)
            while True:
                account = input()
                if account.lower() == 'b':
                    break
                elif account.lower() == 'q':
                    sys.exit()
                elif account not in account_options:
                    print(f'\nInvalid input, please enter one of the options: {account_options}, or b to go back or q to quit\n')
                else:
                    filters['Account'] = account
                    break
        elif action_lower == 'owned':
            filters['Owned'] = not filters['Owned']
        elif action_lower == 'usable in':
            battle = 'Nothing'
            print('\nWhere should gear be usable: All, Everything, PVP, Deckathalon, or b to go back\n')
            usable_in_options = {'All', 'Everything', 'PVP', 'Deckathalon'}
            while True:
                battle = input()
                if battle.lower() == 'b':
                    break
                elif battle not in usable_in_options:
                    print(f'\nInvalid input, please enter one of the options: {usable_in_options}, or b to go back\n')
                else:
                    filters['Usable In'] = battle
                    break
        elif action_lower == 'source' or action_lower == 'good sources' or action_lower == 'bad sources':
            source = 'Nothing'
            print('\nWhich source would you like to add or remove? Enter All to add all, None to remove all, or b to go back\n')
            while True:
                source = input()
                if source.lower() == 'b':
                    break
                elif source.lower() == 'all':
                    filters['Good Sources'] = filters['Good Sources'] | filters['Bad Sources']
                    filters['Bad Sources'] = set()
                    break
                elif source.lower() == 'none':
                    filters['Bad Sources'] = filters['Good Sources'] | filters['Bad Sources']
                    filters['Good Sources'] = set()
                    break
                elif source in filters['Good Sources']:
                    filters['Good Sources'].remove(source)
                    filters['Bad Sources'].add(source)
                    break
                elif source in filters['Bad Sources']:
                    filters['Good Sources'].add(source)
                    filters['Bad Sources'].remove(source)
                    break
                else:
                    print('\nInvalid input, please enter a valid source, or b to go back:\n')
        elif action_lower == 'school stats only':
            filters['School Stats Only'] = not filters['School Stats Only']
        elif action_lower == 'objectively best':
            filters['Objectively Best'] = not filters['Objectively Best']
        elif action_lower == 'jeweled':
            utils.set_jeweled(filters)
        elif action_lower == 'level':
            num = -1
            print('\nInput the maximum level value, or b to go back\n')
            while True:
                num = input()
                if num.lower() == 'b':
                    break
                elif utils.is_int(num):
                    int_num = int(num)
                    if int_num > 0 and int_num <= utils.max_level:
                        filters['Level'] = int_num
                        if 'Jeweled' in filters:
                            utils.set_default_jeweled(filters)
                        break
                    else:
                        print(f'\nInvalid value, enter a number between 1 and {utils.max_level}, or b to go back\n')
                else:
                    print('\nInvalid value, please retry\n')
        elif action in orig_df.columns:
            num = -1
            print(f'\nInput the minimum {action} value, or b to go back\n')
            while True:
                num = input()
                if num.lower() == 'b':
                    break
                elif utils.is_int(num) and int(num) >= 0:
                    if int(num) == 0 and action in filters:
                        filters.pop(action)
                    elif int(num) != 0:
                        filters[action] = int(num)
                    break
                else:
                    print('\nInvalid value, please enter a positive number, or b to go back:\n')
        else:
            print('\nInvalid value, please retry')
