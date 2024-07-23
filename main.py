import createClothing

school = "Ice"
update_gear = True

def main():
    clothing_dfs = createClothing.create_clothing()
    print("\n\n\n")
    print(clothing_dfs[0])
    print(clothing_dfs[1])
    print(clothing_dfs[2])

if __name__ == "__main__":
    main()
    
