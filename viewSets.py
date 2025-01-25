import itertools
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import pandas as pd

import utils

num_to_keep_best = 2
potential_set_types = {'Boss', 'Mob', 'Tank', 'Balanced', 'Healing', 'Secondary School'}
count = 0 # testing

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
        elif action_lower == 'set type':
            set_type = 'Nothing'
            print(f'\nWhat type of set would you like to make? {potential_set_types} Or b to go back or q to quit\n')
            while True:
                set_type = input()
                if set_type.lower() == 'b':
                    break
                elif set_type.lower() == 'q':
                    sys.exit()
                elif set_type not in potential_set_types:
                    print(f'\nInvalid input, please enter one of the options: {potential_set_types}, or b to go back or q to quit\n')
                elif set_type in {'Healing', 'Secondary School'}:
                    print(f'\nUnfortunately, this functionality is not yet complete. Please try again later. For now, select a different set type\n')
                else:
                    filters['Set Type'] = set_type
                    break
        elif action_lower == 'owned':
            if filters['Owned']: # turning off owned gear; turn on all gear
                filters['Owned'] = False
                filters.pop('Jewel My Items')
                utils.set_default_jeweled(filters)
            else: # turning on owned gear only
                rejewel_items = input('\nWould you like to rejewel your items? Enter Y for yes, or b to go back, or q to quit, or anything else for no\n\n').lower()
                if rejewel_items == 'b':
                    continue
                elif rejewel_items == 'q':
                    sys.exit()
                elif rejewel_items == 'y':
                    filters['Jewel My Items'] = True
                else:
                    if 'Jeweled' in filters:
                        filters.pop('Jeweled')
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
        elif action_lower in {'source', 'good sources', 'bad sources'}:
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
        elif action_lower == 'jeweled':
            utils.set_jeweled(filters)
            if not filters['Owned'] or filters['Jewel My Items']:
                print('\nThe items are being jeweled, so jeweled specifications must be included')
                utils.set_default_jeweled(filters)
            else:
                print("\nNote that the jewels currently won't be applied since you are in Owned gear with no Jewel My Items")
        elif action_lower == 'jewel my items':
            if not filters['Owned']:
                print("'\nWith unowned gear, all gear will be jeweled automatically")
            elif filters['Jewel My Items']:
                filters['Jewel My Items'] = False
                filters.pop('Jeweled')
            else:
                filters['Jewel My Items'] = True
                utils.set_default_jeweled(filters)
        elif action in utils.all_gear_types_list:
            good_names = set()
            print(f"\nEnter {action} names to keep, one at a time. When finished, submit an empty string, or b to go back/cancel.\n")
            while True:
                name = input().lower()
                if name == 'b':
                    break
                elif name == 'q':
                    sys.exit()
                elif not name:
                    if good_names:
                        filters[action] = good_names
                        break
                    if action in filters:
                        filters.pop(action)
                        break
                else:
                    good_names.add(name)
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

def filter_pets_by_set_type(df, set_type, school, account):
    if set_type == 'Boss':
        df = df[df['Name'].str.contains(f'{school} Triple Double| \\({account}', case=False, na=False)]
    elif set_type == 'Mob':
        df = df[df['Name'].str.contains(f'{school} Max Damage| \\({account}', case=False, na=False)]
    elif set_type == 'Tank':
        df = df[df['Name'].str.contains(f'Max Resist| \\({account}', case=False, na=False)]
    elif set_type == 'Balanced':
        df = df[df['Name'].str.contains(f'{school} Triple Double| \\({account}', case=False, na=False)]
    elif set_type == 'Healing':
        # not possible yet
        pass
    elif set_type == 'Secondary School':
        # not possible yet
        pass
    return df.reset_index(drop=True)

def filter_by_name(df, filters, gear_type):
    if gear_type in filters:
        mask = df['Name'].apply(
            lambda x: any(item_name_substr in x.lower() for item_name_substr in filters[gear_type])
        )
        return df[mask].reset_index(drop=True)
    return df

def add_owned_column(df, gear_type, filters):
    
    try:
        owned_df = pd.read_csv(f"Owned_Gear\\{filters['Account']}_Owned_Gear\\{filters['Account']}_Unsocketed_Owned_Gear\\{filters['Account']}_Unsocketed_Owned_{gear_type}.csv")
    except: # if there are no owned items, return the original df with all "Owned" as false
        df['Owned'] = False
        return df
    
    owned_df = owned_df[owned_df['School'] == filters['School']].reset_index(drop=True)
    
    # don't need to check pins/jewels, just names
    df['Owned'] = df['Name'].isin(owned_df['Name'])
    
    return df

def add_total_jewel_columns(df, gear_type, owned):
    
    if gear_type in utils.clothing_gear_types:
        df['Total Sword Pins'] = df['Sword Pins']
        df['Total Shield Pins'] = df['Shield Pins']
        df['Total Power Pins'] = df['Power Pins']
        if owned:
            df['Pins Used'] = '(No Pins)'
    elif gear_type in utils.accessory_gear_types:
        df['Total Tear Jewels'] = df['Locked Tear'] + df['Unlocked Tear']
        df['Total Circle Jewels'] = df['Locked Circle'] + df['Unlocked Circle']
        df['Total Square Jewels'] = df['Locked Square'] + df['Unlocked Square']
        df['Total Triangle Jewels'] = df['Locked Triangle'] + df['Unlocked Triangle']
        if owned:
            df['Jewels Used'] = '(No Jewels)'
    
    return df

def add_base_values(set_stats, filters):
    
    set_stats.update(utils.empty_stats()) # get all the stats I care about
    
    df = pd.read_csv(f"Base_Values\\{filters['School']}_Base_Values.csv")
    set_stats.update(df.iloc[filters['Level'] - 1].to_dict()) # actually fill the proper base values
    set_stats.pop('Level') # this was added from base values, we don't actually want it

def is_dragoon_hit_better(orig_damage, amulet_name):
    
    for dragoon_amulet in utils.dragoon_amulet_damages:
        if amulet_name.startswith(dragoon_amulet):
            return max(orig_damage, utils.dragoon_amulet_damages[dragoon_amulet])
    
    return orig_damage

def get_round_one_damage(curr_set, resist, block, filters, spell_df):
    
    spell_df_copy = spell_df.copy()
    
    # get enchant
    enchant_damage = curr_set['Enchant Damage']
    
    # get spell damage
    spell_df_copy['Damage'] = spell_df_copy.apply(
        lambda row: row['Damage'] + (enchant_damage // 2) if row['Has DOT'] else row['Damage'] + enchant_damage,
        axis=1
    )
    spell_damage = spell_df_copy.sort_values(by='Damage', ascending=False).reset_index(drop=True).iloc[0].to_dict()['Damage']
    spell_damage = is_dragoon_hit_better(spell_damage, curr_set['Amulet'])
    
    # return the formula
    school = filters['School']
    damage_multiplier = utils.get_damage_multiplier(curr_set[f"{school} Damage"])
    flat_damage = curr_set[f"{school} Flat Damage"]
    critical_multiplier = utils.get_critical_multiplier(curr_set[f"{school} Critical Rating"], block)
    resist_multiplier = utils.get_resist_multiplier(curr_set[f"{school} Armor Piercing"], resist)
    return int((spell_damage * (damage_multiplier) + flat_damage) * (critical_multiplier) * (resist_multiplier))

def make_set(gear, filters, enemy_stats, spell_df):
    set_stats = {
        'Hat': f"{gear[0]['Name']} {gear[0]['Pins Used']}" if filters['Owned'] else gear[0]['Name'],
        'Robe': f"{gear[1]['Name']} {gear[1]['Pins Used']}" if filters['Owned'] else gear[1]['Name'],
        'Boots': f"{gear[2]['Name']} {gear[2]['Pins Used']}" if filters['Owned'] else gear[2]['Name'],
        'Wand': f"{gear[3]['Name']} {gear[3]['Jewels Used']}" if filters['Owned'] else gear[3]['Name'],
        'Athame': f"{gear[4]['Name']} {gear[4]['Jewels Used']}" if filters['Owned'] else gear[4]['Name'],
        'Amulet': f"{gear[5]['Name']} {gear[5]['Jewels Used']}" if filters['Owned'] else gear[5]['Name'],
        'Ring': f"{gear[6]['Name']} {gear[6]['Jewels Used']}" if filters['Owned'] else gear[6]['Name'],
        'Pet': gear[7]['Name'],
        'Mount': gear[8]['Name'],
        'Deck': f"{gear[9]['Name']} {gear[9]['Jewels Used']}" if filters['Owned'] else gear[9]['Name'],
    }
    
    # set base values, and all other cols to 0
    add_base_values(set_stats, filters)
    
    for item in gear:
        for stat in item:
            if stat in set_stats:
                if stat == 'Enchant Damage':
                    set_stats['Enchant Damage'] = max(set_stats['Enchant Damage'], item['Enchant Damage'])
                elif stat == 'Gear Set':
                    set_stats['Gear Set'] = utils.tally_gear_sets(gear)
                else:
                    set_stats[stat] += item[stat]
    
    # after all gear is collected, add set bonueses
    utils.get_set_bonuses(set_stats, filters['School'])
    
    # tallying up the total sockets
    if not filters['Owned']:
        set_stats['Total Sword Pins'] = gear[0]['Total Sword Pins'] + gear[1]['Total Sword Pins'] + gear[2]['Total Sword Pins']
        set_stats['Total Shield Pins'] = gear[0]['Total Shield Pins'] + gear[1]['Total Shield Pins'] + gear[2]['Total Shield Pins']
        set_stats['Total Power Pins'] = gear[0]['Total Power Pins'] + gear[1]['Total Power Pins'] + gear[2]['Total Power Pins']
        set_stats['Total Tear Jewels'] = gear[3]['Total Tear Jewels'] + gear[4]['Total Tear Jewels'] + gear[5]['Total Tear Jewels'] + gear[6]['Total Tear Jewels'] + gear[9]['Total Tear Jewels']
        set_stats['Total Circle Jewels'] = gear[3]['Total Circle Jewels'] + gear[4]['Total Circle Jewels'] + gear[5]['Total Circle Jewels'] + gear[6]['Total Circle Jewels'] + gear[9]['Total Circle Jewels']
        set_stats['Total Square Jewels'] = gear[3]['Total Square Jewels'] + gear[4]['Total Square Jewels'] + gear[5]['Total Square Jewels'] + gear[6]['Total Square Jewels'] + gear[9]['Total Square Jewels']
        set_stats['Total Triangle Jewels'] = gear[3]['Total Triangle Jewels'] + gear[4]['Total Triangle Jewels'] + gear[5]['Total Triangle Jewels'] + gear[6]['Total Triangle Jewels'] + gear[9]['Total Triangle Jewels']
    # add personal stats
    else: # non-owned gear will calculate these after creating jeweled variations
        set_stats['Adjusted Health'] = set_stats['Max Health'] + (set_stats['Global Resistance'] * 120)
        set_stats['Balanced Rating'] = set_stats['Max Health'] + (set_stats['Global Resistance'] * 120) + (set_stats[f"{filters['School']} Damage"] * 120) + (set_stats[f"{filters['School']} Armor Piercing"] * 120 * 10 // 6)
        set_stats['Mob R1 Dmg'] = get_round_one_damage(set_stats, enemy_stats['Mob Resist'], enemy_stats['Mob Block'], filters, spell_df)
        set_stats['Mob HighRes R1 Dmg'] = get_round_one_damage(set_stats, 60, enemy_stats['Mob Block'], filters, spell_df)
        set_stats['Boss R1 Dmg'] = get_round_one_damage(set_stats, enemy_stats['Boss Resist'], enemy_stats['Boss Block'], filters, spell_df)
    
    return set_stats

def jewel_the_set(created_set, filters):
    
    # this returns each variation of the original set we were given
    # i'll need to add personal stats to each variation
    
    return [created_set] # testing

def sort_sets(sets_df, set_type, school):
    if set_type == 'Boss':
        sort_cols = ['Boss R1 Dmg', f'{school} Damage', f'{school} Armor Piercing', f'{school} Critical Rating', 'Adjusted Health']
        ascending_bools = [False, False, False, False, False]
    elif set_type == 'Mob':
        sort_cols = ['Mob R1 Dmg', f'{school} Damage', f'{school} Armor Piercing', f'{school} Critical Rating', 'Adjusted Health']
        ascending_bools = [False, False, False, False, False]
    elif set_type == 'Tank':
        sort_cols = ['Adjusted Health', 'Global Resistance', 'Global Critical Block', 'Global Flat Resistance', 'Incoming Healing']
        ascending_bools = [False, False, False, False, False]
    elif set_type == 'Balanced':
        sort_cols = ['Balanced Rating', 'Boss R1 Dmg', f'{school} Damage', f'{school} Armor Piercing', 'Global Resistance']
        ascending_bools = [False, False, False, False, False]
    elif set_type == 'Healing':
        # not possible yet
        return sets_df
    elif set_type == 'Secondary School':
        # not possible yet
        return sets_df
    
    return sets_df.sort_values(by=sort_cols, ascending=ascending_bools).reset_index(drop=True)

def chunked_iterator(iterable, size):
    """Yield successive chunks of the iterable of the given size."""
    iterator = iter(iterable)
    for first in iterator:
        yield [first] + list(itertools.islice(iterator, size - 1))

def process_combination(combination, filters, enemy_stats, spell_df):
    # global count  # For testing progress
    # if count % 100 == 0:
    #     print(f"{count} sets made")  # Testing
    # count += 1  # Testing
    
    hat, robe, boots, wand, athame, amulet, ring, pet, mount, deck = combination
    created_set = make_set([hat, robe, boots, wand, athame, amulet, ring, pet, mount, deck], filters, enemy_stats, spell_df)
    if filters['Owned']:
        return [created_set]
    else:
        return jewel_the_set(created_set, filters)

def generate_sets_parallel(gear, filters, enemy_stats, spell_df, chunk_size=1000):
    sets = []
    # Generate all possible combinations of gear
    all_combinations = list(itertools.product(
        gear['Hats'], gear['Robes'], gear['Boots'], gear['Wands'],
        gear['Athames'], gear['Amulets'], gear['Rings'], gear['Pets'],
        gear['Mounts'], gear['Decks']
    ))  # Convert to a list to reuse the combinations
    
    total_combinations = len(all_combinations)  # Get the total number of combinations
    print(f"Total combinations: {total_combinations}")
    
    with ProcessPoolExecutor() as executor:  # Use ProcessPoolExecutor for CPU-bound tasks
        for idx, chunk in enumerate(chunked_iterator(all_combinations, chunk_size)):
            # Process each chunk in parallel
            results = executor.map(
                process_combination,
                chunk,
                itertools.repeat(filters),
                itertools.repeat(enemy_stats),
                itertools.repeat(spell_df)
            )
            for result in results:
                sets.extend(result)
            print(f"Processed {min((idx + 1) * chunk_size, total_combinations)} / {total_combinations} combinations so far...")
    
    print("Processing complete!")
    return sets


def view_sets():
    
    # default filters
    filters = {
        'School': 'Death',
        'Level': utils.max_level,
        'Account': 'Andrew',
        'Set Type': 'Mob',
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
                    gear_type_items_df = add_total_jewel_columns(gear_type_items_df, gear_type, False)
                    gear_type_items_df = add_owned_column(gear_type_items_df, gear_type, filters)
                    gear_type_items_df = gear_type_items_df[gear_type_items_df['Level'] <= filters['Level']].reset_index(drop=True)
                    gear_type_items_df = filter_usability(filters['Usable In'], gear_type_items_df).reset_index(drop=True)
                    gear_type_items_df = filter_by_name(gear_type_items_df, filters, gear_type).reset_index(drop=True)
                    if gear_type != 'Pets':
                        gear_type_items_df = utils.filter_by_sources(gear_type_items_df, filters['Good Sources']).reset_index(drop=True)
                    else:
                        gear_type_items_df = filter_pets_by_set_type(gear_type_items_df, filters['Set Type'], filters['School'], filters['Account']).reset_index(drop=True)
                        gear_type_items_df = gear_type_items_df[gear_type_items_df['Name'].str.contains(f'Other', case=False, na=False)].reset_index(drop=True) # comment this out if I want to make other pets
                    if 'Starting Pips' in gear_type_items_df.columns and filters['Set Type'] != "Tank":
                        gear_type_items_df = gear_type_items_df[gear_type_items_df['Starting Pips'] == gear_type_items_df['Starting Pips'].max()].reset_index(drop=True)
                    gear_type_items_df = utils.objectively_best_gear(gear_type_items_df, filters).sort_values(by=f"{filters['School']} Damage", ascending=False).reset_index(drop=True)
                    print(gear_type_items_df) # testing
                    gear_type_items = gear_type_items_df.to_dict('records')
                    if not gear_type_items:
                        singular_gear_type = gear_type[:-1] if gear_type != 'Boots' else gear_type
                        gear[gear_type] = [utils.empty_item(singular_gear_type)]
                    else:
                        gear[gear_type] = gear_type_items[:num_to_keep_best] if len(gear_type_items) > num_to_keep_best else gear_type_items
            else: # just owned gear
                for gear_type in utils.all_gear_types_list:
                    try:
                        if not filters['Jewel My Items']: # don't jewel my items, whats the best i can do right now
                            gear_type_items_df = pd.read_csv(f"Owned_Gear\\{filters['Account']}_Owned_Gear\\{filters['Account']}_Socketed_Owned_Gear\\{filters['Account']}_Socketed_Owned_{gear_type}.csv")
                            gear_type_items_df = gear_type_items_df[(gear_type_items_df['School'] == filters['School']) & (gear_type_items_df['Level'] <= filters['Level'])].reset_index(drop=True)
                            gear_type_items_df = gear_type_items_df.drop_duplicates().reset_index(drop=True)
                            gear_type_items_df = filter_usability(filters['Usable In'], gear_type_items_df).reset_index(drop=True)
                            gear_type_items_df = filter_by_name(gear_type_items_df, filters, gear_type).reset_index(drop=True)
                            if gear_type == 'Pets':
                                gear_type_items_df = filter_pets_by_set_type(gear_type_items_df, filters['Set Type'], filters['School'], filters['Account']).reset_index(drop=True)
                            if 'Starting Pips' in gear_type_items_df.columns and filters['Set Type'] != "Tank":
                                gear_type_items_df = gear_type_items_df[gear_type_items_df['Starting Pips'] == gear_type_items_df['Starting Pips'].max()].reset_index(drop=True)
                            gear_type_items_df = utils.objectively_best_gear(gear_type_items_df, filters)
                            print(gear_type_items_df) # testing
                            gear_type_items = gear_type_items_df.to_dict('records')
                        else: # if you rejeweled my items, whats the best i can do?
                            gear_type_items_df = pd.read_csv(f"Owned_Gear\\{filters['Account']}_Owned_Gear\\{filters['Account']}_Unsocketed_Owned_Gear\\{filters['Account']}_Unsocketed_Owned_{gear_type}.csv")
                            if "Unlocked" in gear_type_items_df.columns:
                                gear_type_items_df = gear_type_items_df.drop(columns=["Unlocked"])
                            gear_type_items_df = gear_type_items_df.drop_duplicates().reset_index(drop=True)
                            gear_type_items_df = gear_type_items_df[(gear_type_items_df['School'] == filters['School']) & (gear_type_items_df['Level'] <= filters['Level'])].reset_index(drop=True)
                            gear_type_items_df = filter_usability(filters['Usable In'], gear_type_items_df).reset_index(drop=True)
                            gear_type_items_df = filter_by_name(gear_type_items_df, filters, gear_type).reset_index(drop=True)
                            if gear_type == 'Pets':
                                gear_type_items_df = filter_pets_by_set_type(gear_type_items_df, filters['Set Type'], filters['School'], filters['Account']).reset_index(drop=True)
                            gear_type_items_df = add_total_jewel_columns(gear_type_items_df, gear_type, True)
                            if 'Starting Pips' in gear_type_items_df.columns and filters['Set Type'] != "Tank":
                                gear_type_items_df = gear_type_items_df[gear_type_items_df['Starting Pips'] == gear_type_items_df['Starting Pips'].max()].reset_index(drop=True)
                            gear_type_items_df = utils.objectively_best_gear(gear_type_items_df, filters)
                            print(gear_type_items_df) # testing
                            gear_type_items = gear_type_items_df.to_dict('records')
                    except:
                        singular_gear_type = gear_type[:-1] if gear_type != 'Boots' else gear_type
                        empty_item = utils.empty_item(singular_gear_type)
                        if gear_type in utils.clothing_gear_types:
                            empty_item['Total Sword Pins'] = 0
                            empty_item['Total Shield Pins'] = 0
                            empty_item['Total Power Pins'] = 0
                            empty_item['Pins Used'] = '(No Pins)'
                        elif gear_type in utils.accessory_gear_types:
                            empty_item['Total Tear Jewels'] = 0
                            empty_item['Total Circle Jewels'] = 0
                            empty_item['Total Square Jewels'] = 0
                            empty_item['Total Triangle Jewels'] = 0
                            empty_item['Jewels Used'] = '(No Jewels)'
                        gear[gear_type] = [empty_item]
                        continue
                    if not gear_type_items:
                        singular_gear_type = gear_type[:-1] if gear_type != 'Boots' else gear_type
                        empty_item = utils.empty_item(singular_gear_type)
                        if gear_type in utils.clothing_gear_types:
                            empty_item['Total Sword Pins'] = 0
                            empty_item['Total Shield Pins'] = 0
                            empty_item['Total Power Pins'] = 0
                            empty_item['Pins Used'] = '(No Pins)'
                        elif gear_type in utils.accessory_gear_types:
                            empty_item['Total Tear Jewels'] = 0
                            empty_item['Total Circle Jewels'] = 0
                            empty_item['Total Square Jewels'] = 0
                            empty_item['Total Triangle Jewels'] = 0
                            empty_item['Jewels Used'] = '(No Jewels)'
                        gear[gear_type] = [empty_item]
                    else:
                        gear[gear_type] = gear_type_items
            
            # get enemy information
            enemy_df = pd.read_csv(f"Other_CSVs\\Enemy_Stats.csv")
            wiz_level = filters['Level']
            enemy_df = enemy_df[(enemy_df['Low Level'] <= wiz_level) & (enemy_df['High Level'] >= wiz_level)].reset_index(drop=True)
            enemy_stats = enemy_df.iloc[0].to_dict()
            
            # get spell damage
            spell_df = pd.read_csv(f'Other_CSVs\\AOEs.csv')
            spell_df = spell_df[(spell_df['School'] == filters['School']) & (spell_df[f"{filters['Account']} Owned"])].reset_index(drop=True)
            
            # sets = []
            
            # for hat in gear['Hats']:
            #     for robe in gear['Robes']:
            #         for boots in gear['Boots']:
            #             for wand in gear['Wands']:
            #                 for athame in gear['Athames']:
            #                     for amulet in gear['Amulets']:
            #                         for ring in gear['Rings']:
            #                             for pet in gear['Pets']:
            #                                 for mount in gear['Mounts']:
            #                                     for deck in gear['Decks']:
            #                                         created_set = make_set([hat, robe, boots, wand, athame, amulet, ring, pet, mount, deck], filters, enemy_stats, spell_df)
            #                                         if filters['Owned']:
            #                                             sets.append(created_set)
            #                                         else:
            #                                             sets.extend(jewel_the_set(created_set, filters))

            # Example usage
            sets = generate_sets_parallel(gear, filters, enemy_stats, spell_df)
            
            df = pd.DataFrame(sets)
            # df = df[(df[f"{filters['School']} Accuracy"] >= utils.get_perfect_acc(filters['School'])) & (df["Power Pip Chance"] >= 100)] # testing
            if filters['Owned']: # testing
                df = sort_sets(df, filters['Set Type'], filters['School'])
            df = utils.reorder_df_cols(df, 11) # stats start after the 10 gear items
            print(df)
            df = df.iloc[:10000] # microsoft excel can't handle too big of files, keep it at 10,000
            if filters['School Stats Only']:
                df = utils.view_school_stats_only(filters['School'], df)
            # output
            file_path = 'CompleteW101Gear_Output.csv'
            try:
                df.to_csv(file_path, index=False)
            except:
                input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
                df.to_csv(file_path, index=False)
        else:
            return True
