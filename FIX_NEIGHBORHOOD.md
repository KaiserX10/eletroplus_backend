# 🔧 Correção: Coluna neighborhood não existe

## Problema
A coluna `neighborhood` não existe na tabela `users_shippingaddress`, causando erro ao tentar cadastrar endereços.

## Solução

Você tem duas opções para resolver este problema:

### Opção 1: Aplicar a migração do Django (Recomendado)

1. **Ative o ambiente virtual** (se estiver usando):
   ```bash
   # Windows
   .venv\Scripts\activate
   # ou
   venv\Scripts\activate

   # Linux/Mac
   source .venv/bin/activate
   ```

2. **Aplique as migrações pendentes**:
   ```bash
   cd eletroplus_backend
   python manage.py migrate users
   ```

   Ou aplique todas as migrações pendentes:
   ```bash
   python manage.py migrate
   ```

3. **Verifique se a migração foi aplicada**:
   ```bash
   python manage.py showmigrations users
   ```

   Você deve ver `[X]` ao lado de `0003_add_neighborhood_to_shipping_address`.

### Opção 2: Executar SQL diretamente (Alternativa)

Se não conseguir aplicar a migração pelo Django, execute o SQL diretamente no banco de dados:

**Para PostgreSQL:**
```sql
ALTER TABLE users_shippingaddress 
ADD COLUMN neighborhood VARCHAR(100) DEFAULT '' NOT NULL;

ALTER TABLE users_shippingaddress 
ALTER COLUMN neighborhood DROP NOT NULL;
```

Ou de forma mais simples:
```sql
ALTER TABLE users_shippingaddress 
ADD COLUMN IF NOT EXISTS neighborhood VARCHAR(100);
```

**Para SQLite:**
```sql
ALTER TABLE users_shippingaddress 
ADD COLUMN neighborhood VARCHAR(100) DEFAULT '';
```

## Verificação

Após aplicar a migração ou executar o SQL, verifique se a coluna foi criada:

**PostgreSQL:**
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users_shippingaddress' 
AND column_name = 'neighborhood';
```

**SQLite:**
```sql
PRAGMA table_info(users_shippingaddress);
```

## Nota

A migração `0003_add_neighborhood_to_shipping_address.py` já existe no projeto e adiciona o campo `neighborhood` como `CharField(max_length=100, blank=True)`. Ela apenas precisa ser aplicada ao banco de dados.

