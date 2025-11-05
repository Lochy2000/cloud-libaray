from django.contrib import admin
from .models import Author, Tag, Book, Copy, Review, Loan

# Register your models here.

# ============================================================
# BASIC REGISTRATION (Simple Approach)
# ============================================================
# This is the simplest way - just register the model
# Django will create a basic admin interface automatically

# admin.site.register(Author)
# admin.site.register(Tag)
# admin.site.register(Book)
# admin.site.register(Copy)
# admin.site.register(Review)
# admin.site.register(Loan)

# ============================================================
# ENHANCED REGISTRATION (Better UI)
# ============================================================

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Customize how Author appears in admin."""
    
    # Which fields to show in the list view
    list_display = ['last_name', 'first_name', 'date_of_birth']
    
    # Which fields can be searched
    search_fields = ['first_name', 'last_name']
    
    # Add filters in the sidebar
    list_filter = ['date_of_birth']
    
    # Sort by last name
    ordering = ['last_name', 'first_name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Customize how Tag appears in admin."""
    
    list_display = ['name', 'slug']
    search_fields = ['name']
    
    # Auto-generate slug from name (convenient!)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Customize how Book appears in admin."""
    
    list_display = ['title', 'isbn', 'published_date', 'created_at']
    search_fields = ['title', 'isbn', 'description']
    list_filter = ['published_date', 'tags', 'authors']
    
    # Show authors and tags as filter widgets
    filter_horizontal = ['authors', 'tags']
    
    # Make these fields read-only (auto-generated)
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Copy)
class CopyAdmin(admin.ModelAdmin):
    """Customize how Copy appears in admin."""
    
    list_display = ['barcode', 'book', 'status', 'created_at']
    search_fields = ['barcode', 'book__title']  # Can search by book title!
    list_filter = ['status', 'created_at']
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Customize how Review appears in admin."""
    
    list_display = ['book', 'user', 'rating', 'created_at']
    search_fields = ['book__title', 'user__username', 'comment']
    list_filter = ['rating', 'created_at']
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Customize how Loan appears in admin."""
    
    list_display = ['user', 'copy', 'borrowed_at', 'due_back', 'returned_at', 'loan_status']
    search_fields = ['user__username', 'copy__barcode', 'copy__book__title']
    list_filter = ['borrowed_at', 'due_back', 'returned_at']
    
    readonly_fields = ['borrowed_at', 'created_at', 'updated_at']
    
    # Custom method to show if loan is active or returned
    def loan_status(self, obj):
        return "Active" if obj.returned_at is None else "Returned"
    loan_status.short_description = 'Status'