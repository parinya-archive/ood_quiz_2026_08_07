This file is a merged representation of the entire codebase, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
````
.agents/
  skills/
    django-expert/
      references/
        drf-guidelines.md
        examples.md
        models-and-orm.md
        performance-optimization.md
        production-deployment.md
        README.md
        security-checklist.md
        testing-strategies.md
        views-and-urls.md
      SKILL.md
    django-patterns/
      SKILL.md
    django-security/
      SKILL.md
    python-executor/
      SKILL.md
    python-testing-patterns/
      references/
        advanced-patterns.md
      SKILL.md
.codegraph/
  .gitignore
config/
  __init__.py
  asgi.py
  settings.py
  urls.py
  wsgi.py
core/
  migrations/
    __init__.py
    0001_initial.py
  __init__.py
  admin.py
  api.py
  apps.py
  models.py
  schemas.py
  tests.py
  views.py
src/
  ood/
    __init__.py
.python-version
manage.py
pyproject.toml
README.md
seed.py
skills-lock.json
todo.md
````

# Files

## File: .agents/skills/django-expert/references/drf-guidelines.md
````markdown
# Django REST Framework Best Practices

## Serializers

### ModelSerializer Basics

```python
from rest_framework import serializers
from .models import Post, Comment

# ✅ GOOD: Basic ModelSerializer
class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'created_at']
        read_only_fields = ['id', 'created_at', 'author']

# ✅ GOOD: Exclude sensitive fields
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        # NOT password, last_login, etc.

# ❌ BAD: Using __all__ exposes everything
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'  # Exposes password hash!
```

**Rule**: Explicitly list fields. Never use `fields = '__all__'` in production.

### Nested Serializers

```python
# ✅ GOOD: Nested read-only serializer
class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'created_at']

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'comments', 'created_at']

# ✅ GOOD: Different serializers for read/write
class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view."""
    author_name = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'author_name', 'created_at']

class PostDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with nested data."""
    author = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'comments', 'created_at', 'updated_at']
```

### Custom Fields and Validation

```python
# ✅ GOOD: Add computed fields
class PostSerializer(serializers.ModelSerializer):
    comment_count = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'comment_count', 'is_author']

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_is_author(self, obj):
        request = self.context.get('request')
        return request.user == obj.author if request else False

# ✅ GOOD: Field-level validation
class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'content']

    def validate_title(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters")
        return value

# ✅ GOOD: Object-level validation
class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'content', 'is_published']

    def validate(self, data):
        if data.get('is_published') and not data.get('content'):
            raise serializers.ValidationError(
                "Cannot publish post without content"
            )
        return data
```

### Write-Only and Read-Only Fields

```python
# ✅ GOOD: Password handling
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

# ✅ GOOD: Read-only computed field
class PostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name='post-detail', read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author_name', 'url']
```

## ViewSets

### ModelViewSet

```python
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

# ✅ GOOD: Complete CRUD ViewSet
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'is_published']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use different serializers for list vs detail."""
        if self.action == 'list':
            return PostListSerializer
        return PostDetailSerializer

    def get_queryset(self):
        """Optimize queries based on action."""
        queryset = super().get_queryset()

        if self.action == 'list':
            return queryset.select_related('author').only(
                'id', 'title', 'created_at', 'author__username'
            )
        elif self.action == 'retrieve':
            return queryset.select_related('author').prefetch_related('comments')

        return queryset

    def perform_create(self, serializer):
        """Set author automatically."""
        serializer.save(author=self.request.user)

    # ✅ GOOD: Custom action
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        post = self.get_object()
        if post.author != request.user:
            return Response({'error': 'Not authorized'}, status=403)

        post.is_published = True
        post.save()
        return Response({'status': 'published'})

    @action(detail=False, methods=['get'])
    def my_posts(self, request):
        """Get posts by current user."""
        posts = self.get_queryset().filter(author=request.user)
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
```

### ReadOnlyModelViewSet

```python
# ✅ GOOD: Read-only API
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Only allow GET requests (list and retrieve)."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
```

### APIView for Custom Logic

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# ✅ GOOD: Custom API endpoint
class PostStatisticsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        stats = {
            'total_posts': Post.objects.filter(author=user).count(),
            'published_posts': Post.objects.filter(author=user, is_published=True).count(),
            'total_comments': Comment.objects.filter(post__author=user).count(),
        }
        return Response(stats)
```

## Permissions

### Built-in Permissions

```python
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny,
    IsAdminUser,
)

# ✅ GOOD: Require authentication for all actions
class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    ...

# ✅ GOOD: Read-only for anonymous, write for authenticated
class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    ...
```

### Custom Permissions

```python
from rest_framework import permissions

# ✅ GOOD: Object-level permission
class IsAuthorOrReadOnly(permissions.BasePermission):
    """Only author can edit/delete."""

    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for author
        return obj.author == request.user

# ✅ GOOD: Staff or owner permission
class IsStaffOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.author == request.user

# Usage
class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]
    ...
```

### Per-Action Permissions

```python
# ✅ GOOD: Different permissions per action
class PostViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        else:  # update, partial_update, destroy
            return [IsAuthenticated(), IsAuthorOrReadOnly()]
```

## Authentication

### Token Authentication

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# views.py
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
    return Response({'error': 'Invalid credentials'}, status=400)
```

## Pagination

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Custom pagination
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class PostViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination
    ...
```

## Filtering, Searching, Ordering

```bash
pip install django-filter
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    'django_filters',
]

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

# ✅ GOOD: Complete filtering setup
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Exact match filtering
    filterset_fields = ['author', 'category', 'is_published']

    # Full-text search
    search_fields = ['title', 'content', 'author__username']

    # Ordering
    ordering_fields = ['created_at', 'title', 'view_count']
    ordering = ['-created_at']  # Default ordering

# Usage:
# GET /api/posts/?author=1&is_published=true
# GET /api/posts/?search=django
# GET /api/posts/?ordering=-created_at
# GET /api/posts/?author=1&search=tutorial&ordering=title
```

### Advanced Filtering

```python
from django_filters import rest_framework as filters

# ✅ GOOD: Custom FilterSet
class PostFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr='icontains')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    min_views = filters.NumberFilter(field_name='view_count', lookup_expr='gte')

    class Meta:
        model = Post
        fields = ['author', 'category', 'is_published']

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filterset_class = PostFilter
```

## Throttling (Rate Limiting)

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
}

# Custom throttle
from rest_framework.throttling import UserRateThrottle

class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'

class SustainedRateThrottle(UserRateThrottle):
    scope = 'sustained'

# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'burst': '10/min',
        'sustained': '100/hour',
    },
}

# views.py
class PostViewSet(viewsets.ModelViewSet):
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
    ...
```

## Versioning

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
}

# urls.py
urlpatterns = [
    path('api/v1/', include('api.urls', namespace='v1')),
    path('api/v2/', include('api.urls', namespace='v2')),
]

# views.py
class PostViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        if self.request.version == 'v2':
            return PostSerializerV2
        return PostSerializer
```

## Error Handling

```python
from rest_framework.views import exception_handler
from rest_framework.response import Response

# ✅ GOOD: Custom exception handler
def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # Customize error response format
        response.data = {
            'error': response.data,
            'status_code': response.status_code,
        }

    return response

# settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'myapp.exceptions.custom_exception_handler',
}

# Raise custom exceptions
from rest_framework.exceptions import ValidationError, PermissionDenied

def my_view(request):
    if not condition:
        raise ValidationError('Invalid data provided')

    if not has_permission:
        raise PermissionDenied('You do not have permission')
```

## Testing DRF APIs

```python
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

# ✅ GOOD: API test case
class PostAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()

    def test_list_posts(self):
        """Test retrieving post list."""
        Post.objects.create(title='Test Post', author=self.user)

        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_post_authenticated(self):
        """Test creating post when authenticated."""
        self.client.force_authenticate(user=self.user)

        data = {'title': 'New Post', 'content': 'Test content'}
        response = self.client.post('/api/posts/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.first().author, self.user)

    def test_create_post_unauthenticated(self):
        """Test creating post when not authenticated."""
        data = {'title': 'New Post', 'content': 'Test content'}
        response = self.client.post('/api/posts/', data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_own_post(self):
        """Test updating own post."""
        post = Post.objects.create(title='Original', author=self.user)
        self.client.force_authenticate(user=self.user)

        data = {'title': 'Updated'}
        response = self.client.patch(f'/api/posts/{post.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.title, 'Updated')

    def test_delete_others_post(self):
        """Test cannot delete another user's post."""
        other_user = User.objects.create_user(username='other', password='pass')
        post = Post.objects.create(title='Post', author=other_user)
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(f'/api/posts/{post.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
```

## DRF Best Practices Checklist

✅ Explicitly define serializer fields (never use `__all__`)
✅ Use read_only_fields for computed or auto-generated fields
✅ Create separate serializers for list/detail views
✅ Use `select_related()` and `prefetch_related()` in ViewSet querysets
✅ Implement proper permissions (object-level when needed)
✅ Add authentication to all non-public endpoints
✅ Implement pagination for list endpoints
✅ Add filtering, searching, and ordering where appropriate
✅ Use throttling to prevent API abuse
✅ Version your API from the start
✅ Write comprehensive API tests
✅ Document your API (use drf-spectacular or similar)
✅ Validate all input data in serializers
✅ Return appropriate HTTP status codes

---

**Remember**: DRF gives you powerful tools, but you must configure them properly. Security and performance are not automatic - you must implement them deliberately.
````

## File: .agents/skills/django-expert/references/examples.md
````markdown
# Django Expert - Examples

Practical examples demonstrating Django best practices for common development scenarios.

## Example 1: Model Design with Custom Manager

**User Request:**
> "Create a User model with email authentication, profile tracking, and a way to query active users"

**Claude Response:**
```
I'll create a custom User model following Django best practices:

1. Extend AbstractUser for email-based authentication
2. Add custom manager for common queries
3. Include proper Meta configuration with indexes
4. Add timestamp tracking fields
```

**Implementation:**
```python
# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class UserManager(models.Manager):
    """Custom manager for User model with common query methods."""

    def active_users(self):
        """Return users who are active and email verified."""
        return self.filter(is_active=True, email_verified=True)

    def get_by_email(self, email):
        """Case-insensitive email lookup."""
        return self.get(email__iexact=email)

class User(AbstractUser):
    email = models.EmailField(unique=True, db_index=True)
    email_verified = models.BooleanField(default=False)
    profile_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return user's full name or email if name not set."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email
```

**Next steps:**
- Run `python manage.py makemigrations` to create migrations
- Update settings.py: `AUTH_USER_MODEL = 'yourapp.User'`
- Create email verification workflow if needed

---

## Example 2: Query Optimization (N+1 Problem)

**User Request:**
> "This blog post list view is generating 100+ database queries and it's really slow"

**Current Code (Problematic):**
```python
# BAD: N+1 query problem
def post_list(request):
    posts = Post.objects.all()  # 1 query
    return render(request, 'posts/list.html', {'posts': posts})

# Template causes N+1:
# {% for post in posts %}
#   {{ post.author.name }}      # 1 query per post
#   {{ post.comments.count }}   # 1 query per post
# {% endfor %}
```

**Claude Response:**
```
I can see the N+1 query problem. The view fetches posts, but the template
accesses related `author` (ForeignKey) and `comments` (reverse ForeignKey)
for each post, causing additional queries.

Solution: Use select_related() for ForeignKey and prefetch_related() for
reverse relationships.
```

**Optimized Code:**
```python
# GOOD: Optimized with proper eager loading
from django.db.models import Count, Prefetch

def post_list(request):
    posts = Post.objects.select_related(
        'author'  # ForeignKey - use select_related (SQL JOIN)
    ).prefetch_related(
        Prefetch(
            'comments',
            queryset=Comment.objects.select_related('author').filter(is_approved=True)
        )
    ).annotate(
        comment_count=Count('comments', filter=Q(comments__is_approved=True))
    ).order_by('-published_at')

    return render(request, 'posts/list.html', {'posts': posts})

# Now template only uses the prefetched data - no additional queries!
```

**Performance Impact:**
- Before: 1 + N (authors) + N (comment counts) = 201 queries for 100 posts
- After: 3 queries total (posts, authors via JOIN, comments prefetch)

---

## Example 3: Django REST Framework API Endpoint

**User Request:**
> "Create a REST API for my Product model with filtering, pagination, and proper permissions"

**Claude Response:**
```
I'll implement a complete DRF endpoint following best practices:

1. Create ModelSerializer with validation
2. Implement ViewSet with proper permissions
3. Add filtering and search capabilities
4. Configure pagination
5. Set up URL routing
```

**Implementation:**

```python
# serializers.py
from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'stock',
            'category', 'category_name', 'is_available', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_is_available(self, obj):
        """Check if product is in stock."""
        return obj.stock > 0

    def validate_price(self, value):
        """Ensure price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero")
        return value

# views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product CRUD operations.

    List and retrieve are public, create/update/delete require authentication.
    """
    queryset = Product.objects.select_related('category').filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'stock']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'stock']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter products based on query params."""
        queryset = super().get_queryset()

        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset

# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    path('api/', include(router.urls)),
]

# settings.py (pagination configuration)
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

**API Usage Examples:**
```bash
# List all products (paginated)
GET /api/products/

# Search products
GET /api/products/?search=laptop

# Filter by category and price range
GET /api/products/?category=electronics&min_price=100&max_price=500

# Order by price ascending
GET /api/products/?ordering=price

# Retrieve single product
GET /api/products/123/

# Create product (requires authentication)
POST /api/products/
```

---

## Example 4: Writing Django Tests

**User Request:**
> "Write tests for the Product API endpoint"

**Implementation:**
```python
# tests/test_product_api.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from .models import Product, Category

User = get_user_model()

class ProductAPITestCase(TestCase):
    """Test suite for Product API endpoints."""

    def setUp(self):
        """Set up test data before each test."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Test Product',
            description='A test product',
            price=Decimal('99.99'),
            stock=10,
            category=self.category
        )

    def test_list_products_unauthenticated(self):
        """Unauthenticated users can list products."""
        response = self.client.get('/api/products/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_product_requires_authentication(self):
        """Creating products requires authentication."""
        data = {
            'name': 'New Product',
            'price': '49.99',
            'stock': 5,
            'category': self.category.id
        }
        response = self.client.post('/api/products/', data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_product_authenticated(self):
        """Authenticated users can create products."""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'New Product',
            'description': 'A new product',
            'price': '49.99',
            'stock': 5,
            'category': self.category.id
        }
        response = self.client.post('/api/products/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(response.data['name'], 'New Product')

    def test_filter_by_price_range(self):
        """Products can be filtered by price range."""
        Product.objects.create(
            name='Expensive Product',
            price=Decimal('299.99'),
            stock=5,
            category=self.category
        )

        response = self.client.get('/api/products/?min_price=200')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Expensive Product')

    def test_product_availability_field(self):
        """is_available field correctly reflects stock status."""
        response = self.client.get(f'/api/products/{self.product.id}/')

        self.assertEqual(response.data['is_available'], True)

        # Update stock to 0
        self.product.stock = 0
        self.product.save()

        response = self.client.get(f'/api/products/{self.product.id}/')
        self.assertEqual(response.data['is_available'], False)
```

**Run tests:**
```bash
python manage.py test tests.test_product_api
```
````

## File: .agents/skills/django-expert/references/models-and-orm.md
````markdown
# Django ORM Best Practices

## The N+1 Query Problem

The most common performance issue in Django applications.

### Problem Example

```python
# ❌ BAD: N+1 queries (1 + N where N = number of users)
users = User.objects.all()  # 1 query
for user in users:
    print(user.profile.bio)  # N additional queries!
```

This results in:
```sql
SELECT * FROM users;                    -- 1 query
SELECT * FROM profiles WHERE user_id=1; -- Query for each user
SELECT * FROM profiles WHERE user_id=2;
SELECT * FROM profiles WHERE user_id=3;
-- ... etc
```

### Solution: select_related()

Use `select_related()` for **foreign key** and **one-to-one** relationships:

```python
# ✅ GOOD: 1 query with JOIN
users = User.objects.select_related('profile').all()
for user in users:
    print(user.profile.bio)  # No additional queries!
```

This results in:
```sql
SELECT *
FROM users
INNER JOIN profiles ON users.id = profiles.user_id;  -- 1 query
```

### Solution: prefetch_related()

Use `prefetch_related()` for **many-to-many** and **reverse foreign key** relationships:

```python
# ❌ BAD: N+1 queries
users = User.objects.all()
for user in users:
    for group in user.groups.all():  # N queries!
        print(group.name)

# ✅ GOOD: 2 queries total
users = User.objects.prefetch_related('groups').all()
for user in users:
    for group in user.groups.all():  # No additional queries!
        print(group.name)
```

This results in:
```sql
SELECT * FROM users;                                    -- Query 1
SELECT * FROM groups
INNER JOIN user_groups ON groups.id = user_groups.group_id
WHERE user_groups.user_id IN (1, 2, 3, ...);           -- Query 2
```

## Combining select_related() and prefetch_related()

```python
# Get users with their profiles AND groups in 2 queries
users = User.objects.select_related('profile').prefetch_related('groups').all()
```

## Advanced Prefetching

### Prefetch with Filtering

```python
from django.db.models import Prefetch

# Only prefetch active posts
users = User.objects.prefetch_related(
    Prefetch(
        'posts',
        queryset=Post.objects.filter(is_published=True).order_by('-created_at')
    )
).all()
```

### Nested Prefetching

```python
# Get users with their posts and each post's comments
users = User.objects.prefetch_related(
    'posts',
    'posts__comments',
    'posts__comments__author'
).all()
```

## Custom Managers

Encapsulate common queries in custom managers:

```python
class UserManager(models.Manager):
    def active(self):
        """Get active users."""
        return self.filter(is_active=True)

    def with_profile(self):
        """Always include profile to prevent N+1."""
        return self.select_related('profile')

    def with_full_details(self):
        """Get users with all related data."""
        return self.select_related('profile').prefetch_related(
            'groups',
            'user_permissions',
            Prefetch(
                'posts',
                queryset=Post.objects.filter(is_published=True)
            )
        )

class User(AbstractUser):
    objects = UserManager()

# Usage
active_users = User.objects.active().with_profile()
detailed_users = User.objects.with_full_details()
```

## QuerySet Methods

### only() and defer()

Load only specific fields when you don't need the entire model:

```python
# only() - Load ONLY specified fields
users = User.objects.only('id', 'email', 'first_name')
# SELECT id, email, first_name FROM users

# defer() - Load ALL fields EXCEPT specified
users = User.objects.defer('password', 'last_login')
# SELECT id, email, first_name, ... FROM users (excludes password, last_login)
```

**Warning**: Accessing deferred fields triggers an additional query!

```python
users = User.objects.defer('bio').all()
for user in users:
    print(user.bio)  # Additional query per user!
```

### values() and values_list()

Get dictionaries or tuples instead of model instances (faster):

```python
# values() - Returns dictionaries
users = User.objects.values('id', 'email')
# [{'id': 1, 'email': 'user@example.com'}, ...]

# values_list() - Returns tuples
user_ids = User.objects.values_list('id', flat=True)
# [1, 2, 3, 4, ...]

user_data = User.objects.values_list('id', 'email')
# [(1, 'user@example.com'), (2, 'other@example.com'), ...]
```

### exists() and count()

```python
# ❌ BAD: Loads all objects into memory
if len(User.objects.filter(email=email)):
    ...

# ✅ GOOD: Database-level check
if User.objects.filter(email=email).exists():
    ...

# ❌ BAD: Loads all objects to count
total = len(User.objects.all())

# ✅ GOOD: Database-level count
total = User.objects.count()
```

## Aggregation & Annotation

### aggregate()

Get summary statistics:

```python
from django.db.models import Count, Avg, Max, Min, Sum

# Get statistics about all users
stats = User.objects.aggregate(
    total=Count('id'),
    avg_posts=Avg('posts__count'),
    max_created=Max('created_at')
)
# {'total': 100, 'avg_posts': 5.2, 'max_created': datetime(...)}
```

### annotate()

Add calculated fields to each object:

```python
from django.db.models import Count, Q

# Add post count to each user
users = User.objects.annotate(
    total_posts=Count('posts'),
    published_posts=Count('posts', filter=Q(posts__is_published=True))
)

for user in users:
    print(f"{user.email}: {user.total_posts} total, {user.published_posts} published")
```

## Bulk Operations

### bulk_create()

Create multiple objects in one query:

```python
# ❌ BAD: N queries
for i in range(1000):
    User.objects.create(email=f"user{i}@example.com")

# ✅ GOOD: 1 query
users = [
    User(email=f"user{i}@example.com")
    for i in range(1000)
]
User.objects.bulk_create(users, batch_size=500)
```

**Note**: `bulk_create()` doesn't call `save()` or send signals!

### bulk_update()

Update multiple objects in one query:

```python
# ❌ BAD: N queries
for user in users:
    user.is_active = False
    user.save()

# ✅ GOOD: 1 query
for user in users:
    user.is_active = False
User.objects.bulk_update(users, ['is_active'], batch_size=500)
```

### update()

Update multiple objects with one query:

```python
# ❌ BAD: N queries
for user in User.objects.filter(is_active=True):
    user.last_login = timezone.now()
    user.save()

# ✅ GOOD: 1 query
User.objects.filter(is_active=True).update(last_login=timezone.now())
```

**Note**: `update()` doesn't call `save()` or send signals!

## Database Indexes

Add indexes for fields used in:
- Filtering (`WHERE` clauses)
- Ordering (`ORDER BY`)
- Joins (`FOREIGN KEY`)

```python
class User(models.Model):
    email = models.EmailField(unique=True)  # Automatic index
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),  # Single field
            models.Index(fields=['is_active', 'created_at']),  # Composite
            models.Index(fields=['-created_at']),  # Descending order
        ]
```

### When to Add Indexes

✅ **Add indexes for:**
- Foreign keys (automatically indexed)
- Fields used in `filter()` frequently
- Fields used in `order_by()` frequently
- Unique fields (automatically indexed)

❌ **Don't add indexes for:**
- Fields that are rarely queried
- Small tables (< 1000 rows)
- Fields that change frequently
- Too many indexes (slows down writes)

## Query Optimization Patterns

### 1. Filter Early, Annotate/Aggregate Late

```python
# ✅ GOOD: Filter before annotation
active_users = User.objects.filter(is_active=True).annotate(
    post_count=Count('posts')
)

# ❌ BAD: Annotate then filter (processes all rows first)
active_users = User.objects.annotate(
    post_count=Count('posts')
).filter(is_active=True)
```

### 2. Use iterator() for Large QuerySets

```python
# ❌ BAD: Loads all 1M users into memory
for user in User.objects.all():
    process_user(user)

# ✅ GOOD: Streams users in chunks
for user in User.objects.all().iterator(chunk_size=1000):
    process_user(user)
```

### 3. Avoid Chaining Multiple Queries

```python
# ❌ BAD: Multiple queries
active_users = User.objects.filter(is_active=True)
verified_users = active_users.filter(email_verified=True)
recent_users = verified_users.filter(created_at__gte=last_week)

# ✅ GOOD: Single query
recent_users = User.objects.filter(
    is_active=True,
    email_verified=True,
    created_at__gte=last_week
)
```

## Transactions

Use transactions for operations that must succeed or fail together:

```python
from django.db import transaction

# Atomic decorator
@transaction.atomic
def create_user_with_profile(data):
    user = User.objects.create(**data['user'])
    Profile.objects.create(user=user, **data['profile'])
    return user

# Atomic context manager
def transfer_credits(from_user, to_user, amount):
    with transaction.atomic():
        from_user.credits -= amount
        from_user.save()

        to_user.credits += amount
        to_user.save()

# Rollback on error
try:
    with transaction.atomic():
        User.objects.create(email=email)
        send_welcome_email(email)  # If this fails, user creation is rolled back
except Exception:
    # Transaction automatically rolled back
    logger.exception("Failed to create user")
```

## Raw SQL (When Necessary)

Sometimes the ORM can't express complex queries efficiently:

```python
# Use raw SQL as a last resort
users = User.objects.raw('''
    SELECT u.*, COUNT(p.id) as post_count
    FROM users u
    LEFT JOIN posts p ON u.id = p.user_id
    GROUP BY u.id
    HAVING COUNT(p.id) > 10
''')

# ALWAYS use parameters to prevent SQL injection
users = User.objects.raw(
    'SELECT * FROM users WHERE created_at > %s',
    [start_date]
)
```

## Debugging Queries

### See Generated SQL

```python
queryset = User.objects.filter(is_active=True)
print(queryset.query)  # Print SQL

# Or in shell
from django.db import connection
print(connection.queries)  # All queries executed
```

### Django Debug Toolbar

Install and use django-debug-toolbar in development:

```bash
pip install django-debug-toolbar
```

Shows:
- Number of queries per request
- Duplicate queries
- Slow queries
- SQL for each query

## Performance Checklist

Before deploying a feature:

✅ Check for N+1 queries
✅ Use select_related() for FK/OneToOne
✅ Use prefetch_related() for M2M/reverse FK
✅ Add database indexes for filtered/ordered fields
✅ Use bulk operations for creating/updating many objects
✅ Use only()/defer() when loading partial models
✅ Use exists() instead of if queryset
✅ Use count() instead of len(queryset)
✅ Wrap multi-step operations in transactions
✅ Test with production-sized data

---

**Remember**: Premature optimization is the root of all evil, but N+1 queries are not premature - they're fundamental!
````

## File: .agents/skills/django-expert/references/performance-optimization.md
````markdown
# Django Performance Optimization

## Database Query Optimization

### Avoid N+1 Queries (Most Important!)

```python
# ❌ BAD: N+1 queries
posts = Post.objects.all()
for post in posts:
    print(post.author.username)  # N additional queries!

# ✅ GOOD: 1 query with JOIN
posts = Post.objects.select_related('author').all()
for post in posts:
    print(post.author.username)  # No additional queries!
```

See `models-and-orm.md` for comprehensive coverage of select_related, prefetch_related, and query optimization.

### Use only() and defer()

```python
# ✅ GOOD: Load only needed fields
users = User.objects.only('id', 'username', 'email')

# ✅ GOOD: Exclude large fields
posts = Post.objects.defer('content')  # Skip content field
```

### Database Indexes

```python
class Post(models.Model):
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),  # For ordering
            models.Index(fields=['is_published', 'created_at']),  # Composite
            models.Index(fields=['-view_count']),  # For popular posts
        ]

# ✅ GOOD: Check if index is used
# Run: EXPLAIN ANALYZE SELECT ...
from django.db import connection
queryset = Post.objects.filter(is_published=True).order_by('-created_at')
print(queryset.query)
```

### Bulk Operations

```python
# ❌ BAD: N queries
for i in range(1000):
    Post.objects.create(title=f'Post {i}')

# ✅ GOOD: 1 query
posts = [Post(title=f'Post {i}') for i in range(1000)]
Post.objects.bulk_create(posts, batch_size=500)

# ❌ BAD: N updates
for post in posts:
    post.view_count += 1
    post.save()

# ✅ GOOD: 1 query
Post.objects.filter(id__in=post_ids).update(view_count=F('view_count') + 1)
```

### Query Profiling

```python
from django.db import connection
from django.test.utils import override_settings

# Check number of queries
with override_settings(DEBUG=True):
    posts = Post.objects.select_related('author').all()
    list(posts)  # Force evaluation
    print(f"Queries: {len(connection.queries)}")
    for query in connection.queries:
        print(query['sql'])
```

## Caching

### Cache Framework Setup

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'myapp',
        'TIMEOUT': 300,  # 5 minutes default
    }
}
```

### Low-Level Cache API

```python
from django.core.cache import cache

# ✅ GOOD: Cache expensive queries
def get_popular_posts():
    posts = cache.get('popular_posts')
    if posts is None:
        posts = Post.objects.filter(
            is_published=True
        ).select_related('author').order_by('-view_count')[:10]
        cache.set('popular_posts', posts, timeout=300)  # 5 minutes
    return posts

# ✅ GOOD: Cache with complex key
def get_user_posts(user_id):
    cache_key = f'user_{user_id}_posts'
    posts = cache.get(cache_key)
    if posts is None:
        posts = Post.objects.filter(author_id=user_id)
        cache.set(cache_key, posts, timeout=600)
    return posts

# Invalidate cache
def create_post(user, data):
    post = Post.objects.create(author=user, **data)
    cache.delete(f'user_{user.id}_posts')  # Invalidate
    cache.delete('popular_posts')
    return post
```

### Per-View Cache

```python
from django.views.decorators.cache import cache_page

# ✅ GOOD: Cache entire view response
@cache_page(60 * 15)  # 15 minutes
def blog_list(request):
    posts = Post.objects.filter(is_published=True)
    return render(request, 'blog/list.html', {'posts': posts})

# ✅ GOOD: Cache with conditional logic
from django.views.decorators.cache import cache_control

@cache_control(max_age=3600, public=True)
def public_content(request):
    # Browser and CDN can cache for 1 hour
    ...
```

### Template Fragment Caching

```django
{% load cache %}

{# ✅ GOOD: Cache expensive template sections #}
{% cache 300 sidebar %}
  {% for category in categories %}
    <li>{{ category.name }} ({{ category.post_count }})</li>
  {% endfor %}
{% endcache %}

{# ✅ GOOD: Cache with variables #}
{% cache 600 post_detail post.id post.updated_at %}
  <h1>{{ post.title }}</h1>
  <div>{{ post.content }}</div>
{% endcache %}
```

### Caching Patterns

```python
# ✅ GOOD: Cache with get_or_set
from django.core.cache import cache

def get_post_stats(post_id):
    cache_key = f'post_{post_id}_stats'
    return cache.get_or_set(
        cache_key,
        lambda: compute_expensive_stats(post_id),
        timeout=3600
    )

# ✅ GOOD: Cache invalidation pattern
class Post(models.Model):
    ...

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Invalidate related caches
        cache.delete(f'post_{self.id}_detail')
        cache.delete('popular_posts')
        cache.delete(f'user_{self.author_id}_posts')

    def delete(self, *args, **kwargs):
        cache.delete(f'post_{self.id}_detail')
        cache.delete('popular_posts')
        super().delete(*args, **kwargs)
```

## Database Connection Pooling

### Using pgbouncer (PostgreSQL)

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydb',
        'USER': 'myuser',
        'PASSWORD': 'mypass',
        'HOST': '127.0.0.1',
        'PORT': '6432',  # pgbouncer port
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}
```

### Django-DB-Pool

```bash
pip install django-db-pool
```

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django_db_pool.backends.postgresql',
        'POOL_OPTIONS': {
            'POOL_SIZE': 10,
            'MAX_OVERFLOW': 10,
        },
        ...
    }
}
```

## Static File Optimization

### Compression and Minification

```bash
pip install django-compressor
```

```python
# settings.py
INSTALLED_APPS += ['compressor']

COMPRESS_ENABLED = True
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
]
COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter',
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]
```

```django
{% load compress %}

{% compress css %}
  <link rel="stylesheet" href="{% static 'css/style1.css' %}">
  <link rel="stylesheet" href="{% static 'css/style2.css' %}">
{% endcompress %}

{% compress js %}
  <script src="{% static 'js/script1.js' %}"></script>
  <script src="{% static 'js/script2.js' %}"></script>
{% endcompress %}
```

### CDN for Static Files

```python
# settings.py
# Use WhiteNoise for serving static files
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this
    ...
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Or use S3/CloudFront
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

AWS_S3_CUSTOM_DOMAIN = 'd123456.cloudfront.net'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
```

## Background Tasks with Celery

```bash
pip install celery redis
```

```python
# celery.py
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'

# tasks.py
from celery import shared_task
import time

@shared_task
def send_email(user_id, template):
    """Send email asynchronously."""
    user = User.objects.get(id=user_id)
    # Send email logic
    time.sleep(2)  # Simulate email sending
    return f'Email sent to {user.email}'

@shared_task
def generate_report(report_id):
    """Generate report in background."""
    report = Report.objects.get(id=report_id)
    # Generate report logic
    report.status = 'completed'
    report.save()
    return report_id

# views.py
def register(request):
    user = User.objects.create_user(...)
    # ✅ GOOD: Send email asynchronously
    send_email.delay(user.id, 'welcome')
    return redirect('home')
```

## Pagination

```python
from django.core.paginator import Paginator

# ✅ GOOD: Paginate large querysets
def blog_list(request):
    posts = Post.objects.filter(is_published=True).select_related('author')
    paginator = Paginator(posts, 20)  # 20 posts per page

    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/list.html', {'page_obj': page_obj})

# DRF pagination
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 20,
}
```

## Middleware Optimization

```python
# ✅ GOOD: Conditional middleware
class ExpensiveMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for static files
        if request.path.startswith('/static/'):
            return self.get_response(request)

        # Only run for specific paths
        if request.path.startswith('/api/'):
            # Expensive processing
            ...

        response = self.get_response(request)
        return response
```

## Template Optimization

### Use Template Fragment Caching

```django
{% load cache %}

{# Cache expensive queries #}
{% cache 300 sidebar request.user.id %}
  {% include "sidebar.html" %}
{% endcache %}
```

### Avoid Logic in Templates

```django
{# ❌ BAD: N+1 queries in template #}
{% for post in posts %}
  <h2>{{ post.title }}</h2>
  <p>By {{ post.author.username }}</p>  {# N queries! #}
  <p>{{ post.comments.count }} comments</p>  {# N queries! #}
{% endfor %}

{# ✅ GOOD: Preload in view #}
{# posts = Post.objects.select_related('author').annotate(comment_count=Count('comments')) #}
{% for post in posts %}
  <h2>{{ post.title }}</h2>
  <p>By {{ post.author.username }}</p>
  <p>{{ post.comment_count }} comments</p>
{% endfor %}
```

## Profiling and Monitoring

### Django Debug Toolbar

```bash
pip install django-debug-toolbar
```

```python
# settings.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

INTERNAL_IPS = ['127.0.0.1']

# urls.py
from django.conf import settings

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
```

Shows:
- Number of SQL queries
- Duplicate queries
- Query execution time
- Template rendering time
- Cache hits/misses

### Django Silk (Production Profiling)

```bash
pip install django-silk
```

```python
# settings.py
INSTALLED_APPS += ['silk']
MIDDLEWARE += ['silk.middleware.SilkyMiddleware']

# urls.py
urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
```

### Custom Performance Logging

```python
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

def log_performance(func):
    """Decorator to log function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start

        if duration > 1.0:  # Log if > 1 second
            logger.warning(
                f"{func.__name__} took {duration:.2f}s",
                extra={'duration': duration}
            )

        return result
    return wrapper

@log_performance
def expensive_view(request):
    # View logic
    ...
```

## Database Optimization Checklist

✅ Use select_related() for ForeignKey/OneToOne
✅ Use prefetch_related() for ManyToMany/reverse FK
✅ Add database indexes for filtered/ordered fields
✅ Use only()/defer() for partial model loading
✅ Use values()/values_list() for raw data
✅ Use bulk_create()/bulk_update() for batch operations
✅ Use update() instead of save() when possible
✅ Use exists() instead of counting
✅ Use iterator() for large querysets
✅ Avoid N+1 queries (check with Debug Toolbar)

## Caching Checklist

✅ Cache expensive database queries
✅ Cache API responses
✅ Cache template fragments
✅ Use cache versioning for invalidation
✅ Set appropriate cache timeouts
✅ Monitor cache hit rates
✅ Use Redis for production caching
✅ Invalidate cache on data changes

## General Performance Checklist

✅ Enable database connection pooling
✅ Compress and minify static files
✅ Use CDN for static files
✅ Enable GZIP compression
✅ Offload heavy tasks to Celery
✅ Paginate large result sets
✅ Profile with Django Debug Toolbar
✅ Monitor production performance (Sentry, New Relic, etc.)
✅ Optimize images (compress, lazy load)
✅ Use HTTP/2 and browser caching headers

---

**Remember**: Measure first, optimize second. Don't optimize prematurely - profile to find real bottlenecks, then fix them systematically.
````

## File: .agents/skills/django-expert/references/production-deployment.md
````markdown
# Django Production Deployment Reference

This guide covers essential configuration and best practices for deploying Django applications to production environments.

## Pre-Deployment Checklist

### Run Deployment Checks

Django provides an automated deployment check command:

```bash
python manage.py check --deploy
```

This validates critical settings and warns about common misconfigurations.

**Rule**: Always run `check --deploy` before going live.

### Switch from Development Server

```bash
# ❌ NEVER use in production
python manage.py runserver

# ✅ Use production-ready servers
gunicorn myproject.wsgi:application
# or
uvicorn myproject.asgi:application
# or
daphne myproject.asgi:application
```

**Common WSGI/ASGI servers:**
- **Gunicorn**: Standard WSGI server, excellent for most Django apps
- **uWSGI**: High-performance WSGI server with many features
- **Uvicorn**: ASGI server for async Django (channels, async views)
- **Daphne**: ASGI server built for Django Channels

---

## Critical Settings

### SECRET_KEY

**Never commit `SECRET_KEY` to version control.**

```python
# ✅ GOOD: Load from environment
import os
SECRET_KEY = os.environ["SECRET_KEY"]

# ✅ GOOD: Load from file
with open("/etc/secrets/django_secret_key.txt") as f:
    SECRET_KEY = f.read().strip()

# ✅ GOOD: Using python-decouple
from decouple import config
SECRET_KEY = config('SECRET_KEY')

# ❌ BAD: Hardcoded in settings
SECRET_KEY = 'django-insecure-hardcoded-key-123'
```

**Key rotation with fallbacks:**

```python
SECRET_KEY = os.environ["CURRENT_SECRET_KEY"]
SECRET_KEY_FALLBACKS = [
    os.environ["OLD_SECRET_KEY"],
]
```

This allows existing sessions to work during key rotation. Remove old keys from fallbacks after sufficient time.

**Rule**: Treat `SECRET_KEY` like a database password.

### DEBUG

```python
# ✅ PRODUCTION: Debug disabled
DEBUG = False

# ✅ GOOD: Environment-based
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# ❌ NEVER in production
DEBUG = True
```

**Why `DEBUG = True` is dangerous:**
- Exposes source code in error pages
- Shows database queries and local variables
- Reveals settings and library versions
- Significantly impacts performance

**Rule**: `DEBUG = False` in production, always.

### ALLOWED_HOSTS

```python
# ✅ PRODUCTION: Specific hosts only
ALLOWED_HOSTS = ['example.com', 'www.example.com']

# ✅ GOOD: From environment
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# ❌ BAD: Allows any host (CSRF vulnerability)
ALLOWED_HOSTS = ['*']

# ❌ BAD: Empty (Django will refuse to run)
ALLOWED_HOSTS = []
```

**Nginx configuration to handle invalid hosts:**

```nginx
server {
    listen 80 default_server;
    server_name _;
    return 444;  # Close connection without response
}

server {
    listen 80;
    server_name example.com www.example.com;
    # Your Django app configuration
}
```

**Rule**: Always specify exact hostnames in production.

---

## Database Configuration

### Connection Settings

```python
# ✅ PRODUCTION: Secure connection parameters
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Persistent connections
        'OPTIONS': {
            'sslmode': 'require',  # Enforce SSL
        },
    }
}

# ❌ BAD: Hardcoded credentials
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydb',
        'USER': 'postgres',
        'PASSWORD': 'password123',
        'HOST': 'localhost',
    }
}
```

### Connection Pooling

```python
# ✅ GOOD: Persistent connections
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,  # Keep connections open for 10 minutes
    }
}

# ✅ BETTER: External connection pooler (PgBouncer)
DATABASES = {
    'default': {
        'HOST': 'pgbouncer-host',
        'PORT': 6432,
        'CONN_MAX_AGE': None,  # Let PgBouncer handle pooling
    }
}
```

**Rule**: Enable persistent connections or use external pooling.

### Database Backups

```bash
# PostgreSQL backup
pg_dump -h localhost -U user -d database > backup.sql

# Automated backups (example cron)
0 2 * * * pg_dump -h localhost -U user -d database | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz
```

**Rule**: Set up automated backups before going live.

---

## HTTPS Configuration

**All production sites must use HTTPS**, especially those handling authentication.

### SSL/TLS Settings

```python
# ✅ PRODUCTION: Force HTTPS
SECURE_SSL_REDIRECT = True

# ✅ GOOD: Strict Transport Security
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ✅ REQUIRED: Secure cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ✅ GOOD: Additional cookie security
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
```

**HSTS (HTTP Strict Transport Security) considerations:**
- Start with shorter duration for testing: `SECURE_HSTS_SECONDS = 3600`
- Increase gradually: 1 week → 1 month → 1 year
- Only enable `PRELOAD` after testing with shorter durations
- Be aware: HSTS cannot be easily undone

### Nginx SSL Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Rule**: Never serve authenticated pages over HTTP.

---

## Static and Media Files

### Static Files

```python
# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/myproject/static/'

# ✅ GOOD: Use CDN for static files
STATIC_URL = 'https://cdn.example.com/static/'

# ✅ GOOD: Enable compression
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

**Collect static files before deployment:**

```bash
python manage.py collectstatic --no-input
```

**Nginx static file serving:**

```nginx
location /static/ {
    alias /var/www/myproject/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

**Rule**: Serve static files through CDN or reverse proxy, not Django.

### Media Files

```python
# settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/myproject/media/'

# ✅ BETTER: Use object storage
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'my-bucket'
AWS_S3_CUSTOM_DOMAIN = 'cdn.example.com'
```

**Nginx media file serving:**

```nginx
location /media/ {
    alias /var/www/myproject/media/;

    # ✅ CRITICAL: Prevent script execution
    location ~ \.(php|py|pl|sh|cgi)$ {
        deny all;
    }
}
```

**Security considerations:**
- Never execute uploaded files
- Validate file types before saving
- Use unique filenames to prevent overwrites
- Set up backups for user uploads
- Consider virus scanning for uploaded files

**Rule**: Treat all media files as untrusted user input.

---

## Caching

### Cache Backend

```python
# ✅ PRODUCTION: Redis cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': os.environ.get('REDIS_PASSWORD'),
        },
        'KEY_PREFIX': 'myapp',
        'TIMEOUT': 300,
    }
}

# ❌ DEVELOPMENT ONLY: Dummy cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
```

### Session Backend

```python
# ✅ PRODUCTION: Cached sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# ✅ ALSO GOOD: Redis sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ✅ GOOD: Set reasonable session timeout
SESSION_COOKIE_AGE = 86400  # 24 hours
```

**Clear expired sessions regularly:**

```bash
# Add to cron
python manage.py clearsessions
```

**Rule**: Use Redis or Memcached for production caching.

### Template Caching

```python
# ✅ PRODUCTION: Cached template loader
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'OPTIONS': {
        'loaders': [
            ('django.template.loaders.cached.Loader', [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]),
        ],
    },
}]
```

This is automatically enabled when `DEBUG = False`, but explicit configuration provides better control.

---

## Email Configuration

### SMTP Settings

```python
# ✅ PRODUCTION: Proper email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']

DEFAULT_FROM_EMAIL = 'noreply@example.com'
SERVER_EMAIL = 'server@example.com'

# ❌ DEVELOPMENT ONLY: Console backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**Email services:**
- **SendGrid**: Reliable transactional email
- **Mailgun**: Good deliverability and analytics
- **Amazon SES**: Cost-effective for high volume
- **Postmark**: Excellent for transactional email

**Rule**: Use a professional email service, not localhost.

---

## Error Monitoring and Logging

### Logging Configuration

```python
# ✅ PRODUCTION: Comprehensive logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/error.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'myapp': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Error Notifications

```python
# ✅ GOOD: Admin notifications
ADMINS = [
    ('Admin Name', 'admin@example.com'),
]

MANAGERS = [
    ('Manager Name', 'manager@example.com'),
]

# Filter spurious 404s
IGNORABLE_404_URLS = [
    re.compile(r'\.(php|cgi)$'),
    re.compile(r'^/phpmyadmin/'),
]
```

**Limitations of email notifications:**
- Don't scale well with traffic
- Can overwhelm email
- No aggregation or analytics
- Delayed notification

### Sentry Integration

```python
# ✅ BETTER: Sentry for error tracking
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,  # Performance monitoring
    send_default_pii=False,  # Don't send personal data
    environment=os.environ.get('ENVIRONMENT', 'production'),
)
```

**Benefits of Sentry:**
- Real-time error tracking
- Error aggregation and deduplication
- Stack trace analysis
- Performance monitoring
- Release tracking

**Rule**: Use Sentry or similar service for production error monitoring.

---

## Security Headers

```python
# ✅ PRODUCTION: Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ✅ GOOD: Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")  # Avoid unsafe-inline in production
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
```

**Using django-csp:**

```python
MIDDLEWARE = [
    # ...
    'csp.middleware.CSPMiddleware',
]

CSP_DEFAULT_SRC = ("'none'",)
CSP_SCRIPT_SRC = ("'self'", "https://cdn.example.com")
CSP_STYLE_SRC = ("'self'",)
CSP_IMG_SRC = ("'self'", "https://cdn.example.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
```

**Rule**: Enable all security headers in production.

---

## Performance Optimization

### Database Query Optimization

```python
# ✅ PRODUCTION: Monitor slow queries
LOGGING['loggers']['django.db.backends'] = {
    'level': 'DEBUG' if DEBUG else 'WARNING',
    'handlers': ['console'],
}

# ✅ GOOD: Query timeout (PostgreSQL)
DATABASES['default']['OPTIONS'] = {
    'options': '-c statement_timeout=5000'  # 5 seconds
}
```

### Middleware Optimization

```python
# ✅ Order matters for performance
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files early
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',  # Cache first
    'django.middleware.common.CommonMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',  # Then fetch
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### Compression

```python
# ✅ Enable GZip compression
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # Add near top
    # ... other middleware
]
```

**Rule**: Always enable compression in production.

---

## Environment-Based Settings

### Settings Structure

```
myproject/
├── settings/
│   ├── __init__.py
│   ├── base.py          # Shared settings
│   ├── development.py   # Local development
│   ├── staging.py       # Staging environment
│   └── production.py    # Production environment
```

**base.py:**

```python
# Common settings for all environments
INSTALLED_APPS = [...]
MIDDLEWARE = [...]
```

**production.py:**

```python
from .base import *

DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
SECURE_SSL_REDIRECT = True
# ... production-specific settings
```

**Set environment:**

```bash
export DJANGO_SETTINGS_MODULE=myproject.settings.production
```

### Using Environment Variables

```python
# ✅ RECOMMENDED: python-decouple
from decouple import config, Csv

DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
DATABASE_URL = config('DATABASE_URL')
```

**.env file (never commit this):**

```env
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=example.com,www.example.com
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379/1
```

**Rule**: Store all environment-specific config in environment variables.

---

## Deployment Process

### Pre-Deployment Steps

```bash
# 1. Run tests
python manage.py test

# 2. Check for issues
python manage.py check --deploy

# 3. Check migrations
python manage.py makemigrations --check --dry-run

# 4. Collect static files
python manage.py collectstatic --no-input

# 5. Check for security issues
bandit -r myproject/
safety check
```

### Zero-Downtime Deployment

```bash
#!/bin/bash
# deploy.sh

# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate --no-input

# Collect static files
python manage.py collectstatic --no-input

# Graceful restart (sends SIGHUP to workers)
systemctl reload gunicorn

# Or for manual process management
kill -HUP $(cat /tmp/gunicorn.pid)
```

### Health Checks

```python
# myapp/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Simple health check endpoint for load balancers."""
    try:
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Check cache
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')

        return JsonResponse({'status': 'healthy'})
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=500)
```

**Rule**: Implement health checks for load balancers and monitoring.

---

## Monitoring and Observability

### Application Performance Monitoring

```python
# ✅ New Relic
import newrelic.agent
newrelic.agent.initialize('/etc/newrelic.ini')

# ✅ DataDog
from ddtrace import patch_all
patch_all()

# ✅ Application Insights (Azure)
from applicationinsights.django import ApplicationInsightsMiddleware
MIDDLEWARE = [
    'applicationinsights.django.ApplicationInsightsMiddleware',
    # ...
]
```

### Key Metrics to Monitor

- **Response time**: Average, 95th, 99th percentile
- **Error rate**: 4xx and 5xx responses
- **Database query time**: Slow query detection
- **Cache hit rate**: Redis/Memcached efficiency
- **Memory usage**: Application and database
- **CPU usage**: Under load
- **Disk space**: Logs and media files

**Rule**: Monitor application performance from day one.

---

## Backup Strategy

### Database Backups

```bash
#!/bin/bash
# backup-db.sh

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="mydb"

# Create backup
pg_dump -h localhost -U postgres -Fc $DB_NAME > $BACKUP_DIR/db_$DATE.dump

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete

# Upload to S3
aws s3 cp $BACKUP_DIR/db_$DATE.dump s3://my-backups/postgres/
```

### Media Files Backup

```bash
#!/bin/bash
# backup-media.sh

MEDIA_DIR="/var/www/myproject/media"
BACKUP_DIR="/backups/media"
DATE=$(date +%Y%m%d)

# Incremental backup
rsync -avz --delete $MEDIA_DIR $BACKUP_DIR/latest/

# Daily snapshot
cp -al $BACKUP_DIR/latest $BACKUP_DIR/$DATE
```

**Rule**: Test backup restoration regularly.

---

## Checklist Summary

Before going live, verify:

- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` loaded from environment
- [ ] `ALLOWED_HOSTS` configured
- [ ] Database backups scheduled
- [ ] Static files collected and served by CDN/nginx
- [ ] HTTPS enabled with proper certificates
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] Error monitoring configured (Sentry)
- [ ] Logging configured
- [ ] Cache backend configured (Redis)
- [ ] Email backend configured
- [ ] Security headers enabled
- [ ] `python manage.py check --deploy` passes
- [ ] Health check endpoint implemented
- [ ] Monitoring and alerts configured
- [ ] Deployment process documented
- [ ] Rollback plan prepared

**Final command:**

```bash
python manage.py check --deploy --settings=myproject.settings.production
```

If this passes with no warnings, you're ready for production.
````

## File: .agents/skills/django-expert/references/README.md
````markdown
# Django Expert - Reference Documentation

This directory contains comprehensive Django best practices documentation that will be loaded into Claude's context when needed.

## Purpose

Reference files provide detailed guidelines, patterns, and examples that would make SKILL.md too long (>5k words). Claude will read these files as needed based on the specific Django task at hand.

## Recommended Reference Files

Create the following markdown files in this directory to provide comprehensive Django guidance:

### 1. `models-and-orm.md` - Model Design & ORM Best Practices

**Topics to cover:**
- Model field types and when to use each
- Database relationships (ForeignKey, ManyToMany, OneToOne)
- Model Meta options (ordering, indexes, constraints)
- Custom model methods and properties
- Model managers and custom querysets
- Database query optimization (select_related, prefetch_related, only, defer)
- Common ORM patterns and anti-patterns
- Migration best practices
- Database indexing strategies

**Example structure:**
```markdown
# Django Models and ORM Best Practices

## Model Design Patterns

### Field Choices
- Use TextChoices or IntegerChoices for Django 3.0+
- Keep choices close to the model definition
[detailed examples...]

## Query Optimization

### N+1 Query Problem
[explanation and solutions...]

### Using select_related vs prefetch_related
[detailed guidance with examples...]
```

### 2. `views-and-urls.md` - Views, URLs, and Request Handling

**Topics to cover:**
- Function-based views vs class-based views
- When to use generic CBVs (ListView, DetailView, CreateView, etc.)
- Custom mixins and view composition
- URL patterns and routing best practices
- Request/response handling
- Middleware usage
- Context processors
- Form handling in views
- Error handling and custom error pages

### 3. `drf-guidelines.md` - Django REST Framework Best Practices

**Topics to cover:**
- Serializer patterns (ModelSerializer, nested serializers, write-only fields)
- ViewSets vs APIView vs function-based views
- Permissions and authentication
- Filtering, searching, and pagination
- Versioning strategies
- Custom actions and decorators
- Response formatting
- Error handling in APIs
- Testing DRF endpoints

### 4. `testing-strategies.md` - Testing Django Applications

**Topics to cover:**
- Test organization and structure
- TestCase vs TransactionTestCase
- Factory patterns and fixtures
- Mocking external services
- Testing models, views, and APIs
- Testing permissions and authentication
- Database testing best practices
- Coverage and test performance
- Integration vs unit testing

### 5. `security-checklist.md` - Django Security Best Practices

**Topics to cover:**
- CSRF protection
- XSS prevention
- SQL injection prevention
- Authentication and authorization
- Password handling and storage
- Secure settings for production
- HTTPS and SSL/TLS configuration
- Content Security Policy
- Rate limiting and throttling
- Security headers
- Common vulnerabilities and mitigations

### 6. `performance-optimization.md` - Performance and Scaling

**Topics to cover:**
- Database query optimization
- Caching strategies (per-view cache, template fragment cache, low-level cache)
- Redis/Memcached integration
- Database connection pooling
- Async views and background tasks (Celery)
- Static file optimization
- Database indexing and query profiling
- Monitoring and profiling tools
- Pagination strategies for large datasets

## How to Populate These Files

1. **Research**: Gather Django best practices from official docs, style guides, and community resources
2. **Structure**: Use clear headings, code examples, and explanations
3. **Examples**: Include both good and bad examples with explanations
4. **Keep Updated**: Maintain version-specific guidance (note Django version compatibility)
5. **Be Specific**: Provide concrete examples rather than general statements

## Example Reference File

Here's an example of what a well-structured reference file looks like:

```markdown
# Django REST Framework Guidelines

## Serializer Best Practices

### 1. Use ModelSerializer for Standard CRUD

For basic model serialization, always start with ModelSerializer:

```python
# Good
from rest_framework import serializers

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category']
        read_only_fields = ['id', 'created_at']
```

### 2. Nested Serializers for Relationships

For related objects, use nested serializers or use depth:

```python
# Option 1: Nested serializer (more control)
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'items', 'total']

# Option 2: Auto-nesting with depth (simpler but less control)
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        depth = 1  # Be careful with performance
```

# [Continue with more patterns...]
```

## Usage

Claude will automatically read these files when working on Django tasks. You don't need to manually reference them - Claude will determine which references are needed based on the task.

## Notes

- Keep files focused on specific topics (don't create one giant file)
- Use code examples liberally
- Include both do's and don'ts
- Reference Django and DRF version numbers when relevant
- Link to official documentation for deep dives
````

## File: .agents/skills/django-expert/references/security-checklist.md
````markdown
# Django Security Checklist

Django is secure by default, but you must configure it correctly and avoid common pitfalls.

## OWASP Top 10 & Django

### 1. SQL Injection

**Django protects you automatically** when using the ORM.

```python
# ✅ SAFE: ORM parameterizes queries
User.objects.filter(email=user_input)

# ✅ SAFE: Using parameters
User.objects.raw('SELECT * FROM users WHERE email = %s', [user_input])

# ❌ DANGEROUS: String formatting
User.objects.raw(f'SELECT * FROM users WHERE email = "{user_input}"')

# ❌ DANGEROUS: String concatenation
cursor.execute('SELECT * FROM users WHERE id = ' + user_id)
```

**Rule**: Never use string formatting or concatenation for SQL queries.

### 2. Cross-Site Scripting (XSS)

**Django templates auto-escape by default.**

```django
{# ✅ SAFE: Auto-escaped #}
<p>Hello, {{ user.name }}</p>

{# ❌ DANGEROUS: Marks as safe, disables escaping #}
<p>{{ user_bio|safe }}</p>

{# ✅ SAFE: Use linebreaks filter instead #}
<p>{{ user_bio|linebreaks }}</p>
```

**In views returning JSON for HTMX:**

```python
from django.utils.html import escape

# ✅ GOOD: Escape user input
return JsonResponse({
    'message': escape(user_message)
})
```

**Rule**: Never use `|safe` or `mark_safe()` on user-generated content.

### 3. Cross-Site Request Forgery (CSRF)

**Django's CSRF protection is enabled by default.**

```django
{# ✅ REQUIRED: Include CSRF token in forms #}
<form method="post">
  {% csrf_token %}
  ...
</form>

{# For HTMX #}
<button hx-post="/api/delete/" hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
  Delete
</button>
```

**In views:**

```python
from django.views.decorators.csrf import csrf_exempt, csrf_protect

# ✅ DEFAULT: CSRF protection enabled
@csrf_protect
def my_view(request):
    ...

# ❌ DANGEROUS: Only exempt for APIs with other auth (tokens)
@csrf_exempt
def api_view(request):
    # Must have other protection (API key, JWT, etc.)
    ...
```

**For AJAX/HTMX, include CSRF token in headers:**

```javascript
// HTMX auto-includes if you set this
document.body.addEventListener('htmx:configRequest', (event) => {
  event.detail.headers['X-CSRFToken'] = getCookie('csrftoken');
});
```

**Rule**: Never disable CSRF protection unless you have alternative authentication.

### 4. Broken Authentication

```python
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated

# ✅ GOOD: Require authentication
@login_required
def user_profile(request):
    ...

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    ...

# ❌ BAD: Checking authentication manually
def user_profile(request):
    if 'user_id' in request.session:  # Fragile!
        ...
```

**Password Security:**

```python
# settings.py

# ✅ GOOD: Strong password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ✅ GOOD: Use Argon2 for password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]
```

**Rule**: Always use Django's authentication system, never roll your own.

### 5. Broken Access Control

```python
# ❌ BAD: No authorization check
@login_required
def delete_post(request, post_id):
    post = Post.objects.get(id=post_id)
    post.delete()  # Any logged-in user can delete any post!
    return HttpResponse('Deleted')

# ✅ GOOD: Check authorization
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Authorization check
    if post.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden('You cannot delete this post')

    post.delete()
    return HttpResponse('Deleted')

# ✅ BETTER: Use permissions
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user

class PostDetailView(APIView):
    permission_classes = [IsOwnerOrReadOnly]
    ...
```

**Rule**: Authentication ≠ Authorization. Always check permissions.

### 6. Security Misconfiguration

```python
# settings.py

# ❌ DANGEROUS in production
DEBUG = True
SECRET_KEY = 'hardcoded-secret-key'
ALLOWED_HOSTS = ['*']

# ✅ GOOD: Production settings
DEBUG = False
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# ✅ GOOD: Security headers
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ✅ GOOD: Use environment variables
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database from environment
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

**Rule**: Never commit secrets. Always use environment variables.

### 7. Sensitive Data Exposure

```python
# ✅ GOOD: Don't log sensitive data
import logging
logger = logging.getLogger(__name__)

def process_payment(payment_data):
    # ❌ BAD: Logs credit card number
    logger.info(f"Processing payment: {payment_data}")

    # ✅ GOOD: Log only safe data
    logger.info(f"Processing payment for order {payment_data['order_id']}")

# ✅ GOOD: Don't expose sensitive fields in API
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        # NOT password, social_security_number, etc.

# ✅ GOOD: Redact in admin interface
from django.contrib import admin

class UserAdmin(admin.ModelAdmin):
    readonly_fields = ['password']  # Don't allow editing
    exclude = ['social_security_number']  # Don't show at all
```

**For database encryption:**

```bash
# Use django-encrypted-model-fields
pip install django-encrypted-model-fields
```

```python
from encrypted_model_fields.fields import EncryptedCharField

class PaymentInfo(models.Model):
    card_number = EncryptedCharField(max_length=16)
```

**Rule**: Assume logs, databases, and backups may be compromised. Encrypt sensitive data.

### 8. Insecure Deserialization

```python
import pickle
import json

# ❌ DANGEROUS: pickle can execute arbitrary code
data = pickle.loads(request.POST['data'])

# ✅ SAFE: Use JSON
data = json.loads(request.POST['data'])

# ✅ SAFE: Use Django's serialization
from django.core import serializers
data = serializers.deserialize('json', request.POST['data'])
```

**Rule**: Never use `pickle` or `eval()` on user input.

### 9. Using Components with Known Vulnerabilities

```bash
# Check for vulnerabilities
pip install safety
safety check

# Keep dependencies updated
pip list --outdated
```

**In requirements.txt, pin versions:**

```
Django==4.2.7  # Not Django>=4.0 (prevents auto-updates)
psycopg2-binary==2.9.9
redis==5.0.1
```

**Rule**: Keep dependencies updated and monitor security advisories.

### 10. Insufficient Logging & Monitoring

```python
import logging
logger = logging.getLogger(__name__)

# ✅ GOOD: Log security events
@login_required
def delete_account(request):
    user = request.user

    # Log security-relevant action
    logger.warning(
        f"Account deletion requested",
        extra={
            'user_id': user.id,
            'user_email': user.email,
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
        }
    )

    user.delete()
    return HttpResponse('Account deleted')

# ✅ GOOD: Log failed authentication
from django.contrib.auth.signals import user_login_failed

def log_failed_login(sender, credentials, request, **kwargs):
    logger.warning(
        f"Failed login attempt",
        extra={
            'username': credentials.get('username'),
            'ip_address': request.META.get('REMOTE_ADDR'),
        }
    )

user_login_failed.connect(log_failed_login)
```

**Rule**: Log security events, failed auth attempts, privilege escalations.

## Additional Django Security

### Clickjacking Protection

```python
# settings.py
X_FRAME_OPTIONS = 'DENY'  # Prevent embedding in iframes

# Or allow specific domains
X_FRAME_OPTIONS = 'SAMEORIGIN'  # Only same domain
```

### Host Header Validation

```python
# settings.py
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Never use:
ALLOWED_HOSTS = ['*']  # Allows host header injection attacks
```

### File Upload Security

```python
# settings.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880

# Validate file types
from django.core.exceptions import ValidationError

def validate_file_extension(value):
    import os
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.jpg', '.png', '.jpeg']
    if ext.lower() not in valid_extensions:
        raise ValidationError('Unsupported file extension.')

class Document(models.Model):
    file = models.FileField(
        upload_to='documents/',
        validators=[validate_file_extension]
    )

# ✅ GOOD: Store uploads outside web root
MEDIA_ROOT = '/var/www/media/'  # Not in static files directory!
MEDIA_URL = '/media/'
```

### Rate Limiting

```bash
pip install django-ratelimit
```

```python
from django_ratelimit.decorators import ratelimit

# Limit login attempts
@ratelimit(key='ip', rate='5/m', block=True)
def login_view(request):
    ...

# Limit API calls
@ratelimit(key='user', rate='100/h', block=True)
def api_endpoint(request):
    ...
```

## Security Checklist

Before deploying to production:

✅ `DEBUG = False`
✅ `SECRET_KEY` from environment variable
✅ `ALLOWED_HOSTS` configured properly
✅ All security headers enabled (HSTS, CSP, etc.)
✅ HTTPS enforced (`SECURE_SSL_REDIRECT = True`)
✅ Cookies secure (`SESSION_COOKIE_SECURE = True`)
✅ CSRF protection enabled (default)
✅ Strong password validators configured
✅ Database credentials in environment variables
✅ File upload size limits set
✅ Rate limiting on authentication endpoints
✅ Logging configured for security events
✅ Dependencies scanned for vulnerabilities
✅ Admin interface protected (strong password, 2FA if possible)
✅ Run `python manage.py check --deploy`

## Useful Django Management Commands

```bash
# Check deployment security
python manage.py check --deploy

# This checks for:
# - DEBUG = False
# - SECRET_KEY not hardcoded
# - ALLOWED_HOSTS configured
# - Security middleware enabled
# - And more...
```

---

**Remember**: Security is not a feature, it's a requirement. Defense in depth - use multiple layers of security.
````

## File: .agents/skills/django-expert/references/testing-strategies.md
````markdown
# Django Testing Strategies

This guide covers testing Django applications using both Django's built-in `TestCase` and `pytest-django`. Both approaches are valid and widely used in production.

**Quick comparison:**
- **Django TestCase**: Built-in, class-based, familiar to Django developers
- **pytest-django**: Modern, fixture-based, less boilerplate, extensive plugin ecosystem

Choose based on your team's preference and project needs. Both can coexist in the same project.

## Test Organization

### Directory Structure

```
myapp/
├── models.py
├── views.py
├── serializers.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    ├── test_serializers.py
    ├── test_api.py
    └── factories.py  # Factory Boy factories
```

### Test Discovery

Django automatically discovers tests in:
- Files starting with `test_`
- Files in `tests/` directories

```bash
# Run all tests
python manage.py test

# Run specific app
python manage.py test myapp

# Run specific test file
python manage.py test myapp.tests.test_models

# Run specific test class
python manage.py test myapp.tests.test_models.PostModelTest

# Run specific test method
python manage.py test myapp.tests.test_models.PostModelTest.test_create_post
```

## TestCase vs TransactionTestCase

### TestCase (Recommended)

```python
from django.test import TestCase

# ✅ GOOD: Faster, uses transactions
class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='pass')
        self.post = Post.objects.create(title='Test', author=self.user)

    def test_post_creation(self):
        self.assertEqual(self.post.title, 'Test')
        self.assertEqual(Post.objects.count(), 1)
```

**Features:**
- Wraps tests in transactions (rolled back after each test)
- Much faster than TransactionTestCase
- Database is reset between tests automatically

### TransactionTestCase

```python
from django.test import TransactionTestCase

# ✅ GOOD: When you need to test transactions
class PaymentProcessingTest(TransactionTestCase):
    def test_atomic_payment(self):
        with transaction.atomic():
            # Test transaction behavior
            ...
```

**Use TransactionTestCase when:**
- Testing transaction behavior (commit/rollback)
- Testing database-level constraints
- Testing raw SQL that doesn't work in transactions

**Rule**: Use TestCase unless you specifically need TransactionTestCase.

---

## pytest-django Setup

### Installation

```bash
pip install pytest-django
```

### Configuration

Create `pytest.ini` in your project root:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = myproject.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
```

Or use `pyproject.toml`:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "myproject.settings"
python_files = ["test_*.py", "*_test.py"]
```

### Running pytest

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_models.py

# Run specific test
pytest tests/test_models.py::test_create_post

# Verbose output
pytest -v

# Parallel execution (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto

# Reuse database between runs (faster)
pytest --reuse-db

# Skip migrations (much faster for large projects)
pytest --reuse-db --no-migrations
```

### Key pytest-django Fixtures

```python
# Database access fixtures
db                              # Standard database access
transactional_db                # Transaction testing
django_db_reset_sequences       # Reset DB sequences

# Client fixtures
client                          # Django test client
admin_client                    # Pre-authenticated admin client
async_client                    # AsyncClient for async views

# Request factory fixtures
rf                              # RequestFactory
async_rf                        # Async RequestFactory

# User fixtures
admin_user                      # Superuser instance
django_user_model               # User model class

# Utility fixtures
settings                        # Modify settings temporarily
live_server                     # Run development server
mailoutbox                      # Captured emails
django_assert_num_queries       # Query count assertions
```

### pytest-django Markers

```python
import pytest

# Grant database access
@pytest.mark.django_db
def test_model_save():
    pass

# Transaction testing
@pytest.mark.django_db(transaction=True)
def test_transaction():
    pass

# Override URLs
@pytest.mark.urls('myapp.test_urls')
def test_with_custom_urls():
    pass
```

---

## Model Testing

```python
from django.test import TestCase
from django.core.exceptions import ValidationError

# ✅ GOOD: Test model methods and validation
class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_post(self):
        """Test post creation."""
        post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author=self.user
        )
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.author, self.user)
        self.assertIsNotNone(post.created_at)

    def test_str_method(self):
        """Test string representation."""
        post = Post.objects.create(title='Test', author=self.user)
        self.assertEqual(str(post), 'Test')

    def test_slug_generation(self):
        """Test automatic slug generation."""
        post = Post.objects.create(
            title='Test Post Title',
            author=self.user
        )
        self.assertEqual(post.slug, 'test-post-title')

    def test_title_max_length(self):
        """Test title max length validation."""
        long_title = 'x' * 201
        post = Post(title=long_title, author=self.user)

        with self.assertRaises(ValidationError):
            post.full_clean()

    def test_get_absolute_url(self):
        """Test get_absolute_url method."""
        post = Post.objects.create(title='Test', author=self.user)
        expected_url = f'/posts/{post.slug}/'
        self.assertEqual(post.get_absolute_url(), expected_url)

    def test_published_posts_manager(self):
        """Test custom manager."""
        Post.objects.create(title='Published', author=self.user, is_published=True)
        Post.objects.create(title='Draft', author=self.user, is_published=False)

        published = Post.published.all()
        self.assertEqual(published.count(), 1)
        self.assertEqual(published.first().title, 'Published')
```

### Model Testing with pytest-django

```python
import pytest
from django.core.exceptions import ValidationError

# ✅ GOOD: Function-based tests with pytest
@pytest.mark.django_db
def test_create_post(django_user_model):
    """Test post creation."""
    user = django_user_model.objects.create_user(
        username='testuser',
        password='testpass123'
    )
    post = Post.objects.create(
        title='Test Post',
        content='Test content',
        author=user
    )
    assert post.title == 'Test Post'
    assert post.author == user
    assert post.created_at is not None


def test_str_method(db):
    """Test string representation."""
    user = User.objects.create_user(username='test', password='pass')
    post = Post.objects.create(title='Test', author=user)
    assert str(post) == 'Test'


def test_slug_generation(db):
    """Test automatic slug generation."""
    user = User.objects.create_user(username='test', password='pass')
    post = Post.objects.create(
        title='Test Post Title',
        author=user
    )
    assert post.slug == 'test-post-title'


def test_title_max_length(db):
    """Test title max length validation."""
    user = User.objects.create_user(username='test', password='pass')
    long_title = 'x' * 201
    post = Post(title=long_title, author=user)

    with pytest.raises(ValidationError):
        post.full_clean()


def test_get_absolute_url(db):
    """Test get_absolute_url method."""
    user = User.objects.create_user(username='test', password='pass')
    post = Post.objects.create(title='Test', author=user)
    expected_url = f'/posts/{post.slug}/'
    assert post.get_absolute_url() == expected_url


def test_published_posts_manager(db):
    """Test custom manager."""
    user = User.objects.create_user(username='test', password='pass')
    Post.objects.create(title='Published', author=user, is_published=True)
    Post.objects.create(title='Draft', author=user, is_published=False)

    published = Post.published.all()
    assert published.count() == 1
    assert published.first().title == 'Published'


# ✅ GOOD: Using fixtures for reusable test data
@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        password='testpass123'
    )


@pytest.fixture
def test_post(test_user):
    """Create a test post."""
    return Post.objects.create(
        title='Test Post',
        content='Test content',
        author=test_user
    )


def test_post_with_fixtures(test_post):
    """Test using fixtures."""
    assert test_post.title == 'Test Post'
    assert test_post.author.username == 'testuser'


# ✅ GOOD: Parametrized testing
@pytest.mark.django_db
@pytest.mark.parametrize('is_published,expected_count', [
    (True, 1),
    (False, 0),
])
def test_published_filter(is_published, expected_count):
    """Test published posts filter."""
    user = User.objects.create_user(username='test', password='pass')
    Post.objects.create(
        title='Test',
        author=user,
        is_published=is_published
    )
    assert Post.published.count() == expected_count
```

---

## View Testing

```python
from django.test import TestCase, Client
from django.urls import reverse

# ✅ GOOD: Test views thoroughly
class PostViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author=self.user
        )

    def test_post_list_view(self):
        """Test post list view."""
        response = self.client.get(reverse('post_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_list.html')
        self.assertContains(response, 'Test Post')
        self.assertIn('posts', response.context)

    def test_post_detail_view(self):
        """Test post detail view."""
        url = reverse('post_detail', kwargs={'pk': self.post.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['post'], self.post)

    def test_post_detail_404(self):
        """Test 404 for non-existent post."""
        url = reverse('post_detail', kwargs={'pk': 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_create_post_authenticated(self):
        """Test creating post when logged in."""
        self.client.login(username='testuser', password='testpass123')

        data = {
            'title': 'New Post',
            'content': 'New content'
        }
        response = self.client.post(reverse('post_create'), data)

        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Post.objects.count(), 2)
        new_post = Post.objects.latest('created_at')
        self.assertEqual(new_post.title, 'New Post')
        self.assertEqual(new_post.author, self.user)

    def test_create_post_unauthenticated(self):
        """Test creating post when not logged in."""
        data = {'title': 'New Post', 'content': 'New content'}
        response = self.client.post(reverse('post_create'), data)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_update_own_post(self):
        """Test updating own post."""
        self.client.login(username='testuser', password='testpass123')

        url = reverse('post_update', kwargs={'pk': self.post.pk})
        data = {'title': 'Updated Title', 'content': 'Updated content'}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Title')

    def test_cannot_update_others_post(self):
        """Test cannot update another user's post."""
        other_user = User.objects.create_user(username='other', password='pass')
        self.client.login(username='other', password='pass')

        url = reverse('post_update', kwargs={'pk': self.post.pk})
        data = {'title': 'Hacked', 'content': 'Hacked'}
        response = self.client.post(url, data)

        # Should get 403 or 404
        self.assertIn(response.status_code, [403, 404])
        self.post.refresh_from_db()
        self.assertNotEqual(self.post.title, 'Hacked')

    def test_delete_post(self):
        """Test deleting post."""
        self.client.login(username='testuser', password='testpass123')

        url = reverse('post_delete', kwargs={'pk': self.post.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.count(), 0)
```

### View Testing with pytest-django

```python
import pytest
from django.urls import reverse

# ✅ GOOD: Using client fixture
def test_post_list_view(client, test_post):
    """Test post list view."""
    response = client.get(reverse('post_list'))

    assert response.status_code == 200
    assert b'Test Post' in response.content


def test_post_detail_view(client, test_post):
    """Test post detail view."""
    url = reverse('post_detail', kwargs={'pk': test_post.pk})
    response = client.get(url)

    assert response.status_code == 200
    assert response.context['post'] == test_post


def test_post_detail_404(client, db):
    """Test 404 for non-existent post."""
    url = reverse('post_detail', kwargs={'pk': 9999})
    response = client.get(url)
    assert response.status_code == 404


def test_create_post_authenticated(client, test_user):
    """Test creating post when logged in."""
    client.force_login(test_user)

    data = {
        'title': 'New Post',
        'content': 'New content'
    }
    response = client.post(reverse('post_create'), data)

    assert response.status_code == 302  # Redirect after success
    assert Post.objects.count() == 1
    new_post = Post.objects.latest('created_at')
    assert new_post.title == 'New Post'
    assert new_post.author == test_user


def test_create_post_unauthenticated(client, db):
    """Test creating post when not logged in."""
    data = {'title': 'New Post', 'content': 'New content'}
    response = client.post(reverse('post_create'), data)

    # Should redirect to login
    assert response.status_code == 302
    assert '/login/' in response.url


def test_update_own_post(client, test_post):
    """Test updating own post."""
    client.force_login(test_post.author)

    url = reverse('post_update', kwargs={'pk': test_post.pk})
    data = {'title': 'Updated Title', 'content': 'Updated content'}
    response = client.post(url, data)

    assert response.status_code == 302
    test_post.refresh_from_db()
    assert test_post.title == 'Updated Title'


def test_cannot_update_others_post(client, test_post, db):
    """Test cannot update another user's post."""
    other_user = User.objects.create_user(username='other', password='pass')
    client.force_login(other_user)

    url = reverse('post_update', kwargs={'pk': test_post.pk})
    data = {'title': 'Hacked', 'content': 'Hacked'}
    response = client.post(url, data)

    # Should get 403 or 404
    assert response.status_code in [403, 404]
    test_post.refresh_from_db()
    assert test_post.title != 'Hacked'


def test_delete_post(client, test_post):
    """Test deleting post."""
    client.force_login(test_post.author)

    url = reverse('post_delete', kwargs={'pk': test_post.pk})
    response = client.post(url)

    assert response.status_code == 302
    assert Post.objects.count() == 0


# ✅ GOOD: Testing with RequestFactory
def test_view_with_request_factory(rf, test_user):
    """Test view logic directly without full HTTP cycle."""
    from myapp.views import post_list

    request = rf.get('/posts/')
    request.user = test_user

    response = post_list(request)
    assert response.status_code == 200
```

---

## API Testing (DRF)

```python
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

# ✅ GOOD: Test API endpoints
class PostAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author=self.user
        )

    def test_list_posts(self):
        """Test GET /api/posts/"""
        response = self.client.get('/api/posts/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_post(self):
        """Test GET /api/posts/{id}/"""
        response = self.client.get(f'/api/posts/{self.post.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Post')

    def test_create_post_authenticated(self):
        """Test POST /api/posts/ when authenticated."""
        self.client.force_authenticate(user=self.user)

        data = {'title': 'New Post', 'content': 'New content'}
        response = self.client.post('/api/posts/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(response.data['author'], self.user.id)

    def test_create_post_unauthenticated(self):
        """Test POST /api/posts/ when not authenticated."""
        data = {'title': 'New Post', 'content': 'New content'}
        response = self.client.post('/api/posts/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_post(self):
        """Test PUT /api/posts/{id}/"""
        self.client.force_authenticate(user=self.user)

        data = {'title': 'Updated', 'content': 'Updated content'}
        response = self.client.put(
            f'/api/posts/{self.post.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated')

    def test_partial_update_post(self):
        """Test PATCH /api/posts/{id}/"""
        self.client.force_authenticate(user=self.user)

        data = {'title': 'Patched Title'}
        response = self.client.patch(
            f'/api/posts/{self.post.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Patched Title')
        self.assertEqual(self.post.content, 'Test content')  # Unchanged

    def test_delete_post(self):
        """Test DELETE /api/posts/{id}/"""
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(f'/api/posts/{self.post.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)

    def test_filter_by_author(self):
        """Test filtering posts by author."""
        other_user = User.objects.create_user(username='other', password='pass')
        Post.objects.create(title='Other Post', author=other_user)

        response = self.client.get(f'/api/posts/?author={self.user.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['author'], self.user.id)

    def test_search_posts(self):
        """Test searching posts."""
        Post.objects.create(title='Django Tutorial', content='Learn Django', author=self.user)

        response = self.client.get('/api/posts/?search=Django')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
```

### API Testing with pytest-django

```python
import pytest
from rest_framework import status

# ✅ GOOD: API tests with pytest
@pytest.mark.django_db
def test_list_posts(client, test_post):
    """Test GET /api/posts/"""
    response = client.get('/api/posts/')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()['results']) == 1


@pytest.mark.django_db
def test_retrieve_post(client, test_post):
    """Test GET /api/posts/{id}/"""
    response = client.get(f'/api/posts/{test_post.id}/')

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['title'] == 'Test Post'


def test_create_post_authenticated(client, test_user):
    """Test POST /api/posts/ when authenticated."""
    client.force_login(test_user)

    data = {'title': 'New Post', 'content': 'New content'}
    response = client.post('/api/posts/', data, content_type='application/json')

    assert response.status_code == status.HTTP_201_CREATED
    assert Post.objects.count() == 1
    assert response.json()['author'] == test_user.id


def test_create_post_unauthenticated(client, db):
    """Test POST /api/posts/ when not authenticated."""
    data = {'title': 'New Post', 'content': 'New content'}
    response = client.post('/api/posts/', data, content_type='application/json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_post(client, test_post):
    """Test PUT /api/posts/{id}/"""
    client.force_login(test_post.author)

    data = {'title': 'Updated', 'content': 'Updated content'}
    response = client.put(
        f'/api/posts/{test_post.id}/',
        data,
        content_type='application/json'
    )

    assert response.status_code == status.HTTP_200_OK
    test_post.refresh_from_db()
    assert test_post.title == 'Updated'


def test_partial_update_post(client, test_post):
    """Test PATCH /api/posts/{id}/"""
    client.force_login(test_post.author)

    data = {'title': 'Patched Title'}
    response = client.patch(
        f'/api/posts/{test_post.id}/',
        data,
        content_type='application/json'
    )

    assert response.status_code == status.HTTP_200_OK
    test_post.refresh_from_db()
    assert test_post.title == 'Patched Title'
    assert test_post.content == 'Test content'  # Unchanged


def test_delete_post(client, test_post):
    """Test DELETE /api/posts/{id}/"""
    client.force_login(test_post.author)

    response = client.delete(f'/api/posts/{test_post.id}/')

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Post.objects.count() == 0


@pytest.mark.django_db
def test_filter_by_author(client, test_user):
    """Test filtering posts by author."""
    other_user = User.objects.create_user(username='other', password='pass')
    Post.objects.create(title='User Post', author=test_user)
    Post.objects.create(title='Other Post', author=other_user)

    response = client.get(f'/api/posts/?author={test_user.id}')

    assert response.status_code == status.HTTP_200_OK
    results = response.json()['results']
    assert len(results) == 1
    assert results[0]['author'] == test_user.id


@pytest.mark.django_db
def test_search_posts(client, test_user):
    """Test searching posts."""
    Post.objects.create(title='Django Tutorial', content='Learn Django', author=test_user)
    Post.objects.create(title='Python Guide', content='Learn Python', author=test_user)

    response = client.get('/api/posts/?search=Django')

    assert response.status_code == status.HTTP_200_OK
    results = response.json()['results']
    assert len(results) == 1
    assert 'Django' in results[0]['title']


# ✅ GOOD: Parametrized API testing
@pytest.mark.django_db
@pytest.mark.parametrize('endpoint,method,expected_status', [
    ('/api/posts/', 'get', status.HTTP_200_OK),
    ('/api/posts/', 'post', status.HTTP_401_UNAUTHORIZED),
])
def test_api_endpoints(client, endpoint, method, expected_status):
    """Test various API endpoints."""
    response = getattr(client, method)(endpoint)
    assert response.status_code == expected_status
```

---

## Fixtures and Factories

### Fixtures (JSON)

```python
# fixtures/test_data.json
[
    {
        "model": "auth.user",
        "pk": 1,
        "fields": {
            "username": "testuser",
            "email": "test@example.com"
        }
    },
    {
        "model": "blog.post",
        "pk": 1,
        "fields": {
            "title": "Test Post",
            "author": 1
        }
    }
]

# Using fixtures
class PostTest(TestCase):
    fixtures = ['test_data.json']

    def test_with_fixture(self):
        post = Post.objects.get(pk=1)
        self.assertEqual(post.title, 'Test Post')
```

### Factory Boy (Recommended)

```bash
pip install factory-boy
```

```python
# tests/factories.py
import factory
from factory.django import DjangoModelFactory

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')

class PostFactory(DjangoModelFactory):
    class Meta:
        model = Post

    title = factory.Faker('sentence', nb_words=5)
    content = factory.Faker('paragraph', nb_sentences=10)
    author = factory.SubFactory(UserFactory)
    is_published = True

class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    post = factory.SubFactory(PostFactory)
    author = factory.SubFactory(UserFactory)
    content = factory.Faker('paragraph')

# Usage in tests
class PostTest(TestCase):
    def test_create_post_with_factory(self):
        post = PostFactory()
        self.assertIsNotNone(post.id)
        self.assertIsNotNone(post.author)

    def test_create_multiple_posts(self):
        posts = PostFactory.create_batch(10)
        self.assertEqual(Post.objects.count(), 10)

    def test_custom_values(self):
        user = UserFactory(username='specific_user')
        post = PostFactory(author=user, title='Specific Title')
        self.assertEqual(post.author.username, 'specific_user')
```

### Factory Boy with pytest-django

```python
# conftest.py - pytest fixtures available to all tests
import pytest
from tests.factories import UserFactory, PostFactory

@pytest.fixture
def user():
    """Create a test user using factory."""
    return UserFactory()

@pytest.fixture
def post(user):
    """Create a test post using factory."""
    return PostFactory(author=user)

@pytest.fixture
def published_posts(user):
    """Create multiple published posts."""
    return PostFactory.create_batch(5, author=user, is_published=True)


# test_models.py - using the fixtures
def test_create_post_with_factory(post):
    """Test post creation with factory."""
    assert post.id is not None
    assert post.author is not None


def test_create_multiple_posts(published_posts):
    """Test multiple posts creation."""
    assert Post.objects.count() == 5
    assert all(p.is_published for p in published_posts)


def test_custom_values():
    """Test factory with custom values."""
    user = UserFactory(username='specific_user')
    post = PostFactory(author=user, title='Specific Title')
    assert post.author.username == 'specific_user'
    assert post.title == 'Specific Title'
```

**Rule**: Use Factory Boy over JSON fixtures for maintainability and flexibility.

---

## Mocking External Services

```python
from unittest.mock import patch, Mock

# ✅ GOOD: Mock external API calls
class PaymentTest(TestCase):
    @patch('myapp.payment.stripe.Charge.create')
    def test_process_payment(self, mock_charge):
        """Test payment processing."""
        # Configure mock
        mock_charge.return_value = Mock(
            id='ch_123',
            status='succeeded'
        )

        # Call function that uses Stripe
        result = process_payment(amount=1000, token='tok_123')

        # Verify mock was called
        mock_charge.assert_called_once_with(
            amount=1000,
            currency='usd',
            source='tok_123'
        )

        # Verify result
        self.assertTrue(result['success'])
        self.assertEqual(result['charge_id'], 'ch_123')

    @patch('myapp.tasks.send_email.delay')
    def test_user_registration_sends_email(self, mock_send_email):
        """Test registration sends welcome email."""
        user = User.objects.create_user(
            username='test',
            email='test@example.com',
            password='pass'
        )

        # Verify email task was called
        mock_send_email.assert_called_once_with(
            user_id=user.id,
            template='welcome'
        )
```

### Mocking with pytest-django

```python
import pytest
from unittest.mock import patch, Mock

# ✅ GOOD: Using pytest with mocks
@pytest.mark.django_db
@patch('myapp.payment.stripe.Charge.create')
def test_process_payment(mock_charge):
    """Test payment processing."""
    # Configure mock
    mock_charge.return_value = Mock(
        id='ch_123',
        status='succeeded'
    )

    # Call function that uses Stripe
    result = process_payment(amount=1000, token='tok_123')

    # Verify mock was called
    mock_charge.assert_called_once_with(
        amount=1000,
        currency='usd',
        source='tok_123'
    )

    # Verify result
    assert result['success'] is True
    assert result['charge_id'] == 'ch_123'


@pytest.mark.django_db
@patch('myapp.tasks.send_email.delay')
def test_user_registration_sends_email(mock_send_email):
    """Test registration sends welcome email."""
    user = User.objects.create_user(
        username='test',
        email='test@example.com',
        password='pass'
    )

    # Verify email task was called
    mock_send_email.assert_called_once_with(
        user_id=user.id,
        template='welcome'
    )


# ✅ GOOD: Using pytest-mock plugin
def test_with_mocker(mocker, db):
    """Test using pytest-mock plugin."""
    # pip install pytest-mock
    mock_send = mocker.patch('myapp.notifications.send_sms')

    send_notification(phone='+1234567890', message='Test')

    mock_send.assert_called_once_with(
        phone='+1234567890',
        message='Test'
    )
```

---

## Testing Forms

```python
from django.test import TestCase

class PostFormTest(TestCase):
    def test_valid_form(self):
        """Test form with valid data."""
        data = {
            'title': 'Test Post',
            'content': 'Test content'
        }
        form = PostForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_title(self):
        """Test form with missing required field."""
        data = {'content': 'Test content'}
        form = PostForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_invalid_form_title_too_long(self):
        """Test form with title exceeding max length."""
        data = {
            'title': 'x' * 201,
            'content': 'Test content'
        }
        form = PostForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
```

### Form Testing with pytest-django

```python
import pytest

def test_valid_form():
    """Test form with valid data."""
    data = {
        'title': 'Test Post',
        'content': 'Test content'
    }
    form = PostForm(data=data)
    assert form.is_valid()


def test_invalid_form_missing_title():
    """Test form with missing required field."""
    data = {'content': 'Test content'}
    form = PostForm(data=data)
    assert not form.is_valid()
    assert 'title' in form.errors


def test_invalid_form_title_too_long():
    """Test form with title exceeding max length."""
    data = {
        'title': 'x' * 201,
        'content': 'Test content'
    }
    form = PostForm(data=data)
    assert not form.is_valid()
    assert 'title' in form.errors


# ✅ GOOD: Parametrized form testing
@pytest.mark.parametrize('title,content,is_valid', [
    ('Valid', 'Valid content', True),
    ('', 'Valid content', False),  # Missing title
    ('Valid', '', False),  # Missing content
    ('x' * 201, 'Valid', False),  # Title too long
])
def test_post_form_validation(title, content, is_valid):
    """Test various form validation scenarios."""
    form = PostForm(data={'title': title, 'content': content})
    assert form.is_valid() == is_valid
```

---

## Coverage

```bash
pip install coverage
```

```bash
# Run tests with coverage
coverage run --source='.' manage.py test

# View coverage report
coverage report

# Generate HTML report
coverage html
# Open htmlcov/index.html in browser
```

```ini
# .coveragerc
[run]
omit =
    */migrations/*
    */tests/*
    */venv/*
    manage.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

### Coverage with pytest

```bash
# Install pytest-cov
pip install pytest-cov

# Run tests with coverage
pytest --cov=myapp

# Generate HTML report
pytest --cov=myapp --cov-report=html

# Coverage with minimum threshold
pytest --cov=myapp --cov-fail-under=80

# Show missing lines
pytest --cov=myapp --cov-report=term-missing
```

## Performance Testing

```python
from django.test import TestCase
from django.test.utils import override_settings
import time

class PerformanceTest(TestCase):
    def test_query_count(self):
        """Test number of queries."""
        PostFactory.create_batch(10)

        with self.assertNumQueries(2):  # Should be 2 queries max
            posts = Post.objects.select_related('author').all()
            list(posts)  # Force evaluation

    def test_response_time(self):
        """Test view response time."""
        start = time.time()
        response = self.client.get('/posts/')
        duration = time.time() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(duration, 0.5)  # Should respond in < 500ms
```

### Performance Testing with pytest

```python
import pytest
import time

@pytest.mark.django_db
def test_query_count(django_assert_num_queries):
    """Test number of queries."""
    PostFactory.create_batch(10)

    # Should be 2 queries max
    with django_assert_num_queries(2):
        posts = Post.objects.select_related('author').all()
        list(posts)  # Force evaluation


def test_response_time(client, test_post):
    """Test view response time."""
    start = time.time()
    response = client.get('/posts/')
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 0.5  # Should respond in < 500ms


@pytest.mark.django_db
def test_no_n_plus_one(django_assert_num_queries):
    """Test avoiding N+1 queries."""
    PostFactory.create_batch(10)

    # Should execute constant queries regardless of post count
    with django_assert_num_queries(3):
        posts = Post.objects.select_related('author').prefetch_related('comments')
        for post in posts:
            # Access related objects
            _ = post.author.username
            _ = list(post.comments.all())
```

---

## Advanced pytest Patterns

### Shared Fixtures with conftest.py

```python
# tests/conftest.py - Available to all test files
import pytest
from tests.factories import UserFactory, PostFactory

@pytest.fixture
def api_client():
    """DRF API client."""
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, user):
    """Authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def user(db):
    """Create test user."""
    return UserFactory()

@pytest.fixture
def admin_user(db):
    """Create admin user."""
    return UserFactory(is_staff=True, is_superuser=True)
```

### Custom Markers

```python
# pytest.ini
[pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    smoke: marks tests as smoke tests

# Usage in tests
@pytest.mark.slow
def test_expensive_operation(db):
    """This test takes a long time."""
    pass

@pytest.mark.integration
def test_full_workflow(client):
    """Integration test."""
    pass

# Run only fast tests
# pytest -m "not slow"

# Run only smoke tests
# pytest -m smoke
```

### Testing Settings Overrides

```python
def test_with_custom_setting(settings):
    """Test with modified settings."""
    settings.DEBUG = False
    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        }
    }
    # Test behavior with these settings


@pytest.mark.django_db
def test_email_sending(mailoutbox):
    """Test email is sent."""
    send_welcome_email('user@example.com')

    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ['user@example.com']
    assert 'Welcome' in mailoutbox[0].subject
```

### Testing Management Commands

```python
import pytest
from io import StringIO
from django.core.management import call_command

@pytest.mark.django_db
def test_management_command():
    """Test custom management command."""
    out = StringIO()
    call_command('import_posts', '--source=test.csv', stdout=out)

    assert 'Successfully imported' in out.getvalue()
    assert Post.objects.count() > 0


@pytest.mark.django_db
def test_command_with_error():
    """Test command error handling."""
    with pytest.raises(CommandError):
        call_command('import_posts', '--source=nonexistent.csv')
```

### Async View Testing

```python
import pytest

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_async_view(async_client):
    """Test async view."""
    response = await async_client.get('/async-endpoint/')
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_with_transactions(async_client):
    """Test async view with transaction support."""
    user = await User.objects.acreate(username='async_user')
    response = await async_client.get(f'/users/{user.id}/')
    assert response.status_code == 200
```

---

## Choosing Between Django TestCase and pytest-django

### Use Django TestCase when:
- Team is already familiar with unittest-style tests
- Working on legacy Django project with existing TestCase tests
- Prefer explicit class-based organization
- Need Django-specific test client features

### Use pytest-django when:
- Starting a new project
- Want less boilerplate code
- Need powerful fixtures and dependency injection
- Want parametrized testing
- Need to run tests in parallel easily
- Want to use pytest plugins ecosystem

### Can use both:
pytest can run Django TestCase tests, so you can gradually migrate or use both styles in the same project.

```bash
# pytest runs both styles
pytest  # Runs both TestCase classes and pytest functions
```

---

## Testing Best Practices Checklist

✅ Test one thing per test method/function
✅ Use descriptive test names (test_what_when_expected)
✅ Use Factory Boy instead of JSON fixtures
✅ Test both success and failure cases
✅ Test edge cases and boundary conditions
✅ Test permissions and authorization
✅ Mock external services (APIs, email, payment gateways)
✅ Use fixtures (pytest) or setUp() (TestCase) for reusable data
✅ Test database queries (assertNumQueries / django_assert_num_queries)
✅ Aim for >80% code coverage
✅ Run tests before committing code
✅ Use CI/CD to run tests automatically
✅ Keep tests fast (mock slow operations, use --reuse-db)
✅ Test what could break, not Django's built-in functionality
✅ Use parametrized tests to reduce duplication
✅ Organize tests in dedicated test directories
✅ Run tests in parallel (pytest -n auto)
✅ Use meaningful assertion messages

---

## Quick Reference

### Django TestCase
```python
from django.test import TestCase

class MyTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test')

    def test_something(self):
        self.assertEqual(self.user.username, 'test')
```

### pytest-django
```python
import pytest

@pytest.fixture
def user(db):
    return User.objects.create_user(username='test')

def test_something(user):
    assert user.username == 'test'
```

### Running Tests
```bash
# Django TestCase
python manage.py test

# pytest-django
pytest
pytest --reuse-db --no-migrations  # Faster
pytest -n auto  # Parallel
pytest -v  # Verbose
pytest -k "test_user"  # Run matching tests
pytest tests/test_models.py::test_create_user  # Specific test
```

---

**Remember**: Good tests give you confidence to refactor and catch bugs early. Write tests first (TDD) or immediately after implementation.
````

## File: .agents/skills/django-expert/references/views-and-urls.md
````markdown
# Django Views & URLs Best Practices

## Function-Based Views (FBV) vs Class-Based Views (CBV)

### When to Use Each

**Use Function-Based Views when:**
- Simple, straightforward logic
- Unique behavior that doesn't fit standard CRUD patterns
- You prefer explicit code over implicit behavior
- Handling a single HTTP method

**Use Class-Based Views when:**
- Standard CRUD operations (list, detail, create, update, delete)
- Sharing behavior across multiple views (mixins)
- Handling multiple HTTP methods on the same endpoint
- You want DRY code with Django's built-in generic views

## Function-Based Views

### Basic FBV Pattern

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required

# ✅ GOOD: Simple, explicit view
def blog_list(request):
    posts = Post.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'blog/list.html', {'posts': posts})

# ✅ GOOD: Handle form submission
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()

    return render(request, 'blog/create.html', {'form': form})

# ✅ GOOD: Protected view
@login_required
def user_dashboard(request):
    user_posts = Post.objects.filter(author=request.user)
    return render(request, 'dashboard.html', {'posts': user_posts})
```

### Handling Different HTTP Methods

```python
from django.views.decorators.http import require_http_methods, require_POST

# ✅ GOOD: Restrict to specific methods
@require_http_methods(["GET", "POST"])
def contact_form(request):
    if request.method == 'POST':
        # Handle form submission
        ...
    return render(request, 'contact.html')

# ✅ GOOD: POST-only view
@require_POST
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    post.delete()
    return redirect('blog_list')

# ❌ BAD: No method restriction
def delete_post(request, pk):
    # Can be triggered by GET request! (CSRF vulnerability)
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    return redirect('blog_list')
```

## Class-Based Views

### Generic Class-Based Views

```python
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

# ✅ GOOD: Simple list view
class PostListView(ListView):
    model = Post
    template_name = 'blog/list.html'
    context_object_name = 'posts'
    paginate_by = 20

    def get_queryset(self):
        return Post.objects.filter(is_published=True).select_related('author')

# ✅ GOOD: Detail view with related objects
class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return Post.objects.select_related('author').prefetch_related('comments')

# ✅ GOOD: Create view with form validation
class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

# ✅ GOOD: Update view with permission check
class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/edit.html'

    def get_queryset(self):
        # Only allow editing own posts
        return Post.objects.filter(author=self.request.user)

# ✅ GOOD: Delete view
class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('blog_list')

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)
```

### Custom Class-Based Views

```python
from django.views import View

# ✅ GOOD: Handle multiple methods
class PostTogglePublishView(LoginRequiredMixin, View):
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk, author=request.user)
        post.is_published = not post.is_published
        post.save()
        return JsonResponse({
            'success': True,
            'is_published': post.is_published
        })

# ✅ GOOD: API-like view
class PostAPIView(View):
    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        return JsonResponse({
            'id': post.id,
            'title': post.title,
            'content': post.content,
        })

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk, author=request.user)
        data = json.loads(request.body)
        post.title = data.get('title', post.title)
        post.save()
        return JsonResponse({'success': True})
```

## Mixins

Mixins add reusable functionality to CBVs.

### Built-in Mixins

```python
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin

# ✅ GOOD: Require login
class UserDashboardView(LoginRequiredMixin, ListView):
    model = Post
    login_url = '/login/'  # Where to redirect if not logged in

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)

# ✅ GOOD: Require specific permission
class PostCreateView(PermissionRequiredMixin, CreateView):
    model = Post
    permission_required = 'blog.add_post'
    # Redirects to login if permission denied

# ✅ GOOD: Custom permission check
class PostUpdateView(UserPassesTestMixin, UpdateView):
    model = Post

    def test_func(self):
        post = self.get_object()
        return post.author == self.request.user or self.request.user.is_staff
```

### Custom Mixins

```python
# ✅ GOOD: Reusable mixin for adding context
class PageTitleMixin:
    page_title = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.page_title
        return context

# ✅ GOOD: Mixin for filtering by author
class FilterByAuthorMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(author=self.request.user)

# Usage
class MyPostsView(FilterByAuthorMixin, PageTitleMixin, ListView):
    model = Post
    page_title = 'My Posts'
    template_name = 'blog/my_posts.html'
```

**Rule**: Mixins should go before the view class in inheritance order.

## URL Configuration

### URL Patterns

```python
from django.urls import path, include
from . import views

app_name = 'blog'  # ✅ GOOD: Namespace your URLs

urlpatterns = [
    # ✅ GOOD: Named URL patterns
    path('', views.PostListView.as_view(), name='post_list'),
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/create/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<int:pk>/edit/', views.PostUpdateView.as_view(), name='post_edit'),
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),

    # ✅ GOOD: Use path converters
    path('post/<slug:slug>/', views.post_detail_by_slug, name='post_by_slug'),
    path('category/<str:category>/', views.posts_by_category, name='posts_by_category'),
    path('archive/<int:year>/<int:month>/', views.archive, name='archive'),
]
```

### URL Converters

Built-in converters:
- `<int:name>` - Matches integers
- `<str:name>` - Matches non-empty strings (excluding '/')
- `<slug:name>` - Matches slugs (letters, numbers, hyphens, underscores)
- `<uuid:name>` - Matches UUIDs
- `<path:name>` - Matches any string (including '/')

```python
# Custom converter
class YearConverter:
    regex = '[0-9]{4}'

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return f'{value:04d}'

# Register it
from django.urls import register_converter
register_converter(YearConverter, 'year')

# Use it
path('archive/<year:year>/', views.archive, name='archive')
```

### Including Other URLconfs

```python
# project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('blog/', include('blog.urls')),  # ✅ GOOD: Prefix app URLs
    path('api/', include('api.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # Login/logout
]
```

### Reverse URL Resolution

```python
from django.urls import reverse
from django.shortcuts import redirect

# ✅ GOOD: Use reverse() in views
def my_view(request):
    return redirect(reverse('blog:post_list'))

# ✅ GOOD: With arguments
def after_create(request, post):
    return redirect(reverse('blog:post_detail', kwargs={'pk': post.pk}))

# ✅ GOOD: In templates
# <a href="{% url 'blog:post_detail' pk=post.pk %}">View Post</a>
```

**Rule**: Never hardcode URLs. Always use `reverse()` in Python and `{% url %}` in templates.

## Context and Template Rendering

### Adding Context to Views

```python
# Function-based view
def blog_list(request):
    posts = Post.objects.filter(is_published=True)
    categories = Category.objects.all()

    context = {
        'posts': posts,
        'categories': categories,
        'page_title': 'Blog Posts',
    }
    return render(request, 'blog/list.html', context)

# Class-based view
class PostListView(ListView):
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['page_title'] = 'Blog Posts'
        return context
```

### Context Processors

For data needed across ALL templates:

```python
# blog/context_processors.py
def blog_stats(request):
    return {
        'total_posts': Post.objects.count(),
        'total_published': Post.objects.filter(is_published=True).count(),
    }

# settings.py
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                ...
                'blog.context_processors.blog_stats',
            ],
        },
    },
]
```

**Rule**: Only use context processors for truly global data. Don't overuse them.

## HTTP Responses

### Response Types

```python
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect

# ✅ GOOD: HTML response
def blog_list(request):
    posts = Post.objects.all()
    return render(request, 'blog/list.html', {'posts': posts})

# ✅ GOOD: JSON response
def post_api(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return JsonResponse({
        'id': post.id,
        'title': post.title,
        'content': post.content,
    })

# ✅ GOOD: Redirect
def old_url(request):
    return redirect('new_url_name')

# ✅ GOOD: 404 error
def post_detail(request, pk):
    try:
        post = Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        raise Http404("Post not found")

    return render(request, 'blog/detail.html', {'post': post})

# ✅ BETTER: Use get_object_or_404
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/detail.html', {'post': post})
```

### Custom Response Status Codes

```python
from django.http import HttpResponse

# 201 Created
def create_post(request):
    post = Post.objects.create(...)
    return HttpResponse('Created', status=201)

# 204 No Content
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    return HttpResponse(status=204)

# 400 Bad Request
def api_view(request):
    if not request.POST.get('required_field'):
        return JsonResponse({'error': 'Missing field'}, status=400)
    ...

# 403 Forbidden
from django.http import HttpResponseForbidden

def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return HttpResponseForbidden('You cannot delete this post')
    ...
```

## Error Handling

### Custom Error Pages

```python
# views.py
def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)

# urls.py
handler404 = 'blog.views.custom_404'
handler500 = 'blog.views.custom_500'
```

### Exception Handling in Views

```python
from django.core.exceptions import ValidationError, PermissionDenied
import logging

logger = logging.getLogger(__name__)

# ✅ GOOD: Handle specific exceptions
def process_payment(request):
    try:
        result = payment_service.charge(request.POST)
        return JsonResponse({'success': True})
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except PermissionDenied:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    except Exception as e:
        logger.exception("Payment processing failed")
        return JsonResponse({'error': 'Server error'}, status=500)
```

## Middleware

Middleware processes requests/responses globally.

### Custom Middleware

```python
# middleware.py
class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request before view
        logger.info(f"{request.method} {request.path}")

        # Call the view
        response = self.get_response(request)

        # Process response after view
        logger.info(f"Response: {response.status_code}")

        return response

# settings.py
MIDDLEWARE = [
    ...
    'blog.middleware.RequestLoggingMiddleware',
]
```

### Common Middleware Patterns

```python
# Add custom header to all responses
class CustomHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Custom-Header'] = 'value'
        return response

# Block requests from specific IPs
class IPBlockMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.blocked_ips = ['192.168.1.1']

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR')
        if ip in self.blocked_ips:
            return HttpResponseForbidden('Access denied')
        return self.get_response(request)
```

## Decorators

### Common View Decorators

```python
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required, permission_required

# ✅ GOOD: Combine decorators
@login_required
@require_POST
def delete_post(request, pk):
    ...

# ✅ GOOD: Cache view for 5 minutes
@cache_page(60 * 5)
def blog_list(request):
    posts = Post.objects.all()
    return render(request, 'blog/list.html', {'posts': posts})

# ✅ GOOD: Require permission
@permission_required('blog.add_post')
def create_post(request):
    ...
```

### Custom Decorators

```python
from functools import wraps

# ✅ GOOD: Custom decorator for AJAX-only views
def ajax_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return HttpResponseBadRequest('AJAX required')
        return view_func(request, *args, **kwargs)
    return wrapper

# Usage
@ajax_required
def get_comments(request, post_id):
    comments = Comment.objects.filter(post_id=post_id)
    return JsonResponse({'comments': list(comments.values())})
```

## View Best Practices Checklist

✅ Use `get_object_or_404()` instead of try/except
✅ Always validate user permissions (authentication ≠ authorization)
✅ Use `select_related()` and `prefetch_related()` to avoid N+1 queries
✅ Name all URL patterns for easier maintenance
✅ Use namespaces (`app_name`) in URL configurations
✅ Validate form data before saving
✅ Return appropriate HTTP status codes
✅ Log errors and security-relevant events
✅ Use CSRF protection on all POST/PUT/DELETE views
✅ Add caching to expensive views when appropriate
✅ Keep views focused (single responsibility)
✅ Extract complex logic into model methods or services

---

**Remember**: Views should be thin - they orchestrate, they don't contain business logic. Put complex logic in models, managers, or service modules.
````

## File: .agents/skills/django-expert/SKILL.md
````markdown
---
name: django-expert
description: Expert Django backend development guidance. Use when creating Django models, views, serializers, or APIs; debugging ORM queries or migrations; optimizing database performance; implementing authentication; writing tests; or working with Django REST Framework. Follows Django best practices and modern patterns.
---

# Django Expert

## Overview

This skill provides expert guidance for Django backend development with comprehensive coverage of models, views, Django REST Framework, forms, authentication, testing, and performance optimization. It follows official Django best practices and modern Python conventions to help you build robust, maintainable applications.

**Key Capabilities:**
- Model design with optimal ORM patterns
- View implementation (FBV, CBV, DRF viewsets)
- Django REST Framework API development
- Query optimization and performance tuning
- Authentication and permissions
- Testing strategies and patterns
- Security best practices

## When to Use

Invoke this skill when you encounter these triggers:

**Model & Database Work:**
- "Create a Django model for..."
- "Optimize this queryset/database query"
- "Generate migrations for..."
- "Design database schema for..."
- "Fix N+1 query problem"

**View & API Development:**
- "Create an API endpoint for..."
- "Build a Django view that..."
- "Implement DRF serializer/viewset"
- "Add filtering/pagination to API"

**Authentication & Security:**
- "Implement authentication/permissions"
- "Create custom user model"
- "Secure this endpoint/view"

**Testing & Quality:**
- "Write tests for this Django app"
- "Debug this Django error/issue"
- "Review Django code for issues"

**Performance & Optimization:**
- "This Django view is slow"
- "Optimize database queries"
- "Add caching to..."

**Production Deployment:**
- "Deploy Django to production"
- "Configure Django for production"
- "Set up HTTPS/SSL for Django"
- "Production settings checklist"
- "Configure production database/cache"

## Instructions

Follow this workflow when handling Django development requests:

### 1. Analyze the Request and Gather Context

**Identify the task type:**
- Model design (database schema, relationships, migrations)
- View/API development (FBV, CBV, DRF viewsets, serializers)
- Query optimization (N+1 problems, database performance)
- Authentication/permissions (user models, access control)
- Testing (unit tests, integration tests, fixtures)
- Security review (CSRF, XSS, SQL injection, permissions)
- Production deployment (settings, HTTPS, database, caching, monitoring)
- Template rendering (Django templates, context processors)

**Leverage available context:**
- If `django-ai-boost` MCP server is available, use it to understand project structure and existing patterns
- Read relevant existing code to understand conventions
- Check Django version for compatibility considerations

### 2. Load Relevant Reference Documentation

Based on the task type, reference the appropriate bundled documentation:

- **Models/ORM work** -> `references/models-and-orm.md`
  - Model design patterns and field choices
  - Relationship configurations (ForeignKey, ManyToMany)
  - Custom managers and QuerySet methods
  - Migration strategies

- **View/API development** -> `references/views-and-urls.md` + `references/drf-guidelines.md`
  - FBV vs CBV decision criteria
  - DRF serializers, viewsets, and routers
  - URL configuration patterns
  - Middleware and request/response handling

- **Performance issues** -> `references/performance-optimization.md`
  - Query optimization techniques (select_related, prefetch_related)
  - Caching strategies (Redis, Memcached, database caching)
  - Database indexing and query profiling
  - Connection pooling and async patterns

- **Production deployment** -> `references/production-deployment.md`
  - Critical settings (DEBUG, SECRET_KEY, ALLOWED_HOSTS)
  - HTTPS and SSL/TLS configuration
  - Database and cache configuration
  - Static/media file serving
  - Error monitoring and logging
  - Deployment process and health checks

- **Security concerns** -> `references/security-checklist.md`
  - CSRF/XSS/SQL injection prevention
  - Authentication and authorization patterns
  - Secure configuration practices
  - Input validation and sanitization

- **Testing tasks** -> `references/testing-strategies.md`
  - Test structure and organization
  - Fixtures and factories
  - Mocking external dependencies
  - Coverage and CI/CD integration

### 3. Implement Following Django Best Practices

**Code quality standards:**
- Follow PEP 8 and Django coding style
- Use Django built-ins over third-party packages when possible
- Keep views thin, use services/managers for business logic
- Write descriptive variable names and add docstrings for complex logic
- Handle errors gracefully with appropriate exceptions

**Django-specific patterns:**
- Use `select_related()` for FK/OneToOne, `prefetch_related()` for reverse FK/M2M
- Leverage class-based views and mixins for code reuse
- Use Django forms/serializers for validation
- Follow Django's migration workflow (never edit applied migrations)
- Use Django's built-in security features (CSRF tokens, auth decorators)

**API development (DRF):**
- Use ModelSerializer for standard CRUD operations
- Implement proper pagination and filtering
- Use appropriate permission classes
- Follow RESTful conventions for endpoints
- Version APIs when making breaking changes

### 4. Validate and Test

Before presenting the solution:

**Code review:**
- Check for N+1 query problems (use Django Debug Toolbar mentally)
- Verify proper error handling and edge cases
- Ensure security best practices are followed
- Confirm migrations are clean and reversible

**Testing considerations:**
- Suggest or write appropriate tests for new functionality
- Verify test coverage for critical paths
- Check that fixtures/factories are maintainable

**Performance check:**
- Review database queries for efficiency
- Consider caching opportunities
- Verify proper use of database indexes

## Bundled Resources

**references/** - Comprehensive Django documentation loaded into context as needed

These reference files provide detailed guidance beyond this SKILL.md overview:

- **`references/models-and-orm.md`** (~11k words)
  - Model field types and best practices
  - Relationship configurations (ForeignKey, OneToOne, ManyToMany)
  - Custom managers and QuerySet methods
  - Migration patterns and common pitfalls
  - Database-level constraints and indexes

- **`references/views-and-urls.md`** (~17k words)
  - Function-based vs class-based view trade-offs
  - CBV mixins and inheritance patterns
  - URL routing and reverse resolution
  - Middleware implementation
  - Request/response lifecycle

- **`references/drf-guidelines.md`** (~18k words)
  - Serializer patterns (ModelSerializer, nested serializers)
  - ViewSet and router configurations
  - Pagination, filtering, and search
  - Authentication and permission classes
  - API versioning strategies
  - Performance optimization for APIs

- **`references/testing-strategies.md`** (~18k words)
  - Test organization and structure
  - Factory patterns vs fixtures
  - Testing views, models, and serializers
  - Mocking external services
  - Test database optimization
  - CI/CD integration

- **`references/security-checklist.md`** (~12k words)
  - CSRF protection implementation
  - XSS prevention techniques
  - SQL injection defense
  - Authentication best practices
  - Permission and authorization patterns
  - Secure settings configuration

- **`references/performance-optimization.md`** (~14k words)
  - Query optimization (select_related, prefetch_related, only, defer)
  - Database indexing strategies
  - Caching layers (Redis, Memcached, database cache)
  - Database connection pooling
  - Profiling and monitoring tools
  - Async views and background tasks

- **`references/production-deployment.md`** (~20k words)
  - Critical settings (DEBUG, SECRET_KEY, ALLOWED_HOSTS)
  - Database configuration and connection pooling
  - HTTPS/SSL configuration and security headers
  - Static and media file serving
  - Caching with Redis/Memcached
  - Email configuration for production
  - Error monitoring with Sentry
  - Logging and health checks
  - Zero-downtime deployment strategies

- **`references/examples.md`** - Practical implementation examples
  - Model design with custom managers
  - N+1 query optimization
  - DRF API endpoint implementation
  - Writing Django tests

## Additional Notes

**Django Version Compatibility:**
- Consider LTS releases (4.2, 5.2) for production
- Check deprecation warnings when upgrading
- Use `django-upgrade` tool for automated migration

**Common Pitfalls to Avoid:**
- Circular imports (use lazy references)
- Missing `related_name` on relationships
- Forgetting database indexes on frequently queried fields
- Using `get()` without exception handling
- N+1 queries in templates and serializers
````

## File: .agents/skills/django-patterns/SKILL.md
````markdown
---
name: django-patterns
description: Django architecture patterns, REST API design with DRF, ORM best practices, caching, signals, middleware, and production-grade Django apps.
origin: ECC
---

# Django Development Patterns

Production-grade Django architecture patterns for scalable, maintainable applications.

## When to Activate

- Building Django web applications
- Designing Django REST Framework APIs
- Working with Django ORM and models
- Setting up Django project structure
- Implementing caching, signals, middleware

## Project Structure

### Recommended Layout

```
myproject/
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py          # Base settings
│   │   ├── development.py   # Dev settings
│   │   ├── production.py    # Production settings
│   │   └── test.py          # Test settings
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── manage.py
└── apps/
    ├── __init__.py
    ├── users/
    │   ├── __init__.py
    │   ├── models.py
    │   ├── views.py
    │   ├── serializers.py
    │   ├── urls.py
    │   ├── permissions.py
    │   ├── filters.py
    │   ├── services.py
    │   └── tests/
    └── products/
        └── ...
```

### Split Settings Pattern

```python
# config/settings/base.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    # Local apps
    'apps.users',
    'apps.products',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# config/settings/development.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES['default']['NAME'] = 'myproject_dev'

INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# config/settings/production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}
```

## Model Design Patterns

### Model Best Practices

```python
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    """Custom user model extending AbstractUser."""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

class Product(models.Model):
    """Product model with proper field configuration."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=250)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        related_name='products'
    )
    tags = models.ManyToManyField('Tag', blank=True, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['category', 'is_active']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(price__gte=0),
                name='price_non_negative'
            )
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
```

### QuerySet Best Practices

```python
from django.db import models

class ProductQuerySet(models.QuerySet):
    """Custom QuerySet for Product model."""

    def active(self):
        """Return only active products."""
        return self.filter(is_active=True)

    def with_category(self):
        """Select related category to avoid N+1 queries."""
        return self.select_related('category')

    def with_tags(self):
        """Prefetch tags for many-to-many relationship."""
        return self.prefetch_related('tags')

    def in_stock(self):
        """Return products with stock > 0."""
        return self.filter(stock__gt=0)

    def search(self, query):
        """Search products by name or description."""
        return self.filter(
            models.Q(name__icontains=query) |
            models.Q(description__icontains=query)
        )

class Product(models.Model):
    # ... fields ...

    objects = ProductQuerySet.as_manager()  # Use custom QuerySet

# Usage
Product.objects.active().with_category().in_stock()
```

### Manager Methods

```python
class ProductManager(models.Manager):
    """Custom manager for complex queries."""

    def get_or_none(self, **kwargs):
        """Return object or None instead of DoesNotExist."""
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None

    def create_with_tags(self, name, price, tag_names):
        """Create product with associated tags."""
        product = self.create(name=name, price=price)
        tags = [Tag.objects.get_or_create(name=name)[0] for name in tag_names]
        product.tags.set(tags)
        return product

    def bulk_update_stock(self, product_ids, quantity):
        """Bulk update stock for multiple products."""
        return self.filter(id__in=product_ids).update(stock=quantity)

# In model
class Product(models.Model):
    # ... fields ...
    custom = ProductManager()
```

## Django REST Framework Patterns

### Serializer Patterns

```python
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Product, User

class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    discount_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price',
            'discount_price', 'stock', 'category_name',
            'average_rating', 'created_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at']

    def get_discount_price(self, obj):
        """Calculate discount price if applicable."""
        if hasattr(obj, 'discount') and obj.discount:
            return obj.price * (1 - obj.discount.percent / 100)
        return obj.price

    def validate_price(self, value):
        """Ensure price is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating products."""

    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'category']

    def validate(self, data):
        """Custom validation for multiple fields."""
        if data['price'] > 10000 and data['stock'] > 100:
            raise serializers.ValidationError(
                "Cannot have high-value products with large stock."
            )
        return data

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm']

    def validate(self, data):
        """Validate passwords match."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Password fields didn't match."
            })
        return data

    def create(self, validated_data):
        """Create user with hashed password."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user
```

### ViewSet Patterns

```python
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product
from .serializers import ProductSerializer, ProductCreateSerializer
from .permissions import IsOwnerOrReadOnly
from .filters import ProductFilter
from .services import ProductService

class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product model."""

    queryset = Product.objects.select_related('category').prefetch_related('tags')
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ProductCreateSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        """Save with user context."""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Return featured products."""
        featured = self.queryset.filter(is_featured=True)[:10]
        serializer = self.get_serializer(featured, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def purchase(self, request, pk=None):
        """Purchase a product."""
        product = self.get_object()
        service = ProductService()
        result = service.purchase(product, request.user)
        return Response(result, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_products(self, request):
        """Return products created by current user."""
        products = self.queryset.filter(created_by=request.user)
        page = self.paginate_queryset(products)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
```

### Custom Actions

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    """Add product to user cart."""
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity', 1)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    cart, _ = Cart.objects.get_or_create(user=request.user)
    CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=quantity
    )

    return Response({'message': 'Added to cart'}, status=status.HTTP_201_CREATED)
```

## Service Layer Pattern

```python
# apps/orders/services.py
from typing import Optional
from django.db import transaction
from .models import Order, OrderItem

class OrderService:
    """Service layer for order-related business logic."""

    @staticmethod
    @transaction.atomic
    def create_order(user, cart: Cart) -> Order:
        """Create order from cart."""
        order = Order.objects.create(
            user=user,
            total_price=cart.total_price
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        # Clear cart
        cart.items.all().delete()

        return order

    @staticmethod
    def process_payment(order: Order, payment_data: dict) -> bool:
        """Process payment for order."""
        # Integration with payment gateway
        payment = PaymentGateway.charge(
            amount=order.total_price,
            token=payment_data['token']
        )

        if payment.success:
            order.status = Order.Status.PAID
            order.save()
            # Send confirmation email
            OrderService.send_confirmation_email(order)
            return True

        return False

    @staticmethod
    def send_confirmation_email(order: Order):
        """Send order confirmation email."""
        # Email sending logic
        pass
```

## Caching Strategies

### View-Level Caching

```python
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

@method_decorator(cache_page(60 * 15), name='dispatch')  # 15 minutes
class ProductListView(generic.ListView):
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
```

### Template Fragment Caching

```django
{% load cache %}
{% cache 500 sidebar %}
    ... expensive sidebar content ...
{% endcache %}
```

### Low-Level Caching

```python
from django.core.cache import cache

def get_featured_products():
    """Get featured products with caching."""
    cache_key = 'featured_products'
    products = cache.get(cache_key)

    if products is None:
        products = list(Product.objects.filter(is_featured=True))
        cache.set(cache_key, products, timeout=60 * 15)  # 15 minutes

    return products
```

### QuerySet Caching

```python
from django.core.cache import cache

def get_popular_categories():
    cache_key = 'popular_categories'
    categories = cache.get(cache_key)

    if categories is None:
        categories = list(Category.objects.annotate(
            product_count=Count('products')
        ).filter(product_count__gt=10).order_by('-product_count')[:20])
        cache.set(cache_key, categories, timeout=60 * 60)  # 1 hour

    return categories
```

## Signals

### Signal Patterns

```python
# apps/users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create profile when user is created."""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save profile when user is saved."""
    instance.profile.save()

# apps/users/apps.py
from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'

    def ready(self):
        """Import signals when app is ready."""
        import apps.users.signals
```

## Middleware

### Custom Middleware

```python
# middleware/active_user_middleware.py
import time
from django.utils.deprecation import MiddlewareMixin

class ActiveUserMiddleware(MiddlewareMixin):
    """Middleware to track active users."""

    def process_request(self, request):
        """Process incoming request."""
        if request.user.is_authenticated:
            # Update last active time
            request.user.last_active = timezone.now()
            request.user.save(update_fields=['last_active'])

class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware for logging requests."""

    def process_request(self, request):
        """Log request start time."""
        request.start_time = time.time()

    def process_response(self, request, response):
        """Log request duration."""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(f'{request.method} {request.path} - {response.status_code} - {duration:.3f}s')
        return response
```

## Performance Optimization

### N+1 Query Prevention

```python
# Bad - N+1 queries
products = Product.objects.all()
for product in products:
    print(product.category.name)  # Separate query for each product

# Good - Single query with select_related
products = Product.objects.select_related('category').all()
for product in products:
    print(product.category.name)

# Good - Prefetch for many-to-many
products = Product.objects.prefetch_related('tags').all()
for product in products:
    for tag in product.tags.all():
        print(tag.name)
```

### Database Indexing

```python
class Product(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['category', 'created_at']),
        ]
```

### Bulk Operations

```python
# Bulk create
Product.objects.bulk_create([
    Product(name=f'Product {i}', price=10.00)
    for i in range(1000)
])

# Bulk update
products = Product.objects.all()[:100]
for product in products:
    product.is_active = True
Product.objects.bulk_update(products, ['is_active'])

# Bulk delete
Product.objects.filter(stock=0).delete()
```

## Quick Reference

| Pattern | Description |
|---------|-------------|
| Split settings | Separate dev/prod/test settings |
| Custom QuerySet | Reusable query methods |
| Service Layer | Business logic separation |
| ViewSet | REST API endpoints |
| Serializer validation | Request/response transformation |
| select_related | Foreign key optimization |
| prefetch_related | Many-to-many optimization |
| Cache first | Cache expensive operations |
| Signals | Event-driven actions |
| Middleware | Request/response processing |

Remember: Django provides many shortcuts, but for production applications, structure and organization matter more than concise code. Build for maintainability.
````

## File: .agents/skills/django-security/SKILL.md
````markdown
---
name: django-security
description: Django security best practices, authentication, authorization, CSRF protection, SQL injection prevention, XSS prevention, and secure deployment configurations.
origin: ECC
---

# Django Security Best Practices

Comprehensive security guidelines for Django applications to protect against common vulnerabilities.

## When to Activate

- Setting up Django authentication and authorization
- Implementing user permissions and roles
- Configuring production security settings
- Reviewing Django application for security issues
- Deploying Django applications to production

## Core Security Settings

### Production Settings Configuration

```python
# settings/production.py
import os

DEBUG = False  # CRITICAL: Never use True in production

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Security headers
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS and Cookies
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Secret key (must be set via environment variable)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured('DJANGO_SECRET_KEY environment variable is required')

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

## Authentication

### Custom User Model

```python
# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Custom user model for better security."""

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)

    USERNAME_FIELD = 'email'  # Use email as username
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

# settings/base.py
AUTH_USER_MODEL = 'users.User'
```

### Password Hashing

```python
# Django uses PBKDF2 by default. For stronger security:
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]
```

### Session Management

```python
# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'  # Or 'db'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 3600 * 24 * 7  # 1 week
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Better UX, but less secure
```

## Authorization

### Permissions

```python
# models.py
from django.db import models
from django.contrib.auth.models import Permission

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        permissions = [
            ('can_publish', 'Can publish posts'),
            ('can_edit_others', 'Can edit posts of others'),
        ]

    def user_can_edit(self, user):
        """Check if user can edit this post."""
        return self.author == user or user.has_perm('app.can_edit_others')

# views.py
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import UpdateView

class PostUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Post
    permission_required = 'app.can_edit_others'
    raise_exception = True  # Return 403 instead of redirect

    def get_queryset(self):
        """Only allow users to edit their own posts."""
        return Post.objects.filter(author=self.request.user)
```

### Custom Permissions

```python
# permissions.py
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow only owners to edit objects."""

    def has_object_permission(self, request, view, obj):
        # Read permissions allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for owner
        return obj.author == request.user

class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow admins to do anything, others read-only."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsVerifiedUser(permissions.BasePermission):
    """Allow only verified users."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_verified
```

### Role-Based Access Control (RBAC)

```python
# models.py
from django.contrib.auth.models import AbstractUser, Group

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('moderator', 'Moderator'),
        ('user', 'Regular User'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    def is_admin(self):
        return self.role == 'admin' or self.is_superuser

    def is_moderator(self):
        return self.role in ['admin', 'moderator']

# Mixins
class AdminRequiredMixin:
    """Mixin to require admin role."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin():
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
```

## SQL Injection Prevention

### Django ORM Protection

```python
# GOOD: Django ORM automatically escapes parameters
def get_user(username):
    return User.objects.get(username=username)  # Safe

# GOOD: Using parameters with raw()
def search_users(query):
    return User.objects.raw('SELECT * FROM users WHERE username = %s', [query])

# BAD: Never directly interpolate user input
def get_user_bad(username):
    return User.objects.raw(f'SELECT * FROM users WHERE username = {username}')  # VULNERABLE!

# GOOD: Using filter with proper escaping
def get_users_by_email(email):
    return User.objects.filter(email__iexact=email)  # Safe

# GOOD: Using Q objects for complex queries
from django.db.models import Q
def search_users_complex(query):
    return User.objects.filter(
        Q(username__icontains=query) |
        Q(email__icontains=query)
    )  # Safe
```

### Extra Security with raw()

```python
# If you must use raw SQL, always use parameters
User.objects.raw(
    'SELECT * FROM users WHERE email = %s AND status = %s',
    [user_input_email, status]
)
```

## XSS Prevention

### Template Escaping

```django
{# Django auto-escapes variables by default - SAFE #}
{{ user_input }}  {# Escaped HTML #}

{# Explicitly mark safe only for trusted content #}
{{ trusted_html|safe }}  {# Not escaped #}

{# Use template filters for safe HTML #}
{{ user_input|escape }}  {# Same as default #}
{{ user_input|striptags }}  {# Remove all HTML tags #}

{# JavaScript escaping #}
<script>
    var username = {{ username|escapejs }};
</script>
```

### Safe String Handling

```python
from django.utils.safestring import mark_safe
from django.utils.html import escape

# BAD: Never mark user input as safe without escaping
def render_bad(user_input):
    return mark_safe(user_input)  # VULNERABLE!

# GOOD: Escape first, then mark safe
def render_good(user_input):
    return mark_safe(escape(user_input))

# GOOD: Use format_html for HTML with variables
from django.utils.html import format_html

def greet_user(username):
    return format_html('<span class="user">{}</span>', escape(username))
```

### HTTP Headers

```python
# settings.py
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME sniffing
SECURE_BROWSER_XSS_FILTER = True  # Enable XSS filter
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking

# Custom middleware
from django.conf import settings

class SecurityHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Content-Security-Policy'] = "default-src 'self'"
        return response
```

## CSRF Protection

### Default CSRF Protection

```python
# settings.py - CSRF is enabled by default
CSRF_COOKIE_SECURE = True  # Only send over HTTPS
CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access
CSRF_COOKIE_SAMESITE = 'Lax'  # Prevent CSRF in some cases
CSRF_TRUSTED_ORIGINS = ['https://example.com']  # Trusted domains

# Template usage
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Submit</button>
</form>

# AJAX requests
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

fetch('/api/endpoint/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
});
```

### Exempting Views (Use Carefully)

```python
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # Only use when absolutely necessary!
def webhook_view(request):
    # Webhook from external service
    pass
```

## File Upload Security

### File Validation

```python
import os
from django.core.exceptions import ValidationError

def validate_file_extension(value):
    """Validate file extension."""
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')

def validate_file_size(value):
    """Validate file size (max 5MB)."""
    filesize = value.size
    if filesize > 5 * 1024 * 1024:
        raise ValidationError('File too large. Max size is 5MB.')

# models.py
class Document(models.Model):
    file = models.FileField(
        upload_to='documents/',
        validators=[validate_file_extension, validate_file_size]
    )
```

### Secure File Storage

```python
# settings.py
MEDIA_ROOT = '/var/www/media/'
MEDIA_URL = '/media/'

# Use a separate domain for media in production
MEDIA_DOMAIN = 'https://media.example.com'

# Don't serve user uploads directly
# Use whitenoise or a CDN for static files
# Use a separate server or S3 for media files
```

## API Security

### Rate Limiting

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'upload': '10/hour',
    }
}

# Custom throttle
from rest_framework.throttling import UserRateThrottle

class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'
    rate = '60/min'

class SustainedRateThrottle(UserRateThrottle):
    scope = 'sustained'
    rate = '1000/day'
```

### Authentication for APIs

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({'message': 'You are authenticated'})
```

## Security Headers

### Content Security Policy

```python
# settings.py
CSP_DEFAULT_SRC = "'self'"
CSP_SCRIPT_SRC = "'self' https://cdn.example.com"
CSP_STYLE_SRC = "'self' 'unsafe-inline'"
CSP_IMG_SRC = "'self' data: https:"
CSP_CONNECT_SRC = "'self' https://api.example.com"

# Middleware
class CSPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = (
            f"default-src {CSP_DEFAULT_SRC}; "
            f"script-src {CSP_SCRIPT_SRC}; "
            f"style-src {CSP_STYLE_SRC}; "
            f"img-src {CSP_IMG_SRC}; "
            f"connect-src {CSP_CONNECT_SRC}"
        )
        return response
```

## Environment Variables

### Managing Secrets

```python
# Use python-decouple or django-environ
import environ

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

# reading .env file
environ.Env.read_env()

SECRET_KEY = env('DJANGO_SECRET_KEY')
DATABASE_URL = env('DATABASE_URL')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# .env file (never commit this)
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
ALLOWED_HOSTS=example.com,www.example.com
```

## Logging Security Events

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/security.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
```

## Quick Security Checklist

| Check | Description |
|-------|-------------|
| `DEBUG = False` | Never run with DEBUG in production |
| HTTPS only | Force SSL, secure cookies |
| Strong secrets | Use environment variables for SECRET_KEY |
| Password validation | Enable all password validators |
| CSRF protection | Enabled by default, don't disable |
| XSS prevention | Django auto-escapes, don't use `&#124;safe` with user input |
| SQL injection | Use ORM, never concatenate strings in queries |
| File uploads | Validate file type and size |
| Rate limiting | Throttle API endpoints |
| Security headers | CSP, X-Frame-Options, HSTS |
| Logging | Log security events |
| Updates | Keep Django and dependencies updated |

Remember: Security is a process, not a product. Regularly review and update your security practices.
````

## File: .agents/skills/python-executor/SKILL.md
````markdown
---
name: python-executor
description: "Execute Python code in a safe sandboxed environment via [inference.sh](https://inference.sh). Pre-installed: NumPy, Pandas, Matplotlib, requests, BeautifulSoup, Selenium, Playwright, MoviePy, Pillow, OpenCV, trimesh, and 100+ more libraries. Use for: data processing, web scraping, image manipulation, video creation, 3D model processing, PDF generation, API calls, automation scripts. Triggers: python, execute code, run script, web scraping, data analysis, image processing, video editing, 3D models, automation, pandas, matplotlib"
allowed-tools: Bash(belt *)
---

# Python Code Executor

Execute Python code in a safe, sandboxed environment with 100+ pre-installed libraries.

![Python Code Executor](https://cloud.inference.sh/u/33sqbmzt3mrg2xxphnhw5g5ear/01k8d8b4mckh6z89dhtxh72dsz.png)

## Quick Start

> Requires inference.sh CLI (`belt`). [Install instructions](https://raw.githubusercontent.com/inference-sh/skills/refs/heads/main/cli-install.md)

```bash
belt login

# Run Python code
belt app run infsh/python-executor --input '{
  "code": "import pandas as pd\nprint(pd.__version__)"
}'
```


## App Details

| Property | Value |
|----------|-------|
| App ID | `infsh/python-executor` |
| Environment | Python 3.10, CPU-only |
| RAM | 8GB (default) / 16GB (high_memory) |
| Timeout | 1-300 seconds (default: 30) |

## Input Schema

```json
{
  "code": "print('Hello World!')",
  "timeout": 30,
  "capture_output": true,
  "working_dir": null
}
```

## Pre-installed Libraries

### Web Scraping & HTTP
- `requests`, `httpx`, `aiohttp` - HTTP clients
- `beautifulsoup4`, `lxml` - HTML/XML parsing
- `selenium`, `playwright` - Browser automation
- `scrapy` - Web scraping framework

### Data Processing
- `numpy`, `pandas`, `scipy` - Numerical computing
- `matplotlib`, `seaborn`, `plotly` - Visualization

### Image Processing
- `pillow`, `opencv-python-headless` - Image manipulation
- `scikit-image`, `imageio` - Image algorithms

### Video & Audio
- `moviepy` - Video editing
- `av` (PyAV), `ffmpeg-python` - Video processing
- `pydub` - Audio manipulation

### 3D Processing
- `trimesh`, `open3d` - 3D mesh processing
- `numpy-stl`, `meshio`, `pyvista` - 3D file formats

### Documents & Graphics
- `svgwrite`, `cairosvg` - SVG creation
- `reportlab`, `pypdf2` - PDF generation

## Examples

### Web Scraping

```bash
belt app run infsh/python-executor --input '{
  "code": "import requests\nfrom bs4 import BeautifulSoup\n\nresponse = requests.get(\"https://example.com\")\nsoup = BeautifulSoup(response.content, \"html.parser\")\nprint(soup.find(\"title\").text)"
}'
```

### Data Analysis with Visualization

```bash
belt app run infsh/python-executor --input '{
  "code": "import pandas as pd\nimport matplotlib.pyplot as plt\n\ndata = {\"name\": [\"Alice\", \"Bob\"], \"sales\": [100, 150]}\ndf = pd.DataFrame(data)\n\nplt.bar(df[\"name\"], df[\"sales\"])\nplt.savefig(\"outputs/chart.png\")\nprint(\"Chart saved!\")"
}'
```

### Image Processing

```bash
belt app run infsh/python-executor --input '{
  "code": "from PIL import Image\nimport numpy as np\n\n# Create gradient image\narr = np.linspace(0, 255, 256*256, dtype=np.uint8).reshape(256, 256)\nimg = Image.fromarray(arr, mode=\"L\")\nimg.save(\"outputs/gradient.png\")\nprint(\"Image created!\")"
}'
```

### Video Creation

```bash
belt app run infsh/python-executor --input '{
  "code": "from moviepy.editor import ColorClip, TextClip, CompositeVideoClip\n\nclip = ColorClip(size=(640, 480), color=(0, 100, 200), duration=3)\ntxt = TextClip(\"Hello!\", fontsize=70, color=\"white\").set_position(\"center\").set_duration(3)\nvideo = CompositeVideoClip([clip, txt])\nvideo.write_videofile(\"outputs/hello.mp4\", fps=24)\nprint(\"Video created!\")",
  "timeout": 120
}'
```

### 3D Model Processing

```bash
belt app run infsh/python-executor --input '{
  "code": "import trimesh\n\nsphere = trimesh.creation.icosphere(subdivisions=3, radius=1.0)\nsphere.export(\"outputs/sphere.stl\")\nprint(f\"Created sphere with {len(sphere.vertices)} vertices\")"
}'
```

### API Calls

```bash
belt app run infsh/python-executor --input '{
  "code": "import requests\nimport json\n\nresponse = requests.get(\"https://api.github.com/users/octocat\")\ndata = response.json()\nprint(json.dumps(data, indent=2))"
}'
```

## File Output

Files saved to `outputs/` are automatically returned:

```python
# These files will be in the response
plt.savefig('outputs/chart.png')
df.to_csv('outputs/data.csv')
video.write_videofile('outputs/video.mp4')
mesh.export('outputs/model.stl')
```

## Variants

```bash
# Default (8GB RAM)
belt app run infsh/python-executor --input input.json

# High memory (16GB RAM) for large datasets
belt app run infsh/python-executor@high_memory --input input.json
```

## Use Cases

- **Web scraping** - Extract data from websites
- **Data analysis** - Process and visualize datasets
- **Image manipulation** - Resize, crop, composite images
- **Video creation** - Generate videos with text overlays
- **3D processing** - Load, transform, export 3D models
- **API integration** - Call external APIs
- **PDF generation** - Create reports and documents
- **Automation** - Run any Python script

## Important Notes

- **CPU-only** - No GPU/ML libraries (use dedicated AI apps for that)
- **Safe execution** - Runs in isolated subprocess
- **Non-interactive** - Use `plt.savefig()` not `plt.show()`
- **File detection** - Output files are auto-detected and returned

## Related Skills

```bash
# AI image generation (for ML-based images)
npx skills add inference-sh/skills@ai-image-generation

# AI video generation (for ML-based videos)
npx skills add inference-sh/skills@ai-video-generation

# LLM models (for text generation)
npx skills add inference-sh/skills@llm-models
```

## Documentation

- [Running Apps](https://inference.sh/docs/apps/running) - How to run apps via CLI
- [App Code](https://inference.sh/docs/extend/app-code) - Understanding app execution
- [Sandboxed Code Execution](https://inference.sh/blog/tools/sandboxed-execution) - Safe code execution for agents
````

## File: .agents/skills/python-testing-patterns/references/advanced-patterns.md
````markdown
# Python Testing Patterns — Advanced Reference

Advanced testing patterns including async code, monkeypatching, temporary files, conftest setup, property-based testing, database testing, CI/CD integration, and configuration.

## Pattern 6: Testing Async Code

```python
# test_async.py
import pytest
import asyncio

async def fetch_data(url: str) -> dict:
    """Fetch data asynchronously."""
    await asyncio.sleep(0.1)
    return {"url": url, "data": "result"}


@pytest.mark.asyncio
async def test_fetch_data():
    """Test async function."""
    result = await fetch_data("https://api.example.com")
    assert result["url"] == "https://api.example.com"
    assert "data" in result


@pytest.mark.asyncio
async def test_concurrent_fetches():
    """Test concurrent async operations."""
    urls = ["url1", "url2", "url3"]
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks)

    assert len(results) == 3
    assert all("data" in r for r in results)


@pytest.fixture
async def async_client():
    """Async fixture."""
    client = {"connected": True}
    yield client
    client["connected"] = False


@pytest.mark.asyncio
async def test_with_async_fixture(async_client):
    """Test using async fixture."""
    assert async_client["connected"] is True
```

## Pattern 7: Monkeypatch for Testing

```python
# test_environment.py
import os
import pytest

def get_database_url() -> str:
    """Get database URL from environment."""
    return os.environ.get("DATABASE_URL", "sqlite:///:memory:")


def test_database_url_default():
    """Test default database URL."""
    # Will use actual environment variable if set
    url = get_database_url()
    assert url


def test_database_url_custom(monkeypatch):
    """Test custom database URL with monkeypatch."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    assert get_database_url() == "postgresql://localhost/test"


def test_database_url_not_set(monkeypatch):
    """Test when env var is not set."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert get_database_url() == "sqlite:///:memory:"


class Config:
    """Configuration class."""

    def __init__(self):
        self.api_key = "production-key"

    def get_api_key(self):
        return self.api_key


def test_monkeypatch_attribute(monkeypatch):
    """Test monkeypatching object attributes."""
    config = Config()
    monkeypatch.setattr(config, "api_key", "test-key")
    assert config.get_api_key() == "test-key"
```

## Pattern 8: Temporary Files and Directories

```python
# test_file_operations.py
import pytest
from pathlib import Path

def save_data(filepath: Path, data: str):
    """Save data to file."""
    filepath.write_text(data)


def load_data(filepath: Path) -> str:
    """Load data from file."""
    return filepath.read_text()


def test_file_operations(tmp_path):
    """Test file operations with temporary directory."""
    # tmp_path is a pathlib.Path object
    test_file = tmp_path / "test_data.txt"

    # Save data
    save_data(test_file, "Hello, World!")

    # Verify file exists
    assert test_file.exists()

    # Load and verify data
    data = load_data(test_file)
    assert data == "Hello, World!"


def test_multiple_files(tmp_path):
    """Test with multiple temporary files."""
    files = {
        "file1.txt": "Content 1",
        "file2.txt": "Content 2",
        "file3.txt": "Content 3"
    }

    for filename, content in files.items():
        filepath = tmp_path / filename
        save_data(filepath, content)

    # Verify all files created
    assert len(list(tmp_path.iterdir())) == 3

    # Verify contents
    for filename, expected_content in files.items():
        filepath = tmp_path / filename
        assert load_data(filepath) == expected_content
```

## Pattern 9: Custom Fixtures and Conftest

```python
# conftest.py
"""Shared fixtures for all tests."""
import pytest

@pytest.fixture(scope="session")
def database_url():
    """Provide database URL for all tests."""
    return "postgresql://localhost/test_db"


@pytest.fixture(autouse=True)
def reset_database(database_url):
    """Auto-use fixture that runs before each test."""
    # Setup: Clear database
    print(f"Clearing database: {database_url}")
    yield
    # Teardown: Clean up
    print("Test completed")


@pytest.fixture
def sample_user():
    """Provide sample user data."""
    return {
        "id": 1,
        "name": "Test User",
        "email": "test@example.com"
    }


@pytest.fixture
def sample_users():
    """Provide list of sample users."""
    return [
        {"id": 1, "name": "User 1"},
        {"id": 2, "name": "User 2"},
        {"id": 3, "name": "User 3"},
    ]


# Parametrized fixture
@pytest.fixture(params=["sqlite", "postgresql", "mysql"])
def db_backend(request):
    """Fixture that runs tests with different database backends."""
    return request.param


def test_with_db_backend(db_backend):
    """This test will run 3 times with different backends."""
    print(f"Testing with {db_backend}")
    assert db_backend in ["sqlite", "postgresql", "mysql"]
```

## Pattern 10: Property-Based Testing

```python
# test_properties.py
from hypothesis import given, strategies as st
import pytest

def reverse_string(s: str) -> str:
    """Reverse a string."""
    return s[::-1]


@given(st.text())
def test_reverse_twice_is_original(s):
    """Property: reversing twice returns original."""
    assert reverse_string(reverse_string(s)) == s


@given(st.text())
def test_reverse_length(s):
    """Property: reversed string has same length."""
    assert len(reverse_string(s)) == len(s)


@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    """Property: addition is commutative."""
    assert a + b == b + a


@given(st.lists(st.integers()))
def test_sorted_list_properties(lst):
    """Property: sorted list is ordered."""
    sorted_lst = sorted(lst)

    # Same length
    assert len(sorted_lst) == len(lst)

    # All elements present
    assert set(sorted_lst) == set(lst)

    # Is ordered
    for i in range(len(sorted_lst) - 1):
        assert sorted_lst[i] <= sorted_lst[i + 1]
```

## Testing Database Code

```python
# test_database_models.py
import pytest
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    email = Column(String(100), unique=True)


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Create in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


def test_create_user(db_session):
    """Test creating a user."""
    user = User(name="Test User", email="test@example.com")
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.name == "Test User"


def test_query_user(db_session):
    """Test querying users."""
    user1 = User(name="User 1", email="user1@example.com")
    user2 = User(name="User 2", email="user2@example.com")

    db_session.add_all([user1, user2])
    db_session.commit()

    users = db_session.query(User).all()
    assert len(users) == 2


def test_unique_email_constraint(db_session):
    """Test unique email constraint."""
    from sqlalchemy.exc import IntegrityError

    user1 = User(name="User 1", email="same@example.com")
    user2 = User(name="User 2", email="same@example.com")

    db_session.add(user1)
    db_session.commit()

    db_session.add(user2)

    with pytest.raises(IntegrityError):
        db_session.commit()
```

## CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          pytest --cov=myapp --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Configuration Files

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=myapp
    --cov-report=term-missing
markers =
    slow: marks tests as slow
    integration: marks integration tests
    unit: marks unit tests
    e2e: marks end-to-end tests
```

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = [
    "-v",
    "--cov=myapp",
    "--cov-report=term-missing",
]

[tool.coverage.run]
source = ["myapp"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```
````

## File: .agents/skills/python-testing-patterns/SKILL.md
````markdown
---
name: python-testing-patterns
description: Implement comprehensive testing strategies with pytest, fixtures, mocking, and test-driven development. Use when writing Python tests, setting up test suites, or implementing testing best practices.
---

# Python Testing Patterns

Comprehensive guide to implementing robust testing strategies in Python using pytest, fixtures, mocking, parameterization, and test-driven development practices.

## When to Use This Skill

- Writing unit tests for Python code
- Setting up test suites and test infrastructure
- Implementing test-driven development (TDD)
- Creating integration tests for APIs and services
- Mocking external dependencies and services
- Testing async code and concurrent operations
- Setting up continuous testing in CI/CD
- Implementing property-based testing
- Testing database operations
- Debugging failing tests

## Core Concepts

### 1. Test Types

- **Unit Tests**: Test individual functions/classes in isolation
- **Integration Tests**: Test interaction between components
- **Functional Tests**: Test complete features end-to-end
- **Performance Tests**: Measure speed and resource usage

### 2. Test Structure (AAA Pattern)

- **Arrange**: Set up test data and preconditions
- **Act**: Execute the code under test
- **Assert**: Verify the results

### 3. Test Coverage

- Measure what code is exercised by tests
- Identify untested code paths
- Aim for meaningful coverage, not just high percentages

### 4. Test Isolation

- Tests should be independent
- No shared state between tests
- Each test should clean up after itself

## Quick Start

```python
# test_example.py
def add(a, b):
    return a + b

def test_add():
    """Basic test example."""
    result = add(2, 3)
    assert result == 5

def test_add_negative():
    """Test with negative numbers."""
    assert add(-1, 1) == 0

# Run with: pytest test_example.py
```

## Fundamental Patterns

### Pattern 1: Basic pytest Tests

```python
# test_calculator.py
import pytest

class Calculator:
    """Simple calculator for testing."""

    def add(self, a: float, b: float) -> float:
        return a + b

    def subtract(self, a: float, b: float) -> float:
        return a - b

    def multiply(self, a: float, b: float) -> float:
        return a * b

    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b


def test_addition():
    """Test addition."""
    calc = Calculator()
    assert calc.add(2, 3) == 5
    assert calc.add(-1, 1) == 0
    assert calc.add(0, 0) == 0


def test_subtraction():
    """Test subtraction."""
    calc = Calculator()
    assert calc.subtract(5, 3) == 2
    assert calc.subtract(0, 5) == -5


def test_multiplication():
    """Test multiplication."""
    calc = Calculator()
    assert calc.multiply(3, 4) == 12
    assert calc.multiply(0, 5) == 0


def test_division():
    """Test division."""
    calc = Calculator()
    assert calc.divide(6, 3) == 2
    assert calc.divide(5, 2) == 2.5


def test_division_by_zero():
    """Test division by zero raises error."""
    calc = Calculator()
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calc.divide(5, 0)
```

### Pattern 2: Fixtures for Setup and Teardown

```python
# test_database.py
import pytest
from typing import Generator

class Database:
    """Simple database class."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connected = False

    def connect(self):
        """Connect to database."""
        self.connected = True

    def disconnect(self):
        """Disconnect from database."""
        self.connected = False

    def query(self, sql: str) -> list:
        """Execute query."""
        if not self.connected:
            raise RuntimeError("Not connected")
        return [{"id": 1, "name": "Test"}]


@pytest.fixture
def db() -> Generator[Database, None, None]:
    """Fixture that provides connected database."""
    # Setup
    database = Database("sqlite:///:memory:")
    database.connect()

    # Provide to test
    yield database

    # Teardown
    database.disconnect()


def test_database_query(db):
    """Test database query with fixture."""
    results = db.query("SELECT * FROM users")
    assert len(results) == 1
    assert results[0]["name"] == "Test"


@pytest.fixture(scope="session")
def app_config():
    """Session-scoped fixture - created once per test session."""
    return {
        "database_url": "postgresql://localhost/test",
        "api_key": "test-key",
        "debug": True
    }


@pytest.fixture(scope="module")
def api_client(app_config):
    """Module-scoped fixture - created once per test module."""
    # Setup expensive resource
    client = {"config": app_config, "session": "active"}
    yield client
    # Cleanup
    client["session"] = "closed"


def test_api_client(api_client):
    """Test using api client fixture."""
    assert api_client["session"] == "active"
    assert api_client["config"]["debug"] is True
```

### Pattern 3: Parameterized Tests

```python
# test_validation.py
import pytest

def is_valid_email(email: str) -> bool:
    """Check if email is valid."""
    return "@" in email and "." in email.split("@")[1]


@pytest.mark.parametrize("email,expected", [
    ("user@example.com", True),
    ("test.user@domain.co.uk", True),
    ("invalid.email", False),
    ("@example.com", False),
    ("user@domain", False),
    ("", False),
])
def test_email_validation(email, expected):
    """Test email validation with various inputs."""
    assert is_valid_email(email) == expected


@pytest.mark.parametrize("a,b,expected", [
    (2, 3, 5),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
    (-5, -5, -10),
])
def test_addition_parameterized(a, b, expected):
    """Test addition with multiple parameter sets."""
    from test_calculator import Calculator
    calc = Calculator()
    assert calc.add(a, b) == expected


# Using pytest.param for special cases
@pytest.mark.parametrize("value,expected", [
    pytest.param(1, True, id="positive"),
    pytest.param(0, False, id="zero"),
    pytest.param(-1, False, id="negative"),
])
def test_is_positive(value, expected):
    """Test with custom test IDs."""
    assert (value > 0) == expected
```

### Pattern 4: Mocking with unittest.mock

```python
# test_api_client.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

class APIClient:
    """Simple API client."""

    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_user(self, user_id: int) -> dict:
        """Fetch user from API."""
        response = requests.get(f"{self.base_url}/users/{user_id}")
        response.raise_for_status()
        return response.json()

    def create_user(self, data: dict) -> dict:
        """Create new user."""
        response = requests.post(f"{self.base_url}/users", json=data)
        response.raise_for_status()
        return response.json()


def test_get_user_success():
    """Test successful API call with mock."""
    client = APIClient("https://api.example.com")

    mock_response = Mock()
    mock_response.json.return_value = {"id": 1, "name": "John Doe"}
    mock_response.raise_for_status.return_value = None

    with patch("requests.get", return_value=mock_response) as mock_get:
        user = client.get_user(1)

        assert user["id"] == 1
        assert user["name"] == "John Doe"
        mock_get.assert_called_once_with("https://api.example.com/users/1")


def test_get_user_not_found():
    """Test API call with 404 error."""
    client = APIClient("https://api.example.com")

    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

    with patch("requests.get", return_value=mock_response):
        with pytest.raises(requests.HTTPError):
            client.get_user(999)


@patch("requests.post")
def test_create_user(mock_post):
    """Test user creation with decorator syntax."""
    client = APIClient("https://api.example.com")

    mock_post.return_value.json.return_value = {"id": 2, "name": "Jane Doe"}
    mock_post.return_value.raise_for_status.return_value = None

    user_data = {"name": "Jane Doe", "email": "jane@example.com"}
    result = client.create_user(user_data)

    assert result["id"] == 2
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args.kwargs["json"] == user_data
```

### Pattern 5: Testing Exceptions

```python
# test_exceptions.py
import pytest

def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ZeroDivisionError("Division by zero")
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Arguments must be numbers")
    return a / b


def test_zero_division():
    """Test exception is raised for division by zero."""
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)


def test_zero_division_with_message():
    """Test exception message."""
    with pytest.raises(ZeroDivisionError, match="Division by zero"):
        divide(5, 0)


def test_type_error():
    """Test type error exception."""
    with pytest.raises(TypeError, match="must be numbers"):
        divide("10", 5)


def test_exception_info():
    """Test accessing exception info."""
    with pytest.raises(ValueError) as exc_info:
        int("not a number")

    assert "invalid literal" in str(exc_info.value)
```

For advanced patterns including async testing, monkeypatching, temporary files, conftest setup, property-based testing, database testing, CI/CD integration, and configuration files, see [references/advanced-patterns.md](references/advanced-patterns.md)

## Test Design Principles

### One Behavior Per Test

Each test should verify exactly one behavior. This makes failures easy to diagnose and tests easy to maintain.

```python
# BAD - testing multiple behaviors
def test_user_service():
    user = service.create_user(data)
    assert user.id is not None
    assert user.email == data["email"]
    updated = service.update_user(user.id, {"name": "New"})
    assert updated.name == "New"

# GOOD - focused tests
def test_create_user_assigns_id():
    user = service.create_user(data)
    assert user.id is not None

def test_create_user_stores_email():
    user = service.create_user(data)
    assert user.email == data["email"]

def test_update_user_changes_name():
    user = service.create_user(data)
    updated = service.update_user(user.id, {"name": "New"})
    assert updated.name == "New"
```

### Test Error Paths

Always test failure cases, not just happy paths.

```python
def test_get_user_raises_not_found():
    with pytest.raises(UserNotFoundError) as exc_info:
        service.get_user("nonexistent-id")

    assert "nonexistent-id" in str(exc_info.value)

def test_create_user_rejects_invalid_email():
    with pytest.raises(ValueError, match="Invalid email format"):
        service.create_user({"email": "not-an-email"})
```

## Testing Best Practices

### Test Organization

```python
# tests/
#   __init__.py
#   conftest.py           # Shared fixtures
#   test_unit/            # Unit tests
#     test_models.py
#     test_utils.py
#   test_integration/     # Integration tests
#     test_api.py
#     test_database.py
#   test_e2e/            # End-to-end tests
#     test_workflows.py
```

### Test Naming Convention

A common pattern: `test_<unit>_<scenario>_<expected_outcome>`. Adapt to your team's preferences.

```python
# Pattern: test_<unit>_<scenario>_<expected>
def test_create_user_with_valid_data_returns_user():
    ...

def test_create_user_with_duplicate_email_raises_conflict():
    ...

def test_get_user_with_unknown_id_returns_none():
    ...

# Good test names - clear and descriptive
def test_user_creation_with_valid_data():
    """Clear name describes what is being tested."""
    pass

def test_login_fails_with_invalid_password():
    """Name describes expected behavior."""
    pass

def test_api_returns_404_for_missing_resource():
    """Specific about inputs and expected outcomes."""
    pass

# Bad test names - avoid these
def test_1():  # Not descriptive
    pass

def test_user():  # Too vague
    pass

def test_function():  # Doesn't explain what's tested
    pass
```

### Testing Retry Behavior

Verify that retry logic works correctly using mock side effects.

```python
from unittest.mock import Mock

def test_retries_on_transient_error():
    """Test that service retries on transient failures."""
    client = Mock()
    # Fail twice, then succeed
    client.request.side_effect = [
        ConnectionError("Failed"),
        ConnectionError("Failed"),
        {"status": "ok"},
    ]

    service = ServiceWithRetry(client, max_retries=3)
    result = service.fetch()

    assert result == {"status": "ok"}
    assert client.request.call_count == 3

def test_gives_up_after_max_retries():
    """Test that service stops retrying after max attempts."""
    client = Mock()
    client.request.side_effect = ConnectionError("Failed")

    service = ServiceWithRetry(client, max_retries=3)

    with pytest.raises(ConnectionError):
        service.fetch()

    assert client.request.call_count == 3

def test_does_not_retry_on_permanent_error():
    """Test that permanent errors are not retried."""
    client = Mock()
    client.request.side_effect = ValueError("Invalid input")

    service = ServiceWithRetry(client, max_retries=3)

    with pytest.raises(ValueError):
        service.fetch()

    # Only called once - no retry for ValueError
    assert client.request.call_count == 1
```

### Mocking Time with Freezegun

Use freezegun to control time in tests for predictable time-dependent behavior.

```python
from freezegun import freeze_time
from datetime import datetime, timedelta

@freeze_time("2026-01-15 10:00:00")
def test_token_expiry():
    """Test token expires at correct time."""
    token = create_token(expires_in_seconds=3600)
    assert token.expires_at == datetime(2026, 1, 15, 11, 0, 0)

@freeze_time("2026-01-15 10:00:00")
def test_is_expired_returns_false_before_expiry():
    """Test token is not expired when within validity period."""
    token = create_token(expires_in_seconds=3600)
    assert not token.is_expired()

@freeze_time("2026-01-15 12:00:00")
def test_is_expired_returns_true_after_expiry():
    """Test token is expired after validity period."""
    token = Token(expires_at=datetime(2026, 1, 15, 11, 30, 0))
    assert token.is_expired()

def test_with_time_travel():
    """Test behavior across time using freeze_time context."""
    with freeze_time("2026-01-01") as frozen_time:
        item = create_item()
        assert item.created_at == datetime(2026, 1, 1)

        # Move forward in time
        frozen_time.move_to("2026-01-15")
        assert item.age_days == 14
```

### Test Markers

```python
# test_markers.py
import pytest

@pytest.mark.slow
def test_slow_operation():
    """Mark slow tests."""
    import time
    time.sleep(2)


@pytest.mark.integration
def test_database_integration():
    """Mark integration tests."""
    pass


@pytest.mark.skip(reason="Feature not implemented yet")
def test_future_feature():
    """Skip tests temporarily."""
    pass


@pytest.mark.skipif(os.name == "nt", reason="Unix only test")
def test_unix_specific():
    """Conditional skip."""
    pass


@pytest.mark.xfail(reason="Known bug #123")
def test_known_bug():
    """Mark expected failures."""
    assert False


# Run with:
# pytest -m slow          # Run only slow tests
# pytest -m "not slow"    # Skip slow tests
# pytest -m integration   # Run integration tests
```

### Coverage Reporting

```bash
# Install coverage
pip install pytest-cov

# Run tests with coverage
pytest --cov=myapp tests/

# Generate HTML report
pytest --cov=myapp --cov-report=html tests/

# Fail if coverage below threshold
pytest --cov=myapp --cov-fail-under=80 tests/

# Show missing lines
pytest --cov=myapp --cov-report=term-missing tests/
```

For advanced patterns (async testing, monkeypatching, property-based testing, database testing, CI/CD integration, and configuration), see [references/advanced-patterns.md](references/advanced-patterns.md)
````

## File: .codegraph/.gitignore
````
# CodeGraph data files — local to each machine, not for committing.
# Ignore everything in .codegraph/ except this file itself, so transient
# files (the database, daemon.pid, sockets, logs) never show up in git.
*
!.gitignore
````

## File: config/__init__.py
````python

````

## File: config/asgi.py
````python
"""ASGI config for the University Enrollment project."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
````

## File: config/settings.py
````python
"""Django settings for the University Enrollment project."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-dev-only-change-in-production"

DEBUG = True

ALLOWED_HOSTS: list[str] = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Set SQL_DEBUG=1 to trace every ORM query in the console.
_SQL_DEBUG = os.environ.get("SQL_DEBUG") == "1"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "core": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG" if _SQL_DEBUG else "WARNING",
            "propagate": False,
        },
    },
}
````

## File: config/urls.py
````python
"""URL configuration for the University Enrollment project."""

from django.contrib import admin
from django.urls import path

from core.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
````

## File: config/wsgi.py
````python
"""WSGI config for the University Enrollment project."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
````

## File: core/migrations/__init__.py
````python

````

## File: core/migrations/0001_initial.py
````python
# Generated by Django 6.1 on 2026-08-31 06:54

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Department",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="Faculty",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="OpenClass",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("academic_year", models.IntegerField()),
                ("semester", models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name="University",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="Curriculum",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("year", models.IntegerField()),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="curricula",
                        to="core.department",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="department",
            name="faculty",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="departments",
                to="core.faculty",
            ),
        ),
        migrations.CreateModel(
            name="Section",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("section_no", models.CharField(max_length=16)),
                ("capacity", models.IntegerField(blank=True, null=True)),
                (
                    "open_class",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sections",
                        to="core.openclass",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Student",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("student_code", models.CharField(max_length=32, unique=True)),
                ("name", models.CharField(max_length=255)),
                (
                    "curriculum",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="students",
                        to="core.curriculum",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Enrolled", "Enrolled"),
                            ("Withdrawn", "Withdrawn"),
                            ("Completed", "Completed"),
                            ("Failed", "Failed"),
                        ],
                        max_length=16,
                    ),
                ),
                ("grade", models.CharField(blank=True, max_length=8, null=True)),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="core.section",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="core.student",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Subject",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("code", models.CharField(max_length=32, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("credit", models.IntegerField()),
                (
                    "department",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subjects",
                        to="core.department",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="openclass",
            name="subject",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="open_classes",
                to="core.subject",
            ),
        ),
        migrations.CreateModel(
            name="CurriculumSubject",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("Core", "Core"),
                            ("Major", "Major"),
                            ("GenEd", "GenEd"),
                            ("Elective", "Elective"),
                        ],
                        max_length=16,
                    ),
                ),
                ("semester_recommended", models.IntegerField(blank=True, null=True)),
                ("year_recommended", models.IntegerField(blank=True, null=True)),
                (
                    "curriculum",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="curriculum_subjects",
                        to="core.curriculum",
                    ),
                ),
                (
                    "subject",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="curriculum_subjects",
                        to="core.subject",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="faculty",
            name="university",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="faculties",
                to="core.university",
            ),
        ),
        migrations.AddConstraint(
            model_name="section",
            constraint=models.UniqueConstraint(
                fields=("open_class", "section_no"), name="unique_open_class_section_no"
            ),
        ),
        migrations.AddConstraint(
            model_name="enrollment",
            constraint=models.UniqueConstraint(
                fields=("student", "section"), name="unique_student_section"
            ),
        ),
        migrations.AddConstraint(
            model_name="curriculumsubject",
            constraint=models.UniqueConstraint(
                fields=("curriculum", "subject"), name="unique_curriculum_subject"
            ),
        ),
    ]
````

## File: core/__init__.py
````python

````

## File: core/admin.py
````python
from django.contrib import admin

from core.models import (
    Curriculum,
    CurriculumSubject,
    Department,
    Enrollment,
    Faculty,
    OpenClass,
    Section,
    Student,
    Subject,
    University,
)

admin.site.register(University)
admin.site.register(Faculty)
admin.site.register(Department)
admin.site.register(Curriculum)
admin.site.register(Subject)
admin.site.register(CurriculumSubject)
admin.site.register(Student)
admin.site.register(OpenClass)
admin.site.register(Section)
admin.site.register(Enrollment)
````

## File: core/api.py
````python
"""Generic CRUD router factory, registered once per model.

django-ninja builds its ``ViewSignature`` *inside* ``router.post(...)`` /
``router.put(...)`` by reading ``inspect.signature()`` at that call. So the
``payload`` parameter's real schema type must be patched onto the function's
``__annotations__`` *before* it is handed to ``router.post``/``router.put`` -
using ``@router.post(...)`` decorator syntax would register the endpoint
before the patch runs, and ninja would treat ``payload`` as unannotated.
Hence the explicit (non-decorator) calls below.
"""

import logging
import uuid
from typing import Any

from django.db import IntegrityError, models
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Router, Schema

from core.models import (
    Curriculum,
    CurriculumSubject,
    Department,
    Enrollment,
    Faculty,
    OpenClass,
    Section,
    Student,
    Subject,
    University,
)
from core.schemas import (
    CurriculumIn,
    CurriculumOut,
    CurriculumSubjectIn,
    CurriculumSubjectOut,
    DepartmentIn,
    DepartmentOut,
    EnrollmentIn,
    EnrollmentOut,
    FacultyIn,
    FacultyOut,
    OpenClassIn,
    OpenClassOut,
    SectionIn,
    SectionOut,
    StudentIn,
    StudentOut,
    SubjectIn,
    SubjectOut,
    UniversityIn,
    UniversityOut,
)

logger = logging.getLogger("core")


def _model_kwargs(model: type[models.Model], data: dict[str, Any]) -> dict[str, Any]:
    """Translate a schema's ``{field: value}`` dict into ORM kwargs.

    A ``ModelSchema`` field for a ForeignKey carries the *related object's*
    field name (e.g. ``university``) but its value is only the related pk
    (a UUID). Django's ``Model(university=<uuid>)`` requires an actual
    instance for that name, so FK values must be passed as ``university_id``
    instead.
    """
    fk_names = {f.name for f in model._meta.get_fields() if f.many_to_one or f.one_to_one}
    return {(f"{key}_id" if key in fk_names else key): value for key, value in data.items()}


def crud_router[ModelT: models.Model](
    model: type[ModelT],
    schema_in: type[Schema],
    schema_out: type[Schema],
    *,
    tag: str,
) -> Router:
    """Build a Router with list/get/create/update/delete for ``model``."""
    router = Router(tags=[tag])
    name = model.__name__

    def list_items(request: HttpRequest) -> models.QuerySet[ModelT]:
        return model._default_manager.all()

    router.get(
        "/",
        response=list[schema_out],
        summary=f"List {tag}s",
        operation_id=f"{tag.lower()}_list",
    )(list_items)  # type: ignore[valid-type]

    def get_item(request: HttpRequest, item_id: uuid.UUID) -> ModelT:
        return get_object_or_404(model, id=item_id)

    router.get(
        "/{item_id}",
        response=schema_out,
        summary=f"Get {tag}",
        operation_id=f"{tag.lower()}_get",
    )(get_item)

    def create_item(request: HttpRequest, payload: Schema) -> ModelT:
        kwargs = _model_kwargs(model, payload.dict())
        logger.debug("creating %s: %s", name, kwargs)
        obj = model._default_manager.create(**kwargs)
        return obj

    create_item.__annotations__["payload"] = schema_in
    router.post(
        "/",
        response=schema_out,
        summary=f"Create {tag}",
        operation_id=f"{tag.lower()}_create",
    )(create_item)

    def update_item(request: HttpRequest, item_id: uuid.UUID, payload: Schema) -> ModelT:
        obj = get_object_or_404(model, id=item_id)
        for field, value in _model_kwargs(model, payload.dict()).items():
            setattr(obj, field, value)
        obj.save()
        logger.debug("updated %s %s", name, item_id)
        return obj

    update_item.__annotations__["payload"] = schema_in
    router.put(
        "/{item_id}",
        response=schema_out,
        summary=f"Update {tag}",
        operation_id=f"{tag.lower()}_update",
    )(update_item)

    def delete_item(request: HttpRequest, item_id: uuid.UUID) -> dict[str, bool]:
        obj = get_object_or_404(model, id=item_id)
        obj.delete()
        logger.debug("deleted %s %s", name, item_id)
        return {"success": True}

    router.delete(
        "/{item_id}",
        summary=f"Delete {tag}",
        operation_id=f"{tag.lower()}_delete",
    )(delete_item)

    return router


api = NinjaAPI(
    title="University Enrollment API",
    version="1.0.0",
    description=(
        "Academic catalog and student enrollment management API for managing "
        "universities, curricula, courses, sections, and enrollment records."
    ),
    openapi_tags=[
        {"name": "University", "description": "Manage universities in the system."},
        {"name": "Faculty", "description": "Manage faculties within universities."},
        {"name": "Department", "description": "Manage departments within faculties."},
        {"name": "Curriculum", "description": "Manage academic curricula."},
        {"name": "Subject", "description": "Manage subjects and course catalog entries."},
        {
            "name": "Curriculum Subject",
            "description": "Track required or elective subject mappings within a curriculum.",
        },
        {"name": "Student", "description": "Manage student records."},
        {"name": "Open Class", "description": "Manage open-course offerings."},
        {"name": "Section", "description": "Manage course sections and capacities."},
        {"name": "Enrollment", "description": "Manage enrollments and grade records."},
    ],
)
api.openapi_extra = {
    "x-tagGroups": [
        {
            "name": "Academic Catalog",
            "tags": [
                "University",
                "Faculty",
                "Department",
                "Curriculum",
                "Subject",
                "Curriculum Subject",
            ],
        },
        {
            "name": "Student Lifecycle",
            "tags": ["Student", "Open Class", "Section", "Enrollment"],
        },
    ]
}


@api.exception_handler(IntegrityError)
def integrity_error_handler(request: HttpRequest, exc: IntegrityError) -> Any:
    return api.create_response(
        request, {"detail": "Conflict: violates a uniqueness constraint."}, status=409
    )


api.add_router(
    "/universities",
    crud_router(University, UniversityIn, UniversityOut, tag="University"),
)
api.add_router("/faculties", crud_router(Faculty, FacultyIn, FacultyOut, tag="Faculty"))
api.add_router(
    "/departments",
    crud_router(Department, DepartmentIn, DepartmentOut, tag="Department"),
)
api.add_router(
    "/curricula",
    crud_router(Curriculum, CurriculumIn, CurriculumOut, tag="Curriculum"),
)
api.add_router("/subjects", crud_router(Subject, SubjectIn, SubjectOut, tag="Subject"))
api.add_router(
    "/curriculum-subjects",
    crud_router(
        CurriculumSubject,
        CurriculumSubjectIn,
        CurriculumSubjectOut,
        tag="Curriculum Subject",
    ),
)
api.add_router("/students", crud_router(Student, StudentIn, StudentOut, tag="Student"))
api.add_router(
    "/open-classes",
    crud_router(OpenClass, OpenClassIn, OpenClassOut, tag="Open Class"),
)
api.add_router("/sections", crud_router(Section, SectionIn, SectionOut, tag="Section"))
api.add_router(
    "/enrollments",
    crud_router(Enrollment, EnrollmentIn, EnrollmentOut, tag="Enrollment"),
)
````

## File: core/apps.py
````python
from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"
````

## File: core/models.py
````python
"""Models for the university enrollment domain.

Mirrors the DBML schema: University -> Faculty -> Department ->
Curriculum/Subject -> CurriculumSubject, Student, OpenClass -> Section,
Enrollment.
"""

import uuid

from django.db import models


class SubjectRequirementType(models.TextChoices):
    """How a subject counts toward a curriculum's requirements."""

    CORE = "Core", "Core"
    MAJOR = "Major", "Major"
    GEN_ED = "GenEd", "GenEd"
    ELECTIVE = "Elective", "Elective"


class EnrollmentStatus(models.TextChoices):
    """Lifecycle status of a student's enrollment in a section."""

    ENROLLED = "Enrolled", "Enrolled"
    WITHDRAWN = "Withdrawn", "Withdrawn"
    COMPLETED = "Completed", "Completed"
    FAILED = "Failed", "Failed"


class University(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class Faculty(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="faculties")
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class Curriculum(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="curricula")
    name = models.CharField(max_length=255)
    year = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.name} ({self.year})"


class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="subjects",
        null=True,
        blank=True,
    )
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)
    credit = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class CurriculumSubject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    curriculum = models.ForeignKey(
        Curriculum, on_delete=models.CASCADE, related_name="curriculum_subjects"
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="curriculum_subjects"
    )
    type = models.CharField(max_length=16, choices=SubjectRequirementType.choices)
    semester_recommended = models.IntegerField(null=True, blank=True)
    year_recommended = models.IntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["curriculum", "subject"], name="unique_curriculum_subject"
            )
        ]

    def __str__(self) -> str:
        return f"{self.curriculum} - {self.subject}"


class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name="students")
    student_code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.student_code} - {self.name}"


class OpenClass(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="open_classes")
    academic_year = models.IntegerField()
    semester = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.subject.code} - {self.academic_year}/{self.semester}"


class Section(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    open_class = models.ForeignKey(OpenClass, on_delete=models.CASCADE, related_name="sections")
    section_no = models.CharField(max_length=16)
    capacity = models.IntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["open_class", "section_no"], name="unique_open_class_section_no"
            )
        ]

    def __str__(self) -> str:
        return f"{self.open_class} - Sec {self.section_no}"


class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=16, choices=EnrollmentStatus.choices)
    grade = models.CharField(max_length=8, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "section"], name="unique_student_section")
        ]

    def __str__(self) -> str:
        return f"{self.student} - {self.section} ({self.status})"
````

## File: core/schemas.py
````python
"""ninja ModelSchema pairs (In/Out) for every model."""

from ninja import ModelSchema

from core.models import (
    Curriculum,
    CurriculumSubject,
    Department,
    Enrollment,
    EnrollmentStatus,
    Faculty,
    OpenClass,
    Section,
    Student,
    Subject,
    SubjectRequirementType,
    University,
)


class UniversityIn(ModelSchema):
    class Meta:
        model = University
        fields = ["name"]


class UniversityOut(ModelSchema):
    class Meta:
        model = University
        fields = ["id", "name"]


class FacultyIn(ModelSchema):
    class Meta:
        model = Faculty
        fields = ["university", "name"]


class FacultyOut(ModelSchema):
    class Meta:
        model = Faculty
        fields = ["id", "university", "name"]


class DepartmentIn(ModelSchema):
    class Meta:
        model = Department
        fields = ["faculty", "name"]


class DepartmentOut(ModelSchema):
    class Meta:
        model = Department
        fields = ["id", "faculty", "name"]


class CurriculumIn(ModelSchema):
    class Meta:
        model = Curriculum
        fields = ["department", "name", "year"]


class CurriculumOut(ModelSchema):
    class Meta:
        model = Curriculum
        fields = ["id", "department", "name", "year"]


class SubjectIn(ModelSchema):
    class Meta:
        model = Subject
        fields = ["department", "code", "name", "credit"]


class SubjectOut(ModelSchema):
    class Meta:
        model = Subject
        fields = ["id", "department", "code", "name", "credit"]


class CurriculumSubjectIn(ModelSchema):
    type: SubjectRequirementType

    class Meta:
        model = CurriculumSubject
        fields = [
            "curriculum",
            "subject",
            "semester_recommended",
            "year_recommended",
        ]


class CurriculumSubjectOut(ModelSchema):
    type: SubjectRequirementType

    class Meta:
        model = CurriculumSubject
        fields = [
            "id",
            "curriculum",
            "subject",
            "semester_recommended",
            "year_recommended",
        ]


class StudentIn(ModelSchema):
    class Meta:
        model = Student
        fields = ["curriculum", "student_code", "name"]


class StudentOut(ModelSchema):
    class Meta:
        model = Student
        fields = ["id", "curriculum", "student_code", "name"]


class OpenClassIn(ModelSchema):
    class Meta:
        model = OpenClass
        fields = ["subject", "academic_year", "semester"]


class OpenClassOut(ModelSchema):
    class Meta:
        model = OpenClass
        fields = ["id", "subject", "academic_year", "semester"]


class SectionIn(ModelSchema):
    class Meta:
        model = Section
        fields = ["open_class", "section_no", "capacity"]


class SectionOut(ModelSchema):
    class Meta:
        model = Section
        fields = ["id", "open_class", "section_no", "capacity"]


class EnrollmentIn(ModelSchema):
    status: EnrollmentStatus

    class Meta:
        model = Enrollment
        fields = ["student", "section", "grade"]


class EnrollmentOut(ModelSchema):
    status: EnrollmentStatus

    class Meta:
        model = Enrollment
        fields = ["id", "student", "section", "grade"]
````

## File: core/tests.py
````python
"""Smoke tests: unique constraints hold, and the generic CRUD router works."""

import json

from django.db import IntegrityError, transaction
from django.test import Client, TestCase

from core.models import (
    Curriculum,
    CurriculumSubject,
    Department,
    Enrollment,
    EnrollmentStatus,
    Faculty,
    OpenClass,
    Section,
    Student,
    Subject,
    SubjectRequirementType,
    University,
)


class UniqueConstraintTests(TestCase):
    def setUp(self) -> None:
        self.university = University.objects.create(name="Test University")
        self.faculty = Faculty.objects.create(university=self.university, name="Engineering")
        self.department = Department.objects.create(faculty=self.faculty, name="CPE")
        self.curriculum = Curriculum.objects.create(
            department=self.department, name="CPE Curriculum", year=2026
        )
        self.subject = Subject.objects.create(
            department=self.department, code="CPE101", name="Intro", credit=3
        )
        self.student = Student.objects.create(
            curriculum=self.curriculum, student_code="S001", name="Alice"
        )
        self.open_class = OpenClass.objects.create(
            subject=self.subject, academic_year=2026, semester=1
        )
        self.section = Section.objects.create(open_class=self.open_class, section_no="1")

    def test_duplicate_curriculum_subject_rejected(self) -> None:
        CurriculumSubject.objects.create(
            curriculum=self.curriculum,
            subject=self.subject,
            type=SubjectRequirementType.CORE,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            CurriculumSubject.objects.create(
                curriculum=self.curriculum,
                subject=self.subject,
                type=SubjectRequirementType.MAJOR,
            )

    def test_duplicate_section_no_rejected(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            Section.objects.create(open_class=self.open_class, section_no="1")

    def test_duplicate_enrollment_rejected(self) -> None:
        Enrollment.objects.create(
            student=self.student, section=self.section, status=EnrollmentStatus.ENROLLED
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Enrollment.objects.create(
                student=self.student, section=self.section, status=EnrollmentStatus.WITHDRAWN
            )


class CrudApiTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_swagger_docs_and_tag_groups_are_available(self) -> None:
        docs_resp = self.client.get("/api/docs")
        self.assertEqual(docs_resp.status_code, 200)
        self.assertIn("swagger", docs_resp.content.decode("utf-8").lower())

        openapi_resp = self.client.get("/api/openapi.json")
        self.assertEqual(openapi_resp.status_code, 200)

        tags = {tag["name"] for tag in openapi_resp.json().get("tags", [])}
        self.assertIn("University", tags)
        self.assertIn("Student", tags)
        self.assertIn("Enrollment", tags)

    def test_university_crud_round_trip(self) -> None:
        create_resp = self.client.post(
            "/api/universities/",
            data=json.dumps({"name": "Round Trip University"}),
            content_type="application/json",
        )
        self.assertEqual(create_resp.status_code, 200)
        university_id = create_resp.json()["id"]

        list_resp = self.client.get("/api/universities/")
        self.assertEqual(list_resp.status_code, 200)
        self.assertTrue(any(u["id"] == university_id for u in list_resp.json()))

        get_resp = self.client.get(f"/api/universities/{university_id}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["name"], "Round Trip University")

        put_resp = self.client.put(
            f"/api/universities/{university_id}",
            data=json.dumps({"name": "Renamed University"}),
            content_type="application/json",
        )
        self.assertEqual(put_resp.status_code, 200)
        self.assertEqual(put_resp.json()["name"], "Renamed University")

        delete_resp = self.client.delete(f"/api/universities/{university_id}")
        self.assertEqual(delete_resp.status_code, 200)

        final_get = self.client.get(f"/api/universities/{university_id}")
        self.assertEqual(final_get.status_code, 404)

    def test_enrollment_conflict_returns_409(self) -> None:
        university = University.objects.create(name="Conflict University")
        faculty = Faculty.objects.create(university=university, name="Engineering")
        department = Department.objects.create(faculty=faculty, name="CPE")
        curriculum = Curriculum.objects.create(
            department=department, name="CPE Curriculum", year=2026
        )
        subject = Subject.objects.create(
            department=department, code="CPE102", name="Intro 2", credit=3
        )
        student = Student.objects.create(curriculum=curriculum, student_code="S002", name="Bob")
        open_class = OpenClass.objects.create(subject=subject, academic_year=2026, semester=1)
        section = Section.objects.create(open_class=open_class, section_no="1")

        payload = {
            "student_id": str(student.id),
            "section_id": str(section.id),
            "status": "Enrolled",
        }
        first = self.client.post(
            "/api/enrollments/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(first.status_code, 200)

        second = self.client.post(
            "/api/enrollments/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(second.status_code, 409)
````

## File: core/views.py
````python
# All HTTP endpoints are served via django-ninja; see core/api.py.
````

## File: src/ood/__init__.py
````python
def main() -> None:
    print("Hello from ood!")
````

## File: .python-version
````
3.13
````

## File: manage.py
````python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
````

## File: pyproject.toml
````toml
[project]
name = "ood"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
authors = [
    { name = "parinya-ao", email = "flim.parinya.ao@gmail.com" }
]
requires-python = ">=3.13"
dependencies = [
    "django>=6.1",
    "django-ninja>=1.7.0",
]

[project.scripts]
ood = "ood:main"

[build-system]
requires = ["uv_build>=0.12.5,<0.13.0"]
build-backend = "uv_build"

[dependency-groups]
dev = [
    "django-stubs[compatible-mypy]>=6.1.0",
    "mypy>=2.3.1",
    "ruff>=0.16.5",
]

[tool.ruff]
line-length = 100
target-version = "py313"
extend-exclude = ["**/migrations/*.py", ".agents"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
strict = true
disallow_untyped_defs = true
warn_return_any = true
no_implicit_optional = true
plugins = ["mypy_django_plugin.main"]

[[tool.mypy.overrides]]
module = "core.migrations.*"
ignore_errors = true

[tool.django-stubs]
django_settings_module = "config.settings"
````

## File: README.md
````markdown

````

## File: seed.py
````python
#!/usr/bin/env python
"""Seed the database with coherent mock data.

Idempotent: re-running does not duplicate rows (uses get_or_create on the
natural/unique keys). Pass --flush to wipe existing rows from these models
first.

Usage:
    uv run python seed.py [--flush]
"""

import argparse
import logging
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import transaction  # noqa: E402

from core.models import (  # noqa: E402
    Curriculum,
    CurriculumSubject,
    Department,
    Enrollment,
    EnrollmentStatus,
    Faculty,
    OpenClass,
    Section,
    Student,
    Subject,
    SubjectRequirementType,
    University,
)

logger = logging.getLogger("core")

ACADEMIC_YEAR = 2026

SUBJECTS = [
    ("CPE101", "Introduction to Programming", 3),
    ("CPE201", "Data Structures and Algorithms", 3),
    ("CPE301", "Operating Systems", 3),
    ("CPE302", "Computer Networks", 3),
    ("CPE401", "Software Engineering", 3),
    ("CPE402", "Database Systems", 3),
    ("GE101", "English Communication", 3),
    ("GE102", "Critical Thinking", 3),
    ("MA101", "Calculus I", 3),
    ("MA102", "Linear Algebra", 3),
]

# (subject_code, requirement_type, semester_recommended, year_recommended)
CURRICULUM_SUBJECTS = [
    ("CPE101", SubjectRequirementType.CORE, 1, 1),
    ("CPE201", SubjectRequirementType.CORE, 2, 1),
    ("CPE301", SubjectRequirementType.MAJOR, 1, 2),
    ("CPE302", SubjectRequirementType.MAJOR, 2, 2),
    ("CPE401", SubjectRequirementType.MAJOR, 1, 3),
    ("CPE402", SubjectRequirementType.MAJOR, 2, 3),
    ("GE101", SubjectRequirementType.GEN_ED, 1, 1),
    ("GE102", SubjectRequirementType.GEN_ED, 2, 1),
    ("MA101", SubjectRequirementType.ELECTIVE, 1, 1),
    ("MA102", SubjectRequirementType.ELECTIVE, 2, 1),
]


def flush() -> None:
    logger.info("flushing existing seed data")
    Enrollment.objects.all().delete()
    Section.objects.all().delete()
    OpenClass.objects.all().delete()
    CurriculumSubject.objects.all().delete()
    Student.objects.all().delete()
    Subject.objects.all().delete()
    Curriculum.objects.all().delete()
    Department.objects.all().delete()
    Faculty.objects.all().delete()
    University.objects.all().delete()


@transaction.atomic
def seed() -> None:
    university, _ = University.objects.get_or_create(name="Kasetsart University")
    logger.info("university: %s", university.name)

    engineering, _ = Faculty.objects.get_or_create(
        university=university, name="Faculty of Engineering"
    )
    science, _ = Faculty.objects.get_or_create(university=university, name="Faculty of Science")

    cpe_dept, _ = Department.objects.get_or_create(faculty=engineering, name="Computer Engineering")
    ee_dept, _ = Department.objects.get_or_create(
        faculty=engineering, name="Electrical Engineering"
    )
    math_dept, _ = Department.objects.get_or_create(faculty=science, name="Mathematics")
    logger.info("departments: %s", [cpe_dept.name, ee_dept.name, math_dept.name])

    curriculum, _ = Curriculum.objects.get_or_create(
        department=cpe_dept,
        name="Computer Engineering Curriculum",
        year=ACADEMIC_YEAR,
    )
    curriculum_alt, _ = Curriculum.objects.get_or_create(
        department=ee_dept,
        name="Electrical Engineering Curriculum",
        year=ACADEMIC_YEAR,
    )
    logger.info("curricula: %s, %s", curriculum.name, curriculum_alt.name)

    subjects = {}
    for code, name, credit in SUBJECTS:
        subject, _ = Subject.objects.get_or_create(
            code=code, defaults={"name": name, "credit": credit, "department": cpe_dept}
        )
        subjects[code] = subject
    logger.info("subjects: %d created/found", len(subjects))

    for code, req_type, semester, year in CURRICULUM_SUBJECTS:
        CurriculumSubject.objects.get_or_create(
            curriculum=curriculum,
            subject=subjects[code],
            defaults={
                "type": req_type,
                "semester_recommended": semester,
                "year_recommended": year,
            },
        )
    logger.info("curriculum subjects linked: %d", len(CURRICULUM_SUBJECTS))

    students = []
    for i in range(1, 16):
        student, _ = Student.objects.get_or_create(
            student_code=f"651234{i:03d}",
            defaults={"name": f"Student {i}", "curriculum": curriculum},
        )
        students.append(student)
    logger.info("students: %d created/found", len(students))

    open_classes = []
    for code in ["CPE101", "CPE201", "CPE301", "GE101"]:
        for semester in (1, 2):
            open_class, _ = OpenClass.objects.get_or_create(
                subject=subjects[code],
                academic_year=ACADEMIC_YEAR,
                semester=semester,
            )
            open_classes.append(open_class)
    logger.info("open classes: %d created/found", len(open_classes))

    sections = []
    for open_class in open_classes:
        for section_no in ("1", "2"):
            section, _ = Section.objects.get_or_create(
                open_class=open_class, section_no=section_no, defaults={"capacity": 40}
            )
            sections.append(section)
    logger.info("sections: %d created/found", len(sections))

    statuses = [
        EnrollmentStatus.ENROLLED,
        EnrollmentStatus.WITHDRAWN,
        EnrollmentStatus.COMPLETED,
        EnrollmentStatus.FAILED,
    ]
    created = 0
    for i, student in enumerate(students):
        section = sections[i % len(sections)]
        status = statuses[i % len(statuses)]
        grade = "A" if status == EnrollmentStatus.COMPLETED else None
        _, was_created = Enrollment.objects.get_or_create(
            student=student,
            section=section,
            defaults={"status": status, "grade": grade},
        )
        if was_created:
            created += 1
    logger.info("enrollments created: %d", created)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the university enrollment database.")
    parser.add_argument("--flush", action="store_true", help="delete existing rows first")
    args = parser.parse_args()

    if args.flush:
        flush()

    seed()
    logger.info("seeding complete")


if __name__ == "__main__":
    main()
````

## File: skills-lock.json
````json
{
  "version": 1,
  "skills": {
    "django-expert": {
      "source": "vintasoftware/django-ai-plugins",
      "sourceType": "autoskills-registry",
      "computedHash": "953f638e4d26826dffa99d604c987ddc196fd9914be987658a95e479159bbb9f"
    },
    "django-patterns": {
      "source": "affaan-m/everything-claude-code",
      "sourceType": "autoskills-registry",
      "computedHash": "bb25ed3a0d4f7aa705a7f5fefa39808b754cee39da1d9ce7620171dd4e42a3c0"
    },
    "django-security": {
      "source": "affaan-m/everything-claude-code",
      "sourceType": "autoskills-registry",
      "computedHash": "3961ec06ea45e4837e6dc47a18781b17aaa88b337fe4f84dae1501afc5297fd6"
    },
    "python-executor": {
      "source": "inferen-sh/skills",
      "sourceType": "autoskills-registry",
      "computedHash": "bd2d874c27788964fadf03c0840049de0409407f06f883ee90886164cb22ef69"
    },
    "python-testing-patterns": {
      "source": "wshobson/agents",
      "sourceType": "autoskills-registry",
      "computedHash": "07b87d62993c0b6159a91d18fc8723b7f4c13d5000c0984266c207493ce641ff"
    }
  }
}
````

## File: todo.md
````markdown
1. create swagger and group about swagger for beauftiful
2. create all CRUD
3. create logger using logger onpython can debug all 
4. create seed.py for mockup
5. using skills for implements django only
6. using ruff only and mypy strict
[tool.mypy]
# Enable strict mode
strict = true

# Require type hints on all functions
disallow_untyped_defs = true

# Error out if a function returns an untyped 'Any'
warn_return_any = true

# Stop Python from implicitly treating None as a valid value
no_implicit_optional = true

7. keep it simple stupidest
````
