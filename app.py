import streamlit as st
from dataclasses import dataclass
from typing import List, Dict, Set
import urllib.parse

st.set_page_config(page_title="Pantry Chef", page_icon="🥘", layout="wide", initial_sidebar_state="expanded")
st.title("🥘 Pantry Chef — Checkbox Recipe Bot")
st.caption("Pick what you have. I’ll suggest recipes with steps and a related YouTube video.")

# --- Responsive: fixed sidebar on desktop, toggle on mobile ---
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True

col_toggle, _ = st.columns([1, 9])
with col_toggle:
    if st.button("☰ Filters", help="Show/Hide sidebar on phones"):
        st.session_state.sidebar_open = not st.session_state.sidebar_open

st.markdown(
    """
    <style>
    /* Desktop (≥ 992px): sidebar fixed and content pushed right */
    @media (min-width: 992px) {
      section[data-testid="stSidebar"] {
        position: fixed !important; top: 0; left: 0; height: 100vh !important; width: 18rem;
        visibility: visible !important; display: block !important; z-index: 999;
      }
      div[data-testid="stAppViewContainer"] { margin-left: 18rem; }
      .block-container { padding-left: 2rem; padding-right: 2rem; }
    }

    /* Mobile (< 992px): sidebar overlays; content full width */
    @media (max-width: 991px) {
      section[data-testid="stSidebar"] {
        position: fixed !important; top: 0; left: 0; height: 100vh !important; width: 85vw; max-width: 320px;
        box-shadow: 0 0 24px rgba(0,0,0,.15); background: #ffffff;
      }
      div[data-testid="stAppViewContainer"] { margin-left: 0 !important; }
      .block-container { padding-left: 1rem; padding-right: 1rem; }
      .stButton>button, .stSlider, .stMultiSelect div[data-baseweb="select"] { font-size: 1rem; }
      .stMultiSelect [data-baseweb="tag"] { font-size: .95rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.sidebar_open:
    st.markdown(
        """
        <style>
        @media (max-width: 991px) {
          section[data-testid="stSidebar"] { display: none !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

@dataclass
class Recipe:
    title: str
    cuisine: str
    ingredients: Dict[str, List[str]]
    time_minutes: int
    diet: Set[str]
    steps: List[str]

# Ingredient categories
CATEGORIES = [
    "veggies",
    "proteins",
    "masalas_spices",
    "sauces_condiments",
    "carbs",
    "others",
]

synonyms = {
    "scallion": "spring onion",
    "green onion": "spring onion",
    "chili": "chilli",
    "chilies": "chilli",
    "soya sauce": "light soy sauce",
    "paneer cheese": "paneer",
    "bell pepper": "capsicum",
}

def norm(x: str) -> str:
    return synonyms.get(x.strip().lower(), x.strip().lower())

# Expanded Recipe base
RECIPES: List[Recipe] = [
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
            "Sauté onion, green chilli, and tomato in oil until soft.",
            "Pour eggs, cook until set, fold, garnish with cilantro.",
        ],
    ),
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
            "Stir-fry tomatoes; season with soy, sugar, pepper.",
            "Return eggs, toss, finish with sesame oil & spring onion.",
        ],
    ),
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
            "Sizzle garlic and chilli flakes in olive oil.",
            "Toss pasta with oil, pasta water, finish with parsley.",
        ],
    ),
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
            "Sauté veggies in butter.",
            "Add beaten eggs; cook and fold.",
        ],
    ),
    Recipe(
        title="Indian Chana Masala",
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
            "Bloom spices, sauté onion, ginger, garlic.",
            "Add tomato, cook, add chickpeas, simmer.",
            "Adjust seasoning; serve with rice.",
        ],
    ),
    Recipe(
        title="Chinese Garlic Chicken & Broccoli",
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
            "Marinate chicken with soy & cornstarch.",
            "Stir-fry garlic, chicken, then broccoli.",
            "Finish with sauces & sesame oil.",
        ],
    ),
    Recipe(
        title="Italian Tomato Basil Pasta",
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
            "Sauté garlic, add tomato, simmer.",
            "Toss with pasta, finish with basil.",
        ],
    ),
    Recipe(
        title="American Chicken Fajitas",
        cuisine="American",
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
            "Sear chicken with spices.",
            "Sauté peppers & onions, combine, finish with lime.",
        ],
    ),
]

# Ingredient master list
veggies = sorted({"onion", "tomato", "green chilli", "spring onion", "garlic", "ginger", "cilantro", "parsley", "basil", "capsicum", "mushroom", "broccoli", "chilli flakes"})
proteins = sorted({"egg", "chicken", "paneer", "tofu", "chickpeas"})
masalas = sorted({"cumin", "coriander", "turmeric", "garam masala", "chilli powder", "paprika", "black pepper", "white pepper", "salt"})
sauces = sorted({"light soy sauce", "oyster sauce", "sesame oil", "sugar", "lime"})
carbs = sorted({"rice", "pasta", "spaghetti", "tortilla"})
others = sorted({"oil", "olive oil", "butter", "cornstarch"})

# Sidebar filters
st.sidebar.header("Your Pantry")
cuisine_pref = st.sidebar.multiselect("Cuisine preferences", ["Indian", "Chinese", "Italian", "American"])
diet_pref = st.sidebar.selectbox("Diet", ["no preference", "veg", "vegan", "egg-veg", "omnivore"])
time_limit = st.sidebar.slider("Time limit (minutes)", 10, 60, 25)

sel_veggies = st.sidebar.multiselect("Veggies", veggies)
sel_proteins = st.sidebar.multiselect("Proteins", proteins)
sel_masalas = st.sidebar.multiselect("Masalas/Spices", masalas)
sel_sauces = st.sidebar.multiselect("Sauces", sauces)
sel_carbs = st.sidebar.multiselect("Carbs", carbs)
sel_others = st.sidebar.multiselect("Others", others)

run = st.sidebar.button("Suggest Recipes", use_container_width=True)

def coverage_score(have: Set[str], need: List[str]) -> float:
    if not need:
        return 0.0
    return sum(1 for n in need if norm(n) in have) / len(need)

def score_recipe(recipe: Recipe, have: Dict[str, Set[str]]) -> float:
    weights = {"veggies":0.3,"proteins":0.3,"masalas_spices":0.2,"sauces_condiments":0.1,"carbs":0.08,"others":0.02}
    score = 0
    for cat, w in weights.items():
        score += w * coverage_score(have.get(cat, set()), [norm(x) for x in recipe.ingredients.get(cat, [])])
    if cuisine_pref and recipe.cuisine in cuisine_pref:
        score += 0.1
    if diet_pref != "no preference" and diet_pref not in recipe.diet:
        score -= 0.5
    if recipe.time_minutes <= time_limit:
        score += 0.05
    return score

def youtube_link(title: str, cuisine: str) -> str:
    q = urllib.parse.quote_plus(f"{title} {cuisine} recipe")
    return f"https://www.youtube.com/results?search_query={q}"

def render_recipe(r: Recipe, have: Dict[str, Set[str]]):
    st.subheader(f"{r.title} ({r.cuisine}, {r.time_minutes} min)")
    st.write("Steps:")
    for i, step in enumerate(r.steps, 1):
        st.markdown(f"{i}. {step}")
    st.markdown(f"[Watch on YouTube]({youtube_link(r.title, r.cuisine)})")

if run:
    have = {
        "veggies": set(map(norm, sel_veggies)),
        "proteins": set(map(norm, sel_proteins)),
        "masalas_spices": set(map(norm, sel_masalas)),
        "sauces_condiments": set(map(norm, sel_sauces)),
        "carbs": set(map(norm, sel_carbs)),
        "others": set(map(norm, sel_others)),
    }
    ranked = sorted(RECIPES, key=lambda r: score_recipe(r, have), reverse=True)
    if ranked:
        for r in ranked[:3]:
            render_recipe(r, have)
    else:
        st.info("No matches found. Try adding more basics like salt or oil.")
else:
    st.write("Select your ingredients in the sidebar and click Suggest Recipes.")
