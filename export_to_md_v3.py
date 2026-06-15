#!/usr/bin/env python3
from pathlib import Path
import argparse
import mimetypes
import hashlib
import pathspec

DEFAULT_MAX_FILE_SIZE_MB = 2
DEFAULT_MAX_COMBINED_SIZE_MB = 10

TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".kt", ".kts", ".go", ".rs", ".c", ".h", ".cpp", ".hpp",
    ".cs", ".php", ".rb", ".swift", ".scala", ".sh", ".bash", ".zsh",
    ".fish", ".ps1", ".bat", ".cmd", ".html", ".css", ".scss", ".sass",
    ".json", ".yaml", ".yml", ".toml", ".xml", ".ini", ".env", ".example",
    ".gitignore", ".dockerignore", ".sql", ".graphql", ".gql", ".prisma",
    ".gradle", ".properties", ".csv", ".tsv", ".lock"
}

LIKELY_BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip",
    ".tar", ".gz", ".rar", ".7z", ".exe", ".dll", ".so", ".dylib",
    ".mp4", ".mov", ".avi", ".mp3", ".wav", ".flac", ".woff", ".woff2",
    ".ttf", ".otf", ".class", ".jar", ".bin"
}

def load_gitignore(root: Path):
    gitignore = root / ".gitignore"

    if not gitignore.exists():
        return pathspec.PathSpec.from_lines("gitwildmatch", [])

    return pathspec.PathSpec.from_lines(
        "gitwildmatch",
        gitignore.read_text(encoding="utf-8", errors="ignore").splitlines()
    )

def is_ignored(path: Path, root: Path, spec) -> bool:
    if ".git" in path.parts:
        return True

    rel = path.relative_to(root).as_posix()

    return spec.match_file(rel)

def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)

    return hasher.hexdigest()

def is_probably_text(path: Path) -> bool:
    suffix = path.suffix.lower()

    if suffix in LIKELY_BINARY_EXTENSIONS:
        return False

    if suffix in TEXT_EXTENSIONS:
        return True

    try:
        sample = path.read_bytes()[:4096]
    except Exception:
        return False

    if b"\x00" in sample:
        return False

    try:
        sample.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False

def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[ERRO AO LER ARQUIVO: {e}]"

def collect_visible_paths(root: Path, spec):
    paths = []

    for path in root.rglob("*"):
        if is_ignored(path, root, spec):
            continue

        paths.append(path)

    return paths

def is_inside_output_dir(path: Path, output_dir: Path | None) -> bool:
    if output_dir is None:
        return False

    resolved_path = path.resolve()
    resolved_output_dir = output_dir.resolve()

    return resolved_path == resolved_output_dir or resolved_output_dir in resolved_path.parents

def get_visible_children(current: Path, root: Path, spec, output_dir: Path | None) -> list[Path]:
    items = sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))

    return [
        item
        for item in items
        if not is_inside_output_dir(item, output_dir) and not is_ignored(item, root, spec)
    ]

def append_tree_lines(
    current: Path,
    root: Path,
    spec,
    output_dir: Path | None,
    lines: list[str],
    prefix: str = "",
) -> None:
    visible = get_visible_children(current, root, spec, output_dir)

    for index, item in enumerate(visible):
        last = index == len(visible) - 1
        connector = "└── " if last else "├── "
        lines.append(prefix + connector + item.name)

        if item.is_dir():
            next_prefix = prefix + ("    " if last else "│   ")
            append_tree_lines(item, root, spec, output_dir, lines, next_prefix)

def generate_tree(root: Path, spec, output_dir: Path | None = None) -> str:
    lines = [f"{root.name}/"]
    append_tree_lines(root, root, spec, output_dir, lines)
    return "\n".join(lines)

def get_language_hint(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")

    aliases = {
        "py": "python",
        "js": "javascript",
        "jsx": "jsx",
        "ts": "typescript",
        "tsx": "tsx",
        "java": "java",
        "kt": "kotlin",
        "go": "go",
        "rs": "rust",
        "sh": "bash",
        "bash": "bash",
        "zsh": "zsh",
        "html": "html",
        "css": "css",
        "scss": "scss",
        "json": "json",
        "yaml": "yaml",
        "yml": "yaml",
        "toml": "toml",
        "xml": "xml",
        "sql": "sql",
        "md": "markdown",
    }

    return aliases.get(suffix, "text")

def write_file_markdown(source_file: Path, root: Path, output_dir: Path, max_file_size_bytes: int):
    relative_path = source_file.relative_to(root)
    output_file = output_dir / relative_path.parent / f"{relative_path.name}.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    size = source_file.stat().st_size
    mime_type, _ = mimetypes.guess_type(source_file.name)
    digest = sha256_file(source_file)

    metadata = f"""# Caminho

`{relative_path.as_posix()}`

# Metadados

- Tamanho: `{size}` bytes
- MIME estimado: `{mime_type or "desconhecido"}`
- SHA-256: `{digest}`
"""

    if size > max_file_size_bytes:
        body = f"""
# Conteúdo

Arquivo omitido porque ultrapassa o limite configurado de `{max_file_size_bytes}` bytes.
"""
    elif not is_probably_text(source_file):
        body = """
# Conteúdo

Arquivo provavelmente binário. Conteúdo bruto omitido.
"""
    else:
        content = read_text_file(source_file)
        language = get_language_hint(source_file)

        body = f"""
# Conteúdo

```{language}
{content}
```
"""

    output_file.write_text(metadata + body, encoding="utf-8")

def build_summary(files: list[Path]) -> str:
    total_files = len([f for f in files if f.is_file()])
    total_dirs = len([f for f in files if f.is_dir()])
    total_bytes = sum(f.stat().st_size for f in files if f.is_file())

    by_extension = {}

    for file in files:
        if not file.is_file():
            continue

        ext = file.suffix.lower() or "[sem extensão]"
        by_extension.setdefault(ext, {"count": 0, "bytes": 0})
        by_extension[ext]["count"] += 1
        by_extension[ext]["bytes"] += file.stat().st_size

    rows = "\n".join(
        f"| `{ext}` | {data['count']} | {data['bytes']} |"
        for ext, data in sorted(by_extension.items(), key=lambda item: (-item[1]["count"], item[0]))
    )

    return f"""# Resumo do Projeto

## Totais

- Diretórios: `{total_dirs}`
- Arquivos: `{total_files}`
- Tamanho total analisado: `{total_bytes}` bytes

## Arquivos por extensão

| Extensão | Quantidade | Bytes |
|---|---:|---:|
{rows}
"""

def build_project_context(root: Path, files: list[Path], spec, max_combined_size_bytes: int) -> str:
    parts = [
        "# Contexto Consolidado do Projeto",
        "",
        "## Estrutura",
        "",
        "```text",
        generate_tree(root, spec),
        "```",
        ""
    ]

    used_bytes = 0

    for file in sorted([f for f in files if f.is_file()], key=lambda p: p.relative_to(root).as_posix()):
        if not is_probably_text(file):
            continue

        content = read_text_file(file)
        encoded_size = len(content.encode("utf-8", errors="replace"))

        if used_bytes + encoded_size > max_combined_size_bytes:
            parts.extend([
                "",
                "## Limite atingido",
                "",
                f"O arquivo `{file.relative_to(root).as_posix()}` e os próximos foram omitidos porque o limite consolidado foi atingido.",
                ""
            ])
            break

        used_bytes += encoded_size
        relative_path = file.relative_to(root).as_posix()
        language = get_language_hint(file)

        parts.extend([
            f"## `{relative_path}`",
            "",
            f"```{language}",
            content,
            "```",
            ""
        ])

    return "\n".join(parts)

def export_directory_to_markdown(
    root: Path,
    output_dir: Path,
    max_file_size_mb: int,
    max_combined_size_mb: int,
    consolidated: bool,
):
    root = root.resolve()
    output_dir = output_dir.resolve()

    if not root.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"O caminho informado não é uma pasta: {root}")

    output_dir.mkdir(parents=True, exist_ok=True)

    spec = load_gitignore(root)

    visible_paths = []
    for path in collect_visible_paths(root, spec):
        if path == output_dir or output_dir in path.parents:
            continue

        visible_paths.append(path)

    tree_md = f"""# Estrutura do Projeto

```text
{generate_tree(root, spec, output_dir)}
```
"""

    (output_dir / "TREE.md").write_text(tree_md, encoding="utf-8")
    (output_dir / "SUMMARY.md").write_text(build_summary(visible_paths), encoding="utf-8")

    max_file_size_bytes = max_file_size_mb * 1024 * 1024
    max_combined_size_bytes = max_combined_size_mb * 1024 * 1024

    for path in visible_paths:
        if path.is_file():
            write_file_markdown(path, root, output_dir, max_file_size_bytes)

    if consolidated:
        (output_dir / "PROJECT_CONTEXT.md").write_text(
            build_project_context(root, [p for p in visible_paths if p.is_file()], spec, max_combined_size_bytes),
            encoding="utf-8"
        )

def main():
    parser = argparse.ArgumentParser(
        description="Exporta uma pasta para Markdown preservando estrutura, árvore, resumo e contexto consolidado."
    )

    parser.add_argument("folder", help="Pasta que será analisada")

    parser.add_argument(
        "-o",
        "--output",
        default="markdown_export",
        help="Pasta onde os arquivos .md serão criados"
    )

    parser.add_argument(
        "--max-file-size-mb",
        type=int,
        default=DEFAULT_MAX_FILE_SIZE_MB,
        help="Tamanho máximo de arquivo individual para incluir conteúdo bruto"
    )

    parser.add_argument(
        "--max-combined-size-mb",
        type=int,
        default=DEFAULT_MAX_COMBINED_SIZE_MB,
        help="Tamanho máximo do PROJECT_CONTEXT.md consolidado"
    )

    parser.add_argument(
        "--no-consolidated",
        action="store_true",
        help="Não gera PROJECT_CONTEXT.md"
    )

    args = parser.parse_args()

    export_directory_to_markdown(
        root=Path(args.folder),
        output_dir=Path(args.output),
        max_file_size_mb=args.max_file_size_mb,
        max_combined_size_mb=args.max_combined_size_mb,
        consolidated=not args.no_consolidated,
    )

    print(f"Exportação concluída em: {Path(args.output).resolve()}")

if __name__ == "__main__":
    main()
