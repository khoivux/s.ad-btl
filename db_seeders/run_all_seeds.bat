@echo off
echo ==============================================
echo   MICROSTORE DATABASE SEEDER RUNNER
echo ==============================================

set BASE_DIR=%~dp0..

echo [1/8] Seeding User Levels...
set PYTHONPATH=%BASE_DIR%\user-service
python user_levels_seed.py

echo [2/8] Seeding Product Categories...
set PYTHONPATH=%BASE_DIR%\product-service
python product_categories_seed.py

echo [3/8] Seeding Products...
set PYTHONPATH=%BASE_DIR%\product-service
python product_items_seed.py

echo [4/8] Seeding Interactions...
set PYTHONPATH=%BASE_DIR%\interaction-service
python interaction_seed.py

echo [5/8] Seeding Reviews/Comments...
set PYTHONPATH=%BASE_DIR%\comment-rate-service
python comment_seed_reviews.py

echo [6/8] Seeding Orders...
set PYTHONPATH=%BASE_DIR%\order-service
python order_seed.py

echo [7/8] Seeding Neo4j Knowledge Graph...
set PYTHONPATH=%BASE_DIR%\recommender-ai-service
python neo4j_seed.py

echo [8/8] Seeding API Gateway Interactions...
set PYTHONPATH=%BASE_DIR%\api_gateway
python api_seed_interactions.py

echo ==============================================
echo   SEEDING COMPLETED!
echo ==============================================
pause
