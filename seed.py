import firebase_admin
from firebase_admin import credentials, firestore

# 1. Setup Firebase
# We use the key file you just downloaded
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# 2. The Truth List (Data to upload)
# I have pre-filled this with common Malaysian E-codes
ecodes_data = {
    # --- COLORS (E100-E199) ---
    "E100": {"code": "E100", "name": "Curcumin", "status": "Halal", "source": "Plant (Turmeric)", "description": "Natural yellow color."},
    "E101": {"code": "E101", "name": "Riboflavin", "status": "Halal", "source": "Vitamin B2", "description": "Yellow color/vitamin."},
    "E102": {"code": "E102", "name": "Tartrazine", "status": "Halal", "source": "Synthetic", "description": "Yellow color."},
    "E104": {"code": "E104", "name": "Quinoline Yellow", "status": "Halal", "source": "Synthetic", "description": "Yellow color."},
    "E110": {"code": "E110", "name": "Sunset Yellow FCF", "status": "Halal", "source": "Synthetic", "description": "Orange color."},
    "E120": {"code": "E120", "name": "Cochineal / Carmine", "status": "Haram", "source": "Animal (Insects)", "description": "Red dye from crushed beetles. STRICTLY PROHIBITED."},
    "E122": {"code": "E122", "name": "Azorubine / Carmoisine", "status": "Halal", "source": "Synthetic", "description": "Red color."},
    "E123": {"code": "E123", "name": "Amaranth", "status": "Halal", "source": "Synthetic", "description": "Red color."},
    "E124": {"code": "E124", "name": "Ponceau 4R", "status": "Halal", "source": "Synthetic", "description": "Red color."},
    "E127": {"code": "E127", "name": "Erythrosine", "status": "Halal", "source": "Synthetic", "description": "Red color."},
    "E129": {"code": "E129", "name": "Allura Red AC", "status": "Halal", "source": "Synthetic", "description": "Red color."},
    "E132": {"code": "E132", "name": "Indigotine", "status": "Halal", "source": "Synthetic", "description": "Blue color."},
    "E133": {"code": "E133", "name": "Brilliant Blue FCF", "status": "Halal", "source": "Synthetic", "description": "Blue color."},
    "E140": {"code": "E140", "name": "Chlorophylls", "status": "Halal", "source": "Plant", "description": "Green color from plants."},
    "E141": {"code": "E141", "name": "Copper Complexes of Chlorophylls", "status": "Halal", "source": "Plant/Synthetic", "description": "Green color."},
    "E150A": {"code": "E150a", "name": "Plain Caramel", "status": "Halal", "source": "Plant", "description": "Brown color."},
    "E150C": {"code": "E150c", "name": "Ammonia Caramel", "status": "Halal", "source": "Plant", "description": "Brown color."},
    "E150D": {"code": "E150d", "name": "Sulphite Ammonia Caramel", "status": "Halal", "source": "Plant", "description": "Brown color."},
    "E153": {"code": "E153", "name": "Vegetable Carbon", "status": "Halal", "source": "Plant (Charcoal)", "description": "Black color."},
    "E155": {"code": "E155", "name": "Brown HT", "status": "Halal", "source": "Synthetic", "description": "Brown color."},
    "E160A": {"code": "E160a", "name": "Carotenes", "status": "Halal", "source": "Plant", "description": "Orange/Yellow color."},
    "E160B": {"code": "E160b", "name": "Annatto", "status": "Halal", "source": "Plant", "description": "Orange color."},
    "E160C": {"code": "E160c", "name": "Paprika Extract", "status": "Halal", "source": "Plant", "description": "Red/Orange color."},
    "E161B": {"code": "E161b", "name": "Lutein", "status": "Halal", "source": "Plant", "description": "Yellow color."},
    "E162": {"code": "E162", "name": "Beetroot Red", "status": "Halal", "source": "Plant", "description": "Red color."},
    "E163": {"code": "E163", "name": "Anthocyanins", "status": "Halal", "source": "Plant", "description": "Red/Blue/Purple color."},
    "E170": {"code": "E170", "name": "Calcium Carbonate", "status": "Halal", "source": "Mineral", "description": "White color/calcium source."},
    "E171": {"code": "E171", "name": "Titanium Dioxide", "status": "Halal", "source": "Mineral", "description": "White color."},
    "E172": {"code": "E172", "name": "Iron Oxides", "status": "Halal", "source": "Mineral", "description": "Red/Yellow/Black colors."},

    # --- PRESERVATIVES (E200-E299) ---
    "E200": {"code": "E200", "name": "Sorbic Acid", "status": "Halal", "source": "Synthetic", "description": "Preservative."},
    "E202": {"code": "E202", "name": "Potassium Sorbate", "status": "Halal", "source": "Synthetic", "description": "Preservative."},
    "E210": {"code": "E210", "name": "Benzoic Acid", "status": "Halal", "source": "Synthetic", "description": "Preservative."},
    "E211": {"code": "E211", "name": "Sodium Benzoate", "status": "Halal", "source": "Synthetic", "description": "Preservative."},
    "E220": {"code": "E220", "name": "Sulphur Dioxide", "status": "Halal", "source": "Synthetic", "description": "Preservative."},
    "E223": {"code": "E223", "name": "Sodium Metabisulphite", "status": "Halal", "source": "Synthetic", "description": "Preservative."},
    "E250": {"code": "E250", "name": "Sodium Nitrite", "status": "Halal", "source": "Mineral", "description": "Preservative (Meats)."},
    "E251": {"code": "E251", "name": "Sodium Nitrate", "status": "Halal", "source": "Mineral", "description": "Preservative."},
    "E260": {"code": "E260", "name": "Acetic Acid", "status": "Halal", "source": "Synthetic/Plant", "description": "Vinegar acid."},
    "E270": {"code": "E270", "name": "Lactic Acid", "status": "Halal", "source": "Fermentation", "description": "Acidifier."},
    "E280": {"code": "E280", "name": "Propionic Acid", "status": "Halal", "source": "Synthetic", "description": "Preservative."},
    "E296": {"code": "E296", "name": "Malic Acid", "status": "Halal", "source": "Synthetic", "description": "Acidifier."},

    # --- ANTIOXIDANTS & ACIDITY REGULATORS (E300-E399) ---
    "E300": {"code": "E300", "name": "Ascorbic Acid", "status": "Halal", "source": "Synthetic/Plant", "description": "Vitamin C."},
    "E301": {"code": "E301", "name": "Sodium Ascorbate", "status": "Halal", "source": "Synthetic", "description": "Vitamin C salt."},
    "E306": {"code": "E306", "name": "Tocopherol-rich Extract", "status": "Halal", "source": "Plant", "description": "Vitamin E."},
    "E307": {"code": "E307", "name": "Alpha-tocopherol", "status": "Halal", "source": "Synthetic", "description": "Vitamin E."},
    "E319": {"code": "E319", "name": "TBHQ", "status": "Halal", "source": "Synthetic", "description": "Antioxidant."},
    "E320": {"code": "E320", "name": "BHA", "status": "Halal", "source": "Synthetic", "description": "Antioxidant."},
    "E321": {"code": "E321", "name": "BHT", "status": "Halal", "source": "Synthetic", "description": "Antioxidant."},
    "E322": {"code": "E322", "name": "Lecithin", "status": "Halal", "source": "Plant (Soy/Sunflower)", "description": "Emulsifier. Usually Halal."},
    "E330": {"code": "E330", "name": "Citric Acid", "status": "Halal", "source": "Fermentation", "description": "Acidifier."},
    "E331": {"code": "E331", "name": "Sodium Citrates", "status": "Halal", "source": "Mineral/Fermentation", "description": "Acidity regulator."},
    "E339": {"code": "E339", "name": "Sodium Phosphates", "status": "Halal", "source": "Mineral", "description": "Stabilizer."},
    "E341": {"code": "E341", "name": "Calcium Phosphates", "status": "Halal", "source": "Mineral", "description": "Raising agent."},

    # --- THICKENERS, STABILIZERS & EMULSIFIERS (E400-E499) ---
    "E400": {"code": "E400", "name": "Alginic Acid", "status": "Halal", "source": "Seaweed", "description": "Thickener."},
    "E401": {"code": "E401", "name": "Sodium Alginate", "status": "Halal", "source": "Seaweed", "description": "Thickener."},
    "E406": {"code": "E406", "name": "Agar", "status": "Halal", "source": "Seaweed", "description": "Vegetable gelatin."},
    "E407": {"code": "E407", "name": "Carrageenan", "status": "Halal", "source": "Seaweed", "description": "Thickener."},
    "E410": {"code": "E410", "name": "Locust Bean Gum", "status": "Halal", "source": "Plant", "description": "Thickener."},
    "E412": {"code": "E412", "name": "Guar Gum", "status": "Halal", "source": "Plant", "description": "Thickener."},
    "E414": {"code": "E414", "name": "Gum Arabic", "status": "Halal", "source": "Plant", "description": "Stabilizer."},
    "E415": {"code": "E415", "name": "Xanthan Gum", "status": "Halal", "source": "Fermentation", "description": "Thickener."},
    "E420": {"code": "E420", "name": "Sorbitol", "status": "Halal", "source": "Plant", "description": "Sweetener/Humectant."},
    "E422": {"code": "E422", "name": "Glycerol", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Check for Halal logo. Often plant-based but can be animal."},
    "E440": {"code": "E440", "name": "Pectins", "status": "Halal", "source": "Plant (Fruit)", "description": "Gelling agent."},
    "E441": {"code": "E441", "name": "Gelatin", "status": "Syubhah", "source": "Animal (Bone/Skin)", "description": "Could be Pig (Haram) or Cow (Halal). Requires Halal logo."},
    "E450": {"code": "E450", "name": "Diphosphates", "status": "Halal", "source": "Mineral", "description": "Stabilizer."},
    "E451": {"code": "E451", "name": "Triphosphates", "status": "Halal", "source": "Mineral", "description": "Stabilizer."},
    "E460": {"code": "E460", "name": "Cellulose", "status": "Halal", "source": "Plant", "description": "Fiber."},
    "E466": {"code": "E466", "name": "CMC / Sodium Carboxymethyl Cellulose", "status": "Halal", "source": "Plant", "description": "Thickener."},
    "E470A": {"code": "E470a", "name": "Sodium/Potassium Salts of Fatty Acids", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Soaps of fatty acids. Check source."},
    "E470B": {"code": "E470b", "name": "Magnesium Salts of Fatty Acids", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Check source."},
    "E471": {"code": "E471", "name": "Mono- and Diglycerides", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Common emulsifier. Check for Halal logo."},
    "E472A": {"code": "E472a", "name": "Acetic Acid Esters", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Esters of mono-diglycerides. Check source."},
    "E472B": {"code": "E472b", "name": "Lactic Acid Esters", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Check source."},
    "E472C": {"code": "E472c", "name": "Citric Acid Esters", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Check source."},
    "E472E": {"code": "E472e", "name": "DATEM", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Common in bread. Check source."},
    "E473": {"code": "E473", "name": "Sucrose Esters of Fatty Acids", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Check source."},
    "E475": {"code": "E475", "name": "Polyglycerol Esters of Fatty Acids", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Check source."},
    "E476": {"code": "E476", "name": "PGPR", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Common in chocolate. Check source."},
    "E481": {"code": "E481", "name": "Sodium Stearoyl-2-Lactylate", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Check source."},
    "E491": {"code": "E491", "name": "Sorbitan Monostearate", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Check source."},
    "E492": {"code": "E492", "name": "Sorbitan Tristearate", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Check source."},

    # --- ANTI-CAKING & OTHERS (E500-E599) ---
    "E500": {"code": "E500", "name": "Sodium Carbonates", "status": "Halal", "source": "Mineral", "description": "Raising agent."},
    "E501": {"code": "E501", "name": "Potassium Carbonates", "status": "Halal", "source": "Mineral", "description": "Acidity regulator."},
    "E503": {"code": "E503", "name": "Ammonium Carbonates", "status": "Halal", "source": "Mineral", "description": "Raising agent."},
    "E542": {"code": "E542", "name": "Bone Phosphate", "status": "Haram", "source": "Animal Bones", "description": "Phosphates derived from animal bones. Avoid."},
    "E551": {"code": "E551", "name": "Silicon Dioxide", "status": "Halal", "source": "Mineral", "description": "Anti-caking agent."},
    "E570": {"code": "E570", "name": "Fatty Acids", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Check source."},
    "E572": {"code": "E572", "name": "Magnesium Stearate", "status": "Syubhah", "source": "Plant/Animal Fat", "description": "Check source."},

    # --- FLAVOR ENHANCERS (E600-E699) ---
    "E621": {"code": "E621", "name": "Monosodium Glutamate (MSG)", "status": "Halal", "source": "Fermentation", "description": "Flavor enhancer."},
    "E627": {"code": "E627", "name": "Disodium Guanylate", "status": "Syubhah", "source": "Fish/Meat/Seaweed", "description": "Often Halal, but can be animal derived."},
    "E631": {"code": "E631", "name": "Disodium Inosinate", "status": "Syubhah", "source": "Meat/Fish/Fermentation", "description": "Often from meat. Check for Halal logo."},
    "E635": {"code": "E635", "name": "Disodium 5'-Ribonucleotides", "status": "Syubhah", "source": "Meat/Fish/Fermentation", "description": "Mixture of E627 and E631."},

    # --- GLAZING AGENTS & SWEETENERS (E900-E999) ---
    "E901": {"code": "E901", "name": "Beeswax", "status": "Halal", "source": "Insect (Bees)", "description": "Natural wax."},
    "E903": {"code": "E903", "name": "Carnauba Wax", "status": "Halal", "source": "Plant", "description": "Plant wax."},
    "E904": {"code": "E904", "name": "Shellac", "status": "Syubhah", "source": "Insect Secretion", "description": "Debated. JAKIM accepts if cleaned, but often flagged as Syubhah."},
    "E920": {"code": "E920", "name": "L-Cysteine", "status": "Syubhah", "source": "Animal/Human Hair/Synthetic", "description": "Dough conditioner. Synthetic is Halal. Animal/Hair is Haram."},
    "E950": {"code": "E950", "name": "Acesulfame K", "status": "Halal", "source": "Synthetic", "description": "Sweetener."},
    "E951": {"code": "E951", "name": "Aspartame", "status": "Halal", "source": "Synthetic", "description": "Sweetener."},
    "E952": {"code": "E952", "name": "Cyclamate", "status": "Halal", "source": "Synthetic", "description": "Sweetener."},
    "E954": {"code": "E954", "name": "Saccharin", "status": "Halal", "source": "Synthetic", "description": "Sweetener."},
    "E955": {"code": "E955", "name": "Sucralose", "status": "Halal", "source": "Synthetic", "description": "Sweetener."},
    "E965": {"code": "E965", "name": "Maltitol", "status": "Halal", "source": "Plant", "description": "Sweetener."},

    # --- ADDITIONAL ---
    "E1105": {"code": "E1105", "name": "Lysozyme", "status": "Syubhah", "source": "Chicken Egg", "description": "Enzyme from eggs. Halal if egg source is Halal."},
    "E1200": {"code": "E1200", "name": "Polydextrose", "status": "Halal", "source": "Synthetic", "description": "Fiber."},
    "E1400": {"code": "E1400", "name": "Dextrins", "status": "Halal", "source": "Plant", "description": "Thickener."},
    "E1414": {"code": "E1414", "name": "Acetylated Distarch Phosphate", "status": "Halal", "source": "Plant", "description": "Modified starch."},
    "E1422": {"code": "E1422", "name": "Acetylated Distarch Adipate", "status": "Halal", "source": "Plant", "description": "Modified starch."},
    "E1442": {"code": "E1442", "name": "Hydroxypropyl Distarch Phosphate", "status": "Halal", "source": "Plant", "description": "Modified starch."},

    # --- KEYWORDS ---
    "CARMINE": {"code": "E120", "name": "Cochineal / Carmine", "status": "Haram", "source": "Animal (Insects)", "description": "Red dye made from crushed beetles. STRICTLY PROHIBITED."},
    "COCHINEAL": {"code": "E120", "name": "Cochineal / Carmine", "status": "Haram", "source": "Animal (Insects)", "description": "Red dye made from crushed beetles. STRICTLY PROHIBITED."},
    "GELATIN": {"code": "E441", "name": "Gelatin", "status": "Syubhah", "source": "Animal (Bone/Skin)", "description": "Could be Pig (Haram) or Cow (Halal). Look for Halal Logo."},
    "LARD": {"code": "Fat", "name": "Lard", "status": "Haram", "source": "Pig Fat", "description": "Pig fat. STRICTLY PROHIBITED."},
    "PORK": {"code": "Meat", "name": "Pork", "status": "Haram", "source": "Pig Meat", "description": "Pig meat. STRICTLY PROHIBITED."},
    "ALCOHOL": {"code": "Alc", "name": "Alcohol / Ethanol", "status": "Syubhah", "source": "Fermentation", "description": "If used as ingredient/intoxicant: Haram. If trace/processing aid: Syubhah."},
    "WHEY": {"code": "Milk", "name": "Whey", "status": "Syubhah", "source": "Milk/Cheese making", "description": "Rennet used in cheese making might be animal based."},
    "RENNET": {"code": "Enzyme", "name": "Rennet", "status": "Syubhah", "source": "Animal Stomach", "description": "Enzyme for cheese. Animal source requires Halal slaughter."},
    "PEPSIN": {"code": "Enzyme", "name": "Pepsin", "status": "Syubhah", "source": "Animal Stomach", "description": "Enzyme. Often pig derived (Haram) or cow (Halal if slaughtered)."},
    "PHENYLALANINE": {"code": "Amino Acid", "name": "Phenylalanine", "status": "Halal", "source": "Synthetic/Natural", "description": "Common amino acid. Safe for most (Warning for PKU patients)."}
}

# 3. Upload to Firestore
print("🚀 Connecting to Firebase...")
collection = db.collection('ecodes')

for code, data in ecodes_data.items():
    collection.document(code).set(data)
    print(f"✅ Uploaded: {code} ({data['status']})")

print("\n🎉 Database Populated Successfully!")