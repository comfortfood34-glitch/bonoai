"""Data migration CLI command."""

from __future__ import annotations

import argparse
import json

from bonoai.domain.data import DataContractError


def run_data_migrate(args: argparse.Namespace) -> int:
    """Execute data-migrate command."""
    from bonoai.infrastructure.migrations import get_migration_info, migrate_v1_to_v2

    csv_path = args.data_dir / "processed" / "draws.csv"

    if not csv_path.exists():
        result: dict[str, str | None] = {
            "status": "nao_encontrado",
            "path": str(csv_path),
            "message": "Arquivo não encontrado; nada a migrar",
        }
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"Arquivo não encontrado: {csv_path}")
        return 0

    migration_info = get_migration_info(csv_path)
    schema_version = migration_info.get("schema_version")

    if schema_version == "2":
        result = {
            "status": "ja_v2",
            "schema_version": "2",
            "message": "Arquivo já está em schema v2; nenhuma migração necessária",
        }
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("Schema já é v2; nenhuma ação necessária")
        return 0

    if schema_version == "1":
        try:
            migrate_v1_to_v2(csv_path)
            result = {
                "status": "migrado",
                "schema_version": "2",
                "path": str(csv_path),
                "message": "Migração v1 → v2 concluída com sucesso",
            }
            backup = migration_info.get("backup")
            if backup:
                result["backup"] = backup
            if args.as_json:
                print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print(f"Migração concluída: {csv_path}")
                if backup:
                    print(f"Backup preservado: {backup}")
            return 0
        except DataContractError as error:
            result = {
                "status": "erro_dados",
                "message": str(error),
            }
            if args.as_json:
                print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                import sys
                print(f"ERRO nos dados: {error}", file=sys.stderr)
            return 1
        except (OSError, RuntimeError) as error:
            result = {
                "status": "erro_operacional",
                "message": str(error),
            }
            if args.as_json:
                print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                import sys
                print(f"ERRO operacional: {error}", file=sys.stderr)
            return 2

    result = {
        "status": "schema_desconhecido",
        "schema_version": schema_version,
        "message": f"Schema desconhecido: {schema_version}",
    }
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        import sys
        print(f"ERRO: schema desconhecido: {schema_version}", file=sys.stderr)
    return 2
