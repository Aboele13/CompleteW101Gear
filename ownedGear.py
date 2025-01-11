import pandas as pd

import utils

accounts = ['Andrew', 'Chris', 'Tessa']

def add_owned_item(account, gear_type):
    all_items_df = pd.read_csv(f'Gear\\All_Gear\\All_{gear_type}.csv')
    
    item_i = -1 # index of the item to add to owned gear
    
    while item_i < 0 or item_i >= len(all_items_df):
        if len(all_items_df) == 0:
            print(f"\nNo {gear_type} have this name, resetting to the full dataframe")
            add_owned_item(account, gear_type)
        else:
            print(all_items_df)
            # prompt to enter part of the name to filter down
            # once there's less than 20, print records 1 by 1 and select by number menu
            # then ask to jewel it (ask if unlocked)
            # then add the jeweled version to socketed file

def remove_owned_item(account, gear_type):
    file_path = f"Owned_Gear\\{account}_Owned_Gear\\{account}_Socketed_Owned_Gear\\{account}_Socketed_Owned_{gear_type}.csv"
    try:
        socketed_df = pd.read_csv(file_path)
        socketed_df.iloc[0] # if it's empty, except will trigger and say so
    except:
        print(f"\n{account} does not currently own any {gear_type}, so there are none to remove. Returning to previous screen.")
        add_or_remove_owned_item(account, gear_type)
    
    sockets = "Jewels Used" if gear_type in utils.accessory_gear_types else "Pins Used"
    
    data = socketed_df.to_dict('records')
    
    print(f"\nTo remove, enter the number next to the item you no longer own on {account}'s account. Or b to go back or q to quit\n")
    
    for i, record in enumerate(data):
        print(f"[{i}] {record['School']} - {record['Name']} {record[sockets]}")
    print('')
    
    action = input().lower()
    
    if action == 'b':
        add_or_remove_owned_item(account, gear_type)
    elif action == 'q':
        return
    elif utils.is_int(action):
        record_i = int(action)
        if record_i < 0 or record_i >= len(socketed_df):
            print(f"\nInvalid input, please enter the number next to the item you wish to remove")
            remove_owned_item(account, gear_type)
        else:
            # collect info to remove from unsocketed df
            remove_school = socketed_df.iloc[record_i]['School']
            remove_name = socketed_df.iloc[record_i]['Name']
            
            # remove from socketed dataframe
            socketed_df = socketed_df.drop(index=record_i).reset_index(drop=True)
            try:
                socketed_df.to_csv(file_path, index=False)
            except:
                input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
                socketed_df.to_csv(file_path, index=False)
            
            # remove from unsocketed dataframe
            file_path = f"Owned_Gear\\{account}_Owned_Gear\\{account}_Unsocketed_Owned_Gear\\{account}_Socketed_Owned_{gear_type}.csv"
            unsocketed_df = pd.read_csv(file_path)
            
            remove_item = (unsocketed_df['School'] == remove_school) & (unsocketed_df['Name'] == remove_name)
            remove_item_i = unsocketed_df[remove_item].index[0]  # Get the first index matching the condition

            unsocketed_df = unsocketed_df.drop(index=remove_item_i).reset_index(drop=True)
            try:
                unsocketed_df.to_csv(file_path, index=False)
            except:
                input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
                unsocketed_df.to_csv(file_path, index=False)
            
            print(f"The specified {remove_name} has been removed. Would you like to remove another item?")
            remove_owned_item(account, gear_type)
    else:
        print(f"\nInvalid input, please enter the number next to the item you wish to remove")
        remove_owned_item(account, gear_type)

def add_or_remove_owned_item(account, gear_type):
    print(f"\nYou selected to modify {account}'s {gear_type}. How would you like to modify?\n\n[1] Add\n[2] Remove\n[b] Back\n[q] Quit\n\n")
    
    action = input()
    action_lower = action.lower()
    
    if action_lower == 'b':
        select_gear_type(account)
    elif action_lower == 'q':
        return
    elif action == '1' or not action:
        add_owned_item(account, gear_type)
    elif action == '2':
        remove_owned_item(account, gear_type)
    else:
        print('\nInvalid input, please select the number next to your selection\n')

def select_gear_type(account):
    print(f"\nWhich of {account}'s gear types do you want to modify? Or b to go back or q to quit\n")
    utils.print_gear_type_options()
    
    action = input()
    action_lower = action.lower()
    
    if action_lower == 'b':
        owned_gear()
    elif action_lower == 'q':
        return
    elif action in {'1', '2', '3', '4', '5', '6', '7', '8', '9', '0'}:
        add_or_remove_owned_item(account, utils.all_gear_types_list[(int(action) - 1) % len(utils.all_gear_types_list)])
    else:
        print(f"\nInvalid input, please enter an integer between 0 and {len(utils.all_gear_types_list) - 1}\n")
        select_gear_type(account)

def list_accounts_with_nums():
    for i in range(len(accounts)):
        print(f"[{i + 1}] {accounts[i]}")
    print('')

def owned_gear():
    print('\nModifying Owned Gear: Which account would you like to modify? Or b to go back to the menu or q to quit\n')
    list_accounts_with_nums()
    
    action = input()
    action_lower = action.lower()
    
    if action_lower == 'b':
        return True
    elif action_lower == 'q':
        return False
    elif not action:
        select_gear_type(accounts[0])
    elif action in {'1', '2', '3'}:
        select_gear_type(accounts[int(action) - 1])
    else:
        print(f'\nInvalid input, please enter a number between 1 and {len(accounts)}\n')
        owned_gear
