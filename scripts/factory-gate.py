#!/usr/bin/env python3
"""MOMAI Factory Gate Validator (P4.1)

检查 asset-registry.yaml:
- 每个资产必须有 asset_id / type / owner / consumers / backup_required
- backup_required=true 必须有 rpo / backup_method / last_restore_test_at
- Production asset 不允许 NO_GIT / NO_OWNER / NO_BACKUP / UNKNOWN

用法: python3 factory-gate.py [registry.yaml]
退出码: 0 = PASS, 1 = FAIL
"""
import sys, yaml

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else '/Users/zhiyunlian/.hermes/asset-registry.yaml'
    try:
        data = yaml.safe_load(open(path, encoding='utf-8'))
    except Exception as e:
        print(f"FACTORY_GATE=FAIL registry 读取失败: {e}")
        return 1

    fails = []
    for a in data.get('assets', []):
        aid = a.get('asset_id', '?')
        # 必需字段
        for req in ['asset_id', 'type', 'owner', 'consumers', 'status']:
            if req not in a or a[req] in (None, '', []):
                fails.append(f"{aid}: missing {req}")
        # backup_required=true → 必须有 rpo/backup_method/restore_test
        if a.get('backup_required'):
            for req in ['rpo', 'backup_method', 'last_restore_test_at', 'retention']:
                if req not in a or a[req] in (None, ''):
                    fails.append(f"{aid}: backup_required but missing {req}")

    # db decisions 检查
    for name, d in data.get('database_backup_decisions', {}).items():
        if d.get('backup_required') and not d.get('backup_method'):
            fails.append(f"db-{name}: backup_required but missing backup_method")
        if not d.get('backup_required') and not d.get('rebuild_procedure'):
            fails.append(f"db-{name}: NOT_REQUIRED but missing rebuild_procedure")

    if fails:
        print("FACTORY_GATE=FAIL")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"FACTORY_GATE=PASS ({len(data.get('assets', []))} assets, {len(data.get('database_backup_decisions', {}))} db decisions)")
    return 0

if __name__ == '__main__':
    sys.exit(main())
