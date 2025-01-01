import pandas as pd

import utils

all_gear_types = {'Hats', 'Robes', 'Boots', 'Wands', 'Athames', 'Amulets', 'Rings', 'Pets', 'Mounts', 'Decks'}

def reorder_df_cols(df): # health, damage, flat damage, resist, flat resist, accuracy, critical, critical block, pierce, stun resist, incoming, outgoing, pip conserve, power pip, shadow pip, archmastery
    
    ordered_stats = ['Max Health']
    schools = ['Global', 'Fire', 'Ice', 'Storm', 'Myth', 'Life', 'Death', 'Balance', 'Shadow']
    
    for stat in ['Damage', 'Flat Damage', 'Resistance', 'Flat Resistance', 'Accuracy', 'Critical Rating', 'Critical Block Rating', 'Armor Piercing']:
        for school in schools:
            ordered_stats.append(school + " " + stat)
    
    for stat in ['Stun Resistance', 'Incoming Healing', 'Outgoing Healing']:
        ordered_stats.append(stat)
    
    for school in schools:
        ordered_stats.append(school + " Pip Conversion Rating")
    
    for stat in ['Power Pip Chance', 'Shadow Pip Rating', 'Archmastery Rating']:
        ordered_stats.append(stat)
    
    for i in reversed(range(len(ordered_stats))):
        stat_col = df.pop(ordered_stats[i])
        df.insert(2, ordered_stats[i], stat_col)
    
    return df

def filter_by_sources(df, good_sources):
    
    def check_sources(item_sources):
        item_sources_list = [source.strip() for source in item_sources.split(',')]
        for item_source in item_sources_list:
            if item_source in good_sources:
                return True
        return False

    df['match'] = df['Source'].apply(check_sources)
    df = df[df['match']]
    return df.drop('match', axis=1)

def is_int(input):
    try:
        int(input)
        return True
    except:
        return False

def view_gear():
    
    # collect correct csv
    school = "All"
    gear_type = "Hats"
    
    # filters
    filters = {
        'Level': 170,
        'Usable In': 'Everything',
        'School Stats Only': True,
        'Good Sources': {"Gold Vendor", "Drop", "Bazaar", "Crafting", "Gold Key", "Stone Key", "Wooden Key", "Housing Gauntlet", "Rematch", "Quest", "Fishing"},
        'Bad Sources': {"One Shot Housing Gauntlet", "Raid", "Crowns", "Gift Card", "Event Drop"},
    }
    
    action = 'Nothing'
    
    while action.lower() not in {'b', 'q'}:
        
        # collect correct csv
        df = pd.read_csv(f'Gear\\{school}_Gear\\{school}_{gear_type}.csv')
        
        # filters
        for filter in filters:
            if filter == 'Level':
                df = df[df[filter] <= filters[filter]]
            elif filter == 'Name':
                df = df[df[filter].str.contains(filters[filter], case=False)]
            elif filter == 'Gear Set':
                df = df[df[filter] != 'No Gear Set']
            elif filter == 'Usable In':
                battle = filters[filter]
                if battle == 'Everything':
                    df = df[df[filter] == 'Everything']
                elif battle == 'PVP':
                    df = df[df[filter].isin({'Everything', 'PVP'})]
                elif battle == 'Deckathalon':
                    df = df[df[filter].isin({"Everything", 'Deckathalon'})]
            elif filter == 'Good Sources':
                if gear_type != 'Pets':
                    df = filter_by_sources(df, filters[filter])
            elif filter == 'Bad Sources' or filter == 'School Stats Only':
                pass
            else:
                df = df[df[filter] >= filters[filter]]
        
        # show wanted columns
        df = reorder_df_cols(df)
        if filters['School Stats Only']:
            curr_school = 'Global' if school == 'All' else school
            cols_to_drop = []
            for col in df.columns:
                pot_school = col.split()[0]
                if pot_school in utils.all_stat_schools and pot_school != curr_school and col != "Shadow Pip Rating":
                    cols_to_drop.append(col)
            df = df.drop(cols_to_drop, axis=1)
            df.columns = [col.replace(curr_school + " ", "") for col in df.columns]
            df = df.sort_values(by=['Damage', 'Resistance', 'Max Health', 'Critical Rating', 'Armor Piercing'], ascending=[False, False, False, False, False])
        
        # only objectively best
        
        # output
        file_path = 'CompleteW101Gear_Output.csv'
        try:
            df.to_csv(file_path, index=False)
        except:
            input(f"\n{file_path} needs to be closed before it can be written to.\nClose the file and hit enter\n")
            df.to_csv(file_path, index=False)
        
        # print current statuses/filters
        print(f'\nSchool: {school}')
        print(f'Gear Type: {gear_type}')
        for filter in filters:
            print(f'{filter}: {filters[filter]}')
        
        # next action
        action = input("\nWhat would you like to change? Or b to go back to the menu or q to quit\n\n")
        
        if action.lower() == 'b':
            return True
        elif action.lower() == 'q':
            return False
        elif action.lower() == 'school':
            new_school = 'Nothing'
            while new_school not in utils.schools_of_items:
                new_school = input('\nPlease enter the new school to view:\n\n')
            school = 'All' if new_school == 'Global' else new_school
        elif action.lower() == 'gear type':
            new_gear_type = 'Nothing'
            while new_gear_type not in all_gear_types:
                new_gear_type = input('\nPlease enter the new gear type to view:\n\n')
            gear_type = new_gear_type
        elif action == 'Name':
            filters[action] = input(f"\nSearch by name:\n\n")
        elif action == 'Gear Set':
            if action in filters:
                filters.pop(action)
            else:
                filters[action] = True
        elif action == 'Usable In':
            battle = 'Nothing'
            while battle not in {'All', 'Everything', 'PVP', 'Deckathalon'}:
                battle = input("\nWhere should gear be usable: All, Everything, PVP, Deckathalon\n\n")
            if battle == 'All':
                if action in filters:
                    filters.pop(action)
            else:
                filters[action] == battle
        elif action == 'Source' or action == 'Good Sources' or action == 'Bad Sources':
            source = 'Nothing'
            while source not in filters['Good Sources'] and source not in filters['Bad Sources']:
                source = input("\nWhich source would you like to add or remove?\n\n")
            if source in filters['Good Sources']:
                filters['Good Sources'].remove(source)
                filters['Bad Sources'].add(source)
            else:
                filters['Good Sources'].add(source)
                filters['Bad Sources'].remove(source)
        elif action == 'School Stats Only':
            filters['School Stats Only'] = not filters['School Stats Only']
        elif action in df.columns:
            num = -1
            while num == -1:
                num = input(f"\nInput the minimum {action} value\n\n")
                if is_int(num):
                    if int(num) == 0 and action in filters:
                        filters.pop(action)
                    else:
                        filters[action] = int(num)
                else:
                    print('\nInvalid value, please retry')
        else:
            print('\nInvalid value, please retry')
