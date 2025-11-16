from rest_framework import serializers
from .models import User, ShippingAddress


class ShippingAddressSerializer(serializers.ModelSerializer):
    """Serializer para Endereço de Entrega"""
    
    class Meta:
        model = ShippingAddress
        fields = [
            'id', 'street', 'city', 'state', 'zip_code', 'country',
            'complement', 'number', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
