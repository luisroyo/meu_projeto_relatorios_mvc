# 🎨 PROMPT PARA REPLICAR O ESTILO DA INTERFACE

## 🎯 **PROMPT COMPLETO PARA DESIGN SYSTEM**

```
Crie uma interface web moderna e profissional com o seguinte design system:

## 🎨 **PALETA DE CORES**
- **Primária**: Gradiente azul-roxo (#667eea → #764ba2)
- **Secundária**: Gradiente cinza escuro (#2c3e50 → #34495e)
- **Sucesso**: Gradiente verde (#28a745 → #20c997)
- **Info**: Gradiente azul (#007bff → #0056b3)
- **Background**: Gradiente principal (#667eea → #764ba2)
- **Cards**: Branco (#ffffff)
- **Textos**: Cinza escuro (#2c3e50, #495057)
- **Bordas**: Cinza claro (#e9ecef, #dee2e6)

## 🏗️ **ESTRUTURA LAYOUT**
- **Container principal**: max-width 1200px, margin auto, border-radius 20px
- **Header**: Gradiente secundário, padding 30px, text-align center
- **Main content**: padding 40px, background branco
- **Cards**: border-radius 15px, box-shadow 0 5px 15px rgba(0,0,0,0.1)
- **Grid responsivo**: display grid, gap 20px, auto-fit minmax(200px, 1fr)

## 🎭 **COMPONENTES**

### **Botões**
```css
.btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 15px 30px;
    border-radius: 25px;
    font-size: 1.1em;
    cursor: pointer;
    transition: all 0.3s ease;
}

.btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

.btn-success {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
}

.btn-info {
    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
}
```

### **Cards**
```css
.card {
    background: white;
    border-radius: 15px;
    padding: 30px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    border: 2px solid #e9ecef;
}

.stat-card {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    border-left: 4px solid #667eea;
}
```

### **Formulários**
```css
.form-group {
    display: flex;
    flex-direction: column;
    margin-bottom: 20px;
}

.form-group label {
    font-weight: bold;
    color: #495057;
    margin-bottom: 8px;
}

.form-group input, .form-group select {
    padding: 12px;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    font-size: 1em;
    transition: border-color 0.3s ease;
}

.form-group input:focus, .form-group select:focus {
    outline: none;
    border-color: #667eea;
}
```

### **Upload Area**
```css
.upload-section {
    background: #f8f9fa;
    border: 3px dashed #dee2e6;
    border-radius: 15px;
    padding: 40px;
    text-align: center;
    transition: all 0.3s ease;
}

.upload-section:hover {
    border-color: #667eea;
    background: #f0f2ff;
}

.upload-section.dragover {
    border-color: #667eea;
    background: #e8f0ff;
    transform: scale(1.02);
}
```

## 📱 **RESPONSIVIDADE**
```css
@media (max-width: 768px) {
    .filter-row {
        grid-template-columns: 1fr;
    }
    
    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .download-section {
        flex-direction: column;
    }
}
```

## 🎪 **ANIMAÇÕES E TRANSITIONS**
```css
/* Transições suaves */
* {
    transition: all 0.3s ease;
}

/* Hover effects */
.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.15);
}

/* Loading spinner */
.spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #667eea;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
```

## 📋 **ESTRUTURA HTML BASE**
```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sua Aplicação</title>
    <style>
        /* CSS aqui */
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Título da Aplicação</h1>
            <p>Descrição da aplicação</p>
        </div>
        
        <div class="main-content">
            <!-- Seu conteúdo aqui -->
        </div>
    </div>
</body>
</html>
```

## 🎨 **CARACTERÍSTICAS DO DESIGN**

### **Visual**
- ✅ Gradientes modernos e suaves
- ✅ Sombras sutis e elegantes
- ✅ Bordas arredondadas (15-25px)
- ✅ Espaçamento generoso (20-40px)
- ✅ Tipografia clara e legível

### **Interatividade**
- ✅ Hover effects com transform e shadow
- ✅ Transições suaves (0.3s ease)
- ✅ Estados visuais claros (hover, focus, active)
- ✅ Feedback visual imediato

### **UX/UI**
- ✅ Hierarquia visual clara
- ✅ Contraste adequado para acessibilidade
- ✅ Layout responsivo e adaptável
- ✅ Componentes consistentes

## 🚀 **APLICAÇÃO RÁPIDA**

Para aplicar este estilo em qualquer aplicação:

1. **Copie a paleta de cores** acima
2. **Use os componentes CSS** como base
3. **Adapte a estrutura HTML** para sua aplicação
4. **Mantenha a consistência** visual
5. **Teste a responsividade** em diferentes dispositivos

## 🎯 **RESULTADO ESPERADO**

Uma interface moderna, profissional e responsiva com:
- Visual atrativo e contemporâneo
- Experiência de usuário fluida
- Compatibilidade com todos os dispositivos
- Facilidade de manutenção e customização
```

## 🎨 **VERSÃO RESUMIDA PARA IA**

```
Crie uma interface web moderna com:

**ESTILO VISUAL:**
- Gradientes azul-roxo (#667eea → #764ba2) e cinza escuro (#2c3e50 → #34495e)
- Cards brancos com border-radius 15px e sombras sutis
- Botões com gradientes e hover effects (translateY(-2px))
- Layout responsivo com grid e flexbox

**COMPONENTES:**
- Header com gradiente e título centralizado
- Container principal com max-width 1200px e padding 40px
- Cards com background branco, border-radius 15px, box-shadow
- Botões com border-radius 25px, padding 15px 30px
- Formulários com inputs arredondados e focus states

**INTERATIVIDADE:**
- Transições suaves (0.3s ease) em todos os elementos
- Hover effects com transform e shadow
- Estados visuais claros para feedback

**RESPONSIVIDADE:**
- Grid adaptativo com auto-fit
- Media queries para mobile (max-width: 768px)
- Layout flexível que funciona em todos os dispositivos

Aplique este design system mantendo consistência visual e boa experiência do usuário.
```

## 🎯 **COMO USAR ESTE PROMPT**

1. **Copie o prompt completo** para aplicações complexas
2. **Use a versão resumida** para implementações rápidas
3. **Adapte as cores** conforme sua marca
4. **Mantenha a estrutura** de componentes
5. **Teste sempre** a responsividade

**Este design system garante interfaces modernas, profissionais e consistentes!** 🚀 