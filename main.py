import createAccessories
import createClothing
import createMounts
import createPets

# school = "Balance" # use this for testing one school
schools = ["Death", "Fire", "Balance", "Myth", "Storm", "Ice", "Life"]
update_gear = True

def main():

    if update_gear:
        for school in schools:
            clothing_dfs = createClothing.create_clothing(school)
            accessories_dfs = createAccessories.create_accessories(school)
            mounts_df = createMounts.create_mounts(school)
            pets_df = createPets.create_pets(school)
        
            print(f"\n\n\nAll {school} gear has been successfully updated\n")

if __name__ == "__main__":
    main()
