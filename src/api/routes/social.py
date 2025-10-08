"""
Social Routes
Handles friend requests, friendships, and social interactions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import get_db
from api.models.user import User, UserProfile
from api.models.social import Friendship
from api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/friend-request", response_model=dict)
def send_friend_request(
    friend_username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a friend request to another user
    """
    # Find the user to befriend
    friend = db.query(User).filter(User.username == friend_username).first()

    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{friend_username}' not found"
        )

    # Can't befriend yourself
    if friend.user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot send a friend request to yourself"
        )

    # Check if friendship already exists (in either direction)
    existing = db.query(Friendship).filter(
        (
            (Friendship.user_id == current_user.user_id) &
            (Friendship.friend_id == friend.user_id)
        ) |
        (
            (Friendship.user_id == friend.user_id) &
            (Friendship.friend_id == current_user.user_id)
        )
    ).first()

    if existing:
        if existing.status == 'accepted':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already friends with this user"
            )
        elif existing.status == 'pending':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A friend request is already pending with this user"
            )
        elif existing.status == 'blocked':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unable to send friend request"
            )

    # Create friend request
    friendship = Friendship(
        user_id=current_user.user_id,
        friend_id=friend.user_id,
        status='pending'
    )

    db.add(friendship)
    db.commit()
    db.refresh(friendship)

    logger.info(f"Friend request sent from {current_user.username} to {friend.username}")

    return {
        "message": "Friend request sent successfully",
        "friendship_id": str(friendship.friendship_id),
        "friend_username": friend.username,
        "status": "pending"
    }


@router.put("/friend-request/{friendship_id}/accept", response_model=dict)
def accept_friend_request(
    friendship_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accept a pending friend request
    """
    # Find the friendship
    friendship = db.query(Friendship).filter(
        Friendship.friendship_id == friendship_id
    ).first()

    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend request not found"
        )

    # Verify the current user is the recipient (friend_id)
    if friendship.friend_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only accept friend requests sent to you"
        )

    # Check if already accepted
    if friendship.status == 'accepted':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Friend request already accepted"
        )

    # Check if pending
    if friendship.status != 'pending':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Friend request is not pending"
        )

    # Accept the friendship
    friendship.status = 'accepted'
    friendship.updated_at = datetime.utcnow()
    db.commit()

    # Get sender info
    sender = db.query(User).filter(User.user_id == friendship.user_id).first()

    logger.info(f"Friend request accepted: {sender.username} <-> {current_user.username}")

    return {
        "message": "Friend request accepted",
        "friendship_id": str(friendship.friendship_id),
        "friend_username": sender.username,
        "status": "accepted"
    }


@router.delete("/friend/{friend_username}", response_model=dict)
def remove_friend(
    friend_username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a friend or reject a friend request
    """
    # Find the friend
    friend = db.query(User).filter(User.username == friend_username).first()

    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{friend_username}' not found"
        )

    # Find the friendship (in either direction)
    friendship = db.query(Friendship).filter(
        (
            (Friendship.user_id == current_user.user_id) &
            (Friendship.friend_id == friend.user_id)
        ) |
        (
            (Friendship.user_id == friend.user_id) &
            (Friendship.friend_id == current_user.user_id)
        )
    ).first()

    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friendship not found"
        )

    # Delete the friendship
    db.delete(friendship)
    db.commit()

    logger.info(f"Friendship removed: {current_user.username} <-> {friend.username}")

    return {
        "message": "Friend removed successfully",
        "friend_username": friend.username
    }


@router.get("/friends", response_model=List[dict])
def get_friends_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's friends list (accepted friendships)
    """
    # Get all accepted friendships where user is either sender or recipient
    friendships = db.query(Friendship).filter(
        (
            (Friendship.user_id == current_user.user_id) |
            (Friendship.friend_id == current_user.user_id)
        ),
        Friendship.status == 'accepted'
    ).all()

    friends_list = []

    for friendship in friendships:
        # Determine which user is the friend
        friend_id = friendship.friend_id if friendship.user_id == current_user.user_id else friendship.user_id

        # Get friend's user and profile info
        friend = db.query(User).filter(User.user_id == friend_id).first()
        friend_profile = db.query(UserProfile).filter(UserProfile.user_id == friend_id).first()

        if friend and friend_profile:
            friends_list.append({
                "friendship_id": str(friendship.friendship_id),
                "user_id": str(friend.user_id),
                "username": friend.username,
                "display_name": friend_profile.display_name,
                "character_type": friend_profile.character_type,
                "avatar_url": friend_profile.avatar_url,
                "current_level": friend_profile.current_level,
                "total_xp": friend_profile.total_xp,
                "friends_since": friendship.updated_at.isoformat()
            })

    return friends_list


@router.get("/friend-requests", response_model=dict)
def get_friend_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get pending friend requests (both sent and received)
    """
    # Friend requests sent by current user
    sent_requests = db.query(Friendship).filter(
        Friendship.user_id == current_user.user_id,
        Friendship.status == 'pending'
    ).all()

    # Friend requests received by current user
    received_requests = db.query(Friendship).filter(
        Friendship.friend_id == current_user.user_id,
        Friendship.status == 'pending'
    ).all()

    sent_list = []
    for req in sent_requests:
        friend = db.query(User).filter(User.user_id == req.friend_id).first()
        friend_profile = db.query(UserProfile).filter(UserProfile.user_id == req.friend_id).first()

        if friend and friend_profile:
            sent_list.append({
                "friendship_id": str(req.friendship_id),
                "username": friend.username,
                "display_name": friend_profile.display_name,
                "avatar_url": friend_profile.avatar_url,
                "sent_at": req.created_at.isoformat()
            })

    received_list = []
    for req in received_requests:
        sender = db.query(User).filter(User.user_id == req.user_id).first()
        sender_profile = db.query(UserProfile).filter(UserProfile.user_id == req.user_id).first()

        if sender and sender_profile:
            received_list.append({
                "friendship_id": str(req.friendship_id),
                "username": sender.username,
                "display_name": sender_profile.display_name,
                "avatar_url": sender_profile.avatar_url,
                "sent_at": req.created_at.isoformat()
            })

    return {
        "sent": sent_list,
        "received": received_list,
        "total_sent": len(sent_list),
        "total_received": len(received_list)
    }
