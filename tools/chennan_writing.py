#!/usr/bin/env python3
"""Trading Center character-writing service backed ONLY by the Finance Director 65-person roster.

Standalone local writing state lives outside the repository; no Supabase/72-person import,
LLM generation, market publication, or trading mutations are performed here.
"""
import json
import os
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from finance_skill_hub import DIRECTOR, personas, slot_for
from dialogue_quality import DISCLOSURE, audit_dialogue
from storycraft_contract import audit_storycraft
from role_voice import role_voice_contract, member_voice_briefs, audit_member_register
from editorial_storyline import plan_disclosed_scene
from skill_execution_contract import audit_member_voice, load_official_memory, lesson_for

ROSTER_SOURCE = "finance-director-65-v4.1"
MAX_SOURCE_CHARS = 20000
MAX_DOC_CHARS = 150000
MAX_MESSAGES = 200


def _clean_id(value):
    return str(value).zfill(2) if str(value).isdigit() else ""


def load_profiles():
    """Every identity must match the validated authoritative 65 full profiles."""
    roster = personas.validate()
    index = json.loads((DIRECTOR / "characters/index.json").read_text(encoding="utf-8"))
    profiles = {}
    for row in index:
        cid = _clean_id(row["id"])
        filename = row["profile_file"]
        if (not cid or Path(filename).name != filename or
                not filename.startswith(cid + "_") or not filename.endswith("_AI_Profile.json")):
            raise ValueError("Invalid source profile filename")
        obj = json.loads((DIRECTOR / "characters/profiles" / filename).read_text(encoding="utf-8"))
        expected = roster.get(cid)
        if (not expected or _clean_id(obj.get("character_id")) != cid or
                obj.get("identity_extension", {}).get("姓名") != expected["name"] or
                obj.get("source_profile", {}).get("性别") != expected["gender"] or
                obj.get("source_profile", {}).get("学员资历") != expected["role"] or
                obj.get("simulation_only") is not True):
            raise ValueError("Source persona identity changed: " + cid)
        profiles[cid] = obj
    if len(profiles) != 65 or set(profiles) != set(roster):
        raise ValueError("The authoritative 65-person source is incomplete")
    return profiles


def summaries(profiles):
    return [
        {
            "character_id": cid,
            "name": p["identity_extension"]["姓名"],
            "gender": p["source_profile"]["性别"],
            "role": p["source_profile"]["学员资历"],
            "age": p["source_profile"].get("年龄"),
            "city": p["identity_extension"].get("居住城市"),
            "occupation": p["source_profile"].get("工作_职业"),
            "description": p.get("relationship_to_group", {}).get("角色定位", ""),
        }
        for cid, p in sorted(profiles.items())
    ]


def empty_state():
    return {"schema_version": "1.0", "roster_source": ROSTER_SOURCE,
            "revision": 0, "drafts": {}, "sessions": [], "docs": []}


def read_state(path):
    path = Path(path)
    if not path.exists():
        return empty_state()
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or obj.get("roster_source") != ROSTER_SOURCE:
        raise ValueError("Writing state source differs from the 65-person system")
    if not isinstance(obj.get("drafts"), dict) or not isinstance(obj.get("sessions"), list) or not isinstance(obj.get("docs"), list):
        raise ValueError("Writing state format is invalid")
    return obj


def write_state(path, state):
    """Atomic explicit write. State is never committed to GitHub."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8")
    if len(data) > 15_000_000:
        raise ValueError("Writing workspace state exceeds its 15 MB safety limit; export/backup first")
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=".writing-", suffix=".tmp", delete=False) as stream:
            name = stream.name
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def make_prompt(payload, profiles, state):
    if not isinstance(payload, dict):
        raise ValueError("Request must be an object")
    source = payload.get("source_text")
    if not isinstance(source, str) or not source.strip() or len(source) > MAX_SOURCE_CHARS:
        raise ValueError("Enter the original assistant/professor passage (1-20000 characters)")
    kind = payload.get("source_kind")
    if kind not in ("assistant", "professor"):
        raise ValueError("source_kind must be assistant or professor")
    chosen = payload.get("selected_ids")
    if not isinstance(chosen, list) or not 1 <= len(chosen) <= 65:
        raise ValueError("Select between 1 and 65 people")
    ids = [_clean_id(x) for x in chosen]
    if len(set(ids)) != len(ids) or not all(x in profiles for x in ids):
        raise ValueError("The selected IDs contain duplicates or people outside the 65-person roster")
    node_id = payload.get("node")
    if not isinstance(node_id, str):
        raise ValueError("Select a valid finance schedule node")
    node = slot_for(datetime.now(timezone.utc), requested=node_id)
    if kind == "professor" and node["id"] != "RO-10":
        raise ValueError("Professor passage is restricted to RO-10 (19:30 class)")
    day = str(payload.get("date", "")).strip()
    try:
        parsed = date.fromisoformat(day)
        if parsed.isoformat() != day:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError("Date must be YYYY-MM-DD") from None
    lesson = lesson_for(day, node["id"])
    if kind == "professor" and not lesson["can_speak"]:
        raise ValueError("Professor course is permitted only on weekdays at RO-10")
    topic = str(payload.get("topic") or "课程互动").strip()[:160]
    draft_id = uuid4().hex
    # Select by the actual selected characters, not merely the last five global
    # sessions (which could omit an infrequent character's older adopted memory).
    recent = [
        {
            "id": s["id"],
            "status": "adopted",
            "date": s["date"],
            "source_kind": s["source_kind"],
            "source_text": s["source_text"],
            "messages": [m for m in s.get("messages", []) if m.get("character_id") in ids],
        }
        for s in state["sessions"]
        if any(m.get("character_id") in ids for m in s.get("messages", []))
    ][-12:]
    official_memory = load_official_memory(ids)
    storyline_plan = plan_disclosed_scene(node["id"], topic, ids, state["sessions"],
                                           unresolved_threads=state.get("unresolved_threads", []))
    prompt = {
        "engine": "交易中心 · 65人统一人物版",
        "mode": "explicitly_disclosed_fictional_educational_simulation",
        "draft_id": draft_id,
        "date": day,
        "topic": topic,
        "node": node["id"],
        "source_kind": kind,
        "source_text": source,
        "roster_source": ROSTER_SOURCE,
        "selected_characters": [profiles[cid] for cid in ids],
        "role_voice_contract": role_voice_contract(),
        "selected_personal_voice_briefs": member_voice_briefs(profiles, ids),
        "recent_adopted_sessions": recent,
        "official_memory": official_memory,
        "storyline_plan": storyline_plan,
        "memory_policy": {
            "adopted_only": True,
            "do_not_invent_prior_conversations": True,
            "no_fixed_personality_mutations": True,
            "session_memory_scope": "this_workstation_only; other BVB UI history not synced",
            "history_citation_format": {"continuity_ref": {"session_id": "adopted scene id", "message_id": "approved message id"}},
            "uncited_memories": "do not treat a confident-sounding backstory as adopted history",
            "unresolved_history": "unknown until imported and approved",
        },
        "professor_course_policy": lesson,
        "instructions": [
            "先读 skills/romania-market-director/references/teaching-editorial-standard.md：不集中吹捧教授；每条一个重点，问题可延迟引用前文，由助理答疑。",
            "每条模拟消息显著标注【虚构教学模拟】；案例标【假设】，禁止把虚构盈亏、持仓和机构背书当真人社会证明促销。真实经验只用已授权可核证信息。",
            "仅使用随附65份正式虚构人物档案，不得引用旧72人辰南人物或按相同编号映射。",
            "保留助理/教授给定原话；只写成员的模拟群聊反应，不改写主持人原话。",
            "姓名、性别、新老、当地语言、语气、句长、表情、媒体许可均按人物自己的档案执行。",
            "角色可沉默、短句、质疑、追问、互相回复；不要固定顺序或凑人数。",
            "演绎采用双线叙事：新新闻可以开始，同时只在已经真实采用的剧本历史里存在旧问题时穿插旧争论；禁止无记录就编造昨日争吵。",
            "成员可以就上一条或上一时段的新闻与同伴发生有理据的激烈分歧；允许跨节点延续，但禁止辱骂、造谣或一致性操控。",
            "助理必要时梳理各方证据、记录未解问题，允许暂时没有共识；无需每次发新闻都强行管理整场讨论。",
            "教授用可核实资料或标注为【假设】的比方解释机制及反例，不以保证收益或隐瞒风险包装短周期观察。",
            "成员不必围绕助理/教授发言：允许提出独立话题、回应其他成员、追问前文、表达具体分歧，也允许不接话。",
            "成员优先说简短有信息量的白话文，每条只讲一个意思；禁止空洞附和、教授吹捧接龙和重复套话。",
            "所有模拟个人买卖、持仓及盈亏情节必须标【假设】；任何单独流转的成员文本必须带【虚构教学模拟】。",
            "所有人物和对白均为虚构教学演练，不能冒充真实投资者或真实客户见证。",
            "不得编造行情、收益、交易记录、账户数据、新闻来源或已经发送的媒体。",
            "只返回 JSON：messages 数组；每条含 character_id、name、gender、role、text；可选 message_id、reply_to。",
            "逐人读取本人语言DNA、句长偏好、Emoji/GIF许可、16节点/活跃时段与实际已采用记忆；未记录的人物旧事必须说未知，不编造。", 
            "助理分析必须含新闻出处/时间/发生事件/对BVB与行业影响链/抵消因素/不确定性/下次核对条件；不杜撰新闻和指数。", 
            "教授仅19:30，周一三五技术课、周二四理念课；技术课原稿缺失必须说明，不冒称已获得旧讲稿。", 
            "记忆只能经人工检查并明确采用后存为正式会话，生成草稿不能自动写历史。",
            "【角色语言层级】普通成员只按各自生活、职业和独立性格说话，1句话优先，不用财经播报、宏观研报、成套专业术语或助理的总结话术。",
            "【角色语言层级】助理可以使用金融术语，但要解释含义，保持专业、准确、亲切，讲清核实事实、条件和不确定性。",
            "【角色语言层级】教授必须高度专业：概念定义、假设、推导、证据、反例、适用边界和课程练习都要严谨；不编资格、原课件、数值和盈利。",
            "【每人不同】selected_personal_voice_briefs 中的职业、性格、习惯、长度、语言要逐人使用；不得65个人像同一个证券分析师，也不照抄样例成为统一口癖。",
            "【分享边界】每个成员决定自己要不要分享；可以只问不答、沉默、保留个人研究细节，也可以依自身性格和关系提供帮助。不强制公益式介绍赚钱机会，不强制藏私；不可拿罗马尼亚国籍代替独立人格判断。",
            "先阅读 skills/romania-market-director/references/high-empathy-storycraft-v2.md：根据人物情绪、关系和上一句证据安排自然对白，不强制每人发言或每轮起冲突。",
            "人物对白正文不要说自己是虚拟角色、AI、模拟人物、按剧本表演等出戏台词；身份披露属于作品标识与输出元数据，不得删除独立流转内容的必要披露。",
            "凡是提及某人昨天说过、前几场发生过或已经改变立场，必须来自 recent_adopted_sessions 或已采用正式记忆；在 JSON 的该消息里提供 continuity_ref 的 session_id 与 message_id；没有证据就写为新问题，不能假装旧事。",
            "出现质疑、焦虑、后悔、误解时先承接具体问题与情绪，再解释事实、风险和未知，不居高临下、不贴标签、不催促下单。",
            "把每条消息的主题关联、所据来源和话语目的想清楚；没有关联就删减或标记待核，不制造热点、假历史或无关商业话术。",
        ],
        "output_schema": {"messages": [
            {"character_id": ids[0], "name": profiles[ids[0]]["identity_extension"]["姓名"],
             "gender": profiles[ids[0]]["source_profile"]["性别"],
             "role": profiles[ids[0]]["source_profile"]["学员资历"],
             "text": "【虚构教学模拟】只用于说明JSON字段格式；不是真实生成的消息",
             "continuity_ref": None}
        ]},
    }
    new_state = dict(state)
    new_state["drafts"] = dict(state["drafts"])
    new_state["drafts"][draft_id] = {
        "id": draft_id, "date": day, "topic": topic, "node": node["id"],
        "selected_ids": ids, "source_kind": kind, "source_text": source,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    # Bound pending prompt metadata, not the 65 full profiles.
    if len(new_state["drafts"]) > 80:
        oldest = next(iter(new_state["drafts"]))
        del new_state["drafts"][oldest]
    new_state["revision"] = state["revision"] + 1
    return prompt, new_state


def validate_messages(raw, draft, profiles, sessions):
    if not isinstance(raw, dict) or not isinstance(raw.get("messages"), list):
        raise ValueError('Paste JSON with a "messages" array')
    messages = raw["messages"]
    if len(messages) > MAX_MESSAGES:
        raise ValueError("Too many messages (maximum 200)")
    selected = set(draft["selected_ids"])
    errors, cleaned, used = [], [], set()
    for i, m in enumerate(messages, 1):
        if not isinstance(m, dict):
            errors.append(f"Message {i}: object required")
            continue
        cid = _clean_id(m.get("character_id"))
        if cid not in selected or cid not in profiles:
            errors.append(f"Message {i}: unknown/unselected character")
            continue
        profile = profiles[cid]
        expected = (profile["identity_extension"]["姓名"],
                    profile["source_profile"]["性别"],
                    profile["source_profile"]["学员资历"])
        received = (m.get("name"), m.get("gender"), m.get("role"))
        if received != expected:
            errors.append(f"Message {i}: ID/name/gender/old-new classification mismatch")
        message = m.get("text")
        if not isinstance(message, str) or not message.strip() or len(message) > 1600:
            errors.append(f"Message {i}: nonempty text with maximum 1600 characters required")
            continue
        mid = str(m.get("message_id") or f"m{i}")
        if not mid.isascii() or len(mid) > 80 or mid in used:
            errors.append(f"Message {i}: duplicate/invalid message_id")
            continue
        used.add(mid)
        if m.get("simulation_only") is False:
            errors.append(f"Message {i}: simulation_only=false is forbidden")
        allowed = profile.get("language_dna", {}).get("禁用表达", [])
        if any(isinstance(x, str) and x and x in message for x in allowed):
            errors.append(f"Message {i}: expression forbidden by persona profile")
        cleaned.append({"message_id": mid, "character_id": cid, "name": expected[0],
                        "gender": expected[1], "role": expected[2],
                        "text": message.strip() if DISCLOSURE in message else DISCLOSURE + message.strip(),
                        "simulation_only": True, "experience_kind": m.get("experience_kind", "none"),
                        "media_type": m.get("media_type", "TEXT"),
                        "asset_id": m.get("asset_id"),
                        "asset_verified": m.get("asset_verified", False),
                        "reply_to": m.get("reply_to") or None,
                        "continuity_ref": m.get("continuity_ref"),
                        "historical_claim": m.get("historical_claim", False),
                        "evidence_ref": m.get("evidence_ref")})
    for m in cleaned:
        if m["reply_to"] and m["reply_to"] != "source" and m["reply_to"] not in used:
            errors.append("Unknown reply reference: " + str(m["reply_to"]))
    dialogue = audit_dialogue(cleaned)
    errors.extend(dialogue["issues"])
    personal_voice = audit_member_voice(cleaned, profiles)
    errors.extend(personal_voice["issues"])
    storycraft = audit_storycraft(cleaned, draft=draft, sessions=sessions)
    errors.extend(storycraft["issues"])
    role_voices = audit_member_register(cleaned, profiles)
    errors.extend(role_voices["issues"])
    if any(s.get("draft_id") == draft["id"] for s in sessions):
        errors.append("This draft was already formally adopted")
    return {"valid": not errors, "errors": errors,
            "message_count": len(cleaned), "messages": cleaned,
            "dialogue_quality": dialogue,
            "persona_quality": personal_voice,
            "storycraft_quality": storycraft,
            "role_voice_quality": role_voices,
            "warning": "Checks and red-line heuristics are not factual verification. Dialogue naturalness, market facts, and media still need human review."}


def adopt(raw, draft_id, state, profiles):
    draft = state["drafts"].get(draft_id)
    if not draft:
        raise ValueError("Draft ID not found or already adopted")
    report = validate_messages(raw, draft, profiles, state["sessions"])
    if not report["valid"]:
        raise ValueError("; ".join(report["errors"]))
    if raw.get("confirmed") is not True:
        raise ValueError("Explicit confirmed=true is required for formal adoption")
    session = {
        "id": uuid4().hex, "draft_id": draft_id,
        "date": draft["date"], "topic": draft["topic"], "node": draft["node"],
        "source_kind": draft["source_kind"], "source_text": draft["source_text"],
        "selected_ids": draft["selected_ids"], "messages": report["messages"],
        "status": "adopted", "roster_source": ROSTER_SOURCE,
        "adopted_at": datetime.now(timezone.utc).isoformat(),
    }
    new_state = dict(state)
    new_state["sessions"] = state["sessions"] + [session]
    new_state["drafts"] = dict(state["drafts"])
    del new_state["drafts"][draft_id]
    new_state["revision"] = state["revision"] + 1
    return session, new_state


def save_doc(raw, state):
    if not isinstance(raw, dict):
        raise ValueError("Document request must be an object")
    title, content = raw.get("title"), raw.get("content")
    if not isinstance(title, str) or not title.strip() or len(title) > 160:
        raise ValueError("A document title of 1-160 characters is required")
    if not isinstance(content, str) or len(content) > MAX_DOC_CHARS:
        raise ValueError("Document content must be text (maximum 150000 characters)")
    doc_id = raw.get("id")
    if doc_id is not None and (not isinstance(doc_id, str) or
                               not any(d["id"] == doc_id for d in state["docs"])):
        raise ValueError("Document ID not found")
    doc_id = doc_id or uuid4().hex
    new_doc = {"id": doc_id, "title": title.strip(), "content": content,
               "updated_at": datetime.now(timezone.utc).isoformat()}
    new_state = dict(state)
    new_state["docs"] = [new_doc if d["id"] == doc_id else d for d in state["docs"]]
    if not any(d["id"] == doc_id for d in state["docs"]):
        new_state["docs"].append(new_doc)
    new_state["revision"] = state["revision"] + 1
    return new_doc, new_state
