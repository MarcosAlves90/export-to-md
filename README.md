# Export to Markdown

Script para transformar uma pasta inteira em arquivos Markdown próprios para análise por LLMs.

## O que ele faz

- Ignora `.git`
- Respeita `.gitignore`
- Preserva a estrutura original de diretórios
- Cria um `.md` para cada arquivo
- Coloca o caminho relativo original no topo de cada `.md`
- Gera `TREE.md` com a árvore do projeto
- Gera `SUMMARY.md` com estatísticas do projeto
- Gera `PROJECT_CONTEXT.md` consolidado para colar em Claude/GPT/Gemini
- Omite conteúdo bruto de arquivos binários
- Omite arquivos muito grandes, mas mantém metadados

## Instalação

```bash
pip install pathspec
```

## Uso básico

```bash
python export_to_md_v3.py /caminho/da/pasta
```

## Escolher pasta de saída

```bash
python export_to_md_v3.py /caminho/da/pasta -o markdown_export
```

## Aumentar limite de tamanho por arquivo

```bash
python export_to_md_v3.py /caminho/da/pasta --max-file-size-mb 5
```

## Aumentar limite do contexto consolidado

```bash
python export_to_md_v3.py /caminho/da/pasta --max-combined-size-mb 20
```

## Não gerar PROJECT_CONTEXT.md

```bash
python export_to_md_v3.py /caminho/da/pasta --no-consolidated
```

## Saída esperada

```text
markdown_export/
├── TREE.md
├── SUMMARY.md
├── PROJECT_CONTEXT.md
├── README.md.md
└── src/
    ├── main.py.md
    └── services/
        └── user.py.md
```
