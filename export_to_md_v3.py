#!/usr/bin/env python3
"""Export a source directory to Markdown files optimized for LLM review."""

from __future__ import annotations

import argparse
import hashlib
import mimetypes
import sys
from dataclasses import dataclass
from pathlib import Path

import pathspec

DEFAULT_MAX_FILE_SIZE_MB = 2
DEFAULT_MAX_COMBINED_SIZE_MB = 10
BYTES_PER_MB = 1024 * 1024
HASH_CHUNK_SIZE = 1024 * 1024
TEXT_SAMPLE_SIZE = 4096

TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".kt", ".kts", ".go", ".rs", ".c", ".h", ".cpp", ".hpp",
    ".cs", ".php", ".rb", ".swift", ".scala", ".sh", ".bash", ".zsh",
    ".fish", ".ps1", ".bat", ".cmd", ".html", ".css", ".scss", ".sass",
    ".json", ".yaml", ".yml", ".toml", ".xml", ".ini", ".env", ".example",
    ".gitignore", ".dockerignore", ".sql", ".graphql", ".gql", ".prisma",
    ".gradle", ".properties", ".csv", ".tsv", ".lock",
}

LIKELY_BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip",
    ".tar", ".gz", ".rar", ".7z", ".exe", ".dll", ".so", ".dylib",
    ".mp4", ".mov", ".avi", ".mp3", ".wav", ".flac", ".woff", ".woff2",
    ".ttf", ".otf", ".class", ".jar", ".bin",
}

LANGUAGE_ALIASES = {
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


@dataclass(frozen=True)
class ExportConfig:
    root: Path
    output_dir: Path
    max_file_size_bytes: int
    max_combined_size_bytes: int
    consolidated: bool


@dataclass
class ExtensionStats:
    count: int = 0
    bytes: int = 0


def load_gitignore(root: Path) -> pathspec.PathSpec:
    gitignore = root / ".gitignore"

    if not gitignore.exists():
        return pathspec.PathSpec.from_lines("gitwildmatch", [])

    lines = gitignore.read_text(encoding="utf-8", errors="ignore").splitlines()
    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


def is_ignored(path: Path, root: Path, spec: pathspec.PathSpec) -> bool:
    if ".git" in path.parts:
        return True

    try:
        relative_path = path.relative_to(root).as_posix()
    except ValueError:
        return False

    return spec.match_file(relative_path)


def is_descendant_or_same(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def is_inside_output_dir(path: Path, output_dir: Path | None) -> bool:
    if output_dir is None:
        return False

    return is_descendant_or_same(path.resolve(), output_dir.resolve())


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(HASH_CHUNK_SIZE), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def is_probably_text(path: Path) -> bool:
    suffix = path.suffix.lower()

    if suffix in LIKELY_BINARY_EXTENSIONS:
        return False

    if suffix in TEXT_EXTENSIONS:
        return True

    try:
        sample = path.read_bytes()[:TEXT_SAMPLE_SIZE]
    except OSError:
        return False

    if b"\x00" in sample:
        return False

    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return False

    return True


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        return f"[ERRO AO LER ARQUIVO: {error}]"


def collect_visible_paths(root: Path, spec: pathspec.PathSpec, output_dir: Path) -> list[Path]:
    paths: list[Path] = []

    for path in root.rglob("*"):
        if is_inside_output_dir(path, output_dir) or is_ignored(path, root, spec):
            continue

        paths.append(path)

    return paths


def get_visible_children(
    current: Path,
    root: Path,
    spec: pathspec.PathSpec,
    output_dir: Path | None,
) -> list[Path]:
    try:
        items = current.iterdir()
    except OSError:
        return []

    sorted_items = sorted(items, key=lambda path: (path.is_file(), path.name.lower()))

    return [
        item
        for item in sorted_items
        if not is_inside_output_dir(item, output_dir) and not is_ignored(item, root, spec)
    ]


def append_tree_lines(
    current: Path,
    root: Path,
    spec: pathspec.PathSpec,
    output_dir: Path | None,
    lines: list[str],
    prefix: str = "",
) -> None:
    visible_items = get_visible_children(current, root, spec, output_dir)

    for index, item in enumerate(visible_items):
        is_last = index == len(visible_items) - 1
        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + item.name)

        if item.is_dir():
            next_prefix = prefix + ("    " if is_last else "│   ")
            append_tree_lines(item, root, spec, output_dir, lines, next_prefix)


def generate_tree(root: Path, spec: pathspec.PathSpec, output_dir: Path | None = None) -> str:
    lines = [f"{root.name}/"]
    append_tree_lines(root, root, spec, output_dir, lines)
    return "\n".join(lines)


def get_language_hint(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    return LANGUAGE_ALIASES.get(suffix, "text")


def build_file_metadata(source_file: Path, root: Path) -> str:
    relative_path = source_file.relative_to(root)
    size = source_file.stat().st_size
    mime_type, _ = mimetypes.guess_type(source_file.name)
    digest = sha256_file(source_file)

    return f"""# Caminho

`{relative_path.as_posix()}`

# Metadados

- Tamanho: `{size}` bytes
- MIME estimado: `{mime_type or "desconhecido"}`
- SHA-256: `{digest}`
"""


def build_file_body(source_file: Path, max_file_size_bytes: int) -> str:
    size = source_file.stat().st_size

    if size > max_file_size_bytes:
        return f"""
# Conteúdo

Arquivo omitido porque ultrapassa o limite configurado de `{max_file_size_bytes}` bytes.
"""

    if not is_probably_text(source_file):
        return """
# Conteúdo

Arquivo provavelmente binário. Conteúdo bruto omitido.
"""

    content = read_text_file(source_file)
    language = get_language_hint(source_file)

    return f"""
# Conteúdo

```{language}
{content}
```
"""


def write_file_markdown(
    source_file: Path,
    root: Path,
    output_dir: Path,
    max_file_size_bytes: int,
) -> None:
    relative_path = source_file.relative_to(root)
    output_file = output_dir / relative_path.parent / f"{relative_path.name}.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_file.write_text(
        build_file_metadata(source_file, root) + build_file_body(source_file, max_file_size_bytes),
        encoding="utf-8",
    )


def update_extension_stats(stats: dict[str, ExtensionStats], file: Path) -> None:
    extension = file.suffix.lower() or "[sem extensão]"
    file_stats = stats.setdefault(extension, ExtensionStats())
    file_stats.count += 1
    file_stats.bytes += file.stat().st_size


def build_summary(files: list[Path]) -> str:
    file_paths = [path for path in files if path.is_file()]
    directory_paths = [path for path in files if path.is_dir()]
    total_bytes = sum(path.stat().st_size for path in file_paths)

    by_extension: dict[str, ExtensionStats] = {}

    for file in file_paths:
        update_extension_stats(by_extension, file)

    rows = "\n".join(
        f"| `{extension}` | {stats.count} | {stats.bytes} |"
        for extension, stats in sorted(
            by_extension.items(),
            key=lambda item: (-item[1].count, item[0]),
        )
    )

    return f"""# Resumo do Projeto

## Totais

- Diretórios: `{len(directory_paths)}`
- Arquivos: `{len(file_paths)}`
- Tamanho total analisado: `{total_bytes}` bytes

## Arquivos por extensão

| Extensão | Quantidade | Bytes |
|---|---:|---:|
{rows}
"""


def sorted_files(files: list[Path], root: Path) -> list[Path]:
    return sorted(
        [path for path in files if path.is_file()],
        key=lambda path: path.relative_to(root).as_posix(),
    )


def build_project_context(
    root: Path,
    files: list[Path],
    spec: pathspec.PathSpec,
    output_dir: Path,
    max_combined_size_bytes: int,
) -> str:
    parts = [
        "# Contexto Consolidado do Projeto",
        "",
        "## Estrutura",
        "",
        "```text",
        generate_tree(root, spec, output_dir),
        "```",
        "",
    ]

    used_bytes = 0

    for file in sorted_files(files, root):
        if not is_probably_text(file):
            continue

        content = read_text_file(file)
        encoded_size = len(content.encode("utf-8", errors="replace"))

        if used_bytes + encoded_size > max_combined_size_bytes:
            relative_path = file.relative_to(root).as_posix()
            parts.extend([
                "",
                "## Limite atingido",
                "",
                (
                    f"O arquivo `{relative_path}` e os próximos foram omitidos "
                    "porque o limite consolidado foi atingido."
                ),
                "",
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
            "",
        ])

    return "\n".join(parts)


def build_tree_markdown(root: Path, spec: pathspec.PathSpec, output_dir: Path) -> str:
    return f"""# Estrutura do Projeto

```text
{generate_tree(root, spec, output_dir)}
```
"""


def validate_export_config(config: ExportConfig) -> ExportConfig:
    root = config.root.resolve()
    output_dir = config.output_dir.resolve()

    if not root.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"O caminho informado não é uma pasta: {root}")

    if root == output_dir:
        raise ValueError("A pasta de saída não pode ser igual à pasta de origem.")

    return ExportConfig(
        root=root,
        output_dir=output_dir,
        max_file_size_bytes=config.max_file_size_bytes,
        max_combined_size_bytes=config.max_combined_size_bytes,
        consolidated=config.consolidated,
    )


def export_directory_to_markdown(config: ExportConfig) -> None:
    config = validate_export_config(config)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    spec = load_gitignore(config.root)
    visible_paths = collect_visible_paths(config.root, spec, config.output_dir)

    (config.output_dir / "TREE.md").write_text(
        build_tree_markdown(config.root, spec, config.output_dir),
        encoding="utf-8",
    )
    (config.output_dir / "SUMMARY.md").write_text(
        build_summary(visible_paths),
        encoding="utf-8",
    )

    for path in visible_paths:
        if path.is_file():
            write_file_markdown(path, config.root, config.output_dir, config.max_file_size_bytes)

    if config.consolidated:
        (config.output_dir / "PROJECT_CONTEXT.md").write_text(
            build_project_context(
                config.root,
                visible_paths,
                spec,
                config.output_dir,
                config.max_combined_size_bytes,
            ),
            encoding="utf-8",
        )


def positive_int(value: str) -> int:
    try:
        parsed_value = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("deve ser um número inteiro") from error

    if parsed_value <= 0:
        raise argparse.ArgumentTypeError("deve ser maior que zero")

    return parsed_value


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Exporta uma pasta para Markdown preservando estrutura, árvore, "
            "resumo e contexto consolidado."
        )
    )

    parser.add_argument("folder", type=Path, help="Pasta que será analisada")

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("markdown_export"),
        help="Pasta onde os arquivos .md serão criados",
    )

    parser.add_argument(
        "--max-file-size-mb",
        type=positive_int,
        default=DEFAULT_MAX_FILE_SIZE_MB,
        help="Tamanho máximo de arquivo individual para incluir conteúdo bruto",
    )

    parser.add_argument(
        "--max-combined-size-mb",
        type=positive_int,
        default=DEFAULT_MAX_COMBINED_SIZE_MB,
        help="Tamanho máximo do PROJECT_CONTEXT.md consolidado",
    )

    parser.add_argument(
        "--no-consolidated",
        action="store_true",
        help="Não gera PROJECT_CONTEXT.md",
    )

    return parser.parse_args(argv)


def config_from_args(args: argparse.Namespace) -> ExportConfig:
    return ExportConfig(
        root=args.folder,
        output_dir=args.output,
        max_file_size_bytes=args.max_file_size_mb * BYTES_PER_MB,
        max_combined_size_bytes=args.max_combined_size_mb * BYTES_PER_MB,
        consolidated=not args.no_consolidated,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = config_from_args(args)

    try:
        export_directory_to_markdown(config)
    except (OSError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1

    print(f"Exportação concluída em: {config.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
