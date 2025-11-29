"""
Management command para baixar imagens externas e salvar localmente
Uso: python manage.py download_images [--update-db]
"""

import os
import requests
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from catalog.models import Product
from banner.models import Banner


class Command(BaseCommand):
    help = 'Baixa imagens externas e salva localmente em data/images/'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--update-db',
            action='store_true',
            help='Atualiza o banco de dados com os novos caminhos locais',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força o download mesmo se o arquivo já existir',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('📥 Iniciando download de imagens...'))
        
        # Criar diretório se não existir
        data_dir = Path(settings.BASE_DIR.parent) / 'data' / 'images'
        data_dir.mkdir(parents=True, exist_ok=True)
        
        update_db = options['update_db']
        force = options['force']
        
        # Processar produtos
        products_updated = self.process_products(data_dir, force, update_db)
        
        # Processar banners
        banners_updated = self.process_banners(data_dir, force, update_db)
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Download concluído!\n'
            f'   - {products_updated} produtos processados\n'
            f'   - {banners_updated} banners processados'
        ))
        
        if update_db:
            self.stdout.write(self.style.SUCCESS(
                '\n✅ Banco de dados atualizado com os novos caminhos!'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                '\n⚠️  Use --update-db para atualizar o banco de dados com os novos caminhos.'
            ))
    
    def process_products(self, data_dir, force, update_db):
        """Processa imagens de produtos"""
        products = Product.objects.exclude(image_urls=[])
        total = products.count()
        updated = 0
        downloaded = 0
        
        self.stdout.write(f'\n📦 Processando {total} produtos...')
        
        for i, product in enumerate(products, 1):
            if not product.image_urls:
                continue
            
            new_urls = []
            for idx, url in enumerate(product.image_urls):
                if not url or not isinstance(url, str):
                    continue
                
                # Verificar se já é um caminho local
                if url.startswith('/data/images/') or url.startswith('data/images/'):
                    new_urls.append(url)
                    continue
                
                # Gerar nome do arquivo baseado no ID do produto
                file_extension = self.get_file_extension(url)
                filename = f"product_{product.id}_{idx}{file_extension}"
                filepath = data_dir / filename
                
                # Baixar imagem se não existir ou se force=True
                if not filepath.exists() or force:
                    try:
                        self.download_image(url, filepath)
                        downloaded += 1
                        self.stdout.write(f'  ✓ [{i}/{total}] Baixado: {filename}')
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f'  ✗ [{i}/{total}] Erro ao baixar {url}: {str(e)}'
                        ))
                        # Manter URL original se falhar
                        new_urls.append(url)
                        continue
                
                # Atualizar URL para caminho local
                new_url = f'/data/images/{filename}'
                new_urls.append(new_url)
            
            # Atualizar produto se houver mudanças
            if new_urls != product.image_urls:
                if update_db:
                    product.image_urls = new_urls
                    product.save(update_fields=['image_urls'])
                    updated += 1
                else:
                    updated += 1
        
        if downloaded > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✅ {downloaded} imagens baixadas'))
        
        return updated
    
    def process_banners(self, data_dir, force, update_db):
        """Processa imagens de banners"""
        banners = Banner.objects.exclude(image_url='')
        total = banners.count()
        updated = 0
        downloaded = 0
        
        self.stdout.write(f'\n🎨 Processando {total} banners...')
        
        for i, banner in enumerate(banners, 1):
            if not banner.image_url:
                continue
            
            # Verificar se já é um caminho local
            if banner.image_url.startswith('/data/images/') or banner.image_url.startswith('data/images/'):
                continue
            
            # Gerar nome do arquivo baseado no ID do banner
            file_extension = self.get_file_extension(banner.image_url)
            filename = f"banner_{banner.id}{file_extension}"
            filepath = data_dir / filename
            
            # Baixar imagem se não existir ou se force=True
            if not filepath.exists() or force:
                try:
                    self.download_image(banner.image_url, filepath)
                    downloaded += 1
                    self.stdout.write(f'  ✓ [{i}/{total}] Baixado: {filename}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'  ✗ [{i}/{total}] Erro ao baixar {banner.image_url}: {str(e)}'
                    ))
                    continue
            
            # Atualizar URL para caminho local
            new_url = f'/data/images/{filename}'
            
            if update_db and banner.image_url != new_url:
                banner.image_url = new_url
                banner.save(update_fields=['image_url'])
                updated += 1
        
        if downloaded > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✅ {downloaded} imagens baixadas'))
        
        return updated
    
    def download_image(self, url, filepath):
        """Baixa uma imagem de uma URL"""
        try:
            response = requests.get(url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Verificar se é uma imagem válida
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                raise ValueError(f'Tipo de conteúdo inválido: {content_type}')
            
            # Salvar arquivo
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except requests.exceptions.RequestException as e:
            raise Exception(f'Erro na requisição: {str(e)}')
        except Exception as e:
            raise Exception(f'Erro ao salvar: {str(e)}')
    
    def get_file_extension(self, url):
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

