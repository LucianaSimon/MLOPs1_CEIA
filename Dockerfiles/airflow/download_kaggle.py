"""
Script para descargar el dataset 'Airline Passenger Satisfaction' desde Kaggle.

Requisitos previos:
1. Instalar la librería oficial de Kaggle o kagglehub:
   pip install kagglehub
   (o bien: pip install kaggle)

2. Credenciales de Kaggle:
   - Ve a https://www.kaggle.com/settings -> pestaña 'API' -> 'Create New Token'.
   - Se descargará un archivo 'kaggle.json'.
   - Coloca 'kaggle.json' en:
     * Linux/macOS: ~/.kaggle/kaggle.json
     * Windows: C:\Users\<TuUsuario>\.kaggle\kaggle.json
   - Asegúrate de darle permisos adecuados (en Linux/macOS: chmod 600 ~/.kaggle/kaggle.json).
"""

import os
import sys

def download_with_kagglehub():
    """Descarga usando la librería moderna recomendada por Kaggle: kagglehub."""
    try:
        import kagglehub
        print("Descargando dataset usando 'kagglehub'...")
        path = kagglehub.dataset_download("teejmahal20/airline-passenger-satisfaction")
        print(f"Dataset descargado correctamente en: {path}")
        return path
    except ImportError:
        print("[!] 'kagglehub' no está instalado. Probando con la API clásica de kaggle...")
        return None

def download_with_kaggle_api(destination_dir="./data"):
    """Descarga y descomprime usando la API clásica 'kaggle'."""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        
        api = KaggleApi()
        print("Autenticando con Kaggle API...")
        api.authenticate()
        
        os.makedirs(destination_dir, exist_ok=True)
        dataset_slug = "teejmahal20/airline-passenger-satisfaction"
        print(f"Descargando y descomprimiendo '{dataset_slug}' en '{destination_dir}'...")
        
        api.dataset_download_files(dataset_slug, path=destination_dir, unzip=True)
        print(f"Archivos descargados con éxito en: {os.path.abspath(destination_dir)}")
        return os.path.abspath(destination_dir)
    except Exception as e:
        print(f"[!] Error al descargar con Kaggle API: {e}")
        return None

def main():
    dataset_name = "teejmahal20/airline-passenger-satisfaction"
    print(f"Iniciando descarga para: {dataset_name}
")
    
    # Intento 1: kagglehub (método más directo y moderno)
    path = download_with_kagglehub()
    if path:
        sys.exit(0)
        
    # Intento 2: kaggle API clásica con descompresión automática en ./data
    path = download_with_kaggle_api(destination_dir="./airline_passenger_satisfaction_data")
    if path:
        sys.exit(0)
        
    print("
No se pudo completar la descarga automática.")
    print("Asegúrate de instalar una de las opciones:")
    print("  pip install kagglehub")
    print("  pip install kaggle")
    print("Y configurar tu token 'kaggle.json'.")

if __name__ == "__main__":
    main()
Elemento ampliado 