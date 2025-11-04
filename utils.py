import json


def load_profile(filename):
    with open (filename, 'r', encoding='utf-8') as f:
        profile = json.load(f)
        return profile
    
    