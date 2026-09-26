"""
AegisFlow - Workspace & RBAC Service
"""
from datetime import datetime
from bson import ObjectId
from backend.database import workspaces_col, users_col
from backend.models.schemas import WorkspaceRole

def create_workspace(name: str, description: str, owner_id: str) -> dict:
    workspace = {
        "name": name,
        "description": description,
        "owner_id": owner_id,
        "members": [{"user_id": owner_id, "role": WorkspaceRole.ADMIN.value}],
        "created_at": datetime.utcnow()
    }
    result = workspaces_col().insert_one(workspace)
    workspace["_id"] = str(result.inserted_id)
    return workspace

def get_workspaces_for_user(user_id: str) -> list:
    query = {"members.user_id": user_id}
    workspaces = list(workspaces_col().find(query).sort("created_at", -1))
    for w in workspaces:
        w["_id"] = str(w["_id"])
    return workspaces

def get_workspace_by_id(workspace_id: str) -> dict:
    workspace = workspaces_col().find_one({"_id": ObjectId(workspace_id)})
    if workspace:
        workspace["_id"] = str(workspace["_id"])
    return workspace

def add_member_to_workspace(workspace_id: str, username: str, role: str, requester_id: str):
    # Verify requester is admin
    workspace = workspaces_col().find_one({"_id": ObjectId(workspace_id)})
    if not workspace:
        raise ValueError("Workspace not found")
        
    is_admin = any(m["user_id"] == requester_id and m["role"] == WorkspaceRole.ADMIN.value for m in workspace.get("members", []))
    if not is_admin:
        raise ValueError("Only Admins can add members")
        
    user = users_col().find_one({"username": username})
    if not user:
        raise ValueError("User not found")
        
    target_id = str(user["_id"])
    
    # Check if already a member
    if any(m["user_id"] == target_id for m in workspace.get("members", [])):
        raise ValueError("User is already a member of this workspace")
        
    workspaces_col().update_one(
        {"_id": ObjectId(workspace_id)},
        {"$push": {"members": {"user_id": target_id, "role": role}}}
    )
    return True

def remove_member_from_workspace(workspace_id: str, target_user_id: str, requester_id: str):
    workspace = workspaces_col().find_one({"_id": ObjectId(workspace_id)})
    if not workspace:
        raise ValueError("Workspace not found")
        
    is_admin = any(m["user_id"] == requester_id and m["role"] == WorkspaceRole.ADMIN.value for m in workspace.get("members", []))
    if not is_admin:
        raise ValueError("Only Admins can remove members")
        
    if target_user_id == workspace["owner_id"]:
        raise ValueError("Cannot remove the workspace owner")
        
    workspaces_col().update_one(
        {"_id": ObjectId(workspace_id)},
        {"$pull": {"members": {"user_id": target_user_id}}}
    )
    return True

def update_member_role(workspace_id: str, target_user_id: str, new_role: str, requester_id: str):
    workspace = workspaces_col().find_one({"_id": ObjectId(workspace_id)})
    if not workspace:
        raise ValueError("Workspace not found")
        
    is_admin = any(m["user_id"] == requester_id and m["role"] == WorkspaceRole.ADMIN.value for m in workspace.get("members", []))
    if not is_admin:
        raise ValueError("Only Admins can change roles")
        
    if target_user_id == workspace["owner_id"]:
        raise ValueError("Cannot change the role of the workspace owner")
        
    workspaces_col().update_one(
        {"_id": ObjectId(workspace_id), "members.user_id": target_user_id},
        {"$set": {"members.$.role": new_role}}
    )
    return True

def get_workspace_members(workspace_id: str):
    workspace = workspaces_col().find_one({"_id": ObjectId(workspace_id)})
    if not workspace:
        return []
    
    member_ids = [ObjectId(m["user_id"]) for m in workspace.get("members", [])]
    users = list(users_col().find({"_id": {"$in": member_ids}}, {"password": 0}))
    
    # Merge roles
    for user in users:
        user["_id"] = str(user["_id"])
        for m in workspace["members"]:
            if m["user_id"] == user["_id"]:
                user["role"] = m["role"]
                break
                
    return users
