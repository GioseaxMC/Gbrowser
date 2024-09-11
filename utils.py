import json
import os
import random as r
from pathlib import Path
import pygame as p
import pygame_canvas as c
import re
import clipboard
import string
import server as sv
import Levenshtein

ROOT = ""
def set_root(root):
    global ROOT
    ROOT = root

def replace_chars(string: str, old: str, new: str = "random"):
    if not type(string) == str:
        raise TypeError
    if not type(old) == str:
        raise TypeError
    if not type(new) == str and not new == "random":
        raise TypeError
    string = list(string)
    if new == "random":
        for key, char in enumerate(string):
            string[key] = chr(r.randint(65,90)) if char == old else char
    else:
        for key, char in enumerate(string):
            string[key] = new if char == old else char
    return "".join(string)

def serialize_dict(d):
    try:
        """Custom function to serialize a dictionary, skipping non-serializable items."""
        serializable_dict = {}
        for key, value in d.items():
            try:
                # Try to serialize the value using json.dumps
                json.dumps(value)
                serializable_dict[key] = value
            except TypeError:
                # Handle the non-serializable item by just noting its type or name
                serializable_dict[key] = f"<Non-serializable: {type(value).__name__}>"
    except Exception as e:
        serializable_dict = f"Error: {e}"
    return serializable_dict

def get_directory_size(directory):
    total_size = 0
    # Walk through all the directory
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            # Get the full file path
            filepath = os.path.join(dirpath, filename)
            # Add the file size to the total size
            total_size += os.path.getsize(filepath)
    return total_size / (1024 ** 3)

def print_dict(dict, indent = 4):
    print(json.dumps(serialize_dict(dict), indent=indent))

def det_color(string, default):
    if "error" in string.lower():
        return (200,0,0)
    elif "warning" in string.lower():
        return (200,175,0)
    elif "done" in string.lower():
        return (0,200,0)
    else:
        return default

def directory_to_dict(path):
    """Convert a directory tree to a dictionary where directories are keys."""
    path = Path(path)
    if not path.is_dir():
        raise ValueError("Provided path is not a directory")
    
    def scan_dir(directory):
        """Recursively scan the directory and return a dictionary representation."""
        result = {}
        for entry in directory.iterdir():
            if entry.is_dir():
                # Recurse into the subdirectory
                result[entry.name] = scan_dir(entry)
            else:
                # Add the file with its path
                result[entry.name] = str(entry.relative_to(path).as_posix())
        return result

    return scan_dir(path)

def print_dirs_from_dict(dct: dict, level = 0):
    for key, item in dct.items():
        print("|  "*level+"|_", key)
        if type(item) == dict:
            print_dirs_from_dict(item, level+1)

def list_to_string(lst):
    string = ""
    for item in lst:
        string += " "+item 
    return string[1:]

def delete_path(d, path_str):
    keys = path_str.split('/')
    current = d
    
    # Traverse to the second-to-last key
    for key in keys[:-1]:
        if key not in current:
            return False  # Path doesn't exist, nothing to delete
        current = current[key]
    
    # Delete the last key in the path
    last_key = keys[-1]
    if last_key in current:
        del current[last_key]
        return True
    return False  # The last key didn't exist

def create_path(d, path, ignore_root = 0, contains_file = 0):
    keys = path.split('/')
    current = d
    
    for key in keys[1:-1] if ignore_root else keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    last_key = keys[-1]
    
    if contains_file:
        current[last_key] = path
    else:
        if last_key not in current:
            current[last_key] = {}
    
    return d

def get_font_render(text, font: p.Font, color = "white"):
    return font.render(text, color=color, antialias=1)

def base_script(events, inputs, self):
    return {
        
    }

class DictToAttr:
    def __init__(self, dictionary):
        self.__dict__.update(dictionary)
    
    def __guarded_setattr__(self, name, value):
        # Example validation: Only allow attributes named 'name'
        if name not in self.__dict__:
            raise AttributeError(f"Cannot set attribute '{name}'")
        super().__setattr__(name, value)

def replace_placeholders(text, obj):
    # Regular expression to find %obj.attr% or %obj.num%
    pattern = re.compile(r'%(\w+)\.(\w+)%')
    
    def replacer(match):
        # Extract the attribute name from the match
        attribute_name = match.group(2)
        try:
            # Return the value of the attribute from the object
            value = getattr(obj, attribute_name)
            # Convert to string if it's not already
            return str(value)
        except AttributeError:
            # If there's an error, return the original placeholder
            return match.group(0)
    
    # Replace placeholders with attribute values
    return pattern.sub(replacer, text)

def at(string: str, idx: int):
    return string[idx % len(string)]

def trim(string: str, id1: int = 0, id2: int = ""):
    id2 = len(string) if id2 == "" else id2
    return string[id1 : id2]

def get(item, idx):
    try:
        return item[idx]
    except (IndexError, KeyError):
        return None

def strings_in_string(list_of_strings, main_string):
    return any(substring in main_string for substring in list_of_strings)

def generate_random_string(length):
    # Define the character set (letters, digits, punctuation)
    characters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    # Generate a random string
    random_string = ''.join(r.choice(characters) for _ in range(length))
    return random_string

def get_domains(source):
    if sv.file_exists(source):
        source = sv.read_json_file(sv.get_id_by_name(source))
    else:
        with open("domains.json", "r") as f:
            source = json.load(f)
    print("getting domains")
    return source

def write_domains(source, domains):
    if sv.file_exists(source):
        sv.update_json(sv.get_id_by_name(source), domains)
    else:
        with open("domains.json", "w") as f:
            json.dump(domains, f, indent=4)
    return source

class domains_editor:
    def add_domain(domain, ip):
        
        # get_domains <- change
        domains = get_domains("domains.json")

        if any(filter(lambda x: x["domain"] == domain, domains)):
            return (
                "",
                "Error: This domain is taken already."
            )
        else:
            key = generate_random_string(20)
            domains.append(
                {
                    "domain" : domain,
                    "ip" : ip,
                    "key" : key
                }
            )
            write_domains("domains.json", domains)
            clipboard.copy(key)
            return (
                f"API KEY: {key}",
                ""
            )

    def edit_domain(key, ip):

        domains = get_domains("domains.json")

        for item in domains:
            if item.get("key") == key:
                item.update(
                    {
                        "ip" : ip
                    }
                )
                write_domains("domains.json", domains)
                return (
                    "Done!",
                    ""
                )
        return (
            "",
            "Error: Invalid key"
        )

    def delete_domain(key):
        
        domains: list = get_domains("domains.json")

        for item in domains:
            if item.get("key") == key:
                domains.remove(item)
                write_domains("domains.json", domains)
                return (
                    "Done!",
                    ""
                )
        return (
            "",
            "Error: Invalid key"
        )
    
class topbar():
    def __init__(self) -> None:
        self.bg = c.sprite((c.rectangle(c.screen_size()[0], 50, (45, 45, 45)),), (0,0))
        self.bg.hide = 1
        self.bg.update(1)
        self.home_button = c.sprite((c.rectangle(30, 30, (60,60,60)),), (10, 10))
        self.home_button.update(1)
        self.bar = c.sprite((c.rectangle(750, 30, (60,60,60)),), (50, 10))
        self.bar.hide = 1
        self.bar.update(1)
        self.font = c.pygame.font.SysFont("consolas", 15)

    def update_sizes(self):
        self.bg.sprite_images[0] = c.rectangle(c.screen_size()[0], 50, (45, 45, 45))
        self.bg.update(1)
        
    def blits(self):
        c.blit(self.bg.appearence, self.bg.get_position())
        c.blit(self.home_button.appearence, self.home_button.get_position())
        c.blit(self.bar.appearence, self.bar.get_position())

    def update(self, current_name):
        self.blits()
        self.home_button.brightness = 255
        if self.home_button.touching_mouse():
            self.home_button.brightness = 225
        self.home_button.update()
        if self.home_button.clicked():
            return "homepage.rizz"
        c.text(f" H    {current_name}",
               position = (13, 17),
               color = "white",
               font = self.font)
        return None
            
def browse(domains: list, input):
    domains = sorted(domains, key=lambda x: Levenshtein.ratio(x["domain"], input), reverse=1)
    return domains
