from decimal import Decimal

from app.core.database import Base, SessionLocal, engine
from app.models import Category, Product


SEED_DATA = {
    "Mobile Devices": [
        {
            "name": "Aster One",
            "description": "A compact everyday smartphone with a bright display and dependable battery life.",
            "price": Decimal("24999.00"),
            "stock_quantity": 24,
            "brand": "Aster",
            "model_number": "AST-ONE-128",
        },
        {
            "name": "Northline Pro",
            "description": "A performance-focused phone designed for photography, work, and long days.",
            "price": Decimal("48999.00"),
            "stock_quantity": 12,
            "brand": "Northline",
            "model_number": "NLP-15-PRO",
        },
    ],
    "Home Electronics": [
        {
            "name": "Arc Soundbar",
            "description": "A slim living-room soundbar with clear dialogue and room-filling audio.",
            "price": Decimal("12999.00"),
            "stock_quantity": 18,
            "brand": "Arc",
            "model_number": "ARC-SB-200",
        },
        {
            "name": "Lumen Air Purifier",
            "description": "A quiet air purifier for bedrooms and small workspaces.",
            "price": Decimal("8999.00"),
            "stock_quantity": 15,
            "brand": "Lumen",
            "model_number": "LUM-AIR-01",
        },
    ],
    "Computing": [
        {
            "name": "Fieldbook 14",
            "description": "A lightweight laptop for focused work, study, and everyday creative tasks.",
            "price": Decimal("64999.00"),
            "stock_quantity": 9,
            "brand": "Fieldbook",
            "model_number": "FB-14-I5",
        },
        {
            "name": "Grid Dock Mini",
            "description": "A compact USB-C dock for a cleaner desk and more connected workspace.",
            "price": Decimal("6999.00"),
            "stock_quantity": 30,
            "brand": "Grid",
            "model_number": "GRID-DOCK-M1",
        },
    ],
}


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for category_name, products in SEED_DATA.items():
            category = db.query(Category).filter(Category.name == category_name).first()
            if not category:
                category = Category(name=category_name, description=f"{category_name} products")
                db.add(category)
                db.flush()
            for product_data in products:
                existing = db.query(Product).filter(Product.model_number == product_data["model_number"]).first()
                if not existing:
                    db.add(Product(category_id=category.id, **product_data))
        db.commit()
        print("Sample categories and products seeded successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
