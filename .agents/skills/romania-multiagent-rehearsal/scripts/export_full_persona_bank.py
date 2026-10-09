"""Audit all ORIGINAL 65 live repository profiles and export human-readable detail.

No overwriting profiles, approved scene memory or production sources.
"""
from __future__ import annotations
import argparse
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from engine import PROJECT_ROOT, registry

def inspect_bank(root:Path=PROJECT_ROOT):
    bank=registry(root)
    rows=[]
    issues=[]
    for i in range(1,66):
        key=f"{i:02d}"
        p=bank[key]
        src=p.get("source_profile",{})
        identity=p.get("identity_extension",{})
        lang=p.get("language_dna",{})
        media=lang.get("媒体行为管理_v4",{})
        locale=lang.get("角色语言执行_v4_1",{}).get("母语或优先输出语言","未知")
        policy=media.get("媒体许可策略",{})
        style=p.get("personality",{}).get("核心标签",[])
        emotional=p.get("emotion_model",{})
        row={
            "id":key,
            "name":identity.get("姓名"),
            "gender":src.get("性别"),
            "age":src.get("年龄"),
            "occupation":src.get("工作_职业"),
            "city":identity.get("居住城市"),
            "residency":src.get("所在地"),
            "character_traits":style,
            "speech_structure":lang.get("典型结构"),
            "normal_length":lang.get("正常发言长度"),
            "preferred_language":locale,
            "emoji":lang.get("表情习惯",{}).get("常用",[]),
            "gif_allowed":policy.get("GIF",None),
            "png_allowed":policy.get("PNG",None),
            "media_optional_actions":media.get("媒体动作可选",[]),
            "default_emotion":emotional.get("默认状态"),
            "social_relationships":p.get("relationship_network",[]),
            "investment_history_known":bool(p.get("investment_history")),
            "memory_schema_present":bool(p.get("memory_system")),
            "speech_triggers_top_level":bool(p.get("speech_triggers")),
            "activity_pattern":p.get("activity_pattern",{}),
            "fictional_only":p.get("simulation_only")
        }
        if not row["name"] or row["preferred_language"]=="未知":
            issues.append({"id":key,"severity":"ERROR","issue":"identity_or_language_absent"})
        if row["gif_allowed"] is None:
            issues.append({"id":key,"severity":"ERROR","issue":"gif_policy_missing"})
        if not row["speech_triggers_top_level"]:
            issues.append({"id":key,"severity":"INFO","issue":"top_level_speech_triggers_absent_check_other_sections"})
        if row["fictional_only"] is not True:
            issues.append({"id":key,"severity":"ERROR","issue":"missing_fictional_label"})
        rows.append(row)
    return rows,issues


def generate(output:Path,root:Path=PROJECT_ROOT)->dict:
    rows,issues=inspect_bank(root)
    output.mkdir(parents=True,exist_ok=True)
    counts=Counter(r["preferred_language"] for r in rows)
    gif=Counter(str(r["gif_allowed"]) for r in rows)
    err=[i for i in issues if i["severity"]=="ERROR"]
    report={
        "audit_type":"ORIGINAL_65_PERSONA_FULL_PROFILES",
        "source":"skills/romania-market-director/characters/profiles/",
        "source_is_github_workflow_checkout":True,
        "review_status":"NOT_TESTED_FOR_HUMAN_SPEECH_QUALITY",
        "count":len(rows),
        "unique_ids":len({r["id"] for r in rows}),
        "language_counts":dict(counts),
        "gif_permission_counts":dict(gif),
        "missing_top_level_triggers":[r["id"] for r in rows if not r["speech_triggers_top_level"]],
        "errors":err,"informational_flags":len(issues)-len(err)
    }
    (output/"65人人物明细.json").write_text(json.dumps({"summary":report,"people":rows},ensure_ascii=False,indent=2),encoding="utf-8")
    m=["# 罗马尼亚65位虚构教学角色 · 原始完整档案索引",
       "",
       "> 此表由仓库当前65份JSON原文生成；详细性格、历史、关系与完整语言DNA以打包的原始JSON为准。此处的人物均为虚构演练角色，不是真实群成员。",
       "",
       "|ID|姓名|性别/年龄|职业与城市|母语/首选|性格标签|常见发言长度|GIF许可|",
       "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        m.append("|{}|{}|{} / {}|{} · {}|{}|{}|{}|{}|".format(
          r["id"],r["name"],r["gender"],r["age"],r["occupation"],r["city"],
          r["preferred_language"],"、".join(r["character_traits"][:3]),
          (r["normal_length"] or "").replace("|","/"),
          "允许" if r["gif_allowed"] else "禁止"))
    m+=["","## 审核备注",
        f'- 读取人物：{len(rows)}；语言分布：{dict(counts)}；GIF权限：{dict(gif)}',
        f'- 独立 `speech_triggers` 缺失：{len(report["missing_top_level_triggers"])}。属于字段结构差异，不自动当作人物没有动机。',
        f'- 严重字段错误：{len(err)}；未通过真实罗马尼亚语自然度人工验收。',
        '- 正式历史在 memory/state.json 单独管理，未授权不写；请勿将临时模拟视作已发群记录。',
        '- 不得将虚构人物评论用于伪造投资者见证。']
    (output/"65人人物明细_中文.md").write_text("\n".join(m)+"\n",encoding="utf-8")
    (output/"核验报告.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    originals=root/"skills/romania-market-director/characters/profiles"
    with zipfile.ZipFile(output/"原始65人全量JSON.zip","w",zipfile.ZIP_DEFLATED) as z:
        for item in sorted(originals.glob("*_AI_Profile.json")):
            z.write(item,arcname="profiles/"+item.name)
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    arg=p.parse_args()
    report=generate(arg.output)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if report["errors"] or report["count"]!=65 or report["unique_ids"]!=65:
        raise SystemExit("Profile audit FAILED")
