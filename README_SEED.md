# 🌱 Seed de Dados - EletroPlus Backend

Este documento explica como usar o comando de seed para popular o banco de dados com dados de exemplo para testes.

## 📋 Pré-requisitos

- Django instalado e configurado
- Banco de dados configurado e migrações aplicadas
- Ambiente virtual ativado (se estiver usando)

## 🚀 Como Usar

### Comando Básico

```bash
cd eletroplus_backend
python manage.py seed_data
```

Este comando cria:
- **12 categorias** de produtos
- **200 produtos** com especificações técnicas
- **50 usuários** com endereços de entrega
- **6 cupons** de desconto
- **30 carrinhos** (60% dos usuários)
- **100 pedidos** com itens
- **Pagamentos** para pedidos pagos
- **Avaliações** de produtos (0-10 por produto)
- **3 banners** promocionais
- **10 mensagens** de contato

### Opções Disponíveis

#### Limpar dados existentes antes de popular

```bash
python manage.py seed_data --clear
```

⚠️ **Atenção**: Isso remove TODOS os dados (exceto superusuários) antes de popular!

#### Personalizar quantidade de dados

```bash
# Criar 100 usuários
python manage.py seed_data --users 100

# Criar 500 produtos
python manage.py seed_data --products 500

# Criar 200 pedidos
python manage.py seed_data --orders 200

# Combinar opções
python manage.py seed_data --users 100 --products 500 --orders 200 --clear
```

## 📊 Dados Criados

### Categorias
- Geladeiras, Fogões, Micro-ondas, Lavadoras
- Ar Condicionado, Cooktops, Lava-louças
- Aspiradores, Purificadores, Secadoras
- Fornos, Freezers

### Produtos
- Marcas: Electrolux, Brastemp, Consul, LG, Samsung, Panasonic, Midea, Philco
- Preços variados por categoria
- 30% dos produtos têm desconto (10-40%)
- 15% dos produtos são destaque
- Estoque aleatório (0-100 unidades)
- Avaliações de 3.5 a 5.0 estrelas
- Especificações técnicas específicas por categoria

### Usuários
- Nomes brasileiros realistas
- Emails únicos: `nome.sobrenome.numero@example.com`
- Senha padrão: `senha123` (para testes)
- Endereços completos (cidades brasileiras)
- 1-3 endereços de entrega por usuário

### Pedidos
- Status distribuídos: 10% Pendente, 20% Pago, 20% Processando, 20% Enviado, 25% Entregue, 5% Cancelado
- Datas variadas (últimos 90 dias)
- 1-4 produtos por pedido
- 20% dos pedidos usam cupom
- 30% têm frete grátis

### Pagamentos
- Métodos: PIX (30%), Cartão de Crédito (40%), Débito (20%), Boleto (10%)
- Apenas pedidos pagos/processando/enviados/entregues têm pagamento
- Transaction IDs únicos

### Cupons
- `BEMVINDO10` - 10% OFF
- `FRETEGRATIS` - R$ 29,90 OFF
- `BLACKFRIDAY` - 30% OFF
- `PRIMAVERA15` - 15% OFF
- `DESCONTO20` - 20% OFF
- `CASHBACK50` - R$ 50,00 OFF

## 🔧 Exemplos de Uso

### Seed rápido para desenvolvimento
```bash
python manage.py seed_data --users 20 --products 50 --orders 20
```

### Seed massivo para testes de performance
```bash
python manage.py seed_data --users 500 --products 2000 --orders 1000 --clear
```

### Seed mínimo para testes básicos
```bash
python manage.py seed_data --users 10 --products 20 --orders 5
```

## ⚠️ Notas Importantes

1. **Superusuários**: Não são removidos com `--clear`
2. **Senhas**: Todos os usuários criados têm senha `senha123`
3. **Imagens**: Usam placeholders (via.placeholder.com)
4. **Performance**: Seed massivo pode demorar alguns minutos
5. **Transações**: Todo o seed é executado em uma transação única

## 🐛 Troubleshooting

### Erro: "No such file or directory"
Certifique-se de estar no diretório `eletroplus_backend`:
```bash
cd eletroplus_backend
python manage.py seed_data
```

### Erro: "Table doesn't exist"
Execute as migrações primeiro:
```bash
python manage.py migrate
```

### Erro: "IntegrityError"
Use `--clear` para limpar dados existentes:
```bash
python manage.py seed_data --clear
```

## 📈 Estatísticas Esperadas

Com valores padrão (`--users 50 --products 200 --orders 100`):
- ~12 categorias
- ~200 produtos
- ~50 usuários
- ~75 endereços de entrega
- ~6 cupons
- ~30 carrinhos
- ~100 pedidos
- ~80 pagamentos
- ~500-1000 avaliações
- ~3 banners
- ~10 mensagens de contato

## 🔄 Resetar Dados

Para resetar completamente e popular novamente:
```bash
python manage.py seed_data --clear --users 50 --products 200 --orders 100
```

