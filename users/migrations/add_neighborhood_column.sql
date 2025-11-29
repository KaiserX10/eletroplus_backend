-- Script SQL para adicionar a coluna neighborhood à tabela users_shippingaddress
-- Execute este script se não conseguir aplicar a migração do Django

-- PostgreSQL
ALTER TABLE users_shippingaddress 
ADD COLUMN neighborhood VARCHAR(100) DEFAULT '' NOT NULL;

-- Remover o NOT NULL se necessário (para permitir valores nulos)
ALTER TABLE users_shippingaddress 
ALTER COLUMN neighborhood DROP NOT NULL;

-- Ou execute diretamente:
-- ALTER TABLE users_shippingaddress ADD COLUMN neighborhood VARCHAR(100) DEFAULT '';

