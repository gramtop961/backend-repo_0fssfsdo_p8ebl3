import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, CartItem

app = FastAPI(title="ANOMIE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductCreate(Product):
    pass


class ProductOut(Product):
    id: str


class CartItemCreate(CartItem):
    pass


class CartItemOut(CartItem):
    id: str
    product: Optional[ProductOut] = None


@app.get("/")
def read_root():
    return {"brand": "ANOMIE", "sub": "STANDARD DEVIATION"}


@app.get("/schema")
def get_schema_info():
    return {"schemas": ["user", "product", "cartitem"]}


@app.post("/products", response_model=dict)
def create_product(product: ProductCreate):
    try:
        inserted_id = create_document("product", product)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products", response_model=List[ProductOut])
def list_products(limit: int = 50, category: Optional[str] = None):
    try:
        query = {"category": category} if category else {}
        docs = get_documents("product", query, limit)
        out: List[ProductOut] = []
        for d in docs:
            d["id"] = str(d.get("_id"))
            d.pop("_id", None)
            out.append(ProductOut(**d))
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cart/items", response_model=dict)
def add_to_cart(item: CartItemCreate):
    try:
        inserted_id = create_document("cartitem", item)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cart/items", response_model=List[CartItemOut])
def get_cart_items(cart_id: str):
    try:
        docs = get_documents("cartitem", {"cart_id": cart_id}, None)
        # Hydrate with product info
        product_ids = [ObjectId(d["product_id"]) for d in docs if d.get("product_id")]
        product_map = {}
        if product_ids:
            prod_docs = list(db["product"].find({"_id": {"$in": product_ids}}))
            for p in prod_docs:
                p_out = ProductOut(
                    id=str(p["_id"]),
                    title=p.get("title"),
                    description=p.get("description"),
                    price=p.get("price"),
                    category=p.get("category"),
                    image=p.get("image"),
                    in_stock=p.get("in_stock", True),
                    sizes=p.get("sizes"),
                )
                product_map[str(p["_id"])] = p_out
        out: List[CartItemOut] = []
        for d in docs:
            cid = str(d.get("_id"))
            d["id"] = cid
            pid = d.get("product_id")
            d.pop("_id", None)
            product = product_map.get(pid) if pid else None
            out.append(CartItemOut(**d, product=product))
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/seed")
def seed_products():
    """Seed a men's-focused catalog for ANOMIE — STANDARD DEVIATION."""
    try:
        samples = [
            # Outerwear
            {
                "title": "Cropped Technical Bomber",
                "description": "Matte nylon shell, cropped length, two-way zip, tonal hardware.",
                "price": 480.0,
                "category": "outerwear",
                "image": "https://images.unsplash.com/photo-1544025162-d76694265947?q=80&w=1600&auto=format&fit=crop",
                "in_stock": True,
                "sizes": ["S", "M", "L"],
            },
            {
                "title": "Wool Overcoat",
                "description": "Double-faced wool, clean lapel, hidden placket, charcoal.",
                "price": 780.0,
                "category": "outerwear",
                "image": "https://images.unsplash.com/photo-1516822003754-cca485356ecb?q=80&w=1600&auto=format&fit=crop",
                "in_stock": True,
                "sizes": ["M", "L", "XL"],
            },
            # Tops
            {
                "title": "Heavyweight Boxy Tee",
                "description": "26oz cotton, dropped shoulder, bone.",
                "price": 95.0,
                "category": "tops",
                "image": "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?q=80&w=1600&auto=format&fit=crop",
                "in_stock": True,
                "sizes": ["S", "M", "L", "XL"],
            },
            {
                "title": "Knit Polo",
                "description": "Mercerized knit, open collar, ink.",
                "price": 140.0,
                "category": "tops",
                "image": "https://images.unsplash.com/photo-1520975940163-5a6f8f125e8b?q=80&w=1600&auto=format&fit=crop",
                "in_stock": True,
                "sizes": ["S", "M", "L"],
            },
            # Bottoms
            {
                "title": "Pleated Wide Trousers",
                "description": "Single pleat, fluid drape, crease-resistant, black.",
                "price": 260.0,
                "category": "bottoms",
                "image": "https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb?q=80&w=1600&auto=format&fit=crop",
                "in_stock": True,
                "sizes": ["28", "30", "32", "34"],
            },
            {
                "title": "Raw Denim",
                "description": "14oz selvedge, straight leg, indigo.",
                "price": 220.0,
                "category": "bottoms",
                "image": "https://images.unsplash.com/photo-1503342394122-6b8499a3a540?q=80&w=1600&auto=format&fit=crop",
                "in_stock": True,
                "sizes": ["28", "30", "32", "34", "36"],
            },
            # Footwear
            {
                "title": "Leather Derby",
                "description": "Full-grain calfskin, stacked heel, black.",
                "price": 420.0,
                "category": "footwear",
                "image": "https://images.unsplash.com/photo-1519741497674-611481863552?q=80&w=1600&auto=format&fit=crop",
                "in_stock": True,
                "sizes": ["40", "41", "42", "43", "44"],
            },
            {
                "title": "Tech Runner",
                "description": "Ripstop and suede, Vibram sole, grey.",
                "price": 360.0,
                "category": "footwear",
                "image": "https://images.unsplash.com/photo-1539185441755-769473a23570?q=80&w=1600&auto=format&fit=crop",
                "in_stock": True,
                "sizes": ["40", "41", "42", "43"],
            },
            # Accessories
            {
                "title": "Calfskin Belt",
                "description": "Polished edge, matte buckle, black.",
                "price": 160.0,
                "category": "accessories",
                "image": "https://images.unsplash.com/photo-1520975661595-6453be3f7070?q=80&w=1600&auto=format&fit=crop",
                "in_stock": True,
                "sizes": None,
            },
            {
                "title": "Ribbed Beanie",
                "description": "Italian wool, onyx.",
                "price": 80.0,
                "category": "accessories",
                "image": "https://images.unsplash.com/photo-1520975588854-6cdb91f1a6cf?q=80&w=1600&auto=format&fit=crop",
                "in_stock": True,
                "sizes": None,
            },
        ]
        inserted = []
        for s in samples:
            inserted.append(create_document("product", s))
        return {"inserted": inserted, "count": len(inserted)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
