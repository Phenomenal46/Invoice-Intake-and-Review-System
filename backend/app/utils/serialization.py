from bson import ObjectId


def serialize_document(doc: dict) -> dict:
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


def parse_object_id(raw_id: str) -> ObjectId:
    return ObjectId(raw_id)
