"""
Pipeline complet ML: données -> validation -> entraînement -> monitoring
"""
import logging
from pathlib import Path
from turtle import pd
from .data_loader import load_data, split_data, load_config
from .data_validator import validate_data_quality, create_data_validation_report
from .data_preparation import prepare_data, detect_feature_types, transform_new_data
from .model import train_model, evaluate_model
from .performance_monitor import detect_prediction_drift, monitor_model_performance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLPipeline:
    """Pipeline complet pour le projet MLOps"""
    
    def __init__(self, config_path="utils/config.yaml", model_name="enedis_model"):
        """Initialise le pipeline avec la configuration"""
        self.config = load_config(config_path)
        self.data = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.preprocessor = None
        self.feature_names = None
        self.model = None
        self.metrics = {}
        
        # Gestion des stages MLflow
        self.model_name = model_name
        self.version_staging = None
        self.promotion_result = None
        
        logger.info("Pipeline MLOps initialisé")
    
    def step_1_load_data(self, data_path):
        """Étape 1: Chargement des données"""
        logger.info("=== ÉTAPE 1: CHARGEMENT DES DONNÉES ===")
        self.data = load_data(data_path)
        return self.data is not None
    
    def step_2_validate_data(self, save_report=True):
        """Étape 2: Validation des données"""
        logger.info("=== ÉTAPE 2: VALIDATION DES DONNÉES ===")
        
        if self.data is None:
            logger.error("Pas de données à valider")
            return False
        
        # Validation basique
        validation_results = validate_data_quality(self.data)
        logger.info(f"Résultats de validation: {validation_results['is_valid']}")
        
        if not validation_results['is_valid']:
            logger.warning("Attention: Problèmes de qualité détectés")
        
        # Rapport Evidently
        if save_report:
            try:
                create_data_validation_report(
                    self.data,
                    output_path=self.config['monitoring']['report_path']
                )
            except Exception as e:
                logger.warning(f"Rapport Evidently non généré: {e}")
        
        return validation_results['is_valid']
    
    def step_3_prepare_data(self):
        """Étape 3: Préparation et prétraitement avancé des données"""
        logger.info("=== ÉTAPE 3: PRÉPARATION ET PRÉTRAITEMENT ===")
        
        if self.data is None:
            logger.error("Pas de données à préparer")
            return False
        
        # Division train/test
        logger.info("  → Division train/test...")
        test_size = self.config['model']['test_size']
        random_state = self.config['model']['random_state']
        
        self.X_train, self.X_test, self.y_train, self.y_test = split_data(
            self.data,
            test_size=test_size,
            random_state=random_state
        )
        logger.info(f"  ✓ Split effectué: train={self.X_train.shape}, test={self.X_test.shape}")
        
        # Prétraitement avancé (numériques, catégories, encoding)
        try:
            logger.info("  → Prétraitement avancé (imputation, scaling, encoding)...")
            result = prepare_data(self.X_train, self.X_test)
            
            self.X_train = result['X_train']
            self.X_test = result['X_test']
            self.preprocessor = result['preprocessor']
            self.feature_names = result['feature_names']
            
            logger.info(f"  ✓ Prétraitement effectué: {self.X_train.shape} (train), {self.X_test.shape} (test)")
            logger.info(f"  ✓ Features après preprocessing: {len(self.feature_names)}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du prétraitement: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def step_4_train_model(self):
        """Étape 4: Entraînement du modèle"""
        logger.info("=== ÉTAPE 4: ENTRAÎNEMENT DU MODÈLE ===")
        
        if self.X_train is None:
            logger.error("Pas de données d'entraînement")
            return False
        
        self.model = train_model(
            self.X_train,
            self.y_train,
            model_type=self.config['model']['model_type']
        )
        
        return self.model is not None
    
    def step_5_evaluate_model(self):
        """Étape 5: Évaluation du modèle"""
        logger.info("=== ÉTAPE 5: ÉVALUATION DU MODÈLE ===")
        
        if self.model is None:
            logger.error("Pas de modèle à évaluer")
            return False
        
        self.metrics = evaluate_model(self.model, self.X_test, self.y_test)
        return self.metrics is not None
    
    def step_6_monitor_performance(self):
        """Étape 6: Monitoring de la performance"""
        logger.info("=== ÉTAPE 6: MONITORING DE LA PERFORMANCE ===")
        
        if self.model is None:
            logger.error("Pas de modèle à monitorer")
            return False
        
        # Prédictions
        pred_train = self.model.predict(self.X_train)
        pred_test = self.model.predict(self.X_test)
        
        # Détection de drift
        drift_results = detect_prediction_drift(pred_train, pred_test)
        
        logger.info(f"Résultats du monitoring: Drift={drift_results['drift_detected']}")
        
        return True
    
    def step_7_log_with_mlflow(self):
        """Étape 7: Logging avec MLflow"""
        logger.info("=== ÉTAPE 7: LOGGING AVEC MLFLOW ===")
        
        if self.model is None or not self.metrics:
            logger.error("Pas de modèle ou métriques à logger")
            return False
        
        try:
            from .mlflow_tracker import log_training_session
            log_training_session(
                model=self.model,
                metrics=self.metrics,
                params=self.config['model'],
                experiment_name=self.config['mlflow']['experiment_name'],
                tracking_uri=self.config['mlflow']['tracking_uri']
            )
            return True
        except Exception as e:
            logger.error(f"Erreur lors du logging MLflow: {e}")
            return False
    
    def step_8_manage_model_stages(self, metric_keys=None, min_improvement=0.0):
        """
        Étape 8: Gestion des Aliases du modèle (Staging -> Production)
        Fonctionne indépendamment - peut être appelée après fermeture de la run MLflow
        Support de plusieurs métriques (ex: pour prédiction énergétique)
        
        Args:
            metric_keys: Liste de métriques à utiliser pour la comparaison
                        Ex: ["mae", "rmse", "accuracy"] (ordre de priorité)
                        Par défaut: ["mae", "rmse", "accuracy"] pour prédiction énergétique
            min_improvement: Amélioration minimale requise en % (défaut: 0.0)
            
        Returns:
            True si succès, False sinon
        """
        logger.info("=== ÉTAPE 8: GESTION DES ALIASES DU MODÈLE ===")
        
        # Définir les métriques par défaut pour prédiction énergétique
        if metric_keys is None:
            metric_keys = ["mae", "rmse", "accuracy"]
        elif isinstance(metric_keys, str):
            metric_keys = [metric_keys]
        
        try:
            import mlflow
            from .mlflow_tracker import (
                promote_model_to_production,
                get_model_version_by_alias,
                set_mlflow_tracking
            )
            
            # Configurer MLflow (ne pas dépendre de la run active)
            tracking_uri = self.config['mlflow']['tracking_uri']
            experiment_name = self.config['mlflow']['experiment_name']
            
            set_mlflow_tracking(tracking_uri)
            mlflow.set_experiment(experiment_name)
            
            logger.info(f"\n[1/4] Récupération du run_id et enregistrement du modèle en Staging...")
            logger.info(f"  Métriques à comparer (priorité): {metric_keys}")
            
            # Récupérer le run_id de la dernière run
            client = mlflow.tracking.MlflowClient()
            
            # Chercher la dernière run de l'expérience
            experiment = client.get_experiment_by_name(experiment_name)
            if not experiment:
                logger.error(f"Expérience '{experiment_name}' non trouvée")
                return False
            
            # Récupérer les runs de l'expérience
            runs = client.search_runs(experiment_ids=[experiment.experiment_id], max_results=1)
            
            if not runs:
                logger.error("Aucune run trouvée dans l'expérience")
                return False
            
            run_id = runs[0].info.run_id
            logger.info(f"  ℹ Run trouvée: {run_id}")
            
            # Enregistrer le modèle
            try:
                model_uri = f"runs:/{run_id}/model"
                mv = mlflow.register_model(model_uri, self.model_name)
                self.version_staging = int(mv.version)
                logger.info(f"  ✓ Modèle {self.model_name} v{self.version_staging} enregistré")
            except Exception as e:
                if "Model with same name already exists" in str(e):
                    versions = client.get_latest_versions(self.model_name)
                    self.version_staging = int(versions[0].version)
                    logger.info(f"  ✓ Nouvelle version créée: {self.model_name} v{self.version_staging}")
                else:
                    logger.error(f"  ✗ Erreur: {e}")
                    return False
            
            if self.version_staging is None:
                logger.error("Impossible de récupérer la version du modèle")
                return False
            
            # Vérifier les versions existantes avec l'alias "prod"
            logger.info(f"\n[2/4] État des versions avec alias 'prod'...")
            try:
                prod_version = get_model_version_by_alias(self.model_name, "prod")
                if prod_version:
                    logger.info(f"  ℹ Version actuelle avec alias 'prod': v{prod_version.version}")
                else:
                    logger.info(f"  ℹ Aucune version avec alias 'prod' (première fois)")
            except Exception:
                logger.info(f"  ℹ Aucune version avec alias 'prod' (première fois)")
            
            # Promotion automatique
            logger.info(f"\n[3/4] Promotion automatique en Production (alias 'prod')...")
            
            # Promouvoir avec validation des métriques
            self.promotion_result = promote_model_to_production(
                model_name=self.model_name,
                version=self.version_staging,
                alias_prod="prod",
                metric_keys=metric_keys,
                min_improvement=min_improvement
            )
            
            # Résultat final
            logger.info(f"\n[4/4] Résultat:")
            logger.info("-" * 60)
            if self.promotion_result['success']:
                logger.info(f"  ✓ SUCCÈS - Modèle promu avec alias 'prod'")
                logger.info(f"    Version: {self.promotion_result['version']}")
                logger.info(f"    Alias: {self.promotion_result.get('alias_prod', 'prod')}")
                logger.info(f"    Métrique de décision: {self.promotion_result.get('metric_used', 'N/A')}")
                
                # Afficher tous les métriques de la nouvelle version
                if self.promotion_result.get('metrics_new'):
                    logger.info(f"    Métriques de la nouvelle version:")
                    for key, val in self.promotion_result['metrics_new'].items():
                        logger.info(f"      • {key}: {val:.4f}")
                
                # Afficher l'amélioration si disponible
                improvement = self.promotion_result.get('improvement')
                improvement_pct = self.promotion_result.get('improvement_pct')
                if improvement is not None and improvement_pct is not None:
                    logger.info(f"    Amélioration: {improvement:+.4f} ({improvement_pct:+.1f}%)")
            else:
                logger.info(f"  ℹ Modèle v{self.version_staging} pas promu")
                logger.info(f"    Raison: {self.promotion_result['reason']}")
                metric_used = self.promotion_result.get('metric_used', 'N/A')
                logger.info(f"    Métrique de décision: {metric_used}")
                
                improvement = self.promotion_result.get('improvement')
                improvement_pct = self.promotion_result.get('improvement_pct')
                if improvement is not None and improvement_pct is not None:
                    logger.info(f"    Amélioration: {improvement:+.4f} ({improvement_pct:+.1f}%)")
            
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la gestion des aliases: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def run_full_pipeline(self, data_path):
        """Exécute le pipeline complet"""
        logger.info("\n" + "="*50)
        logger.info("DÉMARRAGE DU PIPELINE COMPLET")
        logger.info("="*50 + "\n")
        
        steps = [
            ("Chargement", lambda: self.step_1_load_data(data_path)),
            ("Validation", self.step_2_validate_data),
            ("Préparation et Prétraitement", self.step_3_prepare_data),
            ("Entraînement", self.step_4_train_model),
            ("Évaluation", self.step_5_evaluate_model),
            ("Monitoring", self.step_6_monitor_performance),
            ("MLflow Logging", self.step_7_log_with_mlflow),
            ("Gestion des Stages", self.step_8_manage_model_stages),
        ]
        
        for step_name, step_func in steps:
            try:
                if not step_func():
                    logger.error(f"Erreur à l'étape: {step_name}")
                    return False
            except Exception as e:
                logger.error(f"Exception à l'étape {step_name}: {e}")
                return False
        
        logger.info("\n" + "="*50)
        logger.info("PIPELINE TERMINÉ AVEC SUCCÈS")
        logger.info("="*50 + "\n")
        
        return True
