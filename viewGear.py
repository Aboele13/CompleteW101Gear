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
        df = df.drop(['Locked Tear', 'Locked Circle', 'Locked Square', 'Locked Triangle'], axis=1)
    return df

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

def create_jeweled_variations(df, jewels_dfs_list, jewel_index):
    if jewel_index >= len(all_jewel_shapes):
        return df
    
    combo_data = []
    items_records = df.to_dict('records')  # Convert items_df to list of dicts
    jewels_records = jewels_dfs_list[jewel_index].to_dict('records')  # Convert jewels_df to list of dicts
    curr_jewel_shape = f'Unlocked {all_jewel_shapes[jewel_index]}'
    
    # Determine the columns to sum
    exclude_columns = {'Name', 'Level', 'School', 'Enchant Damage'}
    columns_to_sum = [col for col in jewels_dfs_list[jewel_index].columns if col not in exclude_columns]
    
    for item in items_records:
        # Extract item attributes
        jewels_count = int(item[curr_jewel_shape])
        
        # Generate all combinations of jewels
        jewel_combinations = combinations_with_replacement(jewels_records, jewels_count)
        
        for combination in jewel_combinations:
            # Initialize totals with item's base values
            total_values = {col: item[col] for col in columns_to_sum}
            
            enchant_damage = item['Enchant Damage']
            
            result = item.copy()
            
            for jewel in combination:
                for col in columns_to_sum:
                    total_values[col] += jewel[col] # all stats get added together
                enchant_damage = max(enchant_damage, jewel['Enchant Damage']) # except enchant damage is the maximum
            
            # Update the result entry with the computed totals for summable columns
            result.update(total_values)
            result['Enchant Damage'] = enchant_damage
            combo_data.append(result)
            
    combo_df = pd.DataFrame(combo_data)
    return create_jeweled_variations(combo_df, jewels_dfs_list, jewel_index + 1)

def create_pinned_variations(df, pins_dfs_list, pin_index):
    if pin_index >= len(all_pin_shapes):
        return df
    
    combo_data = []
    items_records = df.to_dict('records')  # Convert items_df to list of dicts
    pins_records = pins_dfs_list[pin_index].to_dict('records')  # Convert jewels_df to list of dicts
    curr_jewel_shape = f'{all_pin_shapes[pin_index]} Pins'
    
    # Determine the columns to sum
    exclude_columns = {'Name', 'Level', 'School', 'Enchant Damage'}
    columns_to_sum = [col for col in pins_dfs_list[pin_index].columns if col not in exclude_columns]
    
    for item in items_records:
        # Extract item attributes
        pins_count = int(item[curr_jewel_shape])
        
        # Generate all combinations of pins
        pin_combinations = combinations_with_replacement(pins_records, pins_count)
        
        for combination in pin_combinations:
            # Initialize totals with item's base values
            total_values = {col: item[col] for col in columns_to_sum}
            
            enchant_damage = item['Enchant Damage']
            
            result = item.copy()
            
            for pin in combination:
                for col in columns_to_sum:
                    total_values[col] += pin[col] # all stats get added together
                enchant_damage = max(enchant_damage, pin['Enchant Damage']) # except enchant damage
            
            # Update the result entry with the computed totals for summable columns
            result.update(total_values)
            result['Enchant Damage'] = enchant_damage
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
        df = objectively_best_jewels(df[mask].reset_index(drop=True))
    elif jewel_shape == 'Shield':
        # Check if any string in the set is a substring of the column value
        mask = df['Name'].apply(
            lambda x: any(s in x.lower() for s in jewels_to_keep)
        )
        df = objectively_best_jewels(df[mask].reset_index(drop=True))
        
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
        df = objectively_best_jewels(df[mask].reset_index(drop=True))
    
    return df

def jewel_the_items(df, filters):
    
    # unlock the sockets if specified
    if filters['Jeweled']['Unlock']:
        df = unlock_sockets(df)
    
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

def objectively_best_gear(df):
    # Identify the columns to compare
    cols_to_compare = [col for col in df.columns if col not in {"Name", "Level", "Source", "Gear Set", "Usable In", "School"}]
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
                continue  # Both stay for now
            elif not i_stays:
                remove_records.add(i)
                break
            elif not j_stays:
                remove_records.add(j)

    # Return the filtered DataFrame
    return df.drop(remove_records).reset_index(drop=True)

def filter_by_sources(df, good_sources):
    
    def check_sources(item_sources):
        item_sources_list = [source.strip() for source in item_sources.split(',')]
        for item_source in item_sources_list:
            if item_source in good_sources:
                return True
        return False

    df['match'] = df['Source'].apply(check_sources)
    df = df[df['match']]
    return df.drop('match', axis=1).reset_index(drop=True)

def is_int(input):
    try:
        int(input)
        return True
    except:
        return False

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
        elif sec_school == 'Global':
            print("\nGlobal can't be a secondary school. Please try again with a valid school\n")
        elif sec_school in utils.schools_of_items:
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
        if len(damage_percent_jewels_df) > 0 and filters['Level'] >= 170:
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
    def_sec_school = 'Life' if filters['School'] != 'Life' else 'Storm'
    filters['Jeweled'] = {
        'Unlock': True,
        'Secondary School': def_sec_school,
        'Tears': {'health'},
        'Circles': {'damage', 'piercing'},
        'Squares': {'health'} if filters['Level'] >= 170 else {'defense opal'},
        'Triangles': {'accurate', 'pip opal'} | set([item_card.lower() for item_card in utils.damage_ICs]),
        'Swords': {'disabling'},
        'Shields': {'resist'},
        'Powers': {'accurate'}
    }
    match_default_jewel_school(filters)

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

def set_jeweled(filters):
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

def view_gear():
    
    # filters
    filters = {
        'School': 'All',
        'Gear Type': 'Hats',
        'Level': 170,
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
            elif filter == 'Good Sources':
                if filters['Gear Type'] != 'Pets':
                    df = filter_by_sources(df, filters[filter]).reset_index(drop=True)
            elif filter == 'School' or filter == 'Gear Type' or filter == 'Objectively Best' or filter == 'School Stats Only' or filter == 'Bad Sources' or filter == 'Jeweled':
                pass # these are handled later/elsewhere
            else:
                stat_filters.add(filter) # save for later, jeweling should come first
        
        # jewel/pin the items
        if 'Jeweled' in filters:
            df = jewel_the_items(df, filters)
        
        # filter by minimum stat requirements (after jeweled)
        for filter in stat_filters:
            if filter in df.columns:
                df = df[df[filter] >= filters[filter]].reset_index(drop=True)
            else:
                filters.pop(filter)
        
        # school stats columns only
        if filters['School Stats Only']:
            curr_school = 'Global' if filters['School'] == 'All' else filters['School']
            cols_to_drop = []
            for col in df.columns:
                pot_school = col.split()[0]
                if pot_school in utils.all_stat_schools and pot_school != curr_school and col != "Shadow Pip Rating":
                    if col == 'Global Resistance':
                        cols_to_drop.append(f'{curr_school} Resistance')
                    elif col == 'Global Flat Resistance':
                        cols_to_drop.append(f'{curr_school} Flat Resistance')
                    elif col == 'Global Critical Block Rating':
                        cols_to_drop.append(f'{curr_school} Critical Block Rating')
                    else:
                        cols_to_drop.append(col)
            df = df.drop(cols_to_drop, axis=1)
            df.columns = [col.replace(curr_school + " ", "").replace('Global' + ' ', '') for col in df.columns]
            df = df.sort_values(by=['Damage', 'Resistance', 'Max Health', 'Critical Rating', 'Armor Piercing'], ascending=[False, False, False, False, False]).reset_index(drop=True)
        
        # only objectively best
        if filters['Objectively Best']:
            df = objectively_best_gear(df)
        
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
            return False
        elif action_lower == 'all':
            school = filters['School']
            gear_type = filters['Gear Type']
            filters = {
                'School': school,
                'Gear Type': gear_type,
                'Level': 170,
                'Usable In': 'All',
                'Objectively Best': False,
                'School Stats Only': False,
                'Good Sources': filters['Good Sources'] | filters['Bad Sources'],
                'Bad Sources': set(),
            }
        elif action_lower == 'school':
            new_school = 'Nothing'
            print('\nPlease enter the new school to view, or b to go back:\n')
            while True:
                new_school = input()
                if new_school.lower() == 'b':
                    break
                elif new_school not in utils.schools_of_items:
                    print(f'\nInvalid input, please enter a valid school from {utils.schools_of_items}, or b to go back\n')
                else:
                    filters['School'] = 'All' if new_school == 'Global' else new_school
                    if 'Jeweled' in filters:
                        set_default_jeweled(filters)
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
            filters[action] = input(f"\nSearch by name:\n\n")
        elif action_lower == 'gear set':
            if 'Gear Set' in filters:
                filters.pop('Gear Set')
            else:
                filters['Gear Set'] = True
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
            print('\nWhich source would you like to add or remove? Or b to go back\n')
            while True:
                source = input()
                if source.lower() == 'b':
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
            set_jeweled(filters)
        elif action_lower == 'level':
            num = -1
            print('\nInput the maximum level value, or b to go back\n')
            while True:
                num = input()
                if num.lower() == 'b':
                    break
                elif is_int(num):
                    int_num = int(num)
                    max_level = 170 # UPDATE WITH NEW WORLD
                    if int_num > 0 and int_num <= max_level:
                        filters['Level'] = int_num
                        if 'Jeweled' in filters:
                            set_default_jeweled(filters)
                        break
                    else:
                        print(f'\nInvalid value, enter a number between 1 and {max_level}, or b to go back\n')
                else:
                    print('\nInvalid value, please retry\n')
        elif action in orig_df.columns:
            num = -1
            print(f'\nInput the minimum {action} value, or b to go back\n')
            while True:
                num = input()
                if num.lower() == 'b':
                    break
                elif is_int(num) and int(num) >= 0:
                    if int(num) == 0 and action in filters:
                        filters.pop(action)
                    elif int(num) != 0:
                        filters[action] = int(num)
                    break
                else:
                    print('\nInvalid value, please enter a positive number, or b to go back:\n')
        else:
            print('\nInvalid value, please retry')
