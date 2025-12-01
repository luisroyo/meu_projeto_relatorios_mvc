# 🔧 Como Reduzir o Tamanho do Repositório Git

## Problema

O repositório está muito grande (254MB) porque provavelmente contém arquivos grandes no histórico do Git que não deveriam estar lá, como:
- Ambiente virtual (`venv/`)
- Arquivos de cache (`__pycache__/`)
- Bancos de dados locais (`.db`, `.sqlite`)
- Arquivos de log grandes

## Solução

### 1. Verificar o que está ocupando espaço

```bash
# Ver tamanho do repositório
git count-objects -vH

# Ver arquivos grandes no histórico
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '/^blob/ {print substr($0,6)}' | sort -k2 -n -r | head -20
```

### 2. Remover arquivos grandes do histórico (BFG Repo-Cleaner - Recomendado)

**Opção A: Usar BFG Repo-Cleaner (Mais rápido e seguro)**

1. Baixe o BFG: https://rtyley.github.io/bfg-repo-cleaner/

2. Clone uma cópia fresca do repositório:
```bash
git clone --mirror https://github.com/luisroyo/meu_projeto_relatorios_mvc.git
```

3. Execute o BFG para remover arquivos grandes:
```bash
# Remover venv/ do histórico
java -jar bfg.jar --delete-folders venv meu_projeto_relatorios_mvc.git

# Remover arquivos .db
java -jar bfg.jar --delete-files *.db meu_projeto_relatorios_mvc.git

# Remover arquivos .log
java -jar bfg.jar --delete-files *.log meu_projeto_relatorios_mvc.git

# Limpar e otimizar
cd meu_projeto_relatorios_mvc.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

4. Force push (⚠️ CUIDADO: Isso reescreve o histórico):
```bash
git push --force
```

**Opção B: Usar git filter-branch (Mais lento, mas nativo)**

```bash
# Remover venv/ do histórico
git filter-branch --force --index-filter "git rm -rf --cached --ignore-unmatch venv" --prune-empty --tag-name-filter cat -- --all

# Remover arquivos .db
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch *.db" --prune-empty --tag-name-filter cat -- --all

# Limpar
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### 3. Atualizar .gitignore (Já está correto, mas verifique)

Certifique-se de que o `.gitignore` contém:

```gitignore
# Python virtual environment
venv/
.venv/

# Bancos de dados locais
*.db
*.sqlite
*.sqlite3

# Logs
*.log
*.log.*

# Cache Python
__pycache__/
*.py[cod]
*$py.class

# Arquivos temporários
*.tmp
*.bak
```

### 4. Verificar se há arquivos grandes sendo rastreados

```bash
# Verificar se venv está sendo rastreado
git ls-files | grep venv

# Verificar arquivos .db
git ls-files | grep "\.db$"

# Verificar arquivos .log
git ls-files | grep "\.log$"
```

### 5. Limpar arquivos locais grandes

Se houver arquivos grandes localmente que não estão no Git:

```bash
# Remover venv local (você pode recriar depois)
rm -rf venv/

# Remover arquivos de cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Remover logs
find . -type f -name "*.log" -delete
```

## ⚠️ AVISOS IMPORTANTES

1. **Backup**: Sempre faça backup antes de reescrever o histórico do Git
2. **Comunicação**: Se trabalha em equipe, avise todos antes de fazer force push
3. **Histórico**: Reescrever o histórico remove commits antigos - certifique-se de que isso é aceitável
4. **Render/Deploy**: Após o force push, você pode precisar reconfigurar o deploy

## Verificação Final

Após limpar, verifique o tamanho:

```bash
git count-objects -vH
```

O tamanho deve estar muito menor (idealmente < 10MB para um projeto Python).

## Alternativa: Git LFS (Large File Storage)

Se você realmente precisa versionar arquivos grandes:

```bash
# Instalar Git LFS
git lfs install

# Rastrear arquivos grandes
git lfs track "*.db"
git lfs track "*.log"

# Adicionar .gitattributes
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

Mas para este projeto, é melhor simplesmente não versionar esses arquivos.

