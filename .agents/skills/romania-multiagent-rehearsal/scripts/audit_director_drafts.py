"""Audit existing official director screenplay drafts against morning 50/afternoon 45.

Counts names *independent messages*, not headings or newline fragments.
Never converts unverified research placeholders into fake market facts.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from engine import PROJECT_ROOT, course_for_date

DIRECTOR=Path("skills/romania-market-director")
DRAFTS=DIRECTOR/"library/drafts"
OLD_50="2026-10-08_上午50条_证据待补编辑稿.md"
REFINED="2026-10-08_上午长助理主题稿_待补全.md"
DAYTIME="2026-10-08_待核验编辑稿.md"

def lines(text:str):
    # For the previous two versions: one numbered/attributed line = one post.
    return re.findall(r"(?m)^\s*(\d{2})[｜|]\s*(?!【编辑位)",text)

def audit(root:Path=PROJECT_ROOT, date:str="2026-10-09") -> dict:
    dr=root/DRAFTS
    original=(dr/OLD_50).read_text(encoding="utf-8")
    refined=(dr/REFINED).read_text(encoding="utf-8")
    combined=(dr/DAYTIME).read_text(encoding="utf-8")
    first=combined.split("## 三、上午",1)[1].split("## 四、下午",1)[0] if "## 三、上午" in combined else ""
    afternoon=combined.split("## 四、下午",1)[1].split("## 五、晚间",1)[0] if "## 四、下午" in combined else ""
    def count_marked(block):
        return len(re.findall(r"(?m)^\s*\*\*(\d{2})[｜|]",block))
    c=course_for_date(date)
    idx=json.loads((root/DIRECTOR/"library/index.json").read_text(encoding="utf-8"))
    mem=json.loads((root/DIRECTOR/"memory/state.json").read_text(encoding="utf-8"))
    info={
       "audit":"SOURCE_GROUNDED_NOT_A_COMPLETED_FINANCE_SCRIPT",
       "date":date,"zone":"Europe/Bucharest",
       "morning_required":50,"afternoon_required":45,
       "legacy_morning_numbered":len(lines(original)),
       "legacy_morning_has_unverified_placeholders":bool(re.search(r"【(?:编辑位|国际资讯|AI相关新闻)",original)),
       "refined_morning_count":len(lines(refined)),
       "refined_morning_has_unverified_placeholders":"【编辑位" in refined or "【国际资讯" in refined,
       "combined_earlier_draft_morning_count":count_marked(first),
       "combined_earlier_draft_afternoon_count":count_marked(afternoon),
       "approved_scenes":len(idx.get("approved_scenes",[])),
       "adopted_memory_scenes":len(mem.get("adopted_scenes",[])),
       "missing_inputs":idx.get("missing_inputs",[]),
       "technical_course_user_manuscript_present":False if any("技术课" in x for x in idx.get("missing_inputs",[])) else "not_verified",
       "professor_course":c["course"],
       "professor_start_bucharest":c["local_start"],
       "professor_morning":c["professor_morning"],
       "requires_human_approval":True,
       "morning_full_pass":False,
       "afternoon_full_pass":False,
       "course_manuscript_pass":False,
       "reason":"Latest complete 50-morning archive was superseded due to fragmented analysis and unverified news. No 45-afternoon verified current draft; user technical manuscript missing.",
       "no_fake_news_inserted":True
    }
    return info

def write_report(out:Path, date:str):
    d=audit(date=date)
    out.mkdir(parents=True,exist_ok=True)
    (out/"导演原始剧本数量与证据验收.json").write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
    doc=f"""# 导演原始剧本 · 可追溯验收报告

> 日期 {date} Europe/Bucharest。此项为**原始草稿审计**，不代表当前行情稿完成或已发布。所有角色为虚构教学演绎。

|核对项目|原要求|实际核对|判定|
|---|---|---|---|
|上午|50条独立署名消息|旧稿{d["legacy_morning_numbered"]}条，已因碎片化与待核验资讯被取代；修订长助理稿{d["refined_morning_count"]}条|**未通过**|
|下午|45条独立署名消息|早期综合草稿仅{d["combined_earlier_draft_afternoon_count"]}条；正式验收稿缺失|**未通过**|
|人物|65+2角色位|实际资料库有65原始档案；不强制全部出场|人物读取已独立通过|
|行情|每项指标来源/时刻/单位/基准|旧稿仍有待核验编辑占位|**禁止当已完成资讯稿**|
|实际采用历史|只记录已采用场景|已有已采用场景{d["adopted_memory_scenes"]}个|不得编造往期互动|
|今晚课程|20:20–20:50正式课，20:50–21:10答疑|今天课程类型：{d["professor_course"]}；课程讲稿是否齐备：{d["technical_course_user_manuscript_present"]}|**待补用户技术课原文**|

不能因为旧稿“排了50个号码”就宣布达到质量要求。真正验收标准是：**资讯源核验、助理完整主题长话、短句人物互动、95条独立消息、教授正式时段、人物档案规则及中文/罗马尼亚语质量。**

本报告只指出真实缺口，**没有添加伪造的新闻或虚构行情**。
"""
    (out/"导演原始剧本验收_中文.md").write_text(doc,encoding="utf-8")
    return d

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--date",default="2026-10-09")
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(write_report(a.output,a.date),ensure_ascii=False,indent=2))
