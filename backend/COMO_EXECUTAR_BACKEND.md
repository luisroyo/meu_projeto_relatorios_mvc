# 🚀 Como Executar o Backend

## 📋 Pré-requisitos

- **Python 3.8+** instalado
- **Git** (para clonar o repositório)
- **Powershell** ou **CMD** (Windows)

## 🛠️ Instalação e Configuração

### 1. **Navegar para o diretório backend**
```powershell
cd D:\Projetos_Diversos\app-gestao-seguranca\backend
```

### 2. **Criar ambiente virtual** (se não existir)
```powershell
python -m venv venv
```

### 3. **Ativar ambiente virtual**
```powershell
.\venv\Scripts\Activate.ps1
```

### 4. **Instalar dependências**
```powershell
python -m pip install -r requirements.txt
```

## 🚀 Executar o Backend

### **Opção 1: Script Automático (Recomendado)**

#### **PowerShell:**
```powershell
.\start_backend.ps1
```

#### **CMD/Batch:**
```cmd
start_backend.bat
```

### **Opção 2: Comando Manual**

```powershell
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Executar o Flask
python run.py
```

## ✅ Verificar se está funcionando

### **1. Verificar porta:**
```powershell
netstat -an | findstr :5000
```
Deve mostrar: `TCP 0.0.0.0:5000 0.0.0.0:0 LISTENING`

### **2. Testar no navegador:**
- Acesse: `http://localhost:5000`
- Deve aparecer a página inicial do Flask

### **3. Testar API:**
- Acesse: `http://localhost:5000/api/`
- Deve retornar informações da API

## 🔧 Configurações

### **Variáveis de Ambiente:**
- `FLASK_ENV=development` (padrão)
- `FLASK_DEBUG=True` (padrão)
- `PORT=5000` (padrão)

### **Arquivo de Configuração:**
- `config.py` - Configurações do banco de dados e aplicação

## 🐛 Solução de Problemas

### **Erro: "Porta 5000 já em uso"**
```powershell
# Encontrar processo usando a porta
netstat -ano | findstr :5000

# Matar o processo (substitua XXXX pelo PID)
taskkill /PID XXXX /F
```

### **Erro: "Ambiente virtual não encontrado"**
```powershell
# Recriar ambiente virtual
rmdir /s venv
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### **Erro: "Dependências não encontradas"**
```powershell
# Atualizar pip
python -m pip install --upgrade pip

# Reinstalar dependências
python -m pip install -r requirements.txt --force-reinstall
```

## 📱 Integração com Frontend

### **Frontend já configurado para:**
- **URL da API:** `http://localhost:5000/api`
- **CORS:** Habilitado para `http://localhost:5173`
- **Autenticação:** JWT Token

### **Para testar a integração:**
1. **Backend rodando:** `http://localhost:5000`
2. **Frontend rodando:** `http://localhost:5173`
3. **Acesse:** `http://localhost:5173/test-api`

## 🎯 Comandos Úteis

### **Parar o servidor:**
- `Ctrl + C` no terminal

### **Reiniciar o servidor:**
```powershell
# Parar (Ctrl+C) e executar novamente
python run.py
```

### **Ver logs:**
- Os logs aparecem no terminal onde o Flask está rodando

### **Modo debug:**
- Já está ativado por padrão
- Mudanças no código reiniciam automaticamente

## 📞 Suporte

Se encontrar problemas:
1. Verifique se Python 3.8+ está instalado
2. Verifique se está no diretório correto
3. Verifique se o ambiente virtual está ativado
4. Verifique se as dependências estão instaladas
5. Verifique se a porta 5000 está livre

---

**🎉 Backend pronto para uso!** 