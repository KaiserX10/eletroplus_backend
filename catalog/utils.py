"""
Utilitários para upload e processamento de imagens
"""
import os
import uuid
from pathlib import Path
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError

try:
    from PIL import Image
except ImportError:
    raise ImportError(
        "Pillow não está instalado. Instale com: pip install Pillow"
    )


# Configurações de upload
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGE_DIMENSION = 4096  # Máximo 4096x4096 pixels
MAX_IMAGES_PER_UPLOAD = 10  # Máximo de imagens por upload


def validate_image_file(file):
    """
    Valida se o arquivo é uma imagem válida
    
    Args:
        file: Arquivo enviado
    
    Returns:
        bool: True se válido
    
    Raises:
        ValidationError: Se o arquivo for inválido
    """
    # Verificar extensão
    file_ext = Path(file.name).suffix.lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f'Formato de arquivo não suportado. Formatos permitidos: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}'
        )
    
    # Verificar tamanho
    if file.size > MAX_IMAGE_SIZE:
        raise ValidationError(
            f'Tamanho do arquivo excede o limite máximo de {MAX_IMAGE_SIZE / (1024*1024):.1f}MB'
        )
    
    # Verificar se é uma imagem válida usando PIL
    try:
        # Ler o arquivo sem salvá-lo
        if hasattr(file, 'read'):
            file.seek(0)  # Voltar ao início do arquivo
            img = Image.open(file)
            img.verify()  # Verifica se é uma imagem válida
            
            # Voltar novamente ao início para processamento posterior
            file.seek(0)
            
            # Verificar dimensões
            img = Image.open(file)
            width, height = img.size
            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                raise ValidationError(
                    f'Dimensões da imagem ({width}x{height}) excedem o máximo permitido de {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION} pixels'
                )
            
            file.seek(0)
        else:
            raise ValidationError('Arquivo inválido')
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f'Arquivo não é uma imagem válida: {str(e)}')
    
    return True


def save_uploaded_image(file, prefix='product'):
    """
    Salva uma imagem enviada no diretório data/images
    
    Args:
        file: Arquivo de imagem enviado
        prefix: Prefixo para o nome do arquivo (default: 'product')
    
    Returns:
        str: Caminho relativo da imagem salva (ex: '/data/images/product_abc123_0.jpg')
    """
    # Validar arquivo
    validate_image_file(file)
    
    # Garantir que o diretório existe
    images_dir = settings.DATA_IMAGES_DIR
    if not images_dir.exists():
        images_dir.mkdir(parents=True, exist_ok=True)
    
    # Gerar nome único para o arquivo
    unique_id = uuid.uuid4().hex[:8]
    file_ext = Path(file.name).suffix.lower()
    
    # Se não tiver extensão, tentar detectar pelo tipo MIME
    if not file_ext:
        try:
            img = Image.open(file)
            if img.format:
                format_map = {
                    'JPEG': '.jpg',
                    'PNG': '.png',
                    'GIF': '.gif',
                    'WEBP': '.webp'
                }
                file_ext = format_map.get(img.format, '.jpg')
            file.seek(0)
        except:
            file_ext = '.jpg'  # Default
    
    filename = f'{prefix}_{unique_id}{file_ext}'
    filepath = images_dir / filename
    
    # Processar e salvar a imagem (redimensionar se necessário)
    try:
        # Garantir que o arquivo está no início
        if hasattr(file, 'seek'):
            file.seek(0)
        
        img = Image.open(file)
        
        # Converter para RGB se necessário (para JPEG)
        if file_ext in ['.jpg', '.jpeg'] and img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # Redimensionar se necessário (manter proporção)
        max_dimension = 2048  # Redimensionar imagens muito grandes
        width, height = img.size
        if width > max_dimension or height > max_dimension:
            if width > height:
                new_width = max_dimension
                new_height = int(height * (max_dimension / width))
            else:
                new_height = max_dimension
                new_width = int(width * (max_dimension / height))
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Salvar a imagem
        if file_ext in ['.jpg', '.jpeg']:
            img.save(filepath, 'JPEG', quality=85, optimize=True)
        elif file_ext == '.png':
            img.save(filepath, 'PNG', optimize=True)
        elif file_ext == '.gif':
            img.save(filepath, 'GIF')
        elif file_ext == '.webp':
            img.save(filepath, 'WEBP', quality=85)
        else:
            img.save(filepath)
        
        # Retornar caminho relativo para URL
        relative_path = f'/data/images/{filename}'
        return relative_path
        
    except Exception as e:
        # Se houver erro no processamento, tentar salvar o arquivo original
        try:
            if hasattr(file, 'seek'):
                file.seek(0)
            
            # Salvar arquivo diretamente
            with open(filepath, 'wb') as f:
                if hasattr(file, 'read'):
                    content = file.read()
                    f.write(content)
                else:
                    for chunk in file.chunks():
                        f.write(chunk)
            
            relative_path = f'/data/images/{filename}'
            return relative_path
        except Exception as save_error:
            raise ValidationError(f'Erro ao salvar imagem: {str(save_error)}')


def delete_image(image_path):
    """
    Deleta uma imagem do diretório data/images
    
    Args:
        image_path: Caminho relativo da imagem (ex: '/data/images/product_abc123.jpg')
    
    Returns:
        bool: True se deletado com sucesso, False caso contrário
    """
    try:
        # Extrair nome do arquivo do caminho
        filename = Path(image_path).name
        filepath = settings.DATA_IMAGES_DIR / filename
        
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    except Exception:
        return False

