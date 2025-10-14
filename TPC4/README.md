## 📝 TPC 4 — Máquina de Vending (com PLY)

### 📌 Enunciado

Desenvolver um programa em **Python** que simule o funcionamento de uma **máquina de vending**, utilizando a biblioteca **`ply.lex`** para criar um **analisador léxico** dos comandos inseridos pelo utilizador.

O programa deve permitir listar produtos, inserir moedas, selecionar produtos e sair (devolvendo o troco).  
O stock é carregado de um ficheiro **`stock.json`**, que é atualizado ao terminar o programa.

---

### ⚙️ Estrutura de Dados

O stock inicial encontra-se num ficheiro `stock.json`, no seguinte formato:

```json
[
    {"cod": "A01", "nome": "Água 0.5L", "quant": 10, "preco": 0.7},
    {"cod": "A02", "nome": "Coca-Cola 0.33L", "quant": 6, "preco": 1.2},
    {"cod": "B01", "nome": "Bolacha Maria", "quant": 8, "preco": 0.5}
]
```

Quando o programa é iniciado, o stock é carregado para memória; ao sair, é novamente gravado no ficheiro, mantendo o estado atualizado.

---

### 🧩 Tokens do Analisador Léxico

O **lexer** criado com `ply.lex` reconhece os seguintes **tokens**:

| Token | Expressão Regular | Exemplo |
|--------|------------------|----------|
| `LISTAR` | `r'LISTAR'` | `LISTAR` |
| `MOEDA` | `r'MOEDA'` | `MOEDA 1e 20c` |
| `SELECIONAR` | `r'SELECIONAR'` | `SELECIONAR A01` |
| `SAIR` | `r'SAIR'` | `SAIR` |
| `ADICIONAR` | `r'ADICIONAR'` | `ADICIONAR A05 Água 5 0.7` |
| `CODIGO` | `r'[A-D]\d{2}'` | `A01`, `B10`, `C07` |
| `VALOR` | `r'((2e)|(1e)|(50c)|(20c)|(10c)|(5c)|(2c)|(1c))+'` | `1e`, `20c`, `2e` |

O lexer ignora espaços, tabulações e quebras de linha (`t_ignore = " \t\n"`).

---

### 💬 Comandos Suportados

| Comando | Descrição | Exemplo |
|----------|------------|----------|
| **LISTAR** | Mostra o stock disponível. | `LISTAR` |
| **MOEDA** | Insere uma ou mais moedas. | `MOEDA 1e 50c 20c` |
| **SELECIONAR** | Seleciona o produto indicado. | `SELECIONAR A03` |
| **ADICIONAR** | Adiciona ou atualiza um produto no stock. | `ADICIONAR B11 Bolacha 5 0.8` |
| **SAIR** | Termina o programa e devolve o troco. | `SAIR` |

---

### 🧠 Funcionamento Geral

1. **Carregamento do stock:**  
   Ao iniciar, o programa lê o ficheiro `stock.json`.  
   Se o ficheiro não existir, é criado um novo.

2. **Interação com o utilizador:**  
   A máquina responde a comandos inseridos no terminal.

3. **Gestão do saldo:**  
   O saldo é atualizado a cada inserção de moedas e subtraído no momento da compra.

4. **Cálculo do troco:**  
   Quando o utilizador sai, o programa calcula o troco com moedas de 2€, 1€, 50c, 20c, 10c, 5c, 2c e 1c.

5. **Atualização do stock:**  
   Ao final, o stock é gravado novamente no ficheiro `stock.json`.

---

### 🧾 Exemplo de Execução

```
maq: 2025-10-14, Stock carregado, Estado atualizado.
maq: Bom dia. Estou disponível para atender o seu pedido.

>> LISTAR
maq:
cod    | nome                 | quant     | preço
--------------------------------------------------
A01    | Água 0.5L            | 10        | 0.7€
A02    | Coca-Cola 0.33L      | 6         | 1.2€
B01    | Bolacha Maria        | 8         | 0.5€

>> MOEDA 1e 1e 1e
maq: Saldo = 3e0c

>> SELECIONAR A02
maq: Pode retirar o produto "Coca-Cola 0.33L".
maq: Saldo = 1e80c

>> SAIR
maq: Pode retirar o troco: 1x 1e, 1x 50c, 1x 20c, 1x 10c.
maq: Até à próxima!
```

---

### ✏️ Resolução
- [TPC 4 — Máquina de Vending](maq_vending.py)



