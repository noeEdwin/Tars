import os

# Define keywords that identify your main "Hubs"
INTERESTS = {
    "AI & Agents": ["Tars", "LangGraph", "LangChainTutorial"],
    "School":  ["University", "automata_languages", "data_bases", "grafication",
    "interface_language", "network_computer", "software_engineering"],
    "Personal": ["Downloads", "Documents", "Personal_Projects", "Personal_Studies", "Pictures", "Chinese_studies", "Wallpapers"],
    "Unknowing":["Others"]
}

# Directories that are "black holes" - stay away!
IGNORE = {'miniconda3', 'anaconda3', 'site-packages', '.git', '__pycache__', 'node_modules', 'snap',
        'etc', 'bin', 'root', 'ssh', 'gnupg'}

def build_system_map(start_path):
    system_map = {category: [] for category in INTERESTS}
    system_map["Other Projects"] = []

    for root, dirs, files in os.walk(start_path):
        # 1. Pruning
        dirs[:] = [d for d in dirs if d not in IGNORE and not d.startswith('.')]
        
        folder_name = os.path.basename(root)
        
        tagged = False
        for category, keywords in INTERESTS.items():
            if any(key in folder_name for key in keywords):
                system_map[category].append(root)
                tagged = True
                break 
        
        if not tagged:
            if any(f in ['manage.py', 'package.json', 'Modelfile', '.ipynb'] for f in files):
                system_map["Other Projects"].append(root)

    return system_map

if __name__ == "__main__":
    home = os.path.expanduser("~")
    my_map = build_system_map(home)
    
    print(f"\n--- TARS System Map for {home} ---")
    for category, paths in my_map.items():
        if paths:
            print(f"\n[ {category} ]")
            for p in paths:
                print(f" -> {p}")