from sqlalchemy.orm import Session, joinedload
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.db.models import AccidentMeta, AccidentNarrative
import os

# Ensure OPENAI_API_KEY is set in environment variables
# from dotenv import load_dotenv
# load_dotenv()

CHROMADB_DIR = "./chroma_db"
COLLECTION_NAME = "aero_safety_db"

def sync_legacy_db_to_chroma(db: Session):
    """
    Ingests data from the MariaDB 'A_FILE' (AccidentMeta) and 'E_FILE' (AccidentNarrative) tables 
    into ChromaDB 'aero_safety_2' collection.
    """
    print("Fetching data from Legacy DB (AccidentMeta)...")
    
    # Verify DB Connection and Fetch
    try:
        # Use joinedload to fetch narratives efficiently in one query if possible, 
        # or just access them (lazy load) since we are in a session.
        # But for large datasets, explicit join or eager load is better.
        records = db.query(AccidentMeta).options(joinedload(AccidentMeta.narratives)).limit(500).all() # Limit for safety during dev
        
        if not records:
             print("No records found in A_FILE.")
             return {"status": "warning", "message": "No records found in DB."}
             
        print(f"Fetched {len(records)} records. Preparing documents...")
        
        documents = []
        for row in records:
            # Extract Narrative
            narrative_text = "N/A"
            # Assuming narratives is a list/relationship. 
            # If it's 1:1 and mapped as object, access directly.
            # Based on models.py: messages = relationship(...) -> usually list unless uselist=False
            if row.narratives:
                if isinstance(row.narratives, list):
                     narrative_text = "\n".join([n.description or "" for n in row.narratives])
                else:
                     narrative_text = row.narratives.description or ""
            
            # Format the content for RAG
            # We want to include key fields that help the LLM understand the context.
            content = f"""
Report ID: {row.report_id or 'N/A'}
Date: {row.date or 'N/A'}
Location: {row.city or 'N/A'}, {row.state or 'N/A'}
Aircraft: {row.aircraft_make or 'N/A'} {row.aircraft_model or 'N/A'}
Event Type: {row.event_type or 'N/A'}

Narrative:
{narrative_text}

Probable Cause:
{row.primary_cause_text or 'N/A'}

Contributing Factors:
{row.contributing_factor_text or 'N/A'}
"""
            # Create Document object
            doc = Document(
                page_content=content,
                metadata={
                    "source": "MariaDB",
                    "report_id": row.report_id,
                    "year": row.year or "Unknown"
                }
            )
            documents.append(doc)

        print(f"Created {len(documents)} documents. Splitting...")
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=150,
            separators=["\n\n", "\n", ".", " ", ""],
        )
        
        split_docs = splitter.split_documents(documents)
        print(f"Total chunks to ingest: {len(split_docs)}")
        
        if not split_docs:
             return {"status": "warning", "message": "No content to ingest after splitting."}

        # Initialize Embeddings
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Initialize Chroma and persist (this will upsert or add)
        # Note: If we want to fully replace, we might need to delete collection first. 
        # For now, we append/update.
        print(f"Ingesting into ChromaDB collection '{COLLECTION_NAME}'...")
        vector_store = Chroma.from_documents(
            documents=split_docs,
            embedding=embeddings,
            persist_directory=CHROMADB_DIR,
            collection_name=COLLECTION_NAME
        )
        
        print("Ingestion complete.")
        return {"status": "success", "count": len(split_docs), "collection": COLLECTION_NAME}

    except Exception as e:
        print(f"Error during DB sync: {e}")
        raise e
