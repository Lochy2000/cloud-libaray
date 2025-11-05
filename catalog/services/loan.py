"""
Loan Service Module

This module provides business logic for borrowing and returning book copies.
It enforces constraints like one active loan per copy and handles all database
operations within transactions to prevent race conditions.

Functions:
    - borrow_copy(copy_id, user_id, due_at): Borrow a book copy
    - return_copy(copy_id, user_id): Return a borrowed book copy
"""

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from catalog.models import Copy, Loan

# Get the User model (Django best practice for referencing users)
User = get_user_model()

# =============================================================================
# Custom Exception Classes
# =============================================================================

class LoanServiceError(Exception):
    """
    Base exception for all loan service errors.
    All other custom exceptions inherit from this.
    """
    pass


class CopyNotFoundError(LoanServiceError):
    """
    Raised when the requested book copy doesn't exist in the database.
    
    Example: borrow_copy(copy_id=999, ...) when copy 999 doesn't exist
    """
    pass


class CopyNotAvailableError(LoanServiceError):
    """
    Raised when a copy exists but its status is not 'available'.
    This could mean it's already borrowed, damaged, or lost.
    
    Example: Trying to borrow a copy with status='damaged'
    """
    pass


class AlreadyLoanedError(LoanServiceError):
    """
    Raised when attempting to borrow a copy that already has an active loan.
    An active loan is one where returned_at is NULL.
    
    Example: User A borrowed a book, User B tries to borrow the same copy
    """
    pass


class NoActiveLoanError(LoanServiceError):
    """
    Raised when trying to return a copy that has no active loan.
    
    Example: Trying to return a copy that was never borrowed or already returned
    """
    pass


class UnauthorizedReturnError(LoanServiceError):
    """
    Raised when a user tries to return a copy they didn't borrow.
    Only the user who borrowed the copy can return it.
    
    Example: User A borrowed a book, User B tries to return it
    """
    pass


class OverdueError(LoanServiceError):
    """
    Raised when a loan is overdue (past its due_back date).
    This can be used for reporting or preventing certain actions.
    
    Example: Checking if a loan is overdue before allowing new borrows
    """
    pass

# =============================================================================
# Service Functions
# =============================================================================

def borrow_copy(copy_id, user_id, due_at):
    """
    Borrow a book copy.
    This function handles all the logic for borrowing a book:
    1. Validates the copy exists and is available
    2. Checks there's no active loan already
    3. Creates a new Loan record
    4. Updates the Copy status to 'borrowed'
    
    All operations happen within a database transaction to ensure atomicity.
    Uses SELECT FOR UPDATE to prevent race conditions (two users borrowing
    the same copy at the exact same time).
    
    Args:
        copy_id (int): The ID of the book copy to borrow
        user_id (int): The ID of the user borrowing the book
        due_at (datetime): When the book is due back
        
    Returns:
        Loan: The newly created Loan object
        
    Raises:
        CopyNotFoundError: If the copy doesn't exist
        CopyNotAvailableError: If the copy status is not 'available'
        AlreadyLoanedError: If there's already an active loan for this copy
        
    Example:
        from datetime import timedelta
        from django.utils import timezone
        
        due_date = timezone.now() + timedelta(days=14)  # 2 weeks from now
        loan = borrow_copy(copy_id=1, user_id=2, due_at=due_date)
        print(f"Loan created: {loan.id}")
        """
    
    # Start a database transaction - everything inside must succeed or all will rollback
    with transaction.atomic():
        
        # Step 1: Try to get the copy with a lock (SELECT FOR UPDATE)
        # This prevents other transactions from modifying this copy until we're done
        try:
            copy = Copy.objects.select_for_update().get(id=copy_id)
        except Copy.DoesNotExist:
            raise CopyNotFoundError(f"Copy with id {copy_id} does not exist.")
        
        # Step 2: Check if the copy is available for borrowing
        if copy.status != 'available':
            raise CopyNotAvailableError(
                f"Copy {copy_id} is not available. Current status: {copy.status}"
            )
        
        # Step 3: Check if there's already an active loan for this copy
        # Active loan = returned_at is NULL (hasn't been returned yet)
        active_loan = Loan.objects.filter(
            copy=copy,
            returned_at__isnull=True
        ).first()
        
        if active_loan:
            raise AlreadyLoanedError(
                f"Copy {copy_id} is already loaned to user {active_loan.user.id}"
            )
        
        # Step 4: Get the user object
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise LoanServiceError(f"User with id {user_id} does not exist.")
        
        # Step 5: Create the new loan record
        loan = Loan.objects.create(
            copy=copy,
            user=user,
            borrowed_at=timezone.now(),  # Current timestamp
            due_back=due_at
            # returned_at is NULL by default (not returned yet)
        )
        
        # Step 6: Update the copy's status and tracking fields
        copy.status = 'borrowed'
        copy.checkout_date = timezone.now()
        copy.due_date = due_at
        copy.save()
        
        # Return the created loan
        # The transaction will commit here automatically if no errors occurred
        return loan
    
def return_copy(copy_id, user_id):
    """
    Return a borrowed book copy.
    
    This function handles all the logic for returning a book:
    1. Finds the active loan for the copy
    2. Validates the user is the one who borrowed it
    3. Sets the returned_at timestamp
    4. Updates the Copy status back to 'available'
    
    All operations happen within a database transaction to ensure atomicity.
    
    Args:
        copy_id (int): The ID of the book copy being returned
        user_id (int): The ID of the user returning the book
        
    Returns:
        Loan: The updated Loan object with returned_at set
        
    Raises:
        CopyNotFoundError: If the copy doesn't exist
        NoActiveLoanError: If there's no active loan for this copy
        UnauthorizedReturnError: If the user didn't borrow this copy
        
    Example:
        loan = return_copy(copy_id=1, user_id=2)
        print(f"Book returned at: {loan.returned_at}")
        print(f"Was overdue: {loan.is_overdue()}")
    """
    
    # Start a database transaction
    with transaction.atomic():
        
        # Step 1: Try to get the copy
        try:
            copy = Copy.objects.select_for_update().get(id=copy_id)
        except Copy.DoesNotExist:
            raise CopyNotFoundError(f"Copy with id {copy_id} does not exist.")
        
        # Step 2: Find the active loan for this copy
        # Active loan = returned_at is NULL
        try:
            active_loan = Loan.objects.select_for_update().get(
                copy=copy,
                returned_at__isnull=True
            )
        except Loan.DoesNotExist:
            raise NoActiveLoanError(
                f"No active loan found for copy {copy_id}. "
                "It may have already been returned or never borrowed."
            )
        
        # Step 3: Verify the user returning the book is the one who borrowed it
        if active_loan.user.id != user_id:
            raise UnauthorizedReturnError(
                f"User {user_id} cannot return copy {copy_id}. "
                f"It was borrowed by user {active_loan.user.id}."
            )
        
        # Step 4: Mark the loan as returned
        active_loan.returned_at = timezone.now()
        active_loan.save()
        
        # Step 5: Update the copy's status back to available
        copy.status = 'available'
        copy.checkout_date = None
        copy.due_date = None
        copy.save()
        
        # Return the updated loan
        # The transaction will commit here automatically if no errors occurred
        return active_loan