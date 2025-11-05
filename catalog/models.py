from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.

#===============================
# Model Author
#===============================

class Author(models.Model):
    """
    Represents a book author.
    Example: George Orwell, J.K Rowling, etc.
    """

    #Basic Feilds
    first_name = models.CharField(
        max_length=100,
        help_text="Author's First Name."
    )
    last_name = models.CharField(
        max_length=100,
        help_text="Author's Last Name."
    )
    date_of_birth = models.DateField(
        null=True, # can be empty
        blank=True, # optionaal
        help_text="Author's Date of Birth(optiona)"
    )

    class Meta:
        # CONSTRAINT: No two authors can have same first name, last name, AND birth date
        # This prevents duplicate entries like "George Orwell, 1903-06-25" appearing twice
        unique_together = ('first_name', 'last_name', 'date_of_birth')

        #sort authors when listing them
        ordering = ['last_name', 'first_name']

    def __str__(self):
        # this is how the object will appear in django logs
        return f"{self.first_name} {self.last_name}"
#===============================
# Model TAG
#===============================

class Tag(models.Model):
    """
    Represents a tag that can be applied to a book.
    Example: Fiction, Non-Fiction, Sci-Fi, etc.
    """

    #Basic Feilds
    name = models.CharField(
        max_length=100,
        unique=True, # no two tags can have the same name
        help_text="Tag name (e.g., 'Science Fiction')"
    )
    slug = models.SlugField(
        max_length=100,
        unique=True, # must be unique for urls
        help_text="URL-friendly version (e.g., 'science-fiction')"
    )
    description = models.TextField(
        null=True, # can be empty
        blank=True, # optional
        help_text="Tag description"
    )
    class Meta:
        #sort tags alphabetically when listing them
        ordering = ['name']

    def __str__(self):
        # this is how the object will appear in django logs
        return self.name
    
#===============================
# Model 3: Book
#===============================

class Book(models.Model):
    """
    Represents a book title (not a pyshical copy).
    example: "1984" by George Orwell
    """
    title = models.CharField(
        max_length=200,
        help_text="Book title"
    )
    description = models.TextField(
        blank=True, # optional
        null=True, # can be empty
        help_text="Book description"
    )
    isbn = models.CharField(
        max_length=13,
        unique=True, # no two books can have the same isbn
        help_text="ISBN number"
    )
    published_date = models.DateField(
        null=True, # can be empty
        blank=True, # optional
        help_text="Publication date"
    )
    # Mant-to-many relationship with Author
    authors = models.ManyToManyField(
        Author,
        related_name="books", # allows: author.books.all() to get all their books
        help_text="Authors who wrote this book"
    )
    # Many-to-many relationship with Tag
    tags = models.ManyToManyField(
        Tag,
        related_name="books", # Allows: tag.books.all() to get all books with this tag
        blank=True, # optional
        help_text="ategories/genres for this book"
    )
    # JSON field: store flexible additonal data
    # Example: {"pages": 300, "publisher": "Penguin", "language": "English"}
    metadata = models.JSONField(
        null=True, # can be empty
        blank=True, # optional
        help_text="Additional metadata for this book"
    )
    #TimeStamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        #sort books alphabetically when listing them
        ordering = ['title']

    def __str__(self):
        # this is how the object will appear in django logs
        return self.title
    

#===============================
# Model 4: copy
#===============================
class Copy(models.Model):
    """
    Represents a physical copy of a book.
    Example: A book in the library's collection.
    """
    # Status choices for the copy
    AVAILABLE = 'available'
    CHECKED_OUT = 'checked_out'
    DAMAGED = 'damaged'
    LOST = 'lost'

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost'),
    ]

    # FOREIGN KEY: each copy belongs to a book
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE, # if book is deleted, delete copis too 
        related_name="copies", # allows: book.copies.all() to get all copies of a book
        help_text="Book this copy belongs to"
    )

    barcode = models.CharField(
        max_length=100,
        unique=True, # each copy must have a unique barcode
        help_text="Unique barcode for this copy"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=AVAILABLE,
        help_text="Current status of this copy"
    )
    checkout_date = models.DateField(
        null=True, # can be empty
        blank=True, # optional
        help_text="Date this copy was checked out"
    )
    due_date = models.DateField(
        null=True, # can be empty
        blank=True, # optional
        help_text="Date this copy is due back"
    )
    #timestampes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "copies"
        #sort copies by status when listing them
        ordering = ['status']

    def __str__(self):
        # this is how the object will appear in django logs
        return f"Copy {self.barcode} of {self.book.title}"
    
#===============================
# Model 5: Review
#===============================

class Review(models.Model):
    """
    Represents a review of a book.
    Example: A user's rating and comment for a book.
    """
    # FOREIGN KEY: each review belongs to a book
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE, # if book is deleted, delete reviews too 
        related_name="reviews", # allows: book.reviews.all() to get all reviews of a book
        help_text="Book this review belongs to"
    )
    # FOREIGN KEY: Review Writtne by one user
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE, # if user is deleted, delete reviews too 
        related_name="reviews", # allows: user.reviews.all() to get all reviews by a user
        help_text="User who wrote this review"
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating (1-5 stars)"
    )
    comment = models.TextField(
        blank=True, # optional
        null=True, # can be empty
        help_text="Review comment"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Contraint: eac user can only review a book once
        # prevents span: cant sumbit 100 review for same book
        unique_together = ['user', 'book']

        #INDEX: fast lookups for "show me review for this book"
        indexes = [
            models.Index(fields=['book']),
        ]
        #sort reviews by created_at when listing them
        ordering = ['-created_at']

    def __str__(self):
        # this is how the object will appear in django logs
        return f"Review of {self.book.title} by {self.user.username}" 
    
#===========================
# Model 6: LOAN
#===========================

class Loan(models.Model):
    """
    Represents a loan of a book copy to a user.
    Example: A user borrowing a book from the library.
    """
    # FOREIGN KEY: each loan belongs to a copy
    copy = models.ForeignKey(
        Copy,
        on_delete=models.CASCADE, # if copy is deleted, delete loans too 
        related_name="loans", # allows: copy.loans.all() to get all loans for a copy
        help_text="Copy this loan belongs to"
    )
    # FOREIGN KEY: each loan belongs to a user
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE, # if user is deleted, delete loans too 
        related_name="loans", # allows: user.loans.all() to get all loans for a user
        help_text="User this loan belongs to"
    )
    borrowed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date this loan was created"
    )
    due_back = models.DateField(
        help_text="Date this loan is due back"
    )
    returned_at = models.DateTimeField(
        null=True, # can be empty
        blank=True, # optional
        help_text="Date this loan was returned"
    )
    #timestampes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-borrowed_at'] # most recent loans first
        # Contraint: each copy can only be loaned out once at a time
        # prevents span: cant borrow same copy twice

        constraints = [
            models.UniqueConstraint(
                fields=['copy'], 
                condition=Q(returned_at=None), 
                name='only_one_active_loan_per_copy'
            ),
        ]
    def __str__(self):
        status = "Active" if self.returned_at is None else "Returned"
        return f"{self.user.username} - {self.copy.barcode} ({status})"
    def is_overdue(self):
        """
        Check if load is overdue
        """
        from django.utils import timezone
        if self.returned_at is None and timezone.now() > self.due_back:
            return True
        return False
