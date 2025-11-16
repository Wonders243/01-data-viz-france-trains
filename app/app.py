
import streamlit as st            
import pandas as pd              
import plotly.express as px      


# --------------------------------------------
#          CONFIGURATION DE LA PAGE
# --------------------------------------------
st.set_page_config(
    page_title="🚄 TGV Regularity Dashboard", 
    layout="wide"
)
st.sidebar.header("PARAMETRE")

st.title("🚄 Régularité Mensuelle des TGV (SNCF)")

st.markdown("""
Analyse interactive des retards et causes de perturbation des TGV en France.  
*Source : data.sncf.com — Régularité Mensuelle TGV AQST*
""")


# --------------------------------------------
#        CHARGEMENT DU FICHIER CSV
# --------------------------------------------

@st.cache_data
def load_data():

    df = pd.read_csv("data/regularite-mensuelle-tgv.csv", sep=";")


    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Conversion de la colonne date en objet datetime
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Création d'une colonne "relation" pour afficher Depart → Arrivée
    df["relation"] = df["gare_de_départ"] + " → " + df["gare_d'arrivée"]

    return df

# Charge les données
df = load_data()


# --------------------------------------------
#       APERCU RAPIDE DES DONNEES
# --------------------------------------------

st.subheader("Aperçu du jeu de données")
st.dataframe(df.head(10))


# --------------------------------------------
#                FILTRES SIDEBAR
# --------------------------------------------

# Filtre par année
periode= st.sidebar.slider("Sélectionner une plage de dates :", 
                  min_value=df["date"].min().date(), 
                  max_value=df["date"].max().date(), 
                  value=(df["date"].min().date(), df["date"].max().date())
                 )


selected_years = list(range(periode[0].year, periode[1].year + 1))

# On filtre le DataFrame selon les années choisies
df_filtered = df[df["date"].dt.year.isin(selected_years)]

# --------------------------------------------
#   VISUALISATION 1 : Causes principales retard
# --------------------------------------------
st.subheader("📊 Répartition des causes de retard")

# Liste des colonnes contenant les % des causes
cause_cols = [
    "prct_retard_pour_causes_externes",
    "prct_retard_pour_cause_infrastructure",
    "prct_retard_pour_cause_gestion_trafic",
    "prct_retard_pour_cause_matériel_roulant",
    "prct_retard_pour_cause_gestion_en_gare_et_réutilisation_de_matériel",
    "prct_retard_pour_cause_prise_en_compte_voyageurs_(affluence,_gestions_psh,_correspondances)"
]

# On calcule la moyenne de chaque cause
cause_data = df_filtered[cause_cols].mean().sort_values(ascending=False)

# Graphique barres horizontales
fig1 = px.bar(
    x=cause_data.values,
    y=[c.replace("_", " ").replace("prct retard pour ", "") for c in cause_data.index],
    orientation="h",
    title="Moyenne des causes de retard (%)"
)

st.plotly_chart(fig1, use_container_width=True)


# -----------------------------------------------------
# VISUALISATION 2 : Retard moyen à l'arrivée par ligne
# -----------------------------------------------------

st.subheader("🚆 Retard moyen à l'arrivée par ligne")

colname = "retard_moyen_des_trains_en_retard_à_l'arrivée" 

if colname in df.columns:

    # Moyenne par ligne + tri décroissant
    top_routes = (
        df_filtered.groupby("relation")[colname]
        .mean()
        .sort_values(ascending=False)
        .head(15)
    )

    # Graphique
    fig2 = px.bar(
        top_routes,
        x=top_routes.values,
        y=top_routes.index,
        orientation="h",
        title="Top 15 des lignes les plus en retard à l'arrivée (minutes)"
    )

    st.plotly_chart(fig2, use_container_width=True)
else:
    st.error(f"❌ Colonne introuvable : {colname}")

# -----------------------------------------------------
# VISUALISATION 3 : Évolution du retard par gare
# -----------------------------------------------------
st.subheader("📈 Évolution du retard moyen des TGV")


relations = sorted(df["relation"].unique())

selected_relations = st.multiselect(
    "🚄 Sélectionne une ou plusieurs lignes TGV :",
    options=relations,
    default=[]
)

# -----------------------------------------------------
# Si aucune relation sélectionnée → rien à afficher
# -----------------------------------------------------
if not selected_relations:
    st.info("🔍 Sélectionne une ligne pour afficher les graphiques.")
else:

    # Filtrage sur les relations sélectionnées
    df_filtered_rel = df[df["relation"].isin(selected_relations)]


    # -----------------------------------------------------
    # FIGURE : évolution du retard moyen
    # -----------------------------------------------------
    fig3 = px.line(
        df_filtered_rel,
        x="date",
        y=colname,   
        color="relation",
        title="Évolution mensuelle du retard moyen à l'arrivée"
    )

    st.plotly_chart(fig3, use_container_width=True)


# -----------------------------------------------------
# VISUALISATION 4 : Courbe des retards par cause
# -----------------------------------------------------

st.subheader("📈 Évolution des retards par cause")

if not selected_relations:
    st.info("🔍 Sélectionne d'abord une ou plusieurs lignes TGV.")
else:

    selected_causes = st.multiselect(
        "🎯 Causes du retard :",
        options=cause_cols,
        default=[]
    )

    df_causes = df[df["relation"].isin(selected_relations)]
    
    # Garder juste les colonnes nécessaires
    df_causes = df_causes[["date", "relation"] + selected_causes]

    # Transformer les causes en format long (melt) pour tracer plusieurs courbes
    df_long = df_causes.melt(
        id_vars=["date", "relation"],
        value_vars=selected_causes,
        var_name="cause",
        value_name="pourcentage"
    )

    # Nettoyage noms pour affichage plus propre
    df_long["cause"] = df_long["cause"].str.replace("_", " ").str.replace("prct retard pour cause","")
    
    # Graphique
    fig_cause_curve = px.line(
        df_long,
        x="date",
        y="pourcentage",
        color="cause",          
        line_dash="relation",   
        title="Évolution des causes de retard dans le temps"
    )

    st.plotly_chart(fig_cause_curve, use_container_width=True)
