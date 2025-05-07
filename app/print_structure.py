import os

EXCLUDED_DIRS = {'__pycache__', 'venv', '.git', 'node_modules', '.idea'}

def print_tree(start_path, prefix="", output_lines=None):
    if output_lines is None:
        output_lines = []

    try:
        items = [i for i in os.listdir(start_path) if i not in EXCLUDED_DIRS]
    except PermissionError:
        return output_lines

    for index, name in enumerate(sorted(items)):
        path = os.path.join(start_path, name)
        connector = "└── " if index == len(items) - 1 else "├── "
        output_lines.append(prefix + connector + name)
        if os.path.isdir(path):
            extension = "    " if index == len(items) - 1 else "│   "
            print_tree(path, prefix + extension, output_lines)

    return output_lines

# Run and write to file
lines = print_tree(".")
with open("structure.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("✅ Folder structure saved to structure.txt")
