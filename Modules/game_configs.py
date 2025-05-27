#!/usr/bin/env python3
"""
Game System Configurations for Multi-Game PDF Processor
Defines supported game systems, editions, books, and detection patterns
"""

# Game system configurations for multi-game support
GAME_CONFIGS = {
    "D&D": {
        "full_name": "Dungeons & Dragons",
        "editions": ["1st", "2nd", "3rd", "3.5", "4th", "5th"],
        "books": {
            "1st": ["DMG", "PHB", "MM", "FF", "DD", "UA", "WSG", "DSG"],
            "2nd": ["DMG", "PHB", "MM", "MC", "TOM", "PHBR", "DMGR"],
            "3rd": ["DMG", "PHB", "MM", "FRCS", "ELH"],
            "3.5": ["DMG", "PHB", "MM", "ELH", "FRCS", "ECS"],
            "4th": ["DMG", "PHB", "MM", "MM2", "MM3"],
            "5th": ["DMG", "PHB", "MM", "XGE", "TCE", "VGM", "MTF", "FTD"]
        },
        "collection_prefix": "dnd",
        "detection_keywords": [
            "dungeons & dragons", "d&d", "ad&d", "thac0", "armor class",
            "saving throw", "hit dice", "experience points", "dungeon master",
            "player character", "non-player character", "treasure type"
        ],
        "schema_fields": ["armor_class", "hit_points", "thac0", "saving_throws", "movement", "hit_dice"],
        "categories": {
            "DMG": ["Combat", "Magic", "Monsters", "Treasure", "Campaign", "Tables", "Rules", "NPCs"],
            "PHB": ["Character Creation", "Spells", "Equipment", "Combat", "Skills", "Rules"],
            "MM": ["Monsters", "Combat", "Special Abilities", "Ecology", "Treasure"]
        }
    },

    "Pathfinder": {
        "full_name": "Pathfinder Roleplaying Game",
        "editions": ["1st", "2nd"],
        "books": {
            "1st": ["Core", "APG", "Bestiary", "Bestiary2", "Bestiary3", "GMG", "UC", "UM"],
            "2nd": ["Core", "APG", "Bestiary", "Bestiary2", "Bestiary3", "GMG", "LOCG", "LOWG"]
        },
        "collection_prefix": "pf",
        "detection_keywords": [
            "pathfinder", "paizo", "base attack bonus", "combat maneuver", "golarion",
            "spell resistance", "caster level", "skill ranks", "feat", "trait"
        ],
        "schema_fields": ["ac", "hp", "bab", "saves", "cmb", "cmd", "sr", "skills"],
        "categories": {
            "Core": ["Combat", "Spells", "Character", "Equipment", "Rules", "Classes", "Races"],
            "APG": ["Classes", "Spells", "Feats", "Equipment", "Rules"],
            "Bestiary": ["Creatures", "Combat", "Special Abilities", "Ecology", "Templates"]
        }
    },

    "Call of Cthulhu": {
        "full_name": "Call of Cthulhu",
        "editions": ["6th", "7th"],
        "books": {
            "6th": ["Keeper", "Investigator", "Companion"],
            "7th": ["Keeper", "Investigator", "Companion", "Pulp"]
        },
        "collection_prefix": "coc",
        "detection_keywords": [
            "call of cthulhu", "sanity", "chaosium", "mythos", "investigator",
            "keeper", "lovecraft", "elder thing", "great old one", "sanity loss"
        ],
        "schema_fields": ["sanity", "skills", "characteristics", "mythos", "luck", "magic_points"],
        "categories": {
            "Keeper": ["Investigation", "Sanity", "Skills", "Mythos", "Combat", "Rules", "Scenarios"],
            "Investigator": ["Character Creation", "Skills", "Equipment", "Occupations", "Rules"]
        }
    },

    "Vampire": {
        "full_name": "Vampire: The Masquerade",
        "editions": ["1st", "2nd", "3rd", "V20", "V5"],
        "books": {
            "1st": ["Core"],
            "2nd": ["Core", "Players"],
            "3rd": ["Core", "Players"],
            "V20": ["Core", "Players", "Companion"],
            "V5": ["Core", "Players", "Companion", "Coteries"]
        },
        "collection_prefix": "vtm",
        "detection_keywords": [
            "vampire", "world of darkness", "blood pool", "disciplines", "masquerade",
            "kindred", "camarilla", "sabbat", "generation", "embrace"
        ],
        "schema_fields": ["blood_pool", "disciplines", "humanity", "generation", "willpower"],
        "categories": {
            "Core": ["Character", "Disciplines", "Social", "Combat", "Supernatural", "Rules", "Clans"]
        }
    },

    "Werewolf": {
        "full_name": "Werewolf: The Apocalypse",
        "editions": ["1st", "2nd", "3rd", "W20", "W5"],
        "books": {
            "1st": ["Core"],
            "2nd": ["Core", "Players"],
            "3rd": ["Core", "Players"],
            "W20": ["Core", "Players", "Companion"],
            "W5": ["Core", "Players"]
        },
        "collection_prefix": "wta",
        "detection_keywords": [
            "werewolf", "apocalypse", "rage", "gnosis", "garou",
            "umbra", "spirit", "gaia", "wyrm", "weaver"
        ],
        "schema_fields": ["rage", "gnosis", "willpower", "renown", "gifts"],
        "categories": {
            "Core": ["Character", "Gifts", "Social", "Combat", "Supernatural", "Rules", "Tribes"]
        }
    },

    "Cyberpunk": {
        "full_name": "Cyberpunk",
        "editions": ["2020", "RED"],
        "books": {
            "2020": ["Core", "Chrome", "Night City"],
            "RED": ["Core", "Data Pack"]
        },
        "collection_prefix": "cp",
        "detection_keywords": [
            "cyberpunk", "netrunner", "corpo", "edgerunner", "night city",
            "cyberware", "netspace", "ice", "daemon"
        ],
        "schema_fields": ["ref", "tech", "int", "cool", "attr", "luck", "ma", "body", "emp"],
        "categories": {
            "Core": ["Character", "Skills", "Combat", "Netrunning", "Equipment", "Rules"]
        }
    },

    "Shadowrun": {
        "full_name": "Shadowrun",
        "editions": ["1st", "2nd", "3rd", "4th", "5th", "6th"],
        "books": {
            "1st": ["Core"],
            "2nd": ["Core"],
            "3rd": ["Core", "Matrix", "Magic"],
            "4th": ["Core", "Arsenal", "Augmentation"],
            "5th": ["Core", "Data Trails", "Street Grimoire"],
            "6th": ["Core", "Firing Squad", "Street Wyrd"]
        },
        "collection_prefix": "sr",
        "detection_keywords": [
            "shadowrun", "matrix", "decker", "rigger", "street samurai",
            "essence", "karma", "nuyen", "corp", "sprawl"
        ],
        "schema_fields": ["body", "agility", "reaction", "strength", "charisma", "intuition", "logic", "willpower"],
        "categories": {
            "Core": ["Character", "Skills", "Combat", "Matrix", "Magic", "Equipment", "Rules"]
        }
    },

    "Traveller": {
        "full_name": "Traveller",
        "editions": ["Classic", "MegaTraveller", "TNE", "T4", "T5", "Mongoose", "Mongoose2"],
        "books": {
            "Classic": ["Core", "Book1", "Book2", "Book3", "Book4", "Book5", "Book6", "Book7", "Book8"],
            "MegaTraveller": ["Core", "Players", "Referee"],
            "TNE": ["Core", "Players"],
            "T4": ["Core"],
            "T5": ["Core"],
            "Mongoose": ["Core", "High Guard", "Mercenary", "Trader", "Scout"],
            "Mongoose2": ["Core", "High Guard", "Central Supply", "Vehicle Handbook", "Robot Handbook"]
        },
        "collection_prefix": "traveller",
        "detection_keywords": [
            "traveller", "imperium", "jump drive", "starship", "subsector",
            "mongoose publishing", "far future", "2d6", "characteristic",
            "universal world profile", "uwp", "tech level", "sophont"
        ],
        "schema_fields": ["strength", "dexterity", "endurance", "intelligence", "education", "social"],
        "categories": {
            "Core": ["Character", "Skills", "Combat", "Starships", "Trade", "Equipment", "Rules", "Worlds"],
            "High Guard": ["Starships", "Combat", "Navy", "Military", "Equipment"],
            "Mercenary": ["Combat", "Military", "Equipment", "Tactics"],
            "Trader": ["Trade", "Commerce", "Economics", "Starships"],
            "Scout": ["Exploration", "Survey", "Starships", "Equipment"]
        }
    }
}

# Book abbreviation expansions by game type
BOOK_EXPANSIONS = {
    "D&D": {
        "DMG": "Dungeon Masters Guide",
        "PHB": "Players Handbook",
        "MM": "Monster Manual",
        "FF": "Fiend Folio",
        "DD": "Deities and Demigods",
        "UA": "Unearthed Arcana",
        "WSG": "Wilderness Survival Guide",
        "DSG": "Dungeoneer's Survival Guide",
        "MC": "Monstrous Compendium",
        "TOM": "Tome of Magic",
        "PHBR": "Player's Handbook Rules Supplement",
        "DMGR": "Dungeon Master's Guide Rules Supplement",
        "FRCS": "Forgotten Realms Campaign Setting",
        "ELH": "Epic Level Handbook",
        "ECS": "Eberron Campaign Setting",
        "XGE": "Xanathar's Guide to Everything",
        "TCE": "Tasha's Cauldron of Everything",
        "VGM": "Volo's Guide to Monsters",
        "MTF": "Mordenkainen's Tome of Foes",
        "FTD": "Fizban's Treasury of Dragons"
    },
    "Pathfinder": {
        "Core": "Core Rulebook",
        "APG": "Advanced Player's Guide",
        "Bestiary": "Bestiary",
        "Bestiary2": "Bestiary 2",
        "Bestiary3": "Bestiary 3",
        "GMG": "GameMastery Guide",
        "UC": "Ultimate Combat",
        "UM": "Ultimate Magic",
        "LOCG": "Lost Omens Character Guide",
        "LOWG": "Lost Omens World Guide"
    },
    "Call of Cthulhu": {
        "Keeper": "Keeper Rulebook",
        "Investigator": "Investigator Handbook",
        "Companion": "Keeper's Companion",
        "Pulp": "Pulp Cthulhu"
    },
    "Vampire": {
        "Core": "Core Rulebook",
        "Players": "Players Guide",
        "Companion": "Storyteller's Companion",
        "Coteries": "Coteries & Shadows"
    },
    "Werewolf": {
        "Core": "Core Rulebook",
        "Players": "Players Guide",
        "Companion": "Storyteller's Companion"
    },
    "Cyberpunk": {
        "Core": "Core Rulebook",
        "Chrome": "Chromebook",
        "Night City": "Night City Sourcebook",
        "Data Pack": "Data Pack"
    },
    "Shadowrun": {
        "Core": "Core Rulebook",
        "Matrix": "Matrix",
        "Magic": "Magic in the Shadows",
        "Arsenal": "Arsenal",
        "Augmentation": "Augmentation",
        "Data Trails": "Data Trails",
        "Street Grimoire": "Street Grimoire",
        "Firing Squad": "Firing Squad",
        "Street Wyrd": "Street Wyrd"
    },
    "Traveller": {
        "Core": "Core Rulebook",
        "Book1": "Characters and Combat",
        "Book2": "Starships",
        "Book3": "Worlds and Adventures",
        "Book4": "Mercenary",
        "Book5": "High Guard",
        "Book6": "Scouts",
        "Book7": "Merchant Prince",
        "Book8": "Robots",
        "Players": "Player's Manual",
        "Referee": "Referee's Manual",
        "High Guard": "High Guard",
        "Mercenary": "Mercenary",
        "Trader": "Trader",
        "Scout": "Scout",
        "Central Supply": "Central Supply Catalogue",
        "Vehicle Handbook": "Vehicle Handbook",
        "Robot Handbook": "Robot Handbook"
    }
}

# Default categories for unknown game types
DEFAULT_CATEGORIES = {
    "Combat": ["combat", "attack", "damage", "weapon", "armor"],
    "Magic": ["spell", "magic", "supernatural", "power"],
    "Character": ["character", "ability", "skill", "attribute"],
    "Rules": ["rule", "system", "mechanic", "procedure"],
    "Equipment": ["equipment", "item", "gear", "weapon", "armor"],
    "Tables": ["table", "chart", "random", "roll", "dice"]
}

def get_game_config(game_type: str) -> dict:
    """Get configuration for a specific game type"""
    return GAME_CONFIGS.get(game_type, GAME_CONFIGS.get("D&D", {}))

def get_supported_games() -> list:
    """Get list of all supported game types"""
    return list(GAME_CONFIGS.keys())

def get_book_expansion(game_type: str, abbreviation: str) -> str:
    """Expand book abbreviation to full name"""
    game_expansions = BOOK_EXPANSIONS.get(game_type, {})
    return game_expansions.get(abbreviation, abbreviation)

def get_detection_keywords(game_type: str) -> list:
    """Get detection keywords for a game type"""
    config = get_game_config(game_type)
    return config.get("detection_keywords", [])

def get_collection_prefix(game_type: str) -> str:
    """Get collection prefix for a game type"""
    config = get_game_config(game_type)
    return config.get("collection_prefix", "unknown")

def get_supported_editions(game_type: str) -> list:
    """Get supported editions for a game type"""
    config = get_game_config(game_type)
    return config.get("editions", [])

def get_supported_books(game_type: str, edition: str) -> list:
    """Get supported books for a game type and edition"""
    config = get_game_config(game_type)
    books = config.get("books", {})
    return books.get(edition, [])

def get_categories_for_book(game_type: str, book: str) -> list:
    """Get categories for a specific game type and book"""
    config = get_game_config(game_type)
    categories = config.get("categories", {})
    return list(categories.get(book, DEFAULT_CATEGORIES.keys()))

def validate_game_config(game_type: str, edition: str = None, book: str = None) -> bool:
    """Validate if game type, edition, and book combination is supported"""
    if game_type not in GAME_CONFIGS:
        return False

    config = GAME_CONFIGS[game_type]

    if edition and edition not in config.get("editions", []):
        return False

    if book and edition:
        supported_books = config.get("books", {}).get(edition, [])
        if book not in supported_books:
            return False

    return True
