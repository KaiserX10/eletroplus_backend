from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from users.models import User
from .models import Category, Product, ProductSpecification


class CategoryAPITestCase(TestCase):
    """Testes para API de Categorias"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = APIClient()
        
        # Criar usuário admin/staff
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            name='Admin User',
            password='testpass123',
            is_staff=True
        )
        
        # Criar usuário comum (não-admin)
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            name='Regular User',
            password='testpass123',
            is_staff=False
        )
        
        # Obter token JWT para admin
        refresh = RefreshToken.for_user(self.admin_user)
        self.admin_token = str(refresh.access_token)
        
        # Obter token JWT para usuário comum
        refresh_regular = RefreshToken.for_user(self.regular_user)
        self.regular_token = str(refresh_regular.access_token)
        
        # URL base para categorias
        self.category_list_url = reverse('category-list')
    
    def test_create_category_as_admin(self):
        """Testa criação de categoria por usuário admin"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        data = {
            'name': 'Geladeiras',
            'icon': 'fridge'
        }
        
        response = self.client.post(self.category_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Category.objects.get().name, 'Geladeiras')
        self.assertEqual(Category.objects.get().slug, 'geladeiras')
        self.assertIn('id', response.data)
        self.assertIn('slug', response.data)
        self.assertIn('created_at', response.data)
    
    def test_create_category_without_authentication(self):
        """Testa que usuário não autenticado não pode criar categoria"""
        data = {
            'name': 'Fogões',
            'icon': 'stove'
        }
        
        response = self.client.post(self.category_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Category.objects.count(), 0)
    
    def test_create_category_as_regular_user(self):
        """Testa que usuário comum não pode criar categoria"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
        
        data = {
            'name': 'Micro-ondas',
            'icon': 'microwave'
        }
        
        response = self.client.post(self.category_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Category.objects.count(), 0)
    
    def test_list_categories_without_authentication(self):
        """Testa que qualquer pessoa pode listar categorias (read-only)"""
        # Criar categoria diretamente no banco
        Category.objects.create(name='Test Category', slug='test-category')
        
        response = self.client.get(self.category_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_category_duplicate_name(self):
        """Testa que não é possível criar categoria com nome duplicado"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        # Criar primeira categoria
        Category.objects.create(name='Geladeiras', slug='geladeiras')
        
        # Tentar criar categoria com mesmo nome
        data = {
            'name': 'Geladeiras',
            'icon': 'fridge'
        }
        
        response = self.client.post(self.category_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Category.objects.count(), 1)
    
    def test_update_category_as_admin(self):
        """Testa atualização de categoria por admin"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        category = Category.objects.create(name='Geladeiras', slug='geladeiras')
        url = reverse('category-detail', kwargs={'slug': category.slug})
        
        data = {
            'name': 'Geladeiras Premium',
            'icon': 'fridge-premium'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        category.refresh_from_db()
        self.assertEqual(category.name, 'Geladeiras Premium')
    
    def test_delete_category_as_admin(self):
        """Testa exclusão de categoria por admin"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        category = Category.objects.create(name='Geladeiras', slug='geladeiras')
        url = reverse('category-detail', kwargs={'slug': category.slug})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)


class ProductAPITestCase(TestCase):
    """Testes para API de Produtos"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = APIClient()
        
        # Criar usuário admin/staff
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            name='Admin User',
            password='testpass123',
            is_staff=True
        )
        
        # Criar usuário comum (não-admin)
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            name='Regular User',
            password='testpass123',
            is_staff=False
        )
        
        # Criar categoria de teste
        self.category = Category.objects.create(
            name='Geladeiras',
            slug='geladeiras'
        )
        
        # Obter token JWT para admin
        refresh = RefreshToken.for_user(self.admin_user)
        self.admin_token = str(refresh.access_token)
        
        # Obter token JWT para usuário comum
        refresh_regular = RefreshToken.for_user(self.regular_user)
        self.regular_token = str(refresh_regular.access_token)
        
        # URL base para produtos
        self.product_list_url = reverse('product-list')
    
    def test_create_product_as_admin(self):
        """Testa criação de produto por usuário admin"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        data = {
            'name': 'Geladeira Brastemp',
            'description': 'Geladeira frost-free com capacidade de 300L',
            'brand': 'Brastemp',
            'model': 'BRM45HK',
            'category': str(self.category.id),
            'price': '2999.99',
            'discount_price': '2499.99',
            'stock': 10,
            'image_urls': [
                'https://example.com/image1.jpg',
                'https://example.com/image2.jpg'
            ],
            'is_featured': True
        }
        
        response = self.client.post(self.product_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)
        
        product = Product.objects.get()
        self.assertEqual(product.name, 'Geladeira Brastemp')
        self.assertEqual(product.brand, 'Brastemp')
        self.assertEqual(product.price, Decimal('2999.99'))
        self.assertEqual(product.discount_price, Decimal('2499.99'))
        self.assertEqual(product.stock, 10)
        self.assertEqual(product.is_featured, True)
        self.assertIn('id', response.data)
    
    def test_create_product_with_specifications(self):
        """Testa criação de produto com especificações técnicas"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        data = {
            'name': 'Geladeira Brastemp',
            'description': 'Geladeira frost-free com capacidade de 300L',
            'brand': 'Brastemp',
            'model': 'BRM45HK',
            'category': str(self.category.id),
            'price': '2999.99',
            'stock': 10,
            'specifications': [
                {'key': 'Capacidade', 'value': '300L'},
                {'key': 'Voltagem', 'value': '220V'},
                {'key': 'Tipo', 'value': 'Frost-Free'}
            ]
        }
        
        response = self.client.post(self.product_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product = Product.objects.get()
        self.assertEqual(product.specifications.count(), 3)
        
        specs = product.specifications.all()
        self.assertEqual(specs[0].key, 'Capacidade')
        self.assertEqual(specs[0].value, '300L')
    
    def test_create_product_without_authentication(self):
        """Testa que usuário não autenticado não pode criar produto"""
        data = {
            'name': 'Geladeira Brastemp',
            'description': 'Geladeira frost-free',
            'brand': 'Brastemp',
            'model': 'BRM45HK',
            'category': str(self.category.id),
            'price': '2999.99',
            'stock': 10
        }
        
        response = self.client.post(self.product_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Product.objects.count(), 0)
    
    def test_create_product_as_regular_user(self):
        """Testa que usuário comum não pode criar produto"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
        
        data = {
            'name': 'Geladeira Brastemp',
            'description': 'Geladeira frost-free',
            'brand': 'Brastemp',
            'model': 'BRM45HK',
            'category': str(self.category.id),
            'price': '2999.99',
            'stock': 10
        }
        
        response = self.client.post(self.product_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Product.objects.count(), 0)
    
    def test_list_products_without_authentication(self):
        """Testa que qualquer pessoa pode listar produtos (read-only)"""
        # Criar produto diretamente no banco
        Product.objects.create(
            name='Geladeira Test',
            description='Descrição teste',
            brand='Test Brand',
            model='Test Model',
            category=self.category,
            price=Decimal('1999.99'),
            stock=5
        )
        
        response = self.client.get(self.product_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_create_product_missing_required_fields(self):
        """Testa validação de campos obrigatórios ao criar produto"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        data = {
            'name': 'Geladeira Brastemp',
            # Faltando campos obrigatórios
        }
        
        response = self.client.post(self.product_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('description', response.data)
        self.assertIn('brand', response.data)
        self.assertIn('model', response.data)
        self.assertIn('category', response.data)
        self.assertIn('price', response.data)
        self.assertEqual(Product.objects.count(), 0)
    
    def test_create_product_invalid_price(self):
        """Testa validação de preço negativo"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        data = {
            'name': 'Geladeira Brastemp',
            'description': 'Geladeira frost-free',
            'brand': 'Brastemp',
            'model': 'BRM45HK',
            'category': str(self.category.id),
            'price': '-100.00',  # Preço negativo
            'stock': 10
        }
        
        response = self.client.post(self.product_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Product.objects.count(), 0)
    
    def test_create_product_invalid_stock(self):
        """Testa validação de estoque negativo"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        data = {
            'name': 'Geladeira Brastemp',
            'description': 'Geladeira frost-free',
            'brand': 'Brastemp',
            'model': 'BRM45HK',
            'category': str(self.category.id),
            'price': '2999.99',
            'stock': -5  # Estoque negativo
        }
        
        response = self.client.post(self.product_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Product.objects.count(), 0)
    
    def test_update_product_as_admin(self):
        """Testa atualização de produto por admin"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        product = Product.objects.create(
            name='Geladeira Test',
            description='Descrição teste',
            brand='Test Brand',
            model='Test Model',
            category=self.category,
            price=Decimal('1999.99'),
            stock=5
        )
        url = reverse('product-detail', kwargs={'pk': product.id})
        
        data = {
            'price': '2499.99',
            'stock': 15
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.price, Decimal('2499.99'))
        self.assertEqual(product.stock, 15)
    
    def test_delete_product_as_admin(self):
        """Testa exclusão de produto por admin"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        product = Product.objects.create(
            name='Geladeira Test',
            description='Descrição teste',
            brand='Test Brand',
            model='Test Model',
            category=self.category,
            price=Decimal('1999.99'),
            stock=5
        )
        url = reverse('product-detail', kwargs={'pk': product.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)
    
    def test_create_product_discount_price_validation(self):
        """Testa que discount_price pode ser menor que price"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        data = {
            'name': 'Geladeira Brastemp',
            'description': 'Geladeira frost-free',
            'brand': 'Brastemp',
            'model': 'BRM45HK',
            'category': str(self.category.id),
            'price': '2999.99',
            'discount_price': '2499.99',  # Desconto válido
            'stock': 10
        }
        
        response = self.client.post(self.product_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product = Product.objects.get()
        self.assertEqual(product.discount_price, Decimal('2499.99'))
        self.assertTrue(product.has_discount)
        self.assertEqual(product.discount_percentage, 16)  # Aproximadamente 16%
    
    def test_create_product_invalid_category(self):
        """Testa validação de categoria inválida"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        data = {
            'name': 'Geladeira Brastemp',
            'description': 'Geladeira frost-free',
            'brand': 'Brastemp',
            'model': 'BRM45HK',
            'category': '00000000-0000-0000-0000-000000000000',  # UUID inválido
            'price': '2999.99',
            'stock': 10
        }
        
        response = self.client.post(self.product_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Product.objects.count(), 0)
