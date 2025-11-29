"""
Classe de paginação customizada para a API
Permite configurar page_size via query parameter
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPageNumberPagination(PageNumberPagination):
    """
    Paginação customizada que permite configurar page_size via query parameter
    """
    page_size = 20  # Tamanho padrão da página
    page_size_query_param = 'page_size'  # Permite sobrescrever via ?page_size=10
    max_page_size = 100  # Limite máximo de itens por página
    
    def get_paginated_response(self, data):
        """
        Retorna resposta paginada com informações adicionais
        """
        # Obter o page_size real usado (pode ser customizado via query param)
        page_size = self.get_page_size(self.request) if hasattr(self, 'request') else self.page_size
        
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'page_size': page_size,
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'results': data
        })

