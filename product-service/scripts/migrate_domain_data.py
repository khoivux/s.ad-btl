import os
import sys
import django

# Setup Django env
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from modules.catalog.infrastructure.models import (
    ProductModel, BookModel, ElectronicsModel, FashionModel,
    CosmeticsModel, ToysModel, FurnitureModel, FoodModel,
    MedicineModel, PetSuppliesModel, AutoPartsModel
)

def migrate():
    products = ProductModel.objects.all()
    print(f"Starting migration for {products.count()} products...")

    stats = {
        'Book': 0, 'Electronics': 0, 'Fashion': 0, 'Cosmetics': 0,
        'Toys': 0, 'Furniture': 0, 'Food': 0, 'Medicine': 0,
        'PetSupplies': 0, 'AutoParts': 0, 'Skipped': 0
    }

    for p in products:
        category_name = p.category.name if p.category else "Unknown"
        attrs = p.attributes or {}
        
        try:
            if category_name == 'Book':
                BookModel.objects.update_or_create(
                    product=p,
                    defaults={
                        'author': attrs.get('author', 'Unknown'),
                        'publisher': attrs.get('publisher', 'Unknown'),
                        'isbn': attrs.get('isbn', 'Unknown')
                    }
                )
                stats['Book'] += 1
            
            elif category_name in ['Laptop', 'Mobile', 'Watch', 'Home Appliances']:
                ElectronicsModel.objects.update_or_create(
                    product=p,
                    defaults={
                        'brand': attrs.get('brand') or attrs.get('manufacturer', 'Unknown'),
                        'warranty': int(attrs.get('warranty', 12))
                    }
                )
                stats['Electronics'] += 1
                
            elif category_name in ['Fashion', 'Shoes']:
                FashionModel.objects.update_or_create(
                    product=p,
                    defaults={
                        'size': attrs.get('size', 'M'),
                        'color': attrs.get('color', 'Black')
                    }
                )
                stats['Fashion'] += 1
                
            elif category_name == 'Cosmetics':
                CosmeticsModel.objects.update_or_create(
                    product=p,
                    defaults={
                        'brand': attrs.get('brand', 'Unknown'),
                        'skin_type': attrs.get('skin_type', 'All'),
                        'is_organic': attrs.get('is_organic', False),
                        'expiration_date': attrs.get('expiration_date')
                    }
                )
                stats['Cosmetics'] += 1
                
            elif category_name == 'Toys':
                ToysModel.objects.update_or_create(
                    product=p,
                    defaults={
                        'age_group': attrs.get('age_group', '3+'),
                        'material': attrs.get('material', 'Plastic'),
                        'requires_batteries': attrs.get('requires_batteries', False)
                    }
                )
                stats['Toys'] += 1
                
            elif category_name == 'Furniture':
                FurnitureModel.objects.update_or_create(
                    product=p,
                    defaults={
                        'material': attrs.get('material', 'Wood'),
                        'dimensions': attrs.get('dimensions', 'Unknown'),
                        'weight_capacity': float(attrs.get('weight_capacity', 0))
                    }
                )
                stats['Furniture'] += 1
                
            elif category_name == 'Food':
                FoodModel.objects.update_or_create(
                    product=p,
                    defaults={
                        'expiration_date': attrs.get('expiration_date', '2026-12-31'),
                        'weight': attrs.get('weight', 'Unknown'),
                        'is_vegetarian': attrs.get('is_vegetarian', False),
                        'calories': int(attrs.get('calories', 0))
                    }
                )
                stats['Food'] += 1
            
            # Medicine, PetSupplies, AutoParts usually don't exist in old seed, but for future-proofing:
            elif category_name == 'Medicine':
                MedicineModel.objects.update_or_create(product=p, defaults={'active_ingredient': attrs.get('active_ingredient', 'N/A'), 'dosage': attrs.get('dosage', 'N/A')})
                stats['Medicine'] += 1
            elif category_name == 'PetSupplies':
                PetSuppliesModel.objects.update_or_create(product=p, defaults={'animal_type': attrs.get('animal_type', 'Pet'), 'brand': attrs.get('brand', 'Unknown')})
                stats['PetSupplies'] += 1
            elif category_name == 'AutoParts':
                AutoPartsModel.objects.update_or_create(product=p, defaults={'part_number': attrs.get('part_number', 'N/A'), 'car_model_compatibility': attrs.get('car_model_compatibility', 'N/A')})
                stats['AutoParts'] += 1
            
            else:
                stats['Skipped'] += 1

            # Trigger sync to Mongo to update the documents there too
            p.save()

        except Exception as e:
            print(f"Error migrating product {p.id} ({p.name}): {e}")
            stats['Skipped'] += 1

    print("\nMigration Summary:")
    for k, v in stats.items():
        print(f" - {k}: {v}")
    print("\nDone.")

if __name__ == "__main__":
    migrate()
