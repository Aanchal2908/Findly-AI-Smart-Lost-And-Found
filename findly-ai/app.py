from datetime import date, datetime, timedelta
from html import escape
from uuid import uuid4

import streamlit as st
from evaluation import evaluate_comparison
from match_engine import MATCH_THRESHOLD
from semantic_matcher import rank_matches_with_mode


st.set_page_config(
    page_title="Findly AI | Campus Lost & Found",
    page_icon=":material/travel_explore:",
    layout="wide",
    initial_sidebar_state="expanded",
)


NAVY = "#152744"
INDIGO = "#4559D6"
VIOLET = "#7764CC"
INK = "#17263E"
MUTED = "#708099"
BORDER = "#E3E9F1"
PALE = "#F5F7FB"

CATEGORIES = ["Electronics", "ID Cards", "Bags", "Books", "Accessories", "Clothing", "Other"]
CATEGORY_ICONS = {
    "Electronics": "devices",
    "ID Cards": "badge",
    "Bags": "work",
    "Books": "menu_book",
    "Accessories": "watch",
    "Clothing": "apparel",
    "Other": "category",
}

SAMPLE_ITEMS = [
    {
        "id": "F-2048", "name": "Navy blue water bottle", "type": "Found", "category": "Accessories",
        "description": "Insulated stainless-steel bottle with a small mountain sticker near the base.",
        "location": "North Library, Level 2", "date": "Oct 18, 2026", "image": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=900&q=85",
        "match": True, "characteristics": "Mountain sticker, silver cap, 750 ml",
    },
    {
        "id": "F-2043", "name": "Wireless headphones", "type": "Found", "category": "Electronics",
        "description": "Black over-ear headphones left on a study desk. Foldable design, no case found.",
        "location": "Engineering Building, Room 104", "date": "Oct 17, 2026", "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=85",
        "match": True, "characteristics": "Matte black, foldable, padded headband",
    },
    {
        "id": "F-2039", "name": "Canvas tote bag", "type": "Found", "category": "Bags",
        "description": "Natural canvas tote with green lettering. A notebook was inside when found.",
        "location": "Student Union, Ground Floor", "date": "Oct 16, 2026", "image": "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?auto=format&fit=crop&w=900&q=85",
        "match": False, "characteristics": "Green print, natural canvas, inner pocket",
    },
    {
        "id": "L-9182", "name": "Wireless headphones", "type": "Lost", "category": "Electronics",
        "description": "Black headphones, probably left after an afternoon lecture. The headband has a small scratch.",
        "location": "Engineering Building", "date": "Oct 17, 2026", "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=85",
        "match": True, "characteristics": "Matte black, small scratch on headband",
    },
    {
        "id": "L-9175", "name": "Student ID card", "type": "Lost", "category": "ID Cards",
        "description": "University ID in a clear card sleeve. Lost somewhere between the science quad and the cafe.",
        "location": "Science Quad", "date": "Oct 15, 2026", "image": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=900&q=85",
        "match": False, "characteristics": "Clear plastic sleeve, blue lanyard",
    },
    {
        "id": "F-2028", "name": "Hardcover statistics book", "type": "Found", "category": "Books",
        "description": "Introductory statistics textbook with a green cover and handwritten notes on the inside cover.",
        "location": "West Lecture Hall", "date": "Oct 14, 2026", "image": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=900&q=85",
        "match": False, "characteristics": "Green cover, notes on inside cover",
    },
]

if "page" not in st.session_state:
    st.session_state.page = "Home"
if "items" not in st.session_state:
    st.session_state["items"] = [item.copy() for item in SAMPLE_ITEMS]
if "claims" not in st.session_state:
    st.session_state.claims = []
if "my_reports" not in st.session_state:
    st.session_state.my_reports = []
if "selected_item" not in st.session_state:
    st.session_state.selected_item = SAMPLE_ITEMS[0]["id"]
if "submitted_report" not in st.session_state:
    st.session_state.submitted_report = None


def go(page):
    st.session_state.page = page
    st.rerun()


def inject_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,400,0,0');
        :root { --navy:#152744; --indigo:#4559D6; --violet:#7764CC; --ink:#17263E; --muted:#708099; --border:#E3E9F1; --pale:#F5F7FB; }
        html, body, [class*="css"], button, input, textarea, select { font-family:'Plus Jakarta Sans', sans-serif !important; }
        .stApp { background:#F6F8FC; color:var(--ink); }
        [data-testid="stHeader"] { background:rgba(246,248,252,.94); }
       /* High-contrast sidebar navigation */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #D5DDEA !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    background-color: #FFFFFF !important;
    color: #17263E !important;
    border-radius: 7px !important;
    padding: 5px 8px !important;
    font-weight: 600 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label p {
    color: #17263E !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background-color: #EEF1FF !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background-color: #4559D6 !important;
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p {
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] .sidebar-caption {
    color: #64748B !important;
}

[data-testid="stSidebar"] .demo-note {
    background: #EEF1FF !important;
    color: #3549C4 !important;
    border-color: #C7D2FE !important;
}
        [data-testid="stSidebar"] > div:first-child { padding-top:1.2rem; }
        .block-container { max-width:1440px; padding:3.25rem 2.5rem 3rem; }
        h1,h2,h3,h4,p { color:var(--ink); }
        h1 { font-size:2rem !important; line-height:1.2 !important; letter-spacing:0 !important; font-weight:750 !important; }
        h2 { font-size:1.38rem !important; letter-spacing:0 !important; font-weight:700 !important; }
        h3 { font-size:1.05rem !important; letter-spacing:0 !important; font-weight:700 !important; }
        .stButton > button, .stDownloadButton > button { border-radius:7px; font-weight:650; min-height:2.55rem; transition:all .18s ease; }
        .stButton > button[kind="primary"] { background:var(--indigo); border:1px solid var(--indigo); color:#fff; }
        .stButton > button[kind="primary"]:hover { background:#3549C4; border-color:#3549C4; box-shadow:0 5px 14px rgba(69,89,214,.18); }
        .stButton > button:not([kind="primary"]), .stDownloadButton > button { color:var(--navy); border-color:#D8E0EC; background:#fff; }
        .stButton > button:focus-visible, a:focus-visible, input:focus-visible { outline:3px solid #9CA9FF !important; outline-offset:2px; }
        .st-key-home-nav { margin-bottom:.25rem; }
        .st-key-home-nav [data-testid="stHorizontalBlock"] { align-items:center; gap:clamp(.25rem, 1vw, .85rem); }
        .st-key-home-nav [data-testid="stColumn"] { min-width:0; padding:0; }
        .st-key-home-nav [data-testid="stColumn"]:first-child [data-testid="stMarkdown"] { min-height:40px; }
        .st-key-home-nav .brand-mark { min-height:40px; line-height:1; white-space:nowrap; overflow:visible; }
        .st-key-home-nav .brand-icon { width:32px; height:32px; flex:0 0 32px; line-height:1; font-size:20px; }
        .st-key-home-nav .stButton { display:flex; align-items:center; min-width:0; }
        .st-key-home-nav .stButton > button { display:flex; align-items:center; justify-content:center; width:100%; height:40px; min-height:40px; padding:0 10px; line-height:1.2; white-space:nowrap; }
        .st-key-home-nav .stButton > button p { margin:0; line-height:1.2; white-space:nowrap; }
        input, textarea, [data-baseweb="select"] > div { border-radius:6px !important; }
        [data-testid="stMetric"] { border:1px solid var(--border); border-radius:8px; background:white; padding:1rem 1.05rem; box-shadow:0 2px 7px rgba(21,39,68,.035); }
        [data-testid="stMetricLabel"] { font-size:.81rem; color:var(--muted); font-weight:600; }
        [data-testid="stMetricValue"] { font-size:1.75rem; color:var(--navy); font-weight:750; }
        [data-testid="stImage"] img { border-radius:7px; }
        div[data-testid="stVerticalBlockBorderWrapper"] { border-radius:8px; border-color:var(--border); background:white; }
        .material-symbols-rounded { font-family:'Material Symbols Rounded'; font-weight:normal; font-style:normal; font-size:20px; line-height:1; display:inline-block; white-space:nowrap; direction:ltr; font-feature-settings:'liga'; -webkit-font-feature-settings:'liga'; -webkit-font-smoothing:antialiased; }
        .brand-mark { display:flex; align-items:center; gap:10px; font-size:1.05rem; font-weight:800; color:var(--navy); letter-spacing:0; }
        .brand-icon { width:34px; height:34px; border-radius:9px; background:var(--navy); color:white; display:grid; place-items:center; }
        .eyebrow { color:var(--indigo); font-weight:750; font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; }
        .muted { color:var(--muted); font-size:.91rem; line-height:1.65; }
        .demo-note { color:#697A94; font-size:.75rem; background:#EEF2F9; border:1px solid #E2E8F1; padding:7px 10px; border-radius:5px; display:inline-flex; gap:6px; align-items:center; }
        .status { font-size:.72rem; font-weight:700; padding:4px 8px; border-radius:4px; display:inline-block; }
        .status-found { color:#14765D; background:#E6F5EF; }
        .status-lost { color:#A45237; background:#FFF0E9; }
        .status-pending { color:#8B6819; background:#FFF5D9; }
        .status-accepted { color:#176C55; background:#E3F4EC; }
        .status-rejected { color:#A14343; background:#FCEAEA; }
        .score-track { background:#E9EDF5; height:7px; border-radius:9px; overflow:hidden; }
        .score-fill { height:100%; background:linear-gradient(90deg,var(--indigo),#7E79DB); border-radius:9px; }
        .feature-icon { color:var(--indigo); background:#EEF0FF; border-radius:8px; width:38px; height:38px; display:grid; place-items:center; }
        .hero-panel { background:#fff; border:1px solid var(--border); border-radius:10px; padding:1.2rem; box-shadow:0 10px 35px rgba(30,49,79,.08); }
        .hero-pill { color:var(--indigo); background:#EEF0FF; border-radius:4px; padding:5px 9px; font-weight:700; font-size:.72rem; }
        .sidebar-caption { color:#8794A7; font-size:.68rem; font-weight:700; text-transform:uppercase; letter-spacing:.09em; padding:1rem 0 .35rem; }
        .item-title { font-weight:750; color:var(--navy); font-size:1rem; }
        .item-meta { color:var(--muted); font-size:.79rem; }
        .footer { border-top:1px solid var(--border); margin-top:3rem; padding-top:1.2rem; color:var(--muted); font-size:.78rem; }
        @media (max-width: 800px) {
          .block-container { padding:3.25rem 1rem 2rem; }
          h1 { font-size:1.65rem !important; }
          [data-testid="stSidebar"] { min-width:0; }
        }
                @media (max-width: 740px) {
                    .st-key-home-nav [data-testid="stHorizontalBlock"] { display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:8px; }
                      .st-key-home-nav [data-testid="stColumn"] { width:auto !important; flex:unset !important; }
                      .st-key-home-nav [data-testid="stColumn"]:nth-child(1) { grid-column:1 / 3; grid-row:1; }
                      .st-key-home-nav [data-testid="stColumn"]:nth-child(5) { grid-column:3; grid-row:1; }
                      .st-key-home-nav [data-testid="stColumn"]:nth-child(2) { grid-column:1; grid-row:2; }
                      .st-key-home-nav [data-testid="stColumn"]:nth-child(3) { grid-column:2; grid-row:2; }
                      .st-key-home-nav [data-testid="stColumn"]:nth-child(4) { grid-column:3; grid-row:2; }
                    .st-key-home-nav .stButton > button { padding:0 6px; font-size:.78rem; }
                }
        @media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior:auto !important; transition:none !important; animation:none !important; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def brand():
    st.markdown(
        '<div class="brand-mark"><span class="brand-icon">⌕</span><span>findly<span style="color:#4559D6">.ai</span></span></div>',
        unsafe_allow_html=True,
    )


def badge(status):
    style = "status-found" if status == "Found" else "status-lost"
    return f'<span class="status {style}">{escape(status)}</span>'


def item_card(item, compact=False):
    with st.container(border=True):
        if item.get("image"):
            st.image(item["image"], width="stretch")
        top = st.columns([1, 1])
        with top[0]:
            st.markdown(badge(item["type"]), unsafe_allow_html=True)
        with top[1]:
            st.markdown(f'<div style="text-align:right;color:#708099;font-size:.75rem">{escape(item["category"])}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="item-title">{escape(item["name"])}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="muted" style="font-size:.82rem">{escape(item["description"][:115])}{"..." if len(item["description"]) > 115 else ""}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="item-meta" style="margin-top:10px">⌖ &nbsp;{escape(item["location"])}<br>◷ &nbsp;Reported {escape(item["date"])}</div>', unsafe_allow_html=True)
        if not compact:
            if item.get("match"):
                st.markdown('<div style="margin:10px 0"><span class="hero-pill">Potential match</span></div>', unsafe_allow_html=True)
            if st.button("View details", key=f"details_{item['id']}", width="stretch"):
                st.session_state.selected_item = item["id"]
                go("Item Details")


def page_header(title, description, tag=None):
    left, right = st.columns([4, 1])
    with left:
        if tag:
            st.markdown(f'<div class="eyebrow">{tag}</div>', unsafe_allow_html=True)
        st.title(title)
        st.markdown(f'<div class="muted">{description}</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        st.markdown('<span class="demo-note">● &nbsp;Demonstration workspace</span>', unsafe_allow_html=True)


def page_home():
    with st.container(key="home-nav"):
        nav1, nav2, nav3, nav4, nav5 = st.columns([2.2, .8, 1.1, .8, 1.2])
        with nav1:
            brand()
        with nav2:
            if st.button("Browse items", key="home_browse", width="stretch"):
                go("Browse Items")
        with nav3:
            if st.button("How it works", key="home_how", width="stretch"):
                st.session_state.show_how = True
        with nav4:
            if st.button("Sign in", key="home_signin", width="stretch"):
                st.session_state.auth_notice = True
                st.rerun()
        with nav5:
            if st.button("Get started", type="primary", key="home_start", width="stretch"):
                go("Overview")
    if st.session_state.get("auth_notice"):
        st.info("Sign-in is not enabled in this capstone demo. Use Get started to open the sample workspace.")

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    hero_text, hero_visual = st.columns([1.04, .96], gap="large", vertical_alignment="center")
    with hero_text:
        st.markdown('<div class="eyebrow">CAMPUS LOST &amp; FOUND</div>', unsafe_allow_html=True)
        st.markdown("<h1 style='font-size:3rem;max-width:650px;margin:.55rem 0 1rem'>Lost something?<br>Let AI help you find it.</h1>", unsafe_allow_html=True)
        st.markdown('<p class="muted" style="max-width:570px;font-size:1rem">An intelligent campus lost-and-found platform that connects lost belongings with their possible matches through smart text analysis.</p>', unsafe_allow_html=True)
        st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
        cta1, cta2 = st.columns([1.05, 1.1])
        with cta1:
            if st.button("Report lost item", type="primary", icon=":material/search:", width="stretch"):
                go("Report Lost Item")
        with cta2:
            if st.button("Report found item", icon=":material/add_circle:", width="stretch"):
                go("Report Found Item")
        st.markdown("<div style='margin-top:14px;color:#8A97AA;font-size:.74rem'>Free to use for your campus community</div>", unsafe_allow_html=True)
    with hero_visual:
        st.markdown('<div class="hero-panel">', unsafe_allow_html=True)
        st.markdown('<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><strong style="color:#152744">Smart match preview</strong><span class="hero-pill">DEMO RESULT</span></div>', unsafe_allow_html=True)
        lost, found = st.columns(2, gap="small")
        with lost:
            st.image(SAMPLE_ITEMS[3]["image"], width="stretch")
            st.markdown('<div class="item-meta">YOUR REPORT</div><div class="item-title">Black wireless headphones</div><div class="item-meta">Engineering Building · Oct 17</div>', unsafe_allow_html=True)
        with found:
            st.image(SAMPLE_ITEMS[1]["image"], width="stretch")
            st.markdown('<div class="item-meta">POSSIBLE FIND</div><div class="item-title">Wireless headphones</div><div class="item-meta">Engineering Building · Oct 17</div>', unsafe_allow_html=True)
        st.markdown('<hr style="border:0;border-top:1px solid #E8ECF3;margin:15px 0 12px"><div style="display:flex;justify-content:space-between;align-items:center"><span style="font-size:.83rem;color:#53627A">Description, category, place and date align</span><strong style="color:#4559D6">92% match</strong></div><div class="score-track" style="margin-top:8px"><div class="score-fill" style="width:92%"></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:58px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">SIMPLE BY DESIGN</div>', unsafe_allow_html=True)
    st.header("A clearer path from lost to found")
    step_cols = st.columns(3, gap="large")
    steps = [
        ("01", "Report an item", "Share a few details about what you lost or found, including where and when."),
        ("02", "Review possible matches", "Text analysis highlights reports with similar descriptions and context."),
        ("03", "Connect and verify", "Review the details and send a claim request to confirm ownership privately."),
    ]
    for col, (number, title, copy) in zip(step_cols, steps):
        with col:
            st.markdown(f'<div style="border-top:2px solid #DDE3EF;padding-top:15px"><div class="eyebrow">STEP {number}</div><div class="item-title" style="margin:10px 0">{title}</div><div class="muted">{copy}</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">CAMPUS FINDS</div>', unsafe_allow_html=True)
    st.header("Browse by category")
    cat_cols = st.columns(7, gap="small")
    for col, category in zip(cat_cols, CATEGORIES):
        with col:
            st.markdown(f'<div style="text-align:center;background:#fff;border:1px solid #E3E9F1;border-radius:7px;padding:14px 5px;color:#4559D6"><span class="material-symbols-rounded">{CATEGORY_ICONS[category]}</span><div style="font-size:.72rem;color:#43516A;margin-top:6px">{category}</div></div>', unsafe_allow_html=True)
    st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">DEMO DATA</div>', unsafe_allow_html=True)
    st.header("A campus community, connected")
    stats = st.columns(4)
    for col, value, label in zip(stats, ["128", "74", "31", "19"], ["Reports in sample", "Items found", "Potential matches", "Returned in sample"]):
        with col:
            st.metric(label, value)
    st.caption("Illustrative figures for the capstone demonstration. Not live campus data.")
    st.markdown('<div class="footer">Findly AI · AI Mini-Capstone demonstration &nbsp;&nbsp;·&nbsp;&nbsp; About &nbsp;&nbsp; Privacy &nbsp;&nbsp; Contact<br><span style="font-size:.72rem">No real-time messaging or campus notifications are enabled in this demo.</span></div>', unsafe_allow_html=True)

    if st.session_state.get("show_how"):
        with st.expander("How Findly AI works", expanded=True):
            st.write("Reports are compared using descriptive text and the item category, location, and date. Scores are rankings for review, not probabilities or proof of ownership.")
            if st.button("Close", key="close_how"):
                st.session_state.show_how = False
                st.rerun()


def page_overview():
    page_header("Campus Lost & Found Overview", "A central place to review campus reports and possible item matches.", "OVERVIEW")
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    metric_cols = st.columns(4, gap="medium")
    metrics = [("Open lost reports", "18", "+3 this week"), ("Found items", "26", "Across 7 locations"), ("Potential matches", "8", "Review suggested"), ("Successfully returned", "12", "Demonstration total")]
    for col, (label, value, delta) in zip(metric_cols, metrics):
        with col:
            st.metric(label, value, delta)
    st.caption("All figures above are illustrative demonstration data; no live campus records are connected.")

    search_col, search_btn = st.columns([5, 1])
    with search_col:
        search = st.text_input("Search reports", placeholder="Try ‘blue bottle’ or ‘library’", label_visibility="collapsed", key="overview_search")
    with search_btn:
        if st.button("Search", icon=":material/search:", width="stretch"):
            st.session_state.browse_query = search
            go("Browse Items")

    left, right = st.columns([1.75, 1], gap="large")
    with left:
        st.subheader("Recent reports")
        cat = st.selectbox("Category", ["All categories"] + CATEGORIES, label_visibility="collapsed", key="overview_category")
        recent = [x for x in st.session_state["items"] if cat == "All categories" or x["category"] == cat][:4]
        for item in recent:
            c1, c2 = st.columns([1, 3])
            with c1:
                st.image(item["image"], width="stretch")
            with c2:
                st.markdown(f'{badge(item["type"])} &nbsp; <span class="item-meta">{escape(item["category"])}</span>', unsafe_allow_html=True)
                st.markdown(f'<div class="item-title" style="margin-top:5px">{escape(item["name"])}</div><div class="item-meta">{escape(item["location"])} · {escape(item["date"])}</div>', unsafe_allow_html=True)
                if st.button("Open report", key=f"recent_{item['id']}"):
                    st.session_state.selected_item = item["id"]
                    go("Item Details")
            st.divider()
    with right:
        with st.container(border=True):
            st.subheader("AI match suggestions")
            st.markdown('<div class="muted">Ranked examples from the demonstration dataset. Scores are not ownership probabilities.</div>', unsafe_allow_html=True)
            st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
            for score, title, context in [("92%", "Wireless headphones", "Engineering Building · Oct 17"), ("78%", "Navy blue water bottle", "North Library · Oct 18"), ("64%", "Black card sleeve", "Science Quad · Oct 15")]:
                st.markdown(f'<div style="display:flex;justify-content:space-between"><strong style="font-size:.84rem;color:#152744">{title}</strong><strong style="font-size:.82rem;color:#4559D6">{score}</strong></div><div class="item-meta">{context}</div><div style="height:10px"></div>', unsafe_allow_html=True)
            if st.button("Review all matches", type="primary", width="stretch"):
                go("AI Matches")
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.subheader("Recent activity")
            for icon, text, when in [("add_circle", "A found item was reported", "12 min ago"), ("travel_explore", "New match suggestion available", "1 hr ago"), ("check_circle", "Claim request marked resolved", "Yesterday")]:
                st.markdown(f'<div style="display:flex;gap:10px;margin:12px 0"><span style="color:#4559D6" class="material-symbols-rounded">{icon}</span><div style="font-size:.82rem;color:#273850">{text}<div class="item-meta">{when} · sample activity</div></div></div>', unsafe_allow_html=True)


def page_browse():
    page_header("Browse items", "Search reports from the campus community and explore possible finds.", "ITEM DISCOVERY")
    st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        f1, f2, f3, f4 = st.columns([2.2, 1, 1.3, 1.1])
        with f1:
            query = st.text_input("Search", placeholder="Name, description or location", label_visibility="collapsed", key="browse_search", value=st.session_state.get("browse_query", ""))
        with f2:
            status = st.selectbox("Status", ["All statuses", "Lost", "Found"], label_visibility="collapsed", key="browse_type")
        with f3:
            category = st.selectbox("Category", ["All categories"] + CATEGORIES, label_visibility="collapsed", key="browse_category")
        with f4:
            matched = st.selectbox("Matches", ["Any match", "Has match", "No match"], label_visibility="collapsed", key="browse_match")
        f5, f6 = st.columns([2, 1])
        with f5:
            location = st.selectbox("Location", ["All locations"] + sorted({item["location"] for item in st.session_state["items"]}), label_visibility="collapsed", key="browse_location")
        with f6:
            period = st.selectbox("Reported", ["Any date", "Last 7 days", "Last 30 days"], label_visibility="collapsed", key="browse_date")

    results = st.session_state["items"]
    if query.strip():
        q = query.lower().strip()
        results = [
            x for x in results
            if q in " ".join([
                x["name"], x["description"], x["location"], x["category"],
                x.get("characteristics", ""),
            ]).lower()
        ]
    if status != "All statuses":
        results = [x for x in results if x["type"] == status]
    if category != "All categories":
        results = [x for x in results if x["category"] == category]
    if location != "All locations":
        results = [x for x in results if x["location"] == location]
    if matched == "Has match":
        results = [x for x in results if x.get("match")]
    elif matched == "No match":
        results = [x for x in results if not x.get("match")]
    if period != "Any date":
        days = 7 if period == "Last 7 days" else 30
        cutoff = date.today() - timedelta(days=days)
        def reported_date(item):
            try:
                return datetime.strptime(item["date"].split(" · ")[0], "%b %d, %Y").date()
            except ValueError:
                return None
        results = [item for item in results if reported_date(item) and cutoff <= reported_date(item) <= date.today()]

    st.markdown(f'<div class="item-meta" style="margin:15px 0">{len(results)} reports · demonstration dataset</div>', unsafe_allow_html=True)
    if results:
        for row_start in range(0, len(results), 3):
            cols = st.columns(3, gap="medium")
            for col, item in zip(cols, results[row_start:row_start + 3]):
                with col:
                    item_card(item)
    else:
        with st.container(border=True):
            st.markdown("### No reports match these filters")
            st.markdown('<div class="muted">Try a different keyword or clear one of the filters.</div>', unsafe_allow_html=True)
            if st.button("Clear search and filters", icon=":material/filter_alt_off:"):
                for key in ["browse_search", "browse_type", "browse_category", "browse_match", "browse_location", "browse_date"]:
                    st.session_state.pop(key, None)
                st.rerun()


def page_report(report_type):
    page_header(f"Report {report_type.lower()} item", "Add the details that can help someone recognize and return this item.", "NEW REPORT")
    if st.session_state.submitted_report and st.session_state.get("submitted_report_type") == report_type:
        st.success(f"{report_type} report {st.session_state.submitted_report} was saved in this session.")
        st.info("This demo stores reports only in this browser session. It does not publish them to a campus service.")
        if st.button("View report", type="primary"):
            st.session_state.selected_item = st.session_state.submitted_report
            go("Item Details")
    with st.container(border=True):
        st.markdown("#### Item information")
        name = st.text_input("Item name *", placeholder="For example, navy wireless headphones", key=f"report_name_{report_type}")
        category = st.selectbox("Category *", CATEGORIES, key=f"report_category_{report_type}")
        description = st.text_area("Description *", placeholder="Describe the item and anything that could help identify it.", max_chars=500, key=f"report_description_{report_type}")
        distinguishing = st.text_input("Distinguishing characteristics", placeholder="Brand, color, stickers, marks, contents", key=f"report_distinguishing_{report_type}")
        loc1, loc2 = st.columns(2)
        with loc1:
            location = st.text_input("Location *", placeholder="Building, room or nearby landmark", key=f"report_location_{report_type}")
        with loc2:
            reported_on = st.date_input("Date *", value=date.today(), key=f"report_date_{report_type}")
        time_value = st.time_input("Approximate time", value=datetime.now().replace(minute=0, second=0, microsecond=0).time(), key=f"report_time_{report_type}")
        uploaded = st.file_uploader("Optional image", type=["png", "jpg", "jpeg", "webp"], help="Avoid including faces, student ID numbers, or other private information.", key=f"report_image_{report_type}")
        st.markdown('<div class="muted" style="font-size:.78rem">Privacy: avoid posting personal contact details or sensitive identifiers. A claim request can be used to verify ownership privately.</div>', unsafe_allow_html=True)
        submit = st.button(f"Submit {report_type.lower()} report", type="primary", icon=":material/send:", key=f"submit_{report_type}")
        if submit:
            missing = []
            if not name.strip(): missing.append("item name")
            if category not in CATEGORIES: missing.append("category")
            if not description.strip(): missing.append("description")
            if not location.strip(): missing.append("location")
            if reported_on is None: missing.append("date")
            if missing:
                st.error("Please complete the required fields: " + ", ".join(missing) + ".")
            else:
                item_id = f"RPT-{uuid4().hex.upper()}"
                image = "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?auto=format&fit=crop&w=900&q=80"
                if uploaded:
                    image = uploaded
                new_item = {
                    "id": item_id, "name": name.strip(), "type": report_type, "category": category,
                    "description": description.strip(), "location": location.strip(),
                    "date": f"{reported_on.strftime('%b %d, %Y')} · {time_value.strftime('%I:%M %p')}", "image": image, "match": False,
                    "characteristics": distinguishing.strip() or "Not provided",
                }
                st.session_state["items"].insert(0, new_item)
                st.session_state.my_reports.insert(0, item_id)
                st.session_state.submitted_report = item_id
                st.session_state.submitted_report_type = report_type
                st.rerun()
    if st.session_state.submitted_report and st.session_state.page == ("Report Lost Item" if report_type == "Lost" else "Report Found Item"):
        pass


def page_matches():
    page_header("Potential Matches", "Lost reports are compared with Found reports using local text and context similarity.", "MATCH REVIEW")
    matching_mode = st.selectbox(
        "Matching mode",
        ["TF-IDF baseline", "Pretrained MiniLM (optional)"],
        key="matching_mode",
    )
    st.caption("Similarity scores rank candidates for review. They are not probabilities or confirmation of ownership.")
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    lost_reports = [item for item in st.session_state["items"] if item.get("type") == "Lost"]
    if not lost_reports:
        st.info("There are no Lost reports to compare yet. Submit a Lost report to see possible Found matches.")
        if st.button("Report a lost item", type="primary", icon=":material/add_circle:"):
            go("Report Lost Item")
        return

    lost_by_id = {item["id"]: item for item in lost_reports}
    selected_id = st.selectbox(
        "Lost report",
        list(lost_by_id),
        format_func=lambda item_id: f'{lost_by_id[item_id]["name"]} · {lost_by_id[item_id]["location"]}',
        key="match_lost_report",
    )
    report = lost_by_id[selected_id]
    with st.container(border=True):
        a, b = st.columns([1, 3])
        with a:
            if report.get("image"):
                st.image(report["image"], width="stretch")
        with b:
            st.markdown('<div class="eyebrow">YOUR LOST ITEM REPORT</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="item-title" style="font-size:1.12rem">{escape(report["name"])}</div><div class="muted">{escape(report["description"])}</div><div class="item-meta" style="margin-top:8px">{escape(report["category"])} · {escape(report["location"])} · {escape(report["date"])}</div><div class="item-meta" style="margin-top:5px">Identifying features: {escape(report.get("characteristics") or "Not provided")}</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
    requested_mode = "semantic" if matching_mode.startswith("Pretrained") else "lexical"
    matches, active_mode, fallback_message = rank_matches_with_mode(
        report, st.session_state["items"], mode=requested_mode
    )
    if fallback_message:
        st.warning(f"MiniLM is unavailable; using the TF-IDF baseline for this request. {fallback_message}")
    elif active_mode == "semantic":
        st.markdown('<div class="demo-note">PRETRAINED MODEL · MiniLM sentence embeddings</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="demo-note">BASELINE · TF-IDF lexical similarity</div>', unsafe_allow_html=True)
    candidates = [match for match in matches if match["score"] >= MATCH_THRESHOLD]
    if not candidates:
        st.info("No suitable Found reports match this Lost report yet. New Found reports can be reviewed here when their descriptions share enough detail.")
        return
    for match in candidates:
        candidate = match["item"]
        score = match["score"]
        with st.container(border=True):
            img, details = st.columns([1, 2.5], gap="large")
            with img:
                if candidate.get("image"):
                    st.image(candidate["image"], width="stretch")
                st.markdown(badge(candidate["type"]), unsafe_allow_html=True)
            with details:
                s1, s2 = st.columns([3, 1])
                with s1:
                    st.markdown(f'<div class="item-title" style="font-size:1.1rem">{escape(candidate["name"])}</div><div class="item-meta">{escape(candidate["category"])} · {escape(candidate["location"])} · {escape(candidate["date"])}</div>', unsafe_allow_html=True)
                with s2:
                    st.markdown(f'<div style="text-align:right;color:#4559D6;font-weight:800;font-size:1.25rem">{score:.1f}%</div><div class="item-meta" style="text-align:right">similarity score</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="score-track" style="margin:10px 0 12px"><div class="score-fill" style="width:{score}%"></div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="muted">{escape(candidate["description"])}</div>', unsafe_allow_html=True)
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                st.markdown('<strong style="font-size:.83rem;color:#263850">Why this ranked</strong>', unsafe_allow_html=True)
                for reason in match["reasons"]:
                    st.markdown(f'<div class="item-meta">· {escape(reason)}</div>', unsafe_allow_html=True)
                st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
                if match["differences"]:
                    st.markdown('<strong style="font-size:.83rem;color:#263850">Differences or missing details</strong>', unsafe_allow_html=True)
                    for difference in match["differences"]:
                        st.markdown(f'<div class="item-meta">· {escape(difference)}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="item-meta">No differences found in the provided fields. Verify the item in person.</div>', unsafe_allow_html=True)
                action1, action2 = st.columns([1, 1.4])
                with action1:
                    if st.button("View details", key=f"match_details_{candidate['id']}"):
                        st.session_state.selected_item = candidate["id"]
                        go("Item Details")
                with action2:
                    if st.button("Request claim", type="primary", key=f"claim_{candidate['id']}"):
                        st.session_state.claim_item = candidate["id"]
                        go("Claim Requests")
    text_method = "pretrained MiniLM cosine similarity" if active_mode == "semantic" else "TF-IDF cosine similarity"
    st.caption(f"Ranking combines {text_method} (65%), category agreement (20%), location term overlap (10%), and date proximity within 30 days (5%). The score is not an ownership probability.")


def page_evaluation():
    page_header("Matching evaluation", "Compare both matching modes against the same fixed, labeled Lost/Found pairs.", "MODEL EVALUATION")
    st.info("This small hand-labeled dataset evaluates this app's rankers only. It is not evidence of general real-world accuracy.")
    comparison = evaluate_comparison()
    baseline = comparison["baseline"]
    semantic = comparison["semantic"]

    st.caption(
        f'{baseline["evaluated_pairs"]} fixed Lost/Found pairs · '
        f'match threshold {baseline["threshold"]:.1f} · '
        "evaluation records are separate from live session reports"
    )
    baseline_col, semantic_col = st.columns(2, gap="large")
    with baseline_col:
        st.subheader("TF-IDF baseline")
        metric_cols = st.columns(3, gap="small")
        for col, label, key in zip(metric_cols, ["Precision", "Recall", "F1-score"], ["precision", "recall", "f1"]):
            with col:
                st.metric(label, f'{baseline["metrics"][key]:.1%}')
        st.caption("Current lexical ranker; no optional package or model required.")
    with semantic_col:
        st.subheader("Pretrained MiniLM")
        if semantic["available"]:
            metric_cols = st.columns(3, gap="small")
            for col, label, key in zip(metric_cols, ["Precision", "Recall", "F1-score"], ["precision", "recall", "f1"]):
                with col:
                    st.metric(label, f'{semantic["metrics"][key]:.1%}')
            st.caption("Pretrained sentence embeddings; evaluated on the same labeled pairs.")
        else:
            st.info(f'Semantic metrics are not available yet. {semantic["error"]}')

    st.subheader("Labeled pair results")
    table_rows = [
        {
            "Scenario": result["scenario"],
            "Lost report": result["lost_name"],
            "Found report": result["found_name"],
            "Expected": "Match" if result["expected_match"] else "Non-match",
            "TF-IDF prediction": "Match" if result["predicted_match"] else "Non-match",
            "TF-IDF score": f'{result["score"]:.1f}' if result["score"] is not None else "—",
            "Semantic prediction": (
                "Not available" if not semantic["available"] else
                "Match" if semantic["results"][index]["predicted_match"] else "Non-match"
            ),
            "Semantic score": (
                "—" if not semantic["available"] or semantic["results"][index]["score"] is None
                else f'{semantic["results"][index]["score"]:.1f}'
            ),
            "TF-IDF outcome": result["outcome"],
        }
        for index, result in enumerate(baseline["results"])
    ]
    st.dataframe(table_rows, hide_index=True, width="stretch")
    st.markdown(
        "**Method:** Both modes use the same expected labels and match threshold. Precision = TP / (TP + FP), "
        "recall = TP / (TP + FN), and F1 is their harmonic mean. A zero denominator returns 0. "
        "The embedding model is pretrained; it was not trained for this project. Similarity scores "
        "are not ownership probabilities, and this small evaluation does not establish real-world accuracy."
    )


def page_details():
    item = next((x for x in st.session_state["items"] if x["id"] == st.session_state.selected_item), None)
    if not item:
        st.warning("This report is not available in the current session.")
        if st.button("Back to browse"):
            go("Browse Items")
        return
    if st.button("Back to browse", icon=":material/arrow_back:"):
        go("Browse Items")
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    photo, content = st.columns([1.05, 1.2], gap="large")
    with photo:
        st.image(item["image"], width="stretch")
    with content:
        st.markdown(badge(item["type"]), unsafe_allow_html=True)
        st.title(item["name"])
        st.markdown(f'<div class="muted">{escape(item["description"])}</div>', unsafe_allow_html=True)
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown(f'<div class="item-meta">CATEGORY</div><strong>{escape(item["category"])}</strong><div style="height:12px"></div><div class="item-meta">APPROXIMATE LOCATION</div><strong>{escape(item["location"])}</strong><div style="height:12px"></div><div class="item-meta">REPORTED</div><strong>{escape(item["date"])}</strong><div style="height:12px"></div><div class="item-meta">IDENTIFYING CHARACTERISTICS</div><strong>{escape(item["characteristics"])}</strong>', unsafe_allow_html=True)
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        if item["type"] == "Found":
            if st.button("Request to claim", type="primary", icon=":material/verified_user:"):
                st.session_state.claim_item = item["id"]
                go("Claim Requests")
        st.caption("Contact details are not displayed publicly. Claim requests are stored locally for this demo session.")
    if item.get("match"):
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.subheader("Possible matching reports")
        st.markdown('<div class="muted">The demonstration dataset includes a related report. Review both descriptions and verify identifying details.</div>', unsafe_allow_html=True)
        if st.button("See potential matches", icon=":material/travel_explore:"):
            go("AI Matches")


def page_claims():
    page_header("Claim requests", "Send a private verification note and track its status in this browser session.", "RESOLUTION")
    preselected = st.session_state.get("claim_item")
    available = [x for x in st.session_state["items"] if x["type"] == "Found"]
    if available:
        default_index = next((i for i, x in enumerate(available) if x["id"] == preselected), 0)
        with st.container(border=True):
            st.subheader("Request to claim a found item")
            chosen = st.selectbox("Found report", available, index=default_index, format_func=lambda x: f'{x["name"]} · {x["location"]}', key="claim_select")
            message = st.text_area("Verification message *", placeholder="Share a detail that only the owner would know. Avoid posting sensitive personal information.", max_chars=400, key="claim_message")
            st.caption("This message is saved only in the current session. No email, notification, or real messaging is sent.")
            if st.button("Submit claim request", type="primary", icon=":material/send:"):
                if not message.strip():
                    st.error("Add a short verification message before submitting.")
                else:
                    st.session_state.claims.append({"item_id": chosen["id"], "item_name": chosen["name"], "message": message.strip(), "status": "Pending", "time": datetime.now().strftime("%b %d, %Y %H:%M")})
                    st.success("Claim request saved to this demo session.")
                    st.session_state.claim_message = ""
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.subheader("Request status")
    if not st.session_state.claims:
        with st.container(border=True):
            st.markdown("#### No claim requests yet")
            st.markdown('<div class="muted">Requests you submit will appear here with a session-only status.</div>', unsafe_allow_html=True)
    for index, claim in enumerate(st.session_state.claims):
        with st.container(border=True):
            status_class = {"Pending": "status-pending", "Accepted": "status-accepted", "Rejected": "status-rejected", "Resolved": "status-accepted"}.get(claim["status"], "status-pending")
            st.markdown(f'<div style="display:flex;justify-content:space-between"><strong>{escape(claim["item_name"])}</strong><span class="status {status_class}">{escape(claim["status"])}</span></div><div class="item-meta" style="margin-top:6px">Submitted {escape(claim["time"])}</div><div class="muted" style="margin-top:10px">{escape(claim["message"])}</div>', unsafe_allow_html=True)
            if claim["status"] == "Pending":
                b1, b2, _ = st.columns([1, 1, 3])
                with b1:
                    if st.button("Accept", key=f"accept_{index}"):
                        claim["status"] = "Accepted"
                        st.rerun()
                with b2:
                    if st.button("Reject", key=f"reject_{index}"):
                        claim["status"] = "Rejected"
                        st.rerun()
            elif claim["status"] == "Accepted":
                if st.button("Mark item returned", type="primary", key=f"resolve_{index}"):
                    claim["status"] = "Resolved"
                    st.success("Marked resolved in this demo session. This does not confirm a real-world return.")
                    st.rerun()
    st.caption("Accepting, rejecting, and resolving are demonstration controls; they do not contact another person or campus office.")


def page_settings():
    page_header("Settings", "Manage this local demonstration experience.", "PREFERENCES")
    with st.container(border=True):
        st.subheader("Demo workspace")
        st.markdown('<div class="muted">Findly AI is running with sample campus reports. Changes and submitted data exist only in the active browser session.</div>', unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.toggle("Show demonstration dataset", value=True, disabled=True)
        st.toggle("Email and push notifications", value=False, disabled=True, help="Notifications are not implemented in this demo.")
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("Reset demo session", icon=":material/restart_alt:"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def page_my_reports():
    page_header("My reports", "Review the lost and found reports you created in this demo session.", "YOUR ACTIVITY")
    reports = [item for item in st.session_state["items"] if item["id"] in st.session_state.my_reports]
    if not reports:
        with st.container(border=True):
            st.markdown("#### You have not submitted a report yet")
            st.markdown('<div class="muted">Reports you submit will appear here for this browser session.</div>', unsafe_allow_html=True)
            if st.button("Report an item", type="primary", icon=":material/add_circle:"):
                go("Report Lost Item")
        return
    for item in reports:
        left, right = st.columns([4, 1])
        with left:
            st.markdown(f'{badge(item["type"])} &nbsp; <strong>{escape(item["name"])}</strong><div class="item-meta">{escape(item["category"])} · {escape(item["location"])} · {escape(item["date"])}</div>', unsafe_allow_html=True)
        with right:
            if st.button("View report", key=f"my_report_{item['id']}"):
                st.session_state.selected_item = item["id"]
                go("Item Details")
        st.divider()


def sidebar():
    with st.sidebar:
        brand()
        st.markdown('<div class="sidebar-caption">WORKSPACE</div>', unsafe_allow_html=True)
        pages = ["Overview", "Browse Items", "Report Lost Item", "Report Found Item", "AI Matches", "Evaluation", "My Reports", "Claim Requests", "Settings"]
        selected = st.radio("Navigation", pages, index=pages.index(st.session_state.page) if st.session_state.page in pages else 0, label_visibility="collapsed", format_func=lambda x: {
            "Overview": ":material/dashboard:  Overview",
            "Browse Items": ":material/search:  Browse items",
            "Report Lost Item": ":material/remove_circle:  Report lost item",
            "Report Found Item": ":material/add_circle:  Report found item",
            "AI Matches": ":material/travel_explore:  AI matches",
            "Evaluation": ":material/assessment:  Evaluation",
            "My Reports": ":material/description:  My reports",
            "Claim Requests": ":material/task_alt:  Claim requests",
            "Settings": ":material/settings:  Settings",
        }[x], key="sidebar_navigation")
        if selected != st.session_state.page:
            st.session_state.page = selected
            st.rerun()
        st.markdown('<div style="height:18px"></div><div style="border-top:1px solid #E8ECF2;padding-top:14px"><span class="demo-note">DEMO MODE</span><div class="item-meta" style="margin-top:9px">Sample reports · Session-only data</div></div>', unsafe_allow_html=True)


def main():
    inject_styles()
    current = st.session_state.page
    if current == "Home":
        page_home()
        return
    sidebar()
    current = st.session_state.page
    if current == "Overview":
        page_overview()
    elif current == "Browse Items":
        page_browse()
    elif current == "Report Lost Item":
        page_report("Lost")
    elif current == "Report Found Item":
        page_report("Found")
    elif current == "AI Matches":
        page_matches()
    elif current == "Evaluation":
        page_evaluation()
    elif current == "Item Details":
        page_details()
    elif current == "Claim Requests":
        page_claims()
    elif current == "My Reports":
        page_my_reports()
    elif current == "Settings":
        page_settings()
    else:
        page_overview()


main()
