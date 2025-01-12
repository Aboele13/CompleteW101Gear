import sys

import pandas as pd

import utils

accounts = ['Andrew', 'Chris', 'Tessa']

def add_shared_item(account, gear_type, item):
    
    shared_item = item.copy()
    
    if gear_type in utils.accessory_gear_types:
        shared_item['Unlocked Tear'] = 0
        shared_item['Unlocked Circle'] = 0
        shared_item['Unlocked Square'] = 0
        shared_item['Unlocked Triangle'] = 0
        shared_item['Locked Tear'] = 0
        shared_item['Locked Circle'] = 0
        shared_item['Locked Square'] = 0
        shared_item['Locked Triangle'] = 0
        shared_item['Unlocked'] = False
    
    # check for mastery items
    bad_school = 'Nothing' if (('School' not in item) or (not item['School'].startswith('Not '))) else item['School'][4:]
    
    for school in utils.schools_of_items:
        if school != 'Global' and school != bad_school:
            
            shared_item['School'] = school
            
            # add the new item to the unsocketed dataframe
            file_path = f"Owned_Gear\\{account}_Owned_Gear\\{account}_Unsocketed_Owned_Gear\\{account}_Unsocketed_Owned_{gear_type}.csv"
            try:
                df = pd.read_csv(file_path)
                try:
                    df.loc[len(df)] = shared_item
                except:
                    print(f"\nThe columns don't match:\ndf1: {df.columns.tolist()}\ndf2: {df.columns.tolist()}\n\n\n\n\n\n\n\n\n\n\n\n")
            except:
                # the file/dataframe hasn't been created yet
                df = pd.DataFrame([shared_item])
            
            # write to the updated unsocketed dataframe
            try:
                if df.columns[2] != 'School':
                    school_col = df.pop('School')
                    df.insert(2, 'School', school_col)
                df = df.sort_values(by=['School', 'Name'], ascending=[True, True]).reset_index(drop=True)
                df.to_csv(file_path, index=False)
            except:
                input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
                df.to_csv(file_path, index=False)
            
            # add the new item to the socketed dataframe
            if gear_type in utils.accessory_gear_types:
                shared_item['Jewels Used'] = '(No Jewels)'
            elif gear_type in utils.clothing_gear_types:
                shared_item['Pins Used'] = '(No Pins)'
            
            file_path = f"Owned_Gear\\{account}_Owned_Gear\\{account}_Socketed_Owned_Gear\\{account}_Socketed_Owned_{gear_type}.csv"
            
            # add the new item to the socketed dataframe
            try:
                df = pd.read_csv(file_path)
                try:
                    df.loc[len(df)] = shared_item
                except:
                    print(f"\nThe columns don't match:\ndf1: {df.columns.tolist()}\ndf2: {df.columns.tolist()}\n\n\n\n\n\n\n\n\n\n\n\n")
            except:
                # the file/dataframe hasn't been created yet
                df = pd.DataFrame([shared_item])
            
            # write to the updated unsocketed dataframe
            try:
                if df.columns[2] != 'School':
                    school_col = df.pop('School')
                    df.insert(2, 'School', school_col)
                df = df.sort_values(by=['School', 'Name'], ascending=[True, True]).reset_index(drop=True)
                df.to_csv(file_path, index=False)
            except:
                input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
                df.to_csv(file_path, index=False)

def select_owned_item_school(account, gear_type, item):
    
    while True:
        
        print(f"\nOn what school did {account} get the {item['Name']}? Or b to go back or q to quit\n")
        
        school = input()
        school_lower = school.lower()
        
        if school_lower == 'b':
            select_owned_item(account, gear_type, item)
            return
        elif school_lower == 'q':
            sys.exit()
        elif school.lower() == 'all':
            add_shared_item(account, gear_type, item)
            return
        elif school in utils.schools_of_items and school != "Global":
            item['School'] = school
            jewel_the_item(account, gear_type, item)
            return
        else:
            print(f"\nInvalid input. Please enter the the school of the wizard you got {item['Name']} on")

def filter_socket(item, shape):
    all_jewels_df = pd.read_csv(f"Jewels\\{item['School']}_Jewels\\{item['School']}_{shape}_Jewels.csv")
    
    item_i = -1 # index of the jewel to add to owned item
    
    while item_i < 0 or item_i >= len(all_jewels_df):
        if len(all_jewels_df) == 0:
            print(f"\nNo {shape} Sockets have this name, resetting to the full dataframe\n")
            select_socket(item, shape)
            return
        elif len(all_jewels_df) <= 20:
            return all_jewels_df
        else:
            print(all_jewels_df)
            print(f"\nEnter part of the {shape} Socket's name to filter down the dataframe, or submit nothing to select no socket, or q to quit:\n")
            name_substr = input().lower()
            if name_substr == 'q':
                sys.exit()
            elif not name_substr:
                return None
            else:
                all_jewels_df = all_jewels_df[all_jewels_df['Name'].str.contains(name_substr, case=False)].reset_index(drop=True)

def select_socket(item, shape):
    df = filter_socket(item, shape)
    
    if len(df) > 0:
        data = df.to_dict('records')
        
        added_socket_name = 'No Name'
        
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
                    # confirm addition
                    print(f"\nYou chose to add\n[{socket_i}] {added_socket_name} - Level {data[socket_i]['Level']}\nIs this correct? (Y/n) or b to go back, or q to quit.\n")
                    action = input().lower()
                    if action == 'q':
                        sys.exit()
                    elif action != 'y':
                        print(f"\n{added_socket_name} will not be added, returning to list of all {shape} Sockets\n")
                        return select_socket(item, shape)
                    
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
                    
                    print(f"\nThe specified {added_socket_name} has been added\n")
                    if shape in {'Sword', 'Shield', 'Power'}:
                        return f"({utils.abbreviate_pin(shape, added_socket_name)})"
                    else:
                        return f"({utils.abbreviate_jewel(shape, added_socket_name)})"
            else:
                print(f"\nInvalid input, please enter an integer between 0 and {len(data) - 1}")
    else:
        return ''

def apply_jewels(item):
    tears = item['Unlocked Tear'] + item['Locked Tear'] if item['Unlocked'] else item['Unlocked Tear']
    circles = item['Unlocked Circle'] + item['Locked Circle'] if item['Unlocked'] else item['Unlocked Circle']
    squares = item['Unlocked Square'] + item['Locked Square'] if item['Unlocked'] else item['Unlocked Square']
    triangles = item['Unlocked Triangle'] + item['Locked Triangle'] if item['Unlocked'] else item['Unlocked Triangle']
    if tears + circles + squares + triangles == 0: # no sockets at all, or all sockets are locked (and item is locked)
        item['Jewels Used'] = '(No Jewels)'
        return item
    
    jewels_used = '' # testing, uncomplete
    
    for i in range(tears):
        jewels_used += select_socket(item, 'Tear')
    for i in range(circles):
        jewels_used += select_socket(item, 'Circle')
    for i in range(squares):
        jewels_used += select_socket(item, 'Square')
    for i in range(triangles):
        jewels_used += select_socket(item, 'Triangle')
    
    item['Jewels Used'] = jewels_used if jewels_used else '(No Jewels)'
    return item

def apply_pins(item):
    swords = item['Sword Pins']
    shields = item['Shield Pins']
    powers = item['Power Pins']
    if swords + shields + powers == 0:
        item['Pins Used'] = '(No Pins)'
        return item
    
    pins_used = ''
    
    for i in range(swords):
        pins_used += select_socket(item, 'Sword')
    for i in range(shields):
        pins_used += select_socket(item, 'Shield')
    for i in range(powers):
        pins_used += select_socket(item, 'Power')
    
    item['Pins Used'] = pins_used if pins_used else '(No Pins)'
    return item

def jewel_the_item(account, gear_type, item):
    # check if the accessories have been unlocked already
    while gear_type in utils.accessory_gear_types:
        print(f"\nAre the sockets unlocked on this {item['Name']}? (Y/n) or b to go back, or q to quit\n")
        unlock = input().lower()
        
        if unlock == 'b':
            add_owned_item(account, gear_type)
            return
        elif unlock == 'q':
            sys.exit()
        elif unlock == 'y':
            item['Unlocked'] = True
            break
        elif unlock == 'n':
            item['Unlocked'] = False
            break
        else:
            print("\nInvalid input, please try again")
    
    # now the initial item is set, this will be added to the unsocketed df when ready
    socketed_item = item.copy()
    if gear_type in utils.accessory_gear_types:
        socketed_item = apply_jewels(socketed_item)
    elif gear_type in utils.clothing_gear_types:
        socketed_item = apply_pins(socketed_item)
    
    # add the new item to the unsocketed dataframe
    file_path = f"Owned_Gear\\{account}_Owned_Gear\\{account}_Unsocketed_Owned_Gear\\{account}_Unsocketed_Owned_{gear_type}.csv"
    try:
        df = pd.read_csv(file_path)
        try:
            df.loc[len(df)] = item
        except:
            print(f"\nThe columns don't match:\ndf1: {df.columns.tolist()}\ndf2: {df.columns.tolist()}\n\n\n\n\n\n\n\n\n\n\n\n")
    except:
        # the file/dataframe hasn't been created yet
        df = pd.DataFrame([item])
    
    # write to the updated unsocketed dataframe
    try:
        if df.columns[2] != 'School':
            school_col = df.pop('School')
            df.insert(2, 'School', school_col)
        df = df.sort_values(by=['School', 'Name'], ascending=[True, True]).reset_index(drop=True)
        df.to_csv(file_path, index=False)
    except:
        input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
        df.to_csv(file_path, index=False)
    
    # add the new item to the socketed dataframe
    file_path = f"Owned_Gear\\{account}_Owned_Gear\\{account}_Socketed_Owned_Gear\\{account}_Socketed_Owned_{gear_type}.csv"
    
    try:
        df = pd.read_csv(file_path)
        try:
            df.loc[len(df)] = socketed_item
        except:
            print(f"\nThe columns don't match:\ndf1: {df.columns.tolist()}\ndf2: {df.columns.tolist()}\n\n\n\n\n\n\n\n\n\n\n\n")
    except:
        # the file/dataframe hasn't been created yet
        df = pd.DataFrame([socketed_item])
    
    # write to the updated unsocketed dataframe
    try:
        if df.columns[2] != 'School':
            school_col = df.pop('School')
            df.insert(2, 'School', school_col)
        df = df.sort_values(by=['School', 'Name'], ascending=[True, True]).reset_index(drop=True)
        df.to_csv(file_path, index=False)
    except:
        input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
        df.to_csv(file_path, index=False)

def select_owned_item(account, gear_type, df):
    
    data = df.to_dict('records')
    
    added_item_name = 'No Name'
    
    while True:
        
        print("\nPlease enter the number next to the item you'd like to add, or b to reset or q to quit\n")

        for i, record in enumerate(data):
            item_info = f"[{i}] {record['Name']} - Level {record['Level']}"
            if gear_type != 'Mounts':
                item_info = f"{item_info} - {record['School']}"
            print(item_info)
        
        item_i = input().lower()
        if item_i == 'b':
            add_owned_item(account, gear_type)
            return
        elif item_i == 'q':
            sys.exit()
        elif utils.is_int(item_i):
            item_i = int(item_i)
            if item_i < 0 or item_i >= len(data):
                print(f"\nInvalid input, please enter an integer between 0 and {len(data) - 1}")
            else:
                added_item_name = data[item_i]['Name']
                if gear_type == 'Mounts' or data[item_i]['School'] == 'Global' or data[item_i]['School'].startswith('Not '):
                    select_owned_item_school(account, gear_type, data[item_i])
                    break
                else: # can only be this school/wizard
                    
                    # confirm addition
                    print(f"\nYou chose to add\n[{item_i}] {added_item_name} - Level {record['Level']} - {data[item_i]['School']}\nIs this correct? (Y/n) or b to go back, or q to quit.\n")
                    action = input().lower()
                    if action == 'q':
                        sys.exit()
                    elif action != 'y':
                        print(f"\n{added_item_name} will not be added, returning to adding menu\n")
                        add_owned_item(account, gear_type)
                        return
                    
                    jewel_the_item(account, gear_type, data[item_i])
                    break
        else:
            print(f"\nInvalid input, please enter an integer between 0 and {len(data) - 1}")
    
    print(f"\nThe specified {added_item_name} has been added. Would you like to add another item?\n")

def add_owned_item(account, gear_type):
    all_items_df = pd.read_csv(f'Gear\\All_Gear\\All_{gear_type}.csv')
    
    item_i = -1 # index of the item to add to owned gear
    
    while item_i < 0 or item_i >= len(all_items_df):
        if len(all_items_df) == 0:
            print(f"\nNo {gear_type} have this name, resetting to the full dataframe\n")
            add_owned_item(account, gear_type)
            return
        elif len(all_items_df) <= 20:
            select_owned_item(account, gear_type, all_items_df)
            add_owned_item(account, gear_type)
            return
        else:
            print(all_items_df)
            print("\nEnter part of the item name to filter down the dataframe, or b to go back or q to quit:\n")
            name_substr = input().lower()
            if name_substr == 'b':
                add_or_remove_owned_item(account, gear_type)
                return
            elif name_substr == 'q':
                sys.exit()
            else:
                all_items_df = all_items_df[all_items_df['Name'].str.contains(name_substr, case=False)].reset_index(drop=True)

def remove_owned_item(account, gear_type):
    file_path = f"Owned_Gear\\{account}_Owned_Gear\\{account}_Socketed_Owned_Gear\\{account}_Socketed_Owned_{gear_type}.csv"
    try:
        socketed_df = pd.read_csv(file_path)
        socketed_df.iloc[0] # if it's empty, except will trigger and say so
    except:
        print(f"\n{account} does not currently own any {gear_type}, so there are none to remove. Returning to previous screen.")
        add_or_remove_owned_item(account, gear_type)
        return
    
    data = socketed_df.to_dict('records')
    
    print(f"\nTo remove, enter the number next to the item you no longer own on {account}'s account. Or b to go back or q to quit\n")
    
    for i, record in enumerate(data):
        if gear_type in utils.accessory_gear_types:
            print(f"[{i}] {record['School']} - {record['Name']} {record['Jewels Used']}")
        elif gear_type in utils.clothing_gear_types:
            print(f"[{i}] {record['School']} - {record['Name']} {record['Pins Used']}")
        else:
            print(f"[{i}] {record['School']} - {record['Name']}")
    print('')
    
    action = input().lower()
    
    if action == 'b':
        add_or_remove_owned_item(account, gear_type)
    elif action == 'q':
        sys.exit()
    elif utils.is_int(action):
        record_i = int(action)
        if record_i < 0 or record_i >= len(socketed_df):
            print(f"\nInvalid input, please enter the number next to the item you wish to remove")
            remove_owned_item(account, gear_type)
            return
        else:
            # collect info to remove from unsocketed df
            remove_school = socketed_df.iloc[record_i]['School']
            remove_name = socketed_df.iloc[record_i]['Name']
            
            # confirm removal
            print(f"\nYou chose to remove\n[{record_i}] {remove_school} - {remove_name}\nIs this correct? (Y/n) or b to go back, or q to quit.\n")
            
            action = input().lower()
            
            if action == 'q':
                sys.exit()
            elif action != 'y':
                print(f"\n{remove_name} will not be removed, returning to remove menu")
                remove_owned_item(account, gear_type)
                return
            
            # remove from socketed dataframe
            socketed_df = socketed_df.drop(index=record_i).reset_index(drop=True)
            try:
                socketed_df.to_csv(file_path, index=False)
            except:
                input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
                socketed_df.to_csv(file_path, index=False)
            
            # remove from unsocketed dataframe
            file_path = f"Owned_Gear\\{account}_Owned_Gear\\{account}_Unsocketed_Owned_Gear\\{account}_Unsocketed_Owned_{gear_type}.csv"
            unsocketed_df = pd.read_csv(file_path)
            
            remove_item = (unsocketed_df['School'] == remove_school) & (unsocketed_df['Name'] == remove_name)
            remove_item_i = unsocketed_df[remove_item].index[0]  # Get the first index matching the condition

            unsocketed_df = unsocketed_df.drop(index=remove_item_i).reset_index(drop=True)
            try:
                unsocketed_df.to_csv(file_path, index=False)
            except:
                input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
                unsocketed_df.to_csv(file_path, index=False)
            
            print(f"\nThe specified {remove_name} has been removed. Would you like to remove another item?")
            remove_owned_item(account, gear_type)
            return
    else:
        print(f"\nInvalid input, please enter the number next to the item you wish to remove")
        remove_owned_item(account, gear_type)
        return

def add_or_remove_owned_item(account, gear_type):
    print(f"\nYou selected to modify {account}'s {gear_type}. How would you like to modify?\n\n[1] Add\n[2] Remove\n[b] Back\n[q] Quit\n")
    
    action = input()
    action_lower = action.lower()
    
    if action_lower == 'b':
        select_gear_type(account)
        return
    elif action_lower == 'q':
        sys.exit()
    elif action == '1' or not action:
        add_owned_item(account, gear_type)
        return
    elif action == '2':
        remove_owned_item(account, gear_type)
        return
    else:
        print('\nInvalid input, please select the number next to your selection\n')

def select_gear_type(account):
    print(f"\nWhich of {account}'s gear types do you want to modify? Or b to go back or q to quit\n")
    utils.print_gear_type_options()
    
    action = input()
    action_lower = action.lower()
    
    if action_lower == 'b':
        return owned_gear()
    elif action_lower == 'q':
        sys.exit()
    elif action in {'1', '2', '3', '4', '5', '6', '7', '8', '9', '0'}:
        add_or_remove_owned_item(account, utils.all_gear_types_list[(int(action) - 1) % len(utils.all_gear_types_list)])
        return
    else:
        print(f"\nInvalid input, please enter an integer between 0 and {len(utils.all_gear_types_list) - 1}\n")
        select_gear_type(account)
        return

def list_accounts_with_nums():
    for i in range(len(accounts)):
        print(f"[{i + 1}] {accounts[i]}")
    print('')

def owned_gear():
    print('\nModifying Owned Gear: Which account would you like to modify? Or b to go back or q to quit\n')
    list_accounts_with_nums()
    
    action = input()
    action_lower = action.lower()
    
    if action_lower == 'b':
        return True
    elif action_lower == 'q':
        sys.exit()
    elif not action:
        select_gear_type(accounts[0])
        return
    elif action in {'1', '2', '3'}:
        select_gear_type(accounts[int(action) - 1])
        return
    else:
        print(f'\nInvalid input, please enter a number between 1 and {len(accounts)}\n')
        owned_gear()
