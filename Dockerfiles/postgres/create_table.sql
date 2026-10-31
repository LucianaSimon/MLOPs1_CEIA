CREATE TABLE bronze.test_table (
    user_id TEXT,
    user_name TEXT,
    user_mail TEXT
);

-- docker exec -it mlops_postgres psql -U postgres -d mlops_ceia -c "CREATE TABLE IF NOT EXISTS bronze.test_table (user_id TEXT, user_name TEXT, user_mail TEXT);"
-- docker build -t postgres-test:latest . 
-- docker run -d --name mlops_postgres -p 5432:5432 postgres-image