import pandas as pd

import utils

all_gear_types = {'Hats', 'Robes', 'Boots', 'Wands', 'Athames', 'Amulets', 'Rings', 'Pets', 'Mounts', 'Decks'}

def objectively_best(df):
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

def view_gear():
    
    # collect correct csv
    school = "All"
    gear_type = "Hats"
    
    # filters
    filters = {
        'Level': 170,
        'Usable In': 'Everything',
        'Objectively Best': False,
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
                if gear_type != 'Pets':
                    df = filter_by_sources(df, filters[filter]).reset_index(drop=True)
            elif filter == 'Bad Sources' or filter == 'School Stats Only' or filter == 'Objectively Best':
                pass
            else:
                df = df[df[filter] >= filters[filter]].reset_index(drop=True)
        
        # show wanted columns
        if filters['School Stats Only']:
            curr_school = 'Global' if school == 'All' else school
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
            df = objectively_best(df)
        
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
        elif action.lower() == 'all':
            filters = {
                'Level': 170,
                'Usable In': 'All',
                'Objectively Best': False,
                'School Stats Only': False,
                'Good Sources': filters['Good Sources'] | filters['Bad Sources'],
                'Bad Sources': set(),
            }
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
        elif action == 'Objectively Best':
            filters['Objectively Best'] = not filters['Objectively Best']
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
