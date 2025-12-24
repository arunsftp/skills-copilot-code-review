"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime, date
from bson import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


@router.get("/active")
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all active announcements (current date is between start_date and expiration_date)"""
    today = date.today().isoformat()
    
    # Find announcements that are currently active
    announcements = announcements_collection.find({
        "$or": [
            {"start_date": {"$exists": False}},
            {"start_date": {"$lte": today}}
        ],
        "expiration_date": {"$gte": today}
    }).sort("created_at", -1)
    
    result = []
    for announcement in announcements:
        announcement["_id"] = str(announcement["_id"])
        result.append(announcement)
    
    return result


@router.get("")
def get_all_announcements(username: str = None) -> List[Dict[str, Any]]:
    """Get all announcements (requires authentication)"""
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Verify user exists
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    # Retrieve all announcements
    announcements = announcements_collection.find().sort("created_at", -1)
    
    result = []
    for announcement in announcements:
        announcement["_id"] = str(announcement["_id"])
        result.append(announcement)
    
    return result


@router.post("")
def create_announcement(
    message: str,
    expiration_date: str,
    username: str,
    start_date: str = None
) -> Dict[str, Any]:
    """Create a new announcement (requires authentication)"""
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Verify user exists
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    # Validate dates
    try:
        exp_date = datetime.fromisoformat(expiration_date).date()
        if start_date:
            st_date = datetime.fromisoformat(start_date).date()
            if st_date > exp_date:
                raise HTTPException(
                    status_code=400, 
                    detail="Start date must be before expiration date"
                )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Create announcement
    announcement = {
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "created_by": username,
        "created_at": datetime.utcnow().isoformat()
    }
    
    result = announcements_collection.insert_one(announcement)
    announcement["_id"] = str(result.inserted_id)
    
    return announcement


@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: str,
    message: str,
    expiration_date: str,
    username: str,
    start_date: str = None
) -> Dict[str, Any]:
    """Update an existing announcement (requires authentication)"""
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Verify user exists
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    # Validate dates
    try:
        exp_date = datetime.fromisoformat(expiration_date).date()
        if start_date:
            st_date = datetime.fromisoformat(start_date).date()
            if st_date > exp_date:
                raise HTTPException(
                    status_code=400, 
                    detail="Start date must be before expiration date"
                )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Update announcement
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    update_data = {
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "updated_by": username,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    result = announcements_collection.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Return updated announcement
    announcement = announcements_collection.find_one({"_id": obj_id})
    announcement["_id"] = str(announcement["_id"])
    
    return announcement


@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: str, username: str) -> Dict[str, str]:
    """Delete an announcement (requires authentication)"""
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Verify user exists
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    # Delete announcement
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    result = announcements_collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    return {"message": "Announcement deleted successfully"}
