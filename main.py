import baseValues
import createAccessories
import createClothing
import createMounts
import createPets
import jewels
import setBonuses

schools = ["Death", "Fire", "Balance", "Myth", "Storm", "Ice", "Life"]
update_gear = True
update_jewels = False
update_base_values = False
update_set_bonuses = False

def main():

    bad_urls = []

    if update_gear:
        for school in schools: # run it for each school
            bad_urls.extend(createClothing.create_clothing(school))
            bad_urls.extend(createAccessories.create_accessories(school))
            bad_urls.extend(createMounts.create_mounts(school))
            bad_urls.extend(createPets.create_pets(school))

            print(f"\n\n\nAll {school} gear has been successfully updated\n")
            
    if update_jewels:
        bad_urls.extend(jewels.collect_jewels(schools)) # each school created in function
        
        print(f"\n\n\nAll jewels have been successfully updated\n")
        
    if update_base_values:
        baseValues.get_base_values(schools) # each school created in function
        
        print(f"\n\n\nAll base values have been successfully updated\n")
        
    if update_set_bonuses:
        for school in schools: # run it for each school
            bad_urls.extend(setBonuses.get_set_bonuses(school))
        
            print(f"\n\n\nAll {school} set bonuses have been successfully updated\n")
    
    # print which links did not work and need to be rechecked
    if bad_urls:
        print("List of URLs that did not process properly:\n")
        
        for bad_url in bad_urls:
            print(bad_url)
        
        print("\n")
        
    else:
        print("Every link worked correctly and all the desired updates were made successfully\n")

if __name__ == "__main__":
    main()