import streamlit as st
from dataclasses import dataclass
from typing import List, Dict, Set
import urllib.parse

st.set_page_config(page_title="Recipe Bot", page_icon="🥘", layout="wide")
st.title("🥘 Recipe Bot")
# ---- Hide Streamlit Toolbar / GitHub / Fork buttons ----
HIDE_TOOLBAR = """
<style>
/* Hide top-right toolbar (Fork, GitHub, ⋮ menu) */
[data-testid="stToolbar"] {display: none !important;}
button[kind="header"] {display: none !important;}
.css-hi6a2p {display: none !important;}  /* legacy */
</style>
"""
st.markdown(HIDE_TOOLBAR, unsafe_allow_html=True)
st.caption("Pick what you have. I’ll suggest recipes with steps and a related YouTube video.")

# ----------------------
# Data Models & Helpers
# ----------------------
@dataclass
class Recipe:
    title: str
    cuisine: str
    ingredients: Dict[str, List[str]]  # by category
    time_minutes: int
    diet: Set[str]  # {"veg", "egg-veg", "vegan", "omnivore"}
    steps: List[str]

CATEGORIES = [
    "veggies",
    "proteins",
    "masalas_spices",
    "sauces_condiments",
    "carbs",
    "others",
]

# Normalization helpers
synonyms = {
    "scallion": "spring onion",
    "green onion": "spring onion",
    "chili": "chilli",
    "chilies": "chilli",
    "chilies green": "chilli",
    "soy sauce": "light soy sauce",
    "soya sauce": "light soy sauce",
    "paneer cheese": "paneer",
    "bell pepper": "capsicum",
    "fenugreek leaves": "kasuri methi",
    "cilantro leaves": "cilantro",
    "lemon juice": "lemon",
}

def norm(x: str) -> str:
    x = x.strip().lower()
    return synonyms.get(x, x)

# ----------------------
# Seed Recipe Base (Expanded)
# ----------------------
RECIPES: List[Recipe] = [
    # ---- INDIAN ----
    Recipe(
        title="Indian Masala Omelette",
        cuisine="Indian",
        ingredients={
            "veggies": ["onion", "tomato", "green chilli", "cilantro"],
            "proteins": ["egg"],
            "masalas_spices": ["turmeric", "cumin", "garam masala", "black pepper", "salt"],
            "sauces_condiments": [],
            "carbs": [],
            "others": ["oil"],
        },
        time_minutes=15,
        diet={"egg-veg", "omnivore"},
        steps=[
            "Beat eggs with salt, turmeric, cumin, and garam masala.",
            "Sauté onion, green chilli, and tomato in a little oil until soft.",
            "Pour eggs, cook until just set, fold, and finish with cilantro.",
        ],
    ),
    Recipe(
        title="Indian Chana Masala (Quick)",
        cuisine="Indian",
        ingredients={
            "veggies": ["onion", "tomato", "ginger", "garlic", "green chilli"],
            "proteins": ["chickpeas"],
            "masalas_spices": ["cumin", "coriander", "turmeric", "garam masala", "chilli powder", "salt"],
            "sauces_condiments": [],
            "carbs": ["rice"],
            "others": ["oil"],
        },
        time_minutes=25,
        diet={"veg", "vegan", "omnivore"},
        steps=[
            "Bloom spices in oil, then sauté onion, ginger, garlic.",
            "Add tomato; cook down, then add chickpeas and simmer.",
            "Adjust seasoning; serve with rice.",
        ],
    ),
    Recipe(
        title="Paneer Butter Masala (Easy)",
        cuisine="Indian",
        ingredients={
            "veggies": ["onion", "tomato", "ginger", "garlic"],
            "proteins": ["paneer"],
            "masalas_spices": ["garam masala", "cumin", "turmeric", "chilli powder", "kasuri methi", "salt"],
            "sauces_condiments": ["tomato paste", "cream"],
            "carbs": ["naan", "rice"],
            "others": ["butter", "oil"],
        },
        time_minutes=25,
        diet={"veg", "omnivore"},
        steps=[
            "Sauté onion, ginger, garlic in butter/oil.",
            "Add tomato paste, spices, splash of water; simmer.",
            "Stir in cream and paneer; finish with kasuri methi.",
        ],
    ),
    Recipe(
        title="Aloo Gobi (Potato Cauliflower)",
        cuisine="Indian",
        ingredients={
            "veggies": ["potato", "cauliflower", "onion", "tomato", "green chilli", "cilantro"],
            "proteins": [],
            "masalas_spices": ["cumin", "turmeric", "coriander", "garam masala", "salt"],
            "sauces_condiments": [],
            "carbs": ["roti", "rice"],
            "others": ["oil"],
        },
        time_minutes=25,
        diet={"veg", "vegan", "omnivore"},
        steps=[
            "Bloom cumin; sauté onion and chilli.",
            "Add potatoes and cauliflower with spices; cover and cook.",
            "Add tomato to finish; garnish with cilantro.",
        ],
    ),
    Recipe(
        title="Dal Tadka",
        cuisine="Indian",
        ingredients={
            "veggies": ["onion", "tomato", "garlic", "ginger", "green chilli"],
            "proteins": ["lentils"],
            "masalas_spices": ["turmeric", "cumin", "mustard seeds", "asafoetida", "chilli powder", "salt"],
            "sauces_condiments": [],
            "carbs": ["rice"],
            "others": ["ghee", "oil"],
        },
        time_minutes=30,
        diet={"veg", "vegan", "omnivore"},
        steps=[
            "Boil lentils with turmeric and salt until soft.",
            "Make tadka: sizzle cumin, mustard, garlic in ghee/oil; add chilli powder.",
            "Pour over lentils; simmer 2–3 minutes.",
        ],
    ),

    # ---- CHINESE ----
    Recipe(
        title="Chinese Tomato & Egg Stir-Fry",
        cuisine="Chinese",
        ingredients={
            "veggies": ["tomato", "spring onion"],
            "proteins": ["egg"],
            "masalas_spices": ["white pepper", "salt"],
            "sauces_condiments": ["light soy sauce", "sugar", "sesame oil"],
            "carbs": ["rice"],
            "others": ["oil"],
        },
        time_minutes=12,
        diet={"egg-veg", "omnivore"},
        steps=[
            "Scramble eggs softly and set aside.",
            "Stir-fry tomatoes; season with soy, sugar, salt, white pepper.",
            "Return eggs; finish with sesame oil and spring onion.",
        ],
    ),
    Recipe(
        title="Veg Fried Rice",
        cuisine="Chinese",
        ingredients={
            "veggies": ["carrot", "peas", "spring onion", "garlic"],
            "proteins": ["egg"],
            "masalas_spices": ["white pepper", "salt"],
            "sauces_condiments": ["light soy sauce", "sesame oil"],
            "carbs": ["rice"],
            "others": ["oil"],
        },
        time_minutes=15,
        diet={"veg", "egg-veg", "omnivore"},
        steps=[
            "Stir-fry aromatics; add veggies.",
            "Add rice and soy; toss on high heat.",
            "Push aside, scramble egg if using; mix and finish with sesame oil.",
        ],
    ),
    Recipe(
        title="Kung Pao Chicken",
        cuisine="Chinese",
        ingredients={
            "veggies": ["garlic", "spring onion", "capsicum"],
            "proteins": ["chicken"],
            "masalas_spices": ["chilli flakes", "white pepper", "salt"],
            "sauces_condiments": ["light soy sauce", "vinegar", "sugar", "cornstarch"],
            "carbs": ["rice"],
            "others": ["oil", "peanuts"],
        },
        time_minutes=18,
        diet={"omnivore"},
        steps=[
            "Marinate chicken with soy and cornstarch.",
            "Stir-fry chilli flakes, chicken, peppers; add sauce (soy, vinegar, sugar).",
            "Finish with spring onion and peanuts.",
        ],
    ),
    Recipe(
        title="Mapo Tofu (mild)",
        cuisine="Chinese",
        ingredients={
            "veggies": ["garlic", "spring onion", "ginger"],
            "proteins": ["tofu", "minced beef"],
            "masalas_spices": ["chilli powder", "white pepper", "salt"],
            "sauces_condiments": ["light soy sauce", "doubanjiang"],
            "carbs": ["rice"],
            "others": ["oil"],
        },
        time_minutes=20,
        diet={"omnivore"},
        steps=[
            "Sauté aromatics and beef; add doubanjiang.",
            "Add tofu and soy; simmer briefly.",
            "Serve with rice; garnish spring onion.",
        ],
    ),
    Recipe(
        title="Chinese Garlic Chicken & Broccoli Stir-Fry",
        cuisine="Chinese",
        ingredients={
            "veggies": ["broccoli", "garlic", "spring onion"],
            "proteins": ["chicken"],
            "masalas_spices": ["white pepper", "salt"],
            "sauces_condiments": ["light soy sauce", "oyster sauce", "cornstarch", "sesame oil"],
            "carbs": ["rice"],
            "others": ["oil"],
        },
        time_minutes=18,
        diet={"omnivore"},
        steps=[
            "Velvet chicken with soy, cornstarch, pinch of oil.",
            "Stir-fry garlic, chicken, then broccoli; splash water to steam.",
            "Finish with sauces; serve over rice.",
        ],
    ),

    # ---- ITALIAN ----
    Recipe(
        title="Italian Aglio e Olio",
        cuisine="Italian",
        ingredients={
            "veggies": ["garlic", "parsley", "chilli flakes"],
            "proteins": [],
            "masalas_spices": ["black pepper", "salt"],
            "sauces_condiments": [],
            "carbs": ["spaghetti"],
            "others": ["olive oil"],
        },
        time_minutes=15,
        diet={"veg", "vegan", "omnivore"},
        steps=[
            "Cook spaghetti al dente.",
            "Gently sizzle garlic and chilli in olive oil.",
            "Toss pasta with oil and pasta water; finish with parsley.",
        ],
    ),
    Recipe(
        title="Penne Arrabbiata",
        cuisine="Italian",
        ingredients={
            "veggies": ["garlic", "chilli flakes", "parsley"],
            "proteins": [],
            "masalas_spices": ["black pepper", "salt"],
            "sauces_condiments": ["tomato paste"],
            "carbs": ["penne"],
            "others": ["olive oil"],
        },
        time_minutes=18,
        diet={"veg", "vegan", "omnivore"},
        steps=[
            "Sauté garlic and chilli; add tomato paste and pasta water.",
            "Simmer; toss with cooked penne; finish with parsley.",
        ],
    ),
    Recipe(
        title="Creamy Alfredo (no-egg)",
        cuisine="Italian",
        ingredients={
            "veggies": ["garlic", "parsley"],
            "proteins": [],
            "masalas_spices": ["black pepper", "salt"],
            "sauces_condiments": ["cream", "parmesan"],
            "carbs": ["pasta"],
            "others": ["butter"],
        },
        time_minutes=20,
        diet={"veg", "omnivore"},
        steps=[
            "Melt butter, add garlic, cream; reduce slightly.",
            "Stir in parmesan; toss pasta; season with pepper.",
        ],
    ),
    Recipe(
        title="Tomato Basil Pasta",
        cuisine="Italian",
        ingredients={
            "veggies": ["garlic", "tomato", "basil"],
            "proteins": [],
            "masalas_spices": ["black pepper", "salt"],
            "sauces_condiments": [],
            "carbs": ["pasta"],
            "others": ["olive oil"],
        },
        time_minutes=20,
        diet={"veg", "vegan", "omnivore"},
        steps=[
            "Sauté garlic in olive oil; add chopped tomatoes; simmer.",
            "Toss with cooked pasta; season; finish with basil.",
        ],
    ),

    # ---- AMERICAN & TEX-MEX ----
    Recipe(
        title="American Veggie Omelette",
        cuisine="American",
        ingredients={
            "veggies": ["onion", "capsicum", "mushroom"],
            "proteins": ["egg"],
            "masalas_spices": ["black pepper", "salt"],
            "sauces_condiments": [],
            "carbs": [],
            "others": ["butter"],
        },
        time_minutes=14,
        diet={"egg-veg", "omnivore"},
        steps=[
            "Sauté onion, pepper, mushrooms in butter.",
            "Add beaten eggs; cook until set, fold, season.",
        ],
    ),
    Recipe(
        title="Mac and Cheese (Stovetop)",
        cuisine="American",
        ingredients={
            "veggies": [],
            "proteins": [],
            "masalas_spices": ["black pepper", "salt", "paprika"],
            "sauces_condiments": ["mustard"],
            "carbs": ["pasta"],
            "others": ["butter", "milk", "cheddar"],
        },
        time_minutes=20,
        diet={"veg", "omnivore"},
        steps=[
            "Cook pasta; make roux with butter and milk.",
            "Melt in cheddar, mustard; season; toss with pasta.",
        ],
    ),
    Recipe(
        title="Chicken Fajita Skillet",
        cuisine="American/Mex-Tex",
        ingredients={
            "veggies": ["onion", "capsicum", "garlic"],
            "proteins": ["chicken"],
            "masalas_spices": ["paprika", "cumin", "chilli powder", "salt", "black pepper"],
            "sauces_condiments": ["lime"],
            "carbs": ["tortilla"],
            "others": ["oil"],
        },
        time_minutes=20,
        diet={"omnivore"},
        steps=[
            "Sear seasoned chicken; remove.",
            "Sauté peppers and onion; return chicken; finish with lime.",
        ],
    ),
    Recipe(
        title="Veg Quesadilla",
        cuisine="Mexican",
        ingredients={
            "veggies": ["onion", "capsicum", "corn"],
            "proteins": ["beans"],
            "masalas_spices": ["cumin", "paprika", "salt", "black pepper"],
            "sauces_condiments": ["lime"],
            "carbs": ["tortilla"],
            "others": ["cheese", "oil"],
        },
        time_minutes=12,
        diet={"veg", "omnivore"},
        steps=[
            "Sauté veg with spices; layer in tortilla with cheese.",
            "Toast on pan until crisp and melty; finish with lime.",
        ],
    ),
    Recipe(
        title="Chicken Tacos (Skillet)",
        cuisine="Mexican",
        ingredients={
            "veggies": ["onion", "tomato", "lettuce"],
            "proteins": ["chicken"],
            "masalas_spices": ["cumin", "paprika", "chilli powder", "salt"],
            "sauces_condiments": ["lime", "salsa"],
            "carbs": ["tortilla"],
            "others": ["oil"],
        },
        time_minutes=18,
        diet={"omnivore"},
        steps=[
            "Sear spiced chicken; slice.",
            "Warm tortillas; fill with chicken, tomato, lettuce, salsa.",
        ],
    ),

    # ---- MEDITERRANEAN ----
    Recipe(
        title="Mediterranean Hummus Bowl",
        cuisine="Mediterranean",
        ingredients={
            "veggies": ["cucumber", "tomato", "lettuce", "red onion"],
            "proteins": ["chickpeas"],
            "masalas_spices": ["cumin", "paprika", "salt", "black pepper"],
            "sauces_condiments": ["lemon", "tahini"],
            "carbs": ["pita", "rice"],
            "others": ["olive oil", "garlic"],
        },
        time_minutes=15,
        diet={"veg", "vegan", "omnivore"},
        steps=[
            "Blend chickpeas with tahini, lemon, garlic, olive oil (hummus).",
            "Assemble bowl with veg, hummus; season with cumin/paprika.",
        ],
    ),
]

# ---------------
# UI — Sidebar Filters
# ---------------
st.sidebar.header("Your Pantry")

# Cuisine preference
cuisine_pref = st.sidebar.multiselect(
    "Cuisine preferences (optional)",
    [
        "Indian", "Chinese", "Italian", "American", "American/Mex-Tex",
        "Mexican", "Mediterranean"
    ],
)

# Diet preference
diet_pref = st.sidebar.selectbox(
    "Diet",
    ["no preference", "veg", "vegan", "egg-veg", "omnivore"],
)

# Time
time_limit = st.sidebar.slider("Time limit (minutes)", 10, 60, 25)

st.sidebar.markdown("---")

# Ingredient categories as multiselect checklists
veggies = sorted({
    "onion", "red onion", "spring onion", "garlic", "ginger", "green chilli", "chilli flakes",
    "tomato", "bell pepper", "capsicum", "carrot", "peas", "corn", "mushroom",
    "broccoli", "cauliflower", "spinach", "lettuce", "cucumber", "potato", "cilantro",
    "parsley", "basil"
})
proteins = sorted({"egg", "paneer", "tofu", "chickpeas", "lentils", "beans", "chicken", "shrimp", "minced beef"})
masalas = sorted({
    "cumin", "coriander", "turmeric", "garam masala", "kasuri methi", "mustard seeds",
    "asafoetida", "curry leaves", "chilli powder", "paprika", "black pepper", "white pepper", "salt"
})
sauces = sorted({
    "light soy sauce", "oyster sauce", "sesame oil", "tomato paste", "salsa",
    "ketchup", "mustard", "vinegar", "lime", "lemon", "tahini", "cream", "parmesan"
})
carbs = sorted({"rice", "pasta", "spaghetti", "penne", "pita", "naan", "tortilla"})
others = sorted({"oil", "olive oil", "butter", "ghee", "milk", "cheddar", "parmesan", "cornstarch", "peanuts", "cheese"})

sel_veggies = st.sidebar.multiselect("Veggies", veggies)
sel_proteins = st.sidebar.multiselect("Proteins (meat/egg/tofu)", proteins)
sel_masalas = st.sidebar.multiselect("Masalas / Spices", masalas)
sel_sauces = st.sidebar.multiselect("Sauces & Condiments", sauces)
sel_carbs = st.sidebar.multiselect("Carbs / Base", carbs)
sel_others = st.sidebar.multiselect("Others", others)

st.sidebar.markdown("---")
run = st.sidebar.button("Suggest Recipes", use_container_width=True)

# ----------------------
# Scoring Logic
# ----------------------

def coverage_score(have: Set[str], need: List[str]) -> float:
    if not need:
        return 0.0
    hits = sum(1 for n in need if norm(n) in have)
    return hits / len(need)


def score_recipe(recipe: Recipe, have_by_cat: Dict[str, Set[str]]) -> float:
    weights = {
        "veggies": 0.30,
        "proteins": 0.30,
        "masalas_spices": 0.20,
        "sauces_condiments": 0.10,
        "carbs": 0.08,
        "others": 0.02,
    }
    s = 0.0
    for cat, w in weights.items():
        need = [norm(x) for x in recipe.ingredients.get(cat, [])]
        have = {norm(x) for x in have_by_cat.get(cat, set())}
        s += w * coverage_score(have, need)

    if cuisine_pref and recipe.cuisine in cuisine_pref:
        s += 0.08

    if diet_pref != "no preference" and diet_pref not in recipe.diet:
        s -= 0.5

    if recipe.time_minutes <= time_limit:
        s += 0.05
    else:
        s -= 0.05

    return s


def youtube_link(recipe_title: str, cuisine: str) -> str:
    q = urllib.parse.quote_plus(f"{recipe_title} {cuisine} recipe")
    return f"https://www.youtube.com/results?search_query={q}"


def render_recipe(r: Recipe, have_by_cat: Dict[str, Set[str]]):
    st.subheader(f"{r.title} · {r.cuisine} · ~{r.time_minutes} min")

    have_flat = {norm(x) for cat in CATEGORIES for x in have_by_cat.get(cat, set())}
    need_flat = {norm(x) for cat in CATEGORIES for x in r.ingredients.get(cat, [])}
    missing = sorted(list(need_flat - have_flat))
    if missing:
        st.markdown("**You might be missing:** " + ", ".join(missing))

    with st.expander("How to make it (steps)", expanded=True):
        for i, step in enumerate(r.steps, 1):
            st.markdown(f"**{i}.** {step}")

    st.markdown(f"[🔗 Related YouTube videos]({youtube_link(r.title, r.cuisine)})")

# ---------------
# Main Area
# ---------------
col1, col2 = st.columns([1, 2])
with col1:
    st.markdown("### Selected Ingredients")
    st.write(
        {
            "veggies": sel_veggies,
            "proteins": sel_proteins,
            "masalas_spices": sel_masalas,
            "sauces_condiments": sel_sauces,
            "carbs": sel_carbs,
            "others": sel_others,
        }
    )

with col2:
    if run:
        have = {
            "veggies": set(map(norm, sel_veggies)),
            "proteins": set(map(norm, sel_proteins)),
            "masalas_spices": set(map(norm, sel_masalas)),
            "sauces_condiments": set(map(norm, sel_sauces)),
            "carbs": set(map(norm, sel_carbs)),
            "others": set(map(norm, sel_others)),
        }

        ranked = sorted(
            RECIPES,
            key=lambda r: score_recipe(r, have),
            reverse=True,
        )
        top = [r for r in ranked if score_recipe(r, have) > 0]

        if not top:
            st.info("No strong matches yet — try adding basics like salt/oil or a protein/carb.")
        else:
            st.markdown("### Best Matches")
            for r in top[:3]:
                render_recipe(r, have)
    else:
        st.markdown(
            "> Use the sidebar to select ingredients and click **Suggest Recipes**."
        )

st.markdown("---")

