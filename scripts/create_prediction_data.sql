-- Crear 100 pasajeros de prueba para el módulo de predicciones.
-- Utilizamos los datos de Test, pero eliminamos la satisfacción conocida.

CREATE TABLE IF NOT EXISTS bronze.passenger_satisfaction_predict AS
SELECT *
FROM bronze.passenger_satisfaction_test
ORDER BY raw_id
LIMIT 100;

-- Eliminar la variable que queremos predecir.
ALTER TABLE bronze.passenger_satisfaction_predict
DROP COLUMN IF EXISTS satisfaction;