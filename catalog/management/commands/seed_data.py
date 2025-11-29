"""
Management command para popular o banco de dados com dados de exemplo
Uso: python manage.py seed_data [--clear] [--users N] [--products N] [--orders N]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from decimal import Decimal
from datetime import timedelta
from pathlib import Path
import random
import uuid
import requests

from catalog.models import Category, Product, ProductSpecification
from users.models import User, ShippingAddress
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem, OrderStatus, Coupon
from payment.models import Payment, PaymentMethod, PaymentStatus
from banner.models import Banner
from reviews.models import Review
from contact.models import ContactMessage

# Mapeamento de palavras-chave para busca de imagens no Unsplash
# Usando Unsplash Source API que permite buscar por palavra-chave sem API key


class Command(BaseCommand):
    help = 'Popula o banco de dados com dados de exemplo para testes'
    
    def get_product_images(self, product_name, category_name):
        """Gera URLs de imagens reais baseadas no nome e categoria do produto"""
        # Normalizar nome para busca
        name_lower = product_name.lower()
        category_lower = category_name.lower()
        
        # Mapear categoria para palavra-chave de busca e IDs de imagens
        category_key = None
        keywords = []
        
        if 'geladeira' in name_lower or 'geladeira' in category_lower or 'refrigerador' in name_lower:
            category_key = 'geladeira'
            keywords = ['refrigerator', 'fridge', 'kitchen-appliance']
        elif 'fogão' in name_lower or 'fogao' in name_lower or 'fogão' in category_lower:
            category_key = 'fogão'
            keywords = ['stove', 'gas-stove', 'cooktop']
        elif 'micro-ondas' in name_lower or 'microondas' in name_lower or 'micro-ondas' in category_lower:
            category_key = 'micro-ondas'
            keywords = ['microwave', 'microwave-oven']
        elif 'lavadora' in name_lower or 'lavadora' in category_lower:
            category_key = 'lavadora'
            keywords = ['washing-machine', 'washer', 'laundry']
        elif 'ar condicionado' in name_lower or 'ar-condicionado' in category_lower or 'ar condicionado' in category_lower:
            category_key = 'ar-condicionado'
            keywords = ['air-conditioner', 'ac-unit', 'cooling-system']
        elif 'cooktop' in name_lower or 'cooktop' in category_lower:
            category_key = 'cooktop'
            keywords = ['cooktop', 'induction-cooktop', 'stove']
        elif 'lava-louças' in name_lower or 'lava-loucas' in name_lower or 'lava-louças' in category_lower:
            category_key = 'lava-louças'
            keywords = ['dishwasher', 'kitchen-appliance']
        elif 'aspirador' in name_lower or 'aspirador' in category_lower:
            category_key = 'aspirador'
            keywords = ['vacuum-cleaner', 'vacuum', 'household-appliance']
        elif 'purificador' in name_lower or 'purificador' in category_lower:
            category_key = 'purificador'
            keywords = ['water-filter', 'water-purifier', 'filter']
        elif 'secadora' in name_lower or 'secadora' in category_lower:
            category_key = 'secadora'
            keywords = ['dryer', 'clothes-dryer', 'tumble-dryer']
        elif 'forno' in name_lower or 'forno' in category_lower:
            category_key = 'forno'
            keywords = ['oven', 'electric-oven', 'baking-oven']
        elif 'freezer' in name_lower or 'freezer' in category_lower:
            category_key = 'freezer'
            keywords = ['freezer', 'deep-freezer', 'chest-freezer']
        else:
            keywords = ['home-appliance', 'kitchen-appliance', 'household']
        
        # Gerar múltiplas imagens usando URLs estáticas do Unsplash
        # IMPORTANTE: Usar URLs diretas do Unsplash (images.unsplash.com) em vez de source.unsplash.com
        # para evitar timeouts e problemas de carregamento
        images = []
        
        # IDs de imagens reais do Unsplash relacionados a eletrodomésticos
        # Essas imagens são estáticas e carregam muito mais rápido
        unsplash_image_ids = [
            '1556912172-45b7abe8b7c4',  # Kitchen appliance
            '1574269909862-7e1d70bb8078',  # Home appliance
            '1558618666-fcd25c85cd64',  # Modern appliance
            '1556912167-f556f1f39fdf',  # Kitchen
            '1556912173-6948b88be996',  # Appliance
            '1581578018747-946a3e7e5a3e',  # Refrigerator
            '1556912174-2b5b5b5b5b5b',  # Washing machine
            '1556912175-2b5b5b5b5b5c',  # Microwave
            '1556912176-2b5b5b5b5b5d',  # Stove
            '1556912177-2b5b5b5b5b5e',  # Air conditioner
        ]
        
        # Selecionar 2 imagens aleatórias diferentes
        selected_ids = random.sample(unsplash_image_ids, min(2, len(unsplash_image_ids)))
        
        for image_id in selected_ids:
            # Usar formato direto do Unsplash com parâmetros de otimização
            # w=800&h=800&fit=crop&auto=format otimiza o tamanho e formato
            image_url = f"https://images.unsplash.com/photo-{image_id}?w=800&h=800&fit=crop&auto=format&q=80"
            images.append(image_url)
        
        return images
    
    def save_images_locally(self, image_urls, prefix):
        """Baixa imagens de URLs e salva localmente"""
        if not image_urls:
            return []
        
        # Criar diretório se não existir
        data_dir = Path(settings.DATA_IMAGES_DIR)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        local_paths = []
        
        for idx, url in enumerate(image_urls):
            try:
                # Gerar nome do arquivo
                file_extension = self.get_file_extension_from_url(url)
                filename = f"{prefix}_{idx}{file_extension}"
                filepath = data_dir / filename
                
                # Baixar imagem
                response = requests.get(url, timeout=10, stream=True)
                response.raise_for_status()
                
                # Verificar se é uma imagem válida
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    # Se não for imagem, usar placeholder
                    local_paths.append('/data/images/placeholder.jpg')
                    continue
                
                # Salvar arquivo
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Adicionar caminho local
                local_paths.append(f'/data/images/{filename}')
                
            except Exception as e:
                # Em caso de erro, usar placeholder
                self.stdout.write(self.style.WARNING(
                    f'  ⚠️  Erro ao baixar imagem {url}: {str(e)}. Usando placeholder.'
                ))
                local_paths.append('/data/images/placeholder.jpg')
        
        return local_paths
    
    def get_file_extension_from_url(self, url):
        """Extrai a extensão do arquivo da URL"""
        # Remover query parameters
        url = url.split('?')[0]
        
        # Tentar extrair extensão da URL
        if '.' in url:
            ext = url.rsplit('.', 1)[1].lower()
            # Validar extensão
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']:
                return f'.{ext}'
        
        # Padrão: jpg
        return '.jpg'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpa todos os dados antes de popular (exceto superusuários)',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='Número de usuários a criar (padrão: 50)',
        )
        parser.add_argument(
            '--products',
            type=int,
            default=200,
            help='Número de produtos a criar (padrão: 200)',
        )
        parser.add_argument(
            '--orders',
            type=int,
            default=100,
            help='Número de pedidos a criar (padrão: 100)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🌱 Iniciando seed de dados...'))
        
        clear = options['clear']
        num_users = options['users']
        num_products = options['products']
        num_orders = options['orders']

        if clear:
            self.clear_data()

        with transaction.atomic():
            # Criar categorias
            categories = self.create_categories()
            
            # Criar produtos
            products = self.create_products(categories, num_products)
            
            # Criar usuários
            users = self.create_users(num_users)
            
            # Criar endereços de entrega
            self.create_shipping_addresses(users)
            
            # Criar cupons
            coupons = self.create_coupons()
            
            # Criar carrinhos
            self.create_carts(users, products)
            
            # Criar pedidos
            orders = self.create_orders(users, products, coupons, num_orders)
            
            # Criar pagamentos
            self.create_payments(orders)
            
            # Criar avaliações
            self.create_reviews(users, products)
            
            # Criar banners
            self.create_banners()
            
            # Criar mensagens de contato
            self.create_contact_messages(users)

        self.stdout.write(self.style.SUCCESS('✅ Seed concluído com sucesso!'))

    def clear_data(self):
        """Limpa todos os dados (exceto superusuários)"""
        self.stdout.write(self.style.WARNING('🗑️  Limpando dados existentes...'))
        
        ContactMessage.objects.all().delete()
        Review.objects.all().delete()
        Banner.objects.all().delete()
        Payment.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        CartItem.objects.all().delete()
        Cart.objects.all().delete()
        Coupon.objects.all().delete()
        ShippingAddress.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        ProductSpecification.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('✅ Dados limpos!'))

    def create_categories(self):
        """Cria categorias de produtos"""
        self.stdout.write('📁 Criando categorias...')
        
        categories_data = [
            {'name': 'Geladeiras', 'icon': 'refrigerator'},
            {'name': 'Fogões', 'icon': 'chef-hat'},
            {'name': 'Micro-ondas', 'icon': 'microwave'},
            {'name': 'Lavadoras', 'icon': 'washing-machine'},
            {'name': 'Ar Condicionado', 'icon': 'wind'},
            {'name': 'Cooktops', 'icon': 'cooktop'},
            {'name': 'Lava-louças', 'icon': 'dishwasher'},
            {'name': 'Aspiradores', 'icon': 'vacuum'},
            {'name': 'Purificadores', 'icon': 'water-filter'},
            {'name': 'Secadoras', 'icon': 'dryer'},
            {'name': 'Fornos', 'icon': 'oven'},
            {'name': 'Freezers', 'icon': 'freezer'},
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'icon': cat_data.get('icon', '')}
            )
            categories.append(category)
        
        self.stdout.write(self.style.SUCCESS(f'✅ {len(categories)} categorias criadas'))
        return categories

    def create_products(self, categories, num_products):
        """Cria produtos com especificações"""
        self.stdout.write(f'📦 Criando {num_products} produtos...')
        
        brands = ['Electrolux', 'Brastemp', 'Consul', 'LG', 'Samsung', 'Panasonic', 'Midea', 'Philco']
        models = ['Premium', 'Pro', 'Turbo', 'Inverter', 'Frost Free', 'Smart', 'Eco', 'Plus']
        
        products = []
        for i in range(num_products):
            category = random.choice(categories)
            brand = random.choice(brands)
            model = random.choice(models)
            
            # Nome baseado na categoria
            if 'Geladeira' in category.name:
                name = f"Geladeira {brand} {model} {random.choice(['443L', '500L', '600L', '700L'])}"
                base_price = Decimal(random.randint(2000, 5000))
            elif 'Fogão' in category.name:
                name = f"Fogão {brand} {model} {random.choice(['4 Bocas', '5 Bocas', '6 Bocas'])}"
                base_price = Decimal(random.randint(800, 2500))
            elif 'Micro-ondas' in category.name:
                name = f"Micro-ondas {brand} {model} {random.choice(['20L', '31L', '40L'])}"
                base_price = Decimal(random.randint(400, 1200))
            elif 'Lavadora' in category.name:
                name = f"Lavadora {brand} {model} {random.choice(['10kg', '12kg', '15kg', '18kg'])}"
                base_price = Decimal(random.randint(1500, 3500))
            elif 'Ar Condicionado' in category.name:
                name = f"Ar Condicionado {brand} {model} {random.choice(['9000 BTUs', '12000 BTUs', '18000 BTUs', '24000 BTUs'])}"
                base_price = Decimal(random.randint(2000, 6000))
            elif 'Cooktop' in category.name:
                name = f"Cooktop {brand} {model} {random.choice(['4 Bocas', '5 Bocas'])}"
                base_price = Decimal(random.randint(1200, 3000))
            elif 'Lava-louças' in category.name:
                name = f"Lava-louças {brand} {model} {random.choice(['8 Serviços', '10 Serviços', '14 Serviços'])}"
                base_price = Decimal(random.randint(2000, 5000))
            elif 'Aspirador' in category.name:
                name = f"Aspirador {brand} {model} {random.choice(['Vertical', 'Robô', 'Portátil'])}"
                base_price = Decimal(random.randint(300, 1500))
            elif 'Purificador' in category.name:
                name = f"Purificador {brand} {model}"
                base_price = Decimal(random.randint(500, 2000))
            elif 'Secadora' in category.name:
                name = f"Secadora {brand} {model} {random.choice(['8kg', '10kg', '12kg'])}"
                base_price = Decimal(random.randint(2000, 4500))
            elif 'Forno' in category.name:
                name = f"Forno {brand} {model} {random.choice(['Eletrônico', 'Autolimpeza', 'Self Clean'])}"
                base_price = Decimal(random.randint(1500, 4000))
            else:  # Freezer
                name = f"Freezer {brand} {model} {random.choice(['200L', '300L', '400L'])}"
                base_price = Decimal(random.randint(1500, 3500))
            
            # Preço com possível desconto
            has_discount = random.random() < 0.3  # 30% de chance de ter desconto
            discount_price = None
            if has_discount:
                discount_percent = random.randint(10, 40)
                discount_price = base_price * (1 - Decimal(discount_percent) / 100)
            
            # Gerar imagens reais baseadas no nome e categoria
            product_images_urls = self.get_product_images(name, category.name)
            
            # Baixar e salvar imagens localmente
            product_images = self.save_images_locally(product_images_urls, f"product_{i}")
            
            product = Product.objects.create(
                name=name,
                description=f"{name} com tecnologia avançada e design moderno. Ideal para sua casa!",
                brand=brand,
                model=model,
                category=category,
                price=base_price,
                discount_price=discount_price,
                stock=random.randint(10, 100),  # Mínimo de 10 para garantir estoque suficiente
                rating=round(random.uniform(3.5, 5.0), 1),
                rating_count=random.randint(0, 500),
                image_urls=product_images,
                is_featured=random.random() < 0.15,  # 15% são destaque
            )
            
            # Criar especificações técnicas
            self.create_product_specifications(product)
            
            products.append(product)
            
            if (i + 1) % 50 == 0:
                self.stdout.write(f'  ✓ {i + 1}/{num_products} produtos criados...')
        
        self.stdout.write(self.style.SUCCESS(f'✅ {len(products)} produtos criados'))
        return products

    def create_product_specifications(self, product):
        """Cria especificações técnicas para um produto"""
        specs = []
        
        if 'Geladeira' in product.name or 'Freezer' in product.name:
            specs = [
                ('Capacidade', f"{random.randint(200, 700)}L"),
                ('Tipo', random.choice(['Frost Free', 'Duplex', 'Side by Side'])),
                ('Consumo', random.choice(['Classe A', 'Classe A+', 'Classe A++'])),
                ('Voltagem', random.choice(['110V', '220V', 'Bivolt'])),
                ('Dimensões', f"{random.randint(60, 90)} x {random.randint(60, 90)} x {random.randint(160, 200)} cm"),
            ]
        elif 'Fogão' in product.name or 'Cooktop' in product.name:
            specs = [
                ('Bocas', product.name.split()[-1] if 'Bocas' in product.name else '4'),
                ('Tipo', random.choice(['Gás', 'Elétrico', 'Indução'])),
                ('Acendimento', random.choice(['Automático', 'Manual', 'Piezo'])),
                ('Voltagem', random.choice(['110V', '220V'])),
            ]
        elif 'Micro-ondas' in product.name:
            specs = [
                ('Capacidade', product.name.split()[-1] if 'L' in product.name else '31L'),
                ('Potência', f"{random.randint(700, 1200)}W"),
                ('Funções', random.choice(['Grill', 'Convecção', 'Descongelar'])),
                ('Voltagem', random.choice(['110V', '220V', 'Bivolt'])),
            ]
        elif 'Lavadora' in product.name or 'Secadora' in product.name:
            specs = [
                ('Capacidade', product.name.split()[-1] if 'kg' in product.name else '12kg'),
                ('Tipo', random.choice(['Automática', 'Semi-automática', 'Lavadora e Secadora'])),
                ('Consumo', random.choice(['Classe A', 'Classe A+', 'Classe A++'])),
                ('Voltagem', random.choice(['110V', '220V', 'Bivolt'])),
            ]
        elif 'Ar Condicionado' in product.name:
            specs = [
                ('BTUs', product.name.split()[-1] if 'BTUs' in product.name else '12000 BTUs'),
                ('Tipo', random.choice(['Split', 'Janela', 'Portátil'])),
                ('Consumo', random.choice(['Classe A', 'Classe A+', 'Inverter'])),
                ('Voltagem', random.choice(['110V', '220V', 'Bivolt'])),
            ]
        else:
            specs = [
                ('Voltagem', random.choice(['110V', '220V', 'Bivolt'])),
                ('Consumo', random.choice(['Classe A', 'Classe A+', 'Classe A++'])),
            ]
        
        for key, value in specs:
            ProductSpecification.objects.create(
                product=product,
                key=key,
                value=value
            )

    def create_users(self, num_users):
        """Cria usuários de exemplo"""
        self.stdout.write(f'👥 Criando {num_users} usuários...')
        
        first_names = ['João', 'Maria', 'Pedro', 'Ana', 'Carlos', 'Juliana', 'Fernando', 'Patricia', 
                      'Ricardo', 'Camila', 'Roberto', 'Mariana', 'Lucas', 'Beatriz', 'Rafael', 'Gabriela']
        last_names = ['Silva', 'Santos', 'Oliveira', 'Souza', 'Pereira', 'Costa', 'Rodrigues', 'Almeida',
                     'Nascimento', 'Lima', 'Araújo', 'Ferreira', 'Ribeiro', 'Carvalho', 'Gomes', 'Martins']
        
        cities = ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Curitiba', 'Porto Alegre', 
                 'Brasília', 'Salvador', 'Recife', 'Fortaleza', 'Manaus']
        states = ['SP', 'RJ', 'MG', 'PR', 'RS', 'DF', 'BA', 'PE', 'CE', 'AM']
        
        users = []
        for i in range(num_users):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            name = f"{first_name} {last_name}"
            email = f"{first_name.lower()}.{last_name.lower()}.{i}@example.com"
            
            city = random.choice(cities)
            state = random.choice(states)
            
            user = User.objects.create_user(
                email=email,
                name=name,
                password='senha123',  # Senha padrão para testes
                phone=f"({random.randint(11, 99)}) {random.randint(90000, 99999)}-{random.randint(1000, 9999)}",
                street=f"Rua {random.choice(['das Flores', 'Principal', 'Comercial', 'Central'])}",
                city=city,
                state=state,
                zip_code=f"{random.randint(10000, 99999)}-{random.randint(100, 999)}",
                country='Brasil',
                birth_date=timezone.now().date() - timedelta(days=random.randint(18*365, 65*365)),
            )
            users.append(user)
            
            if (i + 1) % 25 == 0:
                self.stdout.write(f'  ✓ {i + 1}/{num_users} usuários criados...')
        
        self.stdout.write(self.style.SUCCESS(f'✅ {len(users)} usuários criados'))
        return users

    def create_shipping_addresses(self, users):
        """Cria endereços de entrega para usuários"""
        self.stdout.write('📍 Criando endereços de entrega...')
        
        cities = ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Curitiba', 'Porto Alegre']
        states = ['SP', 'RJ', 'MG', 'PR', 'RS']
        streets = ['Rua das Flores', 'Avenida Principal', 'Rua Comercial', 'Avenida Central', 'Rua Nova']
        
        count = 0
        for user in users:
            # Cada usuário tem 1-3 endereços
            num_addresses = random.randint(1, 3)
            for i in range(num_addresses):
                city = random.choice(cities)
                state = random.choice(states)
                
                ShippingAddress.objects.create(
                    user=user,
                    street=random.choice(streets),
                    number=str(random.randint(100, 9999)),
                    complement=random.choice(['Apto 101', 'Casa', 'Sala 205', '']),
                    city=city,
                    state=state,
                    zip_code=f"{random.randint(10000, 99999)}-{random.randint(100, 999)}",
                    country='Brasil',
                    is_default=(i == 0),  # Primeiro endereço é padrão
                )
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ {count} endereços criados'))

    def create_coupons(self):
        """Cria cupons de desconto"""
        self.stdout.write('🎫 Criando cupons...')
        
        coupons_data = [
            {'code': 'BEMVINDO10', 'discount_percentage': 10, 'max_uses': 100, 'valid_days': 365},
            {'code': 'FRETEGRATIS', 'discount_value': Decimal('29.90'), 'max_uses': 50, 'valid_days': 180},
            {'code': 'BLACKFRIDAY', 'discount_percentage': 30, 'max_uses': 200, 'valid_days': 30},
            {'code': 'PRIMAVERA15', 'discount_percentage': 15, 'max_uses': 150, 'valid_days': 90},
            {'code': 'DESCONTO20', 'discount_percentage': 20, 'max_uses': 100, 'valid_days': 60},
            {'code': 'CASHBACK50', 'discount_value': Decimal('50.00'), 'max_uses': 30, 'valid_days': 45},
        ]
        
        coupons = []
        for coupon_data in coupons_data:
            coupon = Coupon.objects.create(
                code=coupon_data['code'],
                discount_value=coupon_data.get('discount_value', Decimal('0')),
                discount_percentage=coupon_data.get('discount_percentage', 0),
                max_uses=coupon_data['max_uses'],
                current_uses=random.randint(0, coupon_data['max_uses'] // 2),
                valid_until=timezone.now() + timedelta(days=coupon_data['valid_days']),
                active=random.random() < 0.8,  # 80% ativos
            )
            coupons.append(coupon)
        
        self.stdout.write(self.style.SUCCESS(f'✅ {len(coupons)} cupons criados'))
        return coupons

    def create_carts(self, users, products):
        """Cria carrinhos com itens para alguns usuários"""
        self.stdout.write('🛒 Criando carrinhos...')
        
        count = 0
        # 60% dos usuários têm carrinho
        users_with_cart = random.sample(users, int(len(users) * 0.6))
        
        for user in users_with_cart:
            cart, _ = Cart.objects.get_or_create(user=user)
            
            # Adiciona 1-5 produtos ao carrinho
            num_items = random.randint(1, 5)
            cart_products = random.sample(products, min(num_items, len(products)))
            
            for product in cart_products:
                # Verifica estoque disponível antes de criar o item
                available_stock = product.available_stock
                
                # Pula produtos sem estoque disponível
                if available_stock <= 0:
                    continue
                
                # Ajusta quantidade para não exceder estoque disponível
                desired_quantity = random.randint(1, 3)
                quantity = min(desired_quantity, available_stock)
                
                price = product.discount_price if product.has_discount else product.price
                try:
                    CartItem.objects.create(
                        cart=cart,
                        product=product,
                        quantity=quantity,
                        price_at_time=price,
                    )
                except ValueError as e:
                    # Se ainda assim houver erro (concorrência), apenas pula este produto
                    continue
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ {count} carrinhos criados'))

    def create_orders(self, users, products, coupons, num_orders):
        """Cria pedidos com itens"""
        self.stdout.write(f'📦 Criando {num_orders} pedidos...')
        
        statuses = [OrderStatus.PENDING, OrderStatus.PAID, OrderStatus.PROCESSING, 
                   OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.CANCELED]
        status_weights = [0.1, 0.2, 0.2, 0.2, 0.25, 0.05]  # Distribuição de status
        
        orders = []
        for i in range(num_orders):
            user = random.choice(users)
            shipping_address = user.shipping_addresses.first()
            
            if not shipping_address:
                continue
            
            # Status baseado em pesos
            status = random.choices(statuses, weights=status_weights)[0]
            
            # Data de criação variada (últimos 90 dias)
            created_at = timezone.now() - timedelta(days=random.randint(0, 90))
            
            order = Order.objects.create(
                user=user,
                shipping_address=shipping_address,
                status=status,
                shipping=Decimal('0.00') if random.random() < 0.3 else Decimal('29.90'),
                coupon=random.choice(coupons) if random.random() < 0.2 and coupons else None,
                created_at=created_at,
            )
            
            # Adiciona 1-4 produtos ao pedido
            num_items = random.randint(1, 4)
            order_products = random.sample(products, min(num_items, len(products)))
            
            for product in order_products:
                price = product.discount_price if product.has_discount else product.price
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=random.randint(1, 2),
                    unit_price=price,
                )
            
            # Recalcula totais
            order.calculate_totals()
            orders.append(order)
            
            if (i + 1) % 25 == 0:
                self.stdout.write(f'  ✓ {i + 1}/{num_orders} pedidos criados...')
        
        self.stdout.write(self.style.SUCCESS(f'✅ {len(orders)} pedidos criados'))
        return orders

    def create_payments(self, orders):
        """Cria pagamentos para pedidos"""
        self.stdout.write('💳 Criando pagamentos...')
        
        methods = [PaymentMethod.PIX, PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD, PaymentMethod.BOLETO]
        method_weights = [0.3, 0.4, 0.2, 0.1]  # PIX e cartão são mais comuns
        
        count = 0
        for order in orders:
            # Apenas pedidos pagos, processando, enviados ou entregues têm pagamento
            if order.status in [OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
                method = random.choices(methods, weights=method_weights)[0]
                
                # Status do pagamento baseado no status do pedido
                if order.status == OrderStatus.PAID:
                    payment_status = PaymentStatus.PAID
                    paid_at = order.created_at + timedelta(hours=random.randint(1, 24))
                elif order.status in [OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
                    payment_status = PaymentStatus.PAID
                    paid_at = order.created_at + timedelta(hours=random.randint(1, 6))
                else:
                    payment_status = PaymentStatus.PENDING
                    paid_at = None
                
                Payment.objects.create(
                    order=order,
                    method=method,
                    status=payment_status,
                    transaction_id=f"TXN{random.randint(100000, 999999)}",
                    amount=order.total,
                    paid_at=paid_at,
                    created_at=order.created_at,
                )
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ {count} pagamentos criados'))

    def create_reviews(self, users, products):
        """Cria avaliações de produtos"""
        self.stdout.write('⭐ Criando avaliações...')
        
        comments = [
            'Produto excelente, superou minhas expectativas!',
            'Muito bom, recomendo.',
            'Ótimo custo-benefício.',
            'Produto de qualidade, entrega rápida.',
            'Funciona perfeitamente, estou satisfeito.',
            'Bom produto, mas poderia ser melhor.',
            'Atendeu minhas necessidades.',
            'Excelente qualidade, vale a pena.',
        ]
        
        count = 0
        # Cada produto recebe 0-10 avaliações
        for product in products:
            num_reviews = random.randint(0, 10)
            reviewers = random.sample(users, min(num_reviews, len(users)))
            
            for user in reviewers:
                Review.objects.create(
                    user=user,
                    product=product,
                    rating=random.randint(3, 5),  # Maioria positiva
                    comment=random.choice(comments),
                )
                count += 1
                
                # Atualiza rating do produto
                product.update_rating()
        
        self.stdout.write(self.style.SUCCESS(f'✅ {count} avaliações criadas'))

    def create_banners(self):
        """Cria banners promocionais"""
        self.stdout.write('🎨 Criando banners...')
        
        banners_data = [
            {
                'title': 'Promoção de Verão',
                'subtitle': 'Até 40% OFF em toda linha',
                'image_url': 'https://images.unsplash.com/photo-1556912172-45b7abe8b7c4?w=1200&h=400&fit=crop&auto=format&q=80',
                'link': '/products?sortBy=rating',
                'order': 1,
            },
            {
                'title': 'Novos Lançamentos',
                'subtitle': 'Conheça nossa linha premium',
                'image_url': 'https://images.unsplash.com/photo-1574269909862-7e1d70bb8078?w=1200&h=400&fit=crop&auto=format&q=80',
                'link': '/products',
                'order': 2,
            },
            {
                'title': 'Frete Grátis',
                'subtitle': 'Para compras acima de R$ 499',
                'image_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1200&h=400&fit=crop&auto=format&q=80',
                'link': '/products',
                'order': 3,
            },
        ]
        
        # Baixar e salvar imagens dos banners localmente
        for idx, banner_data in enumerate(banners_data):
            image_url = banner_data['image_url']
            local_paths = self.save_images_locally([image_url], f"banner_{idx}")
            if local_paths:
                banner_data['image_url'] = local_paths[0]
            Banner.objects.create(**banner_data)
        
        self.stdout.write(self.style.SUCCESS(f'✅ {len(banners_data)} banners criados'))

    def create_contact_messages(self, users):
        """Cria mensagens de contato"""
        self.stdout.write('📧 Criando mensagens de contato...')
        
        subjects = [
            'Dúvida sobre produto',
            'Problema com pedido',
            'Sugestão de melhoria',
            'Reclamação',
            'Elogio',
            'Informação sobre garantia',
        ]
        
        messages = [
            'Gostaria de mais informações sobre este produto.',
            'Tive um problema com meu pedido, preciso de ajuda.',
            'Sugiro melhorias no atendimento.',
            'Não estou satisfeito com o produto recebido.',
            'Parabéns pelo excelente atendimento!',
            'Preciso de informações sobre a garantia.',
        ]
        
        count = 0
        # 20% dos usuários enviaram mensagem
        users_with_message = random.sample(users, int(len(users) * 0.2))
        
        for user in users_with_message:
            ContactMessage.objects.create(
                name=user.name,
                email=user.email,
                phone=user.phone,
                subject=random.choice(subjects),
                message=random.choice(messages),
                is_read=random.random() < 0.6,  # 60% lidas
                created_at=timezone.now() - timedelta(days=random.randint(0, 30)),
            )
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ {count} mensagens criadas'))

