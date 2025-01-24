import sys

import pandas as pd

import utils

keep_the_best_amount = 3

def modify_filters(filters):
    
    while True:
        
        print('\nCurrent filters:\n')
        
        for filter in filters:
            print(f'{filter}: {filters[filter]}')
        
        action = input("\nWhat filter would you like to change? Or send Go when you're ready, or b to go back or q to quit\n\n")
        action_lower = action.lower()
        
        if action_lower == 'q':
            sys.exit()
        elif action_lower == 'b':
            return False
        elif action_lower == 'go':
            return True
        elif action_lower == 'school':
            new_school = 'Nothing'
            print(f'\nWhat school would you like to make sets for? Or b to go back or q to quit:\n{utils.schools_of_wizards}\n')
            while True:
                new_school = input()
                if new_school.lower() == 'b':
                    break
                elif new_school.lower() == 'q':
                    sys.exit()
                elif new_school not in utils.schools_of_wizards:
                    print(f'\nInvalid input, please enter a valid school from {utils.schools_of_wizards}, or b to go back\n')
                else:
                    filters['School'] = new_school
                    # changing the school affects jewels
                    if not filters['Owned']: # not owned gear always is jeweled
                        utils.set_default_jeweled(filters)
                    elif filters['Jewel My Items']: # owned items are jeweled when told to
                        utils.set_default_jeweled(filters)
                    break
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
        elif action_lower == 'account':
            account = 'Nothing'
            print(f'\nWhat account would you like to make sets for? Or b to go back or q to quit\n{utils.accounts}\n')
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
            if filters['Owned']: # turning off owned gear; turn on all gear
                filters['Owned'] = False
                filters.pop('Jewel My Items')
            else: # turning on owned gear only
                rejewel_items = input('\nWould you like to rejewel your items? Enter Y for yes, or b to go back, or q to quit, or anything else for no\n\n').lower()
                if rejewel_items == 'b':
                    continue
                elif rejewel_items == 'q':
                    sys.exit()
                elif rejewel_items == 'y':
                    filters['Jewel My Items'] = True
                else:
                    filters['Jewel My Items'] = False
                filters['Owned'] = True
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
        elif action_lower == 'school stats only':
            filters['School Stats Only'] = not filters['School Stats Only']
        elif action_lower == 'jeweled':
            utils.set_jeweled(filters)
        else:
            print('\nInvalid input, please try again')

def filter_usability(usable_in, df):
    if usable_in == 'Everything':
        df = df[df['Usable In'] == 'Everything'].reset_index(drop=True)
    elif usable_in == 'PVP':
        df = df[df['Usable In'].isin({'Everything', 'PVP'})].reset_index(drop=True)
    elif usable_in == 'Deckathalon':
        df = df[df['Usable In'].isin({"Everything", 'Deckathalon'})].reset_index(drop=True)
    return df

def view_sets():
    
    # default filters
    filters = {
        'School': 'Death',
        'Level': utils.max_level,
        'Account': 'Andrew',
        'Owned': False,
        'Usable In': 'Everything',
        'School Stats Only': True,
        'Good Sources': {"Gold Vendor", "Drop", "Bazaar", "Crafting", "Gold Key", "Stone Key", "Wooden Key", "Housing Gauntlet", "Rematch", "Quest", "Fishing"},
        'Bad Sources': {"One Shot Housing Gauntlet", "Raid", "Crowns", "Gift Card", "Event Drop", "Unavailable"},
    }
    utils.set_default_jeweled(filters)
    
    while True:
        
        if modify_filters(filters):
            
            gear = {}
            
            if not filters['Owned']: # if looking at all gear (not just owned gear)
                for gear_type in utils.all_gear_types_list:
                    gear_type_items_df = pd.read_csv(f"Gear\\{filters['School']}_Gear\\{filters['School']}_{gear_type}.csv")
                    gear_type_items_df = gear_type_items_df[gear_type_items_df['Level'] <= filters['Level']].reset_index(drop=True)
                    gear_type_items_df = filter_usability(filters['Usable In'], gear_type_items_df)
                    gear_type_items_df = utils.objectively_best_gear(gear_type_items_df, filters).sort_values(by=f"{filters['School']} Damage", ascending=False).reset_index(drop=True)
                    gear_type_items = gear_type_items_df.to_dict('records')
                    if not gear_type_items:
                        singular_gear_type = gear_type[:-1] if gear_type != 'Boots' else gear_type
                        gear[gear_type] = [utils.empty_item(singular_gear_type)]
                    else:
                        gear[gear_type] = gear_type_items[:keep_the_best_amount] if (len(gear_type_items) > keep_the_best_amount) else gear_type_items
            else: # just owned gear
                for gear_type in utils.all_gear_types_list:
                    try:
                        if not filters['Jewel My Items']: # if i jeweled my items, whats the best i can do?
                            gear_type_items_df = pd.read_csv(f"Owned_Gear\\{filters['Account']}_Owned_Gear\\{filters['Account']}_Socketed_Owned_Gear\\{filters['Account']}_Socketed_Owned_{gear_type}.csv")
                            gear_type_items_df = gear_type_items_df[(gear_type_items_df['School'] == filters['School']) & (gear_type_items_df['Level'] <= filters['Level'])].reset_index(drop=True)
                            gear_type_items_df = filter_usability(filters['Usable In'], gear_type_items_df)
                            gear_type_items = gear_type_items_df.to_dict('records')
                        else: # don't jewel my items, whats the best i can do right now
                            gear_type_items_df = pd.read_csv(f"Owned_Gear\\{filters['Account']}_Owned_Gear\\{filters['Account']}_Unsocketed_Owned_Gear\\{filters['Account']}_Unsocketed_Owned_{gear_type}.csv")
                            gear_type_items_df = gear_type_items_df[(gear_type_items_df['School'] == filters['School']) & (gear_type_items_df['Level'] <= filters['Level'])].reset_index(drop=True)
                            gear_type_items_df = filter_usability(filters['Usable In'], gear_type_items_df)
                            gear_type_items = gear_type_items_df.to_dict('records')
                    except:
                        singular_gear_type = gear_type[:-1] if gear_type != 'Boots' else gear_type
                        gear[gear_type] = [utils.empty_item(singular_gear_type)]
                        continue
                    if not gear_type_items:
                        singular_gear_type = gear_type[:-1] if gear_type != 'Boots' else gear_type
                        gear[gear_type] = [utils.empty_item(singular_gear_type)]
                    else:
                        gear[gear_type] = gear_type_items
            
            sets = []
            
            for hat in gear['Hats']:
                for robe in gear['Robes']:
                    for boots in gear['Boots']:
                        for wand in gear['Wands']:
                            for athame in gear['Athames']:
                                for amulet in gear['Amulets']:
                                    for ring in gear['Rings']:
                                        for pet in gear['Pets']:
                                            for mount in gear['Mounts']:
                                                for deck in gear['Decks']:
                                                    sets.append({
                                                        'Hat': hat['Name'],
                                                        'Robe': robe['Name'],
                                                        'Boots': boots['Name'],
                                                        'Wand': wand['Name'],
                                                        'Athame': athame['Name'],
                                                        'Amulet': amulet['Name'],
                                                        'Ring': ring['Name'],
                                                        'Pet': pet['Name'],
                                                        'Mount': mount['Name'],
                                                        'Deck': deck['Name'],
                                                    })
            
            df = pd.DataFrame(sets)
            print(df)
            df = df.iloc[:10000] # microsoft excel can't handle too big of files, keep it at 10,000
            # output
            file_path = 'CompleteW101Gear_Output.csv'
            try:
                df.to_csv(file_path, index=False)
            except:
                input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
                df.to_csv(file_path, index=False)
        else:
            return True
