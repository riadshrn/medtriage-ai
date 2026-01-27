import os
import json
import re
import chromadb
from chromadb.utils import embedding_functions

# --- CONFIGURATION ---
# Chemins relatifs (assure-toi que les dossiers existent)
MD_PATH = "src/data/knowledge_base/medical_knowledge.md"
JSON_PATH = "src/data/knowledge_base/Ressources_Projet.json" 
DB_PATH = "data/vector_db"

# Modèle d'embedding (transforme le texte en vecteurs)
ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="paraphrase-multilingual-MiniLM-L12-v2")

def parse_markdown(file_path):
    """Découpe le protocole MD en sections (##) ET sous-sections (###)."""
    if not os.path.exists(file_path):
        print(f"⚠️ Fichier introuvable : {file_path}")
        return [], [], []

    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # On découpe d'abord par les gros titres (##)
    # Le regex (pointer/lookahead) permet de garder le délimiteur si besoin, 
    # mais ici on split simple et on reconstruit.
    main_sections = re.split(r'\n##\s+', text)
    
    documents = []
    metadatas = []
    ids = []
    
    doc_counter = 0

    for section in main_sections:
        if not section.strip(): continue
        
        # On extrait le titre principal et le reste
        parts = section.split('\n', 1)
        main_title = parts[0].strip()
        content_body = parts[1].strip() if len(parts) > 1 else ""
        
        # Est-ce qu'il y a des sous-sections (###) dans ce corps ?
        # Ex: Dans "Situations Spécifiques", il y a "Douleur Thoracique", "Fièvre"...
        sub_sections = re.split(r'\n###\s+', content_body)
        
        if len(sub_sections) > 1:
            # Cas : Il y a des sous-sections -> On crée un doc pour chaque sous-section
            for sub in sub_sections:
                if not sub.strip(): continue
                sub_lines = sub.split('\n', 1)
                sub_title = sub_lines[0].strip()
                sub_content = sub_lines[1].strip() if len(sub_lines) > 1 else ""
                
                # Le document contient le contexte global + local
                full_doc = f"CONTEXTE : {main_title}\nSUJET : {sub_title}\nREGLES :\n{sub_content}"
                
                documents.append(full_doc)
                metadatas.append({"source": "protocoles", "category": main_title, "topic": sub_title})
                ids.append(f"rule_{doc_counter}")
                doc_counter += 1
        else:
            # Cas : Pas de sous-section (ex: Intro, ou définition ROUGE globale)
            full_doc = f"REGLE GENERALE : {main_title}\nCONTENU :\n{content_body}"
            documents.append(full_doc)
            metadatas.append({"source": "protocoles", "category": "general", "topic": main_title})
            ids.append(f"rule_{doc_counter}")
            doc_counter += 1
            
    return documents, metadatas, ids

def parse_json(file_path):
    """Transforme les exemples JSON en texte cherchable."""
    if not os.path.exists(file_path):
        print(f"⚠️ Fichier introuvable : {file_path}")
        return [], [], []

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    documents = []
    metadatas = []
    ids = []
    
    for item in data:
        # On formate pour que l'IA comprenne que c'est un EXEMPLE
        # Ex: "CAS SIMILAIRE (GRIS) : Petite coupure..."
        text = f"CAS CLINIQUE DE REFERENCE ({item['category']}) : {item['description']}"
        
        documents.append(text)
        metadatas.append({
            "source": "exemples_pdf", 
            "type": "case", 
            "category": item['category']
        })
        ids.append(f"case_{item['id']}")
        
    return documents, metadatas, ids

def main():
    print("🔄 Initialisation de la base vectorielle...")
    
    # On supprime l'ancienne DB si elle existe pour repartir à propre (optionnel mais conseillé en dev)
    if os.path.exists(DB_PATH):
        # Chroma gère mal la suppression de dossier à chaud sous Windows parfois, 
        # donc on se contente de reset la collection
        pass

    client = chromadb.PersistentClient(path=DB_PATH)
    
    # On recrée la collection à zéro
    try:
        client.delete_collection(name="medical_knowledge")
    except:
        pass
        
    collection = client.get_or_create_collection(name="medical_knowledge", embedding_function=ef)
    
    # 1. Traitement Markdown
    docs_md, metas_md, ids_md = parse_markdown(MD_PATH)
    print(f"📚 {len(docs_md)} Règles protocolaires trouvées.")
    
    # 2. Traitement JSON
    docs_json, metas_json, ids_json = parse_json(JSON_PATH)
    print(f"🗂️ {len(docs_json)} Cas cliniques trouvés.")
    
    # 3. Fusion et Indexation
    full_docs = docs_md + docs_json
    full_metas = metas_md + metas_json
    full_ids = ids_md + ids_json
    
    if full_docs:
        print("📥 Indexation en cours dans ChromaDB...")
        collection.upsert(documents=full_docs, metadatas=full_metas, ids=full_ids)
        print("✅ Base Vectorielle générée avec succès !")
    else:
        print("❌ Aucune donnée à indexer.")

if __name__ == "__main__":
    main()