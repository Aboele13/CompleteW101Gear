from bs4 import BeautifulSoup

from webAccess import fetch_url_content, replace_img_with_filename


def get_items_list(url):
    print(f"\n\nLink: {url}\n")
    html_content = fetch_url_content(url)
    if html_content:
        # Parse HTML content and replace <img> tags with filenames
        soup = BeautifulSoup(html_content, 'html.parser')
        soup = replace_img_with_filename(soup)
        
        # Extract all visible text from the modified HTML content
        text_content = soup.get_text(separator='\n', strip=True)
        
        lines = text_content.splitlines()
        
        # Extract content between "Items which give this card" and "Jewels which give this card"
        start_index = None
        end_index = None
        for i, line in enumerate(lines):
            if line.startswith("Items which give this card"):
                start_index = i + 2
            elif line.startswith("Jewels which give this card"):
                end_index = i
                break
            elif line.startswith("Documentation on how to edit this page"):
                end_index = i
                break
        
        return lines[start_index:end_index], True
    else:
        return [], False

def create_damage_item_cards():
    
    bad_urls = []

    item_cards = ["Colossal", "Epic"]

    for card in item_cards:
        
        url = f"https://wiki.wizard101central.com/wiki/ItemCard:{card}"
        
        gear_per_item_card, success = get_items_list(url)
        
        if not success:
            print(f"Failed to fetch content from {url}")
            bad_urls.append(url)
        else:
            print(f"{card} Gear:")
            print(gear_per_item_card)
            # Open a file in write mode
            with open(f"Damage_ICs\\{card}_Gear.txt", "w") as file:
                # Write the string to the file
                file.write(", ".join(gear_per_item_card))

    return bad_urls
