import baseValues
import createAccessories
import createClothing
import createMounts
import createPets
import jewels

# school = "Fire" # use this for testing one school
schools = ["Death", "Fire", "Balance", "Myth", "Storm", "Ice", "Life"]
update_gear = True
update_jewels = True
update_base_values = True

def main():

    if update_gear:
        for school in schools:
            createClothing.create_clothing(school)
            createAccessories.create_accessories(school)
            createMounts.create_mounts(school)
            createPets.create_pets(school)

            print(f"\n\n\nAll {school} gear has been successfully updated\n")
            
    if update_jewels:
        jewels.collect_jewels()
        
        print(f"\n\n\nAll jewels have been successfully updated\n")
        
    if update_base_values:
        baseValues.get_base_values()
        
        print(f"\n\n\nAll base_values have been successfully updated\n")

if __name__ == "__main__":
    main()
