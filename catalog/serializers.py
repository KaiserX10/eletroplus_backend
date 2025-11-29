from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Category, Product, ProductSpecification
from .utils import save_uploaded_image, validate_image_file, MAX_IMAGES_PER_UPLOAD


class ProductSpecificationSerializer(serializers.ModelSerializer):
    """Serializer para Especificação Técnica"""
    
    class Meta:
        model = ProductSpecification
        fields = ['id', 'key', 'value', 'created_at']
        read_only_fields = ['id', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para Categoria"""
    products_count = serializers.IntegerField(source='products.count', read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'products_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class CategoryDetailSerializer(CategorySerializer):
    """Serializer detalhado para Categoria com produtos"""
    products = serializers.SerializerMethodField()
    
    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ['products']
    
    def get_products(self, obj):
        """Retorna lista resumida de produtos da categoria"""
        products = obj.products.all()[:10]  # Limita a 10 produtos
        return ProductListSerializer(products, many=True).data


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer resumido para lista de produtos"""
    category = CategorySerializer(read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'brand', 'model', 'category',
            'price', 'discount_price', 'has_discount', 'discount_percentage',
            'stock', 'rating', 'rating_count',
            'image_urls', 'is_featured', 'created_at'
        ]
        read_only_fields = ['id', 'rating', 'rating_count', 'created_at']


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado para produto com especificações"""
    category = CategorySerializer(read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'brand', 'model', 'category',
            'price', 'discount_price', 'has_discount', 'discount_percentage',
            'stock', 'rating', 'rating_count',
            'image_urls', 'is_featured',
            'specifications', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'rating', 'rating_count', 'created_at', 'updated_at']


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criar/atualizar produto"""
    specifications = ProductSpecificationSerializer(many=True, required=False, allow_null=True)
    images = serializers.ListField(
        child=serializers.ImageField(required=False),
        required=False,
        allow_empty=True,
        allow_null=True,
        write_only=True,
        help_text='Lista de arquivos de imagem para upload (máximo 10)'
    )
    remove_all_images = serializers.BooleanField(required=False, write_only=True, help_text='Remove todas as imagens se True')
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'brand', 'model', 'category',
            'price', 'discount_price', 'stock',
            'image_urls', 'is_featured', 'specifications', 'images', 'remove_all_images'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'image_urls': {'required': False, 'allow_null': True}
        }
    
    def validate_images(self, value):
        """Valida lista de imagens"""
        if value is None:
            return value
        
        if len(value) > MAX_IMAGES_PER_UPLOAD:
            raise ValidationError(f'Máximo de {MAX_IMAGES_PER_UPLOAD} imagens por upload')
        
        # Validar cada imagem
        for image in value:
            if image:  # Ignorar None/empty
                try:
                    validate_image_file(image)
                except ValidationError as e:
                    raise ValidationError(f'Erro na imagem {image.name}: {str(e)}')
        
        return value
    
    def create(self, validated_data):
        """Cria produto com suas especificações e imagens"""
        specifications_data = validated_data.pop('specifications', [])
        
        # Se specifications_data for string (vindo de FormData como JSON string), fazer parse
        if isinstance(specifications_data, str):
            import json
            try:
                specifications_data = json.loads(specifications_data) if specifications_data else []
            except (json.JSONDecodeError, TypeError):
                specifications_data = []
        elif specifications_data is None:
            specifications_data = []
        
        images_data = validated_data.pop('images', [])
        
        # Processar e salvar imagens se fornecidas
        if images_data:
            image_paths = []
            request = self.context.get('request')
            
            for image in images_data:
                try:
                    image_path = save_uploaded_image(image, prefix='product')
                    image_paths.append(image_path)
                except ValidationError as e:
                    raise ValidationError(f'Erro ao salvar imagem {image.name}: {str(e)}')
            
            # Atualizar image_urls com os caminhos salvos
            validated_data['image_urls'] = image_paths
        elif 'image_urls' not in validated_data:
            # Se não forneceu imagens nem image_urls, usar lista vazia
            validated_data['image_urls'] = []
        
        product = Product.objects.create(**validated_data)
        
        # Criar especificações
        for spec_data in specifications_data:
            ProductSpecification.objects.create(product=product, **spec_data)
        
        return product
    
    def update(self, instance, validated_data):
        """Atualiza produto e suas especificações e imagens"""
        specifications_data = validated_data.pop('specifications', None)
        
        # Se specifications_data for string (vindo de FormData como JSON), fazer parse
        if isinstance(specifications_data, str):
            import json
            try:
                specifications_data = json.loads(specifications_data) if specifications_data else None
            except (json.JSONDecodeError, TypeError):
                specifications_data = None
        
        images_data = validated_data.pop('images', None)
        remove_all_images = validated_data.pop('remove_all_images', False)
        
        # Processar imagens se fornecidas
        if remove_all_images:
            # Remover todas as imagens
            validated_data['image_urls'] = []
        elif images_data is not None:
            # Filtrar valores None/vazios
            images_data = [img for img in images_data if img]
            
            if images_data:
                # Novas imagens fornecidas - substituir todas
                image_paths = []
                for image in images_data:
                    try:
                        image_path = save_uploaded_image(image, prefix='product')
                        image_paths.append(image_path)
                    except ValidationError as e:
                        raise ValidationError(f'Erro ao salvar imagem {image.name}: {str(e)}')
                
                validated_data['image_urls'] = image_paths
            else:
                # Lista vazia ou apenas valores None - remover todas as imagens
                validated_data['image_urls'] = []
        
        # Atualiza campos do produto
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Atualiza especificações se fornecidas
        if specifications_data is not None:
            # Remove especificações antigas
            instance.specifications.all().delete()
            # Cria novas especificações
            for spec_data in specifications_data:
                ProductSpecification.objects.create(product=instance, **spec_data)
        
        return instance


class ImageUploadSerializer(serializers.Serializer):
    """Serializer para upload de múltiplas imagens"""
    images = serializers.ListField(
        child=serializers.ImageField(),
        min_length=1,
        max_length=10,
        help_text='Lista de imagens para upload (máximo 10 por vez, até 5MB cada)'
    )
    
    def validate_images(self, value):
        """Valida lista de imagens"""
        if len(value) > 10:
            raise serializers.ValidationError('Máximo de 10 imagens por upload')
        return value
