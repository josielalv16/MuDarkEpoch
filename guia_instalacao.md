# Guia de Instalação e Uso do Sistema MuDarkEpoch

Este guia contém instruções detalhadas para instalar e utilizar o Sistema de Distribuição de Itens MuDarkEpoch.

## Requisitos do Sistema

- Python 3.8 ou superior
- Pip (gerenciador de pacotes do Python)
- Navegador web moderno (Chrome, Firefox, Edge, etc.)

## Instalação

### 1. Preparação do Ambiente

1. Extraia todos os arquivos do pacote ZIP para uma pasta de sua preferência
2. Abra o terminal (Prompt de Comando no Windows ou Terminal no Mac/Linux)
3. Navegue até a pasta onde você extraiu os arquivos:
   ```
   cd caminho/para/pasta/MuDarkEpoch
   ```

### 2. Criação do Ambiente Virtual (Opcional, mas Recomendado)

```
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalação das Dependências

```
pip install flask flask-sqlalchemy flask-login
```

### 4. Executando o Sistema

```
python app.py
```

O sistema estará disponível em:
- Endereço: http://localhost:5000
- Área administrativa: http://localhost:5000/login
  - Usuário: admin
  - Senha: admin123

## Estrutura do Sistema

O sistema MuDarkEpoch é dividido em duas áreas principais:

### 1. Área Pública (Jogadores)
- Visualização dos rankings de distribuição de itens
- Acesso às informações sobre próximos a receber itens
- Não requer autenticação

### 2. Área Administrativa
- Gerenciamento completo de jogadores, itens e pontuações
- Registro de entregas e histórico
- Requer autenticação (login e senha)

## Funcionalidades Principais

### Gerenciamento de Jogadores
- Adicionar novos jogadores
- Editar informações de jogadores existentes
- Ativar/desativar jogadores

### Gerenciamento de Pontuações
- Atualizar reputação semanal
- Registrar participações em bosses
- Registrar participações em castelo
- Visualizar ranking de pontuação

### Gerenciamento de Entregas
- Confirmar entregas de itens
- Visualizar histórico de entregas
- Resetar ranking após limite de entregas

### Gerenciamento de Itens
- Editar informações dos itens
- Configurar limite de reset para cada item

## Fórmula de Pontuação

A pontuação de cada jogador é calculada usando a seguinte fórmula:
```
Pontuação = (Reputação × 2) + (Bosses × 3) + (Castelo × 2,5)
```

Adicionalmente:
- Jogadores que nunca receberam o item recebem um bônus de 50 pontos
- Após receber um item, o jogador tem suas pontuações zeradas para aquele item específico

## Fluxo de Uso Típico

1. Administrador faz login no sistema
2. Cadastra jogadores da guilda
3. Atualiza pontuações semanalmente (reputação, bosses, castelo)
4. Sistema calcula automaticamente a pontuação total
5. Administrador confirma a entrega do item ao jogador com maior pontuação
6. Sistema registra a entrega no histórico
7. Após atingir o limite de entregas, o administrador pode resetar o ranking

## Solução de Problemas

### O sistema não inicia
- Verifique se todas as dependências foram instaladas
- Certifique-se de que a porta 5000 não está sendo usada por outro aplicativo

### Erro ao acessar o banco de dados
- O sistema usa SQLite por padrão, que não requer configuração adicional
- O arquivo de banco de dados será criado automaticamente na primeira execução

### Problemas de login
- Usuário padrão: admin
- Senha padrão: admin123
- Se esquecer a senha, você precisará excluir o arquivo de banco de dados e reiniciar o sistema

## Suporte

Para suporte adicional ou dúvidas, entre em contato com o desenvolvedor.
