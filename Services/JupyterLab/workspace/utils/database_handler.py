"""
Gestion de la base de données PostgreSQL pour stocker les prédictions
"""
import logging
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()


class Prediction(Base):
    """Modèle de données pour les prédictions"""
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    prediction = Column(Float, nullable=False)
    confidence = Column(Float, nullable=True)
    model_version = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseHandler:
    """Classe pour gérer les opérations de base de données"""
    
    def __init__(self, db_uri):
        """
        Initialise la connexion à la base de données
        
        Args:
            db_uri: URI de connexion PostgreSQL 
                   (ex: postgresql://user:password@host:port/dbname)
        """
        self.db_uri = db_uri
        self.engine = None
        self.Session = None
        
        try:
            self.engine = create_engine(db_uri)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("Moteur de base de données créé")
        except Exception as e:
            logger.error(f"Erreur lors de la création du moteur BD: {str(e)}")
    
    def create_tables(self):
        """Crée les tables si elles n'existent pas"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Tables créées avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la création des tables: {str(e)}")
            return False
    
    def store_predictions(self, df_predictions, model_version):
        """
        Stocke les prédictions en base de données
        
        Args:
            df_predictions: DataFrame contenant les prédictions avec colonnes
                           'timestamp', 'prediction', 'confidence' (optionnel)
            model_version: Version du modèle utilisé
            
        Returns:
            True si succès, False sinon
        """
        if self.Session is None:
            logger.error("Session BD non initialisée")
            return False
        
        try:
            session = self.Session()
            
            # Préparer les données
            records = []
            for idx, row in df_predictions.iterrows():
                record = Prediction(
                    timestamp=row['timestamp'],
                    prediction=float(row['prediction']),
                    confidence=float(row['confidence']) if 'confidence' in row and pd.notna(row['confidence']) else None,
                    model_version=model_version
                )
                records.append(record)
            
            # Insérer tous les enregistrements
            session.add_all(records)
            session.commit()
            
            logger.info(f"{len(records)} prédictions stockées en base de données")
            session.close()
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du stockage des prédictions: {str(e)}")
            if session:
                session.rollback()
                session.close()
            return False
    
    def get_recent_predictions(self, limit=100):
        """
        Récupère les prédictions récentes
        
        Args:
            limit: Nombre maximum de prédictions à retourner
            
        Returns:
            DataFrame des prédictions ou None en cas d'erreur
        """
        if self.Session is None:
            logger.error("Session BD non initialisée")
            return None
        
        try:
            session = self.Session()
            
            query = session.query(Prediction).order_by(Prediction.timestamp.desc()).limit(limit)
            predictions = query.all()
            
            # Convertir en DataFrame
            data = []
            for pred in predictions:
                data.append({
                    'id': pred.id,
                    'timestamp': pred.timestamp,
                    'prediction': pred.prediction,
                    'confidence': pred.confidence,
                    'model_version': pred.model_version,
                    'created_at': pred.created_at
                })
            
            df_result = pd.DataFrame(data)
            logger.info(f"{len(df_result)} prédictions récentes récupérées")
            session.close()
            
            return df_result if len(data) > 0 else None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des prédictions: {str(e)}")
            return None
    
    def verify_connection(self):
        """Vérifie la connexion à la base de données"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("Connexion à la base de données vérifiée")
                return True
        except Exception as e:
            logger.error(f"Erreur de connexion BD: {str(e)}")
            return False
    
    def get_prediction_stats(self):
        """Retourne des statistiques sur les prédictions stockées"""
        if self.Session is None:
            return None
        
        try:
            session = self.Session()
            
            count = session.query(Prediction).count()
            
            stats = {
                'total_predictions': count,
                'table_exists': True
            }
            
            session.close()
            logger.info(f"Statistiques: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {str(e)}")
            return None
