from ..models.product_model import ProductModel
from ...domain.entities.product import ProductEntity

class ProductRepositoryImpl:
    def get_all(self):
        return ProductModel.objects.all()

    def get_by_id(self, product_id: int):
        try:
            model = ProductModel.objects.get(pk=product_id)
            return self._to_entity(model)
        except ProductModel.DoesNotExist:
            return None

    def save(self, entity: ProductEntity):
        model, created = ProductModel.objects.update_or_create(
            id=entity.id,
            defaults={
                'name': entity.name,
                'description': entity.description,
                'price': entity.price,
                'stock': entity.stock,
                'image_url': entity.image_url,
                'category_id': entity.category_id,
                'attributes': entity.attributes
            }
        )
        
        # Handle Domain Specific Data
        if entity.product_type == 'Book' and entity.domain_data:
            from ..models.book_model import BookModel
            BookModel.objects.update_or_create(
                product=model,
                defaults={
                    'author': entity.domain_data.get('author'),
                    'publisher': entity.domain_data.get('publisher'),
                    'isbn': entity.domain_data.get('isbn')
                }
            )
        elif entity.product_type == 'Electronics' and entity.domain_data:
            from ..models.electronics_model import ElectronicsModel
            ElectronicsModel.objects.update_or_create(
                product=model,
                defaults={
                    'brand': entity.domain_data.get('brand'),
                    'warranty': entity.domain_data.get('warranty')
                }
            )
        elif entity.product_type == 'Fashion' and entity.domain_data:
            from ..models.fashion_model import FashionModel
            FashionModel.objects.update_or_create(
                product=model,
                defaults={
                    'size': entity.domain_data.get('size'),
                    'color': entity.domain_data.get('color')
                }
            )
        elif entity.product_type == 'Cosmetics' and entity.domain_data:
            from ..models.cosmetics_model import CosmeticsModel
            CosmeticsModel.objects.update_or_create(
                product=model,
                defaults={
                    'brand': entity.domain_data.get('brand'),
                    'skin_type': entity.domain_data.get('skin_type'),
                    'is_organic': entity.domain_data.get('is_organic', False),
                    'expiration_date': entity.domain_data.get('expiration_date')
                }
            )
        elif entity.product_type == 'Toys' and entity.domain_data:
            from ..models.toys_model import ToysModel
            ToysModel.objects.update_or_create(
                product=model,
                defaults={
                    'age_group': entity.domain_data.get('age_group'),
                    'material': entity.domain_data.get('material'),
                    'requires_batteries': entity.domain_data.get('requires_batteries', False)
                }
            )
        elif entity.product_type == 'Furniture' and entity.domain_data:
            from ..models.furniture_model import FurnitureModel
            FurnitureModel.objects.update_or_create(
                product=model,
                defaults={
                    'material': entity.domain_data.get('material'),
                    'dimensions': entity.domain_data.get('dimensions'),
                    'weight_capacity': entity.domain_data.get('weight_capacity')
                }
            )
        elif entity.product_type == 'Food' and entity.domain_data:
            from ..models.food_model import FoodModel
            FoodModel.objects.update_or_create(
                product=model,
                defaults={
                    'expiration_date': entity.domain_data.get('expiration_date'),
                    'weight': entity.domain_data.get('weight'),
                    'is_vegetarian': entity.domain_data.get('is_vegetarian', False),
                    'calories': entity.domain_data.get('calories')
                }
            )
        elif entity.product_type == 'Medicine' and entity.domain_data:
            from ..models.medicine_model import MedicineModel
            MedicineModel.objects.update_or_create(
                product=model,
                defaults={
                    'active_ingredient': entity.domain_data.get('active_ingredient'),
                    'dosage': entity.domain_data.get('dosage'),
                    'prescription_required': entity.domain_data.get('prescription_required', False)
                }
            )
        elif entity.product_type == 'PetSupplies' and entity.domain_data:
            from ..models.pet_supplies_model import PetSuppliesModel
            PetSuppliesModel.objects.update_or_create(
                product=model,
                defaults={
                    'animal_type': entity.domain_data.get('animal_type'),
                    'brand': entity.domain_data.get('brand'),
                    'weight_limit': entity.domain_data.get('weight_limit')
                }
            )
        elif entity.product_type == 'AutoParts' and entity.domain_data:
            from ..models.auto_parts_model import AutoPartsModel
            AutoPartsModel.objects.update_or_create(
                product=model,
                defaults={
                    'part_number': entity.domain_data.get('part_number'),
                    'car_model_compatibility': entity.domain_data.get('car_model_compatibility'),
                    'warranty_years': entity.domain_data.get('warranty_years', 1)
                }
            )

        return self._to_entity(model)

    def delete(self, product_id: int):
        ProductModel.objects.filter(pk=product_id).delete()

    def _to_entity(self, model: ProductModel) -> ProductEntity:
        domain_data = {}
        product_type = "General"

        if hasattr(model, 'book_details'):
            product_type = "Book"
            domain_data = {
                'author': model.book_details.author,
                'publisher': model.book_details.publisher,
                'isbn': model.book_details.isbn
            }
        elif hasattr(model, 'electronics_details'):
            product_type = "Electronics"
            domain_data = {
                'brand': model.electronics_details.brand,
                'warranty': model.electronics_details.warranty
            }
        elif hasattr(model, 'fashion_details'):
            product_type = "Fashion"
            domain_data = {
                'size': model.fashion_details.size,
                'color': model.fashion_details.color
            }
        elif hasattr(model, 'cosmetics_details'):
            product_type = "Cosmetics"
            domain_data = {
                'brand': model.cosmetics_details.brand,
                'skin_type': model.cosmetics_details.skin_type,
                'is_organic': model.cosmetics_details.is_organic,
                'expiration_date': str(model.cosmetics_details.expiration_date) if model.cosmetics_details.expiration_date else None
            }
        elif hasattr(model, 'toys_details'):
            product_type = "Toys"
            domain_data = {
                'age_group': model.toys_details.age_group,
                'material': model.toys_details.material,
                'requires_batteries': model.toys_details.requires_batteries
            }
        elif hasattr(model, 'furniture_details'):
            product_type = "Furniture"
            domain_data = {
                'material': model.furniture_details.material,
                'dimensions': model.furniture_details.dimensions,
                'weight_capacity': model.furniture_details.weight_capacity
            }
        elif hasattr(model, 'food_details'):
            product_type = "Food"
            domain_data = {
                'expiration_date': str(model.food_details.expiration_date),
                'weight': model.food_details.weight,
                'is_vegetarian': model.food_details.is_vegetarian,
                'calories': model.food_details.calories
            }
        elif hasattr(model, 'medicine_details'):
            product_type = "Medicine"
            domain_data = {
                'active_ingredient': model.medicine_details.active_ingredient,
                'dosage': model.medicine_details.dosage,
                'prescription_required': model.medicine_details.prescription_required
            }
        elif hasattr(model, 'pet_supplies_details'):
            product_type = "PetSupplies"
            domain_data = {
                'animal_type': model.pet_supplies_details.animal_type,
                'brand': model.pet_supplies_details.brand,
                'weight_limit': model.pet_supplies_details.weight_limit
            }
        elif hasattr(model, 'auto_parts_details'):
            product_type = "AutoParts"
            domain_data = {
                'part_number': model.auto_parts_details.part_number,
                'car_model_compatibility': model.auto_parts_details.car_model_compatibility,
                'warranty_years': model.auto_parts_details.warranty_years
            }

        return ProductEntity(
            id=model.id,
            name=model.name,
            description=model.description,
            price=float(model.price),
            stock=model.stock,
            image_url=model.image_url,
            category_id=model.category_id,
            attributes=model.attributes,
            product_type=product_type,
            domain_data=domain_data
        )
