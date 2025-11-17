from rest_framework import serializers
from .models import User, ShippingAddress


class UserSerializer(serializers.ModelSerializer):
    """Serializer para Usuário"""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'phone',
            'street', 'city', 'state', 'zip_code', 'country',
            'birth_date', 'cpf', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']


class ShippingAddressSerializer(serializers.ModelSerializer):
    """Serializer para Endereço de Entrega"""
    
    class Meta:
        model = ShippingAddress
        fields = [
            'id', 'street', 'city', 'state', 'zip_code', 'country',
            'complement', 'number', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
