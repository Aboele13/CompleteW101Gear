school = "Death"
update_gear = True

def main():
    import createAccessories
    import createClothing
    import createMounts

    clothing_dfs = createClothing.create_clothing()
    accessories_dfs = createAccessories.create_accessories()
    mounts_df = createMounts.create_mounts()
    
    print("\n\n\n")
    print(clothing_dfs[0])
    print(clothing_dfs[1])
    print(clothing_dfs[2])
    print(accessories_dfs[0])
    print(accessories_dfs[1])
    print(accessories_dfs[2])
    print(accessories_dfs[3])
    print(accessories_dfs[4])
    print(mounts_df)


if __name__ == "__main__":
    main()
    
