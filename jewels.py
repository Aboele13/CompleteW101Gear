from itertools import combinations_with_replacement

import pandas as pd

# remove these, should be getting FROM HTML
school = "Death"
level = 170

# this needs to involve web scraping
def get_jewel_effects(school, level):
    return [155, 11, 6, 550, 16, 10]

def jewel_the_gear(df):
    # Create new rows for each item with each variation
    new_rows = []
    for i, row in df.iterrows():
        # original (unjeweled)
        new_rows.append(row.to_dict())
        
        # unlocked combinations
        if any(row[col] != 0 for col in ['Unlocked Tear', 'Unlocked Circle', 'Unlocked Square', 'Unlocked Triangle']):
            new_rows.extend(jewel_unlocked_sockets(row))
        
        # locked combinations
        if any(row[col] != 0 for col in ['Locked Tear', 'Locked Circle', 'Locked Square', 'Locked Triangle']):
            new_rows.extend(jewel_locked_sockets(row))
    
    return pd.DataFrame(new_rows)

def jewel_unlocked_sockets(item):
    # Define the conversions
    conversions = {
        'Unlocked Tear': ('Health', jewel_effects[0]),
        'Unlocked Circle': [('Damage', jewel_effects[1]), ('Pierce', jewel_effects[2])],
        'Unlocked Square': ('Health', jewel_effects[3]),
        'Unlocked Triangle': [('Accuracy', jewel_effects[4]), ('Pips', jewel_effects[5])]
    }
    
    # Start with the base item, converting Tears and Squares
    base_item = item.copy()
    for col, (target, value) in [('Unlocked Tear', conversions['Unlocked Tear']), ('Unlocked Square', conversions['Unlocked Square'])]:
        base_item[target] += value * base_item[col]
        base_item[col] = 0

    # List to hold all variants
    variants = []

    # Generate all unique combinations for Circles and Triangles
    circle_combinations = list(combinations_with_replacement(conversions['Unlocked Circle'], item['Unlocked Circle']))
    triangle_combinations = list(combinations_with_replacement(conversions['Unlocked Triangle'], item['Unlocked Triangle']))

    # Create variants based on the combinations
    for circle_combo in circle_combinations:
        for triangle_combo in triangle_combinations:
            variant = base_item.copy()
            
            # Apply circle effects
            for (effect, value), count in {(effect, value): circle_combo.count((effect, value)) for (effect, value) in set(circle_combo)}.items():
                variant[effect] += value * count
            
            # Apply triangle effects
            for (effect, value), count in {(effect, value): triangle_combo.count((effect, value)) for (effect, value) in set(triangle_combo)}.items():
                variant[effect] += value * count
            
            # Reset conversion items to 0
            for key in ['Unlocked Tear', 'Unlocked Circle', 'Unlocked Square', 'Unlocked Triangle']:
                variant[key] = 0
            
            # Convert to dict and add Name
            variant_dict = variant.to_dict()
            variant_dict['Name'] = item['Name']  # Keep the original name for all variants
            
            variants.append(variant_dict)
    
    return variants

def jewel_locked_sockets(item):
    item["Unlocked Tear"] += item["Locked Tear"]
    item["Unlocked Circle"] += item["Locked Circle"]
    item["Unlocked Square"] += item["Locked Square"]
    item["Unlocked Triangle"] += item["Locked Triangle"]
    
    item["Locked Tear"] = 0
    item["Locked Circle"] = 0
    item["Locked Square"] = 0
    item["Locked Triangle"] = 0
    
    return jewel_unlocked_sockets(item)

jewel_effects = get_jewel_effects(school, level)