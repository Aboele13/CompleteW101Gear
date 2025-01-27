TODO:

- HECK FRONTEND, I'M DOING EVERYTHING IN CONSOLE, NO WEBSITE

- view sets

    - bug where switching to Mob set type keeps "triple double" pet from other set

    - source doesn't matter if owned is true

    - non-owned gear
        - need to jewel them
            - enchant jewels should only be used if mob set
            - accumulate jewels into "Jewels Used" column
        - need to add personal stats

    - owned gear
        - need to write logic for it jeweling my gear
            - enchant jewels should only be used if mob set
            - jewels used is appended to end of item name, not accumulated on the set





- regular updates that need to be made
    - max_level when new world
    - updateAOEs when new AEO/spellement
    - keep ownedGear up to date

- new features to add
    - add in logic for calculating healing set
    - add in logic for secondary school logic

- maintenance / code health ideas
    - clean up every thing that needs to be updated and put it in one updateVariables file
    - many functions are very similar, combine them to account for all uses in one spot
    - huge functions should be broken up
    - clean up the menu, specifically going "back"