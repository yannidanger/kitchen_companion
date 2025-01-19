import os

def save_directory_structure_to_file(root_dir, output_file):
    """Save the directory structure of a given root directory to a text file."""
    def get_structure(dir_path, indent=0):
        structure = ""
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            structure += " " * indent + item + ("/" if os.path.isdir(item_path) else "") + "\n"
            if os.path.isdir(item_path):
                structure += get_structure(item_path, indent + 4)
        return structure

    structure = get_structure(root_dir)
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(structure)

# Replace 'root_path' with the path to your project directory
root_path = "G:/GroceriesProject/Kitchenapp"
output_file_path = "G:/GroceriesProject/folder_structure.txt"

save_directory_structure_to_file(root_path, output_file_path)
print(f"Folder structure saved to {output_file_path}")
