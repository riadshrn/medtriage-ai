### calcul de la conso de l'agent

J'ai branché l'Agent. Quand il tourne, il stocke ses résultats dans `st.session_state['last_agent_audit'].`

j'ai fait un brouillon de comment tu peux intégrer ça au dashboard mais c'est pas idéal, l'idéal serait peut etre que, pour un traitement (un patient qui arrive aux urgences par exemple), dans *Dashboard* on ait la conso totale du traitement (tokens, latence, consommations) avec les équivalents ampoules allumées etc, et en dessous le détail d'où vient la conso (l'agent : tant de tokens/latence/conso, la RAG : tant de tokens etc...)

Mais jsp comment est ta base de données etc
 
```python
# Snippet pour le Dashboard (à adapter par ta collègue)
if 'last_agent_audit' in st.session_state and st.session_state['last_agent_audit']:
    agent_data = st.session_state['last_agent_audit']
    metrics = agent_data.get('metrics') # C'est le dictionnaire complet
    
    if metrics:
        st.subheader("🌱 Impact Agent (Dernière exécution)")
        
        # Affichage en 4 colonnes
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Latence", f"{metrics['latency_s']:.2f} s")
        c2.metric("Tokens Total", metrics['total_tokens'])
        c3.metric("Coût", f"${metrics['cost_usd']:.5f}")
        
        # Mise en valeur du CO2
        gwp_mg = metrics['gwp_kgco2'] * 1e6 # Conversion en mg pour affichage
        c4.metric("Empreinte CO2", f"{gwp_mg:.3f} mg", help="Modèle calibré sur Mistral-Small/FRA")
        
        # Optionnel : Afficher le détail Input/Output
        with st.expander("Détail consommation"):
            st.json(metrics)
else:
    st.info("Aucune donnée d'agent disponible. Lancez un audit depuis l'Accueil.")
```

