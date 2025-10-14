# 📝 TPC 2 — Conversor simples de Markdown para HTML
### 📌 Enunciado

Desenvolver um pequeno conversor em Python que transforme um subconjunto da sintaxe Markdown (conforme a Basic Syntax da Cheat Sheet) para HTML. O conversor deve reconhecer e traduzir os seguintes elementos:

- **Cabeçalhos:** linhas iniciadas por ``#``, ``##`` ou ``###``.<br>
Ex: ``# Exemplo`` → ``<h1>Exemplo</h1>``

- **Negrito:** texto envolvido por ``**``.<br>
Ex: ``Este é um **exemplo** ...`` → ``Este é um <b>exemplo</b> ...``

- **Itálico:** texto envolvido por ``*``.<br>
Ex: ``Este é um *exemplo* ... ``→ ``Este é um <i>exemplo</i> ...``

- **Lista numerada:** linhas consecutivas começando por ``1.``, ``2.`` ... devem virar uma ``<ol>`` com ``<li>``.

- **Link:** ``[texto](url)``→ ``<a href="url">texto</a>``

- **Imagem:** ``![alt](url)`` → ``<img src="url" alt="alt"/>``

---

### ✏️ Resolução

- [TPC 2 — Conversor de MarkDown para HTML](tpc2.ipynb)

