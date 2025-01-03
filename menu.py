all_gear_types = ['Hats', 'Robes', 'Boots', 'Wands', 'Athames', 'Amulets', 'Rings', 'Pets', 'Mounts', 'Decks']
all_jewel_shapes = ['Tear', 'Circle', 'Square', 'Triangle', 'Sword', 'Shield', 'Power']

def success_return_menu():
    action = input("\nThe process is complete. Would you like to do anything else?\n\n[1] Yes\n[2] No\n\n")
    if action == '1' or not action:
        start_menu()
    elif action == '2':
        return
    else:
        invalid_input_message()
        success_return_menu()

def not_added_yet_message():
    print("\nSorry, this option hasn't been implemented yet. Returning to previous page")

def invalid_input_message():
    print("\nInvalid input. Please try again")

def print_gear_type_options():
    for i in range(len(all_gear_types)):
        print(f"[{(i + 1) % 10}] {all_gear_types[i]}")
    print("")

def nums_to_gear_types(nums):
    gear_types = []
    if min(nums) < 0 or max(nums) > 9:
        return gear_types
    for i in range(len(all_gear_types)):
        if ((i + 1) % 10) in nums:
            gear_types.append(all_gear_types[i])
    return gear_types

def confirm_selected_gear_types(select_gear_types):
    
    print(f"\nYou chose:\n{select_gear_types}")
    
    action = input("Is this correct?\n\n[1] Yes\n[2] No\n[b] Back\n[q] Quit\n\n")
    
    if action.lower() == 'q':
        return
    elif action.lower() == 'b' or action == '2':
        update_gear_select_types_menu()
    elif action == '1' or not action:
        print("\nBeginning to update gear...\n")
        from updateGear import update_gear
        update_gear(select_gear_types)
        success_return_menu()

def confirm_selected_jewel_shapes(select_jewel_shapes):
    
    print(f"\nYou chose:\n{select_jewel_shapes}")
    
    action = input("Is this correct?\n\n[1] Yes\n[2] No\n[b] Back\n[q] Quit\n\n")
    
    if action.lower() == 'q':
        return
    elif action.lower() == 'b' or action == '2':
        update_jewels_select_shapes_menu()
    elif action == '1' or not action:
        print("\nBeginning to update jewels...\n")
        from updateJewels import update_jewels
        update_jewels(select_jewel_shapes)
        success_return_menu()

def update_gear_select_types_menu():
    
    print("\nSelect the gear types as a comma separated list (ex. 1,4,5), or b to go Back, or q to Quit\n")
    print_gear_type_options()
    
    action = input("")
    
    if action.lower() == 'q':
        return
    elif action.lower() == 'b':
        return update_gear_menu()
    else:
        select_gear_types = []
        try:
            select_gear_types = nums_to_gear_types(set([int(num) for num in action.split(',')]))
        except:
            invalid_input_message()
            update_gear_select_types_menu()
        if len(select_gear_types) > 0:
            confirm_selected_gear_types(select_gear_types)
        else:
            invalid_input_message()
            update_gear_select_types_menu()

def update_gear_menu():
    
    action = input("\nWhat gear types would you like to update?\n\n[1] All Gear Types\n[2] Select Gear Types\n[b] Back\n[q] Quit\n\n")
    
    if action.lower() == 'q':
        return
    elif action.lower() == 'b':
        update_info_menu()
    elif action == '1' or not action:
        print("\nBeginning to update gear...\n")
        from updateGear import update_gear
        update_gear(all_gear_types)
        success_return_menu()
    elif action == '2':
        update_gear_select_types_menu()
    else:
        invalid_input_message()
        update_gear_menu()

def print_jewel_shapes_options():
    for i in range(len(all_jewel_shapes)):
        print(f"[{i + 1}] {all_jewel_shapes[i]}")
    print("")

def nums_to_jewel_shapes(nums):
    jewel_shapes = []
    if min(nums) < 1 or max(nums) > 7:
        return jewel_shapes
    for i in range(len(all_jewel_shapes)):
        if (i + 1) in nums:
            jewel_shapes.append(all_jewel_shapes[i])
    return jewel_shapes

def update_jewels_select_shapes_menu():
    print("\nSelect the jewel shapes as a comma separated list (ex. 1,2,4), or b to go Back, or q to Quit\n")
    print_jewel_shapes_options()
    
    action = input("")
    
    if action.lower() == 'q':
        return
    elif action.lower() == 'b':
        return update_jewels_menu()
    else:
        select_jewel_shapes = []
        try:
            select_jewel_shapes = nums_to_jewel_shapes(set([int(num) for num in action.split(',')]))
        except:
            invalid_input_message()
            update_jewels_select_shapes_menu()
        if len(select_jewel_shapes) > 0:
            confirm_selected_jewel_shapes(select_jewel_shapes)
        else:
            invalid_input_message()
            update_jewels_select_shapes_menu()

def update_jewels_menu():
    
    action = input("\nWhat jewel shapes would you like to update?\n\n[1] All Jewel Shapes\n[2] Select Jewel Shapes\n[b] Back\n[q] Quit\n\n")
    
    if action.lower() == 'q':
        return
    if action.lower() == 'b':
        update_info_menu()
    elif action == '1' or not action:
        print("\nBeginning to update jewels...\n")
        from updateJewels import update_jewels
        update_jewels(all_jewel_shapes)
        success_return_menu()
    elif action == '2':
        update_jewels_select_shapes_menu()
    else:
        invalid_input_message()
        update_jewels_menu()

def update_info_menu():
    
    action = input("\nWhat would you like to update?\n\n[1] Update Everything\n[2] Update Gear\n[3] Update Jewels\n[4] Update Base Values\n[5] Update Set Bonuses\n[b] Back\n[q] Quit\n\n")
    
    if action.lower() == 'q':
        return
    elif action.lower() == 'b':
        start_menu()
    elif action == '1' or not action:
        # update gear
        print("\nBeginning to update gear...\n")
        from updateGear import update_gear
        update_gear(all_gear_types)
        # update jewels
        print("\nBeginning to update jewels...\n")
        from updateJewels import update_jewels
        update_jewels(all_jewel_shapes)
        # update base values
        print("\nBeginning to update base values...\n")
        from updateBaseValues import update_base_values
        update_base_values()
        # update set bonuses
        print("\nBeginning to update set bonuses...\n")
        from updateSetBonuses import update_set_bonuses
        update_set_bonuses()
        success_return_menu()
    elif action == '2':
        update_gear_menu()
    elif action == '3':
        update_jewels_menu()
    elif action == '4':
        print("\nBeginning to update base values...\n")
        from updateBaseValues import update_base_values
        update_base_values()
        success_return_menu()
    elif action == '5':
        print("\nBeginning to update set bonuses...\n")
        from updateSetBonuses import update_set_bonuses
        update_set_bonuses()
        success_return_menu()
    else:
        invalid_input_message()
        update_info_menu()

def owned_gear_menu():
    not_added_yet_message()
    start_menu()

def view_sets_menu():
    not_added_yet_message()
    start_menu()

def create_set_menu():
    not_added_yet_message()
    start_menu()

def start_menu():
    
    action = input("\nWhat would you like to do?\n\n[1] Update Information\n[2] View Gear\n[3] Modify Owned Gear\n[4] View Sets\n[5] Create Set\n[q] Quit\n\n")
    
    if action.lower() == 'q':
        return
    elif action == '1' or not action:
        update_info_menu()
    elif action == '2':
        from viewGear import view_gear
        if view_gear():
            start_menu()
    elif action == '3':
        owned_gear_menu()
    elif action == '4':
        view_sets_menu()
    elif action == '5':
        create_set_menu()
    else:
        invalid_input_message()
        start_menu()
