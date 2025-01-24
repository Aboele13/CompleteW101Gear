TODO:

- HECK FRONTEND, I'M DOING EVERYTHING IN CONSOLE, NO WEBSITE

- view sets
    - owned gear
        - jewels go with item, not accumulated on the set
            - will be repeats this way but thats okay (like 2 dmg on athame vs 1 on athame + 1 on ring)
        - need to write logic for it jeweling my gear
            - first filter out repeats from unsocketed_owned_gear
        - filters (dworgyn hat, resist pet)
            - maybe say what set i'm striving for?
                - mob hit, boss hit, healing, tanking
    - then all gear
        - 5 best from objectively best?
        - rather than attaching to items, jewels accumulate on the set to prevent repeats
        - filters (dworgyn hat, resist pet)

- go through and select everything that i and chris own

- updates that need to be made
    - max_level when new world
    - updateAOEs when new AEO/spellement
    - keep ownedGear up to date

- maintenance / code health ideas
    - clean up every thing that needs to be updated and put it in one updateVariables file
    - many functions are very similar, combine them to account for all uses in one spot
    - huge functions should be broken up
    - clean up the menu, specifically going "back"